# Configuration settings for Multi-Agent Inventory Optimization System

# Simulation Settings
SIMULATION_DAYS = 30
TIME_STEP_HOURS = 24

# Inventory Optimization Parameters
SAFETY_STOCK_MULTIPLIER = 1.65  # For 95% service level
EOQ_ENABLED = True

# Agent Communication Settings
MESSAGE_QUEUE_SIZE = 100
COORDINATION_INTERVAL = 1  # days

# Cost Parameters
DEFAULT_HOLDING_COST_PCT = 0.20  # 20% of unit cost annually
DEFAULT_STOCKOUT_COST_MULTIPLIER = 2.0  # 2x unit cost per stockout

# File Paths
DATA_DIR = "data"
INVENTORY_FILE = "data/inventory_data.csv"
SALES_FILE = "data/sales_history.csv"
SUPPLIERS_FILE = "data/suppliers.csv"
WAREHOUSES_FILE = "data/warehouses.csv"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/simulation.log"
