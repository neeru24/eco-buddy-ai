"""
Sustainability Lifecycle & Long-Term Progress Management - Progress Snapshots
Creates and manages historical progress snapshots.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import statistics

from lifecycle.models import ProgressSnapshot

logger = logging.getLogger(__name__)


class SnapshotManager:
    """
    Creates and manages progress snapshots.
    """
    
    def __init__(self):
        """Initialize the snapshot manager."""
        logger.info("Snapshot Manager initialized")
    
    def create_snapshot(self,
                       user_id: str,
                       sustainability_score: float,
                       period: str = "daily",
                       household_id: Optional[str] = None,
                       **kwargs) -> ProgressSnapshot:
        """
        Create a progress snapshot.
        
        Args:
            user_id: User ID
            sustainability_score: Current sustainability score
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
            sustainability_score=sustainability_score,
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
            notes=kwargs.get('notes', '')
        )
        
        logger.info(f"Created snapshot for user {user_id} with score {sustainability_score}")
        return snapshot
    
    def compare_snapshots(self, 
                         snapshot1: ProgressSnapshot,
                         snapshot2: ProgressSnapshot) -> Dict[str, Any]:
        """
        Compare two snapshots.
        
        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot
        
        Returns:
            Dict: Comparison results
        """
        comparison = {
            'period_between': (snapshot2.snapshot_date - snapshot1.snapshot_date).days,
            'score_change': snapshot2.sustainability_score - snapshot1.sustainability_score,
            'score_change_percentage': ((snapshot2.sustainability_score - snapshot1.sustainability_score) / 
                                       (snapshot1.sustainability_score + 0.001) * 100),
            'metrics': {}
        }
        
        # Compare all metrics
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
        
        for key, label in metrics:
            v1 = getattr(snapshot1, key, 0.0)
            v2 = getattr(snapshot2, key, 0.0)
            
            if v1 or v2:
                change = v2 - v1
                change_pct = (change / (v1 + 0.001)) * 100
                
                comparison['metrics'][label] = {
                    'before': v1,
                    'after': v2,
                    'change': change,
                    'change_percentage': change_pct,
                    'improved': change < 0 if key not in ['sustainability_score', 'household_performance'] else change > 0
                }
        
        return comparison
    
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
        dates = [s.snapshot_date.isoformat() for s in sorted_snapshots]
        
        if len(values) < 2:
            return {
                'values': values,
                'dates': dates,
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
        
        return {
            'values': values,
            'dates': dates,
            'trend': trend,
            'average': statistics.mean(values),
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
    
    def get_category_evolution(self, 
                              snapshots: List[ProgressSnapshot]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get evolution of category scores over time.
        
        Args:
            snapshots: List of snapshots
        
        Returns:
            Dict: Category evolution data
        """
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        # Collect all categories
        all_categories = set()
        for snapshot in sorted_snapshots:
            all_categories.update(snapshot.category_scores.keys())
        
        evolution = {}
        
        for category in all_categories:
            data = []
            for snapshot in sorted_snapshots:
                score = snapshot.category_scores.get(category, 0.0)
                data.append({
                    'date': snapshot.snapshot_date.isoformat(),
                    'score': score
                })
            evolution[category] = data
        
        return evolution
    
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