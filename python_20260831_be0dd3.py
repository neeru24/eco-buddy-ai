"""
Sustainability Analytics & Forecasting Engine - Historical Analyzer
Analyzes historical sustainability data across all categories.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from analytics.models import (
    HistoricalData, AnalyticsMetric, AnalyticsPeriod,
    DataGranularity, AnalyticsCategory
)

logger = logging.getLogger(__name__)


class HistoricalAnalyzer:
    """
    Analyzes historical sustainability data.
    """
    
    def __init__(self):
        """Initialize the historical analyzer."""
        self.metric_categories = self._initialize_metric_categories()
        self.aggregation_functions = {
            'sum': sum,
            'mean': statistics.mean,
            'median': statistics.median,
            'min': min,
            'max': max,
            'std': statistics.stdev
        }
        logger.info("Historical Analyzer initialized")
    
    def _initialize_metric_categories(self) -> Dict[AnalyticsMetric, AnalyticsCategory]:
        """
        Initialize metric to category mapping.
        """
        return {
            AnalyticsMetric.SUSTAINABILITY_SCORE: AnalyticsCategory.OVERALL,
            AnalyticsMetric.CARBON_FOOTPRINT: AnalyticsCategory.CARBON,
            AnalyticsMetric.ENERGY_CONSUMPTION: AnalyticsCategory.ENERGY,
            AnalyticsMetric.WATER_CONSUMPTION: AnalyticsCategory.WATER,
            AnalyticsMetric.WASTE_GENERATION: AnalyticsCategory.WASTE,
            AnalyticsMetric.TRANSPORTATION_IMPACT: AnalyticsCategory.TRANSPORTATION,
            AnalyticsMetric.FOOD_IMPACT: AnalyticsCategory.FOOD,
            AnalyticsMetric.SHOPPING_IMPACT: AnalyticsCategory.SHOPPING,
            AnalyticsMetric.HOUSEHOLD_PERFORMANCE: AnalyticsCategory.HOUSEHOLD,
            AnalyticsMetric.GOAL_COMPLETION_RATE: AnalyticsCategory.OVERALL,
            AnalyticsMetric.HABIT_CONSISTENCY: AnalyticsCategory.OVERALL,
            AnalyticsMetric.RECYCLING_RATE: AnalyticsCategory.WASTE,
            AnalyticsMetric.COMPOSTING_RATE: AnalyticsCategory.WASTE
        }
    
    def analyze_historical_data(self,
                               data: List[HistoricalData],
                               period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY,
                               granularity: DataGranularity = DataGranularity.DAILY) -> Dict[str, Any]:
        """
        Analyze historical data.
        
        Args:
            data: List of historical data points
            period: Analysis period
            granularity: Data granularity
        
        Returns:
            Dict: Historical analysis results
        """
        if not data:
            return {'message': 'No historical data available'}
        
        # Group by metric
        grouped_data = self._group_by_metric(data)
        
        # Analyze each metric
        metric_analyses = {}
        for metric, metric_data in grouped_data.items():
            metric_analyses[metric.value] = self._analyze_metric(
                metric_data, period, granularity
            )
        
        # Overall analysis
        overall_analysis = self._analyze_overall(data, period, granularity)
        
        # Category analysis
        category_analysis = self._analyze_by_category(data, period, granularity)
        
        return {
            'total_data_points': len(data),
            'date_range': self._get_date_range(data),
            'metrics': metric_analyses,
            'overall': overall_analysis,
            'by_category': category_analysis,
            'summary': self._generate_historical_summary(data, metric_analyses)
        }
    
    def _group_by_metric(self, data: List[HistoricalData]) -> Dict[AnalyticsMetric, List[HistoricalData]]:
        """
        Group data by metric.
        """
        grouped = defaultdict(list)
        for point in data:
            grouped[point.metric].append(point)
        return dict(grouped)
    
    def _analyze_metric(self,
                       data: List[HistoricalData],
                       period: AnalyticsPeriod,
                       granularity: DataGranularity) -> Dict[str, Any]:
        """
        Analyze a single metric.
        """
        if not data:
            return {'message': 'No data for this metric'}
        
        # Sort by timestamp
        sorted_data = sorted(data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        dates = [d.timestamp for d in sorted_data]
        
        # Calculate statistics
        stats = {
            'count': len(values),
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'first': values[0],
            'last': values[-1],
            'change': values[-1] - values[0],
            'change_percentage': ((values[-1] - values[0]) / (values[0] + 0.001)) * 100 if values[0] > 0 else 0
        }
        
        # Calculate moving averages
        moving_averages = {
            '7_day': self._calculate_moving_average(values, 7),
            '30_day': self._calculate_moving_average(values, 30),
            '90_day': self._calculate_moving_average(values, 90)
        }
        
        # Group by period
        period_data = self._group_by_period(data, period)
        
        return {
            'stats': stats,
            'values': values,
            'dates': [d.isoformat() for d in dates],
            'moving_averages': moving_averages,
            'period_breakdown': period_data,
            'trend': self._calculate_simple_trend(values)
        }
    
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
    
    def _group_by_period(self,
                        data: List[HistoricalData],
                        period: AnalyticsPeriod) -> Dict[str, Dict[str, Any]]:
        """
        Group data by time period.
        """
        grouped = defaultdict(list)
        
        for point in data:
            if period == AnalyticsPeriod.DAILY:
                key = point.timestamp.strftime('%Y-%m-%d')
            elif period == AnalyticsPeriod.WEEKLY:
                key = f"{point.timestamp.year}-W{point.timestamp.isocalendar()[1]:02d}"
            elif period == AnalyticsPeriod.MONTHLY:
                key = point.timestamp.strftime('%Y-%m')
            elif period == AnalyticsPeriod.QUARTERLY:
                quarter = (point.timestamp.month - 1) // 3 + 1
                key = f"{point.timestamp.year}-Q{quarter}"
            elif period == AnalyticsPeriod.YEARLY:
                key = str(point.timestamp.year)
            else:
                key = point.timestamp.strftime('%Y-%m-%d')
            
            grouped[key].append(point.value)
        
        result = {}
        for key, values in grouped.items():
            result[key] = {
                'count': len(values),
                'mean': statistics.mean(values),
                'sum': sum(values),
                'min': min(values),
                'max': max(values)
            }
        
        return dict(sorted(result.items()))
    
    def _calculate_simple_trend(self, values: List[float]) -> str:
        """
        Calculate simple trend direction.
        """
        if len(values) < 3:
            return 'insufficient_data'
        
        # Compare first third with last third
        n = len(values)
        first_third = values[:n//3]
        last_third = values[2*n//3:]
        
        first_avg = statistics.mean(first_third)
        last_avg = statistics.mean(last_third)
        
        if last_avg > first_avg * 1.05:
            return 'improving'
        elif last_avg < first_avg * 0.95:
            return 'declining'
        else:
            return 'stable'
    
    def _analyze_overall(self,
                        data: List[HistoricalData],
                        period: AnalyticsPeriod,
                        granularity: DataGranularity) -> Dict[str, Any]:
        """
        Analyze overall sustainability.
        """
        # Filter for sustainability scores
        score_data = [d for d in data if d.metric == AnalyticsMetric.SUSTAINABILITY_SCORE]
        
        if not score_data:
            return {'message': 'No sustainability score data'}
        
        sorted_data = sorted(score_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        
        return {
            'current_score': values[-1] if values else 0,
            'average_score': statistics.mean(values) if values else 0,
            'min_score': min(values) if values else 0,
            'max_score': max(values) if values else 0,
            'score_change': values[-1] - values[0] if len(values) > 1 else 0,
            'score_change_percentage': ((values[-1] - values[0]) / (values[0] + 0.001)) * 100 if values and values[0] > 0 else 0,
            'data_points': len(values),
            'trend': self._calculate_simple_trend(values)
        }
    
    def _analyze_by_category(self,
                            data: List[HistoricalData],
                            period: AnalyticsPeriod,
                            granularity: DataGranularity) -> Dict[str, Dict[str, Any]]:
        """
        Analyze by category.
        """
        category_data = defaultdict(list)
        
        for point in data:
            category = self.metric_categories.get(point.metric, AnalyticsCategory.OVERALL)
            category_data[category.value].append(point)
        
        result = {}
        for category, category_points in category_data.items():
            values = [p.value for p in category_points]
            result[category] = {
                'count': len(values),
                'mean': statistics.mean(values) if values else 0,
                'min': min(values) if values else 0,
                'max': max(values) if values else 0,
                'trend': self._calculate_simple_trend(values) if len(values) >= 3 else 'insufficient_data'
            }
        
        return result
    
    def _get_date_range(self, data: List[HistoricalData]) -> Dict[str, str]:
        """
        Get date range of data.
        """
        if not data:
            return {}
        
        dates = [d.timestamp for d in data]
        return {
            'start': min(dates).strftime('%Y-%m-%d'),
            'end': max(dates).strftime('%Y-%m-%d'),
            'days': (max(dates) - min(dates)).days
        }
    
    def _generate_historical_summary(self,
                                    data: List[HistoricalData],
                                    metric_analyses: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate historical summary.
        """
        return {
            'total_data_points': len(data),
            'metrics_analyzed': len(metric_analyses),
            'date_range': self._get_date_range(data),
            'overall_trend': self._calculate_overall_trend(data)
        }
    
    def _calculate_overall_trend(self, data: List[HistoricalData]) -> str:
        """
        Calculate overall trend from data.
        """
        # Use sustainability scores for overall trend
        score_data = [d for d in data if d.metric == AnalyticsMetric.SUSTAINABILITY_SCORE]
        
        if len(score_data) < 3:
            return 'insufficient_data'
        
        sorted_data = sorted(score_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        
        return self._calculate_simple_trend(values)
    
    def get_category_breakdown(self, data: List[HistoricalData]) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed category breakdown.
        
        Args:
            data: Historical data
        
        Returns:
            Dict: Category breakdown
        """
        breakdown = {}
        
        for category in AnalyticsCategory:
            category_data = [d for d in data if self.metric_categories.get(d.metric) == category]
            
            if category_data:
                values = [d.value for d in category_data]
                breakdown[category.value] = {
                    'count': len(values),
                    'average': statistics.mean(values) if values else 0,
                    'min': min(values) if values else 0,
                    'max': max(values) if values else 0,
                    'total': sum(values),
                    'trend': self._calculate_simple_trend(values) if len(values) >= 3 else 'insufficient_data'
                }
        
        return breakdown
    
    def get_metric_history(self,
                          data: List[HistoricalData],
                          metric: AnalyticsMetric,
                          days: int = 30) -> List[Dict[str, Any]]:
        """
        Get history for a specific metric.
        
        Args:
            data: Historical data
            metric: Metric to analyze
            days: Number of days to include
        
        Returns:
            List[Dict]: Metric history
        """
        cutoff = datetime.now() - timedelta(days=days)
        filtered = [d for d in data if d.metric == metric and d.timestamp >= cutoff]
        sorted_data = sorted(filtered, key=lambda x: x.timestamp)
        
        return [
            {
                'date': d.timestamp.isoformat(),
                'value': d.value,
                'unit': d.unit,
                'category': d.category
            }
            for d in sorted_data
        ]