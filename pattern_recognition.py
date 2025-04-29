import pandas as pd
import numpy as np
from scipy.signal import argrelextrema

def analyze_patterns(df, config):
    """
    Analyze various patterns in the price data
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        config (dict): Configuration with pattern settings
        
    Returns:
        pandas.DataFrame: Dataframe with pattern detection columns
    """
    # Make a copy to avoid modifying the original
    df = df.copy()
    
    # Analyze candlestick patterns if enabled
    if config.get('use_candlestick_patterns', True):
        df = detect_candlestick_patterns(df)
    
    # Analyze harmonic patterns if enabled
    if config.get('use_harmonic_patterns', True):
        df = detect_harmonic_patterns(df)
    
    # Analyze price action patterns if enabled
    if config.get('use_price_action', True):
        df = detect_price_action_patterns(df)
    
    return df

def detect_candlestick_patterns(df):
    """
    Detect candlestick patterns
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        
    Returns:
        pandas.DataFrame: Dataframe with candlestick pattern detection columns
    """
    # Calculate basic candle metrics
    df['body_size'] = abs(df['close'] - df['open'])
    df['upper_shadow'] = df['high'] - df[['open', 'close']].max(axis=1)
    df['lower_shadow'] = df[['open', 'close']].min(axis=1) - df['low']
    df['is_bullish'] = df['close'] > df['open']
    df['is_bearish'] = df['close'] < df['open']
    df['body_percentage'] = df['body_size'] / (df['high'] - df['low'])
    df['upper_shadow_percentage'] = df['upper_shadow'] / (df['high'] - df['low'])
    df['lower_shadow_percentage'] = df['lower_shadow'] / (df['high'] - df['low'])
    
    # Doji pattern
    df['doji'] = (df['body_size'] / (df['high'] - df['low']) < 0.1) & (df['high'] > df['low'])
    
    # Hammer pattern (bullish)
    df['hammer'] = (df['is_bullish']) & \
                   (df['lower_shadow'] > 2 * df['body_size']) & \
                   (df['upper_shadow'] < 0.1 * df['body_size']) & \
                   (df['body_percentage'] < 0.3) & \
                   (df['lower_shadow_percentage'] > 0.6)
    
    # Inverted hammer pattern (bullish)
    df['inverted_hammer'] = (df['is_bullish']) & \
                            (df['upper_shadow'] > 2 * df['body_size']) & \
                            (df['lower_shadow'] < 0.1 * df['body_size']) & \
                            (df['body_percentage'] < 0.3) & \
                            (df['upper_shadow_percentage'] > 0.6)
    
    # Hanging man pattern (bearish)
    df['hanging_man'] = (df['is_bearish']) & \
                        (df['lower_shadow'] > 2 * df['body_size']) & \
                        (df['upper_shadow'] < 0.1 * df['body_size']) & \
                        (df['body_percentage'] < 0.3) & \
                        (df['lower_shadow_percentage'] > 0.6)
    
    # Shooting star pattern (bearish)
    df['shooting_star'] = (df['is_bearish']) & \
                          (df['upper_shadow'] > 2 * df['body_size']) & \
                          (df['lower_shadow'] < 0.1 * df['body_size']) & \
                          (df['body_percentage'] < 0.3) & \
                          (df['upper_shadow_percentage'] > 0.6)
    
    # Engulfing patterns
    df['prev_close'] = df['close'].shift(1)
    df['prev_open'] = df['open'].shift(1)
    df['prev_is_bullish'] = df['is_bullish'].shift(1)
    df['prev_is_bearish'] = df['is_bearish'].shift(1)
    
    # Bullish engulfing
    df['engulfing_bullish'] = (df['is_bullish']) & \
                              (df['prev_is_bearish']) & \
                              (df['open'] < df['prev_close']) & \
                              (df['close'] > df['prev_open'])
    
    # Bearish engulfing
    df['engulfing_bearish'] = (df['is_bearish']) & \
                              (df['prev_is_bullish']) & \
                              (df['open'] > df['prev_close']) & \
                              (df['close'] < df['prev_open'])
    
    # Morning star pattern (bullish)
    df['morning_star'] = (df['is_bullish']) & \
                         (df['prev_is_bearish'].shift(1)) & \
                         (df['body_size'].shift(1) < 0.3 * df['body_size'].shift(2)) & \
                         (df['body_size'] > 0.6 * df['body_size'].shift(2)) & \
                         (df['close'] > (df['open'].shift(2) + df['close'].shift(2)) / 2)
    
    # Evening star pattern (bearish)
    df['evening_star'] = (df['is_bearish']) & \
                         (df['prev_is_bullish'].shift(1)) & \
                         (df['body_size'].shift(1) < 0.3 * df['body_size'].shift(2)) & \
                         (df['body_size'] > 0.6 * df['body_size'].shift(2)) & \
                         (df['close'] < (df['open'].shift(2) + df['close'].shift(2)) / 2)
    
    # Three white soldiers (bullish)
    df['three_white_soldiers'] = (df['is_bullish']) & \
                                (df['is_bullish'].shift(1)) & \
                                (df['is_bullish'].shift(2)) & \
                                (df['close'] > df['close'].shift(1)) & \
                                (df['close'].shift(1) > df['close'].shift(2)) & \
                                (df['open'] > df['open'].shift(1)) & \
                                (df['open'].shift(1) > df['open'].shift(2)) & \
                                (df['open'] < df['close'].shift(1)) & \
                                (df['open'].shift(1) < df['close'].shift(2))
    
    # Three black crows (bearish)
    df['three_black_crows'] = (df['is_bearish']) & \
                             (df['is_bearish'].shift(1)) & \
                             (df['is_bearish'].shift(2)) & \
                             (df['close'] < df['close'].shift(1)) & \
                             (df['close'].shift(1) < df['close'].shift(2)) & \
                             (df['open'] < df['open'].shift(1)) & \
                             (df['open'].shift(1) < df['open'].shift(2)) & \
                             (df['open'] > df['close'].shift(1)) & \
                             (df['open'].shift(1) > df['close'].shift(2))
    
    # Piercing pattern (bullish)
    df['piercing_pattern'] = (df['is_bullish']) & \
                            (df['prev_is_bearish']) & \
                            (df['open'] < df['prev_close']) & \
                            (df['close'] > (df['prev_open'] + df['prev_close']) / 2) & \
                            (df['close'] < df['prev_open'])
    
    # Dark cloud cover (bearish)
    df['dark_cloud_cover'] = (df['is_bearish']) & \
                            (df['prev_is_bullish']) & \
                            (df['open'] > df['prev_close']) & \
                            (df['close'] < (df['prev_open'] + df['prev_close']) / 2) & \
                            (df['close'] > df['prev_open'])
    
    # Spinning top
    df['spinning_top'] = (df['body_percentage'] < 0.3) & \
                         (df['upper_shadow_percentage'] > 0.3) & \
                         (df['lower_shadow_percentage'] > 0.3)
    
    # Add combined column for bullish and bearish patterns
    bullish_patterns = [
        'hammer', 'inverted_hammer', 'engulfing_bullish', 
        'morning_star', 'three_white_soldiers', 'piercing_pattern'
    ]
    
    bearish_patterns = [
        'hanging_man', 'shooting_star', 'engulfing_bearish',
        'evening_star', 'three_black_crows', 'dark_cloud_cover'
    ]
    
    # Check if any bullish patterns are detected
    df['bullish_candlestick'] = df[bullish_patterns].any(axis=1)
    
    # Check if any bearish patterns are detected
    df['bearish_candlestick'] = df[bearish_patterns].any(axis=1)
    
    return df

def detect_harmonic_patterns(df, tolerance=0.05):
    """
    Detect harmonic patterns like Gartley, Butterfly, Bat, etc.
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        tolerance (float): Tolerance for pattern recognition
        
    Returns:
        pandas.DataFrame: Dataframe with harmonic pattern detection columns
    """
    # Create a copy to avoid modifying the original
    df = df.copy()
    
    # Add columns for harmonic patterns
    df['gartley_bullish'] = False
    df['gartley_bearish'] = False
    df['butterfly_bullish'] = False
    df['butterfly_bearish'] = False
    df['bat_bullish'] = False
    df['bat_bearish'] = False
    df['crab_bullish'] = False
    df['crab_bearish'] = False
    df['shark_bullish'] = False
    df['shark_bearish'] = False
    
    # Find local extrema (pivot points)
    n_points = 5  # Window for local extrema detection
    df['local_max'] = df['high'].rolling(window=2*n_points+1, center=True).apply(
        lambda x: 1 if x[n_points] == max(x) else 0, raw=True
    )
    df['local_min'] = df['low'].rolling(window=2*n_points+1, center=True).apply(
        lambda x: 1 if x[n_points] == min(x) else 0, raw=True
    )
    
    # Unable to accurately implement harmonic pattern detection in this context
    # This would require more complex algorithm with point-to-point measurement
    # and Fibonacci ratio validation
    
    # Instead, implement a simpler version that checks if the recent price movement 
    # approximates a harmonic pattern structure
    
    # Warning: This is a simplified implementation and may not be accurate for all cases
    
    # Get swings for the last 100 bars
    last_bars = min(100, len(df))
    window = 10  # Adjust as needed for smoother extrema detection
    
    # Find local maximum and minimum indices
    high_idx = list(argrelextrema(df['high'].values[-last_bars:], np.greater, order=window)[0])
    low_idx = list(argrelextrema(df['low'].values[-last_bars:], np.less, order=window)[0])
    
    # Sort all extrema by index and take the last 5 (X, A, B, C, D)
    extrema_idx = sorted(high_idx + low_idx)[-5:]
    
    # If we found at least 5 extrema points, check for patterns
    if len(extrema_idx) >= 5:
        # Get the high/low values at the extrema points
        extrema_values = []
        for idx in extrema_idx:
            if idx in high_idx:
                extrema_values.append(df['high'].values[-last_bars:][idx])
            else:
                extrema_values.append(df['low'].values[-last_bars:][idx])
        
        # Calculate retracement levels
        # This is a simplified approach and would need a more complex implementation for accuracy
        if len(extrema_values) == 5:
            xabcd = extrema_values
            
            # Calculate simple XA, AB, BC, CD moves
            xa = xabcd[1] - xabcd[0]
            ab = xabcd[2] - xabcd[1]
            bc = xabcd[3] - xabcd[2]
            cd = xabcd[4] - xabcd[3]
            
            # Calculate retracement ratios 
            # (Simplified - for accurate pattern recognition we need to consider bullish vs bearish patterns)
            if xa != 0:  # Avoid division by zero
                ab_xa_ratio = abs(ab / xa)
            else:
                ab_xa_ratio = 0
                
            if ab != 0:  # Avoid division by zero
                bc_ab_ratio = abs(bc / ab)
            else:
                bc_ab_ratio = 0
                
            if bc != 0:  # Avoid division by zero
                cd_bc_ratio = abs(cd / bc)
            else:
                cd_bc_ratio = 0
            
            # Check if the recent structure matches any harmonic pattern
            # Using simplified ratio checks with tolerance
            
            # Gartley pattern (simplified ratios)
            # AB should retrace 61.8% of XA
            # BC should retrace 38.2% of AB
            # CD should retrace 127.2% to 161.8% of BC
            if (abs(ab_xa_ratio - 0.618) < tolerance and 
                abs(bc_ab_ratio - 0.382) < tolerance and 
                (abs(cd_bc_ratio - 1.272) < tolerance or abs(cd_bc_ratio - 1.618) < tolerance)):
                if cd < 0:  # Bullish pattern ends with up move
                    df.iloc[-1, df.columns.get_loc('gartley_bullish')] = True
                else:  # Bearish pattern ends with down move
                    df.iloc[-1, df.columns.get_loc('gartley_bearish')] = True
            
            # Butterfly pattern (simplified ratios)
            # AB should retrace 78.6% of XA
            # BC should retrace 38.2% to 88.6% of AB
            # CD should retrace 161.8% to 261.8% of BC
            if (abs(ab_xa_ratio - 0.786) < tolerance and 
                (abs(bc_ab_ratio - 0.382) < tolerance or abs(bc_ab_ratio - 0.886) < tolerance) and 
                (abs(cd_bc_ratio - 1.618) < tolerance or abs(cd_bc_ratio - 2.618) < tolerance)):
                if cd < 0:  # Bullish pattern ends with up move
                    df.iloc[-1, df.columns.get_loc('butterfly_bullish')] = True
                else:  # Bearish pattern ends with down move
                    df.iloc[-1, df.columns.get_loc('butterfly_bearish')] = True
            
            # Bat pattern (simplified ratios)
            # AB should retrace 38.2% to 50% of XA
            # BC should retrace 38.2% to 88.6% of AB
            # CD should retrace 161.8% to 261.8% of BC
            if ((abs(ab_xa_ratio - 0.382) < tolerance or abs(ab_xa_ratio - 0.5) < tolerance) and 
                (abs(bc_ab_ratio - 0.382) < tolerance or abs(bc_ab_ratio - 0.886) < tolerance) and 
                (abs(cd_bc_ratio - 1.618) < tolerance or abs(cd_bc_ratio - 2.618) < tolerance)):
                if cd < 0:  # Bullish pattern ends with up move
                    df.iloc[-1, df.columns.get_loc('bat_bullish')] = True
                else:  # Bearish pattern ends with down move
                    df.iloc[-1, df.columns.get_loc('bat_bearish')] = True
            
            # Crab pattern (simplified ratios)
            # AB should retrace 38.2% to 61.8% of XA
            # BC should retrace 38.2% to 88.6% of AB
            # CD should retrace 261.8% to 361.8% of BC
            if ((abs(ab_xa_ratio - 0.382) < tolerance or abs(ab_xa_ratio - 0.618) < tolerance) and 
                (abs(bc_ab_ratio - 0.382) < tolerance or abs(bc_ab_ratio - 0.886) < tolerance) and 
                (abs(cd_bc_ratio - 2.618) < tolerance or abs(cd_bc_ratio - 3.618) < tolerance)):
                if cd < 0:  # Bullish pattern ends with up move
                    df.iloc[-1, df.columns.get_loc('crab_bullish')] = True
                else:  # Bearish pattern ends with down move
                    df.iloc[-1, df.columns.get_loc('crab_bearish')] = True
            
            # Shark pattern (simplified ratios)
            # AB should retrace 113.0% to 161.8% of XA
            # BC should retrace 113.0% to 161.8% of AB
            # CD should retrace 113.0% to 161.8% of BC
            if ((abs(ab_xa_ratio - 1.13) < tolerance or abs(ab_xa_ratio - 1.618) < tolerance) and 
                (abs(bc_ab_ratio - 1.13) < tolerance or abs(bc_ab_ratio - 1.618) < tolerance) and 
                (abs(cd_bc_ratio - 1.13) < tolerance or abs(cd_bc_ratio - 1.618) < tolerance)):
                if cd < 0:  # Bullish pattern ends with up move
                    df.iloc[-1, df.columns.get_loc('shark_bullish')] = True
                else:  # Bearish pattern ends with down move
                    df.iloc[-1, df.columns.get_loc('shark_bearish')] = True
    
    # Add combined columns for bullish and bearish harmonic patterns
    bullish_harmonic = [
        'gartley_bullish', 'butterfly_bullish', 'bat_bullish',
        'crab_bullish', 'shark_bullish'
    ]
    
    bearish_harmonic = [
        'gartley_bearish', 'butterfly_bearish', 'bat_bearish',
        'crab_bearish', 'shark_bearish'
    ]
    
    df['bullish_harmonic'] = df[bullish_harmonic].any(axis=1)
    df['bearish_harmonic'] = df[bearish_harmonic].any(axis=1)
    
    return df

def detect_price_action_patterns(df, window=20):
    """
    Detect price action patterns like double tops/bottoms, head and shoulders, etc.
    
    Args:
        df (pandas.DataFrame): Dataframe with market data
        window (int): Window for detecting pivots
        
    Returns:
        pandas.DataFrame: Dataframe with price action pattern detection columns
    """
    # Create a copy to avoid modifying the original
    df = df.copy()
    
    # Add columns for various price action patterns
    price_action_patterns = [
        'double_top', 'double_bottom', 'triple_top', 'triple_bottom',
        'head_and_shoulders', 'inverse_head_and_shoulders',
        'ascending_triangle', 'descending_triangle', 'symmetrical_triangle',
        'rising_wedge', 'falling_wedge',
        'flag_bullish', 'flag_bearish', 'pennant_bullish', 'pennant_bearish'
    ]
    
    for pattern in price_action_patterns:
        df[pattern] = False
    
    # Find local extrema (pivot points)
    n_points = window  # Window for local extrema detection
    
    # Use rolling window to find local maxima and minima
    # A local maximum is where the price is higher than all prices in the window
    # A local minimum is where the price is lower than all prices in the window
    df['pivot_high'] = df['high'].rolling(window=2*n_points+1, center=True).apply(
        lambda x: 1 if x[n_points] == max(x) else 0, raw=True
    )
    df['pivot_low'] = df['low'].rolling(window=2*n_points+1, center=True).apply(
        lambda x: 1 if x[n_points] == min(x) else 0, raw=True
    )
    
    # Check for double top pattern
    for i in range(len(df) - n_points):
        if i + 2*n_points >= len(df):
            continue
            
        # Get recent pivot highs
        pivot_highs = df.iloc[i:i+2*n_points+1]['pivot_high']
        pivot_high_indices = pivot_highs[pivot_highs == 1].index
        
        # Check if we have at least 2 pivot highs
        if len(pivot_high_indices) >= 2:
            high1_idx = pivot_high_indices[-2]
            high2_idx = pivot_high_indices[-1]
            
            high1 = df.loc[high1_idx, 'high']
            high2 = df.loc[high2_idx, 'high']
            
            # Check if the two highs are within 1% of each other
            if abs(high2 - high1) / high1 < 0.01:
                # Check if there's a pivot low between them
                between_lows = df.loc[high1_idx:high2_idx, 'pivot_low']
                if between_lows.sum() >= 1:
                    df.loc[high2_idx, 'double_top'] = True
    
    # Check for double bottom pattern
    for i in range(len(df) - n_points):
        if i + 2*n_points >= len(df):
            continue
            
        # Get recent pivot lows
        pivot_lows = df.iloc[i:i+2*n_points+1]['pivot_low']
        pivot_low_indices = pivot_lows[pivot_lows == 1].index
        
        # Check if we have at least 2 pivot lows
        if len(pivot_low_indices) >= 2:
            low1_idx = pivot_low_indices[-2]
            low2_idx = pivot_low_indices[-1]
            
            low1 = df.loc[low1_idx, 'low']
            low2 = df.loc[low2_idx, 'low']
            
            # Check if the two lows are within 1% of each other
            if abs(low2 - low1) / low1 < 0.01:
                # Check if there's a pivot high between them
                between_highs = df.loc[low1_idx:low2_idx, 'pivot_high']
                if between_highs.sum() >= 1:
                    df.loc[low2_idx, 'double_bottom'] = True
    
    # Check for triple top pattern (simplified)
    for i in range(len(df) - 2*n_points):
        if i + 3*n_points >= len(df):
            continue
            
        # Get recent pivot highs
        pivot_highs = df.iloc[i:i+3*n_points+1]['pivot_high']
        pivot_high_indices = pivot_highs[pivot_highs == 1].index
        
        # Check if we have at least 3 pivot highs
        if len(pivot_high_indices) >= 3:
            high1_idx = pivot_high_indices[-3]
            high2_idx = pivot_high_indices[-2]
            high3_idx = pivot_high_indices[-1]
            
            high1 = df.loc[high1_idx, 'high']
            high2 = df.loc[high2_idx, 'high']
            high3 = df.loc[high3_idx, 'high']
            
            # Check if the three highs are within 1% of each other
            if (abs(high2 - high1) / high1 < 0.01) and (abs(high3 - high1) / high1 < 0.01):
                df.loc[high3_idx, 'triple_top'] = True
    
    # Check for triple bottom pattern (simplified)
    for i in range(len(df) - 2*n_points):
        if i + 3*n_points >= len(df):
            continue
            
        # Get recent pivot lows
        pivot_lows = df.iloc[i:i+3*n_points+1]['pivot_low']
        pivot_low_indices = pivot_lows[pivot_lows == 1].index
        
        # Check if we have at least 3 pivot lows
        if len(pivot_low_indices) >= 3:
            low1_idx = pivot_low_indices[-3]
            low2_idx = pivot_low_indices[-2]
            low3_idx = pivot_low_indices[-1]
            
            low1 = df.loc[low1_idx, 'low']
            low2 = df.loc[low2_idx, 'low']
            low3 = df.loc[low3_idx, 'low']
            
            # Check if the three lows are within 1% of each other
            if (abs(low2 - low1) / low1 < 0.01) and (abs(low3 - low1) / low1 < 0.01):
                df.loc[low3_idx, 'triple_bottom'] = True
    
    # Check for head and shoulders pattern (simplified)
    for i in range(len(df) - 2*n_points):
        if i + 3*n_points >= len(df):
            continue
            
        # Get recent pivot highs
        pivot_highs = df.iloc[i:i+3*n_points+1]['pivot_high']
        pivot_high_indices = pivot_highs[pivot_highs == 1].index
        
        # Check if we have at least 3 pivot highs
        if len(pivot_high_indices) >= 3:
            left_shoulder_idx = pivot_high_indices[-3]
            head_idx = pivot_high_indices[-2]
            right_shoulder_idx = pivot_high_indices[-1]
            
            left_shoulder = df.loc[left_shoulder_idx, 'high']
            head = df.loc[head_idx, 'high']
            right_shoulder = df.loc[right_shoulder_idx, 'high']
            
            # Check if head is higher than shoulders and shoulders are within 5% of each other
            if (head > left_shoulder) and (head > right_shoulder) and (abs(right_shoulder - left_shoulder) / left_shoulder < 0.05):
                df.loc[right_shoulder_idx, 'head_and_shoulders'] = True
    
    # Check for inverse head and shoulders pattern (simplified)
    for i in range(len(df) - 2*n_points):
        if i + 3*n_points >= len(df):
            continue
            
        # Get recent pivot lows
        pivot_lows = df.iloc[i:i+3*n_points+1]['pivot_low']
        pivot_low_indices = pivot_lows[pivot_lows == 1].index
        
        # Check if we have at least 3 pivot lows
        if len(pivot_low_indices) >= 3:
            left_shoulder_idx = pivot_low_indices[-3]
            head_idx = pivot_low_indices[-2]
            right_shoulder_idx = pivot_low_indices[-1]
            
            left_shoulder = df.loc[left_shoulder_idx, 'low']
            head = df.loc[head_idx, 'low']
            right_shoulder = df.loc[right_shoulder_idx, 'low']
            
            # Check if head is lower than shoulders and shoulders are within 5% of each other
            if (head < left_shoulder) and (head < right_shoulder) and (abs(right_shoulder - left_shoulder) / left_shoulder < 0.05):
                df.loc[right_shoulder_idx, 'inverse_head_and_shoulders'] = True
    
    # Detect triangle patterns (simplified)
    # These are more complex patterns and would require trend line fitting
    # Here we use a simplified approach checking for converging highs and lows
    
    # Detection of other patterns would require more complex analysis
    # that's beyond the scope of this simplified implementation
    
    # Add combined columns for bullish and bearish price action patterns
    bullish_price_action = [
        'double_bottom', 'triple_bottom', 'inverse_head_and_shoulders',
        'ascending_triangle', 'falling_wedge', 'flag_bullish', 'pennant_bullish'
    ]
    
    bearish_price_action = [
        'double_top', 'triple_top', 'head_and_shoulders',
        'descending_triangle', 'rising_wedge', 'flag_bearish', 'pennant_bearish'
    ]
    
    df['bullish_price_action'] = df[bullish_price_action].any(axis=1)
    df['bearish_price_action'] = df[bearish_price_action].any(axis=1)
    
    return df
