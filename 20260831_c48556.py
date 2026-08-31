"""
Sustainability Analytics & Forecasting Engine - Household Analyzer
Analyzes household-level sustainability performance.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from analytics.models import (
    HouseholdAnalytics, AnalyticsPeriod, HistoricalData,
    AnalyticsMetric, AnalyticsCategory, TrendType
)

logger = logging.getLogger(__name__)


class HouseholdAnalyzer:
    """
    Analyzes household-level sustainability performance.
    """
    
    def __init__(self):
        """Initialize the household analyzer."""
        logger.info("Household Analyzer initialized")
    
    def analyze_household(self,
                         data: List[HistoricalData],
                         household_id: str,
                         member_ids: List[str],
                         period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY) -> HouseholdAnalytics:
        """
        Analyze household performance.
        
        Args:
            data: Historical data
            household_id: Household ID
            member_ids: List of member IDs
            period: Analysis period
        
        Returns:
            HouseholdAnalytics: Household analysis
        """
        analysis = HouseholdAnalytics(
            household_id=household_id,
            period=period,
            member_count=len(member_ids)
        )
        
        # Filter data for the household
        household_data = [d for d in data if d.household_id == household_id]
        
        if not household_data:
            analysis.notes = "No data available for this household"
            return analysis
        
        # Sort by timestamp
        sorted_data = sorted(household_data, key=lambda x: x.timestamp)
        
        # Calculate overall metrics
        sustainability_data = [d for d in sorted_data if d.metric == AnalyticsMetric.SUSTAINABILITY_SCORE]
        if sustainability_data:
            values = [d.value for d in sustainability_data]
            analysis.total_sustainability_score = values[-1] if values else 0
            analysis.average_sustainability_score = statistics.mean(values) if values else 0
        
        # Analyze by member
        analysis.member_scores = self._calculate_member_scores(household_data, member_ids)
        analysis.member_rankings = self._rank_members(analysis.member_scores)
        analysis.member_trends = self._calculate_member_trends(household_data, member_ids)
        
        # Analyze by category
        analysis.category_scores = self._calculate_category_scores(household_data)
        analysis.category_rankings = self._rank_categories(analysis.category_scores)
        
        # Calculate household trend
        if sustainability_data:
            values = [d.value for d in sustainability_data]
            if len(values) >= 3:
                analysis.household_trend = self._calculate_trend(values)
        
        # Calculate impact metrics
        analysis.total_carbon_saved = self._calculate_impact(household_data, AnalyticsMetric.CARBON_FOOTPRINT)
        analysis.total_water_saved = self._calculate_impact(household_data, AnalyticsMetric.WATER_CONSUMPTION)
        analysis.total_waste_reduced = self._calculate_impact(household_data, AnalyticsMetric.WASTE_GENERATION)
        
        # Generate insights and recommendations
        analysis.insights = self._generate_household_insights(analysis)
        analysis.recommendations = self._generate_household_recommendations(analysis)
        
        # Calculate confidence
        analysis.confidence = min(1.0, len(household_data) / 50)
        analysis.data_points = len(household_data)
        
        return analysis
    
    def _calculate_member_scores(self,
                                data: List[HistoricalData],
                                member_ids: List[str]) -> Dict[str, float]:
        """
        Calculate scores for each member.
        """
        scores = {}
        
        for member_id in member_ids:
            member_data = [d for d in data if d.metadata.get('member_id') == member_id]
            if member_data:
                # Use sustainability scores if available
                sustainability_data = [d for d in member_data if d.metric == AnalyticsMetric.SUSTAINABILITY_SCORE]
                if sustainability_data:
                    values = [d.value for d in sustainability_data]
                    scores[member_id] = values[-1] if values else 0
                else:
                    # Calculate average of all metrics
                    values = [d.value for d in member_data]
                    scores[member_id] = statistics.mean(values) if values else 0
        
        return scores
    
    def _rank_members(self, member_scores: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Rank members by score.
        """
        sorted_members = sorted(member_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {
                'rank': i + 1,
                'member_id': member_id,
                'score': score
            }
            for i, (member_id, score) in enumerate(sorted_members)
        ]
    
    def _calculate_member_trends(self,
                                data: List[HistoricalData],
                                member_ids: List[str]) -> Dict[str, TrendType]:
        """
        Calculate trends for each member.
        """
        trends = {}
        
        for member_id in member_ids:
            member_data = [d for d in data if d.metadata.get('member_id') == member_id]
            if len(member_data) >= 3:
                values = [d.value for d in member_data]
                trends[member_id] = self._calculate_trend(values)
            else:
                trends[member_id] = TrendType.UNDEFINED
        
        return trends
    
    def _calculate_category_scores(self, data: List[HistoricalData]) -> Dict[str, float]:
        """
        Calculate scores for each category.
        """
        scores = {}
        
        for category in AnalyticsCategory:
            category_data = [d for d in data if d.category == category.value]
            if category_data:
                values = [d.value for d in category_data]
                scores[category.value] = statistics.mean(values) if values else 0
        
        return scores
    
    def _rank_categories(self, category_scores: Dict[str, float]) -> Dict[str, int]:
        """
        Rank categories by score.
        """
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        return {
            category: rank + 1
            for rank, (category, score) in enumerate(sorted_categories)
        }
    
    def _calculate_trend(self, values: List[float]) -> TrendType:
        """
        Calculate trend from values.
        """
        if len(values) < 3:
            return TrendType.UNDEFINED
        
        # Simple trend calculation
        first = values[0]
        last = values[-1]
        change = last - first
        change_pct = (change / (first + 0.001)) * 100 if first > 0 else 0
        
        if change_pct > 5:
            return TrendType.IMPROVING
        elif change_pct < -5:
            return TrendType.DECLINING
        else:
            return TrendType.STABLE
    
    def _calculate_impact(self, data: List[HistoricalData], metric: AnalyticsMetric) -> float:
        """
        Calculate impact for a metric.
        """
        metric_data = [d for d in data if d.metric == metric]
        if len(metric_data) >= 2:
            sorted_data = sorted(metric_data, key=lambda x: x.timestamp)
            first = sorted_data[0].value
            last = sorted_data[-1].value
            return max(0, first - last)
        return 0.0
    
    def _generate_household_insights(self, analysis: HouseholdAnalytics) -> List[str]:
        """
        Generate household insights.
        """
        insights = []
        
        # Overall performance
        if analysis.total_sustainability_score > 70:
            insights.append("Household is performing well overall")
        elif analysis.total_sustainability_score > 50:
            insights.append("Household has moderate sustainability performance")
        else:
            insights.append("Household sustainability needs improvement")
        
        # Member performance
        if analysis.member_rankings:
            best = analysis.member_rankings[0]
            insights.append(f"Best performing member: {best['member_id']} ({best['score']:.1f})")
            
            if len(analysis.member_rankings) > 1:
                worst = analysis.member_rankings[-1]
                insights.append(f"Member needing improvement: {worst['member_id']} ({worst['score']:.1f})")
        
        # Category performance
        if analysis.category_scores:
            best_category = max(analysis.category_scores.items(), key=lambda x: x[1])
            worst_category = min(analysis.category_scores.items(), key=lambda x: x[1])
            insights.append(f"Strongest category: {best_category[0]} ({best_category[1]:.1f})")
            insights.append(f"Weakest category: {worst_category[0]} ({worst_category[1]:.1f})")
        
        # Trend
        if analysis.household_trend == TrendType.IMPROVING:
            insights.append("Household performance is improving over time")
        elif analysis.household_trend == TrendType.DECLINING:
            insights.append("Household performance is declining - need intervention")
        
        return insights[:5]
    
    def _generate_household_recommendations(self, analysis: HouseholdAnalytics) -> List[str]:
        """
        Generate household recommendations.
        """
        recommendations = []
        
        # Based on categories
        if analysis.category_scores:
            worst_category = min(analysis.category_scores.items(), key=lambda x: x[1])
            recommendations.append(f"Focus on improving {worst_category[0]} category")
        
        # Based on members
        if analysis.member_rankings and len(analysis.member_rankings) > 1:
            worst_member = analysis.member_rankings[-1]
            recommendations.append(f"Support {worst_member['member_id']} in improving their sustainability performance")
        
        # Based on trend
        if analysis.household_trend == TrendType.DECLINING:
            recommendations.append("Implement household-wide sustainability intervention")
        
        # General recommendations
        recommendations.append("Consider setting household sustainability goals")
        recommendations.append("Track household progress regularly")
        
        return recommendations[:5]
    
    def get_household_summary(self, analysis: HouseholdAnalytics) -> Dict[str, Any]:
        """
        Get summary of household analysis.
        
        Args:
            analysis: Household analysis
        
        Returns:
            Dict: Summary
        """
        return {
            'household_id': analysis.household_id,
            'period': analysis.period.value,
            'total_score': analysis.total_sustainability_score,
            'average_score': analysis.average_sustainability_score,
            'member_count': analysis.member_count,
            'trend': analysis.household_trend.value if analysis.household_trend else 'undefined',
            'member_rankings': analysis.member_rankings[:3],
            'category_rankings': analysis.category_rankings,
            'total_carbon_saved': analysis.total_carbon_saved,
            'total_water_saved': analysis.total_water_saved,
            'total_waste_reduced': analysis.total_waste_reduced,
            'insights': analysis.insights[:3],
            'recommendations': analysis.recommendations[:3],
            'confidence': analysis.confidence
        }