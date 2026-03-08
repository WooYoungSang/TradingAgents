"""Lightweight experiment runner for TradingAgents configuration comparisons."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

# Allow direct script execution: `python eval/run_experiment.py ...`
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tradingagents.config_loader import load_config  # noqa: E402
from tradingagents.default_config import DEFAULT_CONFIG  # noqa: E402


def parse_symbols(raw: str) -> list[str]:
    """Parse comma-separated symbols into an ordered unique list."""
    symbols: list[str] = []
    for token in raw.split(","):
        symbol = token.strip().upper()
        if symbol and symbol not in symbols:
            symbols.append(symbol)
    return symbols


def _expand_date_range(start: str, end: str) -> list[str]:
    start_date = datetime.strptime(start, "%Y-%m-%d").date()
    end_date = datetime.strptime(end, "%Y-%m-%d").date()
    if end_date < start_date:
        raise ValueError(f"Invalid date range: {start}:{end}")

    dates: list[str] = []
    current = start_date
    while current <= end_date:
        dates.append(current.isoformat())
        current += timedelta(days=1)
    return dates


def parse_dates(raw: str) -> list[str]:
    """Parse date input from comma list and/or range tokens."""
    dates: list[str] = []
    for token in raw.split(","):
        part = token.strip()
        if not part:
            continue
        if ":" in part:
            start, end = [x.strip() for x in part.split(":", 1)]
            expanded = _expand_date_range(start, end)
            for date_text in expanded:
                if date_text not in dates:
                    dates.append(date_text)
        else:
            _ = datetime.strptime(part, "%Y-%m-%d")
            if part not in dates:
                dates.append(part)
    return dates


def resolve_experiment_dir(out_dir: str, exp_id: str) -> Path:
    """Resolve output directory, supporting <exp_id> placeholder."""
    has_placeholder = "<exp_id>" in out_dir
    resolved = out_dir.replace("<exp_id>", exp_id)
    if has_placeholder:
        return Path(resolved)
    if out_dir.endswith("/") or out_dir.endswith("\\"):
        return Path(resolved) / exp_id
    return Path(resolved)


def load_trading_graph_class() -> type[Any]:
    """Load the trading graph class lazily for CLI execution and tests."""
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    return TradingAgentsGraph


def run_experiment(args: argparse.Namespace) -> None:
    """Execute experiment runs and write comparable artifacts."""
    exp_id = args.exp_id or f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{Path(args.config).stem}"
    exp_dir = resolve_experiment_dir(args.out_dir, exp_id)
    exp_dir.mkdir(parents=True, exist_ok=True)

    effective_config = load_config(args.config, DEFAULT_CONFIG.copy())
    symbols = parse_symbols(args.symbols)
    dates = parse_dates(args.dates)

    with open(exp_dir / "config_effective.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(effective_config, f, sort_keys=True, allow_unicode=False)

    runs_path = exp_dir / "runs.jsonl"
    summary_started = time.perf_counter()
    started_at_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"

    failures = 0
    parse_errors = 0
    runtimes: list[float] = []
    action_counter: Counter[str] = Counter()

    graph = load_trading_graph_class()(config=effective_config, debug=args.debug)

    with open(runs_path, "w", encoding="utf-8") as runs_file:
        for symbol in symbols:
            for run_date in dates:
                run_started = time.perf_counter()
                run_record: dict[str, Any] = {
                    "exp_id": exp_id,
                    "symbol": symbol,
                    "date": run_date,
                    "status": "ok",
                    "error": None,
                }

                try:
                    final_state, decision = graph.propagate(symbol, run_date)
                    trade_plan = final_state.get("trade_plan", {})

                    runtime_sec = time.perf_counter() - run_started
                    runtimes.append(runtime_sec)

                    action = str(trade_plan.get("action", "UNKNOWN")).upper()
                    action_counter[action] += 1

                    is_parse_error = str(trade_plan.get("rationale", "")) == "parse_error"
                    if is_parse_error:
                        parse_errors += 1

                    run_record.update(
                        {
                            "runtime_sec": runtime_sec,
                            "decision": decision,
                            "trade_plan": trade_plan,
                            "parse_error": is_parse_error,
                            "log_ref": f"eval_results/{symbol}/TradingAgentsStrategy_logs/full_states_log_{run_date}.json",
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    failures += 1
                    runtime_sec = time.perf_counter() - run_started
                    runtimes.append(runtime_sec)
                    is_parse_error = "TRADEPLAN_PARSE_FAILED" in str(exc)
                    if is_parse_error:
                        parse_errors += 1
                    run_record.update(
                        {
                            "status": "failed",
                            "runtime_sec": runtime_sec,
                            "decision": None,
                            "trade_plan": None,
                            "parse_error": is_parse_error,
                            "log_ref": f"eval_results/{symbol}/TradingAgentsStrategy_logs/full_states_log_{run_date}.json",
                            "error": str(exc),
                        }
                    )

                runs_file.write(json.dumps(run_record, ensure_ascii=True) + "\n")

    total_runs = len(symbols) * len(dates)
    total_runtime = time.perf_counter() - summary_started
    average_runtime = sum(runtimes) / len(runtimes) if runtimes else 0.0

    success_runs = total_runs - failures
    action_distribution = {
        "BUY": int(action_counter.get("BUY", 0)),
        "SELL": int(action_counter.get("SELL", 0)),
        "HOLD": int(action_counter.get("HOLD", 0)),
    }

    summary = {
        "exp_id": exp_id,
        "started_at_utc": started_at_utc,
        "finished_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "config_path": os.path.abspath(args.config),
        "total_runs": total_runs,
        "success_runs": success_runs,
        "failed_runs": failures,
        "total_runtime_sec": total_runtime,
        "average_runtime_sec": average_runtime,
        "parse_error_count": parse_errors,
        "parse_error_rate": (parse_errors / total_runs) if total_runs else 0.0,
        "action_distribution": action_distribution,
        "symbols": symbols,
        "dates": dates,
        "artifacts": {
            "config_effective": str(exp_dir / "config_effective.yaml"),
            "runs_jsonl": str(exp_dir / "runs.jsonl"),
            "summary_json": str(exp_dir / "summary.json"),
        },
    }

    with open(exp_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=True)

    print(f"Experiment complete: {exp_id}")
    print(f"Output directory: {exp_dir}")


def build_arg_parser() -> argparse.ArgumentParser:
    """Build command-line parser for experiment execution."""
    parser = argparse.ArgumentParser(
        description="Run TradingAgents experiments and collect comparable artifacts."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to YAML config (e.g., configs/local_4090.yaml).",
    )
    parser.add_argument(
        "--symbols",
        required=True,
        help='Comma-separated symbols, e.g., "AAPL,MSFT,NVDA".',
    )
    parser.add_argument(
        "--dates",
        required=True,
        help='Date list and/or ranges, e.g., "2026-01-01:2026-01-03,2026-01-10".',
    )
    parser.add_argument(
        "--out_dir",
        default="results/experiments/<exp_id>/",
        help="Output directory. Supports <exp_id> placeholder.",
    )
    parser.add_argument(
        "--exp_id",
        default=None,
        help="Optional experiment id. If omitted, generated from UTC timestamp + config stem.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run TradingAgentsGraph with debug mode enabled.",
    )
    return parser


def main() -> None:
    """CLI entrypoint for experiment runner."""
    parser = build_arg_parser()
    args = parser.parse_args()
    run_experiment(args)


if __name__ == "__main__":
    main()
