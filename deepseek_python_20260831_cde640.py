"""
Sustainability Analytics & Forecasting Engine - Comparative Analyzer
Compares different aspects of sustainability data.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from analytics.models import (
    ComparativeAnalysis, ComparisonType, AnalyticsMetric,
    HistoricalData, AnalyticsCategory
)

logger = logging.getLogger(__name__)


class ComparativeAnalyzer:
    """
    Performs comparative analytics.
    """
    
    def __init__(self):
        """Initialize the comparative analyzer."""
        self.analysis_methods = {
            'period_over_period': self._period_comparison,
            'category_comparison': self._category_comparison,
            'member_comparison': self._member_comparison,
            'actual_vs_target': self._actual_vs_target,
            'year_over_year': self._year_over_year
        }
        logger.info("Comparative Analyzer initialized")
    
    def compare(self,
               data: List[HistoricalData],
               comparison_type: ComparisonType,
               metric: AnalyticsMetric,
               **kwargs) -> ComparativeAnalysis:
        """
        Perform comparative analysis.
        
        Args:
            data: Historical data
            comparison_type: Type of comparison
            metric: Metric to compare
            **kwargs: Additional parameters
        
        Returns:
            ComparativeAnalysis: Comparison results
        """
        analysis_method = self.analysis_methods.get(comparison_type.value)
        if not analysis_method:
            return ComparativeAnalysis(
                user_id=data[0].user_id if data else "",
                comparison_type=comparison_type,
                metric=metric,
                notes="Unsupported comparison type"
            )
        
        return analysis_method(data, metric, **kwargs)
    
    def _period_comparison(self,
                          data: List[HistoricalData],
                          metric: AnalyticsMetric,
                          **kwargs) -> ComparativeAnalysis:
        """
        Compare two time periods.
        """
        period1_start = kwargs.get('period1_start', datetime.now() - timedelta(days=30))
        period1_end = kwargs.get('period1_end', datetime.now() - timedelta(days=15))
        period2_start = kwargs.get('period2_start', datetime.now() - timedelta(days=15))
        period2_end = kwargs.get('period2_end', datetime.now())
        
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        # Filter by periods
        period1_data = [d for d in metric_data if period1_start <= d.timestamp <= period1_end]
        period2_data = [d for d in metric_data if period2_start <= d.timestamp <= period2_end]
        
        # Calculate statistics
        period1_values = [d.value for d in period1_data]
        period2_values = [d.value for d in period2_data]
        
        p1_mean = statistics.mean(period1_values) if period1_values else 0
        p2_mean = statistics.mean(period2_values) if period2_values else 0
        
        # Create comparison
        comparison = ComparativeAnalysis(
            user_id=data[0].user_id if data else "",
            comparison_type=ComparisonType.PERIOD_OVER_PERIOD,
            metric=metric,
            current_period={
                'start': period2_start.isoformat(),
                'end': period2_end.isoformat(),
                'mean': p2_mean,
                'count': len(period2_values)
            },
            previous_period={
                'start': period1_start.isoformat(),
                'end': period1_end.isoformat(),
                'mean': p1_mean,
                'count': len(period1_values)
            }
        )
        
        # Calculate differences
        comparison.absolute_difference = p2_mean - p1_mean
        comparison.percentage_difference = ((p2_mean - p1_mean) / (p1_mean + 0.001)) * 100 if p1_mean > 0 else 0
        
        # Generate insights
        comparison.insights = self._generate_period_insights(comparison)
        
        return comparison
    
    def _category_comparison(self,
                            data: List[HistoricalData],
                            metric: AnalyticsMetric,
                            **kwargs) -> ComparativeAnalysis:
        """
        Compare categories.
        """
        categories = kwargs.get('categories', [])
        
        if not categories:
            return ComparativeAnalysis(
                user_id=data[0].user_id if data else "",
                comparison_type=ComparisonType.CATEGORY_COMPARISON,
                metric=metric,
                notes="No categories specified"
            )
        
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        category_data = {}
        for category in categories:
            category_points = [d for d in metric_data if d.category == category]
            if category_points:
                values = [d.value for d in category_points]
                category_data[category] = {
                    'mean': statistics.mean(values),
                    'count': len(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        # Create comparison
        comparison = ComparativeAnalysis(
            user_id=data[0].user_id if data else "",
            comparison_type=ComparisonType.CATEGORY_COMPARISON,
            metric=metric,
            current_period=category_data,
            previous_period={}
        )
        
        # Find best and worst categories
        if category_data:
            best_category = max(category_data.items(), key=lambda x: x[1]['mean'])
            worst_category = min(category_data.items(), key=lambda x: x[1]['mean'])
            
            comparison.comparison_results = {
                'best_category': best_category[0],
                'best_score': best_category[1]['mean'],
                'worst_category': worst_category[0],
                'worst_score': worst_category[1]['mean'],
                'gap': best_category[1]['mean'] - worst_category[1]['mean']
            }
            
            comparison.insights = [f"Best performing category: {best_category[0]} ({best_category[1]['mean']:.1f})"]
            comparison.insights.append(f"Worst performing category: {worst_category[0]} ({worst_category[1]['mean']:.1f})")
        
        return comparison
    
    def _member_comparison(self,
                          data: List[HistoricalData],
                          metric: AnalyticsMetric,
                          **kwargs) -> ComparativeAnalysis:
        """
        Compare household members.
        """
        members = kwargs.get('members', [])
        household_id = kwargs.get('household_id', '')
        
        if not members:
            return ComparativeAnalysis(
                user_id=data[0].user_id if data else "",
                comparison_type=ComparisonType.MEMBER_COMPARISON,
                metric=metric,
                notes="No members specified"
            )
        
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        member_data = {}
        for member in members:
            member_points = [d for d in metric_data if d.metadata.get('member_id') == member]
            if member_points:
                values = [d.value for d in member_points]
                member_data[member] = {
                    'mean': statistics.mean(values),
                    'count': len(values),
                    'min': min(values),
                    'max': max(values)
                }
        
        # Create comparison
        comparison = ComparativeAnalysis(
            user_id=data[0].user_id if data else "",
            comparison_type=ComparisonType.MEMBER_COMPARISON,
            metric=metric,
            current_period=member_data,
            previous_period={}
        )
        
        # Calculate rankings
        if member_data:
            sorted_members = sorted(member_data.items(), key=lambda x: x[1]['mean'], reverse=True)
            
            comparison.comparison_results = {
                'rankings': [{'member': m[0], 'score': m[1]['mean']} for m in sorted_members]
            }
            
            comparison.insights = []
            for i, (member, data) in enumerate(sorted_members[:3], 1):
                comparison.insights.append(f"#{i}: {member} ({data['mean']:.1f})")
        
        return comparison
    
    def _actual_vs_target(self,
                         data: List[HistoricalData],
                         metric: AnalyticsMetric,
                         **kwargs) -> ComparativeAnalysis:
        """
        Compare actual vs target performance.
        """
        target = kwargs.get('target', 0)
        
        if target <= 0:
            return ComparativeAnalysis(
                user_id=data[0].user_id if data else "",
                comparison_type=ComparisonType.ACTUAL_VS_TARGET,
                metric=metric,
                notes="Invalid target value"
            )
        
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        if not metric_data:
            return ComparativeAnalysis(
                user_id=data[0].user_id if data else "",
                comparison_type=ComparisonType.ACTUAL_VS_TARGET,
                metric=metric,
                notes="No data available"
            )
        
        values = [d.value for d in metric_data]
        current = values[-1] if values else 0
        
        # Create comparison
        comparison = ComparativeAnalysis(
            user_id=data[0].user_id if data else "",
            comparison_type=ComparisonType.ACTUAL_VS_TARGET,
            metric=metric,
            current_period={'current': current},
            previous_period={'target': target}
        )
        
        comparison.absolute_difference = current - target
        comparison.percentage_difference = ((current - target) / (target + 0.001)) * 100
        
        comparison.comparison_results = {
            'current': current,
            'target': target,
            'achieved': current >= target,
            'gap': target - current if current < target else 0
        }
        
        if current >= target:
            comparison.insights = ["Target achieved! Performance meets or exceeds target"]
        else:
            comparison.insights = [f"Target not yet achieved. Need {target - current:.1f} more"]
        
        return comparison
    
    def _year_over_year(self,
                       data: List[HistoricalData],
                       metric: AnalyticsMetric,
                       **kwargs) -> ComparativeAnalysis:
        """
        Compare year over year performance.
        """
        current_year = kwargs.get('current_year', datetime.now().year)
        previous_year = current_year - 1
        
        # Filter data for the metric
        metric_data = [d for d in data if d.metric == metric]
        
        current_data = [d for d in metric_data if d.timestamp.year == current_year]
        previous_data = [d for d in metric_data if d.timestamp.year == previous_year]
        
        current_values = [d.value for d in current_data]
        previous_values = [d.value for d in previous_data]
        
        current_mean = statistics.mean(current_values) if current_values else 0
        previous_mean = statistics.mean(previous_values) if previous_values else 0
        
        # Create comparison
        comparison = ComparativeAnalysis(
            user_id=data[0].user_id if data else "",
            comparison_type=ComparisonType.YEAR_OVER_YEAR,
            metric=metric,
            current_period={'year': current_year, 'mean': current_mean, 'count': len(current_values)},
            previous_period={'year': previous_year, 'mean': previous_mean, 'count': len(previous_values)}
        )
        
        comparison.absolute_difference = current_mean - previous_mean
        comparison.percentage_difference = ((current_mean - previous_mean) / (previous_mean + 0.001)) * 100 if previous_mean > 0 else 0
        
        if comparison.percentage_difference > 5:
            comparison.insights = [f"Year over year improvement of {comparison.percentage_difference:.1f}%"]
        elif comparison.percentage_difference < -5:
            comparison.insights = [f"Year over year decline of {abs(comparison.percentage_difference):.1f}%"]
        else:
            comparison.insights = ["Year over year performance is stable"]
        
        return comparison
    
    def _generate_period_insights(self, comparison: ComparativeAnalysis) -> List[str]:
        """
        Generate insights from period comparison.
        """
        insights = []
        
        if comparison.percentage_difference > 10:
            insights.append(f"Significant improvement of {comparison.percentage_difference:.1f}%")
        elif comparison.percentage_difference > 0:
            insights.append(f"Modest improvement of {comparison.percentage_difference:.1f}%")
        elif comparison.percentage_difference < -10:
            insights.append(f"Significant decline of {abs(comparison.percentage_difference):.1f}%")
        elif comparison.percentage_difference < 0:
            insights.append(f"Modest decline of {abs(comparison.percentage_difference):.1f}%")
        else:
            insights.append("No significant change between periods")
        
        return insights
    
    def get_comparison_summary(self, comparison: ComparativeAnalysis) -> Dict[str, Any]:
        """
        Get summary of comparative analysis.
        
        Args:
            comparison: Comparative analysis
        
        Returns:
            Dict: Summary
        """
        return {
            'comparison_type': comparison.comparison_type.value,
            'metric': comparison.metric.value,
            'absolute_difference': comparison.absolute_difference,
            'percentage_difference': comparison.percentage_difference,
            'current_period': comparison.current_period,
            'previous_period': comparison.previous_period,
            'insights': comparison.insights,
            'confidence': comparison.confidence
        }