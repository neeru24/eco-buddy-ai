"""
Sustainability Analytics & Forecasting Engine - Forecasting Engine
Generates forecasts for sustainability metrics.
"""

import logging
import math
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from analytics.models import (
    ForecastResult, ForecastModel, ConfidenceLevel,
    AnalyticsMetric, HistoricalData
)

logger = logging.getLogger(__name__)


class ForecastingEngine:
    """
    Generates forecasts for sustainability metrics.
    """
    
    def __init__(self):
        """Initialize the forecasting engine."""
        self.forecast_models = {
            'linear': self._linear_forecast,
            'exponential': self._exponential_forecast,
            'moving_average': self._moving_average_forecast,
            'holt_winters': self._holt_winters_forecast,
            'ensemble': self._ensemble_forecast
        }
        logger.info("Forecasting Engine initialized")
    
    def generate_forecast(self,
                         data: List[HistoricalData],
                         metric: AnalyticsMetric,
                         horizon_days: int = 30,
                         model: ForecastModel = ForecastModel.ENSEMBLE,
                         confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM) -> ForecastResult:
        """
        Generate forecast for a metric.
        
        Args:
            data: Historical data
            metric: Metric to forecast
            horizon_days: Forecast horizon in days
            model: Forecasting model
            confidence_level: Confidence level
        
        Returns:
            ForecastResult: Forecast results
        """
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        if len(metric_data) < 5:
            return ForecastResult(
                user_id=data[0].user_id if data else "",
                metric=metric,
                model=model,
                data_points_used=len(metric_data),
                is_reliable=False,
                notes="Insufficient data for forecasting (need at least 5 points)"
            )
        
        # Sort by timestamp
        sorted_data = sorted(metric_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        dates = [d.timestamp for d in sorted_data]
        
        # Convert dates to numeric values
        base_date = dates[0]
        x = [(d - base_date).days for d in dates]
        
        # Generate forecast
        forecast_values = []
        confidence_intervals = []
        
        # Get forecast function
        forecast_func = self.forecast_models.get(model.value, self._ensemble_forecast)
        
        # Generate forecasts
        for i in range(1, horizon_days + 1):
            pred_x = x[-1] + i
            pred_value = forecast_func(x, values, pred_x, model)
            forecast_values.append(pred_value)
            
            # Calculate confidence interval
            ci = self._calculate_confidence_interval(values, confidence_level)
            confidence_intervals.append(ci)
        
        # Create forecast result
        result = ForecastResult(
            user_id=sorted_data[0].user_id,
            metric=metric,
            model=model,
            forecast_date=datetime.now(),
            horizon_days=horizon_days,
            projected_values=forecast_values,
            confidence_intervals=confidence_intervals,
            confidence_level=confidence_level,
            data_points_used=len(values)
        )
        
        # Calculate statistics
        result.mean_forecast = statistics.mean(forecast_values) if forecast_values else 0
        result.median_forecast = statistics.median(forecast_values) if forecast_values else 0
        
        # Calculate scenarios
        result.best_case = max(forecast_values) if forecast_values else 0
        result.current_trend = forecast_values[-1] if forecast_values else 0
        result.worst_case = min(forecast_values) if forecast_values else 0
        
        # Calculate model accuracy
        result.model_accuracy, result.mape, result.rmse = self._calculate_model_accuracy(
            values, forecast_values
        )
        
        # Determine reliability
        result.is_reliable = len(values) >= 15 and result.model_accuracy > 0.5
        
        return result
    
    def _linear_forecast(self, x: List[float], y: List[float], pred_x: float, model: ForecastModel) -> float:
        """
        Linear regression forecast.
        """
        n = len(x)
        if n < 2:
            return y[-1] if y else 0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y[-1] if y else 0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        return max(0, slope * pred_x + intercept)
    
    def _exponential_forecast(self, x: List[float], y: List[float], pred_x: float, model: ForecastModel) -> float:
        """
        Exponential forecast.
        """
        if any(v <= 0 for v in y):
            return self._linear_forecast(x, y, pred_x, model)
        
        n = len(x)
        if n < 2:
            return y[-1] if y else 0
        
        # Transform to log space
        log_y = [math.log(v) for v in y]
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(log_y)
        
        numerator = sum((x[i] - x_mean) * (log_y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return y[-1] if y else 0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        pred_log = slope * pred_x + intercept
        return max(0, math.exp(pred_log))
    
    def _moving_average_forecast(self, x: List[float], y: List[float], pred_x: float, model: ForecastModel) -> float:
        """
        Moving average forecast.
        """
        window = min(7, len(y))
        if window < 2:
            return y[-1] if y else 0
        
        recent = y[-window:]
        return statistics.mean(recent)
    
    def _holt_winters_forecast(self, x: List[float], y: List[float], pred_x: float, model: ForecastModel) -> float:
        """
        Holt-Winters exponential smoothing forecast.
        """
        # Simplified Holt-Winters with only level and trend
        n = len(y)
        if n < 4:
            return self._linear_forecast(x, y, pred_x, model)
        
        # Alpha (level smoothing) and beta (trend smoothing)
        alpha = 0.3
        beta = 0.1
        
        # Initialize level and trend
        level = y[0]
        trend = (y[1] - y[0]) if n > 1 else 0
        
        # Smooth
        for i in range(1, n):
            level = alpha * y[i] + (1 - alpha) * (level + trend)
            trend = beta * (level - y[i-1]) + (1 - beta) * trend
        
        # Forecast
        steps = pred_x - x[-1]
        return max(0, level + steps * trend)
    
    def _ensemble_forecast(self, x: List[float], y: List[float], pred_x: float, model: ForecastModel) -> float:
        """
        Ensemble forecast combining multiple models.
        """
        predictions = []
        
        # Linear
        pred1 = self._linear_forecast(x, y, pred_x, model)
        predictions.append(pred1)
        
        # Exponential (if applicable)
        if all(v > 0 for v in y):
            pred2 = self._exponential_forecast(x, y, pred_x, model)
            predictions.append(pred2)
        
        # Moving average
        pred3 = self._moving_average_forecast(x, y, pred_x, model)
        predictions.append(pred3)
        
        # Holt-Winters
        if len(y) >= 4:
            pred4 = self._holt_winters_forecast(x, y, pred_x, model)
            predictions.append(pred4)
        
        # Average predictions
        return statistics.mean(predictions) if predictions else y[-1] if y else 0
    
    def _calculate_confidence_interval(self, values: List[float], confidence_level: ConfidenceLevel) -> Tuple[float, float]:
        """
        Calculate confidence interval for forecast.
        """
        if len(values) < 2:
            return (0, 0)
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        # Z-scores for confidence levels
        z_scores = {
            ConfidenceLevel.HIGH: 1.96,      # 95%
            ConfidenceLevel.MEDIUM: 1.28,    # 80%
            ConfidenceLevel.LOW: 0.84,       # 60%
            ConfidenceLevel.VERY_LOW: 0.52   # 40%
        }
        
        z_score = z_scores.get(confidence_level, 1.28)
        margin = z_score * std_dev / math.sqrt(len(values))
        
        return (mean - margin, mean + margin)
    
    def _calculate_model_accuracy(self, historical: List[float], forecast: List[float]) -> Tuple[float, float, float]:
        """
        Calculate model accuracy metrics.
        """
        if len(forecast) < 2:
            return 0, 0, 0
        
        # Use last N historical points for validation
        n = min(len(historical), len(forecast))
        if n < 2:
            return 0, 0, 0
        
        actual = historical[-n:]
        predicted = forecast[:n]
        
        # Calculate MAPE
        mape = 0
        for i in range(n):
            if actual[i] > 0:
                mape += abs((actual[i] - predicted[i]) / actual[i])
        
        mape = (mape / n) * 100 if n > 0 else 0
        
        # Calculate RMSE
        rmse = math.sqrt(sum((actual[i] - predicted[i]) ** 2 for i in range(n)) / n) if n > 0 else 0
        
        # Calculate accuracy (1 - MAPE/100)
        accuracy = max(0, 1 - mape / 100)
        
        return accuracy, mape, rmse
    
    def get_forecast_summary(self, forecast: ForecastResult) -> Dict[str, Any]:
        """
        Get summary of forecast results.
        
        Args:
            forecast: Forecast result
        
        Returns:
            Dict: Forecast summary
        """
        return {
            'metric': forecast.metric.value,
            'model': forecast.model.value,
            'horizon_days': forecast.horizon_days,
            'mean_forecast': forecast.mean_forecast,
            'median_forecast': forecast.median_forecast,
            'best_case': forecast.best_case,
            'current_trend': forecast.current_trend,
            'worst_case': forecast.worst_case,
            'confidence_level': forecast.confidence_level.value,
            'model_accuracy': forecast.model_accuracy,
            'mape': forecast.mape,
            'rmse': forecast.rmse,
            'is_reliable': forecast.is_reliable,
            'data_points_used': forecast.data_points_used,
            'forecast_values': forecast.projected_values,
            'confidence_intervals': forecast.confidence_intervals
        }
    
    def get_goal_completion_forecast(self,
                                    current_value: float,
                                    target_value: float,
                                    historical_data: List[HistoricalData],
                                    days_remaining: int) -> Dict[str, Any]:
        """
        Forecast goal completion.
        
        Args:
            current_value: Current value
            target_value: Target value
            historical_data: Historical data
            days_remaining: Days remaining
        
        Returns:
            Dict: Completion forecast
        """
        if not historical_data:
            return {
                'estimated_completion': None,
                'probability': 0,
                'requires_daily_rate': 0,
                'current_daily_rate': 0
            }
        
        # Calculate current daily rate
        sorted_data = sorted(historical_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        
        if len(values) < 2:
            return {
                'estimated_completion': None,
                'probability': 0,
                'requires_daily_rate': 0,
                'current_daily_rate': 0
            }
        
        # Calculate daily rate
        first_value = values[0]
        last_value = values[-1]
        days_elapsed = (sorted_data[-1].timestamp - sorted_data[0].timestamp).days
        
        if days_elapsed == 0:
            daily_rate = 0
        else:
            daily_rate = (last_value - first_value) / days_elapsed
        
        # Calculate required daily rate to reach target
        remaining = target_value - current_value
        required_daily_rate = remaining / days_remaining if days_remaining > 0 else 0
        
        # Estimate completion date
        if daily_rate > 0:
            days_needed = remaining / daily_rate
            estimated_completion = datetime.now() + timedelta(days=days_needed)
        else:
            estimated_completion = None
        
        # Calculate probability
        if required_daily_rate > 0 and daily_rate > 0:
            probability = min(100, (daily_rate / required_daily_rate) * 100)
        elif required_daily_rate <= 0:
            probability = 100 if current_value >= target_value else 50
        else:
            probability = 0
        
        return {
            'estimated_completion': estimated_completion.isoformat() if estimated_completion else None,
            'probability': probability,
            'requires_daily_rate': required_daily_rate,
            'current_daily_rate': daily_rate,
            'days_remaining': days_remaining,
            'target_value': target_value,
            'current_value': current_value
        }
    
    def get_forecast_confidence(self, forecast: ForecastResult) -> str:
        """
        Get confidence description for a forecast.
        
        Args:
            forecast: Forecast result
        
        Returns:
            str: Confidence description
        """
        if not forecast.is_reliable:
            return "Low confidence - insufficient data"
        
        if forecast.model_accuracy > 0.8:
            return "High confidence - model is performing well"
        elif forecast.model_accuracy > 0.6:
            return "Medium confidence - model is performing adequately"
        else:
            return "Low confidence - model performance needs improvement"