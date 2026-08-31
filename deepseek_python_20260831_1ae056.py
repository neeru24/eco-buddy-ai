"""
Sustainability Lifecycle & Long-Term Progress Management - Data Models
Comprehensive models for tracking sustainability journeys.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Set
import uuid
import json


class EventType(Enum):
    """Types of sustainability events."""
    # Goal events
    GOAL_CREATED = "goal_created"
    GOAL_COMPLETED = "goal_completed"
    GOAL_MODIFIED = "goal_modified"
    GOAL_POSTPONED = "goal_postponed"
    GOAL_FAILED = "goal_failed"
    GOAL_RECOVERED = "goal_recovered"
    GOAL_PROGRESS = "goal_progress"
    
    # Habit events
    HABIT_ADOPTED = "habit_adopted"
    HABIT_IMPROVED = "habit_improved"
    HABIT_REGRESSED = "habit_regressed"
    HABIT_BROKEN = "habit_broken"
    HABIT_RECOVERED = "habit_recovered"
    HABIT_STREAK = "habit_streak"
    
    # Roadmap events
    ROADMAP_CREATED = "roadmap_created"
    ROADMAP_MILESTONE = "roadmap_milestone"
    ROADMAP_COMPLETED = "roadmap_completed"
    ROADMAP_ALTERNATIVE = "roadmap_alternative"
    ROADMAP_STAGE = "roadmap_stage"
    
    # Achievement events
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    MILESTONE_REACHED = "milestone_reached"
    CHALLENGE_COMPLETED = "challenge_completed"
    MAJOR_IMPROVEMENT = "major_improvement"
    PERSONAL_RECORD = "personal_record"
    
    # Decision events
    DECISION_MADE = "decision_made"
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    RECOMMENDATION_REJECTED = "recommendation_rejected"
    RECOMMENDATION_IMPLEMENTED = "recommendation_implemented"
    
    # Progress events
    BENCHMARK_CHANGED = "benchmark_changed"
    SNAPSHOT_TAKEN = "snapshot_taken"
    PERIODIC_REPORT = "periodic_report"
    TREND_CHANGED = "trend_changed"
    
    # Other events
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"
    OPTIMIZATION_APPLIED = "optimization_applied"
    RESOURCE_CHANGED = "resource_changed"


class EventCategory(Enum):
    """Categories for event grouping."""
    GOALS = "goals"
    HABITS = "habits"
    ROADMAP = "roadmap"
    ACHIEVEMENTS = "achievements"
    DECISIONS = "decisions"
    PROGRESS = "progress"
    EXPERIMENTS = "experiments"
    OPTIMIZATIONS = "optimizations"
    RECOMMENDATIONS = "recommendations"
    GENERAL = "general"


class LifecycleStatus(Enum):
    """Status of lifecycle entities."""
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    POSTPONED = "postponed"
    RECOVERED = "recovered"
    REGRESSED = "regressed"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    ARCHIVED = "archived"
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"


class LifecycleStage(Enum):
    """Stages in a lifecycle."""
    CREATION = "creation"
    DEVELOPMENT = "development"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DECLINE = "decline"
    RECOVERY = "recovery"
    COMPLETION = "completion"
    ARCHIVAL = "archival"


class TimelinePeriod(Enum):
    """Period for timeline views."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"
    ALL = "all"


class ProgressMetric(Enum):
    """Metrics for progress tracking."""
    SUSTAINABILITY_SCORE = "sustainability_score"
    CARBON_FOOTPRINT = "carbon_footprint"
    ENERGY_USAGE = "energy_usage"
    WATER_USAGE = "water_usage"
    WASTE_GENERATION = "waste_generation"
    TRANSPORTATION_IMPACT = "transportation_impact"
    FOOD_IMPACT = "food_impact"
    SHOPPING_IMPACT = "shopping_impact"
    HOUSEHOLD_PERFORMANCE = "household_performance"
    GOAL_COMPLETION_RATE = "goal_completion_rate"
    HABIT_CONSISTENCY = "habit_consistency"


@dataclass
class SustainabilityEvent:
    """
    Represents a sustainability event in the user's journey.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    event_type: EventType = EventType.GOAL_CREATED
    category: EventCategory = EventCategory.GENERAL
    timestamp: datetime = field(default_factory=datetime.now)
    title: str = ""
    description: str = ""
    impact_score: float = 0.0  # 0-100
    importance: int = 1  # 1-5
    related_entity_id: str = ""
    related_entity_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    is_public: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'event_type': self.event_type.value,
            'category': self.category.value,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'description': self.description,
            'impact_score': self.impact_score,
            'importance': self.importance,
            'related_entity_id': self.related_entity_id,
            'related_entity_type': self.related_entity_type,
            'metadata': self.metadata,
            'tags': self.tags,
            'notes': self.notes,
            'is_public': self.is_public
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SustainabilityEvent':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            household_id=data.get('household_id'),
            event_type=EventType(data.get('event_type', 'goal_created')),
            category=EventCategory(data.get('category', 'general')),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            title=data.get('title', ''),
            description=data.get('description', ''),
            impact_score=data.get('impact_score', 0.0),
            importance=data.get('importance', 1),
            related_entity_id=data.get('related_entity_id', ''),
            related_entity_type=data.get('related_entity_type', ''),
            metadata=data.get('metadata', {}),
            tags=data.get('tags', []),
            notes=data.get('notes', ''),
            is_public=data.get('is_public', False)
        )


@dataclass
class MilestoneEvent:
    """
    Represents a milestone in the sustainability journey.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    event_id: str = ""
    milestone_type: str = ""  # achievement, goal_completion, habit_streak, etc.
    title: str = ""
    description: str = ""
    achieved_at: datetime = field(default_factory=datetime.now)
    progress_before: float = 0.0
    progress_after: float = 0.0
    improvement_percentage: float = 0.0
    category: str = ""
    icon: str = "⭐"
    is_major: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_id': self.event_id,
            'milestone_type': self.milestone_type,
            'title': self.title,
            'description': self.description,
            'achieved_at': self.achieved_at.isoformat(),
            'progress_before': self.progress_before,
            'progress_after': self.progress_after,
            'improvement_percentage': self.improvement_percentage,
            'category': self.category,
            'icon': self.icon,
            'is_major': self.is_major,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MilestoneEvent':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            event_id=data.get('event_id', ''),
            milestone_type=data.get('milestone_type', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            achieved_at=datetime.fromisoformat(data['achieved_at']) if data.get('achieved_at') else datetime.now(),
            progress_before=data.get('progress_before', 0.0),
            progress_after=data.get('progress_after', 0.0),
            improvement_percentage=data.get('improvement_percentage', 0.0),
            category=data.get('category', ''),
            icon=data.get('icon', '⭐'),
            is_major=data.get('is_major', False),
            notes=data.get('notes', '')
        )


@dataclass
class GoalLifecycle:
    """
    Tracks the complete lifecycle of a sustainability goal.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    goal_id: str = ""
    goal_name: str = ""
    category: str = ""
    description: str = ""
    
    # Creation
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    
    # Timeline
    started_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    postponed_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Status
    status: LifecycleStatus = LifecycleStatus.DRAFT
    stage: LifecycleStage = LifecycleStage.CREATION
    
    # Progress
    initial_target: float = 0.0
    current_progress: float = 0.0
    final_achievement: float = 0.0
    progress_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metrics
    total_duration_days: int = 0
    active_duration_days: int = 0
    postponed_duration_days: int = 0
    completion_rate: float = 0.0
    
    # Dependencies
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    
    # Relationships
    related_habits: List[str] = field(default_factory=list)
    related_roadmaps: List[str] = field(default_factory=list)
    
    # Metadata
    priority: int = 3  # 1-5
    difficulty: int = 3  # 1-5
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'goal_name': self.goal_name,
            'category': self.category,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'created_by': self.created_by,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'postponed_at': self.postponed_at.isoformat() if self.postponed_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'status': self.status.value,
            'stage': self.stage.value,
            'initial_target': self.initial_target,
            'current_progress': self.current_progress,
            'final_achievement': self.final_achievement,
            'progress_history': self.progress_history,
            'total_duration_days': self.total_duration_days,
            'active_duration_days': self.active_duration_days,
            'postponed_duration_days': self.postponed_duration_days,
            'completion_rate': self.completion_rate,
            'dependencies': self.dependencies,
            'dependents': self.dependents,
            'related_habits': self.related_habits,
            'related_roadmaps': self.related_roadmaps,
            'priority': self.priority,
            'difficulty': self.difficulty,
            'tags': self.tags,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoalLifecycle':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            goal_id=data.get('goal_id', ''),
            goal_name=data.get('goal_name', ''),
            category=data.get('category', ''),
            description=data.get('description', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            created_by=data.get('created_by', ''),
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            modified_at=datetime.fromisoformat(data['modified_at']) if data.get('modified_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            failed_at=datetime.fromisoformat(data['failed_at']) if data.get('failed_at') else None,
            postponed_at=datetime.fromisoformat(data['postponed_at']) if data.get('postponed_at') else None,
            recovered_at=datetime.fromisoformat(data['recovered_at']) if data.get('recovered_at') else None,
            archived_at=datetime.fromisoformat(data['archived_at']) if data.get('archived_at') else None,
            status=LifecycleStatus(data.get('status', 'draft')),
            stage=LifecycleStage(data.get('stage', 'creation')),
            initial_target=data.get('initial_target', 0.0),
            current_progress=data.get('current_progress', 0.0),
            final_achievement=data.get('final_achievement', 0.0),
            progress_history=data.get('progress_history', []),
            total_duration_days=data.get('total_duration_days', 0),
            active_duration_days=data.get('active_duration_days', 0),
            postponed_duration_days=data.get('postponed_duration_days', 0),
            completion_rate=data.get('completion_rate', 0.0),
            dependencies=data.get('dependencies', []),
            dependents=data.get('dependents', []),
            related_habits=data.get('related_habits', []),
            related_roadmaps=data.get('related_roadmaps', []),
            priority=data.get('priority', 3),
            difficulty=data.get('difficulty', 3),
            tags=data.get('tags', []),
            notes=data.get('notes', '')
        )


@dataclass
class HabitLifecycle:
    """
    Tracks the complete lifecycle of a sustainability habit.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    habit_id: str = ""
    habit_name: str = ""
    category: str = ""
    description: str = ""
    
    # Timeline
    adopted_at: datetime = field(default_factory=datetime.now)
    improved_at: Optional[datetime] = None
    regressed_at: Optional[datetime] = None
    broken_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    archived_at: Optional[datetime] = None
    
    # Status
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    stage: LifecycleStage = LifecycleStage.ACTIVE
    
    # Performance metrics
    consistency_score: float = 0.0  # 0-100
    streak_days: int = 0
    longest_streak: int = 0
    break_days: int = 0
    improvement_rate: float = 0.0
    completion_rate: float = 0.0
    
    # History
    daily_performance: List[Dict[str, Any]] = field(default_factory=list)
    weekly_summary: List[Dict[str, Any]] = field(default_factory=list)
    monthly_summary: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recovery
    recovery_count: int = 0
    average_recovery_time_days: float = 0.0
    last_recovery_at: Optional[datetime] = None
    
    # Relationships
    related_goals: List[str] = field(default_factory=list)
    
    # Metadata
    frequency: str = ""  # daily, weekly, monthly
    difficulty: int = 2  # 1-5
    tags: List[str] = field(default_factory=list)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'habit_id': self.habit_id,
            'habit_name': self.habit_name,
            'category': self.category,
            'description': self.description,
            'adopted_at': self.adopted_at.isoformat(),
            'improved_at': self.improved_at.isoformat() if self.improved_at else None,
            'regressed_at': self.regressed_at.isoformat() if self.regressed_at else None,
            'broken_at': self.broken_at.isoformat() if self.broken_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'archived_at': self.archived_at.isoformat() if self.archived_at else None,
            'status': self.status.value,
            'stage': self.stage.value,
            'consistency_score': self.consistency_score,
            'streak_days': self.streak_days,
            'longest_streak': self.longest_streak,
            'break_days': self.break_days,
            'improvement_rate': self.improvement_rate,
            'completion_rate': self.completion_rate,
            'daily_performance': self.daily_performance,
            'weekly_summary': self.weekly_summary,
            'monthly_summary': self.monthly_summary,
            'recovery_count': self.recovery_count,
            'average_recovery_time_days': self.average_recovery_time_days,
            'last_recovery_at': self.last_recovery_at.isoformat() if self.last_recovery_at else None,
            'related_goals': self.related_goals,
            'frequency': self.frequency,
            'difficulty': self.difficulty,
            'tags': self.tags,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HabitLifecycle':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            habit_id=data.get('habit_id', ''),
            habit_name=data.get('habit_name', ''),
            category=data.get('category', ''),
            description=data.get('description', ''),
            adopted_at=datetime.fromisoformat(data['adopted_at']) if data.get('adopted_at') else datetime.now(),
            improved_at=datetime.fromisoformat(data['improved_at']) if data.get('improved_at') else None,
            regressed_at=datetime.fromisoformat(data['regressed_at']) if data.get('regressed_at') else None,
            broken_at=datetime.fromisoformat(data['broken_at']) if data.get('broken_at') else None,
            recovered_at=datetime.fromisoformat(data['recovered_at']) if data.get('recovered_at') else None,
            archived_at=datetime.fromisoformat(data['archived_at']) if data.get('archived_at') else None,
            status=LifecycleStatus(data.get('status', 'active')),
            stage=LifecycleStage(data.get('stage', 'active')),
            consistency_score=data.get('consistency_score', 0.0),
            streak_days=data.get('streak_days', 0),
            longest_streak=data.get('longest_streak', 0),
            break_days=data.get('break_days', 0),
            improvement_rate=data.get('improvement_rate', 0.0),
            completion_rate=data.get('completion_rate', 0.0),
            daily_performance=data.get('daily_performance', []),
            weekly_summary=data.get('weekly_summary', []),
            monthly_summary=data.get('monthly_summary', []),
            recovery_count=data.get('recovery_count', 0),
            average_recovery_time_days=data.get('average_recovery_time_days', 0.0),
            last_recovery_at=datetime.fromisoformat(data['last_recovery_at']) if data.get('last_recovery_at') else None,
            related_goals=data.get('related_goals', []),
            frequency=data.get('frequency', ''),
            difficulty=data.get('difficulty', 2),
            tags=data.get('tags', []),
            notes=data.get('notes', '')
        )


@dataclass
class ProgressSnapshot:
    """
    Historical snapshot of sustainability progress.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    snapshot_date: datetime = field(default_factory=datetime.now)
    period: str = ""  # daily, weekly, monthly, quarterly, yearly
    
    # Overall metrics
    sustainability_score: float = 0.0
    sustainability_trend: float = 0.0
    
    # Environmental metrics
    carbon_footprint: float = 0.0
    carbon_change: float = 0.0
    energy_usage: float = 0.0
    energy_change: float = 0.0
    water_usage: float = 0.0
    water_change: float = 0.0
    waste_generation: float = 0.0
    waste_change: float = 0.0
    
    # Impact metrics
    transportation_impact: float = 0.0
    food_impact: float = 0.0
    shopping_impact: float = 0.0
    household_performance: float = 0.0
    
    # Category breakdown
    category_scores: Dict[str, float] = field(default_factory=dict)
    category_changes: Dict[str, float] = field(default_factory=dict)
    
    # Goals
    goals_completed: int = 0
    goals_active: int = 0
    goals_total: int = 0
    goal_completion_rate: float = 0.0
    
    # Habits
    habits_active: int = 0
    habits_completed: int = 0
    average_consistency: float = 0.0
    total_streak: int = 0
    
    # Achievements
    achievements_unlocked: int = 0
    milestones_reached: int = 0
    
    # Metrics
    metrics_summary: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    previous_snapshot_id: Optional[str] = None
    comparison_summary: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'snapshot_date': self.snapshot_date.isoformat(),
            'period': self.period,
            'sustainability_score': self.sustainability_score,
            'sustainability_trend': self.sustainability_trend,
            'carbon_footprint': self.carbon_footprint,
            'carbon_change': self.carbon_change,
            'energy_usage': self.energy_usage,
            'energy_change': self.energy_change,
            'water_usage': self.water_usage,
            'water_change': self.water_change,
            'waste_generation': self.waste_generation,
            'waste_change': self.waste_change,
            'transportation_impact': self.transportation_impact,
            'food_impact': self.food_impact,
            'shopping_impact': self.shopping_impact,
            'household_performance': self.household_performance,
            'category_scores': self.category_scores,
            'category_changes': self.category_changes,
            'goals_completed': self.goals_completed,
            'goals_active': self.goals_active,
            'goals_total': self.goals_total,
            'goal_completion_rate': self.goal_completion_rate,
            'habits_active': self.habits_active,
            'habits_completed': self.habits_completed,
            'average_consistency': self.average_consistency,
            'total_streak': self.total_streak,
            'achievements_unlocked': self.achievements_unlocked,
            'milestones_reached': self.milestones_reached,
            'metrics_summary': self.metrics_summary,
            'previous_snapshot_id': self.previous_snapshot_id,
            'comparison_summary': self.comparison_summary,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressSnapshot':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            household_id=data.get('household_id'),
            snapshot_date=datetime.fromisoformat(data['snapshot_date']) if data.get('snapshot_date') else datetime.now(),
            period=data.get('period', ''),
            sustainability_score=data.get('sustainability_score', 0.0),
            sustainability_trend=data.get('sustainability_trend', 0.0),
            carbon_footprint=data.get('carbon_footprint', 0.0),
            carbon_change=data.get('carbon_change', 0.0),
            energy_usage=data.get('energy_usage', 0.0),
            energy_change=data.get('energy_change', 0.0),
            water_usage=data.get('water_usage', 0.0),
            water_change=data.get('water_change', 0.0),
            waste_generation=data.get('waste_generation', 0.0),
            waste_change=data.get('waste_change', 0.0),
            transportation_impact=data.get('transportation_impact', 0.0),
            food_impact=data.get('food_impact', 0.0),
            shopping_impact=data.get('shopping_impact', 0.0),
            household_performance=data.get('household_performance', 0.0),
            category_scores=data.get('category_scores', {}),
            category_changes=data.get('category_changes', {}),
            goals_completed=data.get('goals_completed', 0),
            goals_active=data.get('goals_active', 0),
            goals_total=data.get('goals_total', 0),
            goal_completion_rate=data.get('goal_completion_rate', 0.0),
            habits_active=data.get('habits_active', 0),
            habits_completed=data.get('habits_completed', 0),
            average_consistency=data.get('average_consistency', 0.0),
            total_streak=data.get('total_streak', 0),
            achievements_unlocked=data.get('achievements_unlocked', 0),
            milestones_reached=data.get('milestones_reached', 0),
            metrics_summary=data.get('metrics_summary', {}),
            previous_snapshot_id=data.get('previous_snapshot_id'),
            comparison_summary=data.get('comparison_summary', {}),
            notes=data.get('notes', '')
        )


@dataclass
class LongTermAnalytics:
    """
    Long-term analytics for sustainability journey.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    period: str = ""  # monthly, quarterly, yearly
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    sustainability_score_avg: float = 0.0
    sustainability_score_median: float = 0.0
    sustainability_score_trend: float = 0.0
    sustainability_score_variance: float = 0.0
    
    # Category trends
    category_trends: Dict[str, float] = field(default_factory=dict)
    category_averages: Dict[str, float] = field(default_factory=dict)
    
    # Improvement metrics
    total_improvement_percentage: float = 0.0
    average_monthly_improvement: float = 0.0
    best_monthly_improvement: float = 0.0
    worst_monthly_improvement: float = 0.0
    consistency_score: float = 0.0
    
    # Environmental impact
    total_carbon_reduction: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    total_energy_saved: float = 0.0
    
    # Goal metrics
    goals_completed: int = 0
    goals_failed: int = 0
    goals_active: int = 0
    goal_success_rate: float = 0.0
    average_goal_completion_time_days: float = 0.0
    
    # Habit metrics
    habit_consistency_avg: float = 0.0
    habit_improvement_rate: float = 0.0
    habit_adoption_rate: float = 0.0
    habit_regression_rate: float = 0.0
    
    # Achievement metrics
    achievements_unlocked: int = 0
    milestones_reached: int = 0
    major_improvements: int = 0
    
    # Trends
    improving_trends: List[str] = field(default_factory=list)
    declining_trends: List[str] = field(default_factory=list)
    stable_trends: List[str] = field(default_factory=list)
    
    # Insights
    key_insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period': self.period,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'sustainability_score_avg': self.sustainability_score_avg,
            'sustainability_score_median': self.sustainability_score_median,
            'sustainability_score_trend': self.sustainability_score_trend,
            'sustainability_score_variance': self.sustainability_score_variance,
            'category_trends': self.category_trends,
            'category_averages': self.category_averages,
            'total_improvement_percentage': self.total_improvement_percentage,
            'average_monthly_improvement': self.average_monthly_improvement,
            'best_monthly_improvement': self.best_monthly_improvement,
            'worst_monthly_improvement': self.worst_monthly_improvement,
            'consistency_score': self.consistency_score,
            'total_carbon_reduction': self.total_carbon_reduction,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'total_energy_saved': self.total_energy_saved,
            'goals_completed': self.goals_completed,
            'goals_failed': self.goals_failed,
            'goals_active': self.goals_active,
            'goal_success_rate': self.goal_success_rate,
            'average_goal_completion_time_days': self.average_goal_completion_time_days,
            'habit_consistency_avg': self.habit_consistency_avg,
            'habit_improvement_rate': self.habit_improvement_rate,
            'habit_adoption_rate': self.habit_adoption_rate,
            'habit_regression_rate': self.habit_regression_rate,
            'achievements_unlocked': self.achievements_unlocked,
            'milestones_reached': self.milestones_reached,
            'major_improvements': self.major_improvements,
            'improving_trends': self.improving_trends,
            'declining_trends': self.declining_trends,
            'stable_trends': self.stable_trends,
            'key_insights': self.key_insights,
            'recommendations': self.recommendations
        }


@dataclass
class FutureProjection:
    """
    Projection of future sustainability performance.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    projection_date: datetime = field(default_factory=datetime.now)
    projection_type: str = ""  # sustainability, carbon, goal_completion, etc.
    
    # Current trajectory
    current_trend: float = 0.0
    trend_confidence: float = 0.0
    data_points_used: int = 0
    
    # Projections
    projected_value: float = 0.0
    projected_value_lower: float = 0.0
    projected_value_upper: float = 0.0
    confidence_interval: float = 0.0
    
    # Timeline
    projection_days_ahead: int = 0
    projection_period: str = ""  # days, weeks, months, years
    target_date: Optional[datetime] = None
    
    # Goal completion
    estimated_completion_date: Optional[datetime] = None
    estimated_completion_probability: float = 0.0
    
    # Long-term impact
    projected_carbon_savings: float = 0.0
    projected_water_savings: float = 0.0
    projected_waste_reduction: float = 0.0
    projected_cost_savings: float = 0.0
    
    # Scenarios
    best_case: Dict[str, float] = field(default_factory=dict)
    worst_case: Dict[str, float] = field(default_factory=dict)
    most_likely: Dict[str, float] = field(default_factory=dict)
    
    # Model information
    model_used: str = ""
    model_accuracy: float = 0.0
    r_squared: float = 0.0
    
    # Metadata
    is_reliable: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'projection_date': self.projection_date.isoformat(),
            'projection_type': self.projection_type,
            'current_trend': self.current_trend,
            'trend_confidence': self.trend_confidence,
            'data_points_used': self.data_points_used,
            'projected_value': self.projected_value,
            'projected_value_lower': self.projected_value_lower,
            'projected_value_upper': self.projected_value_upper,
            'confidence_interval': self.confidence_interval,
            'projection_days_ahead': self.projection_days_ahead,
            'projection_period': self.projection_period,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'estimated_completion_date': self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,
            'estimated_completion_probability': self.estimated_completion_probability,
            'projected_carbon_savings': self.projected_carbon_savings,
            'projected_water_savings': self.projected_water_savings,
            'projected_waste_reduction': self.projected_waste_reduction,
            'projected_cost_savings': self.projected_cost_savings,
            'best_case': self.best_case,
            'worst_case': self.worst_case,
            'most_likely': self.most_likely,
            'model_used': self.model_used,
            'model_accuracy': self.model_accuracy,
            'r_squared': self.r_squared,
            'is_reliable': self.is_reliable,
            'notes': self.notes
        }


@dataclass
class AchievementHistory:
    """
    Tracks achievements, milestones, and records.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    achievement_type: str = ""  # achievement, milestone, challenge, record
    title: str = ""
    description: str = ""
    category: str = ""
    unlocked_at: datetime = field(default_factory=datetime.now)
    difficulty: str = ""  # easy, medium, hard, expert
    points: int = 0
    icon: str = "🏆"
    badge_color: str = "#FFD700"
    
    # Achievement details
    requirements: List[str] = field(default_factory=list)
    progress_before: float = 0.0
    progress_after: float = 0.0
    
    # Related entities
    related_entity_id: str = ""
    related_entity_type: str = ""
    
    # Sharing
    is_shared: bool = False
    shared_at: Optional[datetime] = None
    
    # Metadata
    is_verified: bool = False
    verified_at: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_type': self.achievement_type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'unlocked_at': self.unlocked_at.isoformat(),
            'difficulty': self.difficulty,
            'points': self.points,
            'icon': self.icon,
            'badge_color': self.badge_color,
            'requirements': self.requirements,
            'progress_before': self.progress_before,
            'progress_after': self.progress_after,
            'related_entity_id': self.related_entity_id,
            'related_entity_type': self.related_entity_type,
            'is_shared': self.is_shared,
            'shared_at': self.shared_at.isoformat() if self.shared_at else None,
            'is_verified': self.is_verified,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AchievementHistory':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            achievement_type=data.get('achievement_type', ''),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            unlocked_at=datetime.fromisoformat(data['unlocked_at']) if data.get('unlocked_at') else datetime.now(),
            difficulty=data.get('difficulty', ''),
            points=data.get('points', 0),
            icon=data.get('icon', '🏆'),
            badge_color=data.get('badge_color', '#FFD700'),
            requirements=data.get('requirements', []),
            progress_before=data.get('progress_before', 0.0),
            progress_after=data.get('progress_after', 0.0),
            related_entity_id=data.get('related_entity_id', ''),
            related_entity_type=data.get('related_entity_type', ''),
            is_shared=data.get('is_shared', False),
            shared_at=datetime.fromisoformat(data['shared_at']) if data.get('shared_at') else None,
            is_verified=data.get('is_verified', False),
            verified_at=datetime.fromisoformat(data['verified_at']) if data.get('verified_at') else None,
            notes=data.get('notes', '')
        )


@dataclass
class DecisionHistory:
    """
    Tracks sustainability decisions and their outcomes.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    decision_type: str = ""  # purchase, habit_change, lifestyle, investment
    title: str = ""
    description: str = ""
    category: str = ""
    
    # Decision details
    decision_date: datetime = field(default_factory=datetime.now)
    alternatives_considered: List[str] = field(default_factory=list)
    chosen_option: str = ""
    reason: str = ""
    decision_context: str = ""
    
    # Outcome
    outcome_successful: bool = False
    outcome_impact_score: float = 0.0
    outcome_description: str = ""
    outcome_date: Optional[datetime] = None
    
    # Impact
    carbon_impact_kg: float = 0.0
    water_impact_liters: float = 0.0
    waste_impact_kg: float = 0.0
    cost_impact: float = 0.0
    sustainability_impact: float = 0.0
    
    # Review
    review_date: Optional[datetime] = None
    review_notes: str = ""
    effectiveness_rating: float = 0.0
    
    # Related
    related_recommendation_id: str = ""
    related_goal_id: str = ""
    
    # Metadata
    is_recurring: bool = False
    recurrence_frequency: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'decision_type': self.decision_type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'decision_date': self.decision_date.isoformat(),
            'alternatives_considered': self.alternatives_considered,
            'chosen_option': self.chosen_option,
            'reason': self.reason,
            'decision_context': self.decision_context,
            'outcome_successful': self.outcome_successful,
            'outcome_impact_score': self.outcome_impact_score,
            'outcome_description': self.outcome_description,
            'outcome_date': self.outcome_date.isoformat() if self.outcome_date else None,
            'carbon_impact_kg': self.carbon_impact_kg,
            'water_impact_liters': self.water_impact_liters,
            'waste_impact_kg': self.waste_impact_kg,
            'cost_impact': self.cost_impact,
            'sustainability_impact': self.sustainability_impact,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'review_notes': self.review_notes,
            'effectiveness_rating': self.effectiveness_rating,
            'related_recommendation_id': self.related_recommendation_id,
            'related_goal_id': self.related_goal_id,
            'is_recurring': self.is_recurring,
            'recurrence_frequency': self.recurrence_frequency,
            'notes': self.notes
        }


@dataclass
class RecommendationHistory:
    """
    Tracks recommendations received and their effectiveness.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    recommendation_id: str = ""
    recommendation_text: str = ""
    category: str = ""
    
    # Status
    received_date: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    
    # Actions
    was_accepted: bool = False
    was_implemented: bool = False
    implementation_notes: str = ""
    
    # Outcome
    outcome_successful: bool = False
    outcome_score: float = 0.0
    
    # Impact
    actual_impact: float = 0.0
    expected_impact: float = 0.0
    impact_difference: float = 0.0
    impact_difference_percentage: float = 0.0
    
    # Metadata
    source: str = ""  # AI, human, system
    confidence: float = 0.0
    effectiveness_rating: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recommendation_id': self.recommendation_id,
            'recommendation_text': self.recommendation_text,
            'category': self.category,
            'received_date': self.received_date.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'was_accepted': self.was_accepted,
            'was_implemented': self.was_implemented,
            'implementation_notes': self.implementation_notes,
            'outcome_successful': self.outcome_successful,
            'outcome_score': self.outcome_score,
            'actual_impact': self.actual_impact,
            'expected_impact': self.expected_impact,
            'impact_difference': self.impact_difference,
            'impact_difference_percentage': self.impact_difference_percentage,
            'source': self.source,
            'confidence': self.confidence,
            'effectiveness_rating': self.effectiveness_rating,
            'notes': self.notes
        }


@dataclass
class RoadmapHistory:
    """
    Tracks roadmap progress and history.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    roadmap_id: str = ""
    roadmap_name: str = ""
    
    # Creation
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Stages
    current_stage: int = 0
    total_stages: int = 0
    completed_stages: List[int] = field(default_factory=list)
    stage_progress: Dict[str, float] = field(default_factory=dict)
    
    # Milestones
    milestones_completed: int = 0
    milestones_missed: int = 0
    milestones_total: int = 0
    milestone_details: List[Dict[str, Any]] = field(default_factory=list)
    
    # Alternative paths
    alternatives_taken: int = 0
    alternative_paths: List[Dict[str, Any]] = field(default_factory=list)
    
    # History
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    milestone_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Version
    versions: List[Dict[str, Any]] = field(default_factory=list)
    current_version: int = 1
    
    # Metadata
    status: str = "active"
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'roadmap_id': self.roadmap_id,
            'roadmap_name': self.roadmap_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_stage': self.current_stage,
            'total_stages': self.total_stages,
            'completed_stages': self.completed_stages,
            'stage_progress': self.stage_progress,
            'milestones_completed': self.milestones_completed,
            'milestones_missed': self.milestones_missed,
            'milestones_total': self.milestones_total,
            'milestone_details': self.milestone_details,
            'alternatives_taken': self.alternatives_taken,
            'alternative_paths': self.alternative_paths,
            'stage_history': self.stage_history,
            'milestone_history': self.milestone_history,
            'versions': self.versions,
            'current_version': self.current_version,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'notes': self.notes
        }


@dataclass
class SustainabilityReport:
    """
    Periodic sustainability report.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    report_type: str = ""  # monthly, quarterly, yearly, personal, household
    period: str = ""  # e.g., "2024-01", "Q1 2024", "2024"
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Executive summary
    summary: str = ""
    key_achievements: List[str] = field(default_factory=list)
    areas_for_improvement: List[str] = field(default_factory=list)
    
    # Metrics
    current_sustainability_score: float = 0.0
    previous_sustainability_score: float = 0.0
    score_change: float = 0.0
    score_change_percentage: float = 0.0
    
    # Impact
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_reduced_kg: float = 0.0
    energy_saved_kwh: float = 0.0
    cost_saved: float = 0.0
    
    # Goals
    goals_completed: int = 0
    goals_in_progress: int = 0
    goals_failed: int = 0
    goal_completion_rate: float = 0.0
    
    # Habits
    habit_consistency_avg: float = 0.0
    habits_adopted: int = 0
    habits_maintained: int = 0
    habits_regressed: int = 0
    
    # Achievements
    achievements_unlocked: int = 0
    milestones_reached: int = 0
    
    # Charts data
    chart_data: Dict[str, Any] = field(default_factory=dict)
    
    # Content
    content: str = ""
    file_path: str = ""
    shareable: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'report_type': self.report_type,
            'period': self.period,
            'generated_at': self.generated_at.isoformat(),
            'summary': self.summary,
            'key_achievements': self.key_achievements,
            'areas_for_improvement': self.areas_for_improvement,
            'current_sustainability_score': self.current_sustainability_score,
            'previous_sustainability_score': self.previous_sustainability_score,
            'score_change': self.score_change,
            'score_change_percentage': self.score_change_percentage,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_reduced_kg': self.waste_reduced_kg,
            'energy_saved_kwh': self.energy_saved_kwh,
            'cost_saved': self.cost_saved,
            'goals_completed': self.goals_completed,
            'goals_in_progress': self.goals_in_progress,
            'goals_failed': self.goals_failed,
            'goal_completion_rate': self.goal_completion_rate,
            'habit_consistency_avg': self.habit_consistency_avg,
            'habits_adopted': self.habits_adopted,
            'habits_maintained': self.habits_maintained,
            'habits_regressed': self.habits_regressed,
            'achievements_unlocked': self.achievements_unlocked,
            'milestones_reached': self.milestones_reached,
            'chart_data': self.chart_data,
            'content': self.content,
            'file_path': self.file_path,
            'shareable': self.shareable,
            'notes': self.notes
        }


@dataclass
class TrendAnalysis:
    """
    Analysis of trends in sustainability data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: str = ""
    period: str = ""
    
    # Trend data
    values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    
    # Statistics
    mean: float = 0.0
    median: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    
    # Trend direction
    direction: str = ""  # improving, declining, stable
    slope: float = 0.0
    r_squared: float = 0.0
    
    # Seasonality
    has_seasonality: bool = False
    seasonality_period: int = 0
    
    # Metrics
    change_absolute: float = 0.0
    change_percentage: float = 0.0
    improvement_rate: float = 0.0
    
    # Metadata
    confidence: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric,
            'period': self.period,
            'values': self.values,
            'dates': self.dates,
            'mean': self.mean,
            'median': self.median,
            'variance': self.variance,
            'std_dev': self.std_dev,
            'direction': self.direction,
            'slope': self.slope,
            'r_squared': self.r_squared,
            'has_seasonality': self.has_seasonality,
            'seasonality_period': self.seasonality_period,
            'change_absolute': self.change_absolute,
            'change_percentage': self.change_percentage,
            'improvement_rate': self.improvement_rate,
            'confidence': self.confidence,
            'notes': self.notes
        }


@dataclass
class ComparisonResult:
    """
    Result of comparing two points in time.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    comparison_type: str = ""  # before_after, period_comparison, etc.
    
    # Time points
    from_date: datetime = field(default_factory=datetime.now)
    to_date: datetime = field(default_factory=datetime.now)
    
    # Metrics
    metric_changes: Dict[str, Dict[str, float]] = field(default_factory=dict)
    overall_change: float = 0.0
    overall_change_percentage: float = 0.0
    
    # Category comparisons
    category_comparisons: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Summary
    summary: str = ""
    insights: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'comparison_type': self.comparison_type,
            'from_date': self.from_date.isoformat(),
            'to_date': self.to_date.isoformat(),
            'metric_changes': self.metric_changes,
            'overall_change': self.overall_change,
            'overall_change_percentage': self.overall_change_percentage,
            'category_comparisons': self.category_comparisons,
            'summary': self.summary,
            'insights': self.insights
        }


@dataclass
class HistoricalInsight:
    """
    Insight derived from historical data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    insight_type: str = ""  # achievement, warning, opportunity, trend
    title: str = ""
    description: str = ""
    category: str = ""
    
    # Supporting data
    supporting_metrics: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 0.0
    
    # Action
    recommended_action: str = ""
    priority: str = ""  # high, medium, low
    
    # Metadata
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_actioned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'insight_type': self.insight_type,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'supporting_metrics': self.supporting_metrics,
            'confidence_score': self.confidence_score,
            'recommended_action': self.recommended_action,
            'priority': self.priority,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_actioned': self.is_actioned
        }


@dataclass
class JourneySummary:
    """
    Overall summary of the sustainability journey.
    """
    user_id: str = ""
    start_date: datetime = field(default_factory=datetime.now)
    journey_days: int = 0
    
    # Overall metrics
    current_sustainability_score: float = 0.0
    starting_sustainability_score: float = 0.0
    total_improvement: float = 0.0
    improvement_percentage: float = 0.0
    
    # Counts
    total_goals: int = 0
    completed_goals: int = 0
    active_goals: int = 0
    
    total_habits: int = 0
    active_habits: int = 0
    completed_habits: int = 0
    
    total_achievements: int = 0
    total_milestones: int = 0
    
    # Impact
    total_carbon_saved: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    total_cost_saved: float = 0.0
    
    # Trends
    overall_trend: str = ""  # improving, stable, declining
    best_category: str = ""
    weakest_category: str = ""
    
    # Milestones
    major_milestones: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'start_date': self.start_date.isoformat(),
            'journey_days': self.journey_days,
            'current_sustainability_score': self.current_sustainability_score,
            'starting_sustainability_score': self.starting_sustainability_score,
            'total_improvement': self.total_improvement,
            'improvement_percentage': self.improvement_percentage,
            'total_goals': self.total_goals,
            'completed_goals': self.completed_goals,
            'active_goals': self.active_goals,
            'total_habits': self.total_habits,
            'active_habits': self.active_habits,
            'completed_habits': self.completed_habits,
            'total_achievements': self.total_achievements,
            'total_milestones': self.total_milestones,
            'total_carbon_saved': self.total_carbon_saved,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'total_cost_saved': self.total_cost_saved,
            'overall_trend': self.overall_trend,
            'best_category': self.best_category,
            'weakest_category': self.weakest_category,
            'major_milestones': self.major_milestones
        }