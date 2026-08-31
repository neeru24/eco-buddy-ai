"""
Sustainability Gamification & Challenge Platform - Streak System
Manages user streaks for daily activities and challenges.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import Streak, StreakType, GamificationEvent

logger = logging.getLogger(__name__)


class StreakSystem:
    """
    Manages user streaks.
    """
    
    def __init__(self):
        """Initialize the streak system."""
        self.streak_thresholds = self._initialize_streak_thresholds()
        self.streak_milestones = self._initialize_streak_milestones()
        logger.info("Streak System initialized")
    
    def _initialize_streak_thresholds(self) -> Dict[int, int]:
        """
        Initialize streak thresholds for recovery.
        """
        return {
            7: 1,    # 1 day recovery for 7-day streak
            14: 2,   # 2 days recovery for 14-day streak
            30: 3,   # 3 days recovery for 30-day streak
            60: 5,   # 5 days recovery for 60-day streak
            100: 7   # 7 days recovery for 100-day streak
        }
    
    def _initialize_streak_milestones(self) -> Dict[int, str]:
        """
        Initialize streak milestones.
        """
        return {
            1: "First Day",
            3: "Three-Day Streak",
            5: "Five-Day Streak",
            7: "One Week Streak",
            10: "Ten-Day Streak",
            14: "Two Week Streak",
            21: "Three Week Streak",
            30: "One Month Streak",
            60: "Two Month Streak",
            90: "Three Month Streak",
            100: "Century Streak",
            180: "Half Year Streak",
            365: "One Year Streak"
        }
    
    def update_streak(self,
                     streak: Streak,
                     completed: bool,
                     date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Update a user's streak.
        
        Args:
            streak: Streak object
            completed: Whether activity was completed
            date: Date of activity
        
        Returns:
            Dict: Streak update result
        """
        if not date:
            date = datetime.now()
        
        old_streak = streak.current_streak
        old_longest = streak.longest_streak
        
        # Check if the user already updated today
        if streak.last_activity_date:
            last_date = streak.last_activity_date.date()
            today = date.date()
            
            if last_date == today:
                return {
                    'updated': False,
                    'message': 'Already updated today',
                    'current_streak': streak.current_streak
                }
            
            # Check if missed a day
            days_diff = (today - last_date).days
            
            if days_diff > 1:
                # Missed a day
                streak.missed_days += 1
                
                # Reset streak if recovery period passed
                recovery_days = self._get_recovery_days(streak.current_streak)
                if days_diff > recovery_days + 1:
                    streak.current_streak = 0
                    streak.current_start_date = None
        
        # Update streak
        if completed:
            if streak.current_streak == 0:
                streak.current_start_date = date
            streak.current_streak += 1
            streak.total_days += 1
            
            # Check for new longest streak
            if streak.current_streak > streak.longest_streak:
                streak.longest_streak = streak.current_streak
                streak.longest_start_date = streak.current_start_date
                streak.longest_end_date = date
        else:
            # Activity not completed, but we don't reset immediately
            # because we use the check above to detect missed days
            pass
        
        # Update last activity date
        streak.last_activity_date = date
        streak.updated_at = datetime.now()
        
        # Add to history
        streak.streak_history.append({
            'date': date.isoformat(),
            'streak': streak.current_streak,
            'completed': completed
        })
        
        # Check for milestone
        milestone = self._get_streak_milestone(streak.current_streak)
        
        return {
            'updated': True,
            'old_streak': old_streak,
            'new_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'milestone': milestone,
            'reached_new_longest': streak.current_streak > old_longest,
            'current_start_date': streak.current_start_date.isoformat() if streak.current_start_date else None
        }
    
    def _get_recovery_days(self, streak_days: int) -> int:
        """
        Get recovery days for a streak.
        """
        for threshold, recovery in sorted(self.streak_thresholds.items(), reverse=True):
            if streak_days >= threshold:
                return recovery
        return 0
    
    def _get_streak_milestone(self, streak_days: int) -> Optional[str]:
        """
        Get milestone for a streak.
        """
        if streak_days in self.streak_milestones:
            return self.streak_milestones[streak_days]
        return None
    
    def get_streak_summary(self, streak: Streak) -> Dict[str, Any]:
        """
        Get streak summary.
        
        Args:
            streak: Streak object
        
        Returns:
            Dict: Streak summary
        """
        current_milestone = self._get_streak_milestone(streak.current_streak)
        next_milestone = self._get_next_milestone(streak.current_streak)
        
        return {
            'type': streak.streak_type.value,
            'name': streak.name,
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'current_milestone': current_milestone,
            'next_milestone': next_milestone,
            'total_days': streak.total_days,
            'missed_days': streak.missed_days,
            'recovery_count': streak.recovery_count,
            'current_start_date': streak.current_start_date.isoformat() if streak.current_start_date else None,
            'last_activity_date': streak.last_activity_date.isoformat() if streak.last_activity_date else None,
            'is_active': streak.current_streak > 0
        }
    
    def _get_next_milestone(self, current_streak: int) -> Optional[Dict[str, Any]]:
        """
        Get next milestone.
        """
        sorted_milestones = sorted(self.streak_milestones.items())
        
        for days, milestone in sorted_milestones:
            if days > current_streak:
                return {
                    'days': days,
                    'milestone': milestone,
                    'days_remaining': days - current_streak
                }
        
        return None
    
    def get_streak_history_by_period(self, streak: Streak, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get streak history for a period.
        
        Args:
            streak: Streak object
            days: Number of days to include
        
        Returns:
            List[Dict]: Streak history
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return [h for h in streak.streak_history if h['date'] >= cutoff_str]
    
    def check_streak_recovery(self, streak: Streak) -> Dict[str, Any]:
        """
        Check if a streak can be recovered.
        
        Args:
            streak: Streak object
        
        Returns:
            Dict: Recovery information
        """
        if not streak.last_activity_date:
            return {'can_recover': False, 'days_missed': 0}
        
        days_missed = (datetime.now() - streak.last_activity_date).days - 1
        
        if days_missed <= 0:
            return {'can_recover': False, 'days_missed': 0}
        
        recovery_days = self._get_recovery_days(streak.current_streak)
        
        return {
            'can_recover': days_missed <= recovery_days,
            'days_missed': days_missed,
            'recovery_days': recovery_days,
            'days_remaining': max(0, recovery_days - days_missed)
        }
    
    def recover_streak(self, streak: Streak) -> bool:
        """
        Recover a streak.
        
        Args:
            streak: Streak object
        
        Returns:
            bool: True if recovered successfully
        """
        recovery_info = self.check_streak_recovery(streak)
        
        if not recovery_info['can_recover']:
            return False
        
        streak.recovery_count += 1
        streak.current_streak += 1
        streak.updated_at = datetime.now()
        
        return True
    
    def reset_streak(self, streak: Streak) -> Dict[str, Any]:
        """
        Reset a streak.
        
        Args:
            streak: Streak object
        
        Returns:
            Dict: Reset result
        """
        old_streak = streak.current_streak
        
        streak.current_streak = 0
        streak.current_start_date = None
        streak.updated_at = datetime.now()
        
        return {
            'old_streak': old_streak,
            'new_streak': 0,
            'reset': True
        }