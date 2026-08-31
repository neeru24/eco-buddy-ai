"""
Sustainability Gamification & Challenge Platform
A comprehensive system for making sustainability engaging through challenges.
"""

from gamification.models import (
    Challenge, ChallengeType, ChallengeDifficulty, ChallengeStatus,
    ChallengeProgress, UserXP, UserLevel, Achievement, AchievementStatus,
    Streak, StreakType, Leaderboard, LeaderboardEntry,
    ChallengeRecommendation, GamificationEvent, PointTransaction,
    ChallengeCategory, ChallengeTemplate, Reward, Badge
)
from gamification.challenge_manager import ChallengeManager
from gamification.points_system import PointsSystem
from gamification.levels_achievements import LevelsAchievementSystem
from gamification.streak_system import StreakSystem
from gamification.leaderboard import LeaderboardManager
from gamification.progress_tracker import ProgressTracker
from gamification.recommendation_engine import ChallengeRecommendationEngine
from gamification.templates import TemplateManager
from gamification.analytics import GamificationAnalytics
from gamification.database import GamificationDatabase
from gamification.visualizations import GamificationVisualizer

__all__ = [
    'Challenge',
    'ChallengeType',
    'ChallengeDifficulty',
    'ChallengeStatus',
    'ChallengeProgress',
    'UserXP',
    'UserLevel',
    'Achievement',
    'AchievementStatus',
    'Streak',
    'StreakType',
    'Leaderboard',
    'LeaderboardEntry',
    'ChallengeRecommendation',
    'GamificationEvent',
    'PointTransaction',
    'ChallengeCategory',
    'ChallengeTemplate',
    'Reward',
    'Badge',
    'ChallengeManager',
    'PointsSystem',
    'LevelsAchievementSystem',
    'StreakSystem',
    'LeaderboardManager',
    'ProgressTracker',
    'ChallengeRecommendationEngine',
    'TemplateManager',
    'GamificationAnalytics',
    'GamificationDatabase',
    'GamificationVisualizer'
]