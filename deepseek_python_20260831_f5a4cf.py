"""
Sustainability Lifecycle & Long-Term Progress Management - Long-Term Analytics
Provides long-term analytical insights.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from lifecycle.models import (
    LongTermAnalytics, ProgressSnapshot, TrendAnalysis,
    HistoricalInsight, JourneySummary
)

logger = logging.getLogger(__name__)


class LongTermAnalyticsEngine:
    """
    Analyzes long-term sustainability data.
    """
    
    def __init__(self):
        """Initialize the analytics engine."""
        self.analysis_periods = ['monthly', 'quarterly', 'yearly']
        logger.info("Long-Term Analytics Engine initialized")
    
    def analyze_long_term(self, 
                         snapshots: List[ProgressSnapshot],
                         period: str = 'monthly') -> LongTermAnalytics:
        """
        Analyze long-term sustainability data.
        
        Args:
            snapshots: List of progress snapshots
            period: Analysis period
        
        Returns:
            LongTermAnalytics: Long-term analytics
        """
        if not snapshots:
            return LongTermAnalytics()
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        analytics = LongTermAnalytics(
            user_id=sorted_snapshots[0].user_id,
            period=period,
            start_date=sorted_snapshots[0].snapshot_date,
            end_date=sorted_snapshots[-1].snapshot_date
        )
        
        # Calculate overall metrics
        scores = [s.sustainability_score for s in sorted_snapshots]
        analytics.sustainability_score_avg = statistics.mean(scores)
        analytics.sustainability_score_median = statistics.median(scores)
        analytics.sustainability_score_variance = statistics.variance(scores) if len(scores) > 1 else 0
        
        # Calculate trend
        if len(scores) >= 2:
            analytics.sustainability_score_trend = self._calculate_trend(scores)
        
        # Calculate category trends
        category_trends = self._calculate_category_trends(sorted_snapshots)
        analytics.category_trends = category_trends
        analytics.category_averages = self._calculate_category_averages(sorted_snapshots)
        
        # Calculate improvement metrics
        if len(scores) >= 2:
            analytics.total_improvement_percentage = ((scores[-1] - scores[0]) / (scores[0] + 0.001)) * 100
            
            # Monthly improvements
            monthly_changes = []
            for i in range(1, len(scores)):
                change = scores[i] - scores[i-1]
                monthly_changes.append(change)
            
            if monthly_changes:
                analytics.average_monthly_improvement = statistics.mean(monthly_changes)
                analytics.best_monthly_improvement = max(monthly_changes)
                analytics.worst_monthly_improvement = min(monthly_changes)
        
        # Calculate environmental impact
        analytics.total_carbon_reduction = self._calculate_total_carbon_reduction(sorted_snapshots)
        analytics.total_water_saved = self._calculate_total_water_saved(sorted_snapshots)
        analytics.total_waste_reduced = self._calculate_total_waste_reduced(sorted_snapshots)
        analytics.total_energy_saved = self._calculate_total_energy_saved(sorted_snapshots)
        
        # Calculate goal metrics
        analytics.goals_completed = sum(s.goals_completed for s in sorted_snapshots)
        analytics.goals_active = sorted_snapshots[-1].goals_active if sorted_snapshots else 0
        analytics.goal_success_rate = sorted_snapshots[-1].goal_completion_rate if sorted_snapshots else 0
        
        # Calculate habit metrics
        analytics.habit_consistency_avg = statistics.mean([s.average_consistency for s in sorted_snapshots])
        
        # Calculate achievement metrics
        analytics.achievements_unlocked = sorted_snapshots[-1].achievements_unlocked if sorted_snapshots else 0
        analytics.milestones_reached = sorted_snapshots[-1].milestones_reached if sorted_snapshots else 0
        
        # Identify trends
        analytics.improving_trends = self._identify_improving_trends(category_trends)
        analytics.declining_trends = self._identify_declining_trends(category_trends)
        analytics.stable_trends = self._identify_stable_trends(category_trends)
        
        # Generate insights
        analytics.key_insights = self._generate_key_insights(analytics)
        analytics.recommendations = self._generate_recommendations(analytics)
        
        return analytics
    
    def _calculate_trend(self, scores: List[float]) -> float:
        """
        Calculate trend from scores.
        """
        if len(scores) < 2:
            return 0.0
        
        n = len(scores)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(scores)
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _calculate_category_trends(self, 
                                  snapshots: List[ProgressSnapshot]) -> Dict[str, float]:
        """
        Calculate trends for each category.
        """
        trends = {}
        
        if not snapshots:
            return trends
        
        categories = ['sustainability_score', 'carbon_footprint', 'energy_usage', 
                     'water_usage', 'waste_generation', 'transportation_impact',
                     'food_impact', 'shopping_impact', 'household_performance']
        
        for category in categories:
            values = [getattr(s, category, 0.0) for s in snapshots]
            if len(values) >= 2:
                trend = self._calculate_trend(values)
                trends[category] = trend
        
        return trends
    
    def _calculate_category_averages(self, 
                                    snapshots: List[ProgressSnapshot]) -> Dict[str, float]:
        """
        Calculate average scores for each category.
        """
        averages = {}
        
        if not snapshots:
            return averages
        
        categories = ['sustainability_score', 'carbon_footprint', 'energy_usage', 
                     'water_usage', 'waste_generation', 'transportation_impact',
                     'food_impact', 'shopping_impact', 'household_performance']
        
        for category in categories:
            values = [getattr(s, category, 0.0) for s in snapshots]
            if values:
                averages[category] = statistics.mean(values)
        
        return averages
    
    def _calculate_total_carbon_reduction(self, 
                                        snapshots: List[ProgressSnapshot]) -> float:
        """
        Calculate total carbon reduction.
        """
        if len(snapshots) < 2:
            return 0.0
        
        first = snapshots[0]
        last = snapshots[-1]
        
        return max(0, first.carbon_footprint - last.carbon_footprint)
    
    def _calculate_total_water_saved(self, 
                                   snapshots: List[ProgressSnapshot]) -> float:
        """
        Calculate total water saved.
        """
        if len(snapshots) < 2:
            return 0.0
        
        first = snapshots[0]
        last = snapshots[-1]
        
        return max(0, first.water_usage - last.water_usage)
    
    def _calculate_total_waste_reduced(self, 
                                     snapshots: List[ProgressSnapshot]) -> float:
        """
        Calculate total waste reduced.
        """
        if len(snapshots) < 2:
            return 0.0
        
        first = snapshots[0]
        last = snapshots[-1]
        
        return max(0, first.waste_generation - last.waste_generation)
    
    def _calculate_total_energy_saved(self, 
                                    snapshots: List[ProgressSnapshot]) -> float:
        """
        Calculate total energy saved.
        """
        if len(snapshots) < 2:
            return 0.0
        
        first = snapshots[0]
        last = snapshots[-1]
        
        return max(0, first.energy_usage - last.energy_usage)
    
    def _identify_improving_trends(self, 
                                  trends: Dict[str, float]) -> List[str]:
        """
        Identify categories with improving trends.
        """
        improving = []
        
        for category, trend in trends.items():
            if category in ['carbon_footprint', 'energy_usage', 'water_usage', 'waste_generation']:
                if trend < -0.5:  # Negative trend means reduction
                    improving.append(category)
            else:
                if trend > 0.5:  # Positive trend means improvement
                    improving.append(category)
        
        return improving
    
    def _identify_declining_trends(self, 
                                  trends: Dict[str, float]) -> List[str]:
        """
        Identify categories with declining trends.
        """
        declining = []
        
        for category, trend in trends.items():
            if category in ['carbon_footprint', 'energy_usage', 'water_usage', 'waste_generation']:
                if trend > 0.5:  # Positive trend means increasing
                    declining.append(category)
            else:
                if trend < -0.5:  # Negative trend means decline
                    declining.append(category)
        
        return declining
    
    def _identify_stable_trends(self, 
                               trends: Dict[str, float]) -> List[str]:
        """
        Identify categories with stable trends.
        """
        stable = []
        
        for category, trend in trends.items():
            if abs(trend) <= 0.5:
                stable.append(category)
        
        return stable
    
    def _generate_key_insights(self, 
                              analytics: LongTermAnalytics) -> List[str]:
        """
        Generate key insights.
        """
        insights = []
        
        # Overall trend
        if analytics.sustainability_score_trend > 0.5:
            insights.append("Overall sustainability is showing a positive trend")
        elif analytics.sustainability_score_trend < -0.5:
            insights.append("Overall sustainability is showing a negative trend")
        else:
            insights.append("Overall sustainability is stable")
        
        # Improvement insights
        if analytics.total_improvement_percentage > 10:
            insights.append(f"Total improvement of {analytics.total_improvement_percentage:.1f}% achieved")
        elif analytics.total_improvement_percentage < -10:
            insights.append(f"Decline of {abs(analytics.total_improvement_percentage):.1f}% detected")
        
        # Category insights
        if analytics.improving_trends:
            insights.append(f"Improving trends in: {', '.join(analytics.improving_trends[:3])}")
        
        if analytics.declining_trends:
            insights.append(f"Declining trends in: {', '.join(analytics.declining_trends[:3])}")
        
        # Achievement insights
        if analytics.achievements_unlocked > 0:
            insights.append(f"{analytics.achievements_unlocked} achievements unlocked")
        
        # Goal insights
        if analytics.goal_success_rate > 80:
            insights.append(f"Excellent goal success rate of {analytics.goal_success_rate:.1f}%")
        elif analytics.goal_success_rate < 50:
            insights.append(f"Goal success rate of {analytics.goal_success_rate:.1f}% - room for improvement")
        
        return insights
    
    def _generate_recommendations(self, 
                                 analytics: LongTermAnalytics) -> List[str]:
        """
        Generate recommendations.
        """
        recommendations = []
        
        # Based on declining trends
        for category in analytics.declining_trends[:3]:
            recommendations.append(f"Focus on improving {category.replace('_', ' ').title()}")
        
        # Based on goal success rate
        if analytics.goal_success_rate < 50:
            recommendations.append("Review your goal-setting strategy - consider smaller, more achievable goals")
        
        # Based on habit consistency
        if analytics.habit_consistency_avg < 60:
            recommendations.append("Work on improving habit consistency - start with one habit at a time")
        
        # General recommendations
        if analytics.achievements_unlocked == 0:
            recommendations.append("Set specific milestones to unlock achievements and stay motivated")
        
        if analytics.total_improvement_percentage < 0:
            recommendations.append("Review your sustainability practices and identify areas for immediate improvement")
        
        return recommendations
    
    def generate_journey_summary(self, 
                                snapshots: List[ProgressSnapshot],
                                goals: List[Dict[str, Any]],
                                habits: List[Dict[str, Any]],
                                achievements: List[Dict[str, Any]]) -> JourneySummary:
        """
        Generate a summary of the user's sustainability journey.
        
        Args:
            snapshots: Progress snapshots
            goals: List of goals
            habits: List of habits
            achievements: List of achievements
        
        Returns:
            JourneySummary: Journey summary
        """
        if not snapshots:
            return JourneySummary()
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        first = sorted_snapshots[0]
        last = sorted_snapshots[-1]
        
        summary = JourneySummary(
            user_id=first.user_id,
            start_date=first.snapshot_date,
            journey_days=(last.snapshot_date - first.snapshot_date).days,
            current_sustainability_score=last.sustainability_score,
            starting_sustainability_score=first.sustainability_score,
            total_improvement=last.sustainability_score - first.sustainability_score,
            improvement_percentage=((last.sustainability_score - first.sustainability_score) / (first.sustainability_score + 0.001)) * 100,
            total_goals=len(goals),
            completed_goals=sum(1 for g in goals if g.get('status') == 'completed'),
            active_goals=sum(1 for g in goals if g.get('status') in ['active', 'in_progress']),
            total_habits=len(habits),
            active_habits=sum(1 for h in habits if h.get('status') == 'active'),
            completed_habits=sum(1 for h in habits if h.get('status') == 'completed'),
            total_achievements=len(achievements),
            total_milestones=last.milestones_reached,
            total_carbon_saved=self._calculate_total_carbon_reduction(sorted_snapshots),
            total_water_saved=self._calculate_total_water_saved(sorted_snapshots),
            total_waste_reduced=self._calculate_total_waste_reduced(sorted_snapshots)
        )
        
        # Determine overall trend
        if summary.improvement_percentage > 5:
            summary.overall_trend = 'improving'
        elif summary.improvement_percentage < -5:
            summary.overall_trend = 'declining'
        else:
            summary.overall_trend = 'stable'
        
        # Find best and weakest categories
        category_scores = {}
        for snapshot in sorted_snapshots[-3:]:  # Last 3 snapshots
            for category, score in snapshot.category_scores.items():
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)
        
        if category_scores:
            avg_scores = {cat: statistics.mean(scores) for cat, scores in category_scores.items() if scores}
            if avg_scores:
                summary.best_category = max(avg_scores, key=avg_scores.get)
                summary.weakest_category = min(avg_scores, key=avg_scores.get)
        
        # Add major milestones
        summary.major_milestones = self._extract_major_milestones(sorted_snapshots, achievements)
        
        return summary
    
    def _extract_major_milestones(self, 
                                 snapshots: List[ProgressSnapshot],
                                 achievements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract major milestones from snapshots and achievements.
        """
        milestones = []
        
        # Check for significant improvements in snapshots
        for i in range(1, len(snapshots)):
            prev = snapshots[i-1]
            curr = snapshots[i]
            
            if curr.sustainability_score - prev.sustainability_score >= 10:
                milestones.append({
                    'date': curr.snapshot_date.isoformat(),
                    'type': 'significant_improvement',
                    'description': f"Sustainability score improved by {curr.sustainability_score - prev.sustainability_score:.1f}%",
                    'score': curr.sustainability_score
                })
        
        # Add achievements
        for achievement in achievements[:5]:
            milestones.append({
                'date': achievement.get('unlocked_at', datetime.now()).isoformat(),
                'type': 'achievement',
                'description': achievement.get('title', 'Achievement unlocked'),
                'details': achievement.get('description', '')
            })
        
        return sorted(milestones, key=lambda x: x['date'])[:10]