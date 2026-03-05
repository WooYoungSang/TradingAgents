import os
from pathlib import Path

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.config_loader import load_config

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Config loading priority:
# 1) TRADINGAGENTS_CONFIG env var
# 2) local example YAML in configs/local_4090.yaml
# 3) original hardcoded fallback example
env_config_path = os.getenv("TRADINGAGENTS_CONFIG")
example_config_path = Path("configs/local_4090.yaml")

if env_config_path:
    config = load_config(env_config_path, DEFAULT_CONFIG.copy())
elif example_config_path.exists():
    config = load_config(str(example_config_path), DEFAULT_CONFIG.copy())
else:
    # Create a custom config (legacy example fallback)
    config = DEFAULT_CONFIG.copy()
    config["deep_think_llm"] = "gpt-5-mini"  # Use a different model
    config["quick_think_llm"] = "gpt-5-mini"  # Use a different model
    config["max_debate_rounds"] = 1  # Increase debate rounds

    # Configure data vendors (default uses yfinance, no extra API keys needed)
    config["data_vendors"] = {
        "core_stock_apis": "yfinance",           # Options: alpha_vantage, yfinance
        "technical_indicators": "yfinance",      # Options: alpha_vantage, yfinance
        "fundamental_data": "yfinance",          # Options: alpha_vantage, yfinance
        "news_data": "yfinance",                 # Options: alpha_vantage, yfinance
    }

# Initialize with custom config
ta = TradingAgentsGraph(debug=True, config=config)

# forward propagate
_, decision = ta.propagate("NVDA", "2024-05-10")
print(decision)

# Memorize mistakes and reflect
# ta.reflect_and_remember(1000) # parameter is the position returns
