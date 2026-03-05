"""TradePlan contract definitions and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


ALLOWED_ACTIONS = {"BUY", "SELL", "HOLD"}


@dataclass
class TradePlanV1:
    """Structured trade plan output contract."""

    symbol: str
    date: str
    action: str
    position_size: Dict[str, Any]
    constraints: Dict[str, Any]
    confidence: float
    rationale: str
    evidence_refs: List[str] = field(default_factory=list)
    schema_version: str = "tradeplan.v1"

    def validate(self) -> None:
        """Validate the current instance and raise ValueError on violations."""
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be a non-empty string.")
        if not isinstance(self.date, str) or not self.date.strip():
            raise ValueError("date must be a non-empty string.")

        self.action = str(self.action).upper().strip()
        if self.action not in ALLOWED_ACTIONS:
            raise ValueError("action must be one of BUY, SELL, HOLD.")

        if not isinstance(self.position_size, dict):
            raise ValueError("position_size must be an object.")
        if "type" not in self.position_size or "value" not in self.position_size:
            raise ValueError("position_size must include type and value.")

        if not isinstance(self.constraints, dict):
            raise ValueError("constraints must be an object.")
        if "time_in_force" not in self.constraints:
            raise ValueError("constraints must include time_in_force.")
        if "max_slippage_bps" not in self.constraints:
            raise ValueError("constraints must include max_slippage_bps.")

        self.confidence = float(self.confidence)
        if self.confidence < 0.0 or self.confidence > 1.0:
            raise ValueError("confidence must be within [0, 1].")

        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be a non-empty string.")

        if not isinstance(self.evidence_refs, list):
            raise ValueError("evidence_refs must be a list of strings.")
        if not all(isinstance(item, str) for item in self.evidence_refs):
            raise ValueError("evidence_refs must contain only strings.")

        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise ValueError("schema_version must be a non-empty string.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize plan to dictionary and validate before returning."""
        self.validate()
        return {
            "schema_version": self.schema_version,
            "symbol": self.symbol,
            "date": self.date,
            "action": self.action,
            "position_size": self.position_size,
            "constraints": self.constraints,
            "confidence": self.confidence,
            "rationale": self.rationale,
            "evidence_refs": self.evidence_refs,
        }

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "TradePlanV1":
        """Construct and validate TradePlanV1 from payload."""
        plan = cls(
            symbol=payload["symbol"],
            date=payload["date"],
            action=payload["action"],
            position_size=payload["position_size"],
            constraints=payload["constraints"],
            confidence=payload["confidence"],
            rationale=payload["rationale"],
            evidence_refs=payload.get("evidence_refs", []),
            schema_version=payload.get("schema_version", "tradeplan.v1"),
        )
        plan.validate()
        return plan

    @classmethod
    def safe_hold(
        cls,
        symbol: str,
        date: str,
        error_note: str,
        evidence_refs: List[str] | None = None,
        schema_version: str = "tradeplan.v1",
    ) -> "TradePlanV1":
        """Create a safe fallback HOLD plan used for parse failures."""
        refs = list(evidence_refs or [])
        refs.append(f"parse_error:{error_note}")
        return cls(
            symbol=symbol,
            date=date,
            action="HOLD",
            position_size={"type": "fraction", "value": 0.0},
            constraints={
                "time_in_force": "day",
                "max_slippage_bps": 0,
                "parse_error_note": error_note,
            },
            confidence=0.0,
            rationale="parse_error",
            evidence_refs=refs,
            schema_version=schema_version,
        )

