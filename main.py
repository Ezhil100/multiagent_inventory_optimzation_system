"""
Multi-Agent Inventory Optimization System
==========================================
Main entry point for running the inventory optimization simulation.

This system uses cooperative agents to optimize inventory levels:
- SupplierAgent: Manages supply capacity and fulfills orders
- WarehouseAgent: Tracks inventory, calculates EOQ/ROP/Safety Stock
- RetailerAgent: Forecasts demand, requests stock
- CoordinatorAgent: Orchestrates system-wide optimization

Usage:
    python main.py              # Run default 30-day simulation
    python main.py --days 60    # Run 60-day simulation
    python main.py --interactive  # Step-by-step mode
"""

import pandas as pd
import numpy as np
from datetime import datetime
import argparse
import sys

# Import agents
from agents.supplier_agent import SupplierAgent
from agents.warehouse_agent import WarehouseAgent
from agents.retailer_agent import RetailerAgent
from agents.coordinator_agent import CoordinatorAgent

# Import models
from models.demand_forecast import DemandForecaster
from models.optimization import EOQCalculator, SafetyStockCalculator, InventoryOptimizer

# Import utilities
from utils.metrics import InventoryMetrics, PerformanceTracker, format_currency, format_percentage

# Configuration
import config


def load_data():
    """Load all data files."""
    print("\n📂 Loading data files...")
    
    inventory_df = pd.read_csv(config.INVENTORY_FILE)
    sales_df = pd.read_csv(config.SALES_FILE)
    suppliers_df = pd.read_csv(config.SUPPLIERS_FILE)
    warehouses_df = pd.read_csv(config.WAREHOUSES_FILE)
    
    print(f"   ✓ Inventory: {len(inventory_df)} products")
    print(f"   ✓ Sales history: {len(sales_df)} records")
    print(f"   ✓ Suppliers: {len(suppliers_df)}")
    print(f"   ✓ Warehouses: {len(warehouses_df)}")
    
    return inventory_df, sales_df, suppliers_df, warehouses_df


def create_agents(inventory_df, sales_df, suppliers_df, warehouses_df):
    """Create all agent instances."""
    print("\n🤖 Creating agents...")
    
    # Create supplier agents
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
        print(f"   ✓ Supplier: {supplier.name} (reliability: {supplier.reliability:.0%})")
    
    # Create warehouse agents
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
        print(f"   ✓ Warehouse: {warehouse.name} ({len(warehouse.inventory)} products)")
    
    # Create retailer agent
    retailer = RetailerAgent(
        agent_id="RET01",
        name="Main Retailer",
        forecast_horizon=7,
        ma_window=7,
        ema_alpha=0.3,
        sales_history=sales_df
    )
    print(f"   ✓ Retailer: {retailer.name} ({len(retailer.sales_history)} products tracked)")
    
    # Create coordinator
    coordinator = CoordinatorAgent(
        agent_id="COORD01",
        name="System Coordinator"
    )
    print(f"   ✓ Coordinator: {coordinator.name}")
    
    return suppliers, warehouses, [retailer], coordinator


def print_inventory_report(coordinator):
    """Print detailed inventory report."""
    print("\n" + "=" * 70)
    print("📦 INVENTORY STATUS REPORT")
    print("=" * 70)
    
    inventory_df = coordinator.get_all_inventory()
    
    if inventory_df.empty:
        print("No inventory data available.")
        return
    
    # Group by status
    for status in ["CRITICAL", "REORDER", "OK", "OVERSTOCKED"]:
        status_items = inventory_df[inventory_df['status'] == status]
        if not status_items.empty:
            icon = {"CRITICAL": "🔴", "REORDER": "🟡", "OK": "🟢", "OVERSTOCKED": "🔵"}[status]
            print(f"\n{icon} {status} ({len(status_items)} items):")
            print("-" * 70)
            
            for _, item in status_items.iterrows():
                print(f"   {item['product_name'][:30]:<30} | "
                      f"Stock: {item['current_stock']:>5} | "
                      f"ROP: {item['reorder_point']:>5} | "
                      f"EOQ: {item['eoq']:>5} | "
                      f"DoS: {item['days_of_supply']:>5.1f}")


def print_kpi_dashboard(coordinator):
    """Print KPI dashboard."""
    print("\n" + "=" * 70)
    print("📊 KEY PERFORMANCE INDICATORS")
    print("=" * 70)
    
    kpis = coordinator.get_kpis()
    
    print(f"""
    ┌─────────────────────────────────────────────────────────────────┐
    │  Total Inventory Value:    {format_currency(kpis['total_inventory_value']):>15}              │
    │  Total Products:           {kpis['total_products']:>15}              │
    │  Warehouses:               {kpis['total_warehouses']:>15}              │
    │  Suppliers:                {kpis['total_suppliers']:>15}              │
    ├─────────────────────────────────────────────────────────────────┤
    │  Orders Placed:            {kpis['total_orders_placed']:>15}              │
    │  Units Fulfilled:          {kpis['total_units_fulfilled']:>15}              │
    │  Stockouts:                {kpis['total_stockouts']:>15}              │
    ├─────────────────────────────────────────────────────────────────┤
    │  Holding Cost:             {format_currency(kpis['total_holding_cost']):>15}              │
    │  Ordering Cost:            {format_currency(kpis['total_ordering_cost']):>15}              │
    │  Total Cost:               {format_currency(kpis['total_cost']):>15}              │
    ├─────────────────────────────────────────────────────────────────┤
    │  Service Level:            {kpis['average_service_level']:>14.1f}%              │
    │  Alerts:                   {kpis['alerts_count']:>15}              │
    └─────────────────────────────────────────────────────────────────┘
    """)


def print_alerts(coordinator):
    """Print current alerts."""
    alerts = coordinator.get_alerts()
    
    if not alerts:
        print("\n✅ No alerts - all inventory levels healthy!")
        return
    
    print("\n" + "=" * 70)
    print(f"⚠️  ALERTS ({len(alerts)} items need attention)")
    print("=" * 70)
    
    critical = [a for a in alerts if a['level'] == 'critical']
    warnings = [a for a in alerts if a['level'] == 'warning']
    
    if critical:
        print("\n🔴 CRITICAL:")
        for alert in critical[:5]:  # Show top 5
            print(f"   • {alert['message']}")
    
    if warnings:
        print("\n🟡 WARNINGS:")
        for alert in warnings[:5]:  # Show top 5
            print(f"   • {alert['message']}")


def run_simulation(num_days=30, interactive=False):
    """
    Run the multi-agent inventory optimization simulation.
    
    Args:
        num_days: Number of days to simulate
        interactive: If True, pause after each day
    """
    print("\n" + "=" * 70)
    print("🏭 MULTI-AGENT INVENTORY OPTIMIZATION SYSTEM")
    print("=" * 70)
    print(f"   Simulation: {num_days} days")
    print(f"   Mode: {'Interactive' if interactive else 'Automatic'}")
    
    # Load data
    inventory_df, sales_df, suppliers_df, warehouses_df = load_data()
    
    # Create agents
    suppliers, warehouses, retailers, coordinator = create_agents(
        inventory_df, sales_df, suppliers_df, warehouses_df
    )
    
    # Register all agents with coordinator
    print("\n🔗 Registering agents with coordinator...")
    coordinator.register_all(suppliers, warehouses, retailers)
    
    # Configure simulation
    coordinator.configure_simulation(
        num_days=num_days,
        start_date=datetime.now(),
        auto_reorder=True,
        simulate_demand=True,
        random_seed=42  # For reproducibility
    )
    
    # Generate initial forecasts
    print("\n📈 Generating demand forecasts...")
    for retailer in retailers:
        retailer.generate_all_forecasts(method="weighted")
        forecast_df = retailer.get_forecast_data()
        if not forecast_df.empty:
            print(f"   ✓ {len(forecast_df)} product forecasts generated")
    
    # Run simulation
    if interactive:
        print("\n🎮 Interactive mode - press Enter to advance each day, 'q' to quit")
        for day in range(num_days):
            snapshot = coordinator.step_one_day()
            print(f"\nDay {day + 1}: Value=${snapshot.total_inventory_value:,.0f}, "
                  f"Orders={snapshot.total_orders_placed}, "
                  f"Stockouts={snapshot.total_stockouts}")
            
            user_input = input("Press Enter for next day (q to quit, r for report): ")
            if user_input.lower() == 'q':
                break
            elif user_input.lower() == 'r':
                print_inventory_report(coordinator)
    else:
        # Run full simulation
        results = coordinator.run_simulation(num_days)
    
    # Print final reports
    print_kpi_dashboard(coordinator)
    print_alerts(coordinator)
    print_inventory_report(coordinator)
    
    # Export results
    print("\n💾 Exporting results...")
    coordinator.export_inventory_csv("data/inventory_report.csv")
    coordinator.export_to_json("data/simulation_results.json")
    
    # Save daily history for charts
    history_df = coordinator.get_daily_history()
    if not history_df.empty:
        history_df.to_csv("data/daily_history.csv", index=False)
        print("   ✓ Daily history saved to data/daily_history.csv")
    
    print("\n" + "=" * 70)
    print("✅ Simulation complete!")
    print("=" * 70)
    
    return coordinator


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent Inventory Optimization System"
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=30,
        help='Number of days to simulate (default: 30)'
    )
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Run in interactive step-by-step mode'
    )
    parser.add_argument(
        '--seed', '-s',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    args = parser.parse_args()
    
    if args.seed:
        np.random.seed(args.seed)
    
    coordinator = run_simulation(
        num_days=args.days,
        interactive=args.interactive
    )
    
    return coordinator


if __name__ == "__main__":
    coordinator = main()
