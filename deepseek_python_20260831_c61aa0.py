"""
Sustainability Analytics & Forecasting Engine - Goal Trajectory
Analyzes goal trajectories and progress.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from analytics.models import (
    GoalTrajectory, HistoricalData, AnalyticsMetric
)

logger = logging.getLogger(__name__)


class GoalTrajectoryAnalyzer:
    """
    Analyzes goal trajectories and progress.
    """
    
    def __init__(self):
        """Initialize the goal trajectory analyzer."""
        self.risk_thresholds = {
            'on_track': 0.8,
            'at_risk': 0.5,
            'off_track': 0.3
        }
        logger.info("Goal Trajectory Analyzer initialized")
    
    def analyze_goal_trajectory(self,
                               goal_id: str,
                               goal_name: str,
                               category: str,
                               target_value: float,
                               current_value: float,
                               start_value: float,
                               start_date: datetime,
                               target_date: datetime,
                               historical_data: List[HistoricalData]) -> GoalTrajectory:
        """
        Analyze goal trajectory.
        
        Args:
            goal_id: Goal ID
            goal_name: Goal name
            category: Goal category
            target_value: Target value
            current_value: Current value
            start_value: Start value
            start_date: Start date
            target_date: Target date
            historical_data: Historical data
        
        Returns:
            GoalTrajectory: Trajectory analysis
        """
        trajectory = GoalTrajectory(
            user_id=historical_data[0].user_id if historical_data else "",
            goal_id=goal_id,
            goal_name=goal_name,
            category=category,
            target_value=target_value,
            current_value=current_value,
            start_value=start_value
        )
        
        # Calculate progress
        total_required = target_value - start_value
        progress_achieved = current_value - start_value
        
        if total_required > 0:
            trajectory.progress_percentage = (progress_achieved / total_required) * 100
        else:
            trajectory.progress_percentage = 100 if current_value >= target_value else 0
        
        # Calculate expected progress
        days_elapsed = (datetime.now() - start_date).days
        total_days = (target_date - start_date).days if target_date > start_date else 1
        
        if total_days > 0:
            trajectory.expected_progress = (days_elapsed / total_days) * 100
        else:
            trajectory.expected_progress = 100
        
        # Calculate progress gap
        trajectory.progress_gap = trajectory.progress_percentage - trajectory.expected_progress
        
        # Determine if on track
        if trajectory.progress_gap >= -10:
            trajectory.is_on_track = True
        else:
            trajectory.is_on_track = False
        
        # Calculate remaining days
        trajectory.days_remaining = max(0, (target_date - datetime.now()).days)
        
        # Estimate completion date
        if trajectory.progress_percentage > 0 and trajectory.days_remaining > 0:
            days_needed = (trajectory.days_remaining * (100 - trajectory.progress_percentage)) / trajectory.progress_percentage
            trajectory.estimated_completion = datetime.now() + timedelta(days=days_needed)
        
        # Assess risk
        trajectory.risk_level = self._assess_risk(trajectory)
        trajectory.risk_factors = self._identify_risk_factors(trajectory, historical_data)
        
        # Generate recommendations
        trajectory.recommendations = self._generate_recommendations(trajectory)
        
        # Add history
        trajectory.trajectory_history = self._generate_trajectory_history(
            historical_data, start_date, target_date, target_value
        )
        
        trajectory.last_updated = datetime.now()
        
        return trajectory
    
    def _assess_risk(self, trajectory: GoalTrajectory) -> str:
        """
        Assess risk level for a goal.
        """
        if trajectory.is_on_track and trajectory.progress_gap > 5:
            return "low"
        elif trajectory.is_on_track:
            return "medium"
        elif trajectory.progress_gap > -20:
            return "high"
        else:
            return "critical"
    
    def _identify_risk_factors(self, trajectory: GoalTrajectory, historical_data: List[HistoricalData]) -> List[str]:
        """
        Identify risk factors.
        """
        factors = []
        
        if trajectory.risk_level in ['high', 'critical']:
            factors.append("Progress is significantly behind schedule")
        
        if trajectory.days_remaining < 7 and trajectory.progress_percentage < 50:
            factors.append("Insufficient time remaining for current progress rate")
        
        if len(historical_data) < 3:
            factors.append("Limited historical data for trajectory analysis")
        else:
            # Check for declining trend
            recent_values = [d.value for d in historical_data[-5:]]
            if len(recent_values) >= 2 and recent_values[-1] < recent_values[0]:
                factors.append("Recent performance is declining")
        
        return factors
    
    def _generate_recommendations(self, trajectory: GoalTrajectory) -> List[str]:
        """
        Generate recommendations based on trajectory.
        """
        recommendations = []
        
        if trajectory.risk_level == 'critical':
            recommendations.append("Immediate action required to get back on track")
            recommendations.append("Consider breaking down the goal into smaller milestones")
        
        if trajectory.risk_level == 'high':
            recommendations.append("Increase efforts to accelerate progress")
            recommendations.append("Review and adjust your approach")
        
        if trajectory.progress_gap < -30:
            recommendations.append("Consider extending the goal timeline")
            recommendations.append("Re-evaluate if the goal is still realistic")
        
        if trajectory.progress_gap > 10:
            recommendations.append("Great progress! Consider setting more ambitious targets")
        
        if trajectory.days_remaining < 14:
            recommendations.append("Focus on completing the goal within the remaining time")
        
        return recommendations
    
    def _generate_trajectory_history(self,
                                   historical_data: List[HistoricalData],
                                   start_date: datetime,
                                   target_date: datetime,
                                   target_value: float) -> List[Dict[str, Any]]:
        """
        Generate trajectory history from historical data.
        """
        history = []
        
        if not historical_data:
            return history
        
        sorted_data = sorted(historical_data, key=lambda x: x.timestamp)
        
        total_days = (target_date - start_date).days if target_date > start_date else 1
        
        for point in sorted_data:
            progress = ((point.value - start_date.timestamp) / (target_value - start_date.timestamp)) * 100 if target_value > start_date else 0
            days_elapsed = (point.timestamp - start_date).days
            expected_progress = (days_elapsed / total_days) * 100 if total_days > 0 else 0
            
            history.append({
                'date': point.timestamp.isoformat(),
                'value': point.value,
                'progress': progress,
                'expected_progress': expected_progress,
                'gap': progress - expected_progress
            })
        
        return history
    
    def get_trajectory_status(self, trajectory: GoalTrajectory) -> Dict[str, Any]:
        """
        Get trajectory status summary.
        
        Args:
            trajectory: Goal trajectory
        
        Returns:
            Dict: Status summary
        """
        return {
            'goal_name': trajectory.goal_name,
            'status': 'on_track' if trajectory.is_on_track else 'off_track',
            'risk_level': trajectory.risk_level,
            'progress_percentage': trajectory.progress_percentage,
            'expected_progress': trajectory.expected_progress,
            'progress_gap': trajectory.progress_gap,
            'days_remaining': trajectory.days_remaining,
            'estimated_completion': trajectory.estimated_completion.isoformat() if trajectory.estimated_completion else None,
            'target_date': trajectory.target_date.isoformat() if trajectory.target_date else None,
            'risk_factors': trajectory.risk_factors,
            'recommendations': trajectory.recommendations
        }
    
    def compare_goal_trajectories(self, trajectories: List[GoalTrajectory]) -> Dict[str, Any]:
        """
        Compare multiple goal trajectories.
        
        Args:
            trajectories: List of goal trajectories
        
        Returns:
            Dict: Comparison results
        """
        if not trajectories:
            return {'message': 'No trajectories to compare'}
        
        on_track = sum(1 for t in trajectories if t.is_on_track)
        at_risk = sum(1 for t in trajectories if t.risk_level in ['high', 'critical'])
        
        avg_progress = sum(t.progress_percentage for t in trajectories) / len(trajectories)
        avg_gap = sum(t.progress_gap for t in trajectories) / len(trajectories)
        
        return {
            'total_goals': len(trajectories),
            'on_track': on_track,
            'at_risk': at_risk,
            'average_progress': avg_progress,
            'average_gap': avg_gap,
            'best_performing': max(trajectories, key=lambda t: t.progress_percentage).goal_name,
            'worst_performing': min(trajectories, key=lambda t: t.progress_percentage).goal_name,
            'trajectories': [self.get_trajectory_status(t) for t in trajectories]
        }
    
    def get_goal_completion_forecast(self, trajectory: GoalTrajectory) -> Dict[str, Any]:
        """
        Get goal completion forecast.
        
        Args:
            trajectory: Goal trajectory
        
        Returns:
            Dict: Completion forecast
        """
        if trajectory.progress_percentage >= 100:
            return {
                'status': 'already_completed',
                'message': 'Goal has already been completed'
            }
        
        if trajectory.progress_percentage <= 0:
            return {
                'status': 'not_started',
                'message': 'No progress has been made on this goal'
            }
        
        # Calculate completion date based on current rate
        if trajectory.days_remaining > 0 and trajectory.progress_percentage > 0:
            days_needed = (trajectory.days_remaining * (100 - trajectory.progress_percentage)) / trajectory.progress_percentage
            projected_completion = datetime.now() + timedelta(days=days_needed)
            
            # Determine if likely to complete on time
            if days_needed <= trajectory.days_remaining:
                likelihood = "likely"
            elif days_needed <= trajectory.days_remaining * 1.5:
                likelihood = "possible"
            else:
                likelihood = "unlikely"
        else:
            projected_completion = None
            likelihood = "unknown"
        
        return {
            'status': 'in_progress',
            'projected_completion': projected_completion.isoformat() if projected_completion else None,
            'days_needed': days_needed if 'days_needed' in locals() else None,
            'days_remaining': trajectory.days_remaining,
            'likelihood': likelihood,
            'progress_rate': trajectory.progress_percentage / max(1, (datetime.now() - trajectory.start_date).days),
            'needed_rate': (100 - trajectory.progress_percentage) / max(1, trajectory.days_remaining)
        }