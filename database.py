import os
import sqlalchemy as sa
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Create a base class for declarative class definitions
Base = declarative_base()

# Create signal table model
class Signal(Base):
    __tablename__ = 'signals'
    
    id = Column(Integer, primary_key=True)
    signal_id = Column(String(50), unique=True)
    timestamp = Column(DateTime, default=datetime.now)
    symbol = Column(String(20))
    signal_type = Column(String(10))  # LONG or SHORT
    strategy = Column(String(100))
    entry_price = Column(Float)
    current_price = Column(Float)
    stop_loss = Column(Float)
    target1 = Column(Float)
    target2 = Column(Float)
    risk_reward_ratio1 = Column(Float)
    risk_reward_ratio2 = Column(Float)
    risk_percent = Column(Float)
    leverage = Column(Integer)
    status = Column(String(20), default='OPEN')  # OPEN, CLOSED, HIT_TARGET1, HIT_TARGET2, STOPPED
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    profit_loss = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)
    telegram_sent = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<Signal(id={self.id}, symbol={self.symbol}, type={self.signal_type}, strategy={self.strategy})>"

# Create configuration table model
class Configuration(Base):
    __tablename__ = 'configurations'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    exchange = Column(String(50))
    symbol = Column(String(20))
    timeframe = Column(String(10))
    check_interval = Column(Integer)
    use_macd = Column(Boolean)
    macd_fast = Column(Integer)
    macd_slow = Column(Integer)
    macd_signal = Column(Integer)
    use_rsi = Column(Boolean)
    rsi_period = Column(Integer)
    rsi_overbought = Column(Integer)
    rsi_oversold = Column(Integer)
    use_atr = Column(Boolean)
    atr_period = Column(Integer)
    atr_multiplier = Column(Float)
    use_candlestick_patterns = Column(Boolean)
    use_harmonic_patterns = Column(Boolean)
    use_price_action = Column(Boolean)
    telegram_token = Column(String(100), nullable=True)
    telegram_chat_id = Column(String(100), nullable=True)
    tp1_factor = Column(Float)
    tp2_factor = Column(Float)
    default_leverage = Column(Integer)
    risk_percent = Column(Float)
    is_active = Column(Boolean, default=True)
    config_json = Column(Text)  # Store the full config in JSON format for future-proofing
    
    def __repr__(self):
        return f"<Configuration(id={self.id}, name={self.name}, symbol={self.symbol})>"

# Create backtest results table model
class BacktestResult(Base):
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.now)
    exchange = Column(String(50))
    symbol = Column(String(20))
    timeframe = Column(String(10))
    days = Column(Integer)
    total_signals = Column(Integer)
    winning_signals = Column(Integer)
    losing_signals = Column(Integer)
    win_rate = Column(Float)
    avg_profit = Column(Float)
    max_drawdown = Column(Float)
    profit_factor = Column(Float)
    strategy_performance = Column(Text)  # Store strategy performance as JSON
    config_json = Column(Text)  # Store the config used as JSON
    
    def __repr__(self):
        return f"<BacktestResult(id={self.id}, symbol={self.symbol}, win_rate={self.win_rate})>"

# Create database connection
def get_engine():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Create SQLAlchemy engine
    engine = create_engine(database_url)
    return engine

def init_db():
    engine = get_engine()
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session factory
    Session = sessionmaker(bind=engine)
    return Session()

def save_signal(signal_data):
    """
    Save a signal to the database
    
    Args:
        signal_data (dict): Signal data dictionary
    
    Returns:
        Signal: The saved Signal object
    """
    session = init_db()
    
    try:
        # Check if signal already exists
        existing_signal = session.query(Signal).filter_by(signal_id=signal_data.get('id')).first()
        
        if existing_signal:
            # Update existing signal
            for key, value in signal_data.items():
                if key != 'id':
                    setattr(existing_signal, key, value)
            signal = existing_signal
        else:
            # Create new signal
            signal = Signal(
                signal_id=signal_data.get('id'),
                timestamp=datetime.strptime(signal_data.get('timestamp'), '%Y-%m-%d %H:%M:%S') if isinstance(signal_data.get('timestamp'), str) else signal_data.get('timestamp'),
                symbol=signal_data.get('symbol'),
                signal_type=signal_data.get('signal_type'),
                strategy=signal_data.get('strategy'),
                entry_price=signal_data.get('entry_price'),
                current_price=signal_data.get('current_price'),
                stop_loss=signal_data.get('stop_loss'),
                target1=signal_data.get('target1'),
                target2=signal_data.get('target2'),
                risk_reward_ratio1=signal_data.get('risk_reward_ratio1'),
                risk_reward_ratio2=signal_data.get('risk_reward_ratio2'),
                risk_percent=signal_data.get('risk_percent'),
                leverage=signal_data.get('leverage'),
                telegram_sent=False
            )
            
        session.add(signal)
        session.commit()
        return signal
    
    except Exception as e:
        session.rollback()
        print(f"Error saving signal to database: {str(e)}")
        raise
    
    finally:
        session.close()

def get_signals(limit=100, open_only=False):
    """
    Get signals from the database
    
    Args:
        limit (int): Maximum number of signals to return
        open_only (bool): Only return open signals
        
    Returns:
        list: List of Signal objects
    """
    session = init_db()
    
    try:
        query = session.query(Signal)
        
        if open_only:
            query = query.filter(Signal.status == 'OPEN')
        
        return query.order_by(Signal.timestamp.desc()).limit(limit).all()
    
    except Exception as e:
        print(f"Error getting signals from database: {str(e)}")
        return []
    
    finally:
        session.close()

def update_signal_status(signal_id, status, exit_price=None, exit_time=None, profit_loss=None, exit_reason=None):
    """
    Update the status of a signal
    
    Args:
        signal_id (str): Signal ID
        status (str): New status
        exit_price (float, optional): Exit price
        exit_time (datetime, optional): Exit time
        profit_loss (float, optional): Profit/loss percentage
        exit_reason (str, optional): Reason for exit
        
    Returns:
        bool: True if successful, False otherwise
    """
    session = init_db()
    
    try:
        signal = session.query(Signal).filter_by(signal_id=signal_id).first()
        
        if signal:
            signal.status = status
            
            if exit_price is not None:
                signal.exit_price = exit_price
                
            if exit_time is not None:
                signal.exit_time = exit_time
                
            if profit_loss is not None:
                signal.profit_loss = profit_loss
                
            if exit_reason is not None:
                signal.exit_reason = exit_reason
                
            session.commit()
            return True
        
        return False
    
    except Exception as e:
        session.rollback()
        print(f"Error updating signal status: {str(e)}")
        return False
    
    finally:
        session.close()

def save_configuration(config_data, name="default"):
    """
    Save a configuration to the database
    
    Args:
        config_data (dict): Configuration data dictionary
        name (str): Configuration name
        
    Returns:
        Configuration: The saved Configuration object
    """
    import json
    session = init_db()
    
    try:
        # Check if configuration already exists
        existing_config = session.query(Configuration).filter_by(name=name).first()
        
        if existing_config:
            # Update existing configuration
            existing_config.updated_at = datetime.now()
            existing_config.exchange = config_data.get('exchange')
            existing_config.symbol = config_data.get('symbol')
            existing_config.timeframe = config_data.get('timeframe')
            existing_config.check_interval = config_data.get('check_interval')
            existing_config.use_macd = config_data.get('use_macd')
            existing_config.macd_fast = config_data.get('macd_fast')
            existing_config.macd_slow = config_data.get('macd_slow')
            existing_config.macd_signal = config_data.get('macd_signal')
            existing_config.use_rsi = config_data.get('use_rsi')
            existing_config.rsi_period = config_data.get('rsi_period')
            existing_config.rsi_overbought = config_data.get('rsi_overbought')
            existing_config.rsi_oversold = config_data.get('rsi_oversold')
            existing_config.use_atr = config_data.get('use_atr')
            existing_config.atr_period = config_data.get('atr_period')
            existing_config.atr_multiplier = config_data.get('atr_multiplier')
            existing_config.use_candlestick_patterns = config_data.get('use_candlestick_patterns')
            existing_config.use_harmonic_patterns = config_data.get('use_harmonic_patterns')
            existing_config.use_price_action = config_data.get('use_price_action')
            existing_config.telegram_token = config_data.get('telegram_token')
            existing_config.telegram_chat_id = config_data.get('telegram_chat_id')
            existing_config.tp1_factor = config_data.get('tp1_factor')
            existing_config.tp2_factor = config_data.get('tp2_factor')
            existing_config.default_leverage = config_data.get('default_leverage')
            existing_config.risk_percent = config_data.get('risk_percent')
            existing_config.config_json = json.dumps(config_data)
            config = existing_config
        else:
            # Create new configuration
            config = Configuration(
                name=name,
                exchange=config_data.get('exchange'),
                symbol=config_data.get('symbol'),
                timeframe=config_data.get('timeframe'),
                check_interval=config_data.get('check_interval'),
                use_macd=config_data.get('use_macd'),
                macd_fast=config_data.get('macd_fast'),
                macd_slow=config_data.get('macd_slow'),
                macd_signal=config_data.get('macd_signal'),
                use_rsi=config_data.get('use_rsi'),
                rsi_period=config_data.get('rsi_period'),
                rsi_overbought=config_data.get('rsi_overbought'),
                rsi_oversold=config_data.get('rsi_oversold'),
                use_atr=config_data.get('use_atr'),
                atr_period=config_data.get('atr_period'),
                atr_multiplier=config_data.get('atr_multiplier'),
                use_candlestick_patterns=config_data.get('use_candlestick_patterns'),
                use_harmonic_patterns=config_data.get('use_harmonic_patterns'),
                use_price_action=config_data.get('use_price_action'),
                telegram_token=config_data.get('telegram_token'),
                telegram_chat_id=config_data.get('telegram_chat_id'),
                tp1_factor=config_data.get('tp1_factor'),
                tp2_factor=config_data.get('tp2_factor'),
                default_leverage=config_data.get('default_leverage'),
                risk_percent=config_data.get('risk_percent'),
                config_json=json.dumps(config_data)
            )
            
        session.add(config)
        session.commit()
        return config
    
    except Exception as e:
        session.rollback()
        print(f"Error saving configuration to database: {str(e)}")
        raise
    
    finally:
        session.close()

def get_configuration(name="default"):
    """
    Get a configuration from the database
    
    Args:
        name (str): Configuration name
        
    Returns:
        dict: Configuration data dictionary
    """
    import json
    session = init_db()
    
    try:
        config = session.query(Configuration).filter_by(name=name).first()
        
        if config and config.config_json:
            return json.loads(config.config_json)
        
        return None
    
    except Exception as e:
        print(f"Error getting configuration from database: {str(e)}")
        return None
    
    finally:
        session.close()

def save_backtest_result(result_data):
    """
    Save a backtest result to the database
    
    Args:
        result_data (dict): Backtest result data dictionary
        
    Returns:
        BacktestResult: The saved BacktestResult object
    """
    import json
    session = init_db()
    
    try:
        # Create new backtest result
        backtest_result = BacktestResult(
            exchange=result_data.get('exchange'),
            symbol=result_data.get('symbol'),
            timeframe=result_data.get('timeframe'),
            days=result_data.get('days'),
            total_signals=result_data.get('total_signals'),
            winning_signals=result_data.get('winning_signals'),
            losing_signals=result_data.get('losing_signals'),
            win_rate=result_data.get('win_rate'),
            avg_profit=result_data.get('avg_profit'),
            max_drawdown=result_data.get('max_drawdown'),
            profit_factor=result_data.get('profit_factor'),
            strategy_performance=json.dumps(result_data.get('strategy_performance', {})),
            config_json=json.dumps(result_data.get('config', {}))
        )
            
        session.add(backtest_result)
        session.commit()
        return backtest_result
    
    except Exception as e:
        session.rollback()
        print(f"Error saving backtest result to database: {str(e)}")
        raise
    
    finally:
        session.close()

def get_backtest_results(limit=10):
    """
    Get backtest results from the database
    
    Args:
        limit (int): Maximum number of results to return
        
    Returns:
        list: List of BacktestResult objects
    """
    session = init_db()
    
    try:
        return session.query(BacktestResult).order_by(BacktestResult.timestamp.desc()).limit(limit).all()
    
    except Exception as e:
        print(f"Error getting backtest results from database: {str(e)}")
        return []
    
    finally:
        session.close()

def mark_signal_telegram_sent(signal_id):
    """
    Mark a signal as sent to Telegram
    
    Args:
        signal_id (str): Signal ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    session = init_db()
    
    try:
        signal = session.query(Signal).filter_by(signal_id=signal_id).first()
        
        if signal:
            signal.telegram_sent = True
            session.commit()
            return True
        
        return False
    
    except Exception as e:
        session.rollback()
        print(f"Error marking signal as sent to Telegram: {str(e)}")
        return False
    
    finally:
        session.close()

def check_pending_signals():
    """
    Check for pending signals that haven't been sent to Telegram
    
    Returns:
        list: List of Signal objects
    """
    session = init_db()
    
    try:
        return session.query(Signal).filter_by(telegram_sent=False).all()
    
    except Exception as e:
        print(f"Error checking pending signals: {str(e)}")
        return []
    
    finally:
        session.close()