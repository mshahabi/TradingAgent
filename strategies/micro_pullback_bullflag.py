import threading
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd

from data.data_fetcher import histData, usTechStk
from utils import compute_daily_vwap


# bull flag strategy
def backtest(
    selected_stocks: Dict[str, List[str]], app, ticker_event: threading.Event
) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], List[Tuple[str, str, str, float]]]:
    """
    Backtest a combined micro pullback and bull flag strategy ensuring strong volume, momentum, and clean setups.
    """

    date_stats = {}
    transactions = []
    reqID = 1000

    for date in selected_stocks.keys():
        date_stats[date] = {}
        for ticker in selected_stocks[date]:
            ticker_event.clear()
            histData(
                app,
                reqID,
                usTechStk(ticker),
                date + " 22:05:00 US/Eastern",
                "10 D",
                "5 mins",
            )
            ticker_event.wait()

            if reqID not in app.data or app.data[reqID].empty:
                print(f"Warning: No data for {ticker} on {date}")
                continue

            df = app.data[reqID].copy()
            df["Volume"] = df["Volume"].astype(float)
            df["DateTime"] = df["Date"].apply(
                lambda date: datetime.strptime(
                    date.split(" ")[0] + " " + date.split(" ")[1], "%Y%m%d %H:%M:%S"
                )
            )

            df["DateOnly"] = df["DateTime"].dt.date

            df_vwap = (
                df.groupby("DateOnly").apply(compute_daily_vwap).reset_index(drop=True)
            )
            df = df.merge(df_vwap, on="DateTime", how="left")

            # === Micro Pullback Setup ===
            df["Green"] = df["Close"] > df["Open"]
            df["StrongMomentum"] = (
                (df["Green"])
                & (df["Close"] > df["Close"].shift(1) * 1.002)
                & (df["Close"].shift(1) > df["Close"].shift(2) * 1.002)
            )
            df["ATR"] = df["High"].rolling(14).max() - df["Low"].rolling(14).min()
            df["Momentum"] = df["StrongMomentum"] & (
                (df["High"] - df["Low"]) > 0.5 * df["ATR"]
            )
            df["Pullback"] = df["Close"] < df["Close"].shift(1)
            df["PullbackAboveVWAP"] = df["Pullback"] & (df["Low"] > df["VWAP"])
            df["AverageVolume"] = df["Volume"].rolling(window=200).mean()
            df["RelativeVolume"] = df["Volume"] / df["AverageVolume"]
            df["Close_to_VWAP"] = df["Close"] / df["VWAP"]
            df["NotExtended"] = df["Close_to_VWAP"] < 1.05
            df["VWAP_Reclaim"] = (df["Low"] > df["VWAP"]) & (df["Close"] > df["VWAP"])
            df["VolumeSpike"] = df["RelativeVolume"] > 1.4

            df["MicroPullback"] = (
                df["Momentum"].shift(1)
                & df["PullbackAboveVWAP"]
                & df["NotExtended"]
                & df["VWAP_Reclaim"]
                & df["VolumeSpike"]
            )

            # === Bull Flag Setup ===
            df["PriceChange"] = df["Close"] / df["Close"].shift(5)
            df["FlagPole"] = df["PriceChange"] > 1.03  # 3% in 5 candles
            df["Consolidation"] = (
                (df["High"].rolling(3).max() - df["Low"].rolling(3).min())
                < 0.015 * df["Close"]
            ) & (df["Close"] < df["Close"].shift(1))
            df["Breakout"] = (df["Close"] > df["High"].rolling(5).max().shift(1)) & (
                df["RelativeVolume"] > 1.5
            )
            df["BullFlag"] = (
                df["FlagPole"].shift(3) & df["Consolidation"] & df["Breakout"]
            )

            df.dropna(inplace=True)

            # === Simulate Trades ===
            in_position = False
            entry_price, stop_loss, target_price = None, None, None
            buy_date, sell_date = None, None

            for i in range(len(df)):
                close_price = df.iloc[i]["Close"]

                if not in_position:
                    if df.iloc[i]["MicroPullback"] or df.iloc[i]["BullFlag"]:
                        entry_price = close_price
                        stop_loss = entry_price * 0.98
                        target_price = entry_price * 1.08
                        buy_date = df.iloc[i]["Date"]
                        strategy = (
                            "MicroPullback"
                            if df.iloc[i]["MicroPullback"]
                            else "BullFlag"
                        )
                        transactions.append(
                            (buy_date, ticker, f"BUY_{strategy}", entry_price)
                        )
                        in_position = True

                if in_position:
                    if close_price >= target_price or close_price <= stop_loss:
                        exit_price = close_price
                        sell_date = df.iloc[i]["Date"]
                        transactions.append((sell_date, ticker, "SELL", exit_price))

                        date_stats[date][ticker] = {
                            "return": (exit_price - entry_price) / entry_price,
                            "buy_date": buy_date,
                            "sell_date": sell_date,
                        }

                        in_position = False
                        entry_price, stop_loss, target_price = None, None, None
                        buy_date, sell_date = None, None

            app.data[reqID] = df
            reqID += 1

    return date_stats, transactions
