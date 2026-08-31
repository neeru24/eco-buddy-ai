"""
Sustainability Lifecycle & Long-Term Progress Management - Progress Snapshots
Creates and manages historical progress snapshots.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import ProgressSnapshot, ComparisonResult, HistoricalInsight

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    Creates and manages progress snapshots.
    """
    
    def __init__(self):
        """Initialize the snapshot manager."""
        self.metric_weights = self._initialize_metric_weights()
        logger.info("Snapshot Manager initialized")
    
    def _initialize_metric_weights(self) -> Dict[str, float]:
        """
        Initialize weights for different metrics.
        """
        return {
            'sustainability_score': 0.25,
            'carbon_footprint': 0.20,
            'energy_usage': 0.15,
            'water_usage': 0.15,
            'waste_generation': 0.15,
            'transportation_impact': 0.10
        }
    
    def create_snapshot(self,
                       user_id: str,
                       period: str = "monthly",
                       household_id: Optional[str] = None,
                       **kwargs) -> ProgressSnapshot:
        """
        Create a progress snapshot.
        
        Args:
            user_id: User ID
            period: Snapshot period
            household_id: Optional household ID
            **kwargs: Additional metrics
        
        Returns:
            ProgressSnapshot: Created snapshot
        """
        snapshot = ProgressSnapshot(
            user_id=user_id,
            household_id=household_id,
            period=period,
            sustainability_score=kwargs.get('sustainability_score', 0.0),
            carbon_footprint=kwargs.get('carbon_footprint', 0.0),
            energy_usage=kwargs.get('energy_usage', 0.0),
            water_usage=kwargs.get('water_usage', 0.0),
            waste_generation=kwargs.get('waste_generation', 0.0),
            transportation_impact=kwargs.get('transportation_impact', 0.0),
            food_impact=kwargs.get('food_impact', 0.0),
            shopping_impact=kwargs.get('shopping_impact', 0.0),
            household_performance=kwargs.get('household_performance', 0.0),
            category_scores=kwargs.get('category_scores', {}),
            goals_completed=kwargs.get('goals_completed', 0),
            goals_active=kwargs.get('goals_active', 0),
            goals_total=kwargs.get('goals_total', 0),
            habits_active=kwargs.get('habits_active', 0),
            habits_completed=kwargs.get('habits_completed', 0),
            average_consistency=kwargs.get('average_consistency', 0.0),
            achievements_unlocked=kwargs.get('achievements_unlocked', 0),
            milestones_reached=kwargs.get('milestones_reached', 0),
            metrics_summary=kwargs.get('metrics_summary', {}),
            notes=kwargs.get('notes', '')
        )
        
        # Calculate goal completion rate
        if snapshot.goals_total > 0:
            snapshot.goal_completion_rate = (snapshot.goals_completed / snapshot.goals_total) * 100
        
        # Calculate sustainability trend
        snapshot.sustainability_trend = self._calculate_trend(snapshot)
        
        logger.info(f"Created snapshot for user {user_id} with score {snapshot.sustainability_score}")
        return snapshot
    
    def _calculate_trend(self, snapshot: ProgressSnapshot) -> float:
        """
        Calculate sustainability trend.
        """
        # Simple trend based on sustainability score changes
        if snapshot.sustainability_score > 70:
            return 5.0
        elif snapshot.sustainability_score > 50:
            return 2.0
        elif snapshot.sustainability_score > 30:
            return -2.0
        else:
            return -5.0
    
    def compare_snapshots(self, 
                         snapshot1: ProgressSnapshot,
                         snapshot2: ProgressSnapshot) -> ComparisonResult:
        """
        Compare two snapshots.
        
        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot
        
        Returns:
            ComparisonResult: Comparison results
        """
        result = ComparisonResult(
            user_id=snapshot1.user_id,
            from_date=snapshot1.snapshot_date,
            to_date=snapshot2.snapshot_date,
            comparison_type="period_comparison"
        )
        
        # Compare metrics
        metrics = [
            ('sustainability_score', 'Sustainability Score'),
            ('carbon_footprint', 'Carbon Footprint'),
            ('energy_usage', 'Energy Usage'),
            ('water_usage', 'Water Usage'),
            ('waste_generation', 'Waste Generation'),
            ('transportation_impact', 'Transportation Impact'),
            ('food_impact', 'Food Impact'),
            ('shopping_impact', 'Shopping Impact'),
            ('household_performance', 'Household Performance')
        ]
        
        total_change = 0.0
        total_metrics = 0
        
        for key, label in metrics:
            v1 = getattr(snapshot1, key, 0.0)
            v2 = getattr(snapshot2, key, 0.0)
            
            if v1 > 0 or v2 > 0:
                change = v2 - v1
                change_pct = (change / (v1 + 0.001)) * 100 if v1 > 0 else 100
                
                # Determine if improvement (lower is better for most metrics)
                is_improvement = change < 0 if key not in ['sustainability_score', 'household_performance'] else change > 0
                
                result.metric_changes[label] = {
                    'before': v1,
                    'after': v2,
                    'change': change,
                    'change_percentage': change_pct,
                    'improved': is_improvement
                }
                
                total_change += change_pct if is_improvement else -change_pct
                total_metrics += 1
        
        # Calculate overall change
        if total_metrics > 0:
            result.overall_change = total_change / total_metrics
            result.overall_change_percentage = (result.overall_change / (snapshot1.sustainability_score + 0.001)) * 100
        
        # Generate insights
        result.insights = self._generate_comparison_insights(result)
        
        # Generate summary
        result.summary = self._generate_comparison_summary(result)
        
        return result
    
    def _generate_comparison_insights(self, 
                                     comparison: ComparisonResult) -> List[str]:
        """
        Generate insights from comparison.
        """
        insights = []
        
        improved = []
        declined = []
        
        for metric, data in comparison.metric_changes.items():
            if data['improved']:
                improved.append(metric)
            else:
                declined.append(metric)
        
        if improved:
            insights.append(f"Improved in {len(improved)} areas: {', '.join(improved[:3])}")
        if declined:
            insights.append(f"Declined in {len(declined)} areas: {', '.join(declined[:3])}")
        
        if len(improved) > len(declined):
            insights.append("Overall trend is positive with more improvements than declines")
        elif len(declined) > len(improved):
            insights.append("Overall trend is negative with more declines than improvements")
        else:
            insights.append("Overall trend is stable with equal improvements and declines")
        
        return insights
    
    def _generate_comparison_summary(self, 
                                    comparison: ComparisonResult) -> str:
        """
        Generate summary of comparison.
        """
        if comparison.overall_change > 0:
            direction = "improved"
        elif comparison.overall_change < 0:
            direction = "declined"
        else:
            direction = "remained stable"
        
        return f"Overall sustainability {direction} by {abs(comparison.overall_change):.1f}%"
    
    def get_snapshot_trend(self, 
                          snapshots: List[ProgressSnapshot],
                          metric: str = 'sustainability_score') -> Dict[str, Any]:
        """
        Get trend of a metric from snapshots.
        
        Args:
            snapshots: List of snapshots
            metric: Metric to analyze
        
        Returns:
            Dict: Trend analysis
        """
        if not snapshots:
            return {'message': 'No snapshots available'}
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        values = [getattr(s, metric, 0.0) for s in sorted_snapshots]
        dates = [s.snapshot_date.strftime('%Y-%m-%d') for s in sorted_snapshots]
        periods = [s.period for s in sorted_snapshots]
        
        if len(values) < 2:
            return {
                'values': values,
                'dates': dates,
                'periods': periods,
                'trend': 'insufficient_data',
                'average': values[0] if values else 0,
                'change': 0
            }
        
        # Calculate trend
        first = values[0]
        last = values[-1]
        change = last - first
        change_pct = (change / (first + 0.001)) * 100
        
        # Determine trend direction
        if change_pct > 5:
            trend = 'improving'
        elif change_pct < -5:
            trend = 'declining'
        else:
            trend = 'stable'
        
        # Calculate additional statistics
        avg = statistics.mean(values)
        median = statistics.median(values)
        stdev = statistics.stdev(values) if len(values) > 1 else 0
        
        return {
            'values': values,
            'dates': dates,
            'periods': periods,
            'trend': trend,
            'average': avg,
            'median': median,
            'std_dev': stdev,
            'min': min(values),
            'max': max(values),
            'first': first,
            'last': last,
            'change': change,
            'change_percentage': change_pct,
            'count': len(values)
        }
    
    def get_periodic_snapshots(self,
                              snapshots: List[ProgressSnapshot],
                              period: str) -> List[ProgressSnapshot]:
        """
        Get snapshots for a specific period.
        
        Args:
            snapshots: List of snapshots
            period: Period filter
        
        Returns:
            List[ProgressSnapshot]: Filtered snapshots
        """
        if period == 'all':
            return snapshots
        
        now = datetime.now()
        cutoff = now
        
        if period == 'daily':
            cutoff = now - timedelta(days=1)
        elif period == 'weekly':
            cutoff = now - timedelta(days=7)
        elif period == 'monthly':
            cutoff = now - timedelta(days=30)
        elif period == 'quarterly':
            cutoff = now - timedelta(days=90)
        elif period == 'yearly':
            cutoff = now - timedelta(days=365)
        
        return [s for s in snapshots if s.snapshot_date >= cutoff]
    
    def calculate_improvement_percentage(self,
                                        snapshots: List[ProgressSnapshot]) -> Dict[str, float]:
        """
        Calculate improvement percentage for each metric.
        
        Args:
            snapshots: List of snapshots
        
        Returns:
            Dict: Improvement percentages
        """
        if len(snapshots) < 2:
            return {}
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        first = sorted_snapshots[0]
        last = sorted_snapshots[-1]
        
        improvements = {}
        
        metrics = [
            'sustainability_score',
            'carbon_footprint',
            'energy_usage',
            'water_usage',
            'waste_generation',
            'transportation_impact',
            'food_impact',
            'shopping_impact',
            'household_performance'
        ]
        
        for metric in metrics:
            v1 = getattr(first, metric, 0.0)
            v2 = getattr(last, metric, 0.0)
            
            if v1 > 0:
                # For negative metrics (lower is better)
                if metric in ['carbon_footprint', 'energy_usage', 'water_usage', 'waste_generation']:
                    improvement = ((v1 - v2) / v1) * 100
                else:
                    improvement = ((v2 - v1) / v1) * 100
                
                improvements[metric] = improvement
        
        return improvements
    
    def generate_historical_insights(self, 
                                    snapshots: List[ProgressSnapshot]) -> List[HistoricalInsight]:
        """
        Generate insights from historical snapshots.
        
        Args:
            snapshots: List of snapshots
        
        Returns:
            List[HistoricalInsight]: Generated insights
        """
        insights = []
        
        if len(snapshots) < 3:
            return insights
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        # Check for improvement trends
        for metric in ['sustainability_score', 'carbon_footprint', 'energy_usage']:
            values = [getattr(s, metric, 0.0) for s in sorted_snapshots]
            
            if len(values) >= 3:
                # Check if consistently improving or declining
                improving = all(values[i] < values[i-1] for i in range(1, len(values))) if metric != 'sustainability_score' else all(values[i] > values[i-1] for i in range(1, len(values)))
                declining = all(values[i] > values[i-1] for i in range(1, len(values))) if metric != 'sustainability_score' else all(values[i] < values[i-1] for i in range(1, len(values)))
                
                if improving:
                    insights.append(HistoricalInsight(
                        user_id=sorted_snapshots[0].user_id,
                        insight_type='trend',
                        title=f"Consistent Improvement in {metric.replace('_', ' ').title()}",
                        description=f"Your {metric.replace('_', ' ')} has been consistently improving over {len(values)} measurements.",
                        category=metric,
                        confidence_score=0.8,
                        priority='medium',
                        recommended_action='Continue your current approach'
                    ))
                elif declining:
                    insights.append(HistoricalInsight(
                        user_id=sorted_snapshots[0].user_id,
                        insight_type='warning',
                        title=f"Declining Trend in {metric.replace('_', ' ').title()}",
                        description=f"Your {metric.replace('_', ' ')} has been declining over {len(values)} measurements. Consider reviewing your habits.",
                        category=metric,
                        confidence_score=0.8,
                        priority='high',
                        recommended_action='Review and adjust your approach'
                    ))
        
        # Check for milestone achievements
        for snapshot in sorted_snapshots:
            if snapshot.sustainability_score >= 80:
                insights.append(HistoricalInsight(
                    user_id=snapshot.user_id,
                    insight_type='achievement',
                    title="Excellent Sustainability Score",
                    description=f"Reached a sustainability score of {snapshot.sustainability_score:.1f}%!",
                    category='overall',
                    confidence_score=1.0,
                    priority='high',
                    recommended_action='Maintain your excellent habits'
                ))
                break
        
        return insights