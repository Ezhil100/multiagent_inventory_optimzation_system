"""
Inventory Optimization Models
=============================
Mathematical optimization models for inventory management.

Models:
- EOQ (Economic Order Quantity)
- Safety Stock Optimization
- Reorder Point Calculation
- Total Cost Optimization
- Multi-item Optimization
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy.optimize import minimize, minimize_scalar


@dataclass
class EOQResult:
    """Result of EOQ calculation."""
    product_id: str
    eoq: int
    annual_demand: float
    ordering_cost: float
    holding_cost: float
    total_annual_cost: float
    orders_per_year: float
    cycle_time_days: float


@dataclass
class SafetyStockResult:
    """Result of safety stock calculation."""
    product_id: str
    safety_stock: int
    service_level: float
    z_score: float
    demand_std: float
    lead_time_days: int
    stockout_probability: float


@dataclass
class OptimizationResult:
    """Result of inventory optimization."""
    product_id: str
    optimal_order_qty: int
    reorder_point: int
    safety_stock: int
    total_annual_cost: float
    holding_cost: float
    ordering_cost: float
    stockout_cost: float
    service_level: float


class EOQCalculator:
    """
    Economic Order Quantity (EOQ) Calculator.
    
    Uses the Wilson Formula to find optimal order quantity
    that minimizes total inventory costs.
    """
    
    @staticmethod
    def calculate(annual_demand: float,
                  ordering_cost: float,
                  holding_cost_per_unit: float,
                  product_id: str = "unknown") -> EOQResult:
        """
        Calculate Economic Order Quantity.
        
        EOQ = sqrt((2 * D * S) / H)
        
        Args:
            annual_demand: Total annual demand (units)
            ordering_cost: Cost per order ($)
            holding_cost_per_unit: Annual holding cost per unit ($)
            product_id: Product identifier
            
        Returns:
            EOQResult with optimal quantity and costs
        """
        if holding_cost_per_unit <= 0 or annual_demand <= 0:
            # Return sensible default
            return EOQResult(
                product_id=product_id,
                eoq=max(1, int(annual_demand / 12)),
                annual_demand=annual_demand,
                ordering_cost=ordering_cost,
                holding_cost=holding_cost_per_unit,
                total_annual_cost=0,
                orders_per_year=12,
                cycle_time_days=30
            )
        
        # EOQ formula
        eoq = np.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)
        eoq = max(1, int(round(eoq)))
        
        # Calculate costs
        orders_per_year = annual_demand / eoq
        cycle_time_days = 365 / orders_per_year
        
        annual_ordering_cost = orders_per_year * ordering_cost
        annual_holding_cost = (eoq / 2) * holding_cost_per_unit
        total_cost = annual_ordering_cost + annual_holding_cost
        
        return EOQResult(
            product_id=product_id,
            eoq=eoq,
            annual_demand=annual_demand,
            ordering_cost=ordering_cost,
            holding_cost=holding_cost_per_unit,
            total_annual_cost=round(total_cost, 2),
            orders_per_year=round(orders_per_year, 2),
            cycle_time_days=round(cycle_time_days, 1)
        )
    
    @staticmethod
    def calculate_with_constraints(annual_demand: float,
                                   ordering_cost: float,
                                   holding_cost_per_unit: float,
                                   min_order: int = 1,
                                   max_order: int = None,
                                   max_capacity: int = None) -> int:
        """Calculate EOQ with min/max constraints."""
        result = EOQCalculator.calculate(annual_demand, ordering_cost, holding_cost_per_unit)
        eoq = result.eoq
        
        # Apply constraints
        eoq = max(min_order, eoq)
        
        if max_order:
            eoq = min(max_order, eoq)
        
        if max_capacity:
            eoq = min(max_capacity, eoq)
        
        return eoq


class SafetyStockCalculator:
    """
    Safety Stock Calculator for various service levels.
    """
    
    # Z-scores for common service levels
    Z_SCORES = {
        0.50: 0.00,
        0.75: 0.67,
        0.80: 0.84,
        0.85: 1.04,
        0.90: 1.28,
        0.95: 1.65,
        0.97: 1.88,
        0.99: 2.33,
        0.999: 3.09
    }
    
    @classmethod
    def get_z_score(cls, service_level: float) -> float:
        """Get Z-score for a service level."""
        if service_level in cls.Z_SCORES:
            return cls.Z_SCORES[service_level]
        
        # Linear interpolation
        levels = sorted(cls.Z_SCORES.keys())
        for i, level in enumerate(levels[:-1]):
            if levels[i] <= service_level < levels[i + 1]:
                ratio = (service_level - levels[i]) / (levels[i + 1] - levels[i])
                z1, z2 = cls.Z_SCORES[levels[i]], cls.Z_SCORES[levels[i + 1]]
                return z1 + ratio * (z2 - z1)
        
        return 1.65  # Default to 95%
    
    @classmethod
    def calculate(cls,
                  daily_demand_std: float,
                  lead_time_days: int,
                  service_level: float = 0.95,
                  product_id: str = "unknown") -> SafetyStockResult:
        """
        Calculate Safety Stock.
        
        SS = Z * σ_d * sqrt(L)
        
        Args:
            daily_demand_std: Standard deviation of daily demand
            lead_time_days: Lead time in days
            service_level: Target service level (0-1)
            product_id: Product identifier
            
        Returns:
            SafetyStockResult
        """
        z = cls.get_z_score(service_level)
        
        # Safety stock formula
        safety_stock = z * daily_demand_std * np.sqrt(lead_time_days)
        safety_stock = max(0, int(np.ceil(safety_stock)))
        
        # Stockout probability
        stockout_prob = 1 - service_level
        
        return SafetyStockResult(
            product_id=product_id,
            safety_stock=safety_stock,
            service_level=service_level,
            z_score=round(z, 3),
            demand_std=daily_demand_std,
            lead_time_days=lead_time_days,
            stockout_probability=round(stockout_prob, 4)
        )
    
    @classmethod
    def calculate_with_lead_time_variability(cls,
                                              daily_demand_avg: float,
                                              daily_demand_std: float,
                                              lead_time_avg: float,
                                              lead_time_std: float,
                                              service_level: float = 0.95) -> int:
        """
        Calculate Safety Stock with variable lead time.
        
        SS = Z * sqrt(L * σ_d² + d² * σ_L²)
        
        Args:
            daily_demand_avg: Average daily demand
            daily_demand_std: Std dev of daily demand
            lead_time_avg: Average lead time (days)
            lead_time_std: Std dev of lead time
            service_level: Target service level
            
        Returns:
            Safety stock quantity
        """
        z = cls.get_z_score(service_level)
        
        # Combined variability formula
        variance = (lead_time_avg * daily_demand_std ** 2 + 
                   daily_demand_avg ** 2 * lead_time_std ** 2)
        
        safety_stock = z * np.sqrt(variance)
        
        return max(0, int(np.ceil(safety_stock)))


class InventoryOptimizer:
    """
    Comprehensive Inventory Optimizer.
    
    Optimizes order quantities considering:
    - Ordering costs
    - Holding costs
    - Stockout costs
    - Service level constraints
    """
    
    def __init__(self, stockout_cost_multiplier: float = 2.0):
        """
        Args:
            stockout_cost_multiplier: Stockout cost as multiple of unit cost
        """
        self.stockout_cost_multiplier = stockout_cost_multiplier
    
    def optimize(self,
                 daily_demand_avg: float,
                 daily_demand_std: float,
                 unit_cost: float,
                 ordering_cost: float,
                 holding_cost_pct: float,
                 lead_time_days: int,
                 target_service_level: float = 0.95,
                 max_capacity: int = None,
                 product_id: str = "unknown") -> OptimizationResult:
        """
        Optimize inventory parameters for a product.
        
        Args:
            daily_demand_avg: Average daily demand
            daily_demand_std: Std dev of daily demand
            unit_cost: Cost per unit
            ordering_cost: Fixed cost per order
            holding_cost_pct: Annual holding cost as % of unit cost
            lead_time_days: Lead time in days
            target_service_level: Target service level (0-1)
            max_capacity: Maximum storage capacity
            product_id: Product identifier
            
        Returns:
            OptimizationResult with optimal parameters
        """
        # Annual values
        annual_demand = daily_demand_avg * 365
        holding_cost_per_unit = unit_cost * holding_cost_pct
        stockout_cost = unit_cost * self.stockout_cost_multiplier
        
        # Calculate EOQ
        eoq_result = EOQCalculator.calculate(
            annual_demand, ordering_cost, holding_cost_per_unit, product_id
        )
        
        # Calculate Safety Stock
        ss_result = SafetyStockCalculator.calculate(
            daily_demand_std, lead_time_days, target_service_level, product_id
        )
        
        # Calculate Reorder Point
        lead_time_demand = daily_demand_avg * lead_time_days
        reorder_point = int(np.ceil(lead_time_demand + ss_result.safety_stock))
        
        # Apply capacity constraint
        optimal_qty = eoq_result.eoq
        if max_capacity:
            optimal_qty = min(optimal_qty, max_capacity)
        
        # Calculate total costs
        orders_per_year = annual_demand / max(1, optimal_qty)
        
        annual_ordering = orders_per_year * ordering_cost
        annual_holding = ((optimal_qty / 2) + ss_result.safety_stock) * holding_cost_per_unit
        annual_stockout = (1 - target_service_level) * annual_demand * stockout_cost
        
        total_cost = annual_ordering + annual_holding + annual_stockout
        
        return OptimizationResult(
            product_id=product_id,
            optimal_order_qty=optimal_qty,
            reorder_point=reorder_point,
            safety_stock=ss_result.safety_stock,
            total_annual_cost=round(total_cost, 2),
            holding_cost=round(annual_holding, 2),
            ordering_cost=round(annual_ordering, 2),
            stockout_cost=round(annual_stockout, 2),
            service_level=target_service_level
        )
    
    def find_optimal_service_level(self,
                                    daily_demand_avg: float,
                                    daily_demand_std: float,
                                    unit_cost: float,
                                    ordering_cost: float,
                                    holding_cost_pct: float,
                                    lead_time_days: int) -> Tuple[float, float]:
        """
        Find the service level that minimizes total cost.
        
        Returns:
            (optimal_service_level, minimum_total_cost)
        """
        def total_cost(service_level):
            result = self.optimize(
                daily_demand_avg, daily_demand_std, unit_cost,
                ordering_cost, holding_cost_pct, lead_time_days,
                target_service_level=service_level
            )
            return result.total_annual_cost
        
        # Search between 80% and 99.9%
        result = minimize_scalar(total_cost, bounds=(0.80, 0.999), method='bounded')
        
        return round(result.x, 3), round(result.fun, 2)


class MultiItemOptimizer:
    """
    Optimizer for multiple items with shared constraints.
    """
    
    @staticmethod
    def optimize_with_budget_constraint(items: List[Dict],
                                         total_budget: float,
                                         target_service_level: float = 0.95) -> List[OptimizationResult]:
        """
        Optimize multiple items subject to total budget constraint.
        
        Uses priority-based allocation based on:
        - Demand value (demand * unit_cost)
        - Criticality
        """
        optimizer = InventoryOptimizer()
        results = []
        
        # Calculate unconstrained optimal for each
        for item in items:
            result = optimizer.optimize(
                item['daily_demand_avg'],
                item['daily_demand_std'],
                item['unit_cost'],
                item['ordering_cost'],
                item['holding_cost_pct'],
                item['lead_time_days'],
                target_service_level,
                product_id=item.get('product_id', 'unknown')
            )
            results.append({
                'result': result,
                'item': item,
                'priority': item['daily_demand_avg'] * item['unit_cost']  # Demand value
            })
        
        # Sort by priority (highest first)
        results.sort(key=lambda x: x['priority'], reverse=True)
        
        # Allocate budget
        remaining_budget = total_budget
        final_results = []
        
        for r in results:
            result = r['result']
            item = r['item']
            
            # Cost of this item's safety stock
            ss_cost = result.safety_stock * item['unit_cost']
            
            if ss_cost <= remaining_budget:
                remaining_budget -= ss_cost
                final_results.append(result)
            else:
                # Reduce service level to fit budget
                reduced_ss = int(remaining_budget / item['unit_cost'])
                result.safety_stock = reduced_ss
                result.reorder_point = int(
                    item['daily_demand_avg'] * item['lead_time_days'] + reduced_ss
                )
                final_results.append(result)
                remaining_budget = 0
        
        return final_results
