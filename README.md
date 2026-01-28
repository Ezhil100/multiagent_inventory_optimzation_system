# Multi-Agent Inventory Optimization System

A sophisticated inventory management system using multi-agent architecture with demand forecasting, EOQ optimization, and real-time monitoring dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128-green.svg)
![React](https://img.shields.io/badge/React-18+-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [API Documentation](#api-documentation)
- [Usage Guide](#usage-guide)
- [Technical Details](#technical-details)

---

## 🎯 Overview

This system simulates and optimizes inventory management across multiple warehouses using autonomous agents that communicate and coordinate to:

- **Forecast demand** using multiple statistical methods
- **Calculate optimal order quantities** (EOQ)
- **Determine safety stock levels** based on service level targets
- **Automatically place orders** when inventory falls below reorder points
- **Track KPIs** and generate alerts

---

## ✨ Features

### Multi-Agent System
- **Supplier Agent**: Manages orders, lead times, and deliveries
- **Warehouse Agent**: Handles inventory, calculates EOQ/ROP/Safety Stock
- **Retailer Agent**: Forecasts demand using MA, EMA, Weighted methods
- **Coordinator Agent**: Orchestrates all agents and provides API for frontend

### Optimization Models
- **EOQ (Economic Order Quantity)**: Minimizes total inventory costs
- **Safety Stock**: Z-score based calculation for target service levels
- **Reorder Point (ROP)**: Triggers automatic replenishment
- **Demand Forecasting**: SMA, EMA, Weighted Moving Average, Holt's Method

### Dashboard Features
- Real-time KPI monitoring
- Inventory status table with filtering
- Alert system (Critical/Warning)
- Simulation controls
- Historical data tracking

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Frontend (5173)                     │
│         Dashboard | KPIs | Alerts | Inventory Table          │
└─────────────────────────────┬───────────────────────────────┘
                              │ HTTP/REST
┌─────────────────────────────▼───────────────────────────────┐
│                  FastAPI Backend (8001)                      │
│              /api/kpis | /api/inventory | etc.               │
└─────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────┐
│                   Coordinator Agent                          │
│            Orchestrates all agent interactions               │
└──────┬──────────────────┬──────────────────┬────────────────┘
       │                  │                  │
┌──────▼──────┐   ┌───────▼───────┐   ┌──────▼──────┐
│  Supplier   │   │   Warehouse   │   │   Retailer  │
│   Agents    │   │    Agents     │   │    Agent    │
│  (3 total)  │   │   (3 total)   │   │  (1 total)  │
└─────────────┘   └───────────────┘   └─────────────┘
```

---

## 📁 Project Structure

```
d:\project\
├── venv/                      # Python virtual environment
├── data/                      # CSV data files
│   ├── inventory_data.csv     # 20 products inventory
│   ├── sales_history.csv      # Historical sales data
│   ├── suppliers.csv          # 3 suppliers
│   └── warehouses.csv         # 3 warehouses
├── agents/                    # Multi-agent modules
│   ├── __init__.py
│   ├── base_agent.py          # Base class, Message, Order dataclasses
│   ├── supplier_agent.py      # Order processing, deliveries
│   ├── warehouse_agent.py     # EOQ, ROP, Safety Stock calculations
│   ├── retailer_agent.py      # Demand forecasting
│   └── coordinator_agent.py   # Central orchestration
├── models/                    # Optimization models
│   ├── __init__.py
│   ├── demand_forecast.py     # Forecasting algorithms
│   └── optimization.py        # EOQ, Safety Stock calculators
├── utils/                     # Utility functions
│   ├── __init__.py
│   └── metrics.py             # KPI calculations
├── backend/                   # FastAPI backend
│   ├── __init__.py
│   └── api.py                 # REST API endpoints
├── frontend/                  # React frontend
│   ├── node_modules/
│   ├── src/
│   │   ├── api.js             # API service
│   │   ├── App.jsx            # Main dashboard component
│   │   ├── App.css            # Styles
│   │   ├── index.css          # Global styles
│   │   └── main.jsx           # Entry point
│   ├── package.json
│   └── vite.config.js
├── logs/                      # Log files directory
├── config.py                  # Configuration settings
├── main.py                    # CLI entry point
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

---

## 🚀 Installation

### Prerequisites

- **Python 3.10+** 
- **Node.js 18+** and npm
- **Git**

### Step 1: Clone the Repository

```bash
git clone https://github.com/Ezhil100/multiagent_inventory_optimzation_system.git
cd multiagent_inventory_optimzation_system
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# OR
.\venv\Scripts\activate.bat

# Linux/Mac:
source venv/bin/activate
```

### Step 3: Install Python Dependencies

```bash
# Make sure venv is activated!
pip install -r requirements.txt
```

### Step 4: Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

---

## ▶️ Running the System

### Option 1: Run Both Servers (Recommended)

**Terminal 1 - Backend (Python/FastAPI):**
```bash
cd d:\project
.\venv\Scripts\Activate.ps1
python -m uvicorn backend.api:app --host 127.0.0.1 --port 8001
```

**Terminal 2 - Frontend (React/Vite):**
```bash
cd d:\project\frontend
npm run dev
```

**Access the Dashboard:**
- Frontend: http://localhost:5173
- API Docs: http://127.0.0.1:8001/docs

### Option 2: Run CLI Only (No Frontend)

```bash
cd d:\project
.\venv\Scripts\Activate.ps1
python main.py
```

---

## 📡 API Documentation

### Base URL: `http://127.0.0.1:8001`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/initialize` | POST | Initialize system |
| `/api/kpis` | GET | Get KPIs |
| `/api/inventory` | GET | Get inventory (filter: `?status=CRITICAL`) |
| `/api/alerts` | GET | Get alerts |
| `/api/warehouses` | GET | Warehouse status |
| `/api/suppliers` | GET | Supplier performance |
| `/api/forecasts` | GET | Demand forecasts |
| `/api/history` | GET | Simulation history |
| `/api/simulation/run?days=30` | POST | Run simulation |
| `/api/simulation/step` | POST | Step one day |
| `/api/reset` | POST | Reset system |

### Example API Calls

```bash
# Get KPIs
curl http://127.0.0.1:8001/api/kpis

# Run 7-day simulation
curl -X POST "http://127.0.0.1:8001/api/simulation/run?days=7"

# Get alerts
curl http://127.0.0.1:8001/api/alerts
```

---

## 📖 Usage Guide

### Dashboard Features

1. **KPI Cards**: Shows inventory value, service level, orders, costs
2. **Alerts Panel**: Critical (red) and warning (yellow) alerts
3. **Inventory Table**: Filter by status (OK, REORDER, CRITICAL)
4. **Simulation Controls**: 
   - Set days (1-365)
   - Click "Run Simulation" to execute
   - Click "Reset" to start fresh

### Running a Simulation

1. Open dashboard at http://localhost:5173
2. Enter number of days (e.g., 30)
3. Click "▶ Run Simulation"
4. Watch KPIs update
5. Check alerts and inventory status

---

## 🔧 Technical Details

### Optimization Formulas

**EOQ (Economic Order Quantity):**
```
EOQ = √(2 × D × S / H)
Where:
  D = Annual demand
  S = Ordering cost per order
  H = Holding cost per unit per year
```

**Safety Stock:**
```
SS = Z × σ × √L
Where:
  Z = Z-score for service level (95% → 1.645)
  σ = Standard deviation of demand
  L = Lead time in days
```

**Reorder Point:**
```
ROP = (D × L) + SS
Where:
  D = Average daily demand
  L = Lead time
  SS = Safety stock
```

### Agent Communication

Agents communicate via message passing:
- `ORDER_REQUEST`: Warehouse → Supplier
- `ORDER_CONFIRMATION`: Supplier → Warehouse
- `SHIPMENT_NOTIFICATION`: Supplier → Warehouse
- `DELIVERY_COMPLETE`: Supplier → Warehouse
- `FORECAST_UPDATE`: Retailer → Coordinator

---

## 📦 Dependencies

### Python (requirements.txt)
```
pandas>=2.0.0
numpy>=1.24.0
scipy>=1.10.0
mesa>=2.1.0
pulp>=2.7.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.2.0
fastapi>=0.100.0
uvicorn>=0.22.0
python-multipart>=0.0.6
requests>=2.31.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.x",
    "react-dom": "^18.x"
  },
  "devDependencies": {
    "vite": "^5.x"
  }
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👤 Author

**Ezhil**

- GitHub: [@Ezhil100](https://github.com/Ezhil100)

---

## 🙏 Acknowledgments

- Built with FastAPI, React, and Python
- Multi-agent architecture inspired by MESA framework
- Inventory optimization based on classical operations research models
