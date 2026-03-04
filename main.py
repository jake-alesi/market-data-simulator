# main.py
# ACTIVE MODE: Runs the simulation WITH your strategy injected.
# Use this to test Execution, Slippage, and PnL.

import numpy as np
import pandas as pd
import config
from physics import MarketPhysics
from market import OrderBook
from agents import Agent

# IMPORT YOUR STRATEGY
from my_strategy import UserStrategy

def run_active_simulation():
    print(f"--- INITIALIZING ACTIVE SIMULATION ---")
    print(f"Timeframe: {config.TIMEFRAME} | Total Steps: {config.N_STEPS}")
    print(f"Trading: Asset STK_000 ONLY")
    
    # 1. Init Physics
    physics = MarketPhysics()
    vol_path = physics.get_volatility_path()
    
    # 2. Init Assets (We simulate N assets, but you only trade the first one)
    books = [OrderBook() for _ in range(config.N_ASSETS)]
    
    # 3. Init Market Agents
    agents = []
    for _ in range(config.N_TREND_FOLLOWERS): agents.append(Agent('Trend'))
    for _ in range(config.N_MEAN_REVERTERS): agents.append(Agent('MeanRev'))
    for _ in range(config.N_INSTITUTIONAL): agents.append(Agent('Institutional'))
    for _ in range(config.N_NOISE_TRADERS): agents.append(Agent('Noise'))
    
    # 4. Init YOUR Strategy
    my_algo = UserStrategy()
    my_pnl_history = []
    
    # 5. Storage
    price_history = np.zeros((config.N_STEPS, config.N_ASSETS))
    for i in range(config.N_ASSETS): 
        price_history[0, i] = config.INITIAL_PRICE
        books[i].mid_price = config.INITIAL_PRICE
    
    # --- SIMULATION LOOP ---
    panic_factor = 0.0
    swans_triggered = 0
    swan_cooldown = 0
    
    print("--- STARTING LIVE TRADING LOOP ---")
    
    # We use N_STEPS (calculated in config) instead of N_DAYS
    for t in range(1, config.N_STEPS):
        current_vol = vol_path[t] if t < len(vol_path) else vol_path[-1]
        
        # --- BLACK SWAN LOGIC ---
        panic_factor *= 0.92
        if swan_cooldown > 0: swan_cooldown -= 1
        
        if config.ENABLE_BLACK_SWANS:
            if (swans_triggered < config.MAX_SWANS_PER_YEAR and 
                swan_cooldown == 0 and 
                np.random.rand() < config.SWAN_PROBABILITY):
                print(f"[!] BLACK SWAN EVENT at Step {t}")
                panic_factor = config.SWAN_SEVERITY
                swans_triggered += 1
                swan_cooldown = config.SWAN_COOLDOWN

        # Generate Shocks
        shocks = physics.L @ np.random.normal(0, 1, config.N_ASSETS)
        
        # --- ASSET LOOP ---
        for i in range(config.N_ASSETS):
            book = books[i]
            
            # A. Update Book
            book.update_quotes(current_vol, panic_factor)
            
            # B. Physics Drift
            drift = 0.0001
            if panic_factor > 0.1: drift -= (panic_factor * 0.08)
            fund_return = drift + (current_vol * np.sqrt(config.DT) * shocks[i])
            book.mid_price *= np.exp(fund_return)
            
            # C. Gather Order Flow
            asset_hist = price_history[:t, i]
            net_flow = 0
            
            # Internal Agents
            for agent in agents:
                # Pass 't' so agents know when to wait (Patience)
                qty = agent.decide(book, asset_hist, current_vol, panic_factor, t)
                net_flow += qty
            
            # --- D. INJECT YOUR STRATEGY (Asset 0 Only) ---
            user_trade_size = 0
            if i == 0:
                user_trade_size = my_algo.on_data(book, asset_hist, current_vol, t)
                net_flow += user_trade_size # <--- ACTIVE MARKET IMPACT
            
            # E. Execute
            exec_price = book.execute(net_flow)
            price_history[t, i] = exec_price
            
            # F. Mark-to-Market Your Strategy
            if i == 0:
                if user_trade_size != 0:
                    # You pay Ask to buy, receive Bid to sell
                    fill_price = book.ask if user_trade_size > 0 else book.bid
                    
                    # Update Cash & Position
                    my_algo.position += user_trade_size
                    my_algo.cash -= (user_trade_size * fill_price)
                
                # Calculate Equity (Cash + Unrealized PnL)
                equity = my_algo.cash + (my_algo.position * exec_price)
                
                my_pnl_history.append({
                    'Step': t,
                    'Price': exec_price,
                    'Position': my_algo.position,
                    'Cash': my_algo.cash,
                    'Equity': equity,
                    'Trade_Size': user_trade_size
                })

    # --- EXPORT RESULTS ---
    print("--- Simulation Complete ---")
    
    # Save Strategy Performance
    df_res = pd.DataFrame(my_pnl_history)
    df_res.to_csv('my_performance.csv', index=False)
    
    # Print Quick Stats
    start_eq = 100_000
    end_eq = df_res.iloc[-1]['Equity']
    ret = ((end_eq - start_eq) / start_eq) * 100
    
    print(f"Initial Equity: ${start_eq:,.2f}")
    print(f"Final Equity:   ${end_eq:,.2f}")
    print(f"Total Return:   {ret:.2f}%")
    print(f"Saved detailed logs to 'my_performance.csv'")

if __name__ == "__main__":
    run_active_simulation()