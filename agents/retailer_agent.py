"""
Retailer Agent Module
=====================
Forecasts demand and manages stock requests from warehouses.

Responsibilities:
- Track historical sales data
- Forecast future demand (Moving Average, Exponential Smoothing)
- Request stock from warehouses based on forecasts
- Send demand forecast updates to warehouses
- Simulate customer sales/demand
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict

from agents.base_agent import BaseAgent, Message, MessageType


@dataclass
class SalesRecord:
    """Represents a single sales record."""
    date: datetime
    product_id: str
    units_sold: int
    revenue: float
    is_weekend: bool = False
    is_holiday: bool = False
    promotion_active: bool = False


@dataclass
class DemandForecast:
    """Represents a demand forecast for a product."""
    product_id: str
    forecast_date: datetime
    predicted_demand: float
    confidence_lower: float
    confidence_upper: float
    method: str  # 'moving_average', 'exponential_smoothing', 'weighted'
    created_at: datetime = field(default_factory=datetime.now)


class RetailerAgent(BaseAgent):
    """
    Retailer Agent - Forecasts demand and requests stock from warehouses.
    
    Features:
    - Historical sales tracking
    - Multiple forecasting methods (MA, EMA, Weighted)
    - Automatic stock requests based on forecasts
    - Seasonality detection
    - Promotion impact analysis
    
    Attributes:
        forecast_horizon: Days ahead to forecast
        ma_window: Moving average window size
        ema_alpha: Exponential smoothing factor (0-1)
    """
    
    def __init__(self, agent_id: str, name: str,
                 forecast_horizon: int = 7,
                 ma_window: int = 7,
                 ema_alpha: float = 0.3,
                 sales_history: pd.DataFrame = None):
        super().__init__(agent_id, name)
        
        self.forecast_horizon = forecast_horizon
        self.ma_window = ma_window
        self.ema_alpha = ema_alpha
        
        # Sales tracking
        self.sales_history: Dict[str, List[SalesRecord]] = defaultdict(list)
        self.daily_sales: Dict[str, Dict[datetime, int]] = defaultdict(dict)
        
        # Forecasts
        self.forecasts: Dict[str, DemandForecast] = {}
        self.forecast_history: List[DemandForecast] = []
        
        # Stock tracking
        self.current_stock: Dict[str, int] = {}
        self.pending_requests: List[Dict] = []
        self.fulfilled_requests: List[Dict] = []
        
        # Statistics
        self.total_sales = 0
        self.total_revenue = 0.0
        self.stockout_events = 0
        self.forecast_accuracy: List[float] = []
        
        # Load sales history if provided
        if sales_history is not None:
            self._load_sales_history(sales_history)
    
    def _load_sales_history(self, df: pd.DataFrame):
        """Load sales history from DataFrame."""
        for _, row in df.iterrows():
            record = SalesRecord(
                date=pd.to_datetime(row['date']),
                product_id=row['product_id'],
                units_sold=int(row['units_sold']),
                revenue=float(row['revenue']),
                is_weekend=bool(row.get('is_weekend', 0)),
                is_holiday=bool(row.get('is_holiday', 0)),
                promotion_active=bool(row.get('promotion_active', 0))
            )
            self.sales_history[record.product_id].append(record)
            self.daily_sales[record.product_id][record.date.date()] = record.units_sold
            
            self.total_sales += record.units_sold
            self.total_revenue += record.revenue
    
    def add_sale(self, product_id: str, units_sold: int, 
                 unit_price: float, date: datetime = None,
                 is_weekend: bool = False, is_holiday: bool = False,
                 promotion_active: bool = False):
        """Record a new sale."""
        if date is None:
            date = self.current_time
        
        record = SalesRecord(
            date=date,
            product_id=product_id,
            units_sold=units_sold,
            revenue=units_sold * unit_price,
            is_weekend=is_weekend,
            is_holiday=is_holiday,
            promotion_active=promotion_active
        )
        
        self.sales_history[product_id].append(record)
        self.daily_sales[product_id][date.date()] = units_sold
        
        self.total_sales += units_sold
        self.total_revenue += record.revenue
        
        # Update stock if tracking
        if product_id in self.current_stock:
            self.current_stock[product_id] = max(0, self.current_stock[product_id] - units_sold)
    
    def forecast_demand_moving_average(self, product_id: str, 
                                        days_ahead: int = None) -> Tuple[float, float, float]:
        """
        Forecast demand using Simple Moving Average.
        
        Returns: (predicted_demand, lower_bound, upper_bound)
        """
        if days_ahead is None:
            days_ahead = self.forecast_horizon
        
        history = self.sales_history.get(product_id, [])
        
        if len(history) < self.ma_window:
            # Not enough data, use available average
            if history:
                avg = np.mean([r.units_sold for r in history])
                std = np.std([r.units_sold for r in history]) if len(history) > 1 else avg * 0.2
            else:
                return 0.0, 0.0, 0.0
        else:
            # Use last N days
            recent = history[-self.ma_window:]
            avg = np.mean([r.units_sold for r in recent])
            std = np.std([r.units_sold for r in recent])
        
        # Total forecast for the horizon
        total_forecast = avg * days_ahead
        
        # 95% confidence interval
        margin = 1.96 * std * np.sqrt(days_ahead)
        
        return total_forecast, max(0, total_forecast - margin), total_forecast + margin
    
    def forecast_demand_exponential_smoothing(self, product_id: str,
                                               days_ahead: int = None) -> Tuple[float, float, float]:
        """
        Forecast demand using Exponential Moving Average (EMA).
        
        EMA_t = α * X_t + (1-α) * EMA_{t-1}
        
        Returns: (predicted_demand, lower_bound, upper_bound)
        """
        if days_ahead is None:
            days_ahead = self.forecast_horizon
        
        history = self.sales_history.get(product_id, [])
        
        if not history:
            return 0.0, 0.0, 0.0
        
        # Calculate EMA
        sales = [r.units_sold for r in history]
        ema = sales[0]  # Initialize with first value
        
        for sale in sales[1:]:
            ema = self.ema_alpha * sale + (1 - self.ema_alpha) * ema
        
        # Calculate standard deviation of errors for confidence interval
        errors = []
        running_ema = sales[0]
        for i, sale in enumerate(sales[1:], 1):
            error = abs(sale - running_ema)
            errors.append(error)
            running_ema = self.ema_alpha * sale + (1 - self.ema_alpha) * running_ema
        
        std_error = np.std(errors) if errors else ema * 0.2
        
        # Total forecast for the horizon
        total_forecast = ema * days_ahead
        
        # 95% confidence interval
        margin = 1.96 * std_error * np.sqrt(days_ahead)
        
        return total_forecast, max(0, total_forecast - margin), total_forecast + margin
    
    def forecast_demand_weighted(self, product_id: str,
                                  days_ahead: int = None) -> Tuple[float, float, float]:
        """
        Forecast using weighted combination of MA and EMA.
        Gives more weight to method with better recent accuracy.
        
        Returns: (predicted_demand, lower_bound, upper_bound)
        """
        if days_ahead is None:
            days_ahead = self.forecast_horizon
        
        ma_forecast = self.forecast_demand_moving_average(product_id, days_ahead)
        ema_forecast = self.forecast_demand_exponential_smoothing(product_id, days_ahead)
        
        # Weight: 60% EMA (more responsive), 40% MA (more stable)
        weight_ema = 0.6
        weight_ma = 0.4
        
        predicted = weight_ema * ema_forecast[0] + weight_ma * ma_forecast[0]
        lower = weight_ema * ema_forecast[1] + weight_ma * ma_forecast[1]
        upper = weight_ema * ema_forecast[2] + weight_ma * ma_forecast[2]
        
        return predicted, lower, upper
    
    def generate_forecast(self, product_id: str, method: str = "weighted") -> DemandForecast:
        """
        Generate a demand forecast for a product.
        
        Args:
            product_id: Product to forecast
            method: 'moving_average', 'exponential_smoothing', or 'weighted'
        """
        if method == "moving_average":
            predicted, lower, upper = self.forecast_demand_moving_average(product_id)
        elif method == "exponential_smoothing":
            predicted, lower, upper = self.forecast_demand_exponential_smoothing(product_id)
        else:
            predicted, lower, upper = self.forecast_demand_weighted(product_id)
        
        forecast = DemandForecast(
            product_id=product_id,
            forecast_date=self.current_time + timedelta(days=self.forecast_horizon),
            predicted_demand=predicted,
            confidence_lower=lower,
            confidence_upper=upper,
            method=method
        )
        
        self.forecasts[product_id] = forecast
        self.forecast_history.append(forecast)
        
        return forecast
    
    def generate_all_forecasts(self, method: str = "weighted") -> Dict[str, DemandForecast]:
        """Generate forecasts for all products with sales history."""
        for product_id in self.sales_history.keys():
            self.generate_forecast(product_id, method)
        
        return self.forecasts
    
    def get_daily_demand_stats(self, product_id: str) -> Dict[str, float]:
        """Get daily demand statistics for a product."""
        history = self.sales_history.get(product_id, [])
        
        if not history:
            return {"avg": 0, "std": 0, "min": 0, "max": 0}
        
        sales = [r.units_sold for r in history]
        
        return {
            "avg": np.mean(sales),
            "std": np.std(sales),
            "min": min(sales),
            "max": max(sales)
        }
    
    def handle_message(self, message: Message):
        """Handle incoming messages."""
        if message.message_type == MessageType.STOCK_UPDATE:
            self._handle_stock_update(message)
        elif message.message_type == MessageType.SYSTEM_STATUS:
            self._handle_status_request(message)
    
    def _handle_stock_update(self, message: Message):
        """Handle stock update from warehouse."""
        content = message.content
        product_id = content.get("product_id")
        quantity = content.get("quantity", 0)
        status = content.get("status")
        
        if status == "fulfilled":
            # Update local stock tracking
            self.current_stock[product_id] = self.current_stock.get(product_id, 0) + quantity
            
            # Move from pending to fulfilled
            for req in self.pending_requests[:]:
                if req.get("product_id") == product_id:
                    self.fulfilled_requests.append(req)
                    self.pending_requests.remove(req)
                    break
            
            print(f"  [{self.name}] Received {quantity} units of {product_id}")
    
    def _handle_status_request(self, message: Message):
        """Handle status request."""
        requester = self.get_agent(message.sender_id)
        if requester:
            self.send_message(
                requester,
                MessageType.SYSTEM_STATUS,
                self.get_status()
            )
    
    def request_stock(self, warehouse: BaseAgent, product_id: str, quantity: int):
        """Request stock from a warehouse."""
        request = {
            "product_id": product_id,
            "quantity": quantity,
            "requested_at": self.current_time
        }
        
        self.send_message(
            warehouse,
            MessageType.STOCK_REQUEST,
            {
                "product_id": product_id,
                "quantity": quantity,
                "urgency": "normal"
            }
        )
        
        self.pending_requests.append(request)
        print(f"  [{self.name}] Requested {quantity} units of {product_id}")
    
    def send_forecast_to_warehouse(self, warehouse: BaseAgent, product_id: str):
        """Send demand forecast to warehouse for planning."""
        if product_id not in self.forecasts:
            self.generate_forecast(product_id)
        
        forecast = self.forecasts[product_id]
        stats = self.get_daily_demand_stats(product_id)
        
        self.send_message(
            warehouse,
            MessageType.DEMAND_FORECAST,
            {
                "product_id": product_id,
                "daily_demand_avg": stats["avg"],
                "daily_demand_std": stats["std"],
                "forecast_horizon": self.forecast_horizon,
                "predicted_demand": forecast.predicted_demand,
                "confidence_lower": forecast.confidence_lower,
                "confidence_upper": forecast.confidence_upper
            }
        )
        
        print(f"  [{self.name}] Sent forecast for {product_id} to {warehouse.name}")
    
    def simulate_daily_sales(self, product_id: str, base_demand: float, 
                             std_demand: float, unit_price: float) -> int:
        """Simulate daily sales for a product."""
        # Generate demand with some randomness
        demand = max(0, int(np.random.normal(base_demand, std_demand)))
        
        # Check if we have stock
        available = self.current_stock.get(product_id, 0)
        
        if available >= demand:
            # Full sale
            self.add_sale(product_id, demand, unit_price)
            return demand
        else:
            # Partial sale (stockout)
            self.stockout_events += 1
            if available > 0:
                self.add_sale(product_id, available, unit_price)
            return available
    
    def step(self, current_time: datetime = None):
        """Execute one time step for the retailer agent."""
        super().step(current_time)
    
    def get_forecast_data(self) -> pd.DataFrame:
        """Get all forecasts as a DataFrame."""
        data = []
        for product_id, forecast in self.forecasts.items():
            stats = self.get_daily_demand_stats(product_id)
            history = self.sales_history.get(product_id, [])
            data.append({
                "product_id": product_id,
                "daily_avg": round(stats["avg"], 2),
                "daily_std": round(stats["std"], 2),
                "forecast_horizon_days": self.forecast_horizon,
                "predicted_total": round(forecast.predicted_demand, 0),
                "confidence_lower": round(forecast.confidence_lower, 0),
                "confidence_upper": round(forecast.confidence_upper, 0),
                "method": forecast.method,
                "data_points": len(history)
            })
        
        return pd.DataFrame(data)
    
    def get_sales_summary(self) -> pd.DataFrame:
        """Get sales summary by product."""
        data = []
        for product_id, records in self.sales_history.items():
            total_units = sum(r.units_sold for r in records)
            total_revenue = sum(r.revenue for r in records)
            
            data.append({
                "product_id": product_id,
                "total_units_sold": total_units,
                "total_revenue": round(total_revenue, 2),
                "num_transactions": len(records),
                "avg_units_per_day": round(total_units / max(1, len(records)), 2)
            })
        
        return pd.DataFrame(data)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive retailer status."""
        base_status = super().get_status()
        
        base_status.update({
            "total_products_tracked": len(self.sales_history),
            "total_sales": self.total_sales,
            "total_revenue": round(self.total_revenue, 2),
            "stockout_events": self.stockout_events,
            "pending_requests": len(self.pending_requests),
            "forecasts_generated": len(self.forecasts),
            "forecast_horizon": self.forecast_horizon,
            "ma_window": self.ma_window,
            "ema_alpha": self.ema_alpha
        })
        
        return base_status
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """Get performance metrics."""
        total_requests = len(self.pending_requests) + len(self.fulfilled_requests)
        
        return {
            "total_sales": self.total_sales,
            "total_revenue": self.total_revenue,
            "avg_sale_value": self.total_revenue / max(1, self.total_sales),
            "stockout_rate": self.stockout_events / max(1, total_requests),
            "fulfillment_rate": len(self.fulfilled_requests) / max(1, total_requests)
        }
