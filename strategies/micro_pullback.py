from data.data_fetcher import histData, usTechStk
import pandas as pd
from typing import Dict, List, Tuple
import threading


def backtest(
    selected_stocks: Dict[str, List[str]], 
    app, 
    ticker_event: threading.Event
) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], List[Tuple[str, str, str, float]]]:
    """
    Backtest a micro pullback strategy with strict trade closure before a new one starts.
    """

    date_stats = {}
    transactions = []
    reqID = 1000
    
    for date in selected_stocks.keys():
        date_stats[date] = {}
        for ticker in selected_stocks[date]:
            ticker_event.clear()  # Clear event before request
            histData(app, reqID, usTechStk(ticker), date + " 22:05:00 US/Eastern", '10 D', '1 min')
            ticker_event.wait()  # Wait for data retrieval

            if reqID not in app.data or app.data[reqID].empty:
                print(f"Warning: No data for {ticker} on {date}")
                continue
            
            df = app.data[reqID].copy()
            df['Volume'] = df['Volume'].astype(float)  # Ensure all volume values are float

            df['Green'] = df['Close'] > df['Open']
            df['Momentum'] = df['Green'] & df['Green'].shift(1) & df['Green'].shift(2)
            df['Pullback'] = df['Close'] < df['Close'].shift(1)

            df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['Cumulative_PV'] = (df['Typical_Price'] * df['Volume']).cumsum()
            df['Cumulative_Volume'] = df['Volume'].cumsum()
            df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']

            df['PullbackAboveVWAP'] = df['Pullback'] & (df['Low'] > df['VWAP'])
            df['AverageVolume'] = df['Volume'].rolling(window=200).mean()

            df['Extended'] = df['Close'] > df['VWAP'] * 1.03
            df['VolumeSpike'] = df['Volume'] > df['AverageVolume'] * 1.5
            df['MicroPullback'] = df['Momentum'].shift(1) & df['PullbackAboveVWAP'] & df['VolumeSpike'] & df['Extended']

            df.dropna(inplace=True)

            in_position = False  # Track if a trade is open
            entry_price, stop_loss, target_price = None, None, None
            buy_date, sell_date = None, None

            for i in range(len(df)):
                close_price = df.iloc[i]["Close"]

                # **Entry Condition**: Check if no position is open
                if not in_position and df.iloc[i]["MicroPullback"]:
                    entry_price = close_price
                    stop_loss = entry_price * 0.98  # 2% Stop Loss
                    target_price = entry_price * 1.02  # 2% Take Profit
                    buy_date = df.iloc[i]["Date"]

                    transactions.append((buy_date, ticker, 'BUY', entry_price))
                    in_position = True  # Mark position as open

                # **Exit Conditions**: Close trade before opening a new one
                if in_position:
                    if close_price >= target_price or close_price <= stop_loss:
                        exit_price = close_price
                        sell_date = df.iloc[i]["Date"]
                        transactions.append((sell_date, ticker, 'SELL', exit_price))

                        # **Record trade stats**
                        date_stats[date][ticker] = {
                            "return": (exit_price - entry_price) / entry_price,
                            "buy_date": buy_date,
                            "sell_date": sell_date
                        }

                        # Reset trade state before a new one can start
                        in_position = False
                        entry_price, stop_loss, target_price = None, None, None
                        buy_date, sell_date = None, None

            app.data[reqID] = df  # Store processed DataFrame
            reqID += 1

    return date_stats, transactions