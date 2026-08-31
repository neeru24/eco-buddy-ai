"""
Sustainability Gamification & Challenge Platform - Progress Tracker
Tracks challenge progress, completion history, and XP history.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from gamification.models import (
    Challenge, ChallengeProgress, ChallengeStatus, UserXP,
    GamificationEvent, Streak
)

logger = logging.getLogger(__name__)


class ProgressTracker:
    """
    Tracks progress for challenges and gamification.
    """
    
    def __init__(self):
        """Initialize the progress tracker."""
        logger.info("Progress Tracker initialized")
    
    def create_challenge_progress(self,
                                 user_id: str,
                                 challenge: Challenge) -> ChallengeProgress:
        """
        Create progress tracking for a challenge.
        
        Args:
            user_id: User ID
            challenge: Challenge to track
        
        Returns:
            ChallengeProgress: Progress tracking
        """
        progress = ChallengeProgress(
            user_id=user_id,
            challenge_id=challenge.id,
            challenge_title=challenge.title,
            target_value=challenge.target_value,
            status=ChallengeStatus.IN_PROGRESS,
            started_at=datetime.now()
        )
        
        # Add initial progress entry
        progress.progress_history.append({
            'date': datetime.now().isoformat(),
            'value': 0.0,
            'percentage': 0.0,
            'event': 'started'
        })
        
        logger.info(f"Created progress tracking for challenge: {challenge.title}")
        return progress
    
    def update_challenge_progress(self,
                                 progress: ChallengeProgress,
                                 current_value: float,
                                 notes: str = "") -> Dict[str, Any]:
        """
        Update challenge progress.
        
        Args:
            progress: Challenge progress
            current_value: Current progress value
            notes: Progress notes
        
        Returns:
            Dict: Progress update result
        """
        old_value = progress.current_value
        old_percentage = progress.progress_percentage
        
        progress.current_value = min(progress.target_value, current_value)
        progress.progress_percentage = (progress.current_value / progress.target_value * 100) if progress.target_value > 0 else 0
        progress.last_updated = datetime.now()
        
        # Add to history
        progress.progress_history.append({
            'date': datetime.now().isoformat(),
            'value': progress.current_value,
            'percentage': progress.progress_percentage,
            'event': 'updated',
            'notes': notes
        })
        
        # Check if completed
        if progress.progress_percentage >= 100 and progress.status != ChallengeStatus.COMPLETED:
            progress.status = ChallengeStatus.COMPLETED
            progress.completed_at = datetime.now()
            
            # Add completion event
            progress.progress_history.append({
                'date': datetime.now().isoformat(),
                'value': progress.current_value,
                'percentage': 100.0,
                'event': 'completed',
                'notes': 'Challenge completed!'
            })
        
        return {
            'old_value': old_value,
            'new_value': progress.current_value,
            'old_percentage': old_percentage,
            'new_percentage': progress.progress_percentage,
            'completed': progress.progress_percentage >= 100,
            'status': progress.status.value
        }
    
    def get_challenge_progress_summary(self, progress: ChallengeProgress) -> Dict[str, Any]:
        """
        Get challenge progress summary.
        
        Args:
            progress: Challenge progress
        
        Returns:
            Dict: Progress summary
        """
        return {
            'challenge_title': progress.challenge_title,
            'current_value': progress.current_value,
            'target_value': progress.target_value,
            'progress_percentage': progress.progress_percentage,
            'status': progress.status.value,
            'started_at': progress.started_at.isoformat(),
            'completed_at': progress.completed_at.isoformat() if progress.completed_at else None,
            'last_updated': progress.last_updated.isoformat(),
            'history_count': len(progress.progress_history),
            'points_earned': progress.points_earned,
            'xp_earned': progress.xp_earned
        }
    
    def get_completion_history(self,
                              progress_list: List[ChallengeProgress]) -> List[Dict[str, Any]]:
        """
        Get completion history from progress list.
        
        Args:
            progress_list: List of challenge progress
        
        Returns:
            List[Dict]: Completion history
        """
        completed = [p for p in progress_list if p.status == ChallengeStatus.COMPLETED]
        completed.sort(key=lambda p: p.completed_at or p.last_updated, reverse=True)
        
        return [
            {
                'challenge_title': p.challenge_title,
                'completed_at': (p.completed_at or p.last_updated).isoformat(),
                'progress_percentage': p.progress_percentage,
                'points_earned': p.points_earned,
                'xp_earned': p.xp_earned
            }
            for p in completed
        ]
    
    def get_xp_history(self, user_xp: UserXP, days: int = 30) -> Dict[str, Any]:
        """
        Get XP history for a user.
        
        Args:
            user_xp: User XP object
            days: Number of days to include
        
        Returns:
            Dict: XP history
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        filtered_history = [h for h in user_xp.xp_history if h['date'] >= cutoff_str]
        
        # Group by day
        daily_xp = defaultdict(int)
        daily_sources = defaultdict(list)
        
        for entry in filtered_history:
            date = entry['date'][:10]  # YYYY-MM-DD
            daily_xp[date] += entry['amount']
            daily_sources[date].append({
                'source': entry['source'],
                'amount': entry['amount']
            })
        
        # Sort by date
        sorted_dates = sorted(daily_xp.keys())
        
        return {
            'total_xp': sum(entry['amount'] for entry in filtered_history),
            'total_entries': len(filtered_history),
            'daily_breakdown': {
                date: {
                    'xp': daily_xp[date],
                    'sources': daily_sources[date]
                }
                for date in sorted_dates
            },
            'sources': self._get_source_breakdown(filtered_history)
        }
    
    def _get_source_breakdown(self, history: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Get XP breakdown by source.
        
        Args:
            history: XP history entries
        
        Returns:
            Dict: Source breakdown
        """
        sources = defaultdict(int)
        for entry in history:
            sources[entry['source']] += entry['amount']
        return dict(sources)
    
    def get_achievement_progress_summary(self, achievements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get achievement progress summary.
        
        Args:
            achievements: List of achievement progress
        
        Returns:
            Dict: Achievement summary
        """
        unlocked = [a for a in achievements if a.get('status') == 'unlocked']
        in_progress = [a for a in achievements if a.get('status') == 'in_progress']
        locked = [a for a in achievements if a.get('status') == 'locked']
        
        return {
            'total': len(achievements),
            'unlocked': len(unlocked),
            'in_progress': len(in_progress),
            'locked': len(locked),
            'unlock_percentage': (len(unlocked) / len(achievements) * 100) if achievements else 0,
            'recent_unlocked': sorted(unlocked, key=lambda a: a.get('unlocked_at', ''), reverse=True)[:5]
        }
    
    def get_streak_progress(self, streak: Streak) -> Dict[str, Any]:
        """
        Get streak progress summary.
        
        Args:
            streak: Streak object
        
        Returns:
            Dict: Streak progress
        """
        return {
            'current_streak': streak.current_streak,
            'longest_streak': streak.longest_streak,
            'total_days': streak.total_days,
            'missed_days': streak.missed_days,
            'recovery_count': streak.recovery_count,
            'progress_to_next_milestone': self._calculate_progress_to_next_milestone(streak.current_streak)
        }
    
    def _calculate_progress_to_next_milestone(self, current_streak: int) -> Dict[str, Any]:
        """
        Calculate progress to next streak milestone.
        """
        milestones = [7, 14, 21, 30, 60, 90, 100, 180, 365]
        
        for milestone in milestones:
            if milestone > current_streak:
                return {
                    'milestone': milestone,
                    'progress': (current_streak / milestone) * 100,
                    'days_remaining': milestone - current_streak
                }
        
        return {
            'milestone': None,
            'progress': 100,
            'days_remaining': 0
        }