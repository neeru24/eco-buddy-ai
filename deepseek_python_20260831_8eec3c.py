"""
Sustainability Lifecycle & Long-Term Progress Management - Habit Lifecycle
Tracks complete habit lifecycle from adoption to completion.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import statistics

from lifecycle.models import (
    HabitLifecycle, LifecycleStatus, SustainabilityEvent, EventType
)

logger = logging.getLogger(__name__)


class HabitLifecycleTracker:
    """
    Tracks the complete lifecycle of sustainability habits.
    """
    
    def __init__(self):
        """Initialize the habit lifecycle tracker."""
        logger.info("Habit Lifecycle Tracker initialized")
    
    def adopt_habit(self,
                   user_id: str,
                   habit_id: str,
                   habit_name: str,
                   category: str) -> HabitLifecycle:
        """
        Track adoption of a new habit.
        
        Args:
            user_id: User ID
            habit_id: Habit ID
            habit_name: Habit name
            category: Habit category
        
        Returns:
            HabitLifecycle: Habit lifecycle tracking
        """
        tracking = HabitLifecycle(
            user_id=user_id,
            habit_id=habit_id,
            habit_name=habit_name,
            category=category,
            status=LifecycleStatus.ACTIVE,
            adopted_at=datetime.now()
        )
        
        # Initialize daily performance
        tracking.daily_performance.append({
            'date': datetime.now().isoformat(),
            'completed': True,
            'streak': 1
        })
        
        tracking.streak_days = 1
        tracking.longest_streak = 1
        
        logger.info(f"Habit '{habit_name}' adopted")
        return tracking
    
    def record_daily_performance(self,
                                tracking: HabitLifecycle,
                                completed: bool,
                                date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Record daily habit performance.
        
        Args:
            tracking: Habit lifecycle tracking
            completed: Whether habit was completed
            date: Date of performance
        
        Returns:
            Dict: Performance result
        """
        if not date:
            date = datetime.now()
        
        # Update daily performance
        tracking.daily_performance.append({
            'date': date.isoformat(),
            'completed': completed,
            'streak': tracking.streak_days + 1 if completed else 0
        })
        
        # Update streak
        if completed:
            tracking.streak_days += 1
            if tracking.streak_days > tracking.longest_streak:
                tracking.longest_streak = tracking.streak_days
            tracking.break_days = 0
            
            # Check for improvement
            if tracking.streak_days >= 7 and tracking.streak_days % 7 == 0:
                tracking.improved_at = date
                tracking.improvement_rate = tracking.streak_days / 7
                
                # Update status
                if tracking.status in [LifecycleStatus.REGRESSED, LifecycleStatus.DECLINING]:
                    tracking.status = LifecycleStatus.IMPROVING
        else:
            tracking.break_days += 1
            if tracking.break_days >= 3:
                if tracking.status == LifecycleStatus.ACTIVE:
                    tracking.status = LifecycleStatus.REGRESSED
                tracking.regressed_at = date
                tracking.broken_at = date
        
        # Calculate consistency
        tracking.consistency_score = self._calculate_consistency(tracking)
        
        return {
            'completed': completed,
            'streak_days': tracking.streak_days,
            'break_days': tracking.break_days,
            'consistency_score': tracking.consistency_score
        }
    
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
        
        last_30 = tracking.daily_performance[-30:]
        completed = sum(1 for d in last_30 if d.get('completed', False))
        
        if len(last_30) > 0:
            consistency = (completed / len(last_30)) * 100
            return min(100, consistency)
        
        return 50.0
    
    def recover_habit(self, tracking: HabitLifecycle) -> None:
        """
        Mark habit as recovered.
        
        Args:
            tracking: Habit lifecycle tracking
        """
        tracking.status = LifecycleStatus.RECOVERED
        tracking.recovered_at = datetime.now()
        tracking.recovery_count += 1
        
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
            'adopted_at': tracking.adopted_at.isoformat(),
            'consistency_score': tracking.consistency_score,
            'streak_days': tracking.streak_days,
            'longest_streak': tracking.longest_streak,
            'break_days': tracking.break_days,
            'improvement_rate': tracking.improvement_rate,
            'recovery_count': tracking.recovery_count,
            'average_recovery_time_days': tracking.average_recovery_time_days,
            'total_days': len(tracking.daily_performance)
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
        
        for day in recent:
            dates.append(day.get('date', ''))
            completions.append(1 if day.get('completed', False) else 0)
            streaks.append(day.get('streak', 0))
        
        return {
            'dates': dates,
            'completions': completions,
            'streaks': streaks,
            'consistency': tracking.consistency_score,
            'total_completed': sum(completions),
            'total_days': len(completions),
            'completion_rate': (sum(completions) / len(completions) * 100) if completions else 0
        }
    
    def get_weekly_summary(self, tracking: HabitLifecycle) -> List[Dict[str, Any]]:
        """
        Get weekly summary of habit performance.
        
        Args:
            tracking: Habit lifecycle tracking
        
        Returns:
            List[Dict]: Weekly summaries
        """
        if len(tracking.daily_performance) < 7:
            return []
        
        weekly = []
        week_data = []
        week_start = None
        
        for day in tracking.daily_performance:
            date = datetime.fromisoformat(day['date']) if isinstance(day['date'], str) else day['date']
            week_key = date.isocalendar()[1]
            
            if week_start is None:
                week_start = week_key
            
            if week_key != week_start:
                # Process week
                if week_data:
                    weekly.append({
                        'week': f"Week {week_start}",
                        'completion_rate': sum(1 for d in week_data if d.get('completed', False)) / len(week_data) * 100,
                        'days': len(week_data),
                        'streak': max(d.get('streak', 0) for d in week_data)
                    })
                week_data = []
                week_start = week_key
            
            week_data.append(day)
        
        # Process last week
        if week_data:
            weekly.append({
                'week': f"Week {week_start}",
                'completion_rate': sum(1 for d in week_data if d.get('completed', False)) / len(week_data) * 100,
                'days': len(week_data),
                'streak': max(d.get('streak', 0) for d in week_data)
            })
        
        return weekly
    
    def generate_habit_event(self, tracking: HabitLifecycle, event_type: str) -> Optional[SustainabilityEvent]:
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
            'recovered': EventType.HABIT_RECOVERED
        }
        
        event_type_enum = event_map.get(event_type)
        if not event_type_enum:
            return None
        
        return SustainabilityEvent(
            user_id=tracking.user_id,
            event_type=event_type_enum,
            title=f"{event_type_enum.value.replace('_', ' ').title()}: {tracking.habit_name}",
            description=f"Habit '{tracking.habit_name}' was {event_type}",
            category=tracking.category,
            impact_score=tracking.consistency_score,
            related_entity_id=tracking.habit_id,
            related_entity_type='habit',
            importance=3 if event_type in ['adopted', 'improved'] else 2
        )