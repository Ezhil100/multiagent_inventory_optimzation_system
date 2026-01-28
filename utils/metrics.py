"""
Inventory Metrics Module
========================
KPIs and performance tracking for the inventory system.

Metrics:
- Inventory Turnover
- Days of Supply
- Fill Rate
- Stockout Rate
- Total Cost of Ownership
- Service Level
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class InventoryKPIs:
    """Key Performance Indicators for inventory."""
    inventory_turnover: float
    days_of_supply: float
    fill_rate: float
    stockout_rate: float
    service_level: float
    total_inventory_value: float
    total_holding_cost: float
    total_ordering_cost: float
    total_cost: float
    avg_order_cycle: float
    calculated_at: datetime = field(default_factory=datetime.now)


class InventoryMetrics:
    """
    Calculate inventory performance metrics.
    """
    
    @staticmethod
    def inventory_turnover(cost_of_goods_sold: float, 
                          average_inventory_value: float) -> float:
        """
        Calculate Inventory Turnover Ratio.
        
        Higher = better inventory management.
        Typical: 4-6 for most industries.
        
        Formula: COGS / Average Inventory Value
        """
        if average_inventory_value <= 0:
            return 0.0
        return round(cost_of_goods_sold / average_inventory_value, 2)
    
    @staticmethod
    def days_of_supply(current_inventory: float, 
                       daily_demand: float) -> float:
        """
        Calculate Days of Supply (DOS).
        
        How many days current inventory will last.
        
        Formula: Current Inventory / Daily Demand
        """
        if daily_demand <= 0:
            return float('inf')
        return round(current_inventory / daily_demand, 1)
    
    @staticmethod
    def fill_rate(units_shipped: int, units_ordered: int) -> float:
        """
        Calculate Fill Rate (Order Fulfillment Rate).
        
        Percentage of orders fulfilled completely.
        Target: > 95%
        
        Formula: Units Shipped / Units Ordered
        """
        if units_ordered <= 0:
            return 1.0
        return round(units_shipped / units_ordered, 4)
    
    @staticmethod
    def stockout_rate(stockout_events: int, total_demand_events: int) -> float:
        """
        Calculate Stockout Rate.
        
        Percentage of times demand couldn't be met.
        Target: < 5%
        
        Formula: Stockout Events / Total Demand Events
        """
        if total_demand_events <= 0:
            return 0.0
        return round(stockout_events / total_demand_events, 4)
    
    @staticmethod
    def service_level(units_fulfilled: int, units_demanded: int) -> float:
        """
        Calculate Service Level.
        
        Percentage of demand satisfied from stock.
        Target: > 95%
        
        Formula: Units Fulfilled / Units Demanded
        """
        if units_demanded <= 0:
            return 1.0
        return round(units_fulfilled / units_demanded, 4)
    
    @staticmethod
    def total_cost_of_ownership(holding_cost: float,
                                ordering_cost: float,
                                stockout_cost: float = 0) -> float:
        """
        Calculate Total Cost of Ownership.
        
        Formula: Holding Cost + Ordering Cost + Stockout Cost
        """
        return round(holding_cost + ordering_cost + stockout_cost, 2)
    
    @staticmethod
    def carrying_cost_percentage(holding_cost: float,
                                  average_inventory_value: float) -> float:
        """
        Calculate Carrying Cost as percentage of inventory value.
        
        Typical: 20-30% annually
        """
        if average_inventory_value <= 0:
            return 0.0
        return round((holding_cost / average_inventory_value) * 100, 2)
    
    @staticmethod
    def perfect_order_rate(orders_delivered_complete: int,
                           orders_delivered_on_time: int,
                           orders_delivered_undamaged: int,
                           total_orders: int) -> float:
        """
        Calculate Perfect Order Rate.
        
        Orders that are complete, on-time, and undamaged.
        """
        if total_orders <= 0:
            return 1.0
        
        # Minimum of all three factors
        perfect = min(
            orders_delivered_complete,
            orders_delivered_on_time,
            orders_delivered_undamaged
        )
        return round(perfect / total_orders, 4)
    
    @staticmethod
    def calculate_all(data: Dict[str, Any]) -> InventoryKPIs:
        """
        Calculate all KPIs from provided data.
        
        Args:
            data: Dictionary with required values:
                - cost_of_goods_sold
                - average_inventory_value
                - current_inventory
                - daily_demand
                - units_shipped
                - units_ordered
                - stockout_events
                - total_demand_events
                - holding_cost
                - ordering_cost
                - avg_order_cycle_days
        """
        return InventoryKPIs(
            inventory_turnover=InventoryMetrics.inventory_turnover(
                data.get('cost_of_goods_sold', 0),
                data.get('average_inventory_value', 1)
            ),
            days_of_supply=InventoryMetrics.days_of_supply(
                data.get('current_inventory', 0),
                data.get('daily_demand', 1)
            ),
            fill_rate=InventoryMetrics.fill_rate(
                data.get('units_shipped', 0),
                data.get('units_ordered', 1)
            ),
            stockout_rate=InventoryMetrics.stockout_rate(
                data.get('stockout_events', 0),
                data.get('total_demand_events', 1)
            ),
            service_level=InventoryMetrics.service_level(
                data.get('units_fulfilled', 0),
                data.get('units_demanded', 1)
            ),
            total_inventory_value=data.get('total_inventory_value', 0),
            total_holding_cost=data.get('holding_cost', 0),
            total_ordering_cost=data.get('ordering_cost', 0),
            total_cost=InventoryMetrics.total_cost_of_ownership(
                data.get('holding_cost', 0),
                data.get('ordering_cost', 0),
                data.get('stockout_cost', 0)
            ),
            avg_order_cycle=data.get('avg_order_cycle_days', 0)
        )


class PerformanceTracker:
    """
    Track performance metrics over time.
    """
    
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
        self.daily_metrics: List[InventoryKPIs] = []
    
    def record(self, timestamp: datetime, metrics: Dict[str, Any]):
        """Record metrics for a point in time."""
        entry = {
            "timestamp": timestamp,
            **metrics
        }
        self.history.append(entry)
    
    def record_kpis(self, kpis: InventoryKPIs):
        """Record KPIs."""
        self.daily_metrics.append(kpis)
    
    def get_trend(self, metric_name: str, periods: int = 7) -> List[float]:
        """Get trend for a specific metric over last N periods."""
        values = []
        for entry in self.history[-periods:]:
            if metric_name in entry:
                values.append(entry[metric_name])
        return values
    
    def get_average(self, metric_name: str, periods: int = None) -> float:
        """Get average of a metric over specified periods."""
        values = self.get_trend(metric_name, periods or len(self.history))
        return np.mean(values) if values else 0.0
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        if not self.history:
            return {}
        
        df = pd.DataFrame(self.history)
        
        summary = {}
        for col in df.select_dtypes(include=[np.number]).columns:
            summary[col] = {
                "mean": round(df[col].mean(), 2),
                "min": round(df[col].min(), 2),
                "max": round(df[col].max(), 2),
                "std": round(df[col].std(), 2),
                "latest": round(df[col].iloc[-1], 2) if len(df) > 0 else 0
            }
        
        return summary
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert history to DataFrame."""
        return pd.DataFrame(self.history)
    
    def get_alerts(self, thresholds: Dict[str, float] = None) -> List[Dict]:
        """
        Generate alerts based on thresholds.
        
        Default thresholds:
        - stockout_rate > 0.05 (5%)
        - service_level < 0.95 (95%)
        - days_of_supply < 7
        """
        if thresholds is None:
            thresholds = {
                "stockout_rate_max": 0.05,
                "service_level_min": 0.95,
                "days_of_supply_min": 7
            }
        
        alerts = []
        
        if self.daily_metrics:
            latest = self.daily_metrics[-1]
            
            if latest.stockout_rate > thresholds.get("stockout_rate_max", 0.05):
                alerts.append({
                    "level": "warning",
                    "metric": "stockout_rate",
                    "value": latest.stockout_rate,
                    "threshold": thresholds["stockout_rate_max"],
                    "message": f"Stockout rate ({latest.stockout_rate:.1%}) exceeds threshold"
                })
            
            if latest.service_level < thresholds.get("service_level_min", 0.95):
                alerts.append({
                    "level": "warning",
                    "metric": "service_level",
                    "value": latest.service_level,
                    "threshold": thresholds["service_level_min"],
                    "message": f"Service level ({latest.service_level:.1%}) below threshold"
                })
            
            if latest.days_of_supply < thresholds.get("days_of_supply_min", 7):
                alerts.append({
                    "level": "critical",
                    "metric": "days_of_supply",
                    "value": latest.days_of_supply,
                    "threshold": thresholds["days_of_supply_min"],
                    "message": f"Days of supply ({latest.days_of_supply:.1f}) critically low"
                })
        
        return alerts


def format_currency(value: float) -> str:
    """Format value as currency."""
    return f"${value:,.2f}"


def format_percentage(value: float) -> str:
    """Format value as percentage."""
    return f"{value * 100:.1f}%"


def format_number(value: float) -> str:
    """Format large numbers with K/M suffix."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.0f}"
