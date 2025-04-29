import os
import json
from datetime import datetime
from config import DEFAULT_SETTINGS
from database import save_configuration, get_configuration

def load_config():
    """
    Load configuration from database or file, or return default settings
    
    Returns:
        dict: Configuration settings
    """
    try:
        # Try to load from database first
        db_config = get_configuration("default")
        if db_config:
            return db_config
        
        # If not in database, try to load from file
        config_file = "config.json"
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
            # Save to database for future use
            save_configuration(config, "default")
            return config
        else:
            # Return default settings if no config exists
            return DEFAULT_SETTINGS.copy()
    
    except Exception as e:
        print(f"Error loading configuration: {str(e)}")
        return DEFAULT_SETTINGS.copy()

def save_config(config):
    """
    Save configuration to database and file
    
    Args:
        config (dict): Configuration settings
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Save to database
        save_configuration(config, "default")
        
        # Also save to file as backup
        config_file = "config.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
        return True
    
    except Exception as e:
        print(f"Error saving configuration: {str(e)}")
        return False

def format_number(number, decimals=8):
    """
    Format a number with a specified number of decimal places
    
    Args:
        number (float): Number to format
        decimals (int): Number of decimal places
        
    Returns:
        str: Formatted number
    """
    format_string = f"{{:.{decimals}f}}"
    return format_string.format(number)

def calculate_position_size(account_balance, risk_percent, entry_price, stop_loss, leverage=1):
    """
    Calculate position size based on risk parameters
    
    Args:
        account_balance (float): Account balance
        risk_percent (float): Percentage of account to risk
        entry_price (float): Entry price
        stop_loss (float): Stop loss price
        leverage (float): Leverage multiplier
        
    Returns:
        float: Position size
    """
    # Calculate risk amount
    risk_amount = account_balance * (risk_percent / 100)
    
    # Calculate risk per unit
    risk_per_unit = abs(entry_price - stop_loss) / entry_price
    
    # Calculate position size
    position_size = (risk_amount / risk_per_unit) * leverage
    
    return position_size

def log_message(message, log_file="trading_signals.log"):
    """
    Log a message to a file
    
    Args:
        message (str): Message to log
        log_file (str): Log file path
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    
    try:
        with open(log_file, "a") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to log file: {str(e)}")

def parse_timeframe(timeframe):
    """
    Parse a timeframe string into minutes
    
    Args:
        timeframe (str): Timeframe string (e.g., '1h', '15m', '1d')
        
    Returns:
        int: Timeframe in minutes
    """
    unit = timeframe[-1]
    value = int(timeframe[:-1])
    
    if unit == 'm':
        return value
    elif unit == 'h':
        return value * 60
    elif unit == 'd':
        return value * 60 * 24
    elif unit == 'w':
        return value * 60 * 24 * 7
    elif unit == 'M':
        return value * 60 * 24 * 30  # Approximate
    else:
        return value  # Default to the value as is
