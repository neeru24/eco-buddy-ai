"""
Sustainability Analytics & Forecasting Engine - Category Analyzer
Analyzes sustainability performance by category.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from analytics.models import (
    CategoryAnalytics, AnalyticsCategory, AnalyticsPeriod,
    HistoricalData, AnalyticsMetric, TrendType
)

logger = logging.getLogger(__name__)


class CategoryAnalyzer:
    """
    Analyzes sustainability performance by category.
    """
    
    def __init__(self):
        """Initialize the category analyzer."""
        self.category_metrics = self._initialize_category_metrics()
        logger.info("Category Analyzer initialized")
    
    def _initialize_category_metrics(self) -> Dict[AnalyticsCategory, List[AnalyticsMetric]]:
        """
        Initialize metrics for each category.
        """
        return {
            AnalyticsCategory.CARBON: [
                AnalyticsMetric.CARBON_FOOTPRINT
            ],
            AnalyticsCategory.ENERGY: [
                AnalyticsMetric.ENERGY_CONSUMPTION
            ],
            AnalyticsCategory.WATER: [
                AnalyticsMetric.WATER_CONSUMPTION
            ],
            AnalyticsCategory.WASTE: [
                AnalyticsMetric.WASTE_GENERATION,
                AnalyticsMetric.RECYCLING_RATE,
                AnalyticsMetric.COMPOSTING_RATE
            ],
            AnalyticsCategory.TRANSPORTATION: [
                AnalyticsMetric.TRANSPORTATION_IMPACT
            ],
            AnalyticsCategory.FOOD: [
                AnalyticsMetric.FOOD_IMPACT
            ],
            AnalyticsCategory.SHOPPING: [
                AnalyticsMetric.SHOPPING_IMPACT
            ],
            AnalyticsCategory.HOUSEHOLD: [
                AnalyticsMetric.HOUSEHOLD_PERFORMANCE
            ]
        }
    
    def analyze_category(self,
                        data: List[HistoricalData],
                        category: AnalyticsCategory,
                        period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY) -> CategoryAnalytics:
        """
        Analyze a specific category.
        
        Args:
            data: Historical data
            category: Category to analyze
            period: Analysis period
        
        Returns:
            CategoryAnalytics: Category analysis
        """
        # Get metrics for this category
        metrics = self.category_metrics.get(category, [])
        
        if not metrics:
            return CategoryAnalytics(
                user_id=data[0].user_id if data else "",
                category=category,
                period=period,
                notes="No metrics defined for this category"
            )
        
        # Filter data for the category metrics
        category_data = [d for d in data if d.metric in metrics]
        
        if not category_data:
            return CategoryAnalytics(
                user_id=data[0].user_id if data else "",
                category=category,
                period=period,
                data_points=0,
                notes="No data available for this category"
            )
        
        # Sort by timestamp
        sorted_data = sorted(category_data, key=lambda x: x.timestamp)
        values = [d.value for d in sorted_data]
        
        # Create category analysis
        analysis = CategoryAnalytics(
            user_id=sorted_data[0].user_id,
            category=category,
            period=period,
            start_date=sorted_data[0].timestamp,
            end_date=sorted_data[-1].timestamp,
            data_points=len(values)
        )
        
        # Calculate performance metrics
        analysis.current_score = values[-1] if values else 0
        analysis.previous_score = values[0] if values else 0
        analysis.change = analysis.current_score - analysis.previous_score
        analysis.change_percentage = (analysis.change / (analysis.previous_score + 0.001)) * 100 if analysis.previous_score > 0 else 0
        
        # Calculate trend
        if len(values) >= 3:
            slope = self._calculate_slope(values)
            analysis.trend_type = self._determine_trend_type(slope)
            analysis.trend_slope = slope
        
        # Calculate subcategory scores
        analysis.subcategory_scores = self._calculate_subcategory_scores(category_data, metrics)
        analysis.subcategory_trends = self._calculate_subcategory_trends(category_data, metrics)
        
        # Generate strengths and weaknesses
        analysis.strengths = self._identify_strengths(analysis)
        analysis.weaknesses = self._identify_weaknesses(analysis)
        analysis.opportunities = self._identify_opportunities(analysis)
        
        # Calculate confidence
        analysis.confidence = min(1.0, len(values) / 30)
        
        return analysis
    
    def _calculate_slope(self, values: List[float]) -> float:
        """
        Calculate slope of values.
        """
        if len(values) < 2:
            return 0
        
        x = list(range(len(values)))
        n = len(x)
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def _determine_trend_type(self, slope: float) -> TrendType:
        """
        Determine trend type from slope.
        """
        if slope > 0.5:
            return TrendType.IMPROVING
        elif slope > 0.1:
            return TrendType.STABLE
        elif slope > -0.1:
            return TrendType.STABLE
        elif slope > -0.5:
            return TrendType.DECLINING
        else:
            return TrendType.DECLINING
    
    def _calculate_subcategory_scores(self,
                                     data: List[HistoricalData],
                                     metrics: List[AnalyticsMetric]) -> Dict[str, float]:
        """
        Calculate scores for subcategories.
        """
        scores = {}
        
        for metric in metrics:
            metric_data = [d for d in data if d.metric == metric]
            if metric_data:
                values = [d.value for d in metric_data]
                scores[metric.value] = values[-1] if values else 0
        
        return scores
    
    def _calculate_subcategory_trends(self,
                                     data: List[HistoricalData],
                                     metrics: List[AnalyticsMetric]) -> Dict[str, float]:
        """
        Calculate trends for subcategories.
        """
        trends = {}
        
        for metric in metrics:
            metric_data = [d for d in data if d.metric == metric]
            if len(metric_data) >= 3:
                values = [d.value for d in metric_data]
                slope = self._calculate_slope(values)
                trends[metric.value] = slope
        
        return trends
    
    def _identify_strengths(self, analysis: CategoryAnalytics) -> List[str]:
        """
        Identify category strengths.
        """
        strengths = []
        
        if analysis.current_score > 70:
            strengths.append("Strong overall performance")
        
        for subcategory, score in analysis.subcategory_scores.items():
            if score > 75:
                strengths.append(f"Strong performance in {subcategory.replace('_', ' ').title()}")
        
        if analysis.trend_type == TrendType.IMPROVING:
            strengths.append("Consistently improving trend")
        
        return strengths[:3]
    
    def _identify_weaknesses(self, analysis: CategoryAnalytics) -> List[str]:
        """
        Identify category weaknesses.
        """
        weaknesses = []
        
        if analysis.current_score < 40:
            weaknesses.append("Overall performance needs improvement")
        
        for subcategory, score in analysis.subcategory_scores.items():
            if score < 40:
                weaknesses.append(f"Weak performance in {subcategory.replace('_', ' ').title()}")
        
        if analysis.trend_type == TrendType.DECLINING:
            weaknesses.append("Declining trend detected")
        
        return weaknesses[:3]
    
    def _identify_opportunities(self, analysis: CategoryAnalytics) -> List[str]:
        """
        Identify improvement opportunities.
        """
        opportunities = []
        
        for subcategory, score in analysis.subcategory_scores.items():
            if score < 50:
                opportunities.append(f"Focus on improving {subcategory.replace('_', ' ').title()}")
        
        if analysis.trend_type == TrendType.DECLINING:
            opportunities.append("Implement measures to reverse the declining trend")
        elif analysis.trend_type == TrendType.STABLE and analysis.current_score < 60:
            opportunities.append("Look for ways to accelerate improvement from stable performance")
        
        return opportunities[:3]
    
    def get_category_summary(self, analysis: CategoryAnalytics) -> Dict[str, Any]:
        """
        Get summary of category analysis.
        
        Args:
            analysis: Category analysis
        
        Returns:
            Dict: Summary
        """
        return {
            'category': analysis.category.value,
            'period': analysis.period.value,
            'current_score': analysis.current_score,
            'change_percentage': analysis.change_percentage,
            'trend_type': analysis.trend_type.value if analysis.trend_type else 'undefined',
            'data_points': analysis.data_points,
            'confidence': analysis.confidence,
            'strengths': analysis.strengths,
            'weaknesses': analysis.weaknesses,
            'opportunities': analysis.opportunities,
            'subcategory_scores': analysis.subcategory_scores,
            'subcategory_trends': analysis.subcategory_trends
        }
    
    def compare_categories(self,
                          data: List[HistoricalData],
                          categories: List[AnalyticsCategory]) -> Dict[str, Any]:
        """
        Compare multiple categories.
        
        Args:
            data: Historical data
            categories: Categories to compare
        
        Returns:
            Dict: Comparison results
        """
        results = {}
        category_analyses = []
        
        for category in categories:
            analysis = self.analyze_category(data, category)
            category_analyses.append(analysis)
            results[category.value] = {
                'score': analysis.current_score,
                'change': analysis.change_percentage,
                'trend': analysis.trend_type.value if analysis.trend_type else 'undefined'
            }
        
        # Find best and worst
        if category_analyses:
            best = max(category_analyses, key=lambda x: x.current_score)
            worst = min(category_analyses, key=lambda x: x.current_score)
            fastest = max(category_analyses, key=lambda x: x.change_percentage)
            
            results['comparison'] = {
                'best_category': best.category.value,
                'best_score': best.current_score,
                'worst_category': worst.category.value,
                'worst_score': worst.current_score,
                'fastest_improving': fastest.category.value,
                'fastest_improvement': fastest.change_percentage
            }
        
        return results