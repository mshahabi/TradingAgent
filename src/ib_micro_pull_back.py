import threading
import time
import pandas as pd
import mplfinance as mpf
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from datetime import datetime
from pytz import timezone
import numpy as np
# Define selected stocks for backtesting
selected_stocks = {
    "20250402": ["MLGO"]
}
selected_stocks.values()  # Extract the stock symbols for backtesting
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

# Define contract function
def usTechStk(symbol, sec_type="STK", currency="USD", exchange="SMART"):
    contract = Contract()
    contract.symbol = symbol
    contract.secType = sec_type
    contract.currency = currency
    contract.exchange = exchange
    return contract 

# Request historical data
def histData(req_num, contract, endDate, duration, candle_size):
    app.reqHistoricalData(reqId=req_num, 
                          contract=contract,
                          endDateTime=endDate,
                          durationStr=duration,
                          barSizeSetting=candle_size,
                          whatToShow='TRADES',
                          useRTH=1,
                          formatDate=1,
                          keepUpToDate=0,
                          chartOptions=[]) 

def connection():
    app.run()

# Initialize API connection
ticker_event = threading.Event()    
app = TradeApp()
app.connect(host='127.0.0.1', port=7497, clientId=23) 
con_thread = threading.Thread(target=connection, daemon=True)
con_thread.start()
time.sleep(1)

# Backtesting function with synchronized thread handling
def backtest(selected_stocks, app):
    date_stats = {}
    transactions = []
    reqID = 1000
    
    # Synchronize thread
    for date in selected_stocks.keys():
        date_stats[date] = {}
        for ticker in selected_stocks[date]:
            ticker_event.clear()  # Clear the event before making request
            histData(reqID, usTechStk(ticker), date + " 22:05:00 US/Eastern", '10 D', '1 min')
            ticker_event.wait()  # Wait until data is received

            if reqID not in app.data or app.data[reqID].empty:
                print(f"Warning: No data for {ticker} on {date}")
                continue  # Skip if no data is retrieved
            
            df = app.data[reqID]
            df = df.copy()
            df['Momentum'] = 0  # Initialize momentum column
            
            # Define green candle condition
            df['Green'] = df['Close'] > df['Open']
            
            # Identify three consecutive green candles
            df['Momentum'] = (df['Green'].shift(1) & df['Green']& df['Green'].shift(2))
            
            # Calculate pullback conditions directly
            df['Pullback'] = (df['Close'] < df['Close'].shift(1))
            df['MicroPullback'] = df['Momentum'].shift(1) & df['Pullback']
            
            # Calculate VWAP
            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Cumulative_PV'] = (df['Typical_Price'] * df['Volume'].astype(float)).cumsum()
            df['Cumulative_Volume'] = df['Volume'].astype(float).cumsum()
            df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']
            
            # Ensure price is above VWAP
            df['AboveVWAP'] = df['Close'] > df['VWAP']
            
            # Combine MicroPullback and AboveVWAP conditions
            df['MicroPullback'] = df['MicroPullback'] & df['AboveVWAP']
            df.dropna(inplace=True)

            entry_price = None
            exit_price = None
            stop_loss = None
            target_price = None
            buy_date = None
            sell_date = None

            for i in range(len(df)):
                close_price = df.iloc[i]["Close"]
                # Entry Condition: Significant pullback (e.g., -0.005)
           
                if entry_price is None and df.iloc[i]["MicroPullback"]:
                    entry_price = close_price
                    stop_loss = entry_price * 0.98  # 2% Stop Loss
                    target_price = entry_price * 1.02  # 8% Take Profit
                    buy_date = df.iloc[i]["Date"]
                    transactions.append((buy_date, ticker, 'BUY', entry_price))

                # Exit Conditions
                if entry_price and close_price >= target_price:
                    exit_price = close_price
                    sell_date = df.iloc[i]["Date"]
                    transactions.append((sell_date, ticker, 'SELL', exit_price))
                      
                   

                if entry_price and close_price <= stop_loss:
                    exit_price = close_price
                    sell_date = df.iloc[i]["Date"]
                    transactions.append((sell_date, ticker, 'SELL', exit_price))
                    
                    
                # Record trade performance
                if entry_price and exit_price:
                    date_stats[date][ticker] = {
                        "return": (exit_price - entry_price) / entry_price,
                        "buy_date": buy_date,
                        "sell_date": sell_date
                    }
                    entry_price = None
                    exit_price = None
                    target_price = None
                    stop_loss = None
                    buy_date = None
                    sell_date = None
          
            #update the dataframe 
            app.data[reqID] = df
            reqID += 1

    return date_stats, transactions



def plot_trades(data, transactions):
    """Plot stock price using mplfinance and show Buy/Sell markers with Volume and VWAP."""
    for reqId in data:
        df = data[reqId].copy()
        
        if df.empty:
            continue
        
        # Convert 'Date' column to datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'].str.split(' ').str[0] + ' ' + df['Date'].str.split(' ').str[1], format='%Y%m%d %H:%M:%S')
        df.set_index('Date', inplace=True)
        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')

        df = df[['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP']]  # Include VWAP for plotting

        # Create markers for Buy and Sell
        buy_signals = []
        sell_signals = []
        
        for trans in transactions:
            date, ticker, action, price = trans
            
            if reqId in data and not df.empty:
                # Parse transaction date
                try:
                    trans_date_str = date.split(' ')[0] + ' ' + date.split(' ')[1]  # "20240325 09:55:00"
                    trans_date = datetime.strptime(trans_date_str, "%Y%m%d %H:%M:%S")
                except Exception as e:
                    print(f"Error parsing date {date}: {e}")
                    continue

                if trans_date in df.index:  # Ensure the timestamp exists in the dataframe
                    if action == 'BUY':
                        buy_signals.append((trans_date, price))
                    elif action == 'SELL':
                        sell_signals.append((trans_date, price))
        
        # Prepare additional plots for Buy/Sell markers and VWAP
        apds = []
        if buy_signals:
            buy_dates, buy_prices = zip(*buy_signals) if buy_signals else ([], [])
            buy_series = pd.Series(buy_prices, index=pd.to_datetime(buy_dates)).reindex(df.index, method=None).fillna(np.nan)
            apds.append(mpf.make_addplot(buy_series, scatter=True, markersize=100, marker='v', color='g'))  # Green for Buy
        
        if sell_signals:
            sell_dates, sell_prices = zip(*sell_signals) if sell_signals else ([], [])
            sell_series = pd.Series(sell_prices, index=pd.to_datetime(sell_dates)).reindex(df.index, method=None).fillna(np.nan)
            apds.append(mpf.make_addplot(sell_series, scatter=True, markersize=100, marker='^', color='r'))  # Red for Sell
        
        # Add VWAP line to the plot
        apds.append(mpf.make_addplot(df['VWAP'], color='blue',  label='VWAP'))

        # Plot the chart using mplfinance
        mpf.plot(
            df, 
            type='candle', 
            style='charles', 
            title=f'Stock Price with Trades and VWAP (ReqId: {reqId})', 
            ylabel='Price', 
            volume=True,  # Include volume in the plot
            addplot=apds, 
            datetime_format='%Y-%m-%d %H:%M',  # Format x-axis as datetime
            xrotation=45  # Rotate x-axis labels for better readability
        )
date_stats, transactions = backtest(selected_stocks, app)

# Print transactions
def calculate_win_rate(transactions):
    """Calculate the win rate based on transactions."""
    wins = 0
    total_trades = 0

    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            total_trades += 1
            if sell_price > buy_price:  # Check if the trade was profitable
                wins += 1

    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    return win_rate

# Print transactions
for trans in transactions:
    print(f"Date: {trans[0]} | Ticker: {trans[1]} | Action: {trans[2]} | Price: {trans[3]:.2f}")

# Calculate and print win rate
win_rate = calculate_win_rate(transactions)


def calculate_total_profit(transactions):
    """Calculate the total profit based on transactions."""
    total_profit = 0
    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            total_profit += (sell_price - buy_price)
    return total_profit


def calculate_average_trade_return(transactions):
    """Calculate the average return per trade."""
    total_return = 0
    total_trades = 0

    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            total_return += (sell_price - buy_price) / buy_price
            total_trades += 1

    avg_return = (total_return / total_trades) * 100 if total_trades > 0 else 0
    return avg_return


# Calculate and print total profit and average trade return
total_profit = calculate_total_profit(transactions)
average_trade_return = calculate_average_trade_return(transactions)

print(f"Total Profit: {total_profit:.2f}")
print(f"Win Rate: {win_rate:.2f}%")
print(f"Average Trade Return: {average_trade_return:.2f}%")

# Plot trades after backtest is completed
plot_trades(app.data, transactions)