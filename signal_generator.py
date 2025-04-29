import pandas as pd
from datetime import datetime
import uuid
from database import save_signal

def generate_signals(df, config):
    """
    Generate trading signals based on technical analysis and patterns
    
    Args:
        df (pandas.DataFrame): Dataframe with market data and indicators
        config (dict): Configuration for signal generation
        
    Returns:
        list: List of dictionaries containing signal details
    """
    # Get only the most recent candle for signal generation
    recent_df = df.iloc[-1:].copy()
    
    # List to store signals
    signals = []
    
    # Get symbol from config
    symbol = config.get('symbol', 'BTC/USDT')
    
    # Check for MACD signals
    if config.get('use_macd', True) and 'macd_cross_up' in df.columns and 'macd_cross_down' in df.columns:
        # MACD bullish crossover
        if recent_df['macd_cross_up'].iloc[0]:
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='MACD Bullish Crossover',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # MACD bearish crossover
        elif recent_df['macd_cross_down'].iloc[0]:
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='MACD Bearish Crossover',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Check for RSI signals
    if config.get('use_rsi', True) and 'rsi' in df.columns:
        # RSI oversold with bullish divergence
        if recent_df['rsi_oversold'].iloc[0] and recent_df['bullish_divergence'].iloc[0]:
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='RSI Oversold with Bullish Divergence',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # RSI overbought with bearish divergence
        elif recent_df['rsi_overbought'].iloc[0] and recent_df['bearish_divergence'].iloc[0]:
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='RSI Overbought with Bearish Divergence',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Check for candlestick pattern signals
    if config.get('use_candlestick_patterns', True):
        # Bullish candlestick patterns in uptrend
        if recent_df['bullish_candlestick'].iloc[0] and recent_df['uptrend'].iloc[0]:
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Bullish Candlestick Pattern in Uptrend',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # Bearish candlestick patterns in downtrend
        elif recent_df['bearish_candlestick'].iloc[0] and recent_df['downtrend'].iloc[0]:
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Bearish Candlestick Pattern in Downtrend',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Check for harmonic pattern signals
    if config.get('use_harmonic_patterns', True):
        # Bullish harmonic patterns
        if recent_df['bullish_harmonic'].iloc[0]:
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Bullish Harmonic Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # Bearish harmonic patterns
        elif recent_df['bearish_harmonic'].iloc[0]:
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Bearish Harmonic Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Check for price action pattern signals
    if config.get('use_price_action', True):
        # Bullish price action patterns
        if recent_df['bullish_price_action'].iloc[0]:
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Bullish Price Action Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # Bearish price action patterns
        elif recent_df['bearish_price_action'].iloc[0]:
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Bearish Price Action Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Check for moving average crossover signals
    # Golden Cross (50 MA crosses above 200 MA)
    if 'golden_cross' in df.columns and recent_df['golden_cross'].iloc[0]:
        signal = create_signal(
            symbol=symbol,
            signal_type='LONG',
            strategy='Golden Cross (50 MA > 200 MA)',
            entry_price=recent_df['close'].iloc[0],
            current_price=recent_df['close'].iloc[0],
            config=config
        )
        signals.append(signal)
    
    # Death Cross (50 MA crosses below 200 MA)
    elif 'death_cross' in df.columns and recent_df['death_cross'].iloc[0]:
        signal = create_signal(
            symbol=symbol,
            signal_type='SHORT',
            strategy='Death Cross (50 MA < 200 MA)',
            entry_price=recent_df['close'].iloc[0],
            current_price=recent_df['close'].iloc[0],
            config=config
        )
        signals.append(signal)
    
    # Short-term momentum
    elif 'short_term_bull' in df.columns and recent_df['short_term_bull'].iloc[0]:
        signal = create_signal(
            symbol=symbol,
            signal_type='LONG',
            strategy='Short-term Bullish Momentum (20 MA > 50 MA)',
            entry_price=recent_df['close'].iloc[0],
            current_price=recent_df['close'].iloc[0],
            config=config
        )
        signals.append(signal)
    
    elif 'short_term_bear' in df.columns and recent_df['short_term_bear'].iloc[0]:
        signal = create_signal(
            symbol=symbol,
            signal_type='SHORT',
            strategy='Short-term Bearish Momentum (20 MA < 50 MA)',
            entry_price=recent_df['close'].iloc[0],
            current_price=recent_df['close'].iloc[0],
            config=config
        )
        signals.append(signal)
    
    return signals

def create_signal(symbol, signal_type, strategy, entry_price, current_price, config):
    """
    Create a signal with all required details
    
    Args:
        symbol (str): Trading pair symbol
        signal_type (str): 'LONG' or 'SHORT'
        strategy (str): Name of the strategy generating the signal
        entry_price (float): Entry price for the signal
        current_price (float): Current price of the asset
        config (dict): Configuration for signal generation
        
    Returns:
        dict: Signal details
    """
    # Generate unique ID for the signal
    signal_id = str(uuid.uuid4())
    
    # Current timestamp
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate stop loss
    if config.get('use_atr', True) and 'atr' in config:
        atr = config['atr']
        atr_multiplier = config.get('atr_multiplier', 2.0)
        
        if signal_type == 'LONG':
            stop_loss = entry_price - (atr * atr_multiplier)
        else:  # SHORT
            stop_loss = entry_price + (atr * atr_multiplier)
    else:
        # Default stop loss (3% from entry)
        if signal_type == 'LONG':
            stop_loss = entry_price * 0.97
        else:  # SHORT
            stop_loss = entry_price * 1.03
    
    # Calculate risk (distance to stop loss)
    if signal_type == 'LONG':
        risk = entry_price - stop_loss
    else:  # SHORT
        risk = stop_loss - entry_price
    
    # Calculate targets
    tp1_factor = config.get('tp1_factor', 2.0)
    tp2_factor = config.get('tp2_factor', 3.0)
    
    if signal_type == 'LONG':
        target1 = entry_price + (risk * tp1_factor)
        target2 = entry_price + (risk * tp2_factor)
    else:  # SHORT
        target1 = entry_price - (risk * tp1_factor)
        target2 = entry_price - (risk * tp2_factor)
    
    # Get suggested leverage
    leverage = config.get('default_leverage', 5)
    
    # Create signal dictionary with all required details
    signal = {
        'id': signal_id,
        'timestamp': timestamp,
        'symbol': symbol,
        'signal_type': signal_type,
        'strategy': strategy,
        'entry_price': float(entry_price),
        'current_price': float(current_price),
        'stop_loss': float(stop_loss),
        'target1': float(target1),
        'target2': float(target2),
        'risk_reward_ratio1': float(tp1_factor),
        'risk_reward_ratio2': float(tp2_factor),
        'risk_percent': float(config.get('risk_percent', 1.0)),
        'leverage': int(leverage)
    }
    
    try:
        # Save signal to database
        save_signal(signal)
    except Exception as e:
        print(f"Error saving signal to database: {str(e)}")
    
    return signal

def generate_combined_signals(df, config):
    """
    Generate signals based on combined strategies
    
    Args:
        df (pandas.DataFrame): Dataframe with market data and indicators
        config (dict): Configuration for signal generation
        
    Returns:
        list: List of dictionaries containing signal details
    """
    # Get only the most recent candle for signal generation
    recent_df = df.iloc[-1:].copy()
    
    # List to store signals
    signals = []
    
    # Get symbol from config
    symbol = config.get('symbol', 'BTC/USDT')
    
    # Combined strategy: MACD crossover + RSI confirmation + Trend confirmation
    if (config.get('use_macd', True) and config.get('use_rsi', True) and 
            'macd_cross_up' in df.columns and 'rsi' in df.columns):
        
        # MACD bullish crossover + RSI < 50 + Uptrend
        if (recent_df['macd_cross_up'].iloc[0] and 
                recent_df['rsi'].iloc[0] < 50 and 
                recent_df['uptrend'].iloc[0]):
            
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Combined: MACD Bullish Crossover + RSI < 50 + Uptrend',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # MACD bearish crossover + RSI > 50 + Downtrend
        elif (recent_df['macd_cross_down'].iloc[0] and 
                recent_df['rsi'].iloc[0] > 50 and 
                recent_df['downtrend'].iloc[0]):
            
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Combined: MACD Bearish Crossover + RSI > 50 + Downtrend',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Combined strategy: Price Action + Support/Resistance + RSI
    if (config.get('use_price_action', True) and config.get('use_rsi', True) and 
            'bullish_price_action' in df.columns and 'bearish_price_action' in df.columns):
        
        # Bullish price action + RSI oversold
        if (recent_df['bullish_price_action'].iloc[0] and 
                recent_df['rsi_oversold'].iloc[0]):
            
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Combined: Bullish Price Action + RSI Oversold',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # Bearish price action + RSI overbought
        elif (recent_df['bearish_price_action'].iloc[0] and 
                recent_df['rsi_overbought'].iloc[0]):
            
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Combined: Bearish Price Action + RSI Overbought',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    # Combined strategy: Candlestick Patterns + Harmonic Patterns
    if (config.get('use_candlestick_patterns', True) and config.get('use_harmonic_patterns', True) and 
            'bullish_candlestick' in df.columns and 'bullish_harmonic' in df.columns):
        
        # Bullish candlestick + Bullish harmonic
        if (recent_df['bullish_candlestick'].iloc[0] and 
                recent_df['bullish_harmonic'].iloc[0]):
            
            # Generate long signal
            signal = create_signal(
                symbol=symbol,
                signal_type='LONG',
                strategy='Combined: Bullish Candlestick + Bullish Harmonic Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
        
        # Bearish candlestick + Bearish harmonic
        elif (recent_df['bearish_candlestick'].iloc[0] and 
                recent_df['bearish_harmonic'].iloc[0]):
            
            # Generate short signal
            signal = create_signal(
                symbol=symbol,
                signal_type='SHORT',
                strategy='Combined: Bearish Candlestick + Bearish Harmonic Pattern',
                entry_price=recent_df['close'].iloc[0],
                current_price=recent_df['close'].iloc[0],
                config=config
            )
            signals.append(signal)
    
    return signals

def filter_conflicting_signals(signals):
    """
    Filter out conflicting signals (e.g., LONG and SHORT for the same symbol)
    
    Args:
        signals (list): List of signal dictionaries
        
    Returns:
        list: Filtered list of signals
    """
    if not signals:
        return []
    
    # Group signals by symbol
    signals_by_symbol = {}
    for signal in signals:
        symbol = signal['symbol']
        if symbol not in signals_by_symbol:
            signals_by_symbol[symbol] = []
        signals_by_symbol[symbol].append(signal)
    
    # Filter conflicting signals for each symbol
    filtered_signals = []
    for symbol, symbol_signals in signals_by_symbol.items():
        # If there are multiple signals for a symbol, check for conflicts
        if len(symbol_signals) > 1:
            # Check if there are both LONG and SHORT signals
            has_long = any(s['signal_type'] == 'LONG' for s in symbol_signals)
            has_short = any(s['signal_type'] == 'SHORT' for s in symbol_signals)
            
            # If there are conflicting signals, prioritize based on strength
            if has_long and has_short:
                # Get all LONG signals
                long_signals = [s for s in symbol_signals if s['signal_type'] == 'LONG']
                # Get all SHORT signals
                short_signals = [s for s in symbol_signals if s['signal_type'] == 'SHORT']
                
                # Count the number of LONG and SHORT signals
                long_count = len(long_signals)
                short_count = len(short_signals)
                
                # Select signals based on majority
                if long_count > short_count:
                    filtered_signals.extend(long_signals)
                elif short_count > long_count:
                    filtered_signals.extend(short_signals)
                else:
                    # If equal, select the strongest signal based on risk/reward
                    all_signals = sorted(symbol_signals, key=lambda s: s['risk_reward_ratio2'], reverse=True)
                    filtered_signals.append(all_signals[0])
            else:
                # No conflict, add all signals
                filtered_signals.extend(symbol_signals)
        else:
            # Only one signal, no conflict
            filtered_signals.extend(symbol_signals)
    
    return filtered_signals
