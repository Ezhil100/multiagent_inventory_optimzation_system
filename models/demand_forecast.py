"""
Demand Forecasting Models
=========================
Advanced forecasting methods for inventory demand prediction.

Methods:
- Simple Moving Average (SMA)
- Exponential Moving Average (EMA)
- Weighted Moving Average (WMA)
- Double Exponential Smoothing (Holt's Method)
- Seasonal Decomposition
"""

import numpy as np
import pandas as pd
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class ForecastResult:
    """Result of a demand forecast."""
    product_id: str
    method: str
    horizon_days: int
    daily_forecast: float
    total_forecast: float
    confidence_lower: float
    confidence_upper: float
    confidence_level: float
    mae: Optional[float] = None  # Mean Absolute Error
    mape: Optional[float] = None  # Mean Absolute Percentage Error
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


class DemandForecaster:
    """
    Advanced demand forecasting with multiple methods.
    
    Provides various forecasting algorithms with accuracy metrics.
    """
    
    def __init__(self, confidence_level: float = 0.95):
        self.confidence_level = confidence_level
        self.z_score = self._get_z_score(confidence_level)
    
    def _get_z_score(self, confidence: float) -> float:
        """Get Z-score for confidence level."""
        z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
        return z_scores.get(confidence, 1.96)
    
    def simple_moving_average(self, data: List[float], window: int = 7) -> Tuple[float, float]:
        """
        Simple Moving Average forecast.
        
        Args:
            data: Historical demand data
            window: Number of periods to average
            
        Returns:
            (forecast, std_dev)
        """
        if len(data) < window:
            window = len(data)
        
        if not data:
            return 0.0, 0.0
        
        recent = data[-window:]
        forecast = np.mean(recent)
        std_dev = np.std(recent) if len(recent) > 1 else forecast * 0.2
        
        return float(forecast), float(std_dev)
    
    def exponential_moving_average(self, data: List[float], alpha: float = 0.3) -> Tuple[float, float]:
        """
        Exponential Moving Average (EMA) forecast.
        
        EMA_t = α * X_t + (1-α) * EMA_{t-1}
        
        Args:
            data: Historical demand data
            alpha: Smoothing factor (0 < α < 1), higher = more weight on recent
            
        Returns:
            (forecast, std_dev)
        """
        if not data:
            return 0.0, 0.0
        
        ema = data[0]
        errors = []
        
        for i, value in enumerate(data[1:], 1):
            error = abs(value - ema)
            errors.append(error)
            ema = alpha * value + (1 - alpha) * ema
        
        std_dev = np.std(errors) if errors else ema * 0.2
        
        return float(ema), float(std_dev)
    
    def weighted_moving_average(self, data: List[float], weights: List[float] = None) -> Tuple[float, float]:
        """
        Weighted Moving Average with custom weights.
        
        Args:
            data: Historical demand data
            weights: Custom weights (default: linear increasing)
            
        Returns:
            (forecast, std_dev)
        """
        if not data:
            return 0.0, 0.0
        
        n = min(len(data), 7)
        recent = data[-n:]
        
        if weights is None:
            # Linear increasing weights: [1, 2, 3, ..., n]
            weights = list(range(1, n + 1))
        
        weights = weights[-n:]
        total_weight = sum(weights)
        
        forecast = sum(w * v for w, v in zip(weights, recent)) / total_weight
        
        # Calculate weighted std dev
        mean = forecast
        variance = sum(w * (v - mean) ** 2 for w, v in zip(weights, recent)) / total_weight
        std_dev = np.sqrt(variance)
        
        return float(forecast), float(std_dev)
    
    def double_exponential_smoothing(self, data: List[float], 
                                      alpha: float = 0.3, 
                                      beta: float = 0.1) -> Tuple[float, float, float]:
        """
        Double Exponential Smoothing (Holt's Method) for data with trend.
        
        Args:
            data: Historical demand data
            alpha: Level smoothing factor
            beta: Trend smoothing factor
            
        Returns:
            (forecast, trend, std_dev)
        """
        if len(data) < 2:
            return (data[0] if data else 0.0), 0.0, 0.0
        
        # Initialize
        level = data[0]
        trend = data[1] - data[0]
        errors = []
        
        for i, value in enumerate(data[1:], 1):
            last_level = level
            
            # Update level
            level = alpha * value + (1 - alpha) * (last_level + trend)
            
            # Update trend
            trend = beta * (level - last_level) + (1 - beta) * trend
            
            # Track error
            forecast = last_level + trend
            errors.append(abs(value - forecast))
        
        # Forecast is level + trend
        forecast = level + trend
        std_dev = np.std(errors) if errors else abs(forecast) * 0.2
        
        return float(forecast), float(trend), float(std_dev)
    
    def seasonal_naive(self, data: List[float], season_length: int = 7) -> Tuple[float, float]:
        """
        Seasonal Naive forecast - uses same day from previous period.
        
        Args:
            data: Historical demand data
            season_length: Length of seasonal cycle (7 for weekly)
            
        Returns:
            (forecast, std_dev)
        """
        if len(data) < season_length:
            return self.simple_moving_average(data)
        
        # Get all values from same seasonal position
        seasonal_values = data[-season_length::season_length]
        
        if seasonal_values:
            forecast = seasonal_values[-1]
            std_dev = np.std(seasonal_values) if len(seasonal_values) > 1 else forecast * 0.2
            return float(forecast), float(std_dev)
        
        return self.simple_moving_average(data)
    
    def forecast(self, data: List[float], 
                 method: str = "ema",
                 horizon: int = 7,
                 product_id: str = "unknown",
                 **kwargs) -> ForecastResult:
        """
        Generate forecast using specified method.
        
        Args:
            data: Historical demand data
            method: Forecasting method ('sma', 'ema', 'wma', 'holt', 'seasonal')
            horizon: Days to forecast ahead
            product_id: Product identifier
            **kwargs: Method-specific parameters
            
        Returns:
            ForecastResult object
        """
        if method == "sma":
            daily, std = self.simple_moving_average(data, kwargs.get("window", 7))
        elif method == "ema":
            daily, std = self.exponential_moving_average(data, kwargs.get("alpha", 0.3))
        elif method == "wma":
            daily, std = self.weighted_moving_average(data, kwargs.get("weights"))
        elif method == "holt":
            daily, trend, std = self.double_exponential_smoothing(
                data, kwargs.get("alpha", 0.3), kwargs.get("beta", 0.1)
            )
        elif method == "seasonal":
            daily, std = self.seasonal_naive(data, kwargs.get("season_length", 7))
        else:
            # Default to EMA
            daily, std = self.exponential_moving_average(data)
        
        total = daily * horizon
        margin = self.z_score * std * np.sqrt(horizon)
        
        # Calculate accuracy metrics if enough data
        mae, mape = self._calculate_accuracy(data, method, **kwargs)
        
        return ForecastResult(
            product_id=product_id,
            method=method,
            horizon_days=horizon,
            daily_forecast=round(daily, 2),
            total_forecast=round(total, 2),
            confidence_lower=round(max(0, total - margin), 2),
            confidence_upper=round(total + margin, 2),
            confidence_level=self.confidence_level,
            mae=mae,
            mape=mape
        )
    
    def _calculate_accuracy(self, data: List[float], method: str, **kwargs) -> Tuple[Optional[float], Optional[float]]:
        """Calculate MAE and MAPE using walk-forward validation."""
        if len(data) < 10:
            return None, None
        
        errors = []
        pct_errors = []
        
        # Walk-forward validation (last 30% of data)
        split = int(len(data) * 0.7)
        
        for i in range(split, len(data)):
            train = data[:i]
            actual = data[i]
            
            if method == "sma":
                pred, _ = self.simple_moving_average(train, kwargs.get("window", 7))
            elif method == "ema":
                pred, _ = self.exponential_moving_average(train, kwargs.get("alpha", 0.3))
            else:
                pred, _ = self.exponential_moving_average(train)
            
            errors.append(abs(actual - pred))
            if actual > 0:
                pct_errors.append(abs(actual - pred) / actual * 100)
        
        mae = np.mean(errors) if errors else None
        mape = np.mean(pct_errors) if pct_errors else None
        
        return (round(mae, 2) if mae else None, 
                round(mape, 2) if mape else None)
    
    def ensemble_forecast(self, data: List[float],
                          horizon: int = 7,
                          product_id: str = "unknown") -> ForecastResult:
        """
        Ensemble forecast combining multiple methods.
        
        Weights methods by their inverse error (better methods get more weight).
        """
        methods = ["sma", "ema", "wma"]
        forecasts = []
        weights = []
        
        for method in methods:
            result = self.forecast(data, method, horizon, product_id)
            forecasts.append(result)
            
            # Weight by inverse MAE (or equal if no MAE)
            if result.mae and result.mae > 0:
                weights.append(1 / result.mae)
            else:
                weights.append(1.0)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Weighted average
        daily = sum(w * f.daily_forecast for w, f in zip(weights, forecasts))
        total = sum(w * f.total_forecast for w, f in zip(weights, forecasts))
        lower = sum(w * f.confidence_lower for w, f in zip(weights, forecasts))
        upper = sum(w * f.confidence_upper for w, f in zip(weights, forecasts))
        
        return ForecastResult(
            product_id=product_id,
            method="ensemble",
            horizon_days=horizon,
            daily_forecast=round(daily, 2),
            total_forecast=round(total, 2),
            confidence_lower=round(lower, 2),
            confidence_upper=round(upper, 2),
            confidence_level=self.confidence_level
        )
