import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import ccxt
import time
import threading
import os

from config import AVAILABLE_EXCHANGES, AVAILABLE_TIMEFRAMES, AVAILABLE_SYMBOLS, DEFAULT_SETTINGS
from data_fetcher import fetch_market_data, get_available_symbols
from technical_analysis import calculate_indicators
from pattern_recognition import analyze_patterns
from signal_generator import generate_signals
from telegram_notifier import setup_telegram_bot, send_signal_notification
from backtester import run_backtest
from utils import load_config, save_config

# Page configuration
st.set_page_config(
    page_title="Trading Signal Generator",
    page_icon="📈",
    layout="wide"
)

# Initialize session state
if 'running' not in st.session_state:
    st.session_state.running = False
if 'config' not in st.session_state:
    st.session_state.config = load_config()
if 'signals' not in st.session_state:
    st.session_state.signals = []
if 'last_run' not in st.session_state:
    st.session_state.last_run = None
if 'bot_initialized' not in st.session_state:
    st.session_state.bot_initialized = False

# Initialize Telegram bot
def init_telegram_bot():
    telegram_token = st.session_state.config.get('telegram_token', '')
    telegram_chat_id = st.session_state.config.get('telegram_chat_id', '')
    
    if telegram_token and telegram_chat_id:
        try:
            setup_telegram_bot(telegram_token, telegram_chat_id)
            st.session_state.bot_initialized = True
            st.success("Telegram bot initialized successfully!")
        except Exception as e:
            st.error(f"Failed to initialize Telegram bot: {str(e)}")
            st.session_state.bot_initialized = False
    else:
        st.warning("Telegram token and chat ID are required to enable notifications.")
        st.session_state.bot_initialized = False

# Signal generation loop for a single symbol
def signal_generation_loop():
    # Add a check to ensure session_state has required fields
    while True:
        try:
            # Need to access session_state in a thread-safe manner
            if not hasattr(st.session_state, 'running') or not st.session_state.running:
                # If not running or the attribute doesn't exist, exit the loop
                print("Signal generation loop stopped or not properly initialized")
                break
            
            # Get current configuration
            if not hasattr(st.session_state, 'config'):
                print("Config not found in session_state")
                time.sleep(10)  # Wait and retry
                continue
                
            config = st.session_state.config
            
            # Check if we should scan the whole market or just a specific symbol
            scan_whole_market = config.get('scan_whole_market', False)
            
            if scan_whole_market:
                # Scan the whole market
                market_scan_loop()
            else:
                # Fetch market data for a single symbol
                symbol = config.get('symbol', DEFAULT_SETTINGS['symbol'])
                exchange_id = config.get('exchange', DEFAULT_SETTINGS['exchange'])
                timeframe = config.get('timeframe', DEFAULT_SETTINGS['timeframe'])
                
                # Process this single symbol
                process_symbol(symbol, exchange_id, timeframe, config)
            
            # Wait for the next run
            interval_minutes = config.get('check_interval', DEFAULT_SETTINGS['check_interval'])
            time.sleep(interval_minutes * 60)
            
        except Exception as e:
            print(f"Error in signal generation loop: {str(e)}")
            time.sleep(60)  # Wait before retrying

# Function to process a single symbol
def process_symbol(symbol, exchange_id, timeframe, config):
    try:
        # Fetch the data
        df = fetch_market_data(exchange_id, symbol, timeframe)
        
        if df is not None and not df.empty:
            # Calculate technical indicators
            df = calculate_indicators(df, config)
            
            # Analyze patterns
            df = analyze_patterns(df, config)
            
            # Generate signals
            new_signals = generate_signals(df, config)
            
            # Send notifications for new signals
            if new_signals and hasattr(st.session_state, 'bot_initialized') and st.session_state.bot_initialized:
                if not hasattr(st.session_state, 'signals'):
                    st.session_state.signals = []
                    
                for signal in new_signals:
                    # Make sure the symbol is set in the signal
                    signal['symbol'] = symbol
                    
                    # Check if the signal is new (not in the current signals list)
                    if signal not in st.session_state.signals:
                        send_signal_notification(signal)
                        st.session_state.signals.append(signal)
            
            # Update last run time
            if hasattr(st.session_state, 'last_run'):
                st.session_state.last_run = datetime.now()
                
            return new_signals
    except Exception as e:
        print(f"Error processing symbol {symbol}: {str(e)}")
    
    return []

# Market scanning loop
def market_scan_loop():
    try:
        # Get current configuration
        if not hasattr(st.session_state, 'config'):
            print("Config not found in session_state")
            return
            
        config = st.session_state.config
        
        # Exchange and timeframe settings
        exchange_id = config.get('exchange', DEFAULT_SETTINGS['exchange'])
        timeframe = config.get('timeframe', DEFAULT_SETTINGS['timeframe'])
        quote_currency = config.get('quote_currency', 'USDT')
        min_volume = config.get('min_volume', 1000000)  # Minimum 24h volume in USD (default 1M)
        
        print(f"Starting market scan on {exchange_id} for {quote_currency} pairs with minimum volume {min_volume}")
        
        # Get available symbols
        symbols = get_available_symbols(exchange_id, quote_currency, min_volume)
        
        if not symbols:
            print("No symbols found matching criteria")
            return
        
        print(f"Found {len(symbols)} symbols to scan")
        
        # Process each symbol
        all_signals = []
        for symbol in symbols:
            print(f"Processing {symbol}...")
            signals = process_symbol(symbol, exchange_id, timeframe, config)
            if signals:
                all_signals.extend(signals)
                print(f"Found {len(signals)} signals for {symbol}")
        
        print(f"Market scan completed. Found {len(all_signals)} signals across {len(symbols)} symbols.")
        
    except Exception as e:
        print(f"Error in market scan loop: {str(e)}")

# Main application layout
st.markdown("""
<style>
    .main-title {
        font-size: 3rem !important;
        font-weight: bold;
        background: linear-gradient(90deg, #00C853, #18FFFF);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.5rem !important;
        color: #B0BEC5;
        margin-bottom: 2rem;
    }
    .card {
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background-color: #132F4C;
        border-left: 5px solid #00C853;
    }
    .signal-box {
        padding: 1rem;
        border-radius: 5px;
        margin: 0.5rem 0;
    }
    .signal-long {
        background-color: rgba(0, 200, 83, 0.2);
        border-left: 3px solid #00C853;
    }
    .signal-short {
        background-color: rgba(244, 67, 54, 0.2);
        border-left: 3px solid #F44336;
    }
    .indicator {
        font-weight: bold;
        padding: 0.3rem 0.7rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
    .running {
        background-color: rgba(0, 200, 83, 0.2);
        color: #00C853;
    }
    .stopped {
        background-color: rgba(244, 67, 54, 0.2);
        color: #F44336;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">📈 سیستم تشخیص سیگنال معاملاتی</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">تحلیل تکنیکال پیشرفته و سیگنال‌های معاملاتی با اسکن خودکار بازار</div>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    
    # Trading settings
    st.subheader("Trading Settings")
    exchange = st.selectbox(
        "Exchange", 
        AVAILABLE_EXCHANGES, 
        index=AVAILABLE_EXCHANGES.index(st.session_state.config.get('exchange', DEFAULT_SETTINGS['exchange']))
    )
    
    symbol = st.selectbox(
        "Symbol", 
        AVAILABLE_SYMBOLS, 
        index=AVAILABLE_SYMBOLS.index(st.session_state.config.get('symbol', DEFAULT_SETTINGS['symbol']))
    )
    
    timeframe = st.selectbox(
        "Timeframe", 
        AVAILABLE_TIMEFRAMES, 
        index=AVAILABLE_TIMEFRAMES.index(st.session_state.config.get('timeframe', DEFAULT_SETTINGS['timeframe']))
    )
    
    # Strategy settings
    st.subheader("Strategy Settings")
    
    # MACD settings
    st.write("MACD Settings")
    use_macd = st.checkbox("Use MACD", value=st.session_state.config.get('use_macd', DEFAULT_SETTINGS['use_macd']))
    macd_fast = st.number_input("MACD Fast Period", min_value=1, max_value=50, 
                               value=st.session_state.config.get('macd_fast', DEFAULT_SETTINGS['macd_fast']))
    macd_slow = st.number_input("MACD Slow Period", min_value=1, max_value=100, 
                               value=st.session_state.config.get('macd_slow', DEFAULT_SETTINGS['macd_slow']))
    macd_signal = st.number_input("MACD Signal Period", min_value=1, max_value=50, 
                                 value=st.session_state.config.get('macd_signal', DEFAULT_SETTINGS['macd_signal']))
    
    # RSI settings
    st.write("RSI Settings")
    use_rsi = st.checkbox("Use RSI", value=st.session_state.config.get('use_rsi', DEFAULT_SETTINGS['use_rsi']))
    rsi_period = st.number_input("RSI Period", min_value=1, max_value=50, 
                                value=st.session_state.config.get('rsi_period', DEFAULT_SETTINGS['rsi_period']))
    rsi_overbought = st.number_input("RSI Overbought Level", min_value=50, max_value=100, 
                                    value=st.session_state.config.get('rsi_overbought', DEFAULT_SETTINGS['rsi_overbought']))
    rsi_oversold = st.number_input("RSI Oversold Level", min_value=0, max_value=50, 
                                  value=st.session_state.config.get('rsi_oversold', DEFAULT_SETTINGS['rsi_oversold']))
    
    # ATR settings
    st.write("ATR Settings")
    use_atr = st.checkbox("Use ATR", value=st.session_state.config.get('use_atr', DEFAULT_SETTINGS['use_atr']))
    atr_period = st.number_input("ATR Period", min_value=1, max_value=50, 
                                value=st.session_state.config.get('atr_period', DEFAULT_SETTINGS['atr_period']))
    atr_multiplier = st.number_input("ATR Multiplier (for stop loss)", min_value=0.1, max_value=10.0, step=0.1, 
                                    value=st.session_state.config.get('atr_multiplier', DEFAULT_SETTINGS['atr_multiplier']))
    
    # Pattern recognition settings
    st.subheader("Pattern Recognition")
    use_candlestick_patterns = st.checkbox("Use Candlestick Patterns", 
                                          value=st.session_state.config.get('use_candlestick_patterns', 
                                                                          DEFAULT_SETTINGS['use_candlestick_patterns']))
    use_harmonic_patterns = st.checkbox("Use Harmonic Patterns", 
                                       value=st.session_state.config.get('use_harmonic_patterns', 
                                                                       DEFAULT_SETTINGS['use_harmonic_patterns']))
    use_price_action = st.checkbox("Use Price Action", 
                                  value=st.session_state.config.get('use_price_action', 
                                                                  DEFAULT_SETTINGS['use_price_action']))
    
    # Notification settings
    st.subheader("Notification Settings")
    telegram_token = st.text_input("Telegram Bot Token", 
                                  value=st.session_state.config.get('telegram_token', ''), 
                                  type="password")
    telegram_chat_id = st.text_input("Telegram Chat ID", 
                                    value=st.session_state.config.get('telegram_chat_id', ''))
    
    # Signal check interval
    check_interval = st.number_input("Check Interval (minutes)", 
                                    min_value=1, max_value=1440, 
                                    value=st.session_state.config.get('check_interval', DEFAULT_SETTINGS['check_interval']))
    
    # Market scanning settings
    st.subheader("بررسی بازار")
    scan_whole_market = st.checkbox("اسکن خودکار کل بازار", 
                                   value=st.session_state.config.get('scan_whole_market', False),
                                   help="فعال کردن این گزینه باعث می‌شود سیستم به طور خودکار همه ارزها را اسکن کند")
    
    quote_currency = st.selectbox(
        "ارز پایه", 
        ['USDT', 'USD', 'BTC', 'ETH'],
        index=['USDT', 'USD', 'BTC', 'ETH'].index(st.session_state.config.get('quote_currency', 'USDT'))
    )
    
    min_volume = st.number_input(
        "حداقل حجم معاملات 24 ساعته (به دلار)", 
        min_value=10000, 
        max_value=100000000, 
        value=st.session_state.config.get('min_volume', 1000000),
        step=100000
    )

    # Save configuration
    if st.button("ذخیره تنظیمات"):
        # Update configuration
        new_config = {
            'exchange': exchange,
            'symbol': symbol,
            'timeframe': timeframe,
            'use_macd': use_macd,
            'macd_fast': macd_fast,
            'macd_slow': macd_slow,
            'macd_signal': macd_signal,
            'use_rsi': use_rsi,
            'rsi_period': rsi_period,
            'rsi_overbought': rsi_overbought,
            'rsi_oversold': rsi_oversold,
            'use_atr': use_atr,
            'atr_period': atr_period,
            'atr_multiplier': atr_multiplier,
            'use_candlestick_patterns': use_candlestick_patterns,
            'use_harmonic_patterns': use_harmonic_patterns,
            'use_price_action': use_price_action,
            'telegram_token': telegram_token,
            'telegram_chat_id': telegram_chat_id,
            'check_interval': check_interval,
            'scan_whole_market': scan_whole_market,
            'quote_currency': quote_currency,
            'min_volume': min_volume
        }
        
        # Save to session state
        st.session_state.config = new_config
        
        # Save to file
        save_config(new_config)
        
        # Initialize Telegram bot with new settings
        init_telegram_bot()
        
        st.success("تنظیمات با موفقیت ذخیره شد!")

# Main content area
tab1, tab2, tab3 = st.tabs(["Signal Monitor", "Market Data", "Backtesting"])

with tab1:
    st.markdown('<h2 style="border-bottom: 2px solid #00C853; padding-bottom: 10px;">📊 مانیتور سیگنال</h2>', unsafe_allow_html=True)
    
    # Status card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if not st.session_state.running:
            if st.button("🚀 شروع سیگنال‌گیری", use_container_width=True):
                # Initialize the Telegram bot if not already done
                if not st.session_state.bot_initialized:
                    init_telegram_bot()
                
                if st.session_state.bot_initialized or not (telegram_token and telegram_chat_id):
                    st.session_state.running = True
                    # Start the signal generation loop in a separate thread
                    thread = threading.Thread(target=signal_generation_loop, daemon=True)
                    thread.start()
                    st.success("سیگنال‌گیری با موفقیت شروع شد!")
                    st.rerun()
                else:
                    st.error("خطا در اتصال به تلگرام. لطفاً تنظیمات را بررسی کنید.")
        else:
            if st.button("⏹ توقف سیگنال‌گیری", use_container_width=True):
                st.session_state.running = False
                st.success("سیگنال‌گیری متوقف شد!")
                st.rerun()
    
    with col2:
        if st.session_state.last_run:
            st.markdown(f"<p>آخرین بررسی: {st.session_state.last_run.strftime('%Y-%m-%d %H:%M:%S')}</p>", unsafe_allow_html=True)
        
        status_class = "running" if st.session_state.running else "stopped"
        status_text = "فعال" if st.session_state.running else "غیر فعال"
        st.markdown(f'<p>وضعیت: <span class="indicator {status_class}">{status_text}</span></p>', unsafe_allow_html=True)
    
    with col3:
        symbol_count = "همه ارزها" if st.session_state.config.get('scan_whole_market', False) else st.session_state.config.get('symbol', DEFAULT_SETTINGS['symbol'])
        st.markdown(f"<p>ارزهای تحت نظر: <b>{symbol_count}</b></p>", unsafe_allow_html=True)
        signal_count = len(st.session_state.signals) if hasattr(st.session_state, 'signals') else 0
        st.markdown(f"<p>تعداد سیگنال‌ها: <b>{signal_count}</b></p>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display recent signals
    st.markdown('<h3 style="margin-top: 20px;">سیگنال‌های اخیر</h3>', unsafe_allow_html=True)
    
    if not st.session_state.signals:
        st.markdown("""
        <div style="padding: 2rem; border-radius: 0.5rem; background-color: rgba(3, 121, 196, 0.1); margin: 1rem 0;">
            <p style="color: #039BE5; margin: 0; text-align: center; font-weight: 500;">
                هنوز سیگنالی تولید نشده است. برای شروع مانیتورینگ، دکمه شروع سیگنال‌گیری را بزنید.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Custom display for signals with cards
        cols = st.columns(2)
        for i, signal in enumerate(st.session_state.signals):
            signal_type = signal.get("signal_type", "")
            card_class = "signal-long" if signal_type == "LONG" else "signal-short"
            signal_icon = "📈" if signal_type == "LONG" else "📉"
            signal_type_fa = "خرید" if signal_type == "LONG" else "فروش"
            
            col_idx = i % 2
            with cols[col_idx]:
                signal_html = f"""
                <div class="signal-box {card_class}">
                    <h4 style="margin: 0; display: flex; justify-content: space-between;">
                        <span>{signal_icon} {signal.get("symbol", "")}</span>
                        <span style="font-size: 0.8rem;">{signal.get("timestamp", "")}</span>
                    </h4>
                    <p style="margin: 5px 0;">نوع: <b>{signal_type_fa}</b> | استراتژی: <b>{signal.get("strategy", "")}</b></p>
                    <div style="display: flex; justify-content: space-between; margin-top: 10px;">
                        <span>ورود: <b>{signal.get("entry_price", "")}</b></span>
                        <span>هدف ۱: <b>{signal.get("target1", "")}</b></span>
                        <span>هدف ۲: <b>{signal.get("target2", "")}</b></span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                        <span>حد ضرر: <b>{signal.get("stop_loss", "")}</b></span>
                        <span>اهرم: <b>{signal.get("leverage", "")}X</b></span>
                        <span>ریسک/ریوارد: <b>1:{signal.get("risk_reward_ratio2", "")}</b></span>
                    </div>
                </div>
                """
                st.markdown(signal_html, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            # Clear signals button
            if st.button("🧹 پاک کردن سیگنال‌ها", use_container_width=True):
                st.session_state.signals = []
                st.rerun()

with tab2:
    st.markdown('<h2 style="border-bottom: 2px solid #00C853; padding-bottom: 10px;">📊 تحلیل بازار</h2>', unsafe_allow_html=True)
    
    # Market info card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        current_symbol = st.session_state.config.get('symbol', DEFAULT_SETTINGS['symbol'])
        current_exchange = st.session_state.config.get('exchange', DEFAULT_SETTINGS['exchange'])
        st.markdown(f"<p>نماد: <b>{current_symbol}</b></p>", unsafe_allow_html=True)
        st.markdown(f"<p>صرافی: <b>{current_exchange}</b></p>", unsafe_allow_html=True)
    
    with col2:
        current_timeframe = st.session_state.config.get('timeframe', DEFAULT_SETTINGS['timeframe'])
        st.markdown(f"<p>تایم‌فریم: <b>{current_timeframe}</b></p>", unsafe_allow_html=True)
        # Add refresh button
        if st.button("🔄 بارگذاری مجدد داده‌ها", use_container_width=True):
            st.rerun()
    
    with col3:
        # Add manual data check for other symbols
        if not st.session_state.config.get('scan_whole_market', False):
            if st.button("📊 بررسی ارز دیگر", use_container_width=True):
                st.session_state.check_other_symbol = True
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Fetch and display current market data
    try:
        current_symbol = st.session_state.config.get('symbol', DEFAULT_SETTINGS['symbol'])
        current_exchange = st.session_state.config.get('exchange', DEFAULT_SETTINGS['exchange'])
        current_timeframe = st.session_state.config.get('timeframe', DEFAULT_SETTINGS['timeframe'])
        
        with st.spinner("در حال دریافت داده‌های بازار..."):
            df = fetch_market_data(current_exchange, current_symbol, current_timeframe)
        
        if df is not None and not df.empty:
            # Calculate indicators for display
            with st.spinner("در حال محاسبه اندیکاتورها..."):
                df = calculate_indicators(df, st.session_state.config)
            
            # Display current price information
            current_price = df['close'].iloc[-1]
            previous_price = df['close'].iloc[-2]
            price_change = current_price - previous_price
            price_change_pct = (price_change / previous_price) * 100
            price_color = "#00C853" if price_change >= 0 else "#F44336"
            
            # Price info card
            st.markdown(f"""
            <div style="margin-top: 1rem; padding: 1rem; border-radius: 0.5rem; background-color: {price_color}20; border-left: 5px solid {price_color};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h3 style="margin: 0; color: {price_color};">{current_price:.8f}</h3>
                        <p style="margin: 0; font-size: 0.9rem; color: {price_color};">
                            {price_change_pct:.2f}% ({price_change:.8f})
                        </p>
                    </div>
                    <div style="text-align: right;">
                        <p style="margin: 0;">حجم 24 ساعته: <b>{df['volume'].iloc[-1]:.2f}</b></p>
                        <p style="margin: 0;">آخرین به‌روزرسانی: <b>{df.index[-1].strftime('%Y-%m-%d %H:%M')}</b></p>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Create plot
            fig = go.Figure()
            
            # Add candlestick chart
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="قیمت",
                increasing_line_color='#00C853',
                decreasing_line_color='#F44336'
            ))
            
            # Display MACD if enabled
            if st.session_state.config.get('use_macd', DEFAULT_SETTINGS['use_macd']) and 'macd' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['macd'],
                    mode='lines',
                    line=dict(color='#2196F3', width=1.5),
                    name='MACD',
                    yaxis="y2"
                ))
                
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['macd_signal'],
                    mode='lines',
                    line=dict(color='#FF5722', width=1.5),
                    name='سیگنال MACD',
                    yaxis="y2"
                ))
                
                fig.add_trace(go.Bar(
                    x=df.index,
                    y=df['macd_hist'],
                    name='هیستوگرام MACD',
                    marker_color=df['macd_hist'].apply(lambda x: '#00C853' if x > 0 else '#F44336'),
                    yaxis="y2"
                ))
            
            # Display RSI if enabled
            if st.session_state.config.get('use_rsi', DEFAULT_SETTINGS['use_rsi']) and 'rsi' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['rsi'],
                    mode='lines',
                    line=dict(color='#9C27B0', width=1.5),
                    name='RSI',
                    yaxis="y3"
                ))
                
                # Add overbought and oversold lines
                fig.add_trace(go.Scatter(
                    x=[df.index[0], df.index[-1]],
                    y=[st.session_state.config.get('rsi_overbought', DEFAULT_SETTINGS['rsi_overbought']), 
                       st.session_state.config.get('rsi_overbought', DEFAULT_SETTINGS['rsi_overbought'])],
                    mode='lines',
                    line=dict(color='#F44336', dash='dash'),
                    name='اشباع خرید',
                    yaxis="y3"
                ))
                
                fig.add_trace(go.Scatter(
                    x=[df.index[0], df.index[-1]],
                    y=[st.session_state.config.get('rsi_oversold', DEFAULT_SETTINGS['rsi_oversold']), 
                       st.session_state.config.get('rsi_oversold', DEFAULT_SETTINGS['rsi_oversold'])],
                    mode='lines',
                    line=dict(color='#00C853', dash='dash'),
                    name='اشباع فروش',
                    yaxis="y3"
                ))
            
            # Display ATR if enabled
            if st.session_state.config.get('use_atr', DEFAULT_SETTINGS['use_atr']) and 'atr' in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index,
                    y=df['atr'],
                    mode='lines',
                    line=dict(color='#FF9800', width=1.5),
                    name='ATR',
                    yaxis="y4"
                ))
            
            # Update layout for additional y-axes and dark mode
            fig.update_layout(
                title={
                    'text': f"{current_symbol} - {current_timeframe}",
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top',
                    'font': {'size': 24, 'color': '#FFFFFF'}
                },
                yaxis=dict(
                    title="قیمت",
                    domain=[0.6, 1],
                    gridcolor="#132F4C",
                    titlefont=dict(color="#FFFFFF"),
                    tickfont=dict(color="#FFFFFF")
                ),
                yaxis2=dict(
                    title="MACD",
                    domain=[0.4, 0.6],
                    anchor="x",
                    overlaying="y",
                    side="right",
                    gridcolor="#132F4C",
                    titlefont=dict(color="#FFFFFF"),
                    tickfont=dict(color="#FFFFFF")
                ) if st.session_state.config.get('use_macd', DEFAULT_SETTINGS['use_macd']) else None,
                yaxis3=dict(
                    title="RSI",
                    domain=[0.2, 0.4],
                    anchor="x",
                    overlaying="y",
                    side="right",
                    gridcolor="#132F4C",
                    titlefont=dict(color="#FFFFFF"),
                    tickfont=dict(color="#FFFFFF")
                ) if st.session_state.config.get('use_rsi', DEFAULT_SETTINGS['use_rsi']) else None,
                yaxis4=dict(
                    title="ATR",
                    domain=[0, 0.2],
                    anchor="x",
                    overlaying="y",
                    side="right",
                    gridcolor="#132F4C",
                    titlefont=dict(color="#FFFFFF"),
                    tickfont=dict(color="#FFFFFF")
                ) if st.session_state.config.get('use_atr', DEFAULT_SETTINGS['use_atr']) else None,
                xaxis=dict(
                    rangeslider=dict(visible=True),
                    type="date",
                    gridcolor="#132F4C",
                    titlefont=dict(color="#FFFFFF"),
                    tickfont=dict(color="#FFFFFF")
                ),
                height=700,
                dragmode='zoom',
                showlegend=True,
                legend=dict(
                    orientation="h",
                    y=1.1,
                    font=dict(color="#FFFFFF")
                ),
                plot_bgcolor="#0A1929",
                paper_bgcolor="#0A1929",
                margin=dict(l=10, r=10, t=80, b=10)
            )
            
            # Display plot
            st.plotly_chart(fig, use_container_width=True)
            
            # Display recent market data
            st.markdown('<h3 style="margin-top: 20px;">داده‌های اخیر بازار</h3>', unsafe_allow_html=True)
            st.dataframe(df.tail(10).style.background_gradient(cmap='YlGnBu', axis=0), use_container_width=True)
        else:
            st.error(f"خطا در دریافت داده‌های بازار برای {current_symbol} از {current_exchange}")
    
    except Exception as e:
        st.error(f"خطا در نمایش داده‌های بازار: {str(e)}")

with tab3:
    st.markdown('<h2 style="border-bottom: 2px solid #00C853; padding-bottom: 10px;">🔍 آزمایش برگشتی</h2>', unsafe_allow_html=True)
    
    # Backtesting configuration card
    st.markdown('<div class="card">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        symbol = st.session_state.config.get('symbol', DEFAULT_SETTINGS['symbol'])
        st.markdown(f"<p>نماد: <b>{symbol}</b></p>", unsafe_allow_html=True)
        
        backtest_days = st.slider("دوره آزمایش (روز)", min_value=7, max_value=365, value=30)
    
    with col2:
        exchange_id = st.session_state.config.get('exchange', DEFAULT_SETTINGS['exchange'])
        st.markdown(f"<p>صرافی: <b>{exchange_id}</b></p>", unsafe_allow_html=True)
        
        timeframe = st.session_state.config.get('timeframe', DEFAULT_SETTINGS['timeframe'])
        st.markdown(f"<p>تایم‌فریم: <b>{timeframe}</b></p>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("<p>&nbsp;</p>", unsafe_allow_html=True)
        if st.button("🚀 اجرای آزمایش برگشتی", use_container_width=True):
            with st.spinner("در حال اجرای آزمایش برگشتی..."):
                try:
                    # Get configuration
                    config = st.session_state.config
                    
                    # Run the backtest
                    backtest_results = run_backtest(exchange_id, symbol, timeframe, backtest_days, config)
                    
                    if backtest_results:
                        st.session_state.backtest_results = backtest_results
                        st.rerun()
                
                except Exception as e:
                    st.error(f"خطا در آزمایش برگشتی: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Display backtest results if available
    if hasattr(st.session_state, 'backtest_results') and st.session_state.backtest_results:
        backtest_results = st.session_state.backtest_results
        
        # Create performance metrics card
        st.markdown('<div class="card" style="margin-top: 20px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0; border-bottom: 1px solid rgba(250, 250, 250, 0.2); padding-bottom: 10px;">نتایج آزمایش برگشتی</h3>', unsafe_allow_html=True)
        
        # Display performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            win_rate = backtest_results.get('win_rate', 0)
            win_rate_color = "#00C853" if win_rate > 50 else "#F44336"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4 style="margin: 0;">نرخ موفقیت</h4>
                <p style="font-size: 1.8rem; color: {win_rate_color}; margin: 0;">{win_rate:.1f}%</p>
                <p style="font-size: 0.8rem; margin: 0;">{backtest_results.get('winning_signals', 0)} از {backtest_results.get('total_signals', 0)}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            avg_profit = backtest_results.get('avg_profit', 0)
            profit_color = "#00C853" if avg_profit > 0 else "#F44336"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4 style="margin: 0;">میانگین سود</h4>
                <p style="font-size: 1.8rem; color: {profit_color}; margin: 0;">{avg_profit:.1f}%</p>
                <p style="font-size: 0.8rem; margin: 0;">در هر معامله</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            profit_factor = backtest_results.get('profit_factor', 0)
            pf_color = "#00C853" if profit_factor > 1 else "#F44336"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4 style="margin: 0;">ضریب سود</h4>
                <p style="font-size: 1.8rem; color: {pf_color}; margin: 0;">{profit_factor:.2f}</p>
                <p style="font-size: 0.8rem; margin: 0;">سود کل / ضرر کل</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            max_drawdown = backtest_results.get('max_drawdown', 0)
            dd_color = "#F44336"
            st.markdown(f"""
            <div style="text-align: center;">
                <h4 style="margin: 0;">حداکثر افت سرمایه</h4>
                <p style="font-size: 1.8rem; color: {dd_color}; margin: 0;">{max_drawdown:.1f}%</p>
                <p style="font-size: 0.8rem; margin: 0;">در طول دوره آزمایش</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Create equity curve
        if "signals" in backtest_results and backtest_results["signals"]:
            # Initialize equity curve
            config = st.session_state.config
            equity = [100]  # Start with 100 units
            dates = []
            
            # Sort signals by date
            sorted_signals = sorted(backtest_results["signals"], key=lambda x: x.get("timestamp", ""))
            
            for signal in sorted_signals:
                pnl = signal.get("profit_loss", 0)
                dates.append(signal.get("timestamp", ""))
                if pnl:
                    risk = config.get('risk_percent', 1.0) / 100  # Convert to decimal
                    equity.append(equity[-1] * (1 + (pnl / 100 * risk)))
                else:
                    equity.append(equity[-1])
            
            # Create the equity curve plot
            if len(equity) > 1:
                # Card for equity curve
                st.markdown('<div class="card" style="margin-top: 20px;">', unsafe_allow_html=True)
                st.markdown('<h3 style="margin-top: 0; border-bottom: 1px solid rgba(250, 250, 250, 0.2); padding-bottom: 10px;">نمودار رشد سرمایه</h3>', unsafe_allow_html=True)
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=list(range(len(equity))),
                    y=equity,
                    mode='lines',
                    name='رشد سرمایه',
                    line=dict(color='#00C853' if equity[-1] > equity[0] else '#F44336', width=2)
                ))
                
                # Add a reference line at 100%
                fig.add_trace(go.Scatter(
                    x=[0, len(equity)-1],
                    y=[100, 100],
                    mode='lines',
                    name='نقطه شروع',
                    line=dict(color='#FFFFFF', width=1, dash='dash')
                ))
                
                # Calculate final profit/loss percentage
                final_pnl_pct = ((equity[-1] - equity[0]) / equity[0]) * 100
                
                fig.update_layout(
                    title={
                        'text': f"رشد سرمایه (شروع: 100، پایان: {equity[-1]:.2f}, سود/ضرر: {final_pnl_pct:.2f}%)",
                        'y': 0.95,
                        'x': 0.5,
                        'xanchor': 'center',
                        'yanchor': 'top',
                        'font': {'size': 18, 'color': '#FFFFFF'}
                    },
                    xaxis_title="تعداد معاملات",
                    yaxis_title="سرمایه",
                    height=400,
                    plot_bgcolor="#0A1929",
                    paper_bgcolor="#0A1929",
                    font=dict(color="#FFFFFF"),
                    xaxis=dict(gridcolor="#132F4C"),
                    yaxis=dict(gridcolor="#132F4C")
                )
                
                st.plotly_chart(fig, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Display signals table
            st.markdown('<div class="card" style="margin-top: 20px;">', unsafe_allow_html=True)
            st.markdown('<h3 style="margin-top: 0; border-bottom: 1px solid rgba(250, 250, 250, 0.2); padding-bottom: 10px;">سیگنال‌های معاملاتی</h3>', unsafe_allow_html=True)
            
            # Convert signals for display
            signals_display = []
            for signal in sorted_signals:
                signal_type = signal.get("signal_type", "")
                signal_type_fa = "خرید" if signal_type == "LONG" else "فروش"
                exit_status = signal.get("status", "")
                exit_status_fa = "باز" if exit_status == "OPEN" else exit_status
                
                signals_display.append({
                    "تاریخ": signal.get("timestamp", ""),
                    "نوع": signal_type_fa,
                    "استراتژی": signal.get("strategy", ""),
                    "قیمت ورود": signal.get("entry_price", ""),
                    "قیمت خروج": signal.get("exit_price", ""),
                    "سود/ضرر": f"{signal.get('profit_loss', 0):.2f}%" if signal.get('profit_loss') else "-",
                    "وضعیت": exit_status_fa
                })
            
            signals_df = pd.DataFrame(signals_display)
            
            # Color-code the dataframe
            def color_profit_loss(val):
                try:
                    if isinstance(val, str) and "%" in val:
                        num = float(val.replace("%", ""))
                        if num > 0:
                            return 'color: #00C853'
                        elif num < 0:
                            return 'color: #F44336'
                except:
                    pass
                return ''
            
            styled_df = signals_df.style.applymap(color_profit_loss, subset=['سود/ضرر'])
            
            st.dataframe(styled_df, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("هیچ سیگنالی در طول دوره آزمایش تولید نشده است.")
    
    else:
        # Show placeholder message when no backtest has been run
        st.markdown("""
        <div style="padding: 2rem; border-radius: 0.5rem; background-color: rgba(3, 121, 196, 0.1); margin-top: 1rem; text-align: center;">
            <h3 style="color: #039BE5; margin: 0; padding-bottom: 1rem;">آزمایش برگشتی</h3>
            <p style="color: #B0BEC5;">
                با استفاده از ابزار آزمایش برگشتی می‌توانید عملکرد استراتژی‌های معاملاتی خود را روی داده‌های تاریخی بررسی کنید.<br>
                برای شروع، دوره زمانی مورد نظر را انتخاب کرده و دکمه «اجرای آزمایش برگشتی» را بزنید.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
    # Strategy performance comparison - will be implemented when we have results
    if hasattr(st.session_state, 'backtest_results') and st.session_state.backtest_results:
        st.markdown('<div class="card" style="margin-top: 20px;">', unsafe_allow_html=True)
        st.markdown('<h3 style="margin-top: 0; border-bottom: 1px solid rgba(250, 250, 250, 0.2); padding-bottom: 10px;">مقایسه عملکرد استراتژی‌ها</h3>', unsafe_allow_html=True)
        
        # Just a placeholder for now, but will be expanded in future
        st.markdown("""
        <div style="display: flex; justify-content: space-around; text-align: center;">
            <div>
                <h4 style="color: #00C853;">MACD + RSI</h4>
                <p>بهترین استراتژی‌ها در آزمایش</p>
            </div>
            <div>
                <h4 style="color: #FFC107;">الگوهای هارمونیک</h4>
                <p>استراتژی‌های با ریسک متوسط</p>
            </div>
            <div>
                <h4 style="color: #F44336;">الگوهای کندلی</h4>
                <p>استراتژی‌های با ریسک بالا</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("Trading Signal Generator | ⚠️ Trading involves risk. Always do your own research.")
