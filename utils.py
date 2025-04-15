import pandas as pd
import numpy as np
import mplfinance as mpf
from datetime import datetime
from pytz import timezone
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def calculate_profit_by_entry_type(transactions):
    """
    Calculate the profit percentage for each entry type.

    Args:
        transactions (list of tuple): A list of transactions where each transaction 
            is represented as a tuple in the format 
            (date, ticker, action, price, entry_type).

    Returns:
        dict: A dictionary where keys are entry types and values are the profit percentages.
    """
    entry_type_profits = {}
    entry_type_counts = {}

    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2].split(" ")[0] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            entry_type = transactions[i][4]

            profit_pct = ((sell_price - buy_price) / buy_price) * 100

            if entry_type not in entry_type_profits:
                entry_type_profits[entry_type] = 0
                entry_type_counts[entry_type] = 0

            entry_type_profits[entry_type] += profit_pct
            entry_type_counts[entry_type] += 1

    # Calculate average profit percentage for each entry type
    for entry_type in entry_type_profits:
        entry_type_profits[entry_type] /= entry_type_counts[entry_type]

    return entry_type_profits
# Print transactions
def calculate_win_rate(transactions):
    """
    Calculate the win rate for each strategy and the overall win rate.

    This function processes a list of transactions, where each transaction is 
    represented as a tuple. It pairs BUY and SELL transactions, calculates the 
    number of profitable trades for each strategy, and determines the win rate 
    as a percentage for each strategy and overall.

    Args:
        transactions (list of tuple): A list of transactions where each transaction 
            is represented as a tuple in the format (id, timestamp, type, price, strategy). 
            The 'type' field should be either 'BUY' or 'SELL'.

    Returns:
        dict: A dictionary containing the win rate for each strategy and the overall win rate.
    """
    strategy_wins = {}
    strategy_total_trades = {}
    overall_wins = 0
    overall_total_trades = 0

    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2].split(" ")[0] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            strategy = transactions[i][4]
            overall_total_trades += 1

            if strategy not in strategy_wins:
                strategy_wins[strategy] = 0
                strategy_total_trades[strategy] = 0

            strategy_total_trades[strategy] += 1
            if sell_price > buy_price:  # Check if the trade was profitable
                strategy_wins[strategy] += 1
                overall_wins += 1

    # Calculate win rates
    strategy_win_rates = {
        strategy: (strategy_wins[strategy] / strategy_total_trades[strategy]) * 100
        for strategy in strategy_wins
    }
    overall_win_rate = (overall_wins / overall_total_trades) * 100 if overall_total_trades > 0 else 0

    return {
        "strategy_win_rates": strategy_win_rates,
        "overall_win_rate": overall_win_rate
    }

def calculate_total_profit(transactions):
    """Calculate the total profit based on transactions."""
    total_profit = 0
    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2].split(" ")[0] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            total_profit += (sell_price - buy_price)
    return total_profit


def calculate_average_trade_return(transactions):
    """Calculate the average return per trade."""
    total_return = 0
    total_trades = 0

    for i in range(0, len(transactions), 2):  # Pair BUY and SELL transactions
        if i + 1 < len(transactions) and transactions[i][2].split(" ")[0] == 'BUY' and transactions[i + 1][2] == 'SELL':
            buy_price = transactions[i][3]
            sell_price = transactions[i + 1][3]
            total_return += (sell_price - buy_price) / buy_price
            total_trades += 1

    avg_return = (total_return / total_trades) * 100 if total_trades > 0 else 0
    return avg_return, total_trades

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

import pandas as pd
from collections import defaultdict

def analyze_losing_trade_patterns(transactions, df_data):
    """
    Analyze losing trades to determine why they failed.
    
    Args:
        transactions (List[Tuple[str, str, str, float]]): 
            List of (date, ticker, action, price) tuples.
        df_data (Dict[str, pd.DataFrame]): 
            Dictionary containing historical data for each ticker.

    Returns:
        pd.DataFrame: A DataFrame showing reasons for failure.
    """
    trade_log = defaultdict(lambda: {"buy_price": None, "sell_price": None})
    losing_trades_analysis = []

    for date, ticker, action, price in transactions:
        if action == "BUY":
            trade_log[ticker]["buy_price"] = price
        elif action == "SELL" and trade_log[ticker]["buy_price"]:
            buy_price = trade_log[ticker]["buy_price"]
            return_pct = (price - buy_price) / buy_price

            if return_pct < 0:  # Losing trade
                df = df_data.get(ticker, pd.DataFrame())

                # Find the row corresponding to the buy date
                trade_row = df[df["Date"] == date]
                if trade_row.empty:
                    continue
                
                trade_row = trade_row.iloc[0]  # Get the first row if multiple exist
                
                # Analyze failure reasons
                failed_conditions = []

                if trade_row["RelativeVolume"] < 1:
                    failed_conditions.append("Low Relative Volume")
                
                if not trade_row["Momentum"]:
                    failed_conditions.append("Weak Momentum")
                
                if trade_row["PullbackAboveVWAP"] == False:
                    failed_conditions.append("Pullback Below VWAP")
                
                if trade_row["Extended"]:
                    failed_conditions.append("Stock Too Extended Above VWAP")
                
                if trade_row["VWAP"] > buy_price:
                    failed_conditions.append("Entered Below VWAP")

                # Store analysis
                losing_trades_analysis.append({
                    "date": date,
                    "ticker": ticker,
                    "buy_price": buy_price,
                    "sell_price": price,
                    "return_pct": return_pct * 100,
                    "failure_reasons": ", ".join(failed_conditions)
                })

            # Reset trade log after trade completion
            trade_log[ticker]["buy_price"] = None

    # Convert to DataFrame for analysis
    df_losing_analysis = pd.DataFrame(losing_trades_analysis)

    if df_losing_analysis.empty:
        print("No losing trades found.")
        return df_losing_analysis

    # Summary Stats
    print("\n🔎 Losing Trade Analysis")
    print(df_losing_analysis.groupby("failure_reasons").size().reset_index(name="count"))

    return df_losing_analysis


def compute_daily_vwap(df):
    df = df.copy()
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    df['Cumulative_PV'] = (df['Typical_Price'] * df['Volume']).cumsum()
    df['Cumulative_Volume'] = df['Volume'].cumsum()
    df['VWAP'] = df['Cumulative_PV'] / df['Cumulative_Volume']
    return df[['DateTime', 'VWAP']] 



def plot_trades_plotly(data, transactions, strategy_filter=None):
    """Plot stock price using Plotly, show Buy/Sell markers, Volume, and VWAP, with Relative Volume on secondary y-axis.
    
    Args:
        data (dict): Dictionary of dataframes containing stock data.
        transactions (list): List of transactions (date, ticker, action, price, entry_type).
        strategy_filter (str, optional): Filter to show trades for a specific strategy type. Defaults to None.
    """
    for reqId in data:
        df = data[reqId].copy()
        if df.empty:
            continue

        # Parse date without timezone
        df['Date'] = df['Date'].astype(str).str.extract(r'(\d{8} \d{2}:\d{2}:\d{2})')[0]
        df['Date'] = pd.to_datetime(df['Date'], format='%Y%m%d %H:%M:%S', errors='coerce')
        df.dropna(subset=['Date'], inplace=True)
        df.sort_values('Date', inplace=True)

        df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
        df['AverageVolume'] = df['Volume'].rolling(window=80).mean()
        df['RelativeVolume'] = df['Volume'] / df['AverageVolume']

        # Calculate Exponential Moving Averages (EMAs)
        df['EMA_3'] = df['Close'].ewm(span=3, adjust=False).mean()
        df['EMA_5'] = df['Close'].ewm(span=5, adjust=False).mean()
        df['EMA_10'] = df['Close'].ewm(span=10, adjust=False).mean()

        buy_x, buy_y, buy_hover, sell_x, sell_y, sell_hover = [], [], [], [], [], []
        for trans in transactions:
            t_date_str, ticker, action, price, entry_type = trans

            # Apply strategy filter if provided
            if strategy_filter and entry_type != strategy_filter:
                continue

            try:
                t_date_str = ' '.join(t_date_str.split(' ')[:2])  # Remove timezone part
                t_date = datetime.strptime(t_date_str, "%Y%m%d %H:%M:%S")
                nearest_idx = (df['Date'] - t_date).abs().idxmin()
                x_val = df.loc[nearest_idx, 'Date']
                y_val = price
                if action.split(" ")[0] == 'BUY':
                    buy_x.append(x_val)
                    buy_y.append(y_val)
                    buy_hover.append(f"Buy<br>Entry Type: {entry_type}")
                elif action == 'SELL':
                    sell_x.append(x_val)
                    sell_y.append(y_val)
                    sell_hover.append(f"Sell<br>Entry Type: {entry_type}")
            except Exception as e:
                print(f"Error parsing transaction {trans}: {e}")

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05,
            row_heights=[0.7, 0.3],
            specs=[[{"secondary_y": False}], [{"secondary_y": True}]]
        )

        # Candlesticks
        fig.add_trace(go.Candlestick(
            x=df['Date'],
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
        ), row=1, col=1)

        # VWAP line
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['VWAP'],
            mode='lines',
            name='VWAP',
            line=dict(color='blue'),
        ), row=1, col=1)

        # EMA lines
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_3'],
            mode='lines',
            name='EMA 3',
            line=dict(color='purple', dash='solid'),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_5'],
            mode='lines',
            name='EMA 5',
            line=dict(color='green', dash='dot'),
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['EMA_10'],
            mode='lines',
            name='EMA 10',
            line=dict(color='orange', dash='dash'),
        ), row=1, col=1)

        # Volume bars
        colors = ['green' if row['Open'] - row['Close'] >= 0 
                  else 'red' for index, row in df.iterrows()]
        fig.add_trace(go.Bar(
            x=df['Date'],
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ), row=2, col=1, secondary_y=False)

        # Relative Volume as a line on secondary y-axis
        fig.add_trace(go.Scatter(
            x=df['Date'],
            y=df['RelativeVolume'],
            mode='lines',
            name='Relative Volume',
            line=dict(color='orange', dash='dot'),
        ), row=2, col=1, secondary_y=True)

        # Buy markers
        if buy_x:
            fig.add_trace(go.Scatter(
                x=buy_x,
                y=buy_y,
                mode='markers',
                name='Buy',
                marker=dict(symbol='triangle-down', color='green', size=12),
                hovertext=buy_hover,
                hoverinfo="text"
            ), row=1, col=1)

        # Sell markers
        if sell_x:
            fig.add_trace(go.Scatter(
                x=sell_x,
                y=sell_y,
                mode='markers',
                name='Sell',
                marker=dict(symbol='triangle-up', color='red', size=12),
                hovertext=sell_hover,
                hoverinfo="text"
            ), row=1, col=1)

        # Layout
        fig.update_layout(
            title=f"Stock Price with Trades, VWAP, EMAs, and Relative Volume (Ticker: {ticker})",
            hovermode='x unified',
            spikedistance=1000,
            xaxis=dict(
                type="date",
                showgrid=True,
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                spikecolor='grey',
                spikethickness=1,
                gridcolor='rgba(128,128,128,0.2)',
                rangeslider_visible=False,
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(bounds=[20, 4], pattern="hour")
                ]
            ),
            yaxis=dict(
                title='Price',
                showgrid=True,
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                spikecolor='grey',
                spikethickness=1,
                gridcolor='rgba(128,128,128,0.2)',
            ),
            yaxis2=dict(
                title='Volume',
                showgrid=True,
                showspikes=True,
                spikemode='across',
                spikesnap='cursor',
                spikecolor='grey',
                spikethickness=1,
                gridcolor='rgba(128,128,128,0.2)',
                tickformat=',.0f'
            ),
            yaxis3=dict(
                title='Relative Volume',
                overlaying='y2',
                side='right',
                showgrid=False,
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            legend=dict(orientation='h', y=1.02, x=1, xanchor='right'),
            height=800
        )

        fig.update_layout(xaxis_rangeslider_visible=False)

        fig.show()
