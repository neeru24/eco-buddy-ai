"""
Sustainability Gamification & Challenge Platform - Levels & Achievements
Manages user levels, achievements, and badges.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import (
    UserXP, Achievement, AchievementStatus, Badge, Challenge,
    ChallengeStatus, Streak
)

logger = logging.getLogger(__name__)


class LevelsAchievementSystem:
    """
    Manages levels, achievements, and badges.
    """
    
    def __init__(self):
        """Initialize the levels and achievement system."""
        self.achievement_definitions = self._initialize_achievement_definitions()
        self.badge_definitions = self._initialize_badge_definitions()
        logger.info("Levels & Achievement System initialized")
    
    def _initialize_achievement_definitions(self) -> List[Dict[str, Any]]:
        """
        Initialize achievement definitions.
        """
        return [
            {
                'id': 'first_challenge',
                'title': 'First Challenge',
                'description': 'Complete your first sustainability challenge',
                'category': 'challenges',
                'icon': '🎯',
                'condition_type': 'challenges_completed',
                'condition_value': 1,
                'xp_reward': 20,
                'points_reward': 10,
                'badge': 'bronze'
            },
            {
                'id': 'challenge_starter',
                'title': 'Challenge Starter',
                'description': 'Complete 5 sustainability challenges',
                'category': 'challenges',
                'icon': '🏆',
                'condition_type': 'challenges_completed',
                'condition_value': 5,
                'xp_reward': 50,
                'points_reward': 25,
                'badge': 'silver'
            },
            {
                'id': 'challenge_master',
                'title': 'Challenge Master',
                'description': 'Complete 25 sustainability challenges',
                'category': 'challenges',
                'icon': '👑',
                'condition_type': 'challenges_completed',
                'condition_value': 25,
                'xp_reward': 100,
                'points_reward': 50,
                'badge': 'gold'
            },
            {
                'id': 'streak_7',
                'title': 'Week Streak',
                'description': 'Maintain a 7-day streak',
                'category': 'streaks',
                'icon': '🔥',
                'condition_type': 'streak_days',
                'condition_value': 7,
                'xp_reward': 30,
                'points_reward': 15,
                'badge': 'bronze'
            },
            {
                'id': 'streak_30',
                'title': 'Month Streak',
                'description': 'Maintain a 30-day streak',
                'category': 'streaks',
                'icon': '💪',
                'condition_type': 'streak_days',
                'condition_value': 30,
                'xp_reward': 80,
                'points_reward': 40,
                'badge': 'silver'
            },
            {
                'id': 'streak_100',
                'title': 'Century Streak',
                'description': 'Maintain a 100-day streak',
                'category': 'streaks',
                'icon': '💎',
                'condition_type': 'streak_days',
                'condition_value': 100,
                'xp_reward': 200,
                'points_reward': 100,
                'badge': 'gold',
                'is_rare': True
            },
            {
                'id': 'energy_saver',
                'title': 'Energy Saver',
                'description': 'Complete 10 energy-related challenges',
                'category': 'energy',
                'icon': '⚡',
                'condition_type': 'category_challenges',
                'condition_value': 10,
                'xp_reward': 60,
                'points_reward': 30,
                'badge': 'silver'
            },
            {
                'id': 'water_conservator',
                'title': 'Water Conservator',
                'description': 'Complete 10 water-related challenges',
                'category': 'water',
                'icon': '💧',
                'condition_type': 'category_challenges',
                'condition_value': 10,
                'xp_reward': 60,
                'points_reward': 30,
                'badge': 'silver'
            },
            {
                'id': 'waste_reducer',
                'title': 'Waste Reducer',
                'description': 'Complete 10 waste-related challenges',
                'category': 'waste',
                'icon': '♻️',
                'condition_type': 'category_challenges',
                'condition_value': 10,
                'xp_reward': 60,
                'points_reward': 30,
                'badge': 'silver'
            },
            {
                'id': 'level_5',
                'title': 'Level 5 Achiever',
                'description': 'Reach sustainability level 5',
                'category': 'levels',
                'icon': '🌟',
                'condition_type': 'level',
                'condition_value': 5,
                'xp_reward': 40,
                'points_reward': 20,
                'badge': 'bronze'
            },
            {
                'id': 'level_10',
                'title': 'Level 10 Master',
                'description': 'Reach sustainability level 10',
                'category': 'levels',
                'icon': '⭐',
                'condition_type': 'level',
                'condition_value': 10,
                'xp_reward': 80,
                'points_reward': 40,
                'badge': 'silver'
            },
            {
                'id': 'level_25',
                'title': 'Level 25 Legend',
                'description': 'Reach sustainability level 25',
                'category': 'levels',
                'icon': '🌟',
                'condition_type': 'level',
                'condition_value': 25,
                'xp_reward': 150,
                'points_reward': 75,
                'badge': 'gold',
                'is_rare': True
            },
            {
                'id': 'all_categories',
                'title': 'Category Explorer',
                'description': 'Complete challenges in all categories',
                'category': 'exploration',
                'icon': '🗺️',
                'condition_type': 'all_categories',
                'condition_value': 1,
                'xp_reward': 50,
                'points_reward': 25,
                'badge': 'silver'
            },
            {
                'id': 'daily_grinder',
                'title': 'Daily Grinder',
                'description': 'Complete 30 daily challenges',
                'category': 'daily',
                'icon': '📅',
                'condition_type': 'daily_challenges',
                'condition_value': 30,
                'xp_reward': 70,
                'points_reward': 35,
                'badge': 'silver'
            }
        ]
    
    def _initialize_badge_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize badge definitions.
        """
        return {
            'bronze': {
                'name': 'Bronze Badge',
                'icon': '🥉',
                'color': '#CD7F32'
            },
            'silver': {
                'name': 'Silver Badge',
                'icon': '🥈',
                'color': '#C0C0C0'
            },
            'gold': {
                'name': 'Gold Badge',
                'icon': '🥇',
                'color': '#FFD700'
            },
            'platinum': {
                'name': 'Platinum Badge',
                'icon': '💎',
                'color': '#E5E4E2'
            },
            'diamond': {
                'name': 'Diamond Badge',
                'icon': '💠',
                'color': '#B9F2FF'
            }
        }
    
    def check_achievements(self,
                          user_id: str,
                          challenges: List[Challenge],
                          user_xp: UserXP,
                          streak: Optional[Streak] = None) -> List[Achievement]:
        """
        Check and unlock achievements for a user.
        
        Args:
            user_id: User ID
            challenges: List of user's challenges
            user_xp: User XP object
            streak: User streak object
        
        Returns:
            List[Achievement]: Unlocked achievements
        """
        unlocked = []
        
        for definition in self.achievement_definitions:
            # Check if achievement is already unlocked
            # (This would be checked against existing achievements)
            
            condition_type = definition['condition_type']
            condition_value = definition['condition_value']
            
            if self._check_condition(user_id, condition_type, condition_value, challenges, user_xp, streak):
                achievement = Achievement(
                    id=definition['id'],
                    title=definition['title'],
                    description=definition['description'],
                    category=definition['category'],
                    icon=definition['icon'],
                    condition_type=condition_type,
                    condition_value=condition_value,
                    condition_description=f"Complete {condition_value} {condition_type.replace('_', ' ')}",
                    status=AchievementStatus.UNLOCKED,
                    required_progress=condition_value,
                    xp_reward=definition['xp_reward'],
                    points_reward=definition['points_reward'],
                    badge=definition.get('badge'),
                    unlocked_at=datetime.now(),
                    is_rare=definition.get('is_rare', False)
                )
                unlocked.append(achievement)
        
        return unlocked
    
    def _check_condition(self,
                        user_id: str,
                        condition_type: str,
                        condition_value: float,
                        challenges: List[Challenge],
                        user_xp: UserXP,
                        streak: Optional[Streak] = None) -> bool:
        """
        Check if a condition is met.
        """
        if condition_type == 'challenges_completed':
            completed = sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED)
            return completed >= condition_value
        
        elif condition_type == 'streak_days':
            if streak:
                return streak.current_streak >= condition_value
            return False
        
        elif condition_type == 'category_challenges':
            completed = sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED)
            # Check if any category has enough completed challenges
            categories = {}
            for c in challenges:
                if c.status == ChallengeStatus.COMPLETED:
                    categories[c.category.value] = categories.get(c.category.value, 0) + 1
            return any(count >= condition_value for count in categories.values())
        
        elif condition_type == 'level':
            return user_xp.current_level >= condition_value
        
        elif condition_type == 'all_categories':
            completed_categories = set()
            for c in challenges:
                if c.status == ChallengeStatus.COMPLETED:
                    completed_categories.add(c.category.value)
            return len(completed_categories) >= len(ChallengeCategory) * 0.5
        
        elif condition_type == 'daily_challenges':
            completed = sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED and c.challenge_type.value == 'daily')
            return completed >= condition_value
        
        return False
    
    def get_achievement_progress(self,
                                user_id: str,
                                challenges: List[Challenge],
                                user_xp: UserXP,
                                streak: Optional[Streak] = None) -> List[Dict[str, Any]]:
        """
        Get progress toward all achievements.
        
        Args:
            user_id: User ID
            challenges: List of user's challenges
            user_xp: User XP object
            streak: User streak object
        
        Returns:
            List[Dict]: Achievement progress
        """
        progress = []
        
        for definition in self.achievement_definitions:
            condition_type = definition['condition_type']
            condition_value = definition['condition_value']
            
            current_value = self._get_condition_value(user_id, condition_type, challenges, user_xp, streak)
            
            progress.append({
                'id': definition['id'],
                'title': definition['title'],
                'description': definition['description'],
                'icon': definition['icon'],
                'category': definition['category'],
                'current_progress': current_value,
                'required_progress': condition_value,
                'percentage': min(100, (current_value / condition_value) * 100) if condition_value > 0 else 0,
                'xp_reward': definition['xp_reward'],
                'points_reward': definition['points_reward'],
                'badge': definition.get('badge'),
                'is_rare': definition.get('is_rare', False)
            })
        
        return progress
    
    def _get_condition_value(self,
                            user_id: str,
                            condition_type: str,
                            challenges: List[Challenge],
                            user_xp: UserXP,
                            streak: Optional[Streak] = None) -> float:
        """
        Get current value for a condition.
        """
        if condition_type == 'challenges_completed':
            return sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED)
        
        elif condition_type == 'streak_days':
            if streak:
                return streak.current_streak
            return 0
        
        elif condition_type == 'category_challenges':
            max_category = 0
            categories = {}
            for c in challenges:
                if c.status == ChallengeStatus.COMPLETED:
                    categories[c.category.value] = categories.get(c.category.value, 0) + 1
            if categories:
                max_category = max(categories.values())
            return max_category
        
        elif condition_type == 'level':
            return user_xp.current_level
        
        elif condition_type == 'all_categories':
            completed_categories = set()
            for c in challenges:
                if c.status == ChallengeStatus.COMPLETED:
                    completed_categories.add(c.category.value)
            return len(completed_categories)
        
        elif condition_type == 'daily_challenges':
            return sum(1 for c in challenges if c.status == ChallengeStatus.COMPLETED and c.challenge_type.value == 'daily')
        
        return 0
    
    def create_badge(self,
                    user_id: str,
                    badge_id: str,
                    challenge_id: str = "") -> Optional[Badge]:
        """
        Create a badge for a user.
        
        Args:
            user_id: User ID
            badge_id: Badge ID
            challenge_id: Related challenge ID
        
        Returns:
            Optional[Badge]: Created badge
        """
        definition = self.badge_definitions.get(badge_id)
        if not definition:
            return None
        
        # Check if user already has this badge
        # (This would be checked against existing badges)
        
        badge = Badge(
            user_id=user_id,
            badge_id=badge_id,
            name=definition['name'],
            description=f"Earned {definition['name']}",
            icon=definition['icon'],
            earned_at=datetime.now(),
            is_rare=badge_id in ['gold', 'platinum', 'diamond']
        )
        
        return badge
    
    def get_badge_summary(self, badges: List[Badge]) -> Dict[str, Any]:
        """
        Get badge summary.
        
        Args:
            badges: List of badges
        
        Returns:
            Dict: Badge summary
        """
        return {
            'total': len(badges),
            'by_rarity': {
                'common': sum(1 for b in badges if not b.is_rare),
                'rare': sum(1 for b in badges if b.is_rare)
            },
            'recent': sorted(badges, key=lambda b: b.earned_at, reverse=True)[:5]
        }