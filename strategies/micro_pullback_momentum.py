from data.data_fetcher import histData, usTechStk
from strategies.micro_pull_back_ema import compute_micro_pullback_ema_strategy
from strategies.micro_pull_back_breakout import compute_breakout_signal
from strategies.stockastic_bolinger_bands import compute_stochastic_bollinger_band
from strategies.micro_pullback import compute_micro_pullback

import pandas as pd
from typing import Dict, List, Tuple
import threading
from datetime import datetime
from utils import compute_daily_vwap
import ta
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from scipy.stats import entropy
import collections

# def compute_stochastic_bollinger_band(data: pd.DataFrame) -> pd.DataFrame:
#     data = data.copy()

#     # ====== Technical Indicators ======
#     # Stochastic Oscillator
#     high_14 = data['High'].rolling(window=14).max()
#     low_14 = data['Low'].rolling(window=14).min()
#     data['%K'] = 100 * ((data['Close'] - low_14) / (high_14 - low_14))
#     data['%D'] = data['%K'].rolling(window=3).mean()

#     # Bollinger Bands
#     data['MA20'] = data['Close'].rolling(window=20).mean()
#     data['STD20'] = data['Close'].rolling(window=20).std()
#     data['UpperBB'] = data['MA20'] + 2 * data['STD20']
#     data['LowerBB'] = data['MA20'] - 2 * data['STD20']
#     data['BB_Width'] = (data['UpperBB'] - data['LowerBB']) / data['MA20']  # relative BB width

#     # RSI
#     data['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()

#     # ADX
#     adx = ta.trend.ADXIndicator(data['High'], data['Low'], data['Close'], window=14)
#     data['ADX'] = adx.adx()

#     # Volume Spike
#     data['avg_volume'] = data['Volume'].rolling(window=20).mean()
#     data['volume_spike'] = data['Volume'] > 1.5 * data['avg_volume']

#     # ====== Entry Conditions ======

#     # %K crosses above 20 AND is accelerating upward
#     data['StochCross'] = (data['%K'] > 20) & (data['%K'].shift(1) <= 20) & (data['%K'] > data['%K'].shift(1))

#     # Bollinger recovery + band width not too narrow
#     data['BB_Reversal'] = (data['Close'] > data['LowerBB']) & (data['BB_Width'] > 0.015)

#     # Confirmed uptrend (price above 20-MA)
#     data['Trend_OK'] = data['Close'] > data['MA20']

#     # RSI above momentum threshold
#     data['RSI_OK'] = data['RSI'] > 50

#     # Trend strength using ADX
#     data['StrongTrend'] = data['ADX'] > 20

#     # Bullish candle confirmation (close near high AND strong body)
#     candle_range = data['High'] - data['Low']
#     candle_body = abs(data['Close'] - data['Open'])
#     data['BullishCandle'] = (data['Close'] > data['Open']) & \
#                             ((data['Close'] - data['Low']) > 0.6 * candle_range) & \
#                             (candle_body > 0.5 * candle_range)

#     # Final signal
#     data['StochBollingerEntry'] = (
#         data['StochCross'] &
#         data['BB_Reversal'] &
#         data['volume_spike'] &
#         data['RSI_OK'] &
#         data['Trend_OK'] &
#         data['StrongTrend'] &
#         data['BullishCandle']
#     )

#     return data[['DateTime', 'StochBollingerEntry']]

def compute_profit_hunter_signals(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def t3_ma(series, length=5, vfactor=0.7):
        e1 = series.ewm(span=length, adjust=False).mean()
        e2 = e1.ewm(span=length, adjust=False).mean()
        e3 = e2.ewm(span=length, adjust=False).mean()
        e4 = e3.ewm(span=length, adjust=False).mean()
        e5 = e4.ewm(span=length, adjust=False).mean()
        e6 = e5.ewm(span=length, adjust=False).mean()
        c1 = -vfactor ** 3
        c2 = 3 * vfactor ** 2 + 3 * vfactor ** 3
        c3 = -6 * vfactor ** 2 - 3 * vfactor - 3 * vfactor ** 3
        c4 = 1 + 3 * vfactor + vfactor ** 3 + 3 * vfactor ** 2
        return c1 * e6 + c2 * e5 + c3 * e4 + c4 * e3

    df['T3Short'] = t3_ma(df['Close'], length=5)
    df['T3Long'] = t3_ma(df['Close'], length=8)
    df['T3Crossover'] = (df['T3Short'] > df['T3Long']) & (df['T3Short'].shift(1) <= df['T3Long'].shift(1))

    high = df['High']
    low = df['Low']
    close = df['Close']
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).sum() / atr)
    minus_di = 100 * (minus_dm.rolling(14).sum() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(14).mean()
    df['ADX_Strong'] = adx > 40  # raised from 25 to 30

    ma20 = df['Close'].rolling(20).mean()
    std20 = df['Close'].rolling(20).std()
    upper_bb = ma20 + 2 * std20
    lower_bb = ma20 - 2 * std20
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    tr_k = (df['High'] - df['Low']).rolling(20).mean()
    upper_kc = typical_price.rolling(20).mean() + 1.5 * tr_k
    lower_kc = typical_price.rolling(20).mean() - 1.5 * tr_k
    df['BollKelt_Breakout'] = (upper_bb > upper_kc) & (lower_bb < lower_kc)

    # Combine
    df['ProfitHunterRaw'] = (
        df['T3Crossover'] &
        df['ADX_Strong'] &
        df['BollKelt_Breakout']
    )

    # Final signal: momentum + volume + VWAP positioning + cooldown
    df['ProfitHunter'] = (
        df['ProfitHunterRaw'] &
        #df['StrongMomentum'] &
        (df['Volume'] > df['Volume'].rolling(80).mean() * 3) &  # volume spike
        (df['Close'] > df['VWAP']) & # price above VWAP
          (df['Close'] > df['Close'].shift(1)) 
    )
    return df[['DateTime', 'ProfitHunter']]

def backtest(
    selected_stocks: Dict[str, List[str]], 
    app, 
    ticker_event: threading.Event
) -> Tuple[Dict[str, Dict[str, Dict[str, float]]], List[Tuple[str, str, str, float]]]:

    date_stats = {}
    transactions = collections.defaultdict(list)    
    reqID = 1000

    for date in selected_stocks.keys():
        date_stats[date] = {}
        for ticker in selected_stocks[date]:
            ticker_event.clear()
            histData(app, reqID, usTechStk(ticker), date + " 22:05:00 US/Eastern", '5 D', '1 min')
            ticker_event.wait()

            if reqID not in app.data or app.data[reqID].empty:
                print(f"Warning: No data for {ticker} on {date}")
                continue

            df = app.data[reqID].copy()

            df['Volume'] = df['Volume'].astype(float)
            df['DateTime'] = pd.to_datetime(df['Date'].str.replace(' US/Eastern', '', regex=False))
            df['DateOnly'] = df['DateTime'].dt.date

            df_vwap = df.groupby('DateOnly').apply(compute_daily_vwap).reset_index(drop=True)
            df = df.merge(df_vwap, on='DateTime', how='left')

            # df['Green'] = df['Close'] > df['Open']
            # df['StrongMomentum'] = (
            #     df['Green'].shift(1).fillna(False) &
            #     df['Green'].shift(2).fillna(False) &
            #     df['Green'].shift(3).fillna(False) &
            #     (df['High'].shift(1) > df['High'].shift(2)) & 
            #     (df['High'].shift(2) > df['High'].shift(3))
            # )

            # df['ATR'] = df['High'].rolling(15).max() - df['Low'].rolling(15).min()
            # df['Momentum'] = df['StrongMomentum'] & ((df['High'] - df['Low']) > 0.4 * df['ATR'])

            # df['Pullback'] = (
            #     (df['Close'] < df['Close'].shift(1)) & 
            #     ((df['Close'].shift(1) - df['Close']) / df['Close'].shift(1) <= 0.02)
            # )
            # df['PullbackAboveVWAP'] = df['Pullback'] & (df['Low'] > df['VWAP'])

            df['AverageVolume'] = df['Volume'].rolling(window=80).mean()
            df['RelativeVolume'] = df['Volume'] / df['AverageVolume']
            # df['Close_to_VWAP'] = df['Close'] / df['VWAP']
            # df['NotExtended'] = df['Close_to_VWAP'] < 5

            # df['VWAP_Reclaim'] = (df['Low'] > df['VWAP']) & (df['Close'] > df['VWAP'])
            df['VolumeSpike'] = (df['RelativeVolume'] > 5) & (df['Volume'] > 15000)

            # df['MicroPullback'] = (
            #     df['StrongMomentum'] &
            #     df['Pullback'] &
            #     df['VolumeSpike']
            # )
            df_micro_pullback = compute_micro_pullback(df, atr_window=15, volume_window=80, rel_volume_thresh=5, vol_thresh=15000, max_pullback_pct=0.02)
            df = df.merge(df_micro_pullback, on='DateTime', how='left')
            df['MicroPullback'] = df['MicroPullback'].fillna(False) 

            def increasing_trend_with_one_small_red(df):
                small_reds = ((df['Close'] < df['Open']) & 
                            (abs(df['Open'] - df['Close']) / df['Open'] < 0.008))
                return small_reds.rolling(window=5).sum().shift(1) <= 1

            df['AllowTrend'] = increasing_trend_with_one_small_red(df)
            # 3. Breakout Candle Strength
            df['Body'] = abs(df['Close'] - df['Open'])
            df['Range'] = df['High'] - df['Low']
            df['StrongBreakoutCandle'] = (df['Body'] / df['Range']) > 0.8

            # 4. ATR Filter
            df['ATR'] = (df['High'] - df['Low']).rolling(window=10).mean()
            df['SufficientVolatility'] = df['ATR'] > df['ATR'].median()
            df['PrevHigh5'] = df['High'].rolling(window=5).max().shift(1)
            # 5. Final Breakout Condition with all filters
            BREAKOUT_MULTIPLIER = 1.0
            VWAP_MULTIPLIER = 1.08
            df_break_out = compute_breakout_signal(df)
            df = df.merge(df_break_out, on='DateTime', how='left')
            df['Breakout'] = df['Breakout'].fillna(False) & df['VolumeSpike']
            # df['Breakout'] = (
            #     (df['Close'] > df['PrevHigh5'] * BREAKOUT_MULTIPLIER) &
            #     df['VolumeSpike'] &
            #     (df['Close'] > df['VWAP'] * VWAP_MULTIPLIER) &
            #     df['StrongBreakoutCandle'] &
            #     #(df['ADX'] > 20) &
            #     df['AllowTrend'] &
            #     df['SufficientVolatility']
            # )
            # df['PrevHigh5'] = df['High'].rolling(window=4).max().shift(1)
            # df['Breakout'] = (
            #     (df['Close'] > df['PrevHigh5']) & 
            #     df['VolumeSpike'] &
            #     (df['Close'] > 1.15 * df['VWAP']) &
            #     df['AllowTrend']
            # )

            df_stoch_boll = compute_stochastic_bollinger_band(df)
            df = df.merge(df_stoch_boll, on='DateTime', how='left')
            df['StochasticBollinger'] = df['StochBollingerEntry'].fillna(False)
            
            # === Profit Hunter ===
            df_profit = compute_profit_hunter_signals(df)
            df = df.merge(df_profit, on='DateTime', how='left')
            df['ProfitHunter'] = df['ProfitHunter'].fillna(False)
            # === Micro Pullback V2 ===
            # df['VWAP_Diff'] = df['VWAP'] - df['Close']
            # df['VWAP_GapTrend'] = df['VWAP_Diff'].rolling(window=3).apply(lambda x: all(earlier > later for earlier, later in zip(x, x[1:])), raw=True)
            # df['VWAP_GapTrend'] = df['VWAP_GapTrend'].fillna(0).astype(bool)
            # df['CloseNearVWAP'] = abs(df['Close'] - df['VWAP']) / df['VWAP'] < 0.1
            # df['VWAPApproach'] = (
            #     df['StrongMomentum'] &
            #     (df['VWAP_Diff'] > 0) &
            #     df['VWAP_GapTrend'] &
            #     df['CloseNearVWAP'] &
            #     df['VolumeSpike']
            # )

            # df['PriorGreen'] = (
            #                         df['Green'].shift(5) & df['Green'].shift(4) & df['Green'].shift(3)
            # )
            # df['PriorHigherHighs'] = (
            #     (df['Close'].shift(4) > df['Close'].shift(5)) &
            #     (df['Close'].shift(3) > df['Close'].shift(4))
            # )
            # df['StrongMomentumPrior'] = df['PriorGreen'] & df['PriorHigherHighs']

            # # 2. Pullback in most recent 3 candles (more flexible)
            # df['LoosePullback'] = (
            #     (df['Close'] < df['Close'].shift(1)) &
            #     ((df['Close'].shift(1) - df['Close']) / df['Close'].shift(1) <= 0.05)
            # )
            # df['PullbackCount'] = df['LoosePullback'].rolling(window=3).sum()

            # # 3. Entry/explosion on this candle
            # df['Above90VWAP'] = df['Close'] > 0.9 * df['VWAP']
            # df['VolumeTrend'] = df['Volume'].rolling(3).mean() > df['Volume'].rolling(10).mean()
            # df['Explosion'] = (
            #     (df['Close'] > df['Open']) &
            #     ((df['Close'] - df['Open']) > 0.5 * df['ATR']) &
            #     df['VolumeSpike'] &
            #     df['Above90VWAP']
            # )

            # # 4. Final signal: momentum precedes pullback, pullback consolidation, then explosion
            # df['MicroPullbackV2'] = (
            #     df['StrongMomentumPrior'] &
            #     (df['PullbackCount'] >= 1) &
            #     (df['PullbackCount'] <= 3) &
            #     df['Explosion'] &
            #     df['NotExtended']
            # )
            df_ema = compute_micro_pullback_ema_strategy(
                df, 
                threshold=0.0003, 
                volume_spike_factor=2
            )
            df = df.merge(df_ema , on='DateTime', how='left')
            df['EMABuySignal'] = df['EMABuySignal'].fillna(False)
            df.dropna(inplace=True)

            in_position = False
            entry_price, stop_loss, target_price = None, None, None
            buy_date, sell_date, entry_type = None, None, None

            for i in range(len(df)):
                row = df.iloc[i]
                close_price = row["Close"]

                if not in_position:
                    if row['EMABuySignal']:
                        entry_type = "EMA"
                        stop_loss_pct = 0.03
                        target_pct = 0.06
                    elif row["MicroPullback"]:
                        entry_type = "MicroPullback"
                        stop_loss_pct = 0.03
                        target_pct = 0.04
                    elif row["Breakout"]:
                        entry_type = "Breakout"
                        stop_loss_pct = 0.03
                        target_pct = 0.05
                    elif row["StochasticBollinger"]:
                        entry_type = "StochasticBollinger"
                        stop_loss_pct = 0.03
                        target_pct = 0.05
                        
                    else:
                        continue

                    entry_price = close_price
                    stop_loss = entry_price * (1 - stop_loss_pct)
                    target_price = entry_price * (1 + target_pct)
                    buy_date = row["Date"]
                    transactions[reqID].append((buy_date,'BUY', ticker, entry_price, entry_type))
                    in_position = True

                else:
                    if close_price >= target_price or close_price <= stop_loss:
                        exit_price = close_price
                        sell_date = row["Date"]
                        transactions[reqID].append((sell_date,'SELL', ticker,exit_price, entry_type))
                        date_stats[date][ticker] = {
                            "return": (exit_price - entry_price) / entry_price,
                            "buy_date": buy_date,
                            "sell_date": sell_date,
                            "type": entry_type
                        }

                        in_position = False
                        entry_price, stop_loss, target_price = None, None, None
                        buy_date, sell_date, entry_type = None, None, None

            app.data[reqID] = df
            reqID += 1

    return date_stats, transactions