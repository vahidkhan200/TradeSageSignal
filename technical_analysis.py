import pandas as pd
import numpy as np
import pandas_ta as ta

def calculate_indicators(df, config):
    """
    Calculate technical indicators based on configuration
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        config (dict): Configuration with indicator settings
        
    Returns:
        pandas.DataFrame: Dataframe with calculated indicators
    """
    # Create a copy of the dataframe to avoid modifying the original
    df = df.copy()
    
    # Calculate MACD if enabled
    if config.get('use_macd', True):
        fast = config.get('macd_fast', 12)
        slow = config.get('macd_slow', 26)
        signal = config.get('macd_signal', 9)
        
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        df['macd'] = macd['MACD_' + str(fast) + '_' + str(slow) + '_' + str(signal)]
        df['macd_signal'] = macd['MACDs_' + str(fast) + '_' + str(slow) + '_' + str(signal)]
        df['macd_hist'] = macd['MACDh_' + str(fast) + '_' + str(slow) + '_' + str(signal)]
        
        # Calculate MACD crossover signals
        df['macd_cross_up'] = ((df['macd'] > df['macd_signal']) & 
                              (df['macd'].shift(1) <= df['macd_signal'].shift(1)))
        df['macd_cross_down'] = ((df['macd'] < df['macd_signal']) & 
                                (df['macd'].shift(1) >= df['macd_signal'].shift(1)))
    
    # Calculate RSI if enabled
    if config.get('use_rsi', True):
        period = config.get('rsi_period', 14)
        overbought = config.get('rsi_overbought', 70)
        oversold = config.get('rsi_oversold', 30)
        
        df['rsi'] = ta.rsi(df['close'], length=period)
        
        # Calculate RSI overbought/oversold signals
        df['rsi_overbought'] = df['rsi'] > overbought
        df['rsi_oversold'] = df['rsi'] < oversold
        
        # Calculate RSI divergence (simple implementation)
        df['price_higher_high'] = (df['close'] > df['close'].shift(1)) & (df['close'].shift(1) > df['close'].shift(2))
        df['price_lower_low'] = (df['close'] < df['close'].shift(1)) & (df['close'].shift(1) < df['close'].shift(2))
        df['rsi_higher_high'] = (df['rsi'] > df['rsi'].shift(1)) & (df['rsi'].shift(1) > df['rsi'].shift(2))
        df['rsi_lower_low'] = (df['rsi'] < df['rsi'].shift(1)) & (df['rsi'].shift(1) < df['rsi'].shift(2))
        
        # Bearish divergence: price makes higher high, but RSI makes lower high
        df['bearish_divergence'] = (df['price_higher_high'] & ~df['rsi_higher_high']) & (df['rsi'] > 60)
        # Bullish divergence: price makes lower low, but RSI makes higher low
        df['bullish_divergence'] = (df['price_lower_low'] & ~df['rsi_lower_low']) & (df['rsi'] < 40)
    
    # Calculate ATR if enabled
    if config.get('use_atr', True):
        period = config.get('atr_period', 14)
        multiplier = config.get('atr_multiplier', 2.0)
        
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=period)
        
        # Calculate ATR-based stop loss levels
        df['atr_stop_long'] = df['close'] - (df['atr'] * multiplier)
        df['atr_stop_short'] = df['close'] + (df['atr'] * multiplier)
    
    # Calculate moving averages
    # EMA 20, 50, 200
    df['ema20'] = ta.ema(df['close'], length=20)
    df['ema50'] = ta.ema(df['close'], length=50)
    df['ema200'] = ta.ema(df['close'], length=200)
    
    # SMA 20, 50, 200
    df['sma20'] = ta.sma(df['close'], length=20)
    df['sma50'] = ta.sma(df['close'], length=50)
    df['sma200'] = ta.sma(df['close'], length=200)
    
    # Calculate moving average crossovers
    # Golden Cross (50 MA crosses above 200 MA)
    df['golden_cross'] = ((df['ema50'] > df['ema200']) & 
                         (df['ema50'].shift(1) <= df['ema200'].shift(1)))
    
    # Death Cross (50 MA crosses below 200 MA)
    df['death_cross'] = ((df['ema50'] < df['ema200']) & 
                        (df['ema50'].shift(1) >= df['ema200'].shift(1)))
    
    # Short-term momentum (20 MA crosses 50 MA)
    df['short_term_bull'] = ((df['ema20'] > df['ema50']) & 
                            (df['ema20'].shift(1) <= df['ema50'].shift(1)))
    df['short_term_bear'] = ((df['ema20'] < df['ema50']) & 
                            (df['ema20'].shift(1) >= df['ema50'].shift(1)))
    
    # Calculate Bollinger Bands
    bollinger = ta.bbands(df['close'], length=20, std=2)
    df['bb_upper'] = bollinger['BBU_20_2.0']
    df['bb_middle'] = bollinger['BBM_20_2.0']
    df['bb_lower'] = bollinger['BBL_20_2.0']
    df['bb_width'] = ((df['bb_upper'] - df['bb_lower']) / df['bb_middle'])
    
    # Calculate Bollinger Band signals
    df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(window=50).mean()
    df['bb_upper_touch'] = df['high'] >= df['bb_upper']
    df['bb_lower_touch'] = df['low'] <= df['bb_lower']
    
    # Calculate Stochastic Oscillator
    stoch = ta.stoch(df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3)
    df['stoch_k'] = stoch['STOCHk_14_3_3']
    df['stoch_d'] = stoch['STOCHd_14_3_3']
    
    # Calculate Stochastic crossover signals
    df['stoch_cross_up'] = ((df['stoch_k'] > df['stoch_d']) & 
                           (df['stoch_k'].shift(1) <= df['stoch_d'].shift(1)))
    df['stoch_cross_down'] = ((df['stoch_k'] < df['stoch_d']) & 
                             (df['stoch_k'].shift(1) >= df['stoch_d'].shift(1)))
    
    # Calculate Ichimoku Cloud
    ichimoku = ta.ichimoku(df['high'], df['low'], df['close'])
    df['tenkan_sen'] = ichimoku['TENKAN_9']
    df['kijun_sen'] = ichimoku['KIJUN_26']
    df['senkou_span_a'] = ichimoku['SENKOU_A_26']
    df['senkou_span_b'] = ichimoku['SENKOU_B_52']
    df['chikou_span'] = ichimoku['CHIKOU_26']
    
    # Calculate ADX (Average Directional Index)
    adx = ta.adx(df['high'], df['low'], df['close'], length=14)
    df['adx'] = adx['ADX_14']
    df['di_plus'] = adx['DMP_14']
    df['di_minus'] = adx['DMN_14']
    
    # Calculate Volume Profile
    df['volume_sma'] = ta.sma(df['volume'], length=20)
    df['volume_ratio'] = df['volume'] / df['volume_sma']
    df['rising_volume'] = df['volume'] > df['volume'].shift(1)
    
    # Add trend direction columns
    df['uptrend'] = (df['close'] > df['ema200']) & (df['ema50'] > df['ema200'])
    df['downtrend'] = (df['close'] < df['ema200']) & (df['ema50'] < df['ema200'])
    df['sideways'] = ~(df['uptrend'] | df['downtrend'])
    
    return df

def calculate_momentum_indicators(df):
    """
    Calculate additional momentum and volatility indicators
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        
    Returns:
        pandas.DataFrame: Dataframe with additional indicators
    """
    df = df.copy()
    
    # Calculate Rate of Change (ROC)
    df['roc_10'] = ta.roc(df['close'], length=10)
    
    # Calculate Commodity Channel Index (CCI)
    df['cci'] = ta.cci(df['high'], df['low'], df['close'], length=20)
    
    # Calculate Williams %R
    df['williams_r'] = ta.willr(df['high'], df['low'], df['close'], length=14)
    
    # Calculate Chande Momentum Oscillator (CMO)
    df['cmo'] = ta.cmo(df['close'], length=14)
    
    # Calculate Money Flow Index (MFI)
    df['mfi'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=14)
    
    # Calculate Ultimate Oscillator
    df['uo'] = ta.uo(df['high'], df['low'], df['close'])
    
    # Volatility indicators
    
    # Keltner Channel
    keltner = ta.kc(df['high'], df['low'], df['close'], length=20, scalar=2)
    df['kc_upper'] = keltner['KCUe_20_2.0']
    df['kc_lower'] = keltner['KCLe_20_2.0']
    df['kc_middle'] = keltner['KCMe_20_2.0']
    
    # True Strength Index (TSI)
    df['tsi'] = ta.tsi(df['close'])
    
    # Vortex Indicator
    vortex = ta.vortex(df['high'], df['low'], df['close'], length=14)
    df['vi_plus'] = vortex['VTXP_14']
    df['vi_minus'] = vortex['VTXM_14']
    
    return df

def calculate_support_resistance(df, window=10):
    """
    Calculate support and resistance levels
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        window (int): Window for detecting pivots
        
    Returns:
        tuple: Support and resistance levels
    """
    df = df.copy()
    
    # Find pivot highs and lows
    pivot_highs = []
    pivot_lows = []
    
    for i in range(window, len(df) - window):
        # Check for pivot high
        if all(df['high'].iloc[i] > df['high'].iloc[i-j] for j in range(1, window+1)) and \
           all(df['high'].iloc[i] > df['high'].iloc[i+j] for j in range(1, window+1)):
            pivot_highs.append((df.index[i], df['high'].iloc[i]))
        
        # Check for pivot low
        if all(df['low'].iloc[i] < df['low'].iloc[i-j] for j in range(1, window+1)) and \
           all(df['low'].iloc[i] < df['low'].iloc[i+j] for j in range(1, window+1)):
            pivot_lows.append((df.index[i], df['low'].iloc[i]))
    
    # Get most recent pivot points for support and resistance
    pivot_highs = sorted(pivot_highs, key=lambda x: x[0], reverse=True)
    pivot_lows = sorted(pivot_lows, key=lambda x: x[0], reverse=True)
    
    # Get levels as a list of prices
    resistance_levels = [price for _, price in pivot_highs]
    support_levels = [price for _, price in pivot_lows]
    
    return support_levels, resistance_levels
