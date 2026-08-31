"""
Sustainability Lifecycle & Long-Term Progress Management - Habit Lifecycle
Tracks complete habit lifecycle from adoption to completion.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import statistics

from lifecycle.models import (
    HabitLifecycle, LifecycleStatus, LifecycleStage,
    SustainabilityEvent, EventType, EventCategory
)

logger = logging.getLogger(__name__)


class HabitLifecycleTracker:
    """
    Tracks the complete lifecycle of sustainability habits.
    """
    
    def __init__(self):
        """Initialize the habit lifecycle tracker."""
        self.streak_thresholds = {
            'bronze': 7,
            'silver': 14,
            'gold': 30,
            'platinum': 60,
            'diamond': 100
        }
        logger.info("Habit Lifecycle Tracker initialized")
    
    def adopt_habit(self,
                   user_id: str,
                   habit_id: str,
                   habit_name: str,
                   category: str,
                   description: str = "",
                   frequency: str = "daily") -> HabitLifecycle:
        """
        Track adoption of a new habit.
        
        Args:
            user_id: User ID
            habit_id: Habit ID
            habit_name: Habit name
            category: Habit category
            description: Habit description
            frequency: Habit frequency
        
        Returns:
            HabitLifecycle: Habit lifecycle tracking
        """
        tracking = HabitLifecycle(
            user_id=user_id,
            habit_id=habit_id,
            habit_name=habit_name,
            category=category,
            description=description,
            frequency=frequency,
            status=LifecycleStatus.ACTIVE,
            stage=LifecycleStage.CREATION,
            adopted_at=datetime.now()
        )
        
        # Initialize daily performance
        tracking.daily_performance.append({
            'date': datetime.now().isoformat(),
            'completed': True,
            'streak': 1,
            'notes': 'Habit adopted'
        })
        
        tracking.streak_days = 1
        tracking.longest_streak = 1
        tracking.completion_rate = 100.0
        
        logger.info(f"Habit '{habit_name}' adopted")
        return tracking
    
    def record_performance(self,
                          tracking: HabitLifecycle,
                          completed: bool,
                          date: Optional[datetime] = None,
                          notes: str = "") -> Dict[str, Any]:
        """
        Record daily habit performance.
        
        Args:
            tracking: Habit lifecycle tracking
            completed: Whether habit was completed
            date: Date of performance
            notes: Performance notes
        
        Returns:
            Dict: Performance result
        """
        if not date:
            date = datetime.now()
        
        # Calculate streak
        if completed:
            tracking.streak_days += 1
            if tracking.streak_days > tracking.longest_streak:
                tracking.longest_streak = tracking.streak_days
            tracking.break_days = 0
            
            # Check for streak milestones
            streak_achieved = self._check_streak_milestone(tracking.streak_days)
            
            if tracking.streak_days >= 7 and tracking.streak_days % 7 == 0:
                tracking.improved_at = date
                tracking.improvement_rate = tracking.streak_days / 7
                
                if tracking.status in [LifecycleStatus.REGRESSED, LifecycleStatus.DECLINING]:
                    tracking.status = LifecycleStatus.IMPROVING
                    tracking.stage = LifecycleStage.RECOVERY
        else:
            tracking.break_days += 1
            if tracking.break_days >= 3:
                if tracking.status in [LifecycleStatus.ACTIVE, LifecycleStatus.IMPROVING]:
                    tracking.status = LifecycleStatus.REGRESSED
                    tracking.stage = LifecycleStage.DECLINE
                tracking.regressed_at = date
                tracking.broken_at = date
        
        # Update performance history
        tracking.daily_performance.append({
            'date': date.isoformat(),
            'completed': completed,
            'streak': tracking.streak_days,
            'notes': notes
        })
        
        # Calculate consistency
        tracking.consistency_score = self._calculate_consistency(tracking)
        
        # Calculate completion rate
        total_days = len(tracking.daily_performance)
        completed_days = sum(1 for d in tracking.daily_performance if d.get('completed', False))
        tracking.completion_rate = (completed_days / total_days * 100) if total_days > 0 else 0
        
        # Update weekly and monthly summaries
        self._update_weekly_summary(tracking)
        self._update_monthly_summary(tracking)
        
        return {
            'completed': completed,
            'streak_days': tracking.streak_days,
            'break_days': tracking.break_days,
            'consistency_score': tracking.consistency_score,
            'completion_rate': tracking.completion_rate,
            'streak_milestone': self._check_streak_milestone(tracking.streak_days)
        }
    
    def _check_streak_milestone(self, streak_days: int) -> Optional[str]:
        """
        Check if streak achieved a milestone.
        
        Args:
            streak_days: Current streak days
        
        Returns:
            Optional[str]: Milestone name if achieved
        """
        for milestone, days in self.streak_thresholds.items():
            if streak_days == days:
                return milestone
        return None
    
    def _calculate_consistency(self, tracking: HabitLifecycle) -> float:
        """
        Calculate habit consistency score.
        
        Args:
            tracking: Habit lifecycle tracking
        
        Returns:
            float: Consistency score (0-100)
        """
        if len(tracking.daily_performance) < 7:
            # Not enough data
            return 50.0
        
        # Use last 30 days for consistency
        days_to_consider = min(30, len(tracking.daily_performance))
        recent = tracking.daily_performance[-days_to_consider:]
        
        completed = sum(1 for d in recent if d.get('completed', False))
        
        if len(recent) > 0:
            consistency = (completed / len(recent)) * 100
            
            # Add streak bonus
            if tracking.streak_days > 0:
                streak_bonus = min(20, tracking.streak_days * 0.5)
                consistency = min(100, consistency + streak_bonus)
            
            return consistency
        
        return 50.0
    
    def _update_weekly_summary(self, tracking: HabitLifecycle) -> None:
        """
        Update weekly summary.
        """
        if len(tracking.daily_performance) < 7:
            return
        
        last_week = tracking.daily_performance[-7:]
        week_start = datetime.now() - timedelta(days=7)
        
        completed = sum(1 for d in last_week if d.get('completed', False))
        rate = (completed / len(last_week)) * 100
        
        tracking.weekly_summary.append({
            'week_start': week_start.isoformat(),
            'completion_rate': rate,
            'completed_days': completed,
            'total_days': len(last_week)
        })
        
        # Keep only last 12 weeks
        if len(tracking.weekly_summary) > 12:
            tracking.weekly_summary = tracking.weekly_summary[-12:]
    
    def _update_monthly_summary(self, tracking: HabitLifecycle) -> None:
        """
        Update monthly summary.
        """
        if len(tracking.daily_performance) < 30:
            return
        
        last_month = tracking.daily_performance[-30:]
        month_start = datetime.now() - timedelta(days=30)
        
        completed = sum(1 for d in last_month if d.get('completed', False))
        rate = (completed / len(last_month)) * 100
        
        tracking.monthly_summary.append({
            'month_start': month_start.isoformat(),
            'completion_rate': rate,
            'completed_days': completed,
            'total_days': len(last_month)
        })
        
        # Keep only last 12 months
        if len(tracking.monthly_summary) > 12:
            tracking.monthly_summary = tracking.monthly_summary[-12:]
    
    def recover_habit(self, tracking: HabitLifecycle) -> bool:
        """
        Mark habit as recovered.
        
        Args:
            tracking: Habit lifecycle tracking
        
        Returns:
            bool: True if recovered successfully
        """
        if tracking.status not in [LifecycleStatus.REGRESSED, LifecycleStatus.DECLINING]:
            return False
        
        tracking.status = LifecycleStatus.RECOVERED
        tracking.stage = LifecycleStage.RECOVERY
        tracking.recovered_at = datetime.now()
        tracking.recovery_count += 1
        tracking.last_recovery_at = datetime.now()
        
        # Calculate average recovery time
        if tracking.regressed_at:
            recovery_time = (tracking.recovered_at - tracking.regressed_at).days
            if tracking.average_recovery_time_days == 0:
                tracking.average_recovery_time_days = recovery_time
            else:
                tracking.average_recovery_time_days = (
                    tracking.average_recovery_time_days + recovery_time
                ) / 2
        
        logger.info(f"Habit '{tracking.habit_name}' recovered")
        return True
    
    def archive_habit(self, tracking: HabitLifecycle) -> bool:
        """
        Archive a habit.
        
        Args:
            tracking: Habit lifecycle tracking
        
        Returns:
            bool: True if archived successfully
        """
        if tracking.status == LifecycleStatus.ARCHIVED:
            return False
        
        tracking.status = LifecycleStatus.ARCHIVED
        tracking.stage = LifecycleStage.ARCHIVAL
        tracking.archived_at = datetime.now()
        
        logger.info(f"Habit '{tracking.habit_name}' archived")
        return True
    
    def get_habit_summary(self, tracking: HabitLifecycle) -> Dict[str, Any]:
        """
        Get summary of habit lifecycle.
        
        Args:
            tracking: Habit lifecycle tracking
        
        Returns:
            Dict: Habit summary
        """
        return {
            'habit_name': tracking.habit_name,
            'category': tracking.category,
            'status': tracking.status.value,
            'stage': tracking.stage.value,
            'adopted_at': tracking.adopted_at.isoformat(),
            'consistency_score': tracking.consistency_score,
            'streak_days': tracking.streak_days,
            'longest_streak': tracking.longest_streak,
            'break_days': tracking.break_days,
            'completion_rate': tracking.completion_rate,
            'improvement_rate': tracking.improvement_rate,
            'recovery_count': tracking.recovery_count,
            'average_recovery_time_days': tracking.average_recovery_time_days,
            'total_days': len(tracking.daily_performance),
            'frequency': tracking.frequency,
            'difficulty': tracking.difficulty,
            'related_goals': tracking.related_goals
        }
    
    def get_habit_performance_chart(self, 
                                   tracking: HabitLifecycle,
                                   days: int = 30) -> Dict[str, Any]:
        """
        Get habit performance data for charting.
        
        Args:
            tracking: Habit lifecycle tracking
            days: Number of days to include
        
        Returns:
            Dict: Chart data
        """
        recent = tracking.daily_performance[-days:]
        
        dates = []
        completions = []
        streaks = []
        notes = []
        
        for day in recent:
            dates.append(day.get('date', ''))
            completions.append(1 if day.get('completed', False) else 0)
            streaks.append(day.get('streak', 0))
            notes.append(day.get('notes', ''))
        
        return {
            'dates': dates,
            'completions': completions,
            'streaks': streaks,
            'notes': notes,
            'consistency': tracking.consistency_score,
            'completion_rate': tracking.completion_rate,
            'total_completed': sum(completions),
            'total_days': len(completions),
            'current_streak': tracking.streak_days,
            'longest_streak': tracking.longest_streak
        }
    
    def generate_habit_event(self, 
                            tracking: HabitLifecycle, 
                            event_type: str) -> Optional[SustainabilityEvent]:
        """
        Generate a sustainability event for a habit lifecycle change.
        
        Args:
            tracking: Habit lifecycle tracking
            event_type: Type of event
        
        Returns:
            Optional[SustainabilityEvent]: Generated event
        """
        event_map = {
            'adopted': EventType.HABIT_ADOPTED,
            'improved': EventType.HABIT_IMPROVED,
            'regressed': EventType.HABIT_REGRESSED,
            'broken': EventType.HABIT_BROKEN,
            'recovered': EventType.HABIT_RECOVERED,
            'streak': EventType.HABIT_STREAK
        }
        
        event_type_enum = event_map.get(event_type)
        if not event_type_enum:
            return None
        
        # Check for streak milestone
        streak_milestone = self._check_streak_milestone(tracking.streak_days) if event_type == 'streak' else None
        
        return SustainabilityEvent(
            user_id=tracking.user_id,
            event_type=event_type_enum,
            category=EventCategory.HABITS,
            title=f"{event_type_enum.value.replace('_', ' ').title()}: {tracking.habit_name}",
            description=f"Habit '{tracking.habit_name}' was {event_type}" + (f" - {streak_milestone} streak!" if streak_milestone else ""),
            impact_score=tracking.consistency_score,
            importance=4 if streak_milestone else 3,
            related_entity_id=tracking.habit_id,
            related_entity_type='habit',
            metadata={
                'habit_id': tracking.habit_id,
                'category': tracking.category,
                'streak_days': tracking.streak_days,
                'consistency': tracking.consistency_score,
                'streak_milestone': streak_milestone
            }
        )