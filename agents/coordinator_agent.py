"""
Coordinator Agent Module
========================
Central orchestrator for the multi-agent inventory optimization system.

Responsibilities:
- Register and manage all agents (suppliers, warehouses, retailers)
- Coordinate inter-agent communication
- Run simulation time steps
- Optimize system-wide decisions
- Generate comprehensive reports for frontend
- Provide single API for all system data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
import json

from agents.base_agent import BaseAgent, Message, MessageType
from agents.supplier_agent import SupplierAgent
from agents.warehouse_agent import WarehouseAgent
from agents.retailer_agent import RetailerAgent


@dataclass
class SimulationConfig:
    """Configuration for simulation runs."""
    start_date: datetime = field(default_factory=datetime.now)
    num_days: int = 30
    time_step_hours: int = 24
    auto_reorder: bool = True
    simulate_demand: bool = True
    random_seed: Optional[int] = None


@dataclass
class DailySnapshot:
    """Snapshot of system state for a single day."""
    date: datetime
    total_inventory_value: float
    total_orders_placed: int
    total_stockouts: int
    items_below_rop: int
    items_critical: int
    total_holding_cost: float
    total_ordering_cost: float
    service_level: float


class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent - Central orchestrator for the entire system.
    
    This is the MAIN entry point for:
    - Running simulations
    - Getting system-wide data
    - Connecting to frontend
    
    Features:
    - Agent registration and management
    - Simulation loop execution
    - System-wide optimization
    - Comprehensive reporting
    - Data export for frontend
    """
    
    def __init__(self, agent_id: str = "COORD01", name: str = "System Coordinator"):
        super().__init__(agent_id, name)
        
        # Agent registries
        self.suppliers: Dict[str, SupplierAgent] = {}
        self.warehouses: Dict[str, WarehouseAgent] = {}
        self.retailers: Dict[str, RetailerAgent] = {}
        
        # Simulation state
        self.simulation_running = False
        self.current_day = 0
        self.config = SimulationConfig()
        
        # Historical data for frontend
        self.daily_snapshots: List[DailySnapshot] = []
        self.optimization_log: List[Dict] = []
        self.event_log: List[Dict] = []
        
        # Statistics
        self.total_simulation_days = 0
        self.total_orders_coordinated = 0
        self.total_value_optimized = 0.0
    
    # ==================== AGENT REGISTRATION ====================
    
    def register_supplier(self, supplier: SupplierAgent):
        """Register a supplier agent."""
        self.suppliers[supplier.agent_id] = supplier
        supplier.register_agent(self)
        self._cross_register_agent(supplier)
        print(f"  [Coordinator] Registered supplier: {supplier.name}")
    
    def register_warehouse(self, warehouse: WarehouseAgent):
        """Register a warehouse agent."""
        self.warehouses[warehouse.agent_id] = warehouse
        warehouse.register_agent(self)
        self._cross_register_agent(warehouse)
        print(f"  [Coordinator] Registered warehouse: {warehouse.name}")
    
    def register_retailer(self, retailer: RetailerAgent):
        """Register a retailer agent."""
        self.retailers[retailer.agent_id] = retailer
        retailer.register_agent(self)
        self._cross_register_agent(retailer)
        print(f"  [Coordinator] Registered retailer: {retailer.name}")
    
    def _cross_register_agent(self, agent: BaseAgent):
        """Register agent with all other agents for communication."""
        # Register with all suppliers
        for supplier in self.suppliers.values():
            if supplier.agent_id != agent.agent_id:
                supplier.register_agent(agent)
                agent.register_agent(supplier)
        
        # Register with all warehouses
        for warehouse in self.warehouses.values():
            if warehouse.agent_id != agent.agent_id:
                warehouse.register_agent(agent)
                agent.register_agent(warehouse)
        
        # Register with all retailers
        for retailer in self.retailers.values():
            if retailer.agent_id != agent.agent_id:
                retailer.register_agent(agent)
                agent.register_agent(retailer)
    
    def register_all(self, suppliers: List[SupplierAgent], 
                     warehouses: List[WarehouseAgent],
                     retailers: List[RetailerAgent]):
        """Register all agents at once."""
        for s in suppliers:
            self.register_supplier(s)
        for w in warehouses:
            self.register_warehouse(w)
        for r in retailers:
            self.register_retailer(r)
        
        print(f"\n  [Coordinator] Total registered: {len(self.suppliers)} suppliers, "
              f"{len(self.warehouses)} warehouses, {len(self.retailers)} retailers")
    
    # ==================== SIMULATION CONTROL ====================
    
    def configure_simulation(self, num_days: int = 30, 
                            start_date: datetime = None,
                            auto_reorder: bool = True,
                            simulate_demand: bool = True,
                            random_seed: int = None):
        """Configure simulation parameters."""
        self.config = SimulationConfig(
            start_date=start_date or datetime.now(),
            num_days=num_days,
            auto_reorder=auto_reorder,
            simulate_demand=simulate_demand,
            random_seed=random_seed
        )
        
        if random_seed:
            np.random.seed(random_seed)
        
        self.current_time = self.config.start_date
    
    def run_simulation(self, num_days: int = None) -> Dict[str, Any]:
        """
        Run the full simulation.
        
        Returns:
            Summary of simulation results
        """
        if num_days:
            self.config.num_days = num_days
        
        print("\n" + "=" * 60)
        print(f"Starting {self.config.num_days}-Day Simulation")
        print("=" * 60)
        
        self.simulation_running = True
        self.current_time = self.config.start_date
        self.daily_snapshots = []
        
        for day in range(self.config.num_days):
            self.current_day = day + 1
            self._run_daily_step()
        
        self.simulation_running = False
        self.total_simulation_days += self.config.num_days
        
        print("\n" + "=" * 60)
        print("Simulation Complete!")
        print("=" * 60)
        
        return self.get_simulation_summary()
    
    def _run_daily_step(self):
        """Execute one day of simulation."""
        date_str = self.current_time.strftime("%Y-%m-%d")
        
        if self.current_day % 7 == 1 or self.current_day == 1:  # Print weekly
            print(f"\n--- Day {self.current_day}: {date_str} ---")
        
        # 1. Simulate demand at warehouses (consume inventory)
        if self.config.simulate_demand:
            for warehouse in self.warehouses.values():
                warehouse.simulate_daily_demand()
        
        # 2. Check inventory and auto-reorder
        if self.config.auto_reorder:
            self._coordinate_reorders()
        
        # 3. Step all agents (process messages, deliveries)
        for supplier in self.suppliers.values():
            supplier.step(self.current_time)
        
        for warehouse in self.warehouses.values():
            warehouse.step(self.current_time)
        
        for retailer in self.retailers.values():
            retailer.step(self.current_time)
        
        # 4. Take daily snapshot
        snapshot = self._take_snapshot()
        self.daily_snapshots.append(snapshot)
        
        # 5. Advance time
        self.current_time += timedelta(days=1)
    
    def _coordinate_reorders(self):
        """Coordinate reorder decisions across all warehouses."""
        for warehouse in self.warehouses.values():
            reorders = warehouse.check_and_reorder(self.suppliers)
            self.total_orders_coordinated += len(reorders)
            
            for reorder in reorders:
                self.optimization_log.append({
                    "day": self.current_day,
                    "date": self.current_time.isoformat(),
                    "action": "reorder",
                    "warehouse": warehouse.name,
                    **reorder
                })
    
    def _take_snapshot(self) -> DailySnapshot:
        """Take a snapshot of current system state."""
        total_value = 0.0
        total_orders = 0
        total_stockouts = 0
        items_below_rop = 0
        items_critical = 0
        total_holding = 0.0
        total_ordering = 0.0
        
        for warehouse in self.warehouses.values():
            status = warehouse.get_status()
            total_value += status["total_stock_value"]
            total_orders += status["total_orders_placed"]
            total_stockouts += status["total_stockouts"]
            total_holding += status["total_holding_cost"]
            total_ordering += status["total_ordering_cost"]
            
            counts = status["status_counts"]
            items_below_rop += counts.get("REORDER", 0)
            items_critical += counts.get("CRITICAL", 0)
        
        # Calculate service level (1 - stockout rate)
        total_items = sum(len(w.inventory) for w in self.warehouses.values())
        service_level = 1 - (items_critical / max(1, total_items))
        
        return DailySnapshot(
            date=self.current_time,
            total_inventory_value=total_value,
            total_orders_placed=total_orders,
            total_stockouts=total_stockouts,
            items_below_rop=items_below_rop,
            items_critical=items_critical,
            total_holding_cost=total_holding,
            total_ordering_cost=total_ordering,
            service_level=service_level
        )
    
    def step_one_day(self) -> DailySnapshot:
        """Execute a single day step (for interactive use)."""
        self.current_day += 1
        self._run_daily_step()
        return self.daily_snapshots[-1]
    
    # ==================== DATA ACCESS FOR FRONTEND ====================
    
    def get_all_inventory(self) -> pd.DataFrame:
        """Get inventory data from all warehouses."""
        all_data = []
        
        for warehouse in self.warehouses.values():
            df = warehouse.get_inventory_summary()
            df['warehouse_id'] = warehouse.agent_id
            df['warehouse_name'] = warehouse.name
            all_data.append(df)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def get_all_forecasts(self) -> pd.DataFrame:
        """Get forecasts from all retailers."""
        all_data = []
        
        for retailer in self.retailers.values():
            df = retailer.get_forecast_data()
            if not df.empty:
                df['retailer_id'] = retailer.agent_id
                df['retailer_name'] = retailer.name
                all_data.append(df)
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def get_supplier_performance(self) -> pd.DataFrame:
        """Get performance metrics for all suppliers."""
        data = []
        
        for supplier in self.suppliers.values():
            metrics = supplier.get_performance_metrics()
            metrics['supplier_id'] = supplier.agent_id
            metrics['supplier_name'] = supplier.name
            data.append(metrics)
        
        return pd.DataFrame(data)
    
    def get_daily_history(self) -> pd.DataFrame:
        """Get daily snapshot history for charts."""
        data = []
        
        for snapshot in self.daily_snapshots:
            data.append({
                "date": snapshot.date,
                "inventory_value": snapshot.total_inventory_value,
                "orders_placed": snapshot.total_orders_placed,
                "stockouts": snapshot.total_stockouts,
                "items_below_rop": snapshot.items_below_rop,
                "items_critical": snapshot.items_critical,
                "holding_cost": snapshot.total_holding_cost,
                "ordering_cost": snapshot.total_ordering_cost,
                "total_cost": snapshot.total_holding_cost + snapshot.total_ordering_cost,
                "service_level": snapshot.service_level
            })
        
        return pd.DataFrame(data)
    
    def get_agent_status_summary(self) -> Dict[str, Any]:
        """Get status of all agents for frontend dashboard."""
        return {
            "suppliers": {
                s_id: supplier.get_status() 
                for s_id, supplier in self.suppliers.items()
            },
            "warehouses": {
                w_id: warehouse.get_status() 
                for w_id, warehouse in self.warehouses.items()
            },
            "retailers": {
                r_id: retailer.get_status() 
                for r_id, retailer in self.retailers.items()
            }
        }
    
    def get_alerts(self) -> List[Dict]:
        """Get current alerts and warnings."""
        alerts = []
        
        for warehouse in self.warehouses.values():
            # Critical items
            critical = warehouse.get_critical_items()
            for item in critical:
                alerts.append({
                    "level": "critical",
                    "type": "low_stock",
                    "warehouse": warehouse.name,
                    "product": item.product_name,
                    "product_id": item.product_id,
                    "current_stock": item.current_stock,
                    "safety_stock": item.calculated_safety_stock,
                    "message": f"CRITICAL: {item.product_name} stock ({item.current_stock}) below safety level ({item.calculated_safety_stock})"
                })
            
            # Reorder items
            reorder = warehouse.get_items_needing_reorder()
            for item in reorder:
                if item not in critical:
                    alerts.append({
                        "level": "warning",
                        "type": "reorder_needed",
                        "warehouse": warehouse.name,
                        "product": item.product_name,
                        "product_id": item.product_id,
                        "current_stock": item.current_stock,
                        "reorder_point": item.calculated_rop,
                        "message": f"REORDER: {item.product_name} stock ({item.current_stock}) below ROP ({item.calculated_rop})"
                    })
        
        return alerts
    
    def get_kpis(self) -> Dict[str, Any]:
        """Get key performance indicators for dashboard."""
        # Aggregate from all agents
        total_inventory_value = 0
        total_products = 0
        total_stockouts = 0
        total_orders = 0
        total_holding_cost = 0
        total_ordering_cost = 0
        
        for warehouse in self.warehouses.values():
            status = warehouse.get_status()
            total_inventory_value += status["total_stock_value"]
            total_products += status["total_products"]
            total_stockouts += status["total_stockouts"]
            total_orders += status["total_orders_placed"]
            total_holding_cost += status["total_holding_cost"]
            total_ordering_cost += status["total_ordering_cost"]
        
        # Supplier metrics
        total_fulfilled = 0
        total_on_time = 0
        for supplier in self.suppliers.values():
            metrics = supplier.get_performance_metrics()
            total_fulfilled += supplier.total_units_shipped
        
        # Calculate averages
        avg_service_level = np.mean([s.service_level for s in self.daily_snapshots]) if self.daily_snapshots else 0
        
        return {
            "total_inventory_value": round(total_inventory_value, 2),
            "total_products": total_products,
            "total_warehouses": len(self.warehouses),
            "total_suppliers": len(self.suppliers),
            "total_orders_placed": total_orders,
            "total_units_fulfilled": total_fulfilled,
            "total_stockouts": total_stockouts,
            "total_holding_cost": round(total_holding_cost, 2),
            "total_ordering_cost": round(total_ordering_cost, 2),
            "total_cost": round(total_holding_cost + total_ordering_cost, 2),
            "average_service_level": round(avg_service_level * 100, 1),
            "simulation_days": self.current_day,
            "alerts_count": len(self.get_alerts())
        }
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Get comprehensive simulation summary."""
        kpis = self.get_kpis()
        
        return {
            "simulation_config": {
                "days_simulated": self.config.num_days,
                "start_date": self.config.start_date.isoformat(),
                "auto_reorder": self.config.auto_reorder,
                "simulate_demand": self.config.simulate_demand
            },
            "kpis": kpis,
            "final_state": {
                "inventory": self.get_all_inventory().to_dict('records') if not self.get_all_inventory().empty else [],
                "alerts": self.get_alerts()
            },
            "optimization_actions": len(self.optimization_log)
        }
    
    # ==================== DATA EXPORT ====================
    
    def export_to_json(self, filepath: str = "data/simulation_results.json"):
        """Export simulation results to JSON."""
        data = {
            "summary": self.get_simulation_summary(),
            "daily_history": self.get_daily_history().to_dict('records'),
            "optimization_log": self.optimization_log
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        print(f"Results exported to {filepath}")
    
    def export_inventory_csv(self, filepath: str = "data/inventory_report.csv"):
        """Export current inventory to CSV."""
        df = self.get_all_inventory()
        df.to_csv(filepath, index=False)
        print(f"Inventory exported to {filepath}")
    
    # ==================== STATUS ====================
    
    def get_status(self) -> Dict[str, Any]:
        """Get coordinator status."""
        base_status = super().get_status()
        
        base_status.update({
            "registered_suppliers": len(self.suppliers),
            "registered_warehouses": len(self.warehouses),
            "registered_retailers": len(self.retailers),
            "simulation_running": self.simulation_running,
            "current_day": self.current_day,
            "total_simulation_days": self.total_simulation_days,
            "total_orders_coordinated": self.total_orders_coordinated,
            "snapshots_recorded": len(self.daily_snapshots)
        })
        
        return base_status
    
    def handle_message(self, message: Message):
        """Handle incoming messages."""
        # Log all messages for monitoring
        self.event_log.append({
            "timestamp": message.timestamp.isoformat(),
            "from": message.sender_id,
            "to": message.recipient_id,
            "type": message.message_type.value,
            "content_summary": str(message.content)[:100]
        })
