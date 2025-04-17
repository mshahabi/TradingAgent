import threading
import time
import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trade_analyzer import TradeAnalyzer
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from strategies.micro_pullback_momentum import backtest

# Define selected stocks for backtesting
selected_stocks = {
    "20250416": ["MLGO", "FMTO", "TGL", "MIRA"],}

class TradeApp(EWrapper, EClient): 
    def __init__(self): 
        EClient.__init__(self, self) 
        self.data = {}
        self.skip = False
        
    def historicalData(self, reqId, bar):
        if reqId not in self.data:
            self.data[reqId] = pd.DataFrame([
                {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close, "Volume": bar.volume}
            ])
        else:
            self.data[reqId] = pd.concat((self.data[reqId], pd.DataFrame([
                {"Date": bar.date, "Open": bar.open, "High": bar.high, "Low": bar.low, "Close": bar.close, "Volume": bar.volume}
            ])))
          
    def historicalDataEnd(self, reqId, start, end):
        super().historicalDataEnd(reqId, start, end)
        print("HistoricalDataEnd. ReqId:", reqId, "from", start, "to", end)
        self.skip = False
        ticker_event.set()  # Signal that the data for the ticker has been retrieved

#establish connection to IBKR
def connection():
    app.run()

# Initialize API connection
ticker_event = threading.Event()    
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) 
con_thread = threading.Thread(target=connection, daemon=True)
con_thread.start()
time.sleep(1)


date_stats, transactions = backtest(selected_stocks, app, ticker_event)

# Print transactions
for reqID, transaction_list in transactions.items():
    print(f"Ticker: {reqID}")
    for trans in transaction_list:
        print(f"Date: {trans[0]} | Action: {trans[1]} | Ticker: {trans[2]} |Price: {trans[3]:.2f} | Entry Type: {trans[4]}")

# Initialize TradeAnalyzer
trade_analyzer = TradeAnalyzer(transactions, data=app.data)

# Calculate and print win rates
win_rate_results = trade_analyzer.calculate_win_rate()

# Extract strategy-specific and overall win rates
strategy_win_rates = win_rate_results["strategy_win_rates"]
overall_win_rate = win_rate_results["overall_win_rate"]

# Print win rates
print("Win Rate by Strategy:")
for strategy, rate in strategy_win_rates.items():
    print(f"Strategy: {strategy} | Win Rate: {rate:.2f}%")

print(f"Overall Win Rate: {overall_win_rate:.2f}%")

# Calculate and print total profit and average trade return
total_profit = trade_analyzer.calculate_total_profit()
average_trade_return, total_trades = trade_analyzer.calculate_average_trade_return()
profit_by_entry_type = trade_analyzer.calculate_profit_by_entry_type()

#print(f"Total Profit: {total_profit:.2f}")
#print(f"Average Trade Return: {average_trade_return:.2f}% | Total Trades: {total_trades}")

print("Profit by Entry Type:")
for entry_type, profit in profit_by_entry_type.items():
    print(f"Entry Type: {entry_type} | Profit: {profit:.2f}")

# Plot trades after backtest is completed
trade_analyzer.plot_trades()
