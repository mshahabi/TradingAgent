import pandas as pd


def compute_micro_pullback(
    df: pd.DataFrame,
    atr_window=15,
    volume_window=80,
    rel_volume_thresh=5,
    vol_thresh=15000,
    max_pullback_pct=0.015,
):
    """
    Identifies Micro Pullback patterns in the provided DataFrame.

    Parameters:
        df (pd.DataFrame): DataFrame with 'Open', 'High', 'Low', 'Close', 'Volume', and 'VWAP' columns.
        atr_window (int): Rolling window for ATR calculation.
        volume_window (int): Rolling window for average volume.
        rel_volume_thresh (float): Relative volume threshold to detect volume spike.
        vol_thresh (int): Minimum absolute volume threshold.
        max_pullback_pct (float): Maximum % pullback for valid pullback detection.

    Returns:
        pd.DataFrame: Original DataFrame with extra columns indicating pattern detections.
    """

    df = df.copy()

    # Momentum check
    df["Green"] = df["Close"] > df["Open"]
    df["StrongMomentum"] = (
        df["Green"].shift(1).fillna(False)
        & df["Green"].shift(2).fillna(False)
        & df["Green"].shift(3).fillna(False)
        & (df["High"].shift(1) > df["High"].shift(2))
        & (df["High"].shift(2) > df["High"].shift(3))
    )

    # ATR and momentum confirmation
    df["ATR"] = (
        df["High"].rolling(atr_window).max() - df["Low"].rolling(atr_window).min()
    )
    df["Momentum"] = df["StrongMomentum"] & ((df["High"] - df["Low"]) > 0.4 * df["ATR"])

    # Pullback logic
    df["Pullback"] = (df["Close"] < df["Close"].shift(1)) & (
        (df["Close"].shift(1) - df["Close"]) / df["Close"].shift(1) <= max_pullback_pct
    )
    df["PullbackAboveVWAP"] = df["Pullback"] & (df["Low"] > df["VWAP"])

    # Volume filters
    df["AverageVolume"] = df["Volume"].rolling(window=volume_window).mean()
    df["RelativeVolume"] = df["Volume"] / df["AverageVolume"]
    df["Close_to_VWAP"] = df["Close"] / df["VWAP"]
    df["NotExtended"] = df["Close_to_VWAP"] < 5

    # VWAP reclaim and spike
    df["VWAP_Reclaim"] = (df["Low"] > df["VWAP"]) & (df["Close"] > df["VWAP"])
    df["VolumeSpike"] = (df["RelativeVolume"] > rel_volume_thresh) & (
        df["Volume"] > vol_thresh
    )

    # Final micro pullback signal
    df["MicroPullback"] = df["StrongMomentum"] & df["Pullback"] & df["VolumeSpike"]

    return df[["MicroPullback", "DateTime"]]
