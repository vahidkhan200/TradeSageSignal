import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time
import os

def initialize_exchange(exchange_id, rate_limit=True):
    """
    Initialize the exchange API connection
    
    Args:
        exchange_id (str): Exchange identifier (e.g., binance, kraken)
        rate_limit (bool): Whether to enable rate limiting
        
    Returns:
        ccxt.Exchange: Exchange instance
    """
    try:
        # Create exchange instance
        exchange_class = getattr(ccxt, exchange_id)
        exchange = exchange_class({
            'enableRateLimit': rate_limit,
            'timeout': 30000,
            'adjustForTimeDifference': True,
        })
        
        # Use API key and secret if available
        api_key = os.getenv(f"{exchange_id.upper()}_API_KEY", None)
        api_secret = os.getenv(f"{exchange_id.upper()}_API_SECRET", None)
        
        if api_key and api_secret:
            exchange.apiKey = api_key
            exchange.secret = api_secret
        
        return exchange
    
    except Exception as e:
        print(f"Error initializing exchange {exchange_id}: {str(e)}")
        return None

def fetch_market_data(exchange_id, symbol, timeframe, limit=500, fallback=True):
    """
    Fetch market data from exchange
    
    Args:
        exchange_id (str): Exchange identifier
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe for the data
        limit (int): Number of candles to fetch
        fallback (bool): Whether to try fallback exchanges if the primary fails
        
    Returns:
        pandas.DataFrame: Dataframe with market data
    """
    try:
        # Initialize exchange
        exchange = initialize_exchange(exchange_id)
        
        if exchange is None:
            if fallback:
                print(f"Failed to initialize {exchange_id}, trying fallback exchange...")
                return fetch_market_data_from_fallback(symbol, timeframe, limit, [exchange_id])
            return None
        
        # Load markets to validate symbol
        exchange.load_markets()
        
        # Fetch OHLCV data
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        # Convert timestamp to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Set timestamp as index
        df.set_index('timestamp', inplace=True)
        
        return df
    
    except ccxt.BaseError as e:
        print(f"CCXT error when fetching {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for {symbol}...")
            return fetch_market_data_from_fallback(symbol, timeframe, limit, [exchange_id])
        return None
    
    except Exception as e:
        print(f"Error fetching market data for {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for {symbol}...")
            return fetch_market_data_from_fallback(symbol, timeframe, limit, [exchange_id])
        return None

def fetch_market_data_from_fallback(symbol, timeframe, limit=500, excluded_exchanges=None):
    """
    Fetch market data from fallback exchanges
    
    Args:
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe for the data
        limit (int): Number of candles to fetch
        excluded_exchanges (list): List of exchanges to exclude from fallback attempts
        
    Returns:
        pandas.DataFrame: Dataframe with market data
    """
    # List of popular exchanges to try as fallbacks
    fallback_exchanges = ['kraken', 'coinbase', 'kucoin', 'bitfinex', 'huobi', 'okex']
    
    # Remove excluded exchanges
    if excluded_exchanges:
        fallback_exchanges = [ex for ex in fallback_exchanges if ex not in excluded_exchanges]
    
    # Try each fallback exchange
    for exchange_id in fallback_exchanges:
        print(f"Attempting to fetch data from fallback exchange: {exchange_id}")
        df = fetch_market_data(exchange_id, symbol, timeframe, limit, fallback=False)  # Prevent infinite recursion
        if df is not None and not df.empty:
            print(f"Successfully fetched data from fallback exchange: {exchange_id}")
            return df
    
    print("All fallback exchanges failed. No data could be retrieved.")
    return None

def fetch_historical_data(exchange_id, symbol, timeframe, start_date, end_date=None, fallback=True):
    """
    Fetch historical market data for a specific date range
    
    Args:
        exchange_id (str): Exchange identifier
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe for the data
        start_date (datetime): Start date for the data
        end_date (datetime, optional): End date for the data. Defaults to current time.
        fallback (bool): Whether to try fallback exchanges if the primary fails
        
    Returns:
        pandas.DataFrame: Dataframe with historical market data
    """
    try:
        # Initialize exchange
        exchange = initialize_exchange(exchange_id)
        
        if exchange is None:
            if fallback:
                print(f"Failed to initialize {exchange_id}, trying fallback exchange for historical data...")
                return fetch_historical_data_from_fallback(symbol, timeframe, start_date, end_date, [exchange_id])
            return None
        
        # Load markets to validate symbol
        exchange.load_markets()
        
        # Set end date to current time if not provided
        if end_date is None:
            end_date = datetime.now()
        
        # Convert datetime to milliseconds timestamp
        since = int(start_date.timestamp() * 1000)
        
        # Fetch data in chunks due to exchange limitations
        all_candles = []
        while since < int(end_date.timestamp() * 1000):
            try:
                candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
                
                if not candles:
                    break
                
                all_candles.extend(candles)
                
                # Update since to the timestamp of the last candle
                since = candles[-1][0] + 1
                
                # Add delay to avoid rate limiting
                time.sleep(exchange.rateLimit / 1000)
            
            except Exception as e:
                print(f"Error in fetch loop: {str(e)}")
                time.sleep(exchange.rateLimit / 1000)
                break
        
        # Convert to DataFrame
        if all_candles:
            df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Set timestamp as index
            df.set_index('timestamp', inplace=True)
            
            return df
        else:
            print(f"No data returned for {symbol} from {exchange_id}")
            if fallback:
                print(f"Trying fallback exchange for historical data of {symbol}...")
                return fetch_historical_data_from_fallback(symbol, timeframe, start_date, end_date, [exchange_id])
            return None
    
    except ccxt.BaseError as e:
        print(f"CCXT error when fetching historical data for {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for historical data of {symbol}...")
            return fetch_historical_data_from_fallback(symbol, timeframe, start_date, end_date, [exchange_id])
        return None
    
    except Exception as e:
        print(f"Error fetching historical data for {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for historical data of {symbol}...")
            return fetch_historical_data_from_fallback(symbol, timeframe, start_date, end_date, [exchange_id])
        return None

def fetch_historical_data_from_fallback(symbol, timeframe, start_date, end_date=None, excluded_exchanges=None):
    """
    Fetch historical market data from fallback exchanges
    
    Args:
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe for the data
        start_date (datetime): Start date for the data
        end_date (datetime, optional): End date for the data. Defaults to current time.
        excluded_exchanges (list): List of exchanges to exclude from fallback attempts
        
    Returns:
        pandas.DataFrame: Dataframe with historical market data
    """
    # List of popular exchanges to try as fallbacks
    fallback_exchanges = ['kraken', 'coinbase', 'kucoin', 'bitfinex', 'huobi', 'okex']
    
    # Remove excluded exchanges
    if excluded_exchanges:
        fallback_exchanges = [ex for ex in fallback_exchanges if ex not in excluded_exchanges]
    
    # Try each fallback exchange
    for exchange_id in fallback_exchanges:
        print(f"Attempting to fetch historical data from fallback exchange: {exchange_id}")
        df = fetch_historical_data(exchange_id, symbol, timeframe, start_date, end_date, fallback=False)  # Prevent infinite recursion
        if df is not None and not df.empty:
            print(f"Successfully fetched historical data from fallback exchange: {exchange_id}")
            return df
    
    print("All fallback exchanges failed. No historical data could be retrieved.")
    return None

def fetch_ticker(exchange_id, symbol, fallback=True):
    """
    Fetch current ticker data for a symbol
    
    Args:
        exchange_id (str): Exchange identifier
        symbol (str): Trading pair symbol
        fallback (bool): Whether to try fallback exchanges if the primary fails
        
    Returns:
        dict: Ticker data
    """
    try:
        # Initialize exchange
        exchange = initialize_exchange(exchange_id)
        
        if exchange is None:
            if fallback:
                print(f"Failed to initialize {exchange_id}, trying fallback exchange for ticker...")
                return fetch_ticker_from_fallback(symbol, [exchange_id])
            return None
        
        # Fetch ticker
        ticker = exchange.fetch_ticker(symbol)
        return ticker
    
    except ccxt.BaseError as e:
        print(f"CCXT error when fetching ticker for {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for ticker of {symbol}...")
            return fetch_ticker_from_fallback(symbol, [exchange_id])
        return None
    
    except Exception as e:
        print(f"Error fetching ticker for {symbol} from {exchange_id}: {str(e)}")
        if fallback:
            print(f"Trying fallback exchange for ticker of {symbol}...")
            return fetch_ticker_from_fallback(symbol, [exchange_id])
        return None

def fetch_ticker_from_fallback(symbol, excluded_exchanges=None):
    """
    Fetch ticker data from fallback exchanges
    
    Args:
        symbol (str): Trading pair symbol
        excluded_exchanges (list): List of exchanges to exclude from fallback attempts
        
    Returns:
        dict: Ticker data
    """
    # List of popular exchanges to try as fallbacks
    fallback_exchanges = ['kraken', 'coinbase', 'kucoin', 'bitfinex', 'huobi', 'okex']
    
    # Remove excluded exchanges
    if excluded_exchanges:
        fallback_exchanges = [ex for ex in fallback_exchanges if ex not in excluded_exchanges]
    
    # Try each fallback exchange
    for exchange_id in fallback_exchanges:
        print(f"Attempting to fetch ticker from fallback exchange: {exchange_id}")
        ticker = fetch_ticker(exchange_id, symbol, fallback=False)  # Prevent infinite recursion
        if ticker is not None:
            print(f"Successfully fetched ticker from fallback exchange: {exchange_id}")
            return ticker
    
    print("All fallback exchanges failed. No ticker data could be retrieved.")
    return None

def get_available_symbols(exchange_id, quote_currency='USDT', min_volume=100000, fallback=True):
    """
    Get available trading pairs from an exchange with specific quote currency and minimum volume
    
    Args:
        exchange_id (str): Exchange identifier
        quote_currency (str): Quote currency (e.g., 'USDT', 'USD', 'BTC')
        min_volume (float): Minimum 24h volume in USD
        fallback (bool): Whether to try fallback exchanges if the primary fails
        
    Returns:
        list: List of available symbols meeting the criteria
    """
    try:
        # Initialize exchange
        exchange = initialize_exchange(exchange_id)
        
        if exchange is None:
            if fallback:
                print(f"Failed to initialize {exchange_id}, trying fallback exchange for symbols...")
                return get_available_symbols_from_fallback(quote_currency, min_volume, [exchange_id])
            return []
        
        # Load markets
        markets = exchange.load_markets()
        
        # Filter symbols by quote currency and volume
        filtered_symbols = []
        
        for symbol in markets:
            # Check if the symbol ends with the quote currency
            if not symbol.endswith(f'/{quote_currency}'):
                continue
                
            try:
                # Fetch ticker to get volume info
                ticker = exchange.fetch_ticker(symbol)
                
                # Check if volume meets minimum requirements (convert to USD)
                volume_usd = ticker.get('quoteVolume', 0)
                
                if volume_usd >= min_volume:
                    filtered_symbols.append(symbol)
            except Exception as e:
                print(f"Error checking volume for {symbol}: {str(e)}")
                continue
        
        if filtered_symbols:
            return filtered_symbols
        else:
            print(f"No symbols with {quote_currency} and min volume {min_volume} found on {exchange_id}")
            if fallback:
                return get_available_symbols_from_fallback(quote_currency, min_volume, [exchange_id])
            return []
    
    except Exception as e:
        print(f"Error getting available symbols from {exchange_id}: {str(e)}")
        if fallback:
            return get_available_symbols_from_fallback(quote_currency, min_volume, [exchange_id])
        return []

def get_available_symbols_from_fallback(quote_currency='USDT', min_volume=100000, excluded_exchanges=None):
    """
    Get available trading pairs from fallback exchanges
    
    Args:
        quote_currency (str): Quote currency (e.g., 'USDT', 'USD', 'BTC')
        min_volume (float): Minimum 24h volume in USD
        excluded_exchanges (list): List of exchanges to exclude from fallback attempts
        
    Returns:
        list: List of available symbols meeting the criteria
    """
    # List of popular exchanges to try as fallbacks
    fallback_exchanges = ['kraken', 'coinbase', 'kucoin', 'bitfinex', 'huobi', 'okex']
    
    # Remove excluded exchanges
    if excluded_exchanges:
        fallback_exchanges = [ex for ex in fallback_exchanges if ex not in excluded_exchanges]
    
    # Try each fallback exchange
    for exchange_id in fallback_exchanges:
        print(f"Attempting to fetch symbols from fallback exchange: {exchange_id}")
        symbols = get_available_symbols(exchange_id, quote_currency, min_volume, fallback=False)  # Prevent infinite recursion
        if symbols:
            print(f"Successfully fetched symbols from fallback exchange: {exchange_id}")
            return symbols
    
    print("All fallback exchanges failed. No symbols could be retrieved.")
    return []
