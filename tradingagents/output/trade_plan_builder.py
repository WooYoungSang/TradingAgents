"""Builder for converting final decision text into TradePlan.v1 JSON."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from tradingagents.contracts.trade_plan import TradePlanV1


class TradePlanParseError(RuntimeError):
    """Raised when TradePlan JSON cannot be produced after repair retries."""


class TradePlanBuilder:
    """Build TradePlan.v1 payloads using the quick thinking LLM."""

    def __init__(self, quick_thinking_llm: Any, config: Dict[str, Any]):
        self.quick_thinking_llm = quick_thinking_llm
        self.config = config

    def build(
        self,
        symbol: str,
        trade_date: str,
        full_decision_text: str,
        extracted_action: str,
        final_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a validated TradePlan.v1 dictionary or raise parse error."""
        retries = int(self.config.get("json_repair_max_retries", 2))
        schema_version = str(self.config.get("output_schema_version", "tradeplan.v1"))
        evidence_refs = self._collect_evidence_refs(final_state)
        action_hint = extracted_action.strip().upper()

        error_note = "unknown_error"
        previous_output = None

        for attempt in range(retries + 1):
            prompt = self._build_prompt(
                symbol=symbol,
                trade_date=trade_date,
                full_decision_text=full_decision_text,
                action_hint=action_hint,
                evidence_refs=evidence_refs,
                schema_version=schema_version,
                attempt=attempt,
                previous_output=previous_output,
                previous_error=error_note,
            )

            llm_output = self.quick_thinking_llm.invoke(
                [("system", self._system_prompt()), ("human", prompt)]
            ).content

            try:
                payload = self._extract_json_dict(str(llm_output))
                payload["schema_version"] = schema_version
                payload.setdefault("symbol", symbol)
                payload.setdefault("date", trade_date)
                payload.setdefault("action", action_hint if action_hint in {"BUY", "SELL", "HOLD"} else "HOLD")
                payload.setdefault("evidence_refs", evidence_refs)
                plan = TradePlanV1.from_dict(payload)
                return plan.to_dict()
            except Exception as exc:  # noqa: BLE001
                error_note = str(exc)
                previous_output = str(llm_output)

        error_message = (
            "TRADEPLAN_PARSE_FAILED: "
            f"symbol={symbol}, date={trade_date}, retries={retries}, "
            f"last_error={error_note}, "
            f"evidence_refs={json.dumps(evidence_refs)}"
        )
        raise TradePlanParseError(error_message)

    @staticmethod
    def _system_prompt() -> str:
        return (
            "You convert trading analysis text into strict JSON only. "
            "Do not use markdown. Do not include explanation. Return one JSON object."
        )

    def _build_prompt(
        self,
        symbol: str,
        trade_date: str,
        full_decision_text: str,
        action_hint: str,
        evidence_refs: List[str],
        schema_version: str,
        attempt: int,
        previous_output: str | None,
        previous_error: str,
    ) -> str:
        repair_context = ""
        if attempt > 0:
            repair_context = (
                f"\nPrevious output was invalid.\n"
                f"Validation error: {previous_error}\n"
                f"Previous output:\n{previous_output}\n"
                "Repair and return valid JSON only.\n"
            )

        return (
            "Create TradePlan JSON that follows this exact schema:\n"
            "{"
            "\"schema_version\": \"tradeplan.v1\", "
            "\"symbol\": \"<string>\", "
            "\"date\": \"<YYYY-MM-DD>\", "
            "\"action\": \"BUY|SELL|HOLD\", "
            "\"position_size\": {\"type\": \"fraction|shares|usd\", \"value\": <number>}, "
            "\"constraints\": {\"time_in_force\": \"day|gtc\", \"max_slippage_bps\": <number>}, "
            "\"confidence\": <number between 0 and 1>, "
            "\"rationale\": \"<short string>\", "
            "\"evidence_refs\": [\"<string>\"]"
            "}\n"
            "Rules:\n"
            "- Output must be valid JSON object only.\n"
            "- No markdown fences.\n"
            "- confidence must be in [0,1].\n"
            "- rationale should be under 240 characters.\n"
            f"- schema_version must be {schema_version}.\n"
            f"- symbol must be {symbol}.\n"
            f"- date must be {trade_date}.\n"
            f"- Prefer action={action_hint} unless text strongly implies otherwise.\n"
            f"- Include evidence_refs using this list as baseline: {json.dumps(evidence_refs)}.\n"
            f"Decision text:\n{full_decision_text}\n"
            f"{repair_context}"
        )

    @staticmethod
    def _extract_json_dict(raw_text: str) -> Dict[str, Any]:
        text = raw_text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.DOTALL).strip()

        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, flags=re.DOTALL)
            if not match:
                raise
            payload = json.loads(match.group(0))

        if not isinstance(payload, dict):
            raise ValueError("TradePlan payload must be a JSON object.")
        return payload

    def _collect_evidence_refs(self, final_state: Dict[str, Any]) -> List[str]:
        mode = str(self.config.get("evidence_mode", "cache_ref"))

        report_keys = [
            "market_report",
            "sentiment_report",
            "news_report",
            "fundamentals_report",
            "investment_plan",
            "trader_investment_plan",
            "final_trade_decision",
        ]

        refs: List[str] = []
        for key in report_keys:
            value = final_state.get(key)
            if value:
                if mode == "cache_ref":
                    refs.append(f"state://{key}")
                else:
                    preview = str(value).replace("\n", " ")[:80]
                    refs.append(f"{key}:{preview}")

        return refs
