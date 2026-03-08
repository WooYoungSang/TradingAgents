"""Offline unit tests for the experiment runner contract."""

from __future__ import annotations

import argparse
import importlib.util
import json
import tempfile
import unittest
from types import ModuleType
from pathlib import Path
from unittest.mock import patch


def load_run_experiment_module():
    """Load eval/run_experiment.py as a module for unit testing."""
    module_path = Path(__file__).resolve().parents[2] / "eval" / "run_experiment.py"
    spec = importlib.util.spec_from_file_location("run_experiment_module", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load eval/run_experiment.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTradingAgentsGraph:
    """Small fake graph for deterministic experiment runner tests."""

    def __init__(self, *, config, debug):
        self.config = config
        self.debug = debug

    def propagate(self, symbol: str, run_date: str):
        rationale = "parse_error" if run_date.endswith("02") else "ok"
        action = "HOLD" if rationale == "parse_error" else "BUY"
        final_state = {
            "trade_plan": {
                "action": action,
                "rationale": rationale,
            }
        }
        return final_state, action


class RunExperimentTests(unittest.TestCase):
    """Contract coverage for experiment artifact generation."""

    module: ModuleType

    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_run_experiment_module()

    def test_parse_dates_expands_ranges_and_deduplicates(self) -> None:
        dates = self.module.parse_dates("2026-01-01:2026-01-02,2026-01-02,2026-01-03")

        self.assertEqual(dates, ["2026-01-01", "2026-01-02", "2026-01-03"])

    def test_resolve_experiment_dir_supports_placeholder_and_trailing_slash(self) -> None:
        placeholder_dir = self.module.resolve_experiment_dir("results/<exp_id>/", "exp-123")
        trailing_dir = self.module.resolve_experiment_dir("results/experiments/", "exp-123")

        self.assertEqual(placeholder_dir, Path("results/exp-123"))
        self.assertEqual(trailing_dir, Path("results/experiments/exp-123"))

    def test_run_experiment_writes_required_artifacts_and_summary_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            args = argparse.Namespace(
                config="configs/local_4090.yaml",
                symbols="AAPL",
                dates="2026-01-01:2026-01-02",
                out_dir=f"{temp_dir}/<exp_id>/",
                exp_id="offline-contract",
                debug=False,
            )

            with patch.object(
                self.module,
                "load_config",
                return_value={"llm_provider": "stub", "output_schema_version": "tradeplan.v1"},
            ), patch.object(
                self.module,
                "load_trading_graph_class",
                return_value=FakeTradingAgentsGraph,
            ):
                self.module.run_experiment(args)

            exp_dir = Path(temp_dir) / "offline-contract"
            config_effective = exp_dir / "config_effective.yaml"
            runs_jsonl = exp_dir / "runs.jsonl"
            summary_json = exp_dir / "summary.json"

            self.assertTrue(config_effective.exists())
            self.assertTrue(runs_jsonl.exists())
            self.assertTrue(summary_json.exists())

            runs = [json.loads(line) for line in runs_jsonl.read_text(encoding="utf-8").splitlines()]
            summary = json.loads(summary_json.read_text(encoding="utf-8"))

            self.assertEqual(len(runs), 2)
            self.assertEqual(summary["total_runs"], 2)
            self.assertEqual(summary["success_runs"], 2)
            self.assertEqual(summary["failed_runs"], 0)
            self.assertEqual(summary["parse_error_count"], 1)
            self.assertEqual(summary["parse_error_rate"], 0.5)
            self.assertEqual(summary["action_distribution"], {"BUY": 1, "SELL": 0, "HOLD": 1})
            self.assertEqual(summary["artifacts"]["config_effective"], str(config_effective))
            self.assertEqual(summary["artifacts"]["runs_jsonl"], str(runs_jsonl))
            self.assertEqual(summary["artifacts"]["summary_json"], str(summary_json))


if __name__ == "__main__":
    unittest.main()
