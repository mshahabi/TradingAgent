import threading
from datetime import datetime
from typing import Dict, List, Tuple

import pandas as pd

from data.data_fetcher import histData, usTechStk
from utils import compute_daily_vwap


def backtest(selected_stocks, app, ticker_event):
    from datetime import datetime

    from utils import compute_daily_vwap

    date_stats = {}
    transactions = []
    reqID = 1000

    for date in selected_stocks:
        date_stats[date] = {}

        for ticker in selected_stocks[date]:
            ticker_event.clear()
            histData(
                app,
                reqID,
                usTechStk(ticker),
                date + " 22:05:00 US/Eastern",
                "10 D",
                "1 min",
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

            # === Micro Pullback Indicators ===
            df["Green"] = df["Close"] > df["Open"]
            df["StrongMomentum"] = (
                df["Green"]
                & (df["Close"] > df["Close"].shift(1) * 1.003)
                & (df["Close"].shift(1) > df["Close"].shift(2) * 1.003)
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
            df["NotExtended"] = df["Close_to_VWAP"] > 1.05
            df["VWAP_Reclaim"] = (df["Low"] > df["VWAP"]) & (df["Close"] > df["VWAP"])
            df["VolumeSpike"] = df["RelativeVolume"] > 1.4

            # Micro Pullback Score
            df["MicroPullbackScore"] = (
                df["Momentum"].shift(1)
                + df["PullbackAboveVWAP"]
                + df["VWAP_Reclaim"]
                + df["VolumeSpike"]
            )

            # === Trend Following / Breakout Indicators ===
            df["EMA9"] = df["Close"].ewm(span=9).mean()
            df["EMA21"] = df["Close"].ewm(span=21).mean()
            df["EMA50"] = df["Close"].ewm(span=50).mean()
            df["ShortUp"] = df["EMA9"] > df["EMA21"]
            df["LongUp"] = df["EMA21"] > df["EMA50"]
            df["Breakout"] = df["Close"] > df["High"].rolling(20).max().shift(1)

            df["TrendScore"] = (
                df["ShortUp"].astype(int)
                + df["LongUp"].astype(int)
                + df["Breakout"].astype(int)
                + df["VolumeSpike"].astype(int)
            )

            df.dropna(inplace=True)

            in_position = False
            entry_price, stop_loss, target_price = None, None, None
            buy_date, sell_date = None, None

            for i in range(len(df)):
                row = df.iloc[i]
                close_price = row["Close"]

                if not in_position:
                    if row["MicroPullbackScore"] >= 3 or row["TrendScore"] >= 3:
                        if row["MicroPullbackScore"] >= row["TrendScore"]:
                            strategy = "MicroPullback"
                        else:
                            strategy = "TrendBreakout"

                        entry_price = close_price
                        stop_loss = entry_price * 0.98
                        target_price = entry_price * 1.05
                        buy_date = row["Date"]
                        transactions.append(
                            (buy_date, ticker, f"BUY ({strategy})", entry_price)
                        )
                        in_position = True

                else:
                    if close_price >= target_price or close_price <= stop_loss:
                        exit_price = close_price
                        sell_date = row["Date"]
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
