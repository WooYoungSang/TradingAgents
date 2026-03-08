from __future__ import annotations

import importlib
import json
import sys
import types
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tradingagents.output.trade_plan_builder import TradePlanBuilder, TradePlanParseError  # noqa: E402


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class SequenceLLM:
    def __init__(self, outputs: list[str]) -> None:
        self._outputs = list(outputs)

    def invoke(self, _messages: list[tuple[str, str]]) -> FakeResponse:
        if not self._outputs:
            raise AssertionError("No more fake LLM outputs configured.")
        return FakeResponse(self._outputs.pop(0))


def build_final_state() -> dict[str, object]:
    return {
        "company_of_interest": "AAPL",
        "trade_date": "2026-03-08",
        "market_report": "market",
        "sentiment_report": "sentiment",
        "news_report": "news",
        "fundamentals_report": "fundamentals",
        "investment_debate_state": {
            "bull_history": ["bull"],
            "bear_history": ["bear"],
            "history": ["history"],
            "current_response": "response",
            "judge_decision": "judge",
        },
        "trader_investment_plan": "trader-plan",
        "risk_debate_state": {
            "aggressive_history": ["aggressive"],
            "conservative_history": ["conservative"],
            "neutral_history": ["neutral"],
            "history": ["risk-history"],
            "judge_decision": "risk-judge",
        },
        "investment_plan": "investment-plan",
        "final_trade_decision": "BUY because momentum is improving.",
    }


def import_trading_graph_module():
    prebuilt = types.ModuleType("langgraph.prebuilt")

    class ToolNode:
        def __init__(self, tools: list[object]) -> None:
            self.tools = tools

    prebuilt.ToolNode = ToolNode
    sys.modules["langgraph.prebuilt"] = prebuilt

    llm_clients = types.ModuleType("tradingagents.llm_clients")

    class ClientWrapper:
        def get_llm(self) -> object:
            return object()

    llm_clients.create_llm_client = lambda **_kwargs: ClientWrapper()
    sys.modules["tradingagents.llm_clients"] = llm_clients

    agents = types.ModuleType("tradingagents.agents")
    agents.__all__ = []
    sys.modules["tradingagents.agents"] = agents

    memory = types.ModuleType("tradingagents.agents.utils.memory")

    class FinancialSituationMemory:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

    memory.FinancialSituationMemory = FinancialSituationMemory
    sys.modules["tradingagents.agents.utils.memory"] = memory

    agent_states = types.ModuleType("tradingagents.agents.utils.agent_states")

    class AgentState:
        pass

    class InvestDebateState:
        pass

    class RiskDebateState:
        pass

    agent_states.AgentState = AgentState
    agent_states.InvestDebateState = InvestDebateState
    agent_states.RiskDebateState = RiskDebateState
    sys.modules["tradingagents.agents.utils.agent_states"] = agent_states

    dataflows_config = types.ModuleType("tradingagents.dataflows.config")
    dataflows_config.set_config = lambda _config: None
    sys.modules["tradingagents.dataflows.config"] = dataflows_config

    agent_utils = types.ModuleType("tradingagents.agents.utils.agent_utils")
    for name in [
        "get_stock_data",
        "get_indicators",
        "get_fundamentals",
        "get_balance_sheet",
        "get_cashflow",
        "get_income_statement",
        "get_news",
        "get_insider_transactions",
        "get_global_news",
    ]:
        setattr(agent_utils, name, lambda *args, _name=name, **kwargs: _name)
    sys.modules["tradingagents.agents.utils.agent_utils"] = agent_utils

    conditional_logic = types.ModuleType("tradingagents.graph.conditional_logic")

    class ConditionalLogic:
        pass

    conditional_logic.ConditionalLogic = ConditionalLogic
    sys.modules["tradingagents.graph.conditional_logic"] = conditional_logic

    setup = types.ModuleType("tradingagents.graph.setup")

    class GraphSetup:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def setup_graph(self, _selected_analysts: list[str]) -> object:
            return types.SimpleNamespace(stream=lambda *_args, **_kwargs: [], invoke=lambda *_args, **_kwargs: {})

    setup.GraphSetup = GraphSetup
    sys.modules["tradingagents.graph.setup"] = setup

    propagation = types.ModuleType("tradingagents.graph.propagation")

    class Propagator:
        def create_initial_state(self, *_args: object, **_kwargs: object) -> dict[str, object]:
            return {}

        def get_graph_args(self) -> dict[str, object]:
            return {}

    propagation.Propagator = Propagator
    sys.modules["tradingagents.graph.propagation"] = propagation

    reflection = types.ModuleType("tradingagents.graph.reflection")

    class Reflector:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

    reflection.Reflector = Reflector
    sys.modules["tradingagents.graph.reflection"] = reflection

    signal_processing = types.ModuleType("tradingagents.graph.signal_processing")

    class SignalProcessor:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def process_signal(self, full_signal: str) -> str:
            return full_signal

    signal_processing.SignalProcessor = SignalProcessor
    sys.modules["tradingagents.graph.signal_processing"] = signal_processing

    sys.modules.pop("tradingagents.graph.trading_graph", None)
    return importlib.import_module("tradingagents.graph.trading_graph")


def test_trade_plan_builder_returns_valid_trade_plan() -> None:
    builder = TradePlanBuilder(
        quick_thinking_llm=SequenceLLM(
            [
                json.dumps(
                    {
                        "symbol": "AAPL",
                        "date": "2026-03-08",
                        "action": "BUY",
                        "position_size": {"type": "fraction", "value": 0.25},
                        "constraints": {"time_in_force": "day", "max_slippage_bps": 15},
                        "confidence": 0.82,
                        "rationale": "Momentum and sentiment align.",
                        "evidence_refs": ["state://market_report"],
                    }
                )
            ]
        ),
        config={"json_repair_max_retries": 0, "output_schema_version": "tradeplan.v1"},
    )

    trade_plan = builder.build(
        symbol="AAPL",
        trade_date="2026-03-08",
        full_decision_text="BUY because momentum is improving.",
        extracted_action="BUY",
        final_state=build_final_state(),
    )

    assert trade_plan["action"] == "BUY"
    assert trade_plan["schema_version"] == "tradeplan.v1"
    assert "state://final_trade_decision" in trade_plan["evidence_refs"]


def test_trade_plan_builder_surfaces_deterministic_parse_failure() -> None:
    builder = TradePlanBuilder(
        quick_thinking_llm=SequenceLLM(["not-json", "still not json", "plain text"]),
        config={"json_repair_max_retries": 2, "output_schema_version": "tradeplan.v1"},
    )

    with pytest.raises(TradePlanParseError) as exc_info:
        builder.build(
            symbol="AAPL",
            trade_date="2026-03-08",
            full_decision_text="BUY because momentum is improving.",
            extracted_action="BUY",
            final_state=build_final_state(),
        )

    message = str(exc_info.value)
    assert "TRADEPLAN_PARSE_FAILED" in message
    assert "symbol=AAPL" in message
    assert "date=2026-03-08" in message
    assert "last_error=" in message
    assert "last_output_excerpt=" in message
    assert "state://final_trade_decision" in message


def test_propagate_returns_decision_and_logs_trade_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    trading_graph_module = import_trading_graph_module()
    graph = trading_graph_module.TradingAgentsGraph.__new__(trading_graph_module.TradingAgentsGraph)
    graph.debug = False
    graph.ticker = None
    graph.curr_state = None
    graph.log_states_dict = {}
    graph.propagator = types.SimpleNamespace(
        create_initial_state=lambda *_args, **_kwargs: {},
        get_graph_args=lambda: {},
    )
    graph.graph = types.SimpleNamespace(invoke=lambda *_args, **_kwargs: build_final_state())
    graph.process_signal = lambda _signal: "BUY"
    graph.trade_plan_builder = TradePlanBuilder(
        quick_thinking_llm=SequenceLLM(
            [
                json.dumps(
                    {
                        "symbol": "AAPL",
                        "date": "2026-03-08",
                        "action": "BUY",
                        "position_size": {"type": "fraction", "value": 0.25},
                        "constraints": {"time_in_force": "day", "max_slippage_bps": 15},
                        "confidence": 0.82,
                        "rationale": "Momentum and sentiment align.",
                        "evidence_refs": ["state://market_report"],
                    }
                )
            ]
        ),
        config={"json_repair_max_retries": 0, "output_schema_version": "tradeplan.v1"},
    )

    monkeypatch.chdir(tmp_path)

    final_state, decision = graph.propagate("AAPL", date(2026, 3, 8))

    assert decision == "BUY"
    assert final_state["trade_plan"]["action"] == "BUY"

    log_path = tmp_path / "eval_results" / "AAPL" / "TradingAgentsStrategy_logs" / "full_states_log_2026-03-08.json"
    payload = json.loads(log_path.read_text())
    state_log = payload["2026-03-08"]

    assert state_log["final_trade_decision"] == "BUY because momentum is improving."
    assert state_log["trade_plan"]["action"] == "BUY"
