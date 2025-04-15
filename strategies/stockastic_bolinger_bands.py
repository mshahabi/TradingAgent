import pandas as pd
import numpy as np
from typing import Dict, List, Tuple

def compute_stochastic_bollinger_band(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()

    # ====== Technical Indicators ======
    # Stochastic Oscillator
    high_14 = data['High'].rolling(window=14).max()
    low_14 = data['Low'].rolling(window=14).min()
    data['%K'] = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
    data['%D'] = data['%K'].rolling(window=3).mean()

    # Bollinger Bands
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['STD20'] = data['Close'].rolling(window=20).std()
    data['UpperBB'] = data['MA20'] + 2 * data['STD20']
    data['LowerBB'] = data['MA20'] - 2 * data['STD20']
    data['BB_Width'] = (data['UpperBB'] - data['LowerBB']) / data['MA20']  # relative BB width

    # RSI
    data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()

    # ADX
    adx = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close'], window=14)
    data['ADX'] = adx.adx()

    # Volume Spike
    data['avg_volume'] = data['Volume'].rolling(window=20).mean()
    data['volume_spike'] = data['Volume'] > 1.5 * data['avg_volume']

    # ====== Entry Conditions ======

    # %K crosses above 20 AND is accelerating upward
    data['StochCross'] = (data['%K'] > 20) & (data['%K'].shift(1) <= 20) & (data['%K'] > data['%K'].shift(1))

    # Bollinger recovery + band width not too narrow
    data['BB_Reversal'] = (data['Close'] > data['LowerBB']) & (data['BB_Width'] > 0.015)

    # Confirmed uptrend (price above 20-MA)
    data['Trend_OK'] = data['Close'] > data['MA20']

    # RSI above momentum threshold
    data['RSI_OK'] = data['RSI'] > 50

    # Trend strength using ADX
    data['StrongTrend'] = data['ADX'] > 20

    # Bullish candle confirmation (close near high AND strong body)
    candle_range = data['High'] - data['Low']
    candle_body = abs(data['Close'] - data['Open'])
    data['BullishCandle'] = (data['Close'] > data['Open']) & \
                            ((data['Close'] - data['Low']) > 0.6 * candle_range) & \
                            (candle_body > 0.5 * candle_range)

    # Final signal
    data['StochBollingerEntry'] = (
        data['StochCross'] &
        data['BB_Reversal'] &
        data['volume_spike'] &
        data['RSI_OK'] &
        data['Trend_OK'] &
        data['StrongTrend'] &
        data['BullishCandle']
    )

    return data[['DateTime', 'StochBollingerEntry']]