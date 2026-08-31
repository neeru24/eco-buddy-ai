"""
Sustainability Lifecycle & Long-Term Progress Management - Goal Lifecycle
Tracks complete goal lifecycle from creation to completion.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    GoalLifecycle, LifecycleStatus, SustainabilityEvent, EventType
)

logger = logging.getLogger(__name__)


class GoalLifecycleTracker:
    """
    Tracks the complete lifecycle of sustainability goals.
    """
    
    def __init__(self):
        """Initialize the goal lifecycle tracker."""
        logger.info("Goal Lifecycle Tracker initialized")
    
    def create_goal_tracking(self, 
                            user_id: str,
                            goal_id: str,
                            goal_name: str,
                            category: str,
                            initial_target: float) -> GoalLifecycle:
        """
        Create tracking for a new goal.
        
        Args:
            user_id: User ID
            goal_id: Goal ID
            goal_name: Goal name
            category: Goal category
            initial_target: Initial target value
        
        Returns:
            GoalLifecycle: Goal lifecycle tracking
        """
        tracking = GoalLifecycle(
            user_id=user_id,
            goal_id=goal_id,
            goal_name=goal_name,
            category=category,
            initial_target=initial_target,
            status=LifecycleStatus.ACTIVE
        )
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'created',
            'details': f'Goal "{goal_name}" created with target {initial_target}'
        })
        
        logger.info(f"Created goal tracking for {goal_name}")
        return tracking
    
    def update_goal_progress(self, 
                            tracking: GoalLifecycle,
                            progress: float) -> Dict[str, Any]:
        """
        Update goal progress.
        
        Args:
            tracking: Goal lifecycle tracking
            progress: Current progress
        
        Returns:
            Dict: Update result
        """
        old_progress = tracking.current_progress
        tracking.current_progress = progress
        tracking.modified_at = datetime.now()
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'progress_updated',
            'details': f'Progress updated from {old_progress} to {progress}'
        })
        
        # Check if completed
        if progress >= 100 and tracking.status != LifecycleStatus.COMPLETED:
            self.complete_goal(tracking)
        
        return {
            'old_progress': old_progress,
            'new_progress': progress,
            'completed': progress >= 100
        }
    
    def complete_goal(self, tracking: GoalLifecycle) -> None:
        """
        Mark goal as completed.
        
        Args:
            tracking: Goal lifecycle tracking
        """
        tracking.status = LifecycleStatus.COMPLETED
        tracking.completed_at = datetime.now()
        tracking.final_achievement = tracking.current_progress
        
        # Calculate total duration
        if tracking.created_at:
            tracking.total_duration_days = (tracking.completed_at - tracking.created_at).days
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'completed',
            'details': f'Goal "{tracking.goal_name}" completed at {tracking.current_progress}%'
        })
        
        logger.info(f"Goal {tracking.goal_name} completed")
    
    def postpone_goal(self, tracking: GoalLifecycle, reason: str = "") -> None:
        """
        Postpone a goal.
        
        Args:
            tracking: Goal lifecycle tracking
            reason: Reason for postponement
        """
        tracking.status = LifecycleStatus.POSTPONED
        tracking.postponed_at = datetime.now()
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'postponed',
            'details': f'Goal "{tracking.goal_name}" postponed. Reason: {reason}'
        })
        
        logger.info(f"Goal {tracking.goal_name} postponed")
    
    def fail_goal(self, tracking: GoalLifecycle, reason: str = "") -> None:
        """
        Mark goal as failed.
        
        Args:
            tracking: Goal lifecycle tracking
            reason: Reason for failure
        """
        tracking.status = LifecycleStatus.FAILED
        tracking.failed_at = datetime.now()
        tracking.final_achievement = tracking.current_progress
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'failed',
            'details': f'Goal "{tracking.goal_name}" failed. Reason: {reason}'
        })
        
        logger.info(f"Goal {tracking.goal_name} failed")
    
    def recover_goal(self, tracking: GoalLifecycle) -> None:
        """
        Recover a goal from failure or postponement.
        
        Args:
            tracking: Goal lifecycle tracking
        """
        tracking.status = LifecycleStatus.RECOVERED
        tracking.recovered_at = datetime.now()
        
        # Add history entry
        tracking.history_entries.append({
            'date': datetime.now().isoformat(),
            'event': 'recovered',
            'details': f'Goal "{tracking.goal_name}" recovered'
        })
        
        logger.info(f"Goal {tracking.goal_name} recovered")
    
    def get_goal_summary(self, tracking: GoalLifecycle) -> Dict[str, Any]:
        """
        Get summary of goal lifecycle.
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            Dict: Goal summary
        """
        return {
            'goal_name': tracking.goal_name,
            'category': tracking.category,
            'status': tracking.status.value,
            'created_at': tracking.created_at.isoformat(),
            'completed_at': tracking.completed_at.isoformat() if tracking.completed_at else None,
            'duration_days': tracking.total_duration_days,
            'progress': tracking.current_progress,
            'history_count': len(tracking.history_entries),
            'dependencies': tracking.dependencies
        }
    
    def get_goal_history(self, tracking: GoalLifecycle) -> List[Dict[str, Any]]:
        """
        Get detailed goal history.
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            List[Dict]: Goal history
        """
        history = []
        
        # Add key events
        events = [
            {'date': tracking.created_at, 'event': 'Goal Created', 'details': f'Target: {tracking.initial_target}'},
        ]
        
        if tracking.started_at:
            events.append({'date': tracking.started_at, 'event': 'Goal Started', 'details': ''})
        if tracking.modified_at:
            events.append({'date': tracking.modified_at, 'event': 'Goal Modified', 'details': ''})
        if tracking.completed_at:
            events.append({'date': tracking.completed_at, 'event': 'Goal Completed', 'details': ''})
        if tracking.failed_at:
            events.append({'date': tracking.failed_at, 'event': 'Goal Failed', 'details': ''})
        if tracking.postponed_at:
            events.append({'date': tracking.postponed_at, 'event': 'Goal Postponed', 'details': ''})
        if tracking.recovered_at:
            events.append({'date': tracking.recovered_at, 'event': 'Goal Recovered', 'details': ''})
        
        # Add all history entries
        for entry in tracking.history_entries:
            if 'date' in entry:
                try:
                    date = datetime.fromisoformat(entry['date'])
                    events.append({
                        'date': date,
                        'event': entry.get('event', 'Update'),
                        'details': entry.get('details', '')
                    })
                except:
                    pass
        
        # Sort by date
        events.sort(key=lambda x: x['date'])
        
        return [
            {
                'date': e['date'].strftime('%Y-%m-%d %H:%M') if isinstance(e['date'], datetime) else e['date'],
                'event': e['event'],
                'details': e['details']
            }
            for e in events
        ]
    
    def generate_goal_event(self, tracking: GoalLifecycle, event_type: str) -> Optional[SustainabilityEvent]:
        """
        Generate a sustainability event for a goal lifecycle change.
        
        Args:
            tracking: Goal lifecycle tracking
            event_type: Type of event
        
        Returns:
            Optional[SustainabilityEvent]: Generated event
        """
        event_map = {
            'created': EventType.GOAL_CREATED,
            'completed': EventType.GOAL_COMPLETED,
            'modified': EventType.GOAL_MODIFIED,
            'postponed': EventType.GOAL_POSTPONED,
            'failed': EventType.GOAL_FAILED,
            'recovered': EventType.GOAL_RECOVERED
        }
        
        event_type_enum = event_map.get(event_type)
        if not event_type_enum:
            return None
        
        return SustainabilityEvent(
            user_id=tracking.user_id,
            event_type=event_type_enum,
            title=f"{event_type_enum.value.replace('_', ' ').title()}: {tracking.goal_name}",
            description=f"Goal '{tracking.goal_name}' was {event_type}",
            category=tracking.category,
            impact_score=tracking.current_progress,
            related_entity_id=tracking.goal_id,
            related_entity_type='goal',
            importance=4 if event_type in ['completed', 'failed'] else 2
        )