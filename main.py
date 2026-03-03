# main.py, the main simulation loop, initializes physics, assets, agents, runs the daily loop, collects data, and exports to CSV
import numpy as np
import pandas as pd
import config
from physics import MarketPhysics
from market import OrderBook
from agents import Agent

def run_simulation():
    print(f"--- Initializing {config.N_ASSETS} Assets over {config.N_DAYS} Days ---")
    
    # 1. Init Physics & Volatility
    physics = MarketPhysics()
    vol_path = physics.get_volatility_path()
    
    # 2. Init Assets
    books = [OrderBook() for _ in range(config.N_ASSETS)]
    
    # 3. Init Agents
    agents = []
    for _ in range(config.N_TREND_FOLLOWERS): agents.append(Agent('Trend'))
    for _ in range(config.N_MEAN_REVERTERS): agents.append(Agent('MeanRev'))
    for _ in range(config.N_INSTITUTIONAL): agents.append(Agent('Institutional'))
    for _ in range(config.N_NOISE_TRADERS): agents.append(Agent('Noise'))
    
    # 4. Storage & State
    price_history = np.zeros((config.N_DAYS, config.N_ASSETS))
    for i in range(config.N_ASSETS): price_history[0, i] = config.INITIAL_PRICE
    
    all_data = []
    
    # --- BLACK SWAN STATE MACHINE ---
    panic_factor = 0.0
    swans_triggered = 0
    swan_cooldown = 0
    
    print("--- Starting Simulation Loop ---")
    
    for t in range(1, config.N_DAYS):
        current_vol = vol_path[t]
        
        # --- RANDOM BLACK SWAN LOGIC ---
        # Decay existing panic
        panic_factor *= 0.92
        if swan_cooldown > 0: swan_cooldown -= 1
        
        if config.ENABLE_BLACK_SWANS:
            # Check conditions: Under limit, cooldown over, random chance hit
            if (swans_triggered < config.MAX_SWANS_PER_YEAR and 
                swan_cooldown == 0 and 
                np.random.rand() < config.SWAN_PROBABILITY):
                
                print(f"[!] BLACK SWAN EVENT TRIGGERED AT DAY {t}")
                panic_factor = config.SWAN_SEVERITY
                swans_triggered += 1
                swan_cooldown = config.SWAN_COOLDOWN

        # Generate daily shocks
        shocks = physics.L @ np.random.normal(0, 1, config.N_ASSETS)
        
        # Loop through assets
        for i in range(config.N_ASSETS):
            book = books[i]
            
            # A. Update Order Book (Spreads)
            book.update_quotes(current_vol, panic_factor)
            
            # B. Physics Drift
            # If panic, add massive downside drag (-8% per day limit)
            drift = 0.0001
            if panic_factor > 0.1: drift -= (panic_factor * 0.08)
            
            fund_return = drift + (current_vol * shocks[i])
            book.mid_price *= np.exp(fund_return)
            
            # C. Agent Decisions
            asset_hist = price_history[:t, i]
            net_flow = 0
            volume = 0
            
            for agent in agents:
                qty = agent.decide(book, asset_hist, current_vol, panic_factor)
                net_flow += qty
                volume += abs(qty)
            
            # D. Execution
            close_price = book.execute(net_flow)
            price_history[t, i] = close_price
            
            # E. Record Data
            # Fake High/Low based on volatility
            daily_range = close_price * current_vol * (1 + panic_factor)
            
            all_data.append({
                'Day': t,
                'Ticker': f"STK_{i:03d}",
                'Sector': f"Sector_{i // (config.N_ASSETS//4) + 1}",
                'Open': price_history[t-1, i],
                'High': close_price + (daily_range/2),
                'Low': close_price - (daily_range/2),
                'Close': close_price,
                'Volume': int(volume),
                'Bid': book.bid,
                'Ask': book.ask,
                'Spread': book.ask - book.bid,
                'Panic_Score': panic_factor
            })
            
    # Export
    print("--- Compiling Data ---")
    df = pd.DataFrame(all_data)
    filename = 'phd_market_data.csv'
    df.to_csv(filename, index=False)
    print(f"Done! Saved to {filename}")
    print(f"Total Black Swans Triggered: {swans_triggered}")

if __name__ == "__main__":
    run_simulation()