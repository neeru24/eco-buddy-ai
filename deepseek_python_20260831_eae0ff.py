"""
Sustainability Lifecycle & Long-Term Progress Management - Achievement Tracker
Tracks achievements, milestones, and personal records.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    AchievementHistory, MilestoneEvent, SustainabilityEvent,
    EventType, EventCategory
)

logger = logging.getLogger(__name__)


class AchievementTracker:
    """
    Tracks achievements and milestones in the sustainability journey.
    """
    
    def __init__(self):
        """Initialize the achievement tracker."""
        self.achievement_definitions = self._initialize_achievement_definitions()
        self.milestone_definitions = self._initialize_milestone_definitions()
        logger.info("Achievement Tracker initialized")
    
    def _initialize_achievement_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize achievement definitions.
        """
        return {
            'first_goal': {
                'title': 'First Goal',
                'description': 'Create your first sustainability goal',
                'icon': '🎯',
                'points': 10,
                'difficulty': 'easy',
                'badge_color': '#4CAF50'
            },
            'goal_master': {
                'title': 'Goal Master',
                'description': 'Complete 5 sustainability goals',
                'icon': '🏆',
                'points': 50,
                'difficulty': 'medium',
                'badge_color': '#FFD700'
            },
            'goal_expert': {
                'title': 'Goal Expert',
                'description': 'Complete 20 sustainability goals',
                'icon': '👑',
                'points': 100,
                'difficulty': 'hard',
                'badge_color': '#FF6F00'
            },
            'habit_starter': {
                'title': 'Habit Starter',
                'description': 'Adopt your first sustainability habit',
                'icon': '🌟',
                'points': 10,
                'difficulty': 'easy',
                'badge_color': '#66BB6A'
            },
            'habit_master': {
                'title': 'Habit Master',
                'description': 'Maintain a habit for 30 days straight',
                'icon': '🔥',
                'points': 40,
                'difficulty': 'medium',
                'badge_color': '#FF6F00'
            },
            'streak_champion': {
                'title': 'Streak Champion',
                'description': 'Achieve a 100-day streak on any habit',
                'icon': '💎',
                'points': 100,
                'difficulty': 'hard',
                'badge_color': '#1A237E'
            },
            'sustainability_star': {
                'title': 'Sustainability Star',
                'description': 'Reach a sustainability score of 80%',
                'icon': '⭐',
                'points': 75,
                'difficulty': 'medium',
                'badge_color': '#FFD700'
            },
            'sustainability_legend': {
                'title': 'Sustainability Legend',
                'description': 'Reach a sustainability score of 95%',
                'icon': '🌟',
                'points': 150,
                'difficulty': 'expert',
                'badge_color': '#FF6F00'
            },
            'carbon_reducer': {
                'title': 'Carbon Reducer',
                'description': 'Reduce carbon footprint by 50%',
                'icon': '🌍',
                'points': 60,
                'difficulty': 'medium',
                'badge_color': '#2E7D32'
            },
            'water_saver': {
                'title': 'Water Saver',
                'description': 'Reduce water usage by 30%',
                'icon': '💧',
                'points': 50,
                'difficulty': 'medium',
                'badge_color': '#0277BD'
            },
            'waste_reducer': {
                'title': 'Waste Reducer',
                'description': 'Reduce waste generation by 40%',
                'icon': '♻️',
                'points': 50,
                'difficulty': 'medium',
                'badge_color': '#2E7D32'
            },
            'roadmap_completer': {
                'title': 'Roadmap Completer',
                'description': 'Complete a sustainability roadmap',
                'icon': '🗺️',
                'points': 80,
                'difficulty': 'hard',
                'badge_color': '#1565C0'
            },
            'experiment_pioneer': {
                'title': 'Experiment Pioneer',
                'description': 'Complete your first sustainability experiment',
                'icon': '🧪',
                'points': 30,
                'difficulty': 'easy',
                'badge_color': '#E65100'
            },
            'household_leader': {
                'title': 'Household Leader',
                'description': 'Lead a household sustainability initiative',
                'icon': '🏠',
                'points': 60,
                'difficulty': 'medium',
                'badge_color': '#4E342E'
            },
            'optimizer': {
                'title': 'Optimizer',
                'description': 'Apply an optimization plan to your household',
                'icon': '⚙️',
                'points': 70,
                'difficulty': 'medium',
                'badge_color': '#4527A0'
            }
        }
    
    def _initialize_milestone_definitions(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize milestone definitions.
        """
        return {
            'first_week': {
                'title': 'First Week Complete',
                'description': 'Complete your first week of sustainability tracking',
                'icon': '📅',
                'is_major': False
            },
            'first_month': {
                'title': 'First Month Complete',
                'description': 'Complete your first month of sustainability tracking',
                'icon': '📆',
                'is_major': True
            },
            'first_quarter': {
                'title': 'First Quarter Complete',
                'description': 'Complete your first quarter of sustainability tracking',
                'icon': '📊',
                'is_major': True
            },
            'first_year': {
                'title': 'First Year Complete',
                'description': 'Complete your first year of sustainability tracking',
                'icon': '🎉',
                'is_major': True
            },
            'score_50': {
                'title': 'Sustainability Score 50%',
                'description': 'Achieve a sustainability score of 50%',
                'icon': '⭐',
                'is_major': False
            },
            'score_75': {
                'title': 'Sustainability Score 75%',
                'description': 'Achieve a sustainability score of 75%',
                'icon': '🌟',
                'is_major': True
            },
            'score_90': {
                'title': 'Sustainability Score 90%',
                'description': 'Achieve a sustainability score of 90%',
                'icon': '💫',
                'is_major': True
            }
        }
    
    def unlock_achievement(self,
                          user_id: str,
                          achievement_key: str,
                          related_entity_id: str = "",
                          related_entity_type: str = "",
                          progress_before: float = 0.0,
                          progress_after: float = 0.0) -> Optional[AchievementHistory]:
        """
        Unlock an achievement for a user.
        
        Args:
            user_id: User ID
            achievement_key: Achievement key
            related_entity_id: Related entity ID
            related_entity_type: Related entity type
            progress_before: Progress before achievement
            progress_after: Progress after achievement
        
        Returns:
            Optional[AchievementHistory]: Unlocked achievement
        """
        definition = self.achievement_definitions.get(achievement_key)
        if not definition:
            logger.warning(f"Achievement definition not found: {achievement_key}")
            return None
        
        achievement = AchievementHistory(
            user_id=user_id,
            achievement_type='achievement',
            title=definition['title'],
            description=definition['description'],
            category=definition.get('category', 'general'),
            unlocked_at=datetime.now(),
            difficulty=definition['difficulty'],
            points=definition['points'],
            icon=definition['icon'],
            badge_color=definition['badge_color'],
            requirements=[achievement_key],
            progress_before=progress_before,
            progress_after=progress_after,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type,
            is_verified=True,
            verified_at=datetime.now()
        )
        
        logger.info(f"Achievement unlocked: {definition['title']} for user {user_id}")
        return achievement
    
    def check_achievement_eligibility(self,
                                     user_id: str,
                                     events: List[SustainabilityEvent],
                                     snapshots: List[Dict[str, Any]],
                                     goals: List[Dict[str, Any]],
                                     habits: List[Dict[str, Any]]) -> List[str]:
        """
        Check which achievements a user is eligible for.
        
        Args:
            user_id: User ID
            events: List of sustainability events
            snapshots: List of progress snapshots
            goals: List of goals
            habits: List of habits
        
        Returns:
            List[str]: Eligible achievement keys
        """
        eligible = []
        
        # Check each achievement
        for key, definition in self.achievement_definitions.items():
            if self._check_achievement_condition(key, events, snapshots, goals, habits):
                eligible.append(key)
        
        return eligible
    
    def _check_achievement_condition(self,
                                   key: str,
                                   events: List[SustainabilityEvent],
                                   snapshots: List[Dict[str, Any]],
                                   goals: List[Dict[str, Any]],
                                   habits: List[Dict[str, Any]]) -> bool:
        """
        Check condition for a specific achievement.
        """
        if key == 'first_goal':
            return len(goals) >= 1
        
        if key == 'goal_master':
            return sum(1 for g in goals if g.get('status') == 'completed') >= 5
        
        if key == 'goal_expert':
            return sum(1 for g in goals if g.get('status') == 'completed') >= 20
        
        if key == 'habit_starter':
            return len(habits) >= 1
        
        if key == 'habit_master':
            for habit in habits:
                if habit.get('streak_days', 0) >= 30:
                    return True
            return False
        
        if key == 'streak_champion':
            for habit in habits:
                if habit.get('longest_streak', 0) >= 100:
                    return True
            return False
        
        if key == 'sustainability_star':
            for snapshot in snapshots:
                if snapshot.get('sustainability_score', 0) >= 80:
                    return True
            return False
        
        if key == 'sustainability_legend':
            for snapshot in snapshots:
                if snapshot.get('sustainability_score', 0) >= 95:
                    return True
            return False
        
        if key == 'carbon_reducer':
            if len(snapshots) >= 2:
                first = snapshots[0].get('carbon_footprint', 0)
                last = snapshots[-1].get('carbon_footprint', 0)
                if first > 0:
                    reduction = ((first - last) / first) * 100
                    return reduction >= 50
            return False
        
        if key == 'water_saver':
            if len(snapshots) >= 2:
                first = snapshots[0].get('water_usage', 0)
                last = snapshots[-1].get('water_usage', 0)
                if first > 0:
                    reduction = ((first - last) / first) * 100
                    return reduction >= 30
            return False
        
        if key == 'waste_reducer':
            if len(snapshots) >= 2:
                first = snapshots[0].get('waste_generation', 0)
                last = snapshots[-1].get('waste_generation', 0)
                if first > 0:
                    reduction = ((first - last) / first) * 100
                    return reduction >= 40
            return False
        
        if key == 'roadmap_completer':
            for event in events:
                if event.event_type == EventType.ROADMAP_COMPLETED:
                    return True
            return False
        
        if key == 'experiment_pioneer':
            for event in events:
                if event.event_type == EventType.EXPERIMENT_COMPLETED:
                    return True
            return False
        
        if key == 'household_leader':
            for event in events:
                if event.event_type == EventType.GOAL_COMPLETED and 'household' in event.metadata.get('tags', []):
                    return True
            return False
        
        if key == 'optimizer':
            for event in events:
                if event.event_type == EventType.OPTIMIZATION_APPLIED:
                    return True
            return False
        
        return False
    
    def create_milestone_event(self,
                              user_id: str,
                              milestone_key: str,
                              event_id: str = "",
                              progress_before: float = 0.0,
                              progress_after: float = 0.0) -> MilestoneEvent:
        """
        Create a milestone event.
        
        Args:
            user_id: User ID
            milestone_key: Milestone key
            event_id: Related event ID
            progress_before: Progress before milestone
            progress_after: Progress after milestone
        
        Returns:
            MilestoneEvent: Created milestone
        """
        definition = self.milestone_definitions.get(milestone_key, {})
        
        return MilestoneEvent(
            user_id=user_id,
            event_id=event_id,
            milestone_type=milestone_key,
            title=definition.get('title', milestone_key.replace('_', ' ').title()),
            description=definition.get('description', 'Milestone reached'),
            achieved_at=datetime.now(),
            progress_before=progress_before,
            progress_after=progress_after,
            improvement_percentage=((progress_after - progress_before) / (progress_before + 0.001)) * 100 if progress_before > 0 else 0,
            category='progress',
            icon=definition.get('icon', '⭐'),
            is_major=definition.get('is_major', False)
        )
    
    def get_achievement_summary(self, achievements: List[AchievementHistory]) -> Dict[str, Any]:
        """
        Get summary of achievements.
        
        Args:
            achievements: List of achievements
        
        Returns:
            Dict: Achievement summary
        """
        if not achievements:
            return {
                'total': 0,
                'points': 0,
                'by_difficulty': {},
                'recent': []
            }
        
        points_by_difficulty = {'easy': 0, 'medium': 0, 'hard': 0, 'expert': 0}
        count_by_difficulty = {'easy': 0, 'medium': 0, 'hard': 0, 'expert': 0}
        
        for ach in achievements:
            difficulty = ach.difficulty
            if difficulty in count_by_difficulty:
                count_by_difficulty[difficulty] += 1
                points_by_difficulty[difficulty] += ach.points
        
        recent = sorted(achievements, key=lambda a: a.unlocked_at, reverse=True)[:5]
        
        return {
            'total': len(achievements),
            'total_points': sum(a.points for a in achievements),
            'by_difficulty': count_by_difficulty,
            'points_by_difficulty': points_by_difficulty,
            'recent': [
                {
                    'title': a.title,
                    'icon': a.icon,
                    'points': a.points,
                    'unlocked_at': a.unlocked_at.isoformat()
                }
                for a in recent
            ]
        }
    
    def get_milestone_timeline(self, milestones: List[MilestoneEvent]) -> List[Dict[str, Any]]:
        """
        Get timeline of milestones.
        
        Args:
            milestones: List of milestones
        
        Returns:
            List[Dict]: Milestone timeline
        """
        sorted_milestones = sorted(milestones, key=lambda m: m.achieved_at)
        
        timeline = []
        for i, milestone in enumerate(sorted_milestones):
            timeline.append({
                'order': i + 1,
                'title': milestone.title,
                'description': milestone.description,
                'icon': milestone.icon,
                'date': milestone.achieved_at.isoformat(),
                'is_major': milestone.is_major,
                'improvement': milestone.improvement_percentage,
                'category': milestone.category
            })
        
        return timeline