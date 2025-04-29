import requests
import time
import threading
import json
from datetime import datetime
from database import mark_signal_telegram_sent, check_pending_signals

# Global variables
telegram_token = None
telegram_chat_id = None

def setup_telegram_bot(token, chat_id):
    """
    Set up Telegram bot with token and chat ID
    
    Args:
        token (str): Telegram bot token
        chat_id (str): Telegram chat ID to send messages to
    """
    global telegram_token, telegram_chat_id
    
    if not token or not chat_id:
        raise ValueError("Telegram token and chat ID are required")
    
    telegram_token = token
    telegram_chat_id = chat_id
    
    # Test the connection
    test_telegram_connection()

def test_telegram_connection():
    """
    Test the Telegram connection by sending a test message
    
    Returns:
        bool: True if successful, False otherwise
    """
    global telegram_token, telegram_chat_id
    
    if not telegram_token or not telegram_chat_id:
        return False
    
    try:
        message = "🔔 *سیستم سیگنال دهی ترید متصل شد*\n\n" \
                  "سیستم سیگنال دهی ترید راه‌اندازی شده و در حال پایش بازارها است."
        
        send_telegram_message(message)
        return True
    
    except Exception as e:
        print(f"Error testing Telegram connection: {str(e)}")
        return False

def send_telegram_message(message):
    """
    Send a message to Telegram
    
    Args:
        message (str): Message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    global telegram_token, telegram_chat_id
    
    if not telegram_token or not telegram_chat_id:
        print("Telegram bot not initialized")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        data = {
            "chat_id": telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send Telegram message: {response.text}")
            return False
    
    except Exception as e:
        print(f"Error sending Telegram message: {str(e)}")
        return False

def send_signal_notification(signal):
    """
    Send a trading signal notification via Telegram
    
    Args:
        signal (dict): Signal details
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Format signal for Telegram message
    signal_id = signal.get('id', '')
    symbol = signal.get('symbol', '')
    signal_type = signal.get('signal_type', '')
    signal_type_fa = "خرید" if signal_type == "LONG" else "فروش"
    strategy = signal.get('strategy', '')
    entry_price = signal.get('entry_price', 0)
    stop_loss = signal.get('stop_loss', 0)
    target1 = signal.get('target1', 0)
    target2 = signal.get('target2', 0)
    risk_reward_ratio1 = signal.get('risk_reward_ratio1', 0)
    risk_reward_ratio2 = signal.get('risk_reward_ratio2', 0)
    leverage = signal.get('leverage', 1)
    timestamp = signal.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    # Create message
    emoji = "🟢" if signal_type == "LONG" else "🔴"
    
    message = f"{emoji} *سیگنال جدید {signal_type_fa} برای {symbol}*\n\n" \
              f"*استراتژی:* {strategy}\n" \
              f"*زمان:* {timestamp}\n\n" \
              f"*قیمت ورود:* {entry_price:.8f}\n" \
              f"*حد ضرر:* {stop_loss:.8f}\n" \
              f"*هدف اول:* {target1:.8f}\n" \
              f"*هدف دوم:* {target2:.8f}\n\n" \
              f"*نسبت ریسک/ریوارد ۱:* {risk_reward_ratio1:.2f}\n" \
              f"*نسبت ریسک/ریوارد ۲:* {risk_reward_ratio2:.2f}\n" \
              f"*اهرم پیشنهادی:* {leverage}x\n\n" \
              "⚠️ *سلب مسئولیت:* این یک سیگنال خودکار است. همیشه تحقیقات خود را انجام دهید و مدیریت ریسک مناسب داشته باشید."
    
    # Send the message
    success = send_telegram_message(message)
    
    # Mark signal as sent in database if successful
    if success and signal_id:
        try:
            mark_signal_telegram_sent(signal_id)
        except Exception as e:
            print(f"Error marking signal as sent in database: {str(e)}")
    
    return success

def check_and_send_pending_signals():
    """
    Check for pending signals that haven't been sent to Telegram and send them
    
    Returns:
        int: Number of signals sent
    """
    try:
        # Get pending signals
        pending_signals = check_pending_signals()
        
        if not pending_signals:
            return 0
        
        # Send each pending signal
        sent_count = 0
        for signal in pending_signals:
            # Convert to dictionary
            signal_dict = {
                'id': signal.signal_id,
                'timestamp': signal.timestamp.strftime('%Y-%m-%d %H:%M:%S') if hasattr(signal.timestamp, 'strftime') else signal.timestamp,
                'symbol': signal.symbol,
                'signal_type': signal.signal_type,
                'strategy': signal.strategy,
                'entry_price': signal.entry_price,
                'current_price': signal.current_price,
                'stop_loss': signal.stop_loss,
                'target1': signal.target1,
                'target2': signal.target2,
                'risk_reward_ratio1': signal.risk_reward_ratio1,
                'risk_reward_ratio2': signal.risk_reward_ratio2,
                'risk_percent': signal.risk_percent,
                'leverage': signal.leverage
            }
            
            # Send the signal
            success = send_signal_notification(signal_dict)
            
            if success:
                sent_count += 1
        
        return sent_count
    
    except Exception as e:
        print(f"Error checking and sending pending signals: {str(e)}")
        return 0

def send_error_notification(error_message):
    """
    Send an error notification via Telegram
    
    Args:
        error_message (str): Error message
        
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"❌ *هشدار خطا*\n\n" \
              f"سیستم سیگنال دهی ترید با خطا مواجه شد:\n" \
              f"`{error_message}`\n\n" \
              f"زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return send_telegram_message(message)

def send_status_update(status_message):
    """
    Send a status update via Telegram
    
    Args:
        status_message (str): Status message
        
    Returns:
        bool: True if successful, False otherwise
    """
    message = f"ℹ️ *بروزرسانی وضعیت*\n\n" \
              f"{status_message}\n\n" \
              f"زمان: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    return send_telegram_message(message)
