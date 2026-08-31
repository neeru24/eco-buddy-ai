"""
Sustainability Gamification & Challenge Platform - Leaderboard
Manages leaderboards and rankings.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import Leaderboard, LeaderboardEntry, Challenge, UserXP

logger = logging.getLogger(__name__)


class LeaderboardManager:
    """
    Manages leaderboards and rankings.
    """
    
    def __init__(self):
        """Initialize the leaderboard manager."""
        self.leaderboard_types = ['personal', 'household', 'community']
        self.periods = ['daily', 'weekly', 'monthly', 'all_time']
        logger.info("Leaderboard Manager initialized")
    
    def create_leaderboard(self,
                          name: str,
                          description: str,
                          leaderboard_type: str,
                          category: str = "",
                          period: str = "weekly") -> Leaderboard:
        """
        Create a new leaderboard.
        
        Args:
            name: Leaderboard name
            description: Leaderboard description
            leaderboard_type: Type of leaderboard
            category: Category filter
            period: Time period
        
        Returns:
            Leaderboard: Created leaderboard
        """
        leaderboard = Leaderboard(
            name=name,
            description=description,
            leaderboard_type=leaderboard_type,
            category=category,
            period=period,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        logger.info(f"Created leaderboard: {name}")
        return leaderboard
    
    def update_leaderboard(self,
                          leaderboard: Leaderboard,
                          users: List[Dict[str, Any]],
                          user_xp: Dict[str, UserXP],
                          challenges: Dict[str, List[Challenge]]) -> Leaderboard:
        """
        Update a leaderboard with current rankings.
        
        Args:
            leaderboard: Leaderboard to update
            users: List of user information
            user_xp: Map of user XP
            challenges: Map of user challenges
        
        Returns:
            Leaderboard: Updated leaderboard
        """
        entries = []
        
        for user in users:
            user_id = user['id']
            user_name = user.get('name', 'Unknown')
            
            # Calculate score based on leaderboard type and period
            score = self._calculate_score(user_id, leaderboard, user_xp, challenges)
            
            entry = LeaderboardEntry(
                leaderboard_id=leaderboard.id,
                user_id=user_id,
                user_name=user_name,
                score=score,
                challenges_completed=self._count_challenges_completed(challenges.get(user_id, [])),
                points_earned=self._calculate_points_earned(challenges.get(user_id, [])),
                xp_earned=self._calculate_xp_earned(user_xp.get(user_id)),
                streaks=self._calculate_streaks(challenges.get(user_id, [])),
                updated_at=datetime.now()
            )
            entries.append(entry)
        
        # Sort by score
        entries.sort(key=lambda e: e.score, reverse=True)
        
        # Assign ranks
        for i, entry in enumerate(entries):
            entry.rank = i + 1
        
        leaderboard.entries = entries
        leaderboard.updated_at = datetime.now()
        
        logger.info(f"Updated leaderboard: {leaderboard.name} with {len(entries)} entries")
        return leaderboard
    
    def _calculate_score(self,
                        user_id: str,
                        leaderboard: Leaderboard,
                        user_xp: Dict[str, UserXP],
                        challenges: Dict[str, List[Challenge]]) -> int:
        """
        Calculate score for a user.
        """
        score = 0
        
        # XP contribution
        if user_id in user_xp:
            score += user_xp[user_id].current_xp
        
        # Challenge contribution
        user_challenges = challenges.get(user_id, [])
        completed = [c for c in user_challenges if c.status.value == 'completed']
        score += len(completed) * 10
        
        # Streak bonus
        if completed:
            longest_streak = self._calculate_longest_streak(completed)
            score += longest_streak * 5
        
        # Period filter
        if leaderboard.period != 'all_time':
            now = datetime.now()
            cutoff = now
            
            if leaderboard.period == 'daily':
                cutoff = now - timedelta(days=1)
            elif leaderboard.period == 'weekly':
                cutoff = now - timedelta(days=7)
            elif leaderboard.period == 'monthly':
                cutoff = now - timedelta(days=30)
            
            # Only count recent activities
            recent_completed = [c for c in completed if c.completed_at and c.completed_at >= cutoff]
            score = len(recent_completed) * 10
        
        return score
    
    def _count_challenges_completed(self, challenges: List[Challenge]) -> int:
        """
        Count completed challenges.
        """
        return sum(1 for c in challenges if c.status.value == 'completed')
    
    def _calculate_points_earned(self, challenges: List[Challenge]) -> int:
        """
        Calculate points earned from challenges.
        """
        return sum(c.base_points + c.bonus_points for c in challenges if c.status.value == 'completed')
    
    def _calculate_xp_earned(self, xp: Optional[UserXP]) -> int:
        """
        Calculate XP earned.
        """
        if xp:
            return xp.total_xp_earned
        return 0
    
    def _calculate_streaks(self, challenges: List[Challenge]) -> int:
        """
        Calculate streaks from challenges.
        """
        # Simple streak calculation from completed challenges
        completed = [c for c in challenges if c.status.value == 'completed']
        if not completed:
            return 0
        
        completed.sort(key=lambda c: c.completed_at or c.updated_at)
        streak = 1
        for i in range(1, len(completed)):
            prev_date = completed[i-1].completed_at or completed[i-1].updated_at
            curr_date = completed[i].completed_at or completed[i].updated_at
            
            if (curr_date - prev_date).days <= 2:
                streak += 1
            else:
                break
        
        return streak
    
    def _calculate_longest_streak(self, challenges: List[Challenge]) -> int:
        """
        Calculate longest streak from challenges.
        """
        if not challenges:
            return 0
        
        completed = [c for c in challenges if c.status.value == 'completed']
        if not completed:
            return 0
        
        completed.sort(key=lambda c: c.completed_at or c.updated_at)
        
        longest = 0
        current = 1
        
        for i in range(1, len(completed)):
            prev_date = completed[i-1].completed_at or completed[i-1].updated_at
            curr_date = completed[i].completed_at or completed[i].updated_at
            
            if (curr_date - prev_date).days <= 2:
                current += 1
            else:
                longest = max(longest, current)
                current = 1
        
        longest = max(longest, current)
        return longest
    
    def get_leaderboard_summary(self, leaderboard: Leaderboard) -> Dict[str, Any]:
        """
        Get leaderboard summary.
        
        Args:
            leaderboard: Leaderboard to summarize
        
        Returns:
            Dict: Leaderboard summary
        """
        top_entries = leaderboard.entries[:10]
        
        return {
            'name': leaderboard.name,
            'description': leaderboard.description,
            'type': leaderboard.leaderboard_type,
            'period': leaderboard.period,
            'total_entries': len(leaderboard.entries),
            'top_10': [
                {
                    'rank': e.rank,
                    'user': e.user_name,
                    'score': e.score,
                    'challenges': e.challenges_completed
                }
                for e in top_entries
            ],
            'user_rank': next((e.rank for e in leaderboard.entries if e.user_id == 'current_user'), None)
        }
    
    def get_user_rank(self, leaderboard: Leaderboard, user_id: str) -> Optional[int]:
        """
        Get user's rank in a leaderboard.
        
        Args:
            leaderboard: Leaderboard
            user_id: User ID
        
        Returns:
            Optional[int]: User's rank
        """
        for entry in leaderboard.entries:
            if entry.user_id == user_id:
                return entry.rank
        return None
    
    def get_top_performers(self, leaderboard: Leaderboard, limit: int = 10) -> List[LeaderboardEntry]:
        """
        Get top performers.
        
        Args:
            leaderboard: Leaderboard
            limit: Number of top performers
        
        Returns:
            List[LeaderboardEntry]: Top performers
        """
        return leaderboard.entries[:limit]