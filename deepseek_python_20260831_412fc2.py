"""
Sustainability Gamification & Challenge Platform - Points System
Manages points, XP, and level progression.
"""

import logging
import math
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import (
    UserXP, UserLevel, PointTransaction, Challenge,
    ChallengeDifficulty, Achievement
)

logger = logging.getLogger(__name__)


class PointsSystem:
    """
    Manages points, XP, and level progression.
    """
    
    def __init__(self):
        """Initialize the points system."""
        self.level_thresholds = self._initialize_level_thresholds()
        self.level_titles = self._initialize_level_titles()
        self.xp_multipliers = self._initialize_xp_multipliers()
        logger.info("Points System initialized")
    
    def _initialize_level_thresholds(self) -> List[int]:
        """
        Initialize XP thresholds for each level.
        """
        thresholds = [0]  # Level 0
        xp = 100
        for i in range(1, 51):  # 50 levels
            thresholds.append(xp)
            xp = int(xp * 1.2)  # 20% increase per level
        return thresholds
    
    def _initialize_level_titles(self) -> Dict[int, str]:
        """
        Initialize titles for each level.
        """
        return {
            1: "Sustainability Beginner",
            2: "Eco-Conscious Starter",
            3: "Green Enthusiast",
            4: "Earth Protector",
            5: "Sustainability Advocate",
            6: "Eco-Warrior",
            7: "Green Champion",
            8: "Sustainability Leader",
            9: "Eco-Master",
            10: "Sustainability Legend",
            15: "Green Pioneer",
            20: "Eco-Revolutionary",
            25: "Sustainability Visionary",
            30: "Earth Guardian",
            40: "Green Icon",
            50: "Sustainability God"
        }
    
    def _initialize_xp_multipliers(self) -> Dict[str, float]:
        """
        Initialize XP multipliers for different activities.
        """
        return {
            'challenge_completed': 1.0,
            'streak_bonus': 1.5,
            'achievement_unlocked': 2.0,
            'daily_login': 0.5,
            'challenge_streak': 1.2,
            'milestone_reached': 1.8,
            'household_contribution': 1.3
        }
    
    def add_xp(self, user_xp: UserXP, amount: int, source: str, source_id: str = "", multiplier: float = 1.0) -> Dict[str, Any]:
        """
        Add XP to a user.
        
        Args:
            user_xp: User XP object
            amount: XP amount to add
            source: Source of XP
            source_id: Source ID
            multiplier: XP multiplier
        
        Returns:
            Dict: XP update result
        """
        old_xp = user_xp.current_xp
        old_level = user_xp.current_level
        
        # Apply multiplier
        final_amount = int(amount * multiplier)
        
        # Add XP
        user_xp.current_xp += final_amount
        user_xp.total_xp_earned += final_amount
        
        # Update category XP
        if source in user_xp.xp_by_category:
            user_xp.xp_by_category[source] += final_amount
        else:
            user_xp.xp_by_category[source] = final_amount
        
        # Add to history
        user_xp.xp_history.append({
            'date': datetime.now().isoformat(),
            'amount': final_amount,
            'source': source,
            'source_id': source_id,
            'level': user_xp.current_level
        })
        
        # Check for level up
        leveled_up = False
        new_level = user_xp.current_level
        
        while user_xp.current_xp >= self.level_thresholds[user_xp.current_level + 1]:
            new_level += 1
            leveled_up = True
            user_xp.current_level = new_level
            
            # Add level history
            user_xp.level_history.append({
                'date': datetime.now().isoformat(),
                'level': new_level,
                'xp_at_level': user_xp.current_xp,
                'title': self._get_level_title(new_level)
            })
        
        user_xp.updated_at = datetime.now()
        
        # Calculate XP to next level
        next_level = user_xp.current_level + 1
        if next_level < len(self.level_thresholds):
            user_xp.xp_to_next_level = self.level_thresholds[next_level] - user_xp.current_xp
        else:
            user_xp.xp_to_next_level = 0
        
        return {
            'old_xp': old_xp,
            'new_xp': user_xp.current_xp,
            'xp_added': final_amount,
            'old_level': old_level,
            'new_level': user_xp.current_level,
            'leveled_up': leveled_up,
            'xp_to_next_level': user_xp.xp_to_next_level,
            'multiplier': multiplier
        }
    
    def _get_level_title(self, level: int) -> str:
        """
        Get title for a level.
        """
        # Check exact matches
        if level in self.level_titles:
            return self.level_titles[level]
        
        # Check nearest lower title
        titles = sorted(self.level_titles.keys())
        for t in reversed(titles):
            if level >= t:
                return self.level_titles[t]
        
        return f"Level {level} Explorer"
    
    def get_level_info(self, user_xp: UserXP) -> UserLevel:
        """
        Get level information for a user.
        
        Args:
            user_xp: User XP object
        
        Returns:
            UserLevel: Level information
        """
        level = user_xp.current_level
        current_xp = user_xp.current_xp
        
        # XP required for current level
        xp_required = self.level_thresholds[level] if level < len(self.level_thresholds) else 0
        xp_next = self.level_thresholds[level + 1] if level + 1 < len(self.level_thresholds) else xp_required + 1000
        
        if xp_next > xp_required:
            xp_progress = current_xp - xp_required
            xp_needed = xp_next - xp_required
            xp_percentage = (xp_progress / xp_needed) * 100 if xp_needed > 0 else 0
        else:
            xp_progress = 0
            xp_percentage = 0
        
        return UserLevel(
            level=level,
            title=self._get_level_title(level),
            xp_required=xp_next,
            xp_progress=xp_progress,
            xp_percentage=min(100, xp_percentage),
            unlocks=self._get_level_unlocks(level),
            bonuses=self._get_level_bonuses(level)
        )
    
    def _get_level_unlocks(self, level: int) -> List[str]:
        """
        Get unlocks for a level.
        """
        unlocks = []
        
        if level >= 3:
            unlocks.append("Access to advanced challenges")
        if level >= 5:
            unlocks.append("Create custom challenges")
        if level >= 10:
            unlocks.append("Household challenges")
        if level >= 15:
            unlocks.append("Community challenges")
        if level >= 20:
            unlocks.append("Mentor other users")
        if level >= 30:
            unlocks.append("Create challenge templates")
        
        return unlocks
    
    def _get_level_bonuses(self, level: int) -> Dict[str, float]:
        """
        Get level bonuses.
        """
        bonuses = {}
        
        if level >= 5:
            bonuses['xp_multiplier'] = 1.05
        if level >= 10:
            bonuses['xp_multiplier'] = 1.10
        if level >= 20:
            bonuses['xp_multiplier'] = 1.15
        if level >= 30:
            bonuses['xp_multiplier'] = 1.20
        if level >= 40:
            bonuses['xp_multiplier'] = 1.25
        
        return bonuses
    
    def calculate_challenge_points(self, challenge: Challenge) -> int:
        """
        Calculate points for a challenge.
        
        Args:
            challenge: Challenge to calculate points for
        
        Returns:
            int: Points earned
        """
        base_points = challenge.base_points
        
        # Difficulty bonus
        difficulty_bonus = {
            ChallengeDifficulty.BEGINNER: 0,
            ChallengeDifficulty.INTERMEDIATE: 5,
            ChallengeDifficulty.ADVANCED: 10,
            ChallengeDifficulty.EXPERT: 20
        }.get(challenge.difficulty, 0)
        
        # Category bonus
        category_bonus = 0
        if challenge.category in [ChallengeCategory.ENERGY, ChallengeCategory.WATER]:
            category_bonus = 5
        
        # Impact bonus
        impact_bonus = 0
        if challenge.estimated_carbon_savings > 10:
            impact_bonus += 5
        if challenge.estimated_water_savings > 50:
            impact_bonus += 5
        if challenge.estimated_waste_reduction > 5:
            impact_bonus += 5
        
        total_points = base_points + difficulty_bonus + category_bonus + impact_bonus
        
        # Bonus for streak (if applicable)
        if challenge.challenge_type == ChallengeType.DAILY:
            total_points += 2
        
        return total_points
    
    def calculate_challenge_xp(self, challenge: Challenge) -> int:
        """
        Calculate XP for a challenge.
        
        Args:
            challenge: Challenge to calculate XP for
        
        Returns:
            int: XP earned
        """
        base_xp = challenge.xp_reward
        
        # Difficulty bonus
        difficulty_bonus = {
            ChallengeDifficulty.BEGINNER: 0,
            ChallengeDifficulty.INTERMEDIATE: 10,
            ChallengeDifficulty.ADVANCED: 20,
            ChallengeDifficulty.EXPERT: 40
        }.get(challenge.difficulty, 0)
        
        # Impact bonus
        impact_bonus = 0
        if challenge.estimated_carbon_savings > 20:
            impact_bonus += 10
        if challenge.estimated_water_savings > 100:
            impact_bonus += 10
        
        # Duration bonus
        duration_bonus = 0
        if challenge.duration_days >= 30:
            duration_bonus = 20
        elif challenge.duration_days >= 14:
            duration_bonus = 10
        
        return base_xp + difficulty_bonus + impact_bonus + duration_bonus
    
    def get_xp_summary(self, user_xp: UserXP) -> Dict[str, Any]:
        """
        Get XP summary for a user.
        
        Args:
            user_xp: User XP object
        
        Returns:
            Dict: XP summary
        """
        level_info = self.get_level_info(user_xp)
        
        return {
            'current_xp': user_xp.current_xp,
            'current_level': user_xp.current_level,
            'level_title': level_info.title,
            'xp_to_next_level': user_xp.xp_to_next_level,
            'xp_progress': level_info.xp_percentage,
            'total_xp_earned': user_xp.total_xp_earned,
            'xp_by_category': user_xp.xp_by_category,
            'level_bonuses': level_info.bonuses,
            'level_unlocks': level_info.unlocks,
            'xp_history_count': len(user_xp.xp_history),
            'level_history_count': len(user_xp.level_history)
        }
    
    def get_xp_history_by_period(self, user_xp: UserXP, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get XP history for a period.
        
        Args:
            user_xp: User XP object
            days: Number of days to include
        
        Returns:
            List[Dict]: XP history
        """
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()
        
        return [h for h in user_xp.xp_history if h['date'] >= cutoff_str]
    
    def calculate_xp_for_achievement(self, achievement: Achievement) -> int:
        """
        Calculate XP for an achievement.
        
        Args:
            achievement: Achievement to calculate XP for
        
        Returns:
            int: XP earned
        """
        base_xp = achievement.xp_reward
        
        if achievement.is_rare:
            base_xp *= 2
        
        if achievement.is_hidden:
            base_xp *= 1.5
        
        return base_xp