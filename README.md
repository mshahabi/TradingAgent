# TradingAgent

Designing a Gen AI Agent for Building Trading Agents.

## Overview

The `TradingAgent` project is a Python-based framework for developing, testing, and deploying trading strategies. It integrates with the Interactive Brokers (IB) API to fetch historical and real-time market data, perform backtesting, and execute trades. The project also includes tools for visualizing trading performance, analyzing results, and generating insights using advanced design patterns.

## Features

- **Historical Data Retrieval**: Fetch historical market data using the IB API.
- **Backtesting**: Test trading strategies on historical data to evaluate performance.
- **Trading Strategies**: Implement and test custom trading strategies, such as micro pullbacks.
- **Visualization**: Plot trading signals, volume, and VWAP using `mplfinance`.
- **Performance Metrics**: Calculate win rate, total profit, and average trade return.
- **Thread Synchronization**: Handle API requests and responses efficiently using threading.
- **Modular Design**: Encapsulate functionality using object-oriented design principles and design patterns for scalability and maintainability.

## Project Structure

```plaintext
TradingAgent/
├── backtesting/
│   ├── ib_micro_pull_back.py       # Main script for backtesting micro pullback strategy
│   └── __init__.py
├── strategies/
│   ├── micro_pullback_momentum.py  # Implementation of the micro pullback momentum strategy
│   └── __init__.py
├── utils/
│   ├── __init__.py                 # Utility functions and helpers
│   ├── trade_analyzer.py           # Encapsulates trade analysis logic
│   ├── calculate_metrics.py        # Functions for calculating performance metrics
│   ├── plot_utils.py               # Functions for plotting trading data
│   └── trade_analysis.py           # Functions for analyzing trade patterns
├── tests/
│   ├── test_backtesting.py         # Unit tests for backtesting logic
│   ├── test_strategies.py          # Unit tests for trading strategies
│   └── test_utils.py               # Unit tests for utility functions
├── requirements.txt                # Python dependencies
└── README.md                       # Project documentation
```

## Installation

To install the `TradingAgent` project, follow these steps:

```bash
git clone https://github.com/yourusername/TradingAgent.git
cd TradingAgent
pip install -r requirements.txt
```