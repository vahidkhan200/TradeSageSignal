import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import fetch_historical_data
from technical_analysis import calculate_indicators
from pattern_recognition import analyze_patterns
from signal_generator import generate_signals, filter_conflicting_signals

def run_backtest(exchange_id, symbol, timeframe, days, config):
    """
    Run a backtest of the trading strategy over a specified period
    
    Args:
        exchange_id (str): Exchange identifier
        symbol (str): Trading pair symbol
        timeframe (str): Timeframe for the data
        days (int): Number of days to backtest
        config (dict): Configuration for signal generation
        
    Returns:
        dict: Backtest results
    """
    try:
        # Calculate start and end dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Fetch historical data
        df = fetch_historical_data(exchange_id, symbol, timeframe, start_date, end_date)
        
        if df is None or df.empty:
            print(f"No historical data available for {symbol} on {exchange_id}")
            return None
        
        # Calculate indicators
        df = calculate_indicators(df, config)
        
        # Analyze patterns
        df = analyze_patterns(df, config)
        
        # Run through the data and generate signals
        signals = []
        position = None
        
        for i in range(1, len(df)):
            # Get the current row
            current_df = df.iloc[:i+1]
            
            # Generate signals for the current row
            new_signals = generate_signals(current_df, config)
            new_signals = filter_conflicting_signals(new_signals)
            
            for signal in new_signals:
                # Add the signal timestamp
                signal['timestamp'] = df.index[i].strftime('%Y-%m-%d %H:%M:%S')
                
                # Initialize position tracking data
                signal['exit_price'] = None
                signal['exit_time'] = None
                signal['profit_loss'] = None
                signal['exit_reason'] = None
                
                signals.append(signal)
        
        # Simulate trades and calculate results
        for i, signal in enumerate(signals):
            # Get signal details
            try:
                entry_time_str = signal['timestamp']
                entry_time = pd.to_datetime(entry_time_str)
                entry_price = signal['entry_price']
                stop_loss = signal['stop_loss']
                target1 = signal['target1']
                target2 = signal['target2']
                signal_type = signal['signal_type']
                
                # Find data after entry - safely handle any timestamp issues
                try:
                    entry_idx = df.index.get_indexer([entry_time], method='nearest')[0]
                except:
                    # If there's an issue with direct indexing, find the closest time
                    time_diffs = [(idx, abs(idx - entry_time)) for idx in df.index]
                    closest_time = min(time_diffs, key=lambda x: x[1])[0]
                    entry_idx = df.index.get_loc(closest_time)
                    
                future_data = df.iloc[entry_idx+1:]
            except Exception as e:
                print(f"Error processing signal timestamp: {e}, signal: {signal}")
                # Skip this signal
                continue
            
            if future_data.empty:
                # Signal was at the end of the data, no future data to evaluate
                signal['exit_price'] = entry_price
                signal['exit_time'] = entry_time.strftime('%Y-%m-%d %H:%M:%S')
                signal['profit_loss'] = 0
                signal['exit_reason'] = 'End of data'
                continue
            
            # Initialize variables for tracking the trade
            exit_price = None
            exit_time = None
            profit_loss = None
            exit_reason = None
            
            # Simulate the trade
            for idx, row in future_data.iterrows():
                high = row['high']
                low = row['low']
                close = row['close']
                
                # Check for stop loss hit
                if signal_type == 'LONG' and low <= stop_loss:
                    exit_price = stop_loss
                    exit_time = idx
                    profit_loss = (exit_price - entry_price) / entry_price * 100
                    exit_reason = 'Stop Loss'
                    break
                
                elif signal_type == 'SHORT' and high >= stop_loss:
                    exit_price = stop_loss
                    exit_time = idx
                    profit_loss = (entry_price - exit_price) / entry_price * 100
                    exit_reason = 'Stop Loss'
                    break
                
                # Check for target1 hit
                if signal_type == 'LONG' and high >= target1:
                    exit_price = target1
                    exit_time = idx
                    profit_loss = (exit_price - entry_price) / entry_price * 100
                    exit_reason = 'Target 1'
                    break
                
                elif signal_type == 'SHORT' and low <= target1:
                    exit_price = target1
                    exit_time = idx
                    profit_loss = (entry_price - exit_price) / entry_price * 100
                    exit_reason = 'Target 1'
                    break
                
                # Check for target2 hit (rarely but possible)
                if signal_type == 'LONG' and high >= target2:
                    exit_price = target2
                    exit_time = idx
                    profit_loss = (exit_price - entry_price) / entry_price * 100
                    exit_reason = 'Target 2'
                    break
                
                elif signal_type == 'SHORT' and low <= target2:
                    exit_price = target2
                    exit_time = idx
                    profit_loss = (entry_price - exit_price) / entry_price * 100
                    exit_reason = 'Target 2'
                    break
            
            # If trade hasn't exited, use the last close price
            if exit_price is None:
                exit_price = future_data.iloc[-1]['close']
                exit_time = future_data.index[-1]
                
                if signal_type == 'LONG':
                    profit_loss = (exit_price - entry_price) / entry_price * 100
                else:  # SHORT
                    profit_loss = (entry_price - exit_price) / entry_price * 100
                
                exit_reason = 'End of data'
            
            # Update signal with trade results
            signal['exit_price'] = float(exit_price)
            signal['exit_time'] = exit_time.strftime('%Y-%m-%d %H:%M:%S')
            signal['profit_loss'] = float(profit_loss)
            signal['exit_reason'] = exit_reason
        
        # Calculate performance metrics
        total_signals = len(signals)
        winning_signals = len([s for s in signals if s['profit_loss'] > 0])
        losing_signals = len([s for s in signals if s['profit_loss'] <= 0])
        
        if total_signals > 0:
            win_rate = (winning_signals / total_signals) * 100
        else:
            win_rate = 0
        
        # Calculate average profit
        if total_signals > 0:
            avg_profit = sum([s['profit_loss'] for s in signals]) / total_signals
        else:
            avg_profit = 0
        
        # Calculate maximum drawdown
        if total_signals > 0:
            # Sort signals by timestamp
            sorted_signals = sorted(signals, key=lambda s: s['timestamp'])
            
            # Calculate cumulative returns
            equity_curve = [100]  # Start with 100 units
            for signal in sorted_signals:
                profit_loss = signal['profit_loss'] / 100  # Convert to decimal
                equity_curve.append(equity_curve[-1] * (1 + profit_loss))
            
            # Calculate drawdown
            running_max = np.maximum.accumulate(equity_curve)
            drawdown = ((running_max - equity_curve) / running_max) * 100
            max_drawdown = max(drawdown)
        else:
            max_drawdown = 0
        
        # Calculate profit factor
        winning_sum = sum([s['profit_loss'] for s in signals if s['profit_loss'] > 0])
        losing_sum = abs(sum([s['profit_loss'] for s in signals if s['profit_loss'] < 0]))
        
        if losing_sum > 0:
            profit_factor = winning_sum / losing_sum
        else:
            profit_factor = winning_sum if winning_sum > 0 else 0
        
        # Prepare strategy performance comparison
        strategy_performance = {}
        
        for signal in signals:
            strategy = signal['strategy']
            if strategy not in strategy_performance:
                strategy_performance[strategy] = {
                    'count': 0,
                    'win_count': 0,
                    'loss_count': 0,
                    'profit_sum': 0,
                    'loss_sum': 0
                }
            
            strategy_performance[strategy]['count'] += 1
            
            if signal['profit_loss'] > 0:
                strategy_performance[strategy]['win_count'] += 1
                strategy_performance[strategy]['profit_sum'] += signal['profit_loss']
            else:
                strategy_performance[strategy]['loss_count'] += 1
                strategy_performance[strategy]['loss_sum'] += abs(signal['profit_loss'])
        
        # Calculate win rate and profit factor for each strategy
        for strategy, perf in strategy_performance.items():
            perf['win_rate'] = (perf['win_count'] / perf['count']) * 100 if perf['count'] > 0 else 0
            
            if perf['loss_sum'] > 0:
                perf['profit_factor'] = perf['profit_sum'] / perf['loss_sum']
            else:
                perf['profit_factor'] = perf['profit_sum'] if perf['profit_sum'] > 0 else 0
        
        # Prepare the results
        results = {
            'total_signals': total_signals,
            'winning_signals': winning_signals,
            'losing_signals': losing_signals,
            'win_rate': win_rate,
            'avg_profit': avg_profit,
            'max_drawdown': max_drawdown,
            'profit_factor': profit_factor,
            'signals': signals,
            'strategy_performance': strategy_performance
        }
        
        return results
    
    except Exception as e:
        print(f"Error in backtesting: {str(e)}")
        return None
