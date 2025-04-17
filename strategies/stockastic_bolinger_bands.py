from typing import Optional

import numpy as np
import pandas as pd
import ta


def compute_stochastic_bollinger_band(
    data: pd.DataFrame,
    volume_multiplier: float = 1.5,
    bb_width_threshold: float = 0.015,
    adx_threshold: float = 20,
    rsi_threshold: float = 30,
    atr_multiplier: float = 1.0,
) -> pd.DataFrame:
    data = data.copy()

    # ====== Technical Indicators ======
    high_14 = data["High"].rolling(window=14).max()
    low_14 = data["Low"].rolling(window=14).min()
    data["%K"] = 100 * ((data["Close"] - low_14) / (high_14 - low_14))
    data["%D"] = data["%K"].rolling(window=3).mean()

    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["STD20"] = data["Close"].rolling(window=20).std()
    data["UpperBB"] = data["MA20"] + 2 * data["STD20"]
    data["LowerBB"] = data["MA20"] - 2 * data["STD20"]
    data["BB_Width"] = (data["UpperBB"] - data["LowerBB"]) / data["MA20"]

    data["RSI"] = ta.momentum.RSIIndicator(data["Close"], window=14).rsi()
    adx = ta.trend.ADXIndicator(data["High"], data["Low"], data["Close"], window=14)
    data["ADX"] = adx.adx()
    atr = ta.volatility.AverageTrueRange(
        data["High"], data["Low"], data["Close"], window=14
    )
    data["ATR"] = atr.average_true_range()
    data["ATR_avg"] = data["ATR"].rolling(window=20).mean()

    data["avg_volume"] = data["Volume"].rolling(window=20).mean()
    data["volume_spike"] = data["Volume"] > volume_multiplier * data["avg_volume"]

    # ====== Candlestick Features ======
    candle_range = data["High"] - data["Low"]
    candle_body = abs(data["Close"] - data["Open"])
    data["BullishCandle"] = (
        (data["Close"] > data["Open"])
        & ((data["Close"] - data["Low"]) > 0.6 * candle_range)
        & (candle_body > 0.5 * candle_range)
    )

    # ====== Entry Conditions ======
    data["StochCross"] = (
        (data["%K"] > data["%D"])
        & (data["%K"].shift(1) <= data["%D"].shift(1))
        & (data["%K"] > data["%K"].shift(1))
    )

    data["BB_Reversal"] = (
        (data["Close"].shift(1) < data["LowerBB"].shift(1))
        & (data["Close"] > data["LowerBB"])
        & (data["BB_Width"] > bb_width_threshold)
    )

    data["BreakPrevHigh"] = data["Close"] > data["High"].shift(1)

    data["RSI_OK"] = data["RSI"] < rsi_threshold
    data["StrongTrend"] = data["ADX"] > adx_threshold
    data["Volatility_OK"] = data["ATR"] > atr_multiplier * data["ATR_avg"]

    data["StochBollingerEntry"] = (
        data["StochCross"]
        & data["BB_Reversal"]
        & data["volume_spike"]
        & data["RSI_OK"]
        & data["BreakPrevHigh"]
        & data["StrongTrend"]
        & data["Volatility_OK"]
        & data["BullishCandle"]
    )

    return data[["DateTime", "StochBollingerEntry"]]
