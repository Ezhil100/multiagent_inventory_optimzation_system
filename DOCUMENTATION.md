# Multi-Agent Inventory Optimization System - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Data Models](#data-models)
6. [Agent System](#agent-system)
7. [Optimization Algorithms](#optimization-algorithms)
8. [Backend API](#backend-api)
9. [Frontend Dashboard](#frontend-dashboard)
10. [Installation & Setup](#installation--setup)
11. [Configuration](#configuration)
12. [Usage Guide](#usage-guide)
13. [Features in Detail](#features-in-detail)
14. [Troubleshooting](#troubleshooting)

---

## Project Overview

### What This System Does

The **Multi-Agent Inventory Optimization System** is an enterprise-grade inventory management solution that uses autonomous agents to:

1. **Monitor** inventory levels across multiple warehouses
2. **Forecast** demand using statistical methods (Moving Average, Exponential Smoothing, Weighted Methods)
3. **Calculate** optimal order quantities using Economic Order Quantity (EOQ) formula
4. **Determine** reorder points and safety stock levels
5. **Automatically place orders** when inventory falls below reorder points
6. **Track** supplier performance and lead times
7. **Generate alerts** for critical stock situations
8. **Simulate** inventory operations over time
9. **Visualize** KPIs and metrics in real-time dashboard

### Key Benefits

- **Automated Decision Making**: Agents make ordering decisions based on mathematical models
- **Cost Optimization**: Minimizes holding and ordering costs through EOQ
- **Stock-out Prevention**: Safety stock and reorder points ensure high service levels
- **Multi-Warehouse Support**: Manages inventory across 3 warehouses
- **Real-Time Monitoring**: Dashboard shows live KPIs and alerts
- **Scalable Architecture**: Agent-based design allows easy addition of new warehouses/suppliers

### Use Cases

- **Retail Chains**: Managing inventory across multiple store locations
- **Distribution Centers**: Optimizing warehouse stock levels
- **Manufacturing**: Raw material inventory management
- **E-commerce**: Multi-warehouse fulfillment optimization
- **Academic Research**: Studying multi-agent systems and inventory optimization

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER INTERFACE LAYER                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           React Frontend (Port 5173)                    │    │
│  │  - Login Page (admin/admin)                            │    │
│  │  - Dashboard with KPIs                                 │    │
│  │  - 7 Navigation Tabs with Search                       │    │
│  │  - Real-time Charts & Tables                           │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP REST API
┌───────────────────────────▼─────────────────────────────────────┐
│                     APPLICATION LAYER                            │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │           FastAPI Backend (Port 8001)                   │    │
│  │  - 15+ REST Endpoints                                   │    │
│  │  - JSON Request/Response                                │    │
│  │  - CORS Enabled                                         │    │
│  │  - Auto-generated Swagger Docs                          │    │
│  └────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ Direct Function Calls
┌───────────────────────────▼─────────────────────────────────────┐
│                     BUSINESS LOGIC LAYER                         │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              Coordinator Agent                          │    │
│  │  - Orchestrates all agent communication                 │    │
│  │  - Runs simulation loop                                 │    │
│  │  - Aggregates data for API                              │    │
│  └───────────┬────────────────┬──────────────┬─────────────┘    │
│              │                │              │                   │
│  ┌───────────▼──────┐ ┌───────▼────────┐ ┌─▼──────────────┐   │
│  │  SupplierAgent   │ │ WarehouseAgent │ │ RetailerAgent   │   │
│  │  (3 instances)   │ │ (3 instances)  │ │ (1 instance)    │   │
│  │  - SUP01, SUP02  │ │ - WH01, WH02   │ │ - RET01         │   │
│  │  - SUP03         │ │ - WH03         │ │ - Forecasting   │   │
│  └──────────────────┘ └────────────────┘ └─────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                        DATA LAYER                                │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │                  CSV Data Files                         │    │
│  │  - inventory_data.csv (20 products)                     │    │
│  │  - sales_history.csv (historical data)                  │    │
│  │  - suppliers.csv (3 suppliers)                          │    │
│  │  - warehouses.csv (3 warehouses)                        │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              In-Memory State Storage                    │    │
│  │  - Inventory levels (Dict)                              │    │
│  │  - Orders (List)                                        │    │
│  │  - Daily snapshots (List)                               │    │
│  │  - Agent state (Objects)                                │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
User Action (Run Simulation) 
    ↓
Frontend sends POST /api/simulation/run?days=7
    ↓
FastAPI receives request
    ↓
Coordinator Agent.run_simulation(7)
    ↓
For each day (1 to 7):
    ├─> RetailerAgent.forecast_demand()
    ├─> WarehouseAgent.check_inventory()
    ├─> If below ROP → WarehouseAgent.place_order()
    ├─> SupplierAgent.process_order()
    ├─> SupplierAgent.ship_delivery() (after lead time)
    ├─> WarehouseAgent.receive_delivery()
    ├─> RetailerAgent.simulate_sales()
    └─> CoordinatorAgent.create_daily_snapshot()
    ↓
Return simulation results
    ↓
Frontend displays updated KPIs and tables
```

---

## Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Core programming language |
| **FastAPI** | 0.100+ | REST API framework |
| **Uvicorn** | 0.22+ | ASGI server |
| **Pandas** | 2.0+ | Data manipulation |
| **NumPy** | 1.24+ | Numerical computations |
| **SciPy** | 1.10+ | Statistical functions |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.x | UI framework |
| **Vite** | 5.x | Build tool & dev server |
| **JavaScript** | ES6+ | Programming language |
| **CSS3** | - | Styling |

### Development Tools

- **Git** - Version control
- **npm** - Package manager
- **pip** - Python package manager
- **VS Code** - IDE (recommended)

---

## Project Structure

```
d:\project\
│
├── venv/                          # Python virtual environment (not in git)
│   ├── Scripts/
│   └── Lib/
│
├── data/                          # CSV data files
│   ├── inventory_data.csv         # Initial inventory (20 products)
│   ├── sales_history.csv          # Historical sales for forecasting
│   ├── suppliers.csv              # Supplier configurations (3 suppliers)
│   └── warehouses.csv             # Warehouse configurations (3 warehouses)
│
├── agents/                        # Multi-agent system
│   ├── __init__.py
│   ├── base_agent.py             # Base Agent class, Message, Order dataclasses
│   ├── supplier_agent.py         # SupplierAgent - handles orders & deliveries
│   ├── warehouse_agent.py        # WarehouseAgent - EOQ, ROP, safety stock
│   ├── retailer_agent.py         # RetailerAgent - demand forecasting
│   └── coordinator_agent.py      # CoordinatorAgent - orchestration
│
├── models/                        # Optimization models
│   ├── __init__.py
│   ├── demand_forecast.py        # Forecasting algorithms (MA, EMA, Holt)
│   └── optimization.py           # EOQ, Safety Stock, ROP calculations
│
├── utils/                         # Utility functions
│   ├── __init__.py
│   └── metrics.py                # KPI calculations
│
├── backend/                       # FastAPI application
│   ├── __init__.py
│   └── api.py                    # REST API endpoints
│
├── frontend/                      # React application
│   ├── node_modules/             # npm packages (not in git)
│   ├── src/
│   │   ├── api.js                # API service (fetch functions)
│   │   ├── App.jsx               # Main component (dashboard)
│   │   ├── App.css               # Component styles
│   │   ├── index.css             # Global styles
│   │   └── main.jsx              # Entry point
│   ├── index.html                # HTML template
│   ├── package.json              # npm dependencies
│   ├── package-lock.json
│   └── vite.config.js            # Vite configuration
│
├── logs/                          # Application logs (generated)
│   └── optimization.log
│
├── __pycache__/                   # Python bytecode cache (not in git)
│
├── .git/                          # Git repository
├── .gitignore                     # Git ignore rules
├── config.py                      # Configuration settings
├── main.py                        # CLI entry point
├── requirements.txt               # Python dependencies
├── README.md                      # Project README
├── DOCUMENTATION.md               # This file
└── test_api.py                    # API test script
```

---

## Data Models

### 1. Inventory Data (inventory_data.csv)

**20 Products across 3 warehouses (WH01, WH02, WH03)**

| Column | Type | Description |
|--------|------|-------------|
| `product_id` | String | Unique ID (P001-P020) |
| `product_name` | String | Product name |
| `category` | String | Electronics, Furniture, Supplies |
| `warehouse_id` | String | WH01, WH02, WH03 |
| `current_stock` | Integer | Current inventory level |
| `unit_cost` | Float | Cost per unit (₹) |
| `unit_price` | Float | Selling price (₹) |
| `holding_cost_pct` | Float | Annual holding cost % |
| `ordering_cost` | Float | Fixed cost per order (₹) |
| `lead_time_days` | Integer | Supplier lead time |
| `demand_mean` | Float | Average daily demand |
| `demand_std` | Float | Demand standard deviation |
| `service_level` | Float | Target service level (0.95 = 95%) |

**Example:**
```csv
P001,Laptop Pro 15,Electronics,WH01,85,75000,89999,0.20,500,5,12,3,0.95
```

### 2. Sales History (sales_history.csv)

**Historical sales data for demand forecasting**

| Column | Type | Description |
|--------|------|-------------|
| `date` | Date | Sale date |
| `product_id` | String | Product ID |
| `units_sold` | Integer | Quantity sold |
| `revenue` | Float | Total revenue (₹) |
| `is_weekend` | Boolean | Weekend flag |
| `is_holiday` | Boolean | Holiday flag |
| `promotion_active` | Boolean | Promotion flag |

### 3. Suppliers (suppliers.csv)

**3 Suppliers with different characteristics**

| Column | Type | Description |
|--------|------|-------------|
| `supplier_id` | String | SUP01, SUP02, SUP03 |
| `name` | String | Supplier name |
| `lead_time_days` | Integer | Delivery lead time |
| `reliability` | Float | On-time delivery rate (0.95 = 95%) |
| `min_order_quantity` | Integer | Minimum order size |
| `category_specialization` | String | Electronics, Furniture, Supplies |

**Example:**
```csv
SUP01,TechParts Global,5,0.95,10,Electronics
SUP02,FurniturePro Inc,12,0.88,5,Furniture
SUP03,OfficeSupply Direct,3,0.92,20,Supplies
```

### 4. Warehouses (warehouses.csv)

**3 Warehouses with different capacities**

| Column | Type | Description |
|--------|------|-------------|
| `warehouse_id` | String | WH01, WH02, WH03 |
| `name` | String | Warehouse name |
| `location` | String | City |
| `capacity` | Integer | Max storage units |
| `current_utilization` | Float | Current usage % |
| `operating_cost_per_day` | Float | Daily operating cost (₹) |

**Example:**
```csv
WH01,Central Electronics Hub,Mumbai,5000,0.65,5000
WH02,Furniture Distribution Center,Delhi,3000,0.55,3500
WH03,Office Supplies Depot,Bangalore,4000,0.60,4200
```

---

## Agent System

### Base Agent Class

**Location:** `agents/base_agent.py`

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name
        self.current_time = datetime.now()
        self.message_queue = []
    
    def send_message(self, recipient, message_type, content)
    def receive_message(self, message)
    def step(self, current_time)
    def get_status()
```

### Message Types

```python
class MessageType(Enum):
    ORDER_REQUEST = "order_request"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPMENT_NOTIFICATION = "shipment_notification"
    DELIVERY_COMPLETE = "delivery_complete"
    FORECAST_UPDATE = "forecast_update"
    STOCK_UPDATE = "stock_update"
    SYSTEM_STATUS = "system_status"
```

### 1. CoordinatorAgent

**Location:** `agents/coordinator_agent.py`

**Purpose:** Central orchestrator that manages all other agents

**Responsibilities:**
- Initialize all agents (3 suppliers, 3 warehouses, 1 retailer)
- Run simulation loop
- Create daily snapshots of system state
- Aggregate data for API endpoints
- Manage agent lifecycle

**Key Methods:**
```python
def initialize():
    # Load data from CSV
    # Create supplier agents (3)
    # Create warehouse agents (3)
    # Create retailer agent (1)
    # Link agents together

def run_simulation(days: int):
    # For each day:
    #   - Step through each agent
    #   - Process orders
    #   - Update inventory
    #   - Create snapshot
    # Return results

def get_kpis():
    # Calculate and return KPIs

def get_all_inventory():
    # Aggregate inventory from all warehouses
```

**State:**
- `suppliers: Dict[str, SupplierAgent]` - 3 suppliers
- `warehouses: Dict[str, WarehouseAgent]` - 3 warehouses
- `retailers: Dict[str, RetailerAgent]` - 1 retailer
- `daily_snapshots: List[Snapshot]` - Historical data
- `current_day: int` - Current simulation day

### 2. SupplierAgent

**Location:** `agents/supplier_agent.py`

**Purpose:** Manages order fulfillment and deliveries

**Responsibilities:**
- Receive orders from warehouses
- Process orders (confirm, reject, partial fill)
- Schedule shipments based on lead time
- Track delivery status
- Maintain order history

**Key Attributes:**
```python
self.supplier_id: str           # SUP01, SUP02, SUP03
self.name: str                  # Supplier name
self.lead_time_days: int        # 3-12 days
self.reliability: float         # 0.88-0.95
self.min_order_quantity: int    # Minimum order size
self.pending_orders: List       # Orders in transit
self.fulfilled_orders: List     # Completed orders
```

**Order Processing Flow:**
1. Receive ORDER_REQUEST from warehouse
2. Check inventory availability
3. Send ORDER_CONFIRMATION
4. Wait lead_time_days
5. Send SHIPMENT_NOTIFICATION
6. Send DELIVERY_COMPLETE
7. Update fulfillment metrics

### 3. WarehouseAgent

**Location:** `agents/warehouse_agent.py`

**Purpose:** Manages inventory and calculates order quantities

**Responsibilities:**
- Track inventory for assigned products
- Calculate EOQ (Economic Order Quantity)
- Calculate ROP (Reorder Point)
- Calculate Safety Stock
- Automatically place orders when stock < ROP
- Receive deliveries from suppliers
- Fulfill retailer demand

**Key Attributes:**
```python
self.warehouse_id: str          # WH01, WH02, WH03
self.name: str                  # Warehouse name
self.capacity: int              # Max storage
self.inventory: Dict            # Product inventory
self.pending_orders: List       # Orders awaiting delivery
```

**Inventory Item Structure:**
```python
class InventoryItem:
    product_id: str
    product_name: str
    category: str
    current_stock: int
    unit_cost: float
    unit_price: float
    holding_cost_pct: float
    ordering_cost: float
    lead_time_days: int
    demand_mean: float
    demand_std: float
    service_level: float
    eoq: int                    # Calculated
    reorder_point: int          # Calculated
    safety_stock: int           # Calculated
    demand_history: List[int]   # Last N days
```

**EOQ Calculation:**
```python
def calculate_eoq(self, product_id):
    D = demand_mean * 365  # Annual demand
    S = ordering_cost       # Cost per order
    H = unit_cost * holding_cost_pct  # Holding cost per unit
    EOQ = sqrt((2 * D * S) / H)
    return int(EOQ)
```

**Safety Stock Calculation:**
```python
def calculate_safety_stock(self, product_id):
    z_score = norm.ppf(service_level)  # 0.95 → 1.645
    σ = demand_std
    L = lead_time_days
    SS = z_score * σ * sqrt(L)
    return int(SS)
```

**Reorder Point Calculation:**
```python
def calculate_reorder_point(self, product_id):
    daily_demand = demand_mean
    lead_time = lead_time_days
    safety_stock = calculate_safety_stock(product_id)
    ROP = (daily_demand * lead_time) + safety_stock
    return int(ROP)
```

**Order Logic:**
```python
def check_and_order(self):
    for product_id, item in self.inventory.items():
        if item.current_stock <= item.reorder_point:
            order_quantity = item.eoq
            supplier = self.get_supplier_for_product(product_id)
            self.place_order(supplier, product_id, order_quantity)
```

### 4. RetailerAgent

**Location:** `agents/retailer_agent.py`

**Purpose:** Forecasts demand and simulates customer sales

**Responsibilities:**
- Track historical sales data
- Generate demand forecasts using multiple methods
- Simulate customer purchases
- Update demand patterns
- Provide forecasts to warehouses

**Forecasting Methods:**

1. **Simple Moving Average (SMA)**
```python
def forecast_demand_moving_average(product_id, days_ahead=7):
    recent_sales = sales_history[-7:]  # Last 7 days
    avg = mean(recent_sales)
    forecast = avg * days_ahead
    return forecast
```

2. **Exponential Moving Average (EMA)**
```python
def forecast_demand_exponential_smoothing(product_id, alpha=0.3):
    ema = sales_history[0]
    for sale in sales_history[1:]:
        ema = alpha * sale + (1 - alpha) * ema
    forecast = ema * days_ahead
    return forecast
```

3. **Weighted Method (60% EMA, 40% SMA)**
```python
def forecast_demand_weighted(product_id):
    ema_forecast = forecast_ema(product_id)
    sma_forecast = forecast_sma(product_id)
    forecast = 0.6 * ema_forecast + 0.4 * sma_forecast
    return forecast
```

**Demand Simulation:**
```python
def simulate_demand(self, product_id):
    # Generate demand using normal distribution
    demand = np.random.normal(demand_mean, demand_std)
    demand = max(0, int(demand))  # No negative demand
    
    # Record sale
    self.sales_history[product_id].append(demand)
    
    # Request from warehouse
    self.request_stock(product_id, demand)
```

---

## Optimization Algorithms

### 1. Economic Order Quantity (EOQ)

**Purpose:** Minimize total inventory costs (holding + ordering)

**Formula:**
```
EOQ = √(2 × D × S / H)
```

**Where:**
- D = Annual demand (units)
- S = Ordering cost per order (₹)
- H = Annual holding cost per unit (₹)

**Example Calculation:**
```
Product: Laptop Pro 15
D = 12 units/day × 365 = 4,380 units/year
S = ₹500 per order
H = ₹75,000 × 20% = ₹15,000 per unit per year

EOQ = √(2 × 4,380 × 500 / 15,000)
    = √(292)
    = 17 units

Optimal order quantity: 17 laptops per order
```

**Benefits:**
- Minimizes sum of ordering and holding costs
- Determines optimal order frequency
- Reduces total inventory costs by 10-30%

### 2. Safety Stock

**Purpose:** Buffer inventory to maintain service level despite demand variability

**Formula:**
```
SS = Z × σ × √L
```

**Where:**
- Z = Z-score for desired service level
  - 90% → 1.282
  - 95% → 1.645
  - 99% → 2.326
- σ = Standard deviation of daily demand
- L = Lead time in days

**Example Calculation:**
```
Product: Wireless Mouse
Service Level: 95% (Z = 1.645)
σ = 7 units/day
L = 5 days

SS = 1.645 × 7 × √5
   = 1.645 × 7 × 2.236
   = 25.7 ≈ 26 units

Safety stock: 26 mice
```

**Benefits:**
- Prevents stockouts during lead time
- Maintains target service level
- Accounts for demand variability

### 3. Reorder Point (ROP)

**Purpose:** Trigger point to place new order

**Formula:**
```
ROP = (d̄ × L) + SS
```

**Where:**
- d̄ = Average daily demand
- L = Lead time in days
- SS = Safety stock

**Example Calculation:**
```
Product: USB-C Hub
Average daily demand = 15 units/day
Lead time = 5 days
Safety stock = 19 units

ROP = (15 × 5) + 19
    = 75 + 19
    = 94 units

Place order when stock reaches 94 units
```

**Benefits:**
- Ensures stock arrives before running out
- Automates ordering decision
- Maintains continuous availability

### 4. Total Cost Calculation

**Components:**
1. **Holding Cost** = Average Inventory × Holding Cost Rate × Unit Cost
2. **Ordering Cost** = Number of Orders × Cost per Order
3. **Total Cost** = Holding Cost + Ordering Cost

**Example:**
```
Using EOQ = 60 units
Annual demand = 4,380 units
Orders per year = 4,380 / 60 = 73 orders

Holding Cost = (60/2) × 0.20 × 75,000 = ₹450,000
Ordering Cost = 73 × 500 = ₹36,500
Total Cost = ₹486,500

Without EOQ (order 100 at a time):
Orders per year = 4,380 / 100 = 44 orders
Holding Cost = (100/2) × 0.20 × 75,000 = ₹750,000
Ordering Cost = 44 × 500 = ₹22,000
Total Cost = ₹772,000

Savings = ₹285,500 (37% reduction)
```

---

## Backend API

### FastAPI Application

**Location:** `backend/api.py`

**Base URL:** `http://127.0.0.1:8001`

**CORS:** Enabled for `http://localhost:5173` and `http://localhost:5174`

### API Endpoints

#### 1. Health & Info

**GET /**
```json
{
  "name": "Multi-Agent Inventory Optimization API",
  "version": "1.0.0",
  "status": "running"
}
```

**GET /health**
```json
{
  "status": "healthy"
}
```

#### 2. Initialization

**POST /api/initialize**

Initializes the system by loading data and creating agents.

**Response:**
```json
{
  "status": "initialized",
  "suppliers": 3,
  "warehouses": 3,
  "retailers": 1,
  "total_products": 20
}
```

#### 3. KPIs

**GET /api/kpis**

Returns system-wide KPIs.

**Response:**
```json
{
  "total_inventory_value": 292207.37,
  "total_products": 20,
  "total_warehouses": 3,
  "total_suppliers": 3,
  "total_orders_placed": 20,
  "total_units_fulfilled": 4394,
  "total_stockouts": 36,
  "total_holding_cost": 1588.41,
  "total_ordering_cost": 708.0,
  "total_cost": 2296.41,
  "average_service_level": 83.6,
  "simulation_days": 14,
  "alerts_count": 17
}
```

#### 4. Inventory

**GET /api/inventory**

Returns all inventory items.

**Query Parameters:**
- `warehouse_id` (optional): Filter by warehouse (WH01, WH02, WH03)
- `status` (optional): Filter by status (OK, REORDER, CRITICAL)

**Response:**
```json
{
  "items": [
    {
      "product_id": "P001",
      "product_name": "Laptop Pro 15",
      "category": "Electronics",
      "warehouse_id": "WH01",
      "warehouse_name": "Central Electronics Hub",
      "current_stock": 75,
      "reorder_point": 98,
      "safety_stock": 14,
      "eoq": 60,
      "days_of_supply": 6.2,
      "stock_value": 67499.25,
      "status": "REORDER"
    }
  ],
  "total": 20
}
```

**Status Levels:**
- **OK**: Stock > Reorder Point
- **REORDER**: Stock ≤ Reorder Point but > Safety Stock
- **CRITICAL**: Stock ≤ Safety Stock

#### 5. Alerts

**GET /api/alerts**

Returns all active alerts.

**Response:**
```json
{
  "alerts": [
    {
      "level": "critical",
      "type": "low_stock",
      "warehouse": "Central Electronics Hub",
      "product": "Wireless Mouse",
      "product_id": "P002",
      "current_stock": 24,
      "safety_stock": 35,
      "message": "CRITICAL: Wireless Mouse stock (24) below safety level (35)"
    },
    {
      "level": "warning",
      "type": "reorder_needed",
      "warehouse": "Central Electronics Hub",
      "product": "Laptop Pro 15",
      "product_id": "P001",
      "current_stock": 71,
      "reorder_point": 98,
      "message": "REORDER: Laptop Pro 15 stock (71) below ROP (98)"
    }
  ],
  "total": 14
}
```

#### 6. Warehouses

**GET /api/warehouses**

Returns warehouse status.

**Response:**
```json
{
  "warehouses": [
    {
      "warehouse_id": "WH01",
      "name": "Central Electronics Hub",
      "total_products": 9,
      "total_value": 142843.62,
      "items_ok": 3,
      "items_reorder": 3,
      "items_critical": 3
    }
  ],
  "total": 3
}
```

#### 7. Suppliers

**GET /api/suppliers**

Returns supplier performance metrics.

**Response:**
```json
{
  "suppliers": [
    {
      "supplier_id": "SUP01",
      "name": "TechParts Global",
      "lead_time_days": 5,
      "reliability": 0.95,
      "orders_received": 9,
      "orders_fulfilled": 9,
      "total_units_supplied": 1625
    }
  ],
  "total": 3
}
```

#### 8. Forecasts

**GET /api/forecasts**

Returns demand forecasts for all products.

**Response:**
```json
{
  "forecasts": [
    {
      "product_id": "P001",
      "daily_avg": 13.79,
      "daily_std": 3.1,
      "forecast_horizon_days": 7,
      "predicted_total": 94.0,
      "confidence_lower": 80.0,
      "confidence_upper": 108.0,
      "method": "weighted",
      "data_points": 14,
      "retailer_id": "RET01",
      "retailer_name": "Main Retailer"
    }
  ],
  "total": 13
}
```

#### 9. Orders

**GET /api/orders**

Returns all orders placed during simulation.

**Response:**
```json
{
  "orders": [
    {
      "day": 1,
      "warehouse": "Central Electronics Hub",
      "warehouse_id": "WH01",
      "product_id": "P001",
      "quantity": 60,
      "status": "Ordered",
      "action": "Order placed"
    }
  ],
  "total": 20
}
```

#### 10. History

**GET /api/history**

Returns daily simulation snapshots.

**Response:**
```json
{
  "history": [
    {
      "date": "2026-01-28 14:39:59",
      "inventory_value": 292207.37,
      "orders_placed": 11,
      "stockouts": 0,
      "items_below_rop": 11,
      "items_critical": 0,
      "holding_cost": 152.47,
      "ordering_cost": 480.0,
      "total_cost": 632.47,
      "service_level": 1.0
    }
  ],
  "days": 7
}
```

#### 11. Simulation

**POST /api/simulation/run?days={N}**

Runs simulation for N days.

**Parameters:**
- `days`: Number of days to simulate (1-365)

**Response:**
```json
{
  "status": "completed",
  "days_simulated": 7,
  "summary": {
    "simulation_config": {...},
    "kpis": {...},
    "final_state": {...},
    "optimization_actions": 20
  }
}
```

**POST /api/simulation/step**

Advances simulation by 1 day.

**Response:**
```json
{
  "status": "stepped",
  "current_day": 8,
  "actions_taken": 3
}
```

#### 12. Reset

**POST /api/reset**

Resets system to initial state.

**Response:**
```json
{
  "status": "reset",
  "message": "System reset to initial state"
}
```

---

## Frontend Dashboard

### React Application

**Location:** `frontend/src/`

**Dev Server:** Port 5173 (Vite)

### Pages & Navigation

#### 1. Login Page

**URL:** `/` (when not authenticated)

**Features:**
- Username: `admin`
- Password: `admin`
- Session stored in `localStorage`
- Redirects to dashboard after login

**Components:**
- Username input field
- Password input field (type=password)
- Submit button
- Error message display
- Hint text

#### 2. Dashboard (Home)

**Tab:** Dashboard

**Features:**
- 4 KPI Cards:
  - Inventory Value (₹)
  - Service Level (%)
  - Orders Placed
  - Total Cost (₹)
- Active Alerts Panel (top 5)
- Simulation History:
  - Start/End Value
  - Average Service Level
  - Last 5 days table

**Auto-refresh:** Every time simulation runs

#### 3. Inventory Page

**Tab:** Inventory

**Features:**
- Search bar (product, warehouse)
- 4 Status Count Cards:
  - Total Products
  - OK Status
  - Reorder Status
  - Critical Status
- Status filter dropdown (All, OK, REORDER, CRITICAL)
- Inventory table (9 columns):
  - Product (Name + ID)
  - Warehouse
  - Current Stock
  - Reorder Point
  - Safety Stock
  - EOQ
  - Days of Supply
  - Value (₹)
  - Status (colored pill)

**Table Features:**
- Sortable columns
- Color-coded rows (critical = red background)
- Real-time search filtering
- Status badge colors:
  - Green = OK
  - Yellow = REORDER
  - Red = CRITICAL

#### 4. Orders Page

**Tab:** Orders

**Features:**
- Search bar (product, warehouse)
- 3 KPI Cards:
  - Total Orders
  - Units Fulfilled
  - Stockouts
- Recent Orders table:
  - Day number
  - Warehouse
  - Product ID
  - Quantity
  - Status

**Order Types:**
- Ordered (initial placement)
- Confirmed (supplier confirmed)
- Shipped (in transit)
- Delivered (received at warehouse)

#### 5. Suppliers Page

**Tab:** Suppliers

**Features:**
- Search bar (supplier name, ID)
- 3 KPI Cards:
  - Total Suppliers
  - Orders Received
  - Orders Fulfilled
- Supplier Performance table:
  - Supplier (Name + ID)
  - Lead Time (days)
  - Reliability (%)
  - Orders Received
  - Orders Fulfilled
  - Total Units

**Metrics:**
- Lead time: Fixed supplier attribute (3-12 days)
- Reliability: On-time delivery rate (88-95%)
- Order counts: From simulation
- Units supplied: Total across all orders

#### 6. Warehouses Page

**Tab:** Warehouses

**Features:**
- Search bar (warehouse name, ID)
- Warehouse cards (3 cards):
  - Warehouse name + ID
  - Products count
  - Total value (₹)
  - Status breakdown (OK/Reorder/Critical)

**Card Design:**
- Card per warehouse
- Color-coded status indicators
- Click to filter inventory by warehouse

#### 7. Forecasts Page

**Tab:** Forecasts

**Features:**
- Search bar (product)
- Prediction window badge (7 days)
- Demand Forecasts table:
  - Product (Name + ID)
  - Daily Avg Demand
  - Forecast (7 days)
  - Confidence Range (min-max)
  - Data Points (days of history)

**Forecasting Info:**
- Method: Weighted (60% EMA + 40% SMA)
- Horizon: 7 days
- Confidence: 95% interval
- Updates after each simulation

#### 8. Alerts Page

**Tab:** Alerts

**Features:**
- Search bar (product, warehouse, type)
- 3 KPI Cards:
  - Critical Count
  - Warning Count
  - Total Alerts
- Critical Alerts section (red)
- Warning Alerts section (yellow)

**Alert Types:**
- **low_stock** (Critical): Stock < Safety Stock
- **reorder_needed** (Warning): Stock < Reorder Point

**Alert Display:**
- Color-coded dot (red/yellow)
- Product name
- Warehouse + Stock level
- Status badge
- Auto-refresh on simulation

### Header Controls

**Located:** Top right of dashboard

**Elements:**
1. **Simulate Input**
   - Number input (1-365 days)
   - Default: 7 days
   - Label: "Simulate X days"

2. **Run Button**
   - Text: "Run" or "Running..."
   - Color: Blue (primary)
   - Disabled during simulation

3. **Reset Button**
   - Text: "Reset"
   - Color: Gray (secondary)
   - Resets system to initial state

4. **User Section**
   - Username display
   - Logout button

### Search Functionality

**Available On:** All pages except Dashboard

**Features:**
- Real-time filtering (no submit needed)
- Case-insensitive matching
- Searches multiple fields:
  - Inventory: product name, ID, warehouse
  - Orders: product, warehouse, action
  - Suppliers: name, supplier ID
  - Warehouses: name, warehouse ID
  - Forecasts: product name, ID, warehouse
  - Alerts: product, warehouse, type

**Implementation:**
```javascript
const filteredItems = items.filter(item => {
  if (search === '') return true;
  const searchLower = search.toLowerCase();
  return item.product_name?.toLowerCase().includes(searchLower) ||
         item.product_id?.toLowerCase().includes(searchLower);
});
```

### Styling

**Color Scheme:**
- Primary: Blue (#3b82f6)
- Success: Green (#10b981)
- Warning: Yellow (#f59e0b)
- Danger: Red (#ef4444)
- Background: Light gray (#f8fafc)
- Text: Dark gray (#1e293b)

**Typography:**
- Font: System fonts (Apple, Segoe UI, Roboto)
- Headings: 700 weight
- Body: 400 weight
- Numbers: Monospace font

**Components:**
- Border radius: 8px (cards, buttons)
- Shadows: Subtle elevation
- Transitions: 0.2s ease
- Responsive: Mobile-friendly grid

---

## Installation & Setup

### Prerequisites

1. **Python 3.10 or higher**
   ```bash
   python --version
   # Should show Python 3.10.x or higher
   ```

2. **Node.js 18 or higher**
   ```bash
   node --version
   # Should show v18.x.x or higher
   ```

3. **Git**
   ```bash
   git --version
   ```

### Step-by-Step Installation

#### Step 1: Clone Repository

```bash
git clone https://github.com/Ezhil100/multiagent_inventory_optimzation_system.git
cd multiagent_inventory_optimzation_system
```

#### Step 2: Create Python Virtual Environment

**Windows:**
```powershell
# Create venv
python -m venv venv

# Activate venv
.\venv\Scripts\Activate.ps1
# OR
.\venv\Scripts\activate.bat

# Verify activation (should show (venv) in prompt)
```

**Linux/Mac:**
```bash
# Create venv
python3 -m venv venv

# Activate venv
source venv/bin/activate

# Verify activation (should show (venv) in prompt)
```

#### Step 3: Install Python Dependencies

```bash
# Make sure venv is activated!
pip install --upgrade pip
pip install -r requirements.txt
```

**Installed packages:**
- pandas (data manipulation)
- numpy (numerical computing)
- scipy (statistics)
- fastapi (web framework)
- uvicorn (ASGI server)
- And more...

#### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

**Installed packages:**
- react (UI library)
- react-dom (React renderer)
- vite (build tool)

#### Step 5: Verify Data Files

Check that CSV files exist in `data/` folder:
```bash
ls data/
# Should show:
# inventory_data.csv
# sales_history.csv
# suppliers.csv
# warehouses.csv
```

---

## Configuration

### Config File

**Location:** `config.py`

```python
# System Configuration
SIMULATION_CONFIG = {
    "max_simulation_days": 365,
    "default_service_level": 0.95,
    "auto_reorder": True,
    "log_level": "INFO"
}

# Data Paths
DATA_DIR = "data"
INVENTORY_FILE = f"{DATA_DIR}/inventory_data.csv"
SALES_HISTORY_FILE = f"{DATA_DIR}/sales_history.csv"
SUPPLIERS_FILE = f"{DATA_DIR}/suppliers.csv"
WAREHOUSES_FILE = f"{DATA_DIR}/warehouses.csv"

# API Configuration
API_HOST = "127.0.0.1"
API_PORT = 8001
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:5174"
]
```

### Environment Variables

No environment variables required. All configuration is in `config.py`.

### Customization Options

1. **Change Service Level Target:**
   ```python
   # In config.py
   SIMULATION_CONFIG["default_service_level"] = 0.99  # 99%
   ```

2. **Disable Auto-Reordering:**
   ```python
   SIMULATION_CONFIG["auto_reorder"] = False
   ```

3. **Change API Port:**
   ```python
   API_PORT = 8080
   ```

4. **Add Data Sources:**
   - Place new CSV files in `data/` folder
   - Update file paths in `config.py`
   - Modify loading functions in agents

---

## Usage Guide

### Running the System

#### Option 1: Full System (Backend + Frontend)

**Terminal 1 - Backend:**
```powershell
cd D:\project
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd D:\project\frontend
npm run dev
```

**Access:**
- Frontend: http://localhost:5173
- API Docs: http://127.0.0.1:8001/docs
- Login: admin / admin

#### Option 2: Backend Only (API Testing)

```bash
cd D:\project
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001

# Test with curl or browser
curl http://127.0.0.1:8001/api/kpis
```

#### Option 3: CLI Mode (No Web Interface)

```bash
cd D:\project
.\venv\Scripts\Activate.ps1
python main.py
```

### Using the Dashboard

#### 1. Login
1. Open http://localhost:5173
2. Enter username: `admin`
3. Enter password: `admin`
4. Click "Sign In"

#### 2. View System Status
1. Dashboard shows current KPIs
2. Check alerts panel for issues
3. Review inventory levels

#### 3. Run Simulation
1. Enter days (e.g., 30)
2. Click "Run"
3. Wait for completion (progress shown)
4. View updated metrics

#### 4. Analyze Results
1. **Dashboard:** Overall KPIs and trends
2. **Inventory:** Check stock levels and status
3. **Orders:** Review ordering activity
4. **Suppliers:** Evaluate supplier performance
5. **Alerts:** Address critical issues
6. **Forecasts:** Review demand predictions
7. **History:** Analyze trends over time

#### 5. Search & Filter
1. Use search bars to find specific items
2. Use status filters on Inventory page
3. Click on items for details

#### 6. Reset System
1. Click "Reset" button
2. Confirm action
3. System returns to initial state

### API Usage Examples

#### Using curl

```bash
# Get KPIs
curl http://127.0.0.1:8001/api/kpis

# Initialize system
curl -X POST http://127.0.0.1:8001/api/initialize

# Run simulation
curl -X POST "http://127.0.0.1:8001/api/simulation/run?days=30"

# Get inventory
curl http://127.0.0.1:8001/api/inventory

# Filter inventory by status
curl "http://127.0.0.1:8001/api/inventory?status=CRITICAL"

# Get alerts
curl http://127.0.0.1:8001/api/alerts
```

#### Using PowerShell

```powershell
# Get KPIs
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/kpis"

# Run simulation
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/simulation/run?days=7" -Method Post

# Get inventory as JSON
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/inventory" | ConvertTo-Json -Depth 5
```

#### Using Python

```python
import requests

BASE_URL = "http://127.0.0.1:8001"

# Get KPIs
response = requests.get(f"{BASE_URL}/api/kpis")
kpis = response.json()
print(f"Service Level: {kpis['average_service_level']}%")

# Run simulation
response = requests.post(f"{BASE_URL}/api/simulation/run?days=30")
result = response.json()
print(f"Simulated {result['days_simulated']} days")

# Get critical inventory
response = requests.get(f"{BASE_URL}/api/inventory?status=CRITICAL")
inventory = response.json()
print(f"Critical items: {inventory['total']}")
```

---

## Features in Detail

### 1. Multi-Agent System

**7 Autonomous Agents:**
- 3 Supplier Agents (SUP01, SUP02, SUP03)
- 3 Warehouse Agents (WH01, WH02, WH03)
- 1 Retailer Agent (RET01)

**Agent Communication:**
- Message passing architecture
- Asynchronous message queue
- 7 message types
- No direct coupling between agents

**Agent Autonomy:**
- Each agent makes independent decisions
- Agents react to their environment
- Agents maintain their own state
- Coordinator orchestrates but doesn't dictate

### 2. Inventory Optimization

**EOQ (Economic Order Quantity):**
- Minimizes total costs (holding + ordering)
- Calculated per product
- Used as default order quantity
- Recalculated based on demand changes

**Safety Stock:**
- Protects against stockouts
- Based on service level target (95%)
- Accounts for demand variability
- Uses normal distribution (Z-score)

**Reorder Point:**
- Automated triggering mechanism
- Considers lead time
- Includes safety stock buffer
- Ensures continuous availability

### 3. Demand Forecasting

**Multiple Methods:**
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Weighted Combination
- Holt's Linear Trend (future)

**Forecast Features:**
- 7-day prediction window
- Confidence intervals (95%)
- Historical data tracking
- Seasonality detection (future)

**Forecast Accuracy:**
- Tracks actual vs predicted
- Calculates MAPE (Mean Absolute Percentage Error)
- Updates models based on performance

### 4. Simulation Engine

**Time-Based Simulation:**
- Day-by-day progression
- Each day represents a full business cycle
- Configurable duration (1-365 days)

**Daily Cycle:**
1. Retailer forecasts demand
2. Warehouses check inventory levels
3. Orders placed if stock < ROP
4. Suppliers process pending orders
5. Deliveries received (after lead time)
6. Customer demand simulated
7. Sales fulfilled or recorded as stockout
8. Snapshot created for analytics

**Simulation State:**
- Persistent across runs
- Days accumulate
- Historical data preserved
- Can be reset to initial state

### 5. Real-Time Monitoring

**KPI Dashboard:**
- Total inventory value (₹)
- Service level (%)
- Orders placed & fulfilled
- Stockouts count
- Holding costs
- Ordering costs
- Total costs

**Alerts System:**
- Critical alerts (red): Stock < Safety Stock
- Warning alerts (yellow): Stock < ROP
- Auto-generated on each update
- Grouped by severity

**Historical Tracking:**
- Daily snapshots stored
- Trends visualization ready
- Exportable data (future)

### 6. Login & Authentication

**Security Features:**
- Username/password authentication
- Session persistence (localStorage)
- Automatic logout
- Protected routes

**Credentials:**
- Username: `admin`
- Password: `admin`
- Can be changed in code

### 7. Search & Filtering

**Search Available On:**
- Inventory page
- Orders page
- Suppliers page
- Warehouses page
- Forecasts page
- Alerts page

**Search Capabilities:**
- Real-time filtering
- Multiple field search
- Case-insensitive
- No submit needed

**Filtering:**
- Status filter on Inventory
- Date range filter (future)
- Warehouse filter (future)

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Make sure venv is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

**Error:** `Port 8001 already in use`

**Solution:**
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill process (replace PID)
taskkill /PID <PID> /F

# OR use different port
python -m uvicorn backend.api:app --port 8002
```

#### 2. Frontend Won't Start

**Error:** `npm: command not found`

**Solution:**
```bash
# Install Node.js from https://nodejs.org
# Then run:
npm install -g npm@latest
```

**Error:** `Port 5173 already in use`

**Solution:**
```bash
# Vite will automatically try port 5174
# Or stop other Vite instance
```

#### 3. Data Not Loading

**Error:** `FileNotFoundError: data/inventory_data.csv`

**Solution:**
```bash
# Make sure you're in project root
cd D:\project

# Check data files exist
ls data/

# If missing, recreate from repository
```

#### 4. Login Not Working

**Issue:** "Invalid username or password"

**Solution:**
```javascript
// Check credentials:
Username: admin
Password: admin

// Case-sensitive, no spaces
// Clear browser cache if needed
```

#### 5. API Requests Failing

**Error:** `Failed to fetch`

**Solution:**
```bash
# Check backend is running
curl http://127.0.0.1:8001/health

# Check CORS settings in backend/api.py
# Should include frontend URL
```

#### 6. Simulation Not Updating

**Issue:** Dashboard not refreshing

**Solution:**
```javascript
// Check browser console for errors (F12)
// Force refresh: Ctrl + Shift + R
// Check API response in Network tab
```

### Debug Mode

**Enable Debug Logging:**

```python
# In backend/api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Check Logs:**

```bash
# Logs are in logs/ folder
cat logs/optimization.log
```

**Test API Directly:**

```bash
# Visit Swagger docs
http://127.0.0.1:8001/docs

# Try each endpoint manually
```

### Performance Issues

**Slow Simulation:**
- Reduce simulation days
- Decrease product count
- Check system resources

**Memory Usage:**
- Reset system periodically
- Clear daily snapshots
- Restart backend

**Frontend Lag:**
- Reduce table row count
- Enable pagination (future)
- Clear browser cache

---

## Development Notes

### Code Organization

**Backend:**
- `agents/` - Agent classes
- `models/` - Optimization algorithms
- `utils/` - Helper functions
- `backend/` - FastAPI application

**Frontend:**
- `src/App.jsx` - Main component (900+ lines)
- `src/api.js` - API calls
- `src/App.css` - Styles (900+ lines)

### Key Dependencies

**Python:**
- FastAPI - Web framework
- Pandas - Data manipulation
- NumPy/SciPy - Math/statistics
- Uvicorn - ASGI server

**JavaScript:**
- React - UI library
- Vite - Build tool
- Fetch API - HTTP requests

### Future Enhancements

1. **Database Integration:**
   - Replace CSV with PostgreSQL/MongoDB
   - Persistent storage
   - Better scalability

2. **Advanced Forecasting:**
   - ARIMA models
   - LSTM neural networks
   - Seasonal decomposition

3. **Reporting:**
   - PDF export
   - Excel reports
   - Email alerts

4. **Visualization:**
   - Charts (Chart.js)
   - Graphs (D3.js)
   - Dashboards

5. **Multi-User:**
   - Role-based access
   - User management
   - Audit logs

6. **Optimization:**
   - Genetic algorithms
   - Simulated annealing
   - Multi-objective optimization

---

## Conclusion

This system provides a complete solution for multi-warehouse inventory management using:

- **Multi-Agent Architecture** for distributed decision-making
- **Mathematical Optimization** for cost minimization
- **Statistical Forecasting** for demand prediction
- **Real-Time Monitoring** for operational visibility
- **Web Dashboard** for easy access and control

The system can be extended, customized, and scaled to meet specific business needs.

---

## Support

For issues, questions, or contributions:

- GitHub: https://github.com/Ezhil100/multiagent_inventory_optimzation_system
- Open an issue for bugs
- Submit pull requests for features

---

**Document Version:** 1.0  
**Last Updated:** January 28, 2026  
**Author:** Ezhil
