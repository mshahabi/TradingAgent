import numpy as np
import pandas as pd
import ta  # Technical Analysis library
from sklearn.linear_model import LinearRegression


def compute_slope(series: pd.Series) -> float:
    """Compute slope of a serires using linear regression."""
    y = series.values.reshape(-1, 1)
    x = np.arange(len(series)).reshape(-1, 1)
    model = LinearRegression().fit(x, y)
    return model.coef_[0][0]


def compute_choppiness_index(high, low, close, window=14):
    """Calculate choppiness index: lower = trending, higher = choppy"""
    # tr: Captures how much price moved including any gaps from the previous close.
    tr = np.maximum(
        high - low, np.maximum(abs(high - close.shift(1)), abs(low - close.shift(1)))
    )
    atr = pd.Series(tr).rolling(window=window).sum()
    high_max = high.rolling(window=window).max()
    low_min = low.rolling(window=window).min()
    choppiness = 100 * np.log10(atr / (high_max - low_min)) / np.log10(window)
    return choppiness


def compute_micro_pullback_ema_strategy(
    df,
    threshold=0.001,
    volume_spike_factor=4,
    volume_window=80,
    slope_window=10,
    slope_threshold=0.002,
    choppiness_threshold=61,
    adx_threshold=20,
    breakout_window=10,
):
    """
    Enhanced micro pullback strategy with choppiness index, breakout confirmation, ADX.
    """

    df = df.copy()

    # === EMAs ===
    df["EMA4"] = df["Close"].ewm(span=4, adjust=False).mean()
    df["EMA7"] = df["Close"].ewm(span=7, adjust=False).mean()
    df["EMA15"] = df["Close"].ewm(span=15, adjust=False).mean()

    # === Crossovers ===
    df["EMA4_cross_EMA7"] = (df["EMA4"].shift(2) <= df["EMA7"].shift(2)) & (
        df["EMA4"].shift(1) > df["EMA7"].shift(1)
    )
    df["EMA4_cross_EMA15"] = (df["EMA4"] > df["EMA15"]) & (df["EMA7"] > df["EMA15"])
    df["PreSignal"] = df["EMA4_cross_EMA7"] & df["EMA4_cross_EMA15"]

    # === Candle & Volume Filters ===
    df["GreenCandle"] = df["Close"] > df["Open"]
    df["AvgVolume"] = df["Volume"].rolling(window=volume_window).mean()
    df["VolumeSpike"] = (df["Volume"] > df["AvgVolume"] * volume_spike_factor) & (
        df["Volume"] > 15000
    )
    df["EMA4_pct_change"] = df["EMA4"].pct_change()

    # === EMA Slope ===
    df["EMA15_Slope"] = (
        df["EMA15"].rolling(window=slope_window).apply(compute_slope, raw=False)
    )

    # === Trend Strength Filters ===
    df["ChoppinessIndex"] = compute_choppiness_index(df["High"], df["Low"], df["Close"])
    df["ADX"] = ta.trend.adx(df["High"], df["Low"], df["Close"], window=15)

    # === Breakout Filter ===
    df["RecentHigh"] = df["High"].rolling(breakout_window).max().shift(1)
    df["BreakoutConfirm"] = df["High"] > df["RecentHigh"]

    # === Strong Close ===
    df["StrongClose"] = df["Close"] > (df["Open"] + 0.5 * (df["High"] - df["Low"]))

    # === Final Buy Signal ===
    df["EMABuySignal"] = (
        df["PreSignal"]
        & (df["EMA4_pct_change"] >= threshold)
        & df["GreenCandle"]
        & df["VolumeSpike"]
        & (df["EMA15_Slope"] > slope_threshold)
        & (df["ChoppinessIndex"] < choppiness_threshold)
        & (df["ADX"] > adx_threshold)
        & df["BreakoutConfirm"]
        & df["StrongClose"]
    )

    return df[
        [
            "DateTime",
            "EMA4",
            "EMA7",
            "EMA15",
            "EMA4_pct_change",
            "EMA15_Slope",
            "ChoppinessIndex",
            "ADX",
            "BreakoutConfirm",
            "StrongClose",
            "EMABuySignal",
        ]
    ]
