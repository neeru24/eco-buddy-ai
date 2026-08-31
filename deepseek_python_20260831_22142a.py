"""
Sustainability Lifecycle & Long-Term Progress Management - Goal Lifecycle
Tracks complete goal lifecycle from creation to completion.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    GoalLifecycle, LifecycleStatus, LifecycleStage,
    SustainabilityEvent, EventType, EventCategory
)

logger = logging.getLogger(__name__)


class GoalLifecycleTracker:
    """
    Tracks the complete lifecycle of sustainability goals.
    """
    
    def __init__(self):
        """Initialize the goal lifecycle tracker."""
        self.valid_transitions = self._initialize_valid_transitions()
        logger.info("Goal Lifecycle Tracker initialized")
    
    def _initialize_valid_transitions(self) -> Dict[LifecycleStatus, List[LifecycleStatus]]:
        """
        Initialize valid status transitions.
        """
        return {
            LifecycleStatus.DRAFT: [LifecycleStatus.ACTIVE, LifecycleStatus.ARCHIVED],
            LifecycleStatus.ACTIVE: [LifecycleStatus.IN_PROGRESS, LifecycleStatus.POSTPONED, LifecycleStatus.ARCHIVED],
            LifecycleStatus.IN_PROGRESS: [LifecycleStatus.COMPLETED, LifecycleStatus.FAILED, LifecycleStatus.POSTPONED],
            LifecycleStatus.POSTPONED: [LifecycleStatus.ACTIVE, LifecycleStatus.IN_PROGRESS, LifecycleStatus.FAILED],
            LifecycleStatus.COMPLETED: [LifecycleStatus.ARCHIVED],
            LifecycleStatus.FAILED: [LifecycleStatus.RECOVERED, LifecycleStatus.ARCHIVED],
            LifecycleStatus.RECOVERED: [LifecycleStatus.ACTIVE, LifecycleStatus.IN_PROGRESS],
            LifecycleStatus.ARCHIVED: []
        }
    
    def create_goal_tracking(self, 
                            user_id: str,
                            goal_id: str,
                            goal_name: str,
                            category: str,
                            initial_target: float,
                            description: str = "") -> GoalLifecycle:
        """
        Create tracking for a new goal.
        
        Args:
            user_id: User ID
            goal_id: Goal ID
            goal_name: Goal name
            category: Goal category
            initial_target: Initial target value
            description: Goal description
        
        Returns:
            GoalLifecycle: Goal lifecycle tracking
        """
        tracking = GoalLifecycle(
            user_id=user_id,
            goal_id=goal_id,
            goal_name=goal_name,
            category=category,
            description=description,
            initial_target=initial_target,
            status=LifecycleStatus.DRAFT,
            stage=LifecycleStage.CREATION,
            created_at=datetime.now()
        )
        
        # Add progress history
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': 0.0,
            'event': 'created',
            'notes': f'Goal "{goal_name}" created with target {initial_target}'
        })
        
        logger.info(f"Created goal tracking for {goal_name}")
        return tracking
    
    def start_goal(self, tracking: GoalLifecycle) -> bool:
        """
        Start a goal (move from draft to active).
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            bool: True if started successfully
        """
        if tracking.status != LifecycleStatus.DRAFT:
            return False
        
        tracking.status = LifecycleStatus.ACTIVE
        tracking.stage = LifecycleStage.ACTIVE
        tracking.started_at = datetime.now()
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'started',
            'notes': f'Goal "{tracking.goal_name}" started'
        })
        
        logger.info(f"Started goal {tracking.goal_name}")
        return True
    
    def update_goal_progress(self, 
                            tracking: GoalLifecycle,
                            progress: float,
                            notes: str = "") -> Dict[str, Any]:
        """
        Update goal progress.
        
        Args:
            tracking: Goal lifecycle tracking
            progress: Current progress (0-100)
            notes: Progress notes
        
        Returns:
            Dict: Update result
        """
        old_progress = tracking.current_progress
        tracking.current_progress = min(100.0, max(0.0, progress))
        tracking.modified_at = datetime.now()
        
        # Update stage
        if tracking.status in [LifecycleStatus.ACTIVE, LifecycleStatus.IN_PROGRESS]:
            tracking.status = LifecycleStatus.IN_PROGRESS
            tracking.stage = LifecycleStage.ACTIVE
        
        # Add progress history
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'progress_update',
            'notes': notes or f'Progress updated from {old_progress:.1f}% to {tracking.current_progress:.1f}%'
        })
        
        # Check if completed
        if tracking.current_progress >= 100 and tracking.status != LifecycleStatus.COMPLETED:
            self.complete_goal(tracking)
        
        return {
            'old_progress': old_progress,
            'new_progress': tracking.current_progress,
            'completed': tracking.current_progress >= 100,
            'status': tracking.status.value
        }
    
    def complete_goal(self, tracking: GoalLifecycle) -> bool:
        """
        Mark goal as completed.
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            bool: True if completed successfully
        """
        if tracking.status in [LifecycleStatus.COMPLETED, LifecycleStatus.ARCHIVED]:
            return False
        
        tracking.status = LifecycleStatus.COMPLETED
        tracking.stage = LifecycleStage.COMPLETION
        tracking.completed_at = datetime.now()
        tracking.final_achievement = tracking.current_progress
        
        # Calculate duration metrics
        if tracking.started_at:
            tracking.total_duration_days = (tracking.completed_at - tracking.started_at).days
        
        # Calculate completion rate
        if tracking.total_duration_days > 0:
            tracking.completion_rate = min(100.0, (tracking.total_duration_days / 30) * 100)
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'completed',
            'notes': f'Goal "{tracking.goal_name}" completed at {tracking.current_progress}%'
        })
        
        logger.info(f"Goal {tracking.goal_name} completed")
        return True
    
    def postpone_goal(self, tracking: GoalLifecycle, reason: str = "") -> bool:
        """
        Postpone a goal.
        
        Args:
            tracking: Goal lifecycle tracking
            reason: Reason for postponement
        
        Returns:
            bool: True if postponed successfully
        """
        if tracking.status in [LifecycleStatus.COMPLETED, LifecycleStatus.ARCHIVED]:
            return False
        
        tracking.status = LifecycleStatus.POSTPONED
        tracking.stage = LifecycleStage.DECLINE
        tracking.postponed_at = datetime.now()
        
        # Update postponed duration
        if tracking.postponed_at:
            tracking.postponed_duration_days = (datetime.now() - tracking.postponed_at).days
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'postponed',
            'notes': f'Goal "{tracking.goal_name}" postponed. Reason: {reason}'
        })
        
        logger.info(f"Goal {tracking.goal_name} postponed")
        return True
    
    def fail_goal(self, tracking: GoalLifecycle, reason: str = "") -> bool:
        """
        Mark goal as failed.
        
        Args:
            tracking: Goal lifecycle tracking
            reason: Reason for failure
        
        Returns:
            bool: True if failed successfully
        """
        if tracking.status in [LifecycleStatus.COMPLETED, LifecycleStatus.ARCHIVED]:
            return False
        
        tracking.status = LifecycleStatus.FAILED
        tracking.stage = LifecycleStage.DECLINE
        tracking.failed_at = datetime.now()
        tracking.final_achievement = tracking.current_progress
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'failed',
            'notes': f'Goal "{tracking.goal_name}" failed. Reason: {reason}'
        })
        
        logger.info(f"Goal {tracking.goal_name} failed")
        return True
    
    def recover_goal(self, tracking: GoalLifecycle) -> bool:
        """
        Recover a goal from failure or postponement.
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            bool: True if recovered successfully
        """
        if tracking.status not in [LifecycleStatus.FAILED, LifecycleStatus.POSTPONED]:
            return False
        
        tracking.status = LifecycleStatus.RECOVERED
        tracking.stage = LifecycleStage.RECOVERY
        tracking.recovered_at = datetime.now()
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'recovered',
            'notes': f'Goal "{tracking.goal_name}" recovered'
        })
        
        logger.info(f"Goal {tracking.goal_name} recovered")
        return True
    
    def archive_goal(self, tracking: GoalLifecycle) -> bool:
        """
        Archive a goal.
        
        Args:
            tracking: Goal lifecycle tracking
        
        Returns:
            bool: True if archived successfully
        """
        if tracking.status == LifecycleStatus.ARCHIVED:
            return False
        
        tracking.status = LifecycleStatus.ARCHIVED
        tracking.stage = LifecycleStage.ARCHIVAL
        tracking.archived_at = datetime.now()
        
        tracking.progress_history.append({
            'date': datetime.now().isoformat(),
            'progress': tracking.current_progress,
            'event': 'archived',
            'notes': f'Goal "{tracking.goal_name}" archived'
        })
        
        logger.info(f"Goal {tracking.goal_name} archived")
        return True
    
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
            'stage': tracking.stage.value,
            'created_at': tracking.created_at.isoformat(),
            'started_at': tracking.started_at.isoformat() if tracking.started_at else None,
            'completed_at': tracking.completed_at.isoformat() if tracking.completed_at else None,
            'duration_days': tracking.total_duration_days,
            'progress': tracking.current_progress,
            'target': tracking.initial_target,
            'achievement': tracking.final_achievement,
            'completion_rate': tracking.completion_rate,
            'history_count': len(tracking.progress_history),
            'dependencies': tracking.dependencies,
            'related_habits': tracking.related_habits,
            'related_roadmaps': tracking.related_roadmaps,
            'priority': tracking.priority,
            'difficulty': tracking.difficulty
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
            {'date': tracking.created_at, 'event': 'Created', 'progress': 0.0, 'details': f'Target: {tracking.initial_target}'}
        ]
        
        if tracking.started_at:
            events.append({'date': tracking.started_at, 'event': 'Started', 'progress': 0.0, 'details': ''})
        if tracking.modified_at:
            events.append({'date': tracking.modified_at, 'event': 'Modified', 'progress': tracking.current_progress, 'details': ''})
        if tracking.completed_at:
            events.append({'date': tracking.completed_at, 'event': 'Completed', 'progress': 100.0, 'details': ''})
        if tracking.failed_at:
            events.append({'date': tracking.failed_at, 'event': 'Failed', 'progress': tracking.current_progress, 'details': ''})
        if tracking.postponed_at:
            events.append({'date': tracking.postponed_at, 'event': 'Postponed', 'progress': tracking.current_progress, 'details': ''})
        if tracking.recovered_at:
            events.append({'date': tracking.recovered_at, 'event': 'Recovered', 'progress': tracking.current_progress, 'details': ''})
        if tracking.archived_at:
            events.append({'date': tracking.archived_at, 'event': 'Archived', 'progress': tracking.current_progress, 'details': ''})
        
        # Add progress history entries
        for entry in tracking.progress_history:
            try:
                date = datetime.fromisoformat(entry['date']) if isinstance(entry['date'], str) else entry['date']
                events.append({
                    'date': date,
                    'event': entry.get('event', 'Progress Update'),
                    'progress': entry.get('progress', 0.0),
                    'details': entry.get('notes', '')
                })
            except:
                pass
        
        # Sort by date
        events.sort(key=lambda x: x['date'])
        
        return [
            {
                'date': e['date'].strftime('%Y-%m-%d %H:%M') if isinstance(e['date'], datetime) else e['date'],
                'event': e['event'],
                'progress': e['progress'],
                'details': e['details']
            }
            for e in events
        ]
    
    def generate_goal_event(self, 
                           tracking: GoalLifecycle, 
                           event_type: str) -> Optional[SustainabilityEvent]:
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
            'started': EventType.GOAL_PROGRESS,
            'completed': EventType.GOAL_COMPLETED,
            'modified': EventType.GOAL_MODIFIED,
            'postponed': EventType.GOAL_POSTPONED,
            'failed': EventType.GOAL_FAILED,
            'recovered': EventType.GOAL_RECOVERED,
            'progress': EventType.GOAL_PROGRESS
        }
        
        event_type_enum = event_map.get(event_type)
        if not event_type_enum:
            return None
        
        return SustainabilityEvent(
            user_id=tracking.user_id,
            event_type=event_type_enum,
            category=EventCategory.GOALS,
            title=f"{event_type_enum.value.replace('_', ' ').title()}: {tracking.goal_name}",
            description=f"Goal '{tracking.goal_name}' was {event_type}",
            impact_score=tracking.current_progress,
            importance=4 if event_type in ['completed', 'failed'] else 3,
            related_entity_id=tracking.goal_id,
            related_entity_type='goal',
            metadata={
                'goal_id': tracking.goal_id,
                'category': tracking.category,
                'progress': tracking.current_progress,
                'target': tracking.initial_target
            }
        )