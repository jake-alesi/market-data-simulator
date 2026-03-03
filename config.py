# config.py, global settings for the market simulator, volatility, correlation structure, market factor, sector blocks, Heston model, Cholesky decomposition, order book, spreads, execution, liquidity, panic factor, price impact, black swan events, agent population

# ==========================================
# SIMULATION SETTINGS
# ==========================================
N_ASSETS = 100          # Total number of tickers
N_DAYS = 252            # Duration (1 trading year)
DT = 1 / 252            # Time step size (Daily)

# ==========================================
# HESTON MODEL (VOLATILITY) PARAMETERS
# ==========================================
# How fast volatility returns to the mean (Higher = faster recovery)
MEAN_REVERSION_SPEED = 4.0  
# The long-term average variance (0.04 = 20% Volatility)
LONG_TERM_VARIANCE = 0.04   
# "Vol of Vol" - How jumpy the fear index is (Higher = more instability)
VOL_OF_VOL = 0.7            
# Starting variance
INITIAL_VARIANCE = 0.04     

# ==========================================
# MARKET MICROSTRUCTURE
# ==========================================
INITIAL_PRICE = 100.0
# Base Bid/Ask spread in basis points (0.0005 = 5 bps)
BASE_SPREAD = 0.0005    
# Market Impact (Kyle's Lambda): How much price moves per share traded
PRICE_IMPACT_FACTOR = 0.0005 
# Available liquidity at best bid/ask
BASE_LIQUIDITY = 10000  

# ==========================================
# BLACK SWAN EVENTS
# ==========================================
ENABLE_BLACK_SWANS = True
# Maximum number of crashes allowed per year
MAX_SWANS_PER_YEAR = 2  
# Probability of a crash happening on any given day (0.005 ~= 1.25% chance)
SWAN_PROBABILITY = 0.005 
# Minimum days between crashes to prevent back-to-back chaos
SWAN_COOLDOWN = 60      
# How severe the panic is (0.0 to 1.0)
SWAN_SEVERITY = 0.9     

# ==========================================
# AGENT POPULATION
# ==========================================
# Count of each agent type
N_TREND_FOLLOWERS = 40
N_MEAN_REVERTERS = 30
N_INSTITUTIONAL = 10
N_NOISE_TRADERS = 20