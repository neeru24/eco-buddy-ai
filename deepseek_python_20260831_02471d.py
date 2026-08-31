"""
Sustainability Gamification & Challenge Platform - Data Models
Comprehensive models for gamification and challenges.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
import json


class ChallengeType(Enum):
    """Types of challenges."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    LONG_TERM = "long_term"
    CUSTOM = "custom"
    HOUSEHOLD = "household"


class ChallengeDifficulty(Enum):
    """Difficulty levels for challenges."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ChallengeStatus(Enum):
    """Status of a challenge."""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ChallengeCategory(Enum):
    """Categories of challenges."""
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    SHOPPING = "shopping"
    RECYCLING = "recycling"
    COMPOSTING = "composting"
    HABIT = "habit"
    LIFESTYLE = "lifestyle"
    HOUSEHOLD = "household"
    COMMUNITY = "community"
    EDUCATION = "education"
    FITNESS = "fitness"
    WELLNESS = "wellness"
    OTHER = "other"


class AchievementStatus(Enum):
    """Status of an achievement."""
    LOCKED = "locked"
    IN_PROGRESS = "in_progress"
    UNLOCKED = "unlocked"
    COMPLETED = "completed"


class StreakType(Enum):
    """Types of streaks."""
    DAILY = "daily"
    WEEKLY = "weekly"
    CATEGORY = "category"
    CHALLENGE = "challenge"


@dataclass
class Challenge:
    """
    Represents a sustainability challenge.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: ChallengeCategory = ChallengeCategory.OTHER
    challenge_type: ChallengeType = ChallengeType.DAILY
    difficulty: ChallengeDifficulty = ChallengeDifficulty.BEGINNER
    
    # Target
    target_value: float = 0.0
    unit: str = ""
    target_metric: str = ""  # carbon, water, waste, energy, etc.
    
    # Timeline
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=lambda: datetime.now() + timedelta(days=7))
    duration_days: int = 7
    
    # Status
    status: ChallengeStatus = ChallengeStatus.DRAFT
    
    # Progress
    current_progress: float = 0.0
    required_progress: float = 0.0
    progress_percentage: float = 0.0
    
    # Points & Rewards
    base_points: int = 10
    bonus_points: int = 0
    xp_reward: int = 20
    rewards: List[str] = field(default_factory=list)  # Reward IDs
    
    # Environmental Impact
    estimated_carbon_savings: float = 0.0
    estimated_water_savings: float = 0.0
    estimated_waste_reduction: float = 0.0
    
    # Completion criteria
    completion_criteria: str = ""
    requires_verification: bool = False
    verification_method: str = ""
    
    # Relationships
    parent_challenge_id: Optional[str] = None
    prerequisite_challenge_ids: List[str] = field(default_factory=list)
    related_habit_ids: List[str] = field(default_factory=list)
    related_goal_ids: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    is_template: bool = False
    template_id: Optional[str] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'challenge_type': self.challenge_type.value,
            'difficulty': self.difficulty.value,
            'target_value': self.target_value,
            'unit': self.unit,
            'target_metric': self.target_metric,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'duration_days': self.duration_days,
            'status': self.status.value,
            'current_progress': self.current_progress,
            'required_progress': self.required_progress,
            'progress_percentage': self.progress_percentage,
            'base_points': self.base_points,
            'bonus_points': self.bonus_points,
            'xp_reward': self.xp_reward,
            'rewards': self.rewards,
            'estimated_carbon_savings': self.estimated_carbon_savings,
            'estimated_water_savings': self.estimated_water_savings,
            'estimated_waste_reduction': self.estimated_waste_reduction,
            'completion_criteria': self.completion_criteria,
            'requires_verification': self.requires_verification,
            'verification_method': self.verification_method,
            'parent_challenge_id': self.parent_challenge_id,
            'prerequisite_challenge_ids': self.prerequisite_challenge_ids,
            'related_habit_ids': self.related_habit_ids,
            'related_goal_ids': self.related_goal_ids,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'tags': self.tags,
            'is_template': self.is_template,
            'template_id': self.template_id,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Challenge':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=ChallengeCategory(data.get('category', 'other')),
            challenge_type=ChallengeType(data.get('challenge_type', 'daily')),
            difficulty=ChallengeDifficulty(data.get('difficulty', 'beginner')),
            target_value=data.get('target_value', 0.0),
            unit=data.get('unit', ''),
            target_metric=data.get('target_metric', ''),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else datetime.now(),
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else datetime.now() + timedelta(days=7),
            duration_days=data.get('duration_days', 7),
            status=ChallengeStatus(data.get('status', 'draft')),
            current_progress=data.get('current_progress', 0.0),
            required_progress=data.get('required_progress', 0.0),
            progress_percentage=data.get('progress_percentage', 0.0),
            base_points=data.get('base_points', 10),
            bonus_points=data.get('bonus_points', 0),
            xp_reward=data.get('xp_reward', 20),
            rewards=data.get('rewards', []),
            estimated_carbon_savings=data.get('estimated_carbon_savings', 0.0),
            estimated_water_savings=data.get('estimated_water_savings', 0.0),
            estimated_waste_reduction=data.get('estimated_waste_reduction', 0.0),
            completion_criteria=data.get('completion_criteria', ''),
            requires_verification=data.get('requires_verification', False),
            verification_method=data.get('verification_method', ''),
            parent_challenge_id=data.get('parent_challenge_id'),
            prerequisite_challenge_ids=data.get('prerequisite_challenge_ids', []),
            related_habit_ids=data.get('related_habit_ids', []),
            related_goal_ids=data.get('related_goal_ids', []),
            created_by=data.get('created_by', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            tags=data.get('tags', []),
            is_template=data.get('is_template', False),
            template_id=data.get('template_id'),
            notes=data.get('notes', '')
        )
    
    def calculate_progress(self) -> float:
        """Calculate progress percentage."""
        if self.required_progress > 0:
            self.progress_percentage = (self.current_progress / self.required_progress) * 100
        return self.progress_percentage
    
    def is_completed(self) -> bool:
        """Check if challenge is completed."""
        return self.status == ChallengeStatus.COMPLETED
    
    def is_expired(self) -> bool:
        """Check if challenge has expired."""
        return datetime.now() > self.end_date and self.status != ChallengeStatus.COMPLETED


@dataclass
class ChallengeProgress:
    """
    Tracks progress for a user on a challenge.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    challenge_id: str = ""
    challenge_title: str = ""
    
    # Progress
    current_value: float = 0.0
    target_value: float = 0.0
    progress_percentage: float = 0.0
    
    # Status
    status: ChallengeStatus = ChallengeStatus.IN_PROGRESS
    
    # Timeline
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    # History
    progress_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Points earned
    points_earned: int = 0
    xp_earned: int = 0
    
    # Metadata
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'challenge_id': self.challenge_id,
            'challenge_title': self.challenge_title,
            'current_value': self.current_value,
            'target_value': self.target_value,
            'progress_percentage': self.progress_percentage,
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'last_updated': self.last_updated.isoformat(),
            'progress_history': self.progress_history,
            'points_earned': self.points_earned,
            'xp_earned': self.xp_earned,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChallengeProgress':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            challenge_id=data.get('challenge_id', ''),
            challenge_title=data.get('challenge_title', ''),
            current_value=data.get('current_value', 0.0),
            target_value=data.get('target_value', 0.0),
            progress_percentage=data.get('progress_percentage', 0.0),
            status=ChallengeStatus(data.get('status', 'in_progress')),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else datetime.now(),
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            progress_history=data.get('progress_history', []),
            points_earned=data.get('points_earned', 0),
            xp_earned=data.get('xp_earned', 0),
            notes=data.get('notes', '')
        )


@dataclass
class UserXP:
    """
    Tracks user experience points and level.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    current_xp: int = 0
    current_level: int = 1
    xp_to_next_level: int = 100
    
    # XP History
    xp_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Level history
    level_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Total XP earned
    total_xp_earned: int = 0
    
    # XP by category
    xp_by_category: Dict[str, int] = field(default_factory=dict)
    
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'current_xp': self.current_xp,
            'current_level': self.current_level,
            'xp_to_next_level': self.xp_to_next_level,
            'xp_history': self.xp_history,
            'level_history': self.level_history,
            'total_xp_earned': self.total_xp_earned,
            'xp_by_category': self.xp_by_category,
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserXP':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            current_xp=data.get('current_xp', 0),
            current_level=data.get('current_level', 1),
            xp_to_next_level=data.get('xp_to_next_level', 100),
            xp_history=data.get('xp_history', []),
            level_history=data.get('level_history', []),
            total_xp_earned=data.get('total_xp_earned', 0),
            xp_by_category=data.get('xp_by_category', {}),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


@dataclass
class UserLevel:
    """
    User level information.
    """
    level: int = 1
    title: str = "Sustainability Beginner"
    xp_required: int = 0
    xp_progress: int = 0
    xp_percentage: float = 0.0
    
    # Level benefits
    unlocks: List[str] = field(default_factory=list)
    bonuses: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'level': self.level,
            'title': self.title,
            'xp_required': self.xp_required,
            'xp_progress': self.xp_progress,
            'xp_percentage': self.xp_percentage,
            'unlocks': self.unlocks,
            'bonuses': self.bonuses
        }


@dataclass
class Achievement:
    """
    Represents a sustainability achievement.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    category: str = ""
    icon: str = "🏆"
    
    # Unlock conditions
    condition_type: str = ""  # xp, challenges, streak, etc.
    condition_value: float = 0.0
    condition_description: str = ""
    
    # Status
    status: AchievementStatus = AchievementStatus.LOCKED
    
    # Progress
    current_progress: float = 0.0
    required_progress: float = 0.0
    
    # Rewards
    xp_reward: int = 0
    points_reward: int = 0
    badge: Optional[str] = None
    
    # Metadata
    unlocked_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    is_hidden: bool = False
    is_rare: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'icon': self.icon,
            'condition_type': self.condition_type,
            'condition_value': self.condition_value,
            'condition_description': self.condition_description,
            'status': self.status.value,
            'current_progress': self.current_progress,
            'required_progress': self.required_progress,
            'xp_reward': self.xp_reward,
            'points_reward': self.points_reward,
            'badge': self.badge,
            'unlocked_at': self.unlocked_at.isoformat() if self.unlocked_at else None,
            'created_at': self.created_at.isoformat(),
            'is_hidden': self.is_hidden,
            'is_rare': self.is_rare
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Achievement':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            icon=data.get('icon', '🏆'),
            condition_type=data.get('condition_type', ''),
            condition_value=data.get('condition_value', 0.0),
            condition_description=data.get('condition_description', ''),
            status=AchievementStatus(data.get('status', 'locked')),
            current_progress=data.get('current_progress', 0.0),
            required_progress=data.get('required_progress', 0.0),
            xp_reward=data.get('xp_reward', 0),
            points_reward=data.get('points_reward', 0),
            badge=data.get('badge'),
            unlocked_at=datetime.fromisoformat(data['unlocked_at']) if data.get('unlocked_at') else None,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            is_hidden=data.get('is_hidden', False),
            is_rare=data.get('is_rare', False)
        )


@dataclass
class Streak:
    """
    Tracks user streaks.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    streak_type: StreakType = StreakType.DAILY
    category: str = ""
    name: str = ""
    
    # Current streak
    current_streak: int = 0
    current_start_date: Optional[datetime] = None
    
    # History
    longest_streak: int = 0
    longest_start_date: Optional[datetime] = None
    longest_end_date: Optional[datetime] = None
    
    # Statistics
    total_days: int = 0
    missed_days: int = 0
    recovery_count: int = 0
    
    # History
    streak_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Last activity
    last_activity_date: Optional[datetime] = None
    
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'streak_type': self.streak_type.value,
            'category': self.category,
            'name': self.name,
            'current_streak': self.current_streak,
            'current_start_date': self.current_start_date.isoformat() if self.current_start_date else None,
            'longest_streak': self.longest_streak,
            'longest_start_date': self.longest_start_date.isoformat() if self.longest_start_date else None,
            'longest_end_date': self.longest_end_date.isoformat() if self.longest_end_date else None,
            'total_days': self.total_days,
            'missed_days': self.missed_days,
            'recovery_count': self.recovery_count,
            'streak_history': self.streak_history,
            'last_activity_date': self.last_activity_date.isoformat() if self.last_activity_date else None,
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Streak':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            streak_type=StreakType(data.get('streak_type', 'daily')),
            category=data.get('category', ''),
            name=data.get('name', ''),
            current_streak=data.get('current_streak', 0),
            current_start_date=datetime.fromisoformat(data['current_start_date']) if data.get('current_start_date') else None,
            longest_streak=data.get('longest_streak', 0),
            longest_start_date=datetime.fromisoformat(data['longest_start_date']) if data.get('longest_start_date') else None,
            longest_end_date=datetime.fromisoformat(data['longest_end_date']) if data.get('longest_end_date') else None,
            total_days=data.get('total_days', 0),
            missed_days=data.get('missed_days', 0),
            recovery_count=data.get('recovery_count', 0),
            streak_history=data.get('streak_history', []),
            last_activity_date=datetime.fromisoformat(data['last_activity_date']) if data.get('last_activity_date') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )


@dataclass
class Leaderboard:
    """
    Represents a leaderboard.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    leaderboard_type: str = ""  # personal, household, community
    category: str = ""
    period: str = ""  # daily, weekly, monthly, all_time
    
    # Entries
    entries: List['LeaderboardEntry'] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leaderboard_type': self.leaderboard_type,
            'category': self.category,
            'period': self.period,
            'entries': [e.to_dict() for e in self.entries],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }


@dataclass
class LeaderboardEntry:
    """
    Represents an entry in a leaderboard.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    leaderboard_id: str = ""
    user_id: str = ""
    user_name: str = ""
    score: int = 0
    rank: int = 0
    
    # Metrics
    challenges_completed: int = 0
    points_earned: int = 0
    xp_earned: int = 0
    streaks: int = 0
    
    # Metadata
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'leaderboard_id': self.leaderboard_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'score': self.score,
            'rank': self.rank,
            'challenges_completed': self.challenges_completed,
            'points_earned': self.points_earned,
            'xp_earned': self.xp_earned,
            'streaks': self.streaks,
            'updated_at': self.updated_at.isoformat()
        }


@dataclass
class ChallengeRecommendation:
    """
    Represents a challenge recommendation for a user.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    challenge_id: str = ""
    challenge_title: str = ""
    reason: str = ""
    confidence: float = 0.0
    priority: int = 0
    
    # Based on
    based_on_habits: List[str] = field(default_factory=list)
    based_on_goals: List[str] = field(default_factory=list)
    based_on_roadmap: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_accepted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'challenge_id': self.challenge_id,
            'challenge_title': self.challenge_title,
            'reason': self.reason,
            'confidence': self.confidence,
            'priority': self.priority,
            'based_on_habits': self.based_on_habits,
            'based_on_goals': self.based_on_goals,
            'based_on_roadmap': self.based_on_roadmap,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_accepted': self.is_accepted
        }


@dataclass
class GamificationEvent:
    """
    Represents a gamification event.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    event_type: str = ""  # challenge_completed, achievement_unlocked, streak_achieved, etc.
    title: str = ""
    description: str = ""
    
    # Points and XP
    points_awarded: int = 0
    xp_awarded: int = 0
    
    # Related entities
    related_challenge_id: Optional[str] = None
    related_achievement_id: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    is_read: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type,
            'title': self.title,
            'description': self.description,
            'points_awarded': self.points_awarded,
            'xp_awarded': self.xp_awarded,
            'related_challenge_id': self.related_challenge_id,
            'related_achievement_id': self.related_achievement_id,
            'created_at': self.created_at.isoformat(),
            'is_read': self.is_read
        }


@dataclass
class PointTransaction:
    """
    Represents a point transaction.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    points: int = 0
    transaction_type: str = ""  # earned, spent, bonus, penalty
    source: str = ""  # challenge, achievement, streak, etc.
    source_id: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ChallengeTemplate:
    """
    Represents a reusable challenge template.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    category: ChallengeCategory = ChallengeCategory.OTHER
    challenge_type: ChallengeType = ChallengeType.DAILY
    difficulty: ChallengeDifficulty = ChallengeDifficulty.BEGINNER
    
    # Default values
    default_target: float = 0.0
    default_unit: str = ""
    default_duration: int = 7
    default_points: int = 10
    default_xp: int = 20
    
    # Environmental impact estimates
    estimated_carbon_savings: float = 0.0
    estimated_water_savings: float = 0.0
    estimated_waste_reduction: float = 0.0
    
    # Instructions
    instructions: str = ""
    tips: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0
    is_active: bool = True
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.value,
            'challenge_type': self.challenge_type.value,
            'difficulty': self.difficulty.value,
            'default_target': self.default_target,
            'default_unit': self.default_unit,
            'default_duration': self.default_duration,
            'default_points': self.default_points,
            'default_xp': self.default_xp,
            'estimated_carbon_savings': self.estimated_carbon_savings,
            'estimated_water_savings': self.estimated_water_savings,
            'estimated_waste_reduction': self.estimated_waste_reduction,
            'instructions': self.instructions,
            'tips': self.tips,
            'resources': self.resources,
            'created_at': self.created_at.isoformat(),
            'usage_count': self.usage_count,
            'is_active': self.is_active,
            'tags': self.tags
        }


@dataclass
class Reward:
    """
    Represents a reward for completing challenges.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    type: str = ""  # badge, virtual, discount, recognition
    icon: str = "🎁"
    points_cost: int = 0
    
    # Requirements
    requires_challenges: int = 0
    requires_streak: int = 0
    requires_level: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    is_available: bool = True
    expires_at: Optional[datetime] = None


@dataclass
class Badge:
    """
    Represents a badge earned by a user.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    badge_id: str = ""
    name: str = ""
    description: str = ""
    icon: str = "🏅"
    earned_at: datetime = field(default_factory=datetime.now)
    is_rare: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'badge_id': self.badge_id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'earned_at': self.earned_at.isoformat(),
            'is_rare': self.is_rare
        }