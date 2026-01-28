"""
FastAPI Backend for Multi-Agent Inventory Optimization System
==============================================================
REST API endpoints for the React frontend.

Run with: uvicorn backend.api:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.supplier_agent import SupplierAgent
from agents.warehouse_agent import WarehouseAgent
from agents.retailer_agent import RetailerAgent
from agents.coordinator_agent import CoordinatorAgent
import config

# ==================== FastAPI App ====================
app = FastAPI(
    title="Inventory Optimization API",
    description="Multi-Agent Inventory Optimization System API",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Global State ====================
# Store coordinator instance for the session
coordinator: Optional[CoordinatorAgent] = None
simulation_initialized = False


# ==================== Pydantic Models ====================
class SimulationConfig(BaseModel):
    num_days: int = 30
    auto_reorder: bool = True
    simulate_demand: bool = True
    random_seed: int = 42


class StepResponse(BaseModel):
    day: int
    date: str
    inventory_value: float
    orders_placed: int
    stockouts: int
    service_level: float


class KPIResponse(BaseModel):
    total_inventory_value: float
    total_products: int
    total_warehouses: int
    total_suppliers: int
    total_orders_placed: int
    total_units_fulfilled: int
    total_stockouts: int
    total_holding_cost: float
    total_ordering_cost: float
    total_cost: float
    average_service_level: float
    simulation_days: int
    alerts_count: int


class AlertResponse(BaseModel):
    level: str
    type: str
    warehouse: str
    product: str
    product_id: str
    current_stock: int
    message: str


class InventoryItemResponse(BaseModel):
    product_id: str
    product_name: str
    category: str
    current_stock: int
    reorder_point: int
    safety_stock: int
    eoq: int
    days_of_supply: float
    stock_value: float
    status: str
    warehouse_id: str
    warehouse_name: str


# ==================== Helper Functions ====================
def initialize_system():
    """Initialize the multi-agent system."""
    global coordinator, simulation_initialized
    
    # Load data
    inventory_df = pd.read_csv(config.INVENTORY_FILE)
    sales_df = pd.read_csv(config.SALES_FILE)
    suppliers_df = pd.read_csv(config.SUPPLIERS_FILE)
    warehouses_df = pd.read_csv(config.WAREHOUSES_FILE)
    
    # Create suppliers
    suppliers = []
    for _, row in suppliers_df.iterrows():
        supplier = SupplierAgent(
            agent_id=row['supplier_id'],
            name=row['supplier_name'],
            lead_time_days=int(row['avg_lead_time']),
            reliability=float(row['reliability_score']),
            max_daily_capacity=int(row['max_capacity_per_month'] / 30)
        )
        suppliers.append(supplier)
    
    # Create warehouses
    warehouses = []
    for _, row in warehouses_df.iterrows():
        warehouse = WarehouseAgent(
            agent_id=row['warehouse_id'],
            name=row['warehouse_name'],
            location=row['location'],
            service_level=0.95,
            inventory_df=inventory_df
        )
        warehouses.append(warehouse)
    
    # Create retailer
    retailer = RetailerAgent(
        agent_id="RET01",
        name="Main Retailer",
        forecast_horizon=7,
        ma_window=7,
        ema_alpha=0.3,
        sales_history=sales_df
    )
    
    # Create coordinator
    coordinator = CoordinatorAgent(
        agent_id="COORD01",
        name="System Coordinator"
    )
    coordinator.register_all(suppliers, warehouses, [retailer])
    
    simulation_initialized = True
    return coordinator


def get_coordinator():
    """Get or create coordinator instance."""
    global coordinator, simulation_initialized
    if not simulation_initialized or coordinator is None:
        initialize_system()
    return coordinator


# ==================== API Endpoints ====================

@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Multi-Agent Inventory Optimization API",
        "version": "1.0.0",
        "status": "running",
        "initialized": simulation_initialized
    }


@app.post("/api/initialize")
async def initialize():
    """Initialize or reset the system."""
    global coordinator, simulation_initialized
    simulation_initialized = False
    coordinator = None
    coord = get_coordinator()
    return {
        "status": "initialized",
        "suppliers": len(coord.suppliers),
        "warehouses": len(coord.warehouses),
        "retailers": len(coord.retailers)
    }


@app.post("/api/simulation/configure")
async def configure_simulation(config: SimulationConfig):
    """Configure simulation parameters."""
    coord = get_coordinator()
    coord.configure_simulation(
        num_days=config.num_days,
        start_date=datetime.now(),
        auto_reorder=config.auto_reorder,
        simulate_demand=config.simulate_demand,
        random_seed=config.random_seed
    )
    return {"status": "configured", "config": config.dict()}


@app.post("/api/simulation/run")
async def run_simulation(days: int = Query(default=30, ge=1, le=365)):
    """Run full simulation for specified days."""
    coord = get_coordinator()
    coord.configure_simulation(num_days=days, start_date=datetime.now())
    
    try:
        results = coord.run_simulation(days)
        
        # Regenerate forecasts after simulation (based on new sales data)
        for retailer in coord.retailers.values():
            retailer.generate_all_forecasts(method="weighted")
        
        # Ensure datetime objects are serialized properly
        import json
        def serialize_datetime(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)
        
        # Convert to JSON-safe format
        safe_results = json.loads(json.dumps(results, default=serialize_datetime))
        
        return {
            "status": "completed",
            "days_simulated": days,
            "summary": safe_results
        }
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "days_simulated": days
        }


@app.post("/api/simulation/step")
async def step_simulation():
    """Execute one day of simulation."""
    coord = get_coordinator()
    if coord.current_day == 0:
        coord.configure_simulation(num_days=365, start_date=datetime.now())
    
    snapshot = coord.step_one_day()
    
    return StepResponse(
        day=coord.current_day,
        date=snapshot.date.isoformat(),
        inventory_value=snapshot.total_inventory_value,
        orders_placed=snapshot.total_orders_placed,
        stockouts=snapshot.total_stockouts,
        service_level=snapshot.service_level
    )


@app.get("/api/kpis", response_model=KPIResponse)
async def get_kpis():
    """Get current KPIs."""
    coord = get_coordinator()
    kpis = coord.get_kpis()
    return KPIResponse(**kpis)


@app.get("/api/inventory")
async def get_inventory(
    warehouse_id: Optional[str] = None,
    status: Optional[str] = None
):
    """Get inventory data with optional filters."""
    coord = get_coordinator()
    df = coord.get_all_inventory()
    
    if df.empty:
        return {"items": [], "total": 0}
    
    # Apply filters
    if warehouse_id:
        df = df[df['warehouse_id'] == warehouse_id]
    if status:
        df = df[df['status'] == status]
    
    items = df.to_dict('records')
    return {
        "items": items,
        "total": len(items),
        "by_status": df['status'].value_counts().to_dict() if not df.empty else {}
    }


@app.get("/api/alerts", response_model=List[AlertResponse])
async def get_alerts():
    """Get current alerts."""
    coord = get_coordinator()
    alerts = coord.get_alerts()
    return [AlertResponse(**{**a, 'current_stock': a.get('current_stock', 0)}) for a in alerts]


@app.get("/api/warehouses")
async def get_warehouses():
    """Get warehouse status."""
    coord = get_coordinator()
    status = coord.get_agent_status_summary()
    return {
        "warehouses": status.get("warehouses", {}),
        "total": len(coord.warehouses)
    }


@app.get("/api/suppliers")
async def get_suppliers():
    """Get supplier performance."""
    coord = get_coordinator()
    df = coord.get_supplier_performance()
    
    if df.empty:
        return {"suppliers": [], "total": 0}
    
    return {
        "suppliers": df.to_dict('records'),
        "total": len(df)
    }


@app.get("/api/forecasts")
async def get_forecasts():
    """Get demand forecasts based on warehouse demand history."""
    coord = get_coordinator()
    
    # First try to get retailer forecasts
    df = coord.get_all_forecasts()
    
    if df.empty:
        # Generate forecasts from warehouse inventory data instead
        forecasts = []
        for warehouse in coord.warehouses.values():
            for product_id, item in warehouse.inventory.items():
                demand_history = item.demand_history
                if demand_history and len(demand_history) > 0:
                    avg_demand = sum(demand_history) / len(demand_history)
                    std_demand = (sum((x - avg_demand) ** 2 for x in demand_history) / len(demand_history)) ** 0.5
                    forecast_days = 7
                    predicted = avg_demand * forecast_days
                    forecasts.append({
                        "product_id": product_id,
                        "product_name": item.name,
                        "warehouse": warehouse.name,
                        "daily_avg": round(avg_demand, 1),
                        "daily_std": round(std_demand, 1),
                        "forecast_horizon_days": forecast_days,
                        "predicted_total": round(predicted, 0),
                        "confidence_lower": round(max(0, predicted - 1.96 * std_demand * (forecast_days ** 0.5)), 0),
                        "confidence_upper": round(predicted + 1.96 * std_demand * (forecast_days ** 0.5), 0),
                        "method": "warehouse_demand",
                        "data_points": len(demand_history)
                    })
        
        if forecasts:
            return {"forecasts": forecasts, "total": len(forecasts)}
    
    if df.empty:
        return {"forecasts": [], "total": 0}
    
    return {
        "forecasts": df.to_dict('records'),
        "total": len(df)
    }


@app.get("/api/history")
async def get_history():
    """Get daily simulation history."""
    coord = get_coordinator()
    df = coord.get_daily_history()
    
    if df.empty:
        return {"history": [], "days": 0}
    
    # Convert datetime to string for JSON
    df['date'] = df['date'].astype(str)
    
    return {
        "history": df.to_dict('records'),
        "days": len(df)
    }


@app.get("/api/orders")
async def get_orders():
    """Get all orders from optimization log."""
    coord = get_coordinator()
    orders = [log for log in coord.optimization_log if log.get("action") == "reorder"]
    return {
        "orders": orders[-50:],  # Last 50 orders
        "total": len(orders)
    }


@app.get("/api/agents/status")
async def get_agent_status():
    """Get status of all agents."""
    coord = get_coordinator()
    return coord.get_agent_status_summary()


@app.get("/api/optimization/log")
async def get_optimization_log():
    """Get optimization actions log."""
    coord = get_coordinator()
    return {
        "log": coord.optimization_log[-100:],  # Last 100 entries
        "total_actions": len(coord.optimization_log)
    }


@app.post("/api/reset")
async def reset_system():
    """Reset the entire system."""
    global coordinator, simulation_initialized
    simulation_initialized = False
    coordinator = None
    return {"status": "reset", "message": "System has been reset"}


# ==================== Health Check ====================
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "initialized": simulation_initialized
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
