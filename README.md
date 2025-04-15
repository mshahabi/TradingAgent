# TradingAgent

Designing a Gen AI Agents for Building Trading Agents.

## Overview

The `TradingAgent` project is a Python-based framework for developing, testing, and deploying trading strategies. It integrates with Interactive Brokers (IB) API to fetch historical and real-time market data, perform backtesting, and execute trades. The project also includes tools for visualizing trading performance and analyzing results.

## Features

- **Historical Data Retrieval**: Fetch historical market data using the IB API.
- **Backtesting**: Test trading strategies on historical data to evaluate performance.
- **Trading Strategies**: Implement and test custom trading strategies, such as micro pullbacks.
- **Visualization**: Plot trading signals, volume, and VWAP using `mplfinance` or `plotly`.
- **Performance Metrics**: Calculate win rate, total profit, and average trade return.
- **Thread Synchronization**: Handle API requests and responses efficiently using threading.

## Project Structure

```plaintext
TradingAgent/
├── src/
│   ├── ib_micro_pull_back.py       # Main script for micro pullback strategy
│   ├── agents/                     # Directory for agent implementations
│   │   └── __init__.py
│   ├── strategies/                 # Directory for trading strategies
│   │   └── __init__.py
│   ├── utils/                      # Utility functions and helpers
│   │   └── __init__.py
│   ├── tests/                      # Unit tests for the project
│   │   └── test_main.py
├── [requirements.txt](http://_vscodecontentref_/1)                # Python dependencies
└── [README.md](http://_vscodecontentref_/2)                       # Project documentation
```

## Installation

To install the `TradingAgent` project, run the following commands:

```bash
git clone https://github.com/yourusername/TradingAgent.git
cd TradingAgent
pip install -r requirements.txt
```
