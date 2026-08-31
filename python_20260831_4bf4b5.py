"""
Sustainability Analytics & Forecasting Engine - Trend Analyzer
Analyzes trends in sustainability data.
"""

import logging
import statistics
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from analytics.models import (
    TrendAnalysis, TrendType, AnalyticsMetric, AnalyticsPeriod,
    DataGranularity, HistoricalData
)

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Analyzes trends in sustainability data.
    """
    
    def __init__(self):
        """Initialize the trend analyzer."""
        self.seasonality_periods = {
            'daily': 7,    # Weekly seasonality
            'weekly': 4,   # Monthly seasonality
            'monthly': 12,  # Yearly seasonality
            'quarterly': 4  # Yearly seasonality
        }
        logger.info("Trend Analyzer initialized")
    
    def analyze_trend(self,
                     data: List[HistoricalData],
                     metric: AnalyticsMetric,
                     period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY,
                     granularity: DataGranularity = DataGranularity.DAILY) -> TrendAnalysis:
        """
        Analyze trend for a specific metric.
        
        Args:
            data: Historical data
            metric: Metric to analyze
            period: Analysis period
            granularity: Data granularity
        
        Returns:
            TrendAnalysis: Trend analysis results
        """
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        if len(metric_data) < 3:
            return TrendAnalysis(
                user_id=data[0].user_id if data else "",
                metric=metric,
                period=period,
                data_points=len(metric_data),
                notes="Insufficient data for trend analysis"
            )
        
        # Sort by timestamp
        sorted_data = sorted(metric_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        dates = [d.timestamp for d in sorted_data]
        
        # Create trend analysis
        trend = TrendAnalysis(
            user_id=sorted_data[0].user_id,
            metric=metric,
            period=period,
            start_date=dates[0],
            end_date=dates[-1],
            values=values,
            dates=[d.isoformat() for d in dates],
            granularity=granularity,
            data_points=len(values)
        )
        
        # Calculate statistics
        trend.mean = statistics.mean(values)
        trend.median = statistics.median(values)
        trend.variance = statistics.variance(values) if len(values) > 1 else 0
        trend.std_dev = statistics.stdev(values) if len(values) > 1 else 0
        trend.min_value = min(values)
        trend.max_value = max(values)
        
        # Calculate linear regression
        slope, intercept, r_squared, p_value = self._linear_regression(dates, values)
        trend.slope = slope
        trend.intercept = intercept
        trend.r_squared = r_squared
        trend.p_value = p_value
        
        # Determine trend type
        trend.trend_type = self._determine_trend_type(values, slope, r_squared)
        
        # Detect seasonality
        seasonality = self._detect_seasonality(values, period)
        if seasonality:
            trend.has_seasonality = True
            trend.seasonality_period = seasonality['period']
            trend.seasonality_strength = seasonality['strength']
        
        # Calculate changes
        if len(values) >= 2:
            trend.absolute_change = values[-1] - values[0]
            trend.percentage_change = (trend.absolute_change / (values[0] + 0.001)) * 100 if values[0] > 0 else 0
            
            # Calculate rates
            days_span = (dates[-1] - dates[0]).days
            if days_span > 0:
                trend.daily_rate = trend.absolute_change / days_span
                trend.monthly_rate = trend.daily_rate * 30
        
        # Calculate moving averages
        trend.moving_average_7 = self._calculate_moving_average(values, 7)
        trend.moving_average_30 = self._calculate_moving_average(values, 30)
        trend.moving_average_90 = self._calculate_moving_average(values, 90)
        
        # Calculate confidence
        trend.confidence = self._calculate_confidence(values, r_squared, len(values))
        
        return trend
    
    def _linear_regression(self, dates: List[datetime], values: List[float]) -> Tuple[float, float, float, float]:
        """
        Perform linear regression on time series data.
        """
        n = len(dates)
        if n < 2:
            return 0, 0, 0, 1
        
        # Convert dates to days since first date
        base_date = dates[0]
        x = [(d - base_date).days for d in dates]
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0, y_mean, 0, 1
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared
        ss_total = sum((values[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        # Calculate p-value (approximate)
        if n > 2 and r_squared > 0:
            t_stat = slope / (math.sqrt((1 - r_squared) / (n - 2)) + 0.001)
            p_value = 2 * (1 - self._t_cdf(abs(t_stat), n - 2))
        else:
            p_value = 1.0
        
        return slope, intercept, r_squared, p_value
    
    def _t_cdf(self, t: float, df: int) -> float:
        """
        Approximate Student's t CDF.
        """
        # Simplified approximation
        if df > 30:
            # Use normal approximation
            return 0.5 * (1 + math.erf(t / math.sqrt(2)))
        
        # For small df, use a rough approximation
        x = t / math.sqrt(df)
        return 0.5 * (1 + x / math.sqrt(1 + x * x))
    
    def _determine_trend_type(self, values: List[float], slope: float, r_squared: float) -> TrendType:
        """
        Determine trend type.
        """
        if len(values) < 3:
            return TrendType.UNDEFINED
        
        # Check for linear trend
        if r_squared > 0.7:
            if slope > 0:
                # Check if exponential
                if self._is_exponential(values):
                    return TrendType.EXPONENTIAL
                return TrendType.IMPROVING
            elif slope < 0:
                return TrendType.DECLINING
            else:
                return TrendType.STABLE
        
        # Check for other patterns
        if self._is_exponential(values):
            return TrendType.EXPONENTIAL
        elif self._is_logarithmic(values):
            return TrendType.LOGARITHMIC
        elif self._is_s_curve(values):
            return TrendType.S_CURVE
        elif self._is_plateau(values):
            return TrendType.PLATEAU
        elif self._is_volatile(values):
            return TrendType.VOLATILE
        
        return TrendType.UNDEFINED
    
    def _is_exponential(self, values: List[float]) -> bool:
        """
        Check if values follow exponential pattern.
        """
        if len(values) < 4 or any(v <= 0 for v in values):
            return False
        
        # Check if log of values is approximately linear
        log_values = [math.log(v) for v in values]
        x = list(range(len(log_values)))
        
        n = len(x)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(log_values)
        
        numerator = sum((x[i] - x_mean) * (log_values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return False
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate R-squared in log space
        ss_total = sum((log_values[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((log_values[i] - (slope * x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        return r_squared > 0.8
    
    def _is_logarithmic(self, values: List[float]) -> bool:
        """
        Check if values follow logarithmic pattern.
        """
        if len(values) < 4:
            return False
        
        x = list(range(1, len(values) + 1))
        log_x = [math.log(i) for i in x]
        
        n = len(x)
        x_mean = statistics.mean(log_x)
        y_mean = statistics.mean(values)
        
        numerator = sum((log_x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((log_x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return False
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        ss_total = sum((values[i] - y_mean) ** 2 for i in range(n))
        ss_residual = sum((values[i] - (slope * log_x[i] + intercept)) ** 2 for i in range(n))
        r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0
        
        return r_squared > 0.8
    
    def _is_s_curve(self, values: List[float]) -> bool:
        """
        Check if values follow S-curve pattern.
        """
        if len(values) < 5:
            return False
        
        # Check for sigmoid shape
        differences = [values[i+1] - values[i] for i in range(len(values)-1)]
        
        if len(differences) < 4:
            return False
        
        # Check if differences increase then decrease
        mid = len(differences) // 2
        first_half = differences[:mid]
        second_half = differences[mid:]
        
        if len(first_half) < 2 or len(second_half) < 2:
            return False
        
        increasing = all(first_half[i] <= first_half[i+1] for i in range(len(first_half)-1))
        decreasing = all(second_half[i] >= second_half[i+1] for i in range(len(second_half)-1))
        
        return increasing and decreasing
    
    def _is_plateau(self, values: List[float]) -> bool:
        """
        Check if values have plateaued.
        """
        if len(values) < 5:
            return False
        
        # Check if recent values are stable
        recent = values[-5:]
        std_dev = statistics.stdev(recent) if len(recent) > 1 else 0
        mean = statistics.mean(recent)
        
        return std_dev < mean * 0.05
    
    def _is_volatile(self, values: List[float]) -> bool:
        """
        Check if values are volatile.
        """
        if len(values) < 5:
            return False
        
        mean = statistics.mean(values)
        if mean == 0:
            return False
        
        cv = statistics.stdev(values) / abs(mean)
        return cv > 0.5
    
    def _detect_seasonality(self, values: List[float], period: AnalyticsPeriod) -> Optional[Dict[str, Any]]:
        """
        Detect seasonality in values.
        """
        if len(values) < 15:
            return None
        
        period_days = self.seasonality_periods.get(period.value, 7)
        
        # Check if values show periodic pattern
        strength = self._calculate_seasonality_strength(values, period_days)
        
        if strength > 0.3:
            return {
                'period': period_days,
                'strength': strength
            }
        
        return None
    
    def _calculate_seasonality_strength(self, values: List[float], period: int) -> float:
        """
        Calculate strength of seasonality.
        """
        if len(values) < period * 2:
            return 0
        
        # Calculate seasonal means
        seasonal_means = []
        for i in range(period):
            indices = list(range(i, len(values), period))
            if indices:
                seasonal_values = [values[j] for j in indices]
                seasonal_means.append(statistics.mean(seasonal_values))
        
        if len(seasonal_means) < 2:
            return 0
        
        # Calculate variance of seasonal means vs overall mean
        overall_mean = statistics.mean(values)
        variance_seasonal = statistics.variance(seasonal_means) if len(seasonal_means) > 1 else 0
        variance_overall = statistics.variance(values) if len(values) > 1 else 0
        
        if variance_overall == 0:
            return 0
        
        return min(1.0, variance_seasonal / variance_overall)
    
    def _calculate_moving_average(self, values: List[float], window: int) -> List[float]:
        """
        Calculate moving average.
        """
        if len(values) < window:
            return []
        
        moving_avg = []
        for i in range(len(values) - window + 1):
            avg = sum(values[i:i+window]) / window
            moving_avg.append(avg)
        
        return moving_avg
    
    def _calculate_confidence(self, values: List[float], r_squared: float, n: int) -> float:
        """
        Calculate confidence in trend.
        """
        confidence = 0.0
        
        # R-squared contributes
        confidence += r_squared * 0.4
        
        # Data points count contributes
        data_count_ratio = min(1.0, n / 30)
        confidence += data_count_ratio * 0.3
        
        # Volatility contributes (lower volatility = higher confidence)
        if len(values) > 1:
            cv = statistics.stdev(values) / (statistics.mean(values) + 0.001)
            volatility_confidence = min(1.0, 1 / (1 + cv))
            confidence += volatility_confidence * 0.3
        
        return min(1.0, confidence)
    
    def get_trend_summary(self, trend: TrendAnalysis) -> Dict[str, Any]:
        """
        Get summary of trend analysis.
        
        Args:
            trend: Trend analysis
        
        Returns:
            Dict: Trend summary
        """
        return {
            'metric': trend.metric.value,
            'period': trend.period.value,
            'data_points': trend.data_points,
            'trend_type': trend.trend_type.value,
            'direction': 'improving' if trend.slope > 0 else 'declining' if trend.slope < 0 else 'stable',
            'slope': trend.slope,
            'r_squared': trend.r_squared,
            'confidence': trend.confidence,
            'percentage_change': trend.percentage_change,
            'absolute_change': trend.absolute_change,
            'daily_rate': trend.daily_rate,
            'monthly_rate': trend.monthly_rate,
            'has_seasonality': trend.has_seasonality,
            'seasonality_period': trend.seasonality_period,
            'seasonality_strength': trend.seasonality_strength,
            'mean_value': trend.mean,
            'current_value': trend.values[-1] if trend.values else 0,
            'baseline_value': trend.values[0] if trend.values else 0
        }
    
    def get_moving_average_trend(self, trend: TrendAnalysis, window: int = 30) -> List[float]:
        """
        Get moving average trend.
        
        Args:
            trend: Trend analysis
            window: Moving average window
        
        Returns:
            List[float]: Moving average values
        """
        if window == 7:
            return trend.moving_average_7
        elif window == 30:
            return trend.moving_average_30
        elif window == 90:
            return trend.moving_average_90
        else:
            return self._calculate_moving_average(trend.values, window)