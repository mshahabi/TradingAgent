# TradingAgent

Designing a Gen AI Agent for Building Trading Agents.

## Overview

The `TradingAgent` project is a Python-based framework for developing, testing, and deploying trading strategies. It integrates with the Interactive Brokers (IB) API to fetch historical and real-time market data, perform backtesting, and execute trades. The project also includes tools for visualizing trading performance, analyzing results, and generating insights using advanced design patterns.

## Features

- **Historical Data Retrieval**: Fetch historical market data using the IB API.
- **Backtesting**: Test trading strategies on historical data to evaluate performance.
- **Trading Strategies**: Implement and test custom trading strategies, such as micro pullbacks.
- **Visualization**: Plot trading signals, volume, VWAP, and EMAs using `mplfinance` and `plotly`.
- **Performance Metrics**: Calculate win rate, total profit, average trade return, and analyze losing trade patterns.
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

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/TradingAgent.git
   cd TradingAgent
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running Backtests
To run a backtest using the micro pullback strategy:
```bash
python backtesting/ib_micro_pull_back.py
```

### Visualizing Trades
The `TradeAnalyzer` class provides tools for visualizing trades, including VWAP, EMAs, and trade markers:
```python
from utils.trade_analyzer import TradeAnalyzer

# Initialize the TradeAnalyzer with transactions and data
analyzer = TradeAnalyzer(transactions, data=app.data)

# Plot trades
analyzer.plot_trades()
```

### Analyzing Performance
Use the `TradeAnalyzer` class to calculate performance metrics:
```python
# Calculate metrics
profit_by_entry_type = analyzer.calculate_profit_by_entry_type()
win_rate = analyzer.calculate_win_rate()
total_profit = analyzer.calculate_total_profit()
average_trade_return = analyzer.calculate_average_trade_return()
```

## Key Components

### `TradeAnalyzer` Class
The `TradeAnalyzer` class encapsulates all trade analysis functionality, including:
- Calculating profits by entry type
- Calculating win rates
- Analyzing losing trade patterns
- Plotting trades with VWAP, EMAs, and volume

### Utility Functions
The `utils` module contains helper functions for:
- Calculating VWAP (`compute_daily_vwap`)
- Plotting trading data
- Analyzing trade patterns

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Submit a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or support, please contact [your_email@example.com](mailto:your_email@example.com).