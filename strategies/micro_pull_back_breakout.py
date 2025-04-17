import numpy as np
import pandas as pd


def compute_breakout_signal(
    df, breakout_multiplier=1.0, vwap_multiplier=1.1, rsi_overbought=85
):
    """
    Compute breakout signal based on strong candle breakout with volatility and trend confirmation.
    Filters out 'buying the top' behavior with RSI and VWAP extension filters.
    """

    df = df.copy()

    # Small red candle allowance in trend
    def increasing_trend_with_one_small_red(df):
        small_reds = (df["Close"] < df["Open"]) & (
            abs(df["Open"] - df["Close"]) / df["Open"] < 0.008
        )
        return small_reds.rolling(window=5).sum().shift(1) <= 1

    df["AllowTrend"] = increasing_trend_with_one_small_red(df)

    # Candle body strength
    df["Body"] = abs(df["Close"] - df["Open"])
    df["Range"] = df["High"] - df["Low"]
    df["StrongBreakoutCandle"] = (df["Body"] / df["Range"]) > 0.8

    # Volatility filter
    df["ATR"] = (df["High"] - df["Low"]).rolling(window=10).mean()
    df["SufficientVolatility"] = df["ATR"] > df["ATR"].median()

    # Previous local high for breakout comparison
    df["PrevHigh5"] = df["High"].rolling(window=5).max().shift(1)

    # RSI for overbought filter
    delta = df["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()
    rs = gain / (loss + 1e-10)
    df["RSI"] = 100 - (100 / (1 + rs))

    # Final breakout signal
    df["Breakout"] = (
        (df["Close"] > df["PrevHigh5"] * breakout_multiplier)
        & (
            df["Close"] < df["VWAP"] * vwap_multiplier
        )  # Prevent buying extreme extensions
        & (df["RSI"] < rsi_overbought)
        & df["VolumeSpike"]
        & df["StrongBreakoutCandle"]
        & df["AllowTrend"]
        & df["SufficientVolatility"]
    )

    return df[
        [
            "DateTime",
            "PrevHigh5",
            "RSI",
            "StrongBreakoutCandle",
            "AllowTrend",
            "SufficientVolatility",
            "Breakout",
        ]
    ]
