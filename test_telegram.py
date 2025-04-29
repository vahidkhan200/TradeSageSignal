import streamlit as st
import sys
from telegram_notifier import setup_telegram_bot, send_telegram_message, send_signal_notification

def test_telegram(telegram_token=None, telegram_chat_id=None):
    """
    تست اتصال تلگرام
    
    Args:
        telegram_token (str): توکن ربات تلگرام
        telegram_chat_id (str): شناسه چت تلگرام
    """
    print("در حال تست اتصال تلگرام...")
    
    # Check if the token and chat ID are provided
    if not telegram_token or not telegram_chat_id:
        print("خطا: توکن ربات تلگرام و شناسه چت تلگرام باید به عنوان پارامتر ارسال شوند.")
        print("نحوه استفاده: python test_telegram.py [توکن-تلگرام] [شناسه-چت]")
        return
    
    try:
        # Setup the Telegram bot
        setup_telegram_bot(telegram_token, telegram_chat_id)
        
        # Send a test message
        print("در حال ارسال پیام تست ساده...")
        result = send_telegram_message("🔔 این یک پیام تست از سیستم سیگنال دهی ترید است")
        
        if result:
            print("پیام تست با موفقیت ارسال شد!")
        else:
            print("ارسال پیام تست با خطا مواجه شد.")
        
        # Send a test signal
        print("در حال ارسال سیگنال تست...")
        test_signal = {
            'id': 'test_signal_001',
            'symbol': 'BTC/USDT',
            'signal_type': 'LONG',
            'strategy': 'MACD + RSI',
            'entry_price': 60000.0,
            'current_price': 60000.0,
            'stop_loss': 58000.0,
            'target1': 63000.0,
            'target2': 65000.0,
            'risk_reward_ratio1': 1.5,
            'risk_reward_ratio2': 2.5,
            'risk_percent': 1.0,
            'leverage': 3
        }
        
        result = send_signal_notification(test_signal)
        
        if result:
            print("سیگنال تست با موفقیت ارسال شد!")
        else:
            print("ارسال سیگنال تست با خطا مواجه شد.")
        
    except Exception as e:
        print(f"خطا در تست تلگرام: {str(e)}")

if __name__ == "__main__":
    # Get token and chat ID from command line arguments
    if len(sys.argv) >= 3:
        token = sys.argv[1]
        chat_id = sys.argv[2]
        test_telegram(token, chat_id)
    else:
        print("خطا: توکن ربات تلگرام و شناسه چت تلگرام باید به عنوان پارامتر ارسال شوند.")
        print("نحوه استفاده: python test_telegram.py [توکن-تلگرام] [شناسه-چت]")