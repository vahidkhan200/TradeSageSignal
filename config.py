# Configuration settings for the trading signal generator

# Default settings
DEFAULT_SETTINGS = {
    # Exchange and symbol settings
    'exchange': 'kraken',
    'symbol': 'BTC/USDT',
    'timeframe': '1h',
    'check_interval': 30,  # minutes
    
    # MACD settings
    'use_macd': True,
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # RSI settings
    'use_rsi': True,
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    
    # ATR settings
    'use_atr': True,
    'atr_period': 14,
    'atr_multiplier': 2.0,
    
    # Pattern recognition settings
    'use_candlestick_patterns': True,
    'use_harmonic_patterns': True,
    'use_price_action': True,
    
    # Target and stop loss settings
    'tp1_factor': 1.5,  # Target 1 is 1.5x the risk
    'tp2_factor': 3.0,  # Target 2 is 3x the risk (1:3 risk/reward ratio)
    
    # Position settings
    'default_leverage': 5,
    'risk_percent': 1.0  # Risk 1% of account per trade
}

# Available exchanges
AVAILABLE_EXCHANGES = [
    'binance',
    'bitfinex',
    'bitmex',
    'bittrex',
    'coinbase',
    'huobi',
    'kraken',
    'kucoin',
    'okex'
]

# Available timeframes
AVAILABLE_TIMEFRAMES = [
    '1m', '3m', '5m', '15m', '30m',
    '1h', '2h', '4h', '6h', '8h', '12h',
    '1d', '3d', '1w', '1M'
]

# Available symbols
AVAILABLE_SYMBOLS = [
    'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
    'ADA/USDT', 'DOGE/USDT', 'DOT/USDT', 'MATIC/USDT', 'AVAX/USDT',
    'LINK/USDT', 'UNI/USDT', 'LTC/USDT', 'BCH/USDT', 'ALGO/USDT',
    'ATOM/USDT', 'FIL/USDT', 'XLM/USDT', 'TRX/USDT', 'ETC/USDT',
    'ETH/BTC', 'BNB/BTC', 'SOL/BTC', 'XRP/BTC', 'ADA/BTC'
]

# Candlestick patterns
CANDLESTICK_PATTERNS = [
    'hammer',
    'inverted_hammer',
    'hanging_man',
    'shooting_star',
    'engulfing_bullish',
    'engulfing_bearish',
    'doji',
    'morning_star',
    'evening_star',
    'three_white_soldiers',
    'three_black_crows',
    'piercing_pattern',
    'dark_cloud_cover',
    'spinning_top'
]

# Harmonic patterns
HARMONIC_PATTERNS = [
    'gartley',
    'butterfly',
    'bat',
    'crab',
    'shark',
    'cypher'
]

# Price action patterns
PRICE_ACTION_PATTERNS = [
    'double_top',
    'double_bottom',
    'triple_top',
    'triple_bottom',
    'head_and_shoulders',
    'inverse_head_and_shoulders',
    'ascending_triangle',
    'descending_triangle',
    'symmetrical_triangle',
    'rising_wedge',
    'falling_wedge',
    'flag_bullish',
    'flag_bearish',
    'pennant_bullish',
    'pennant_bearish'
]
