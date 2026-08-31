"""
Sustainability Lifecycle & Long-Term Progress Management - Data Models
Comprehensive models for tracking sustainability journeys.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
import json


class EventType(Enum):
    """Types of sustainability events."""
    GOAL_CREATED = "goal_created"
    GOAL_COMPLETED = "goal_completed"
    GOAL_MODIFIED = "goal_modified"
    GOAL_POSTPONED = "goal_postponed"
    GOAL_FAILED = "goal_failed"
    GOAL_RECOVERED = "goal_recovered"
    HABIT_ADOPTED = "habit_adopted"
    HABIT_IMPROVED = "habit_improved"
    HABIT_REGRESSED = "habit_regressed"
    HABIT_BROKEN = "habit_broken"
    HABIT_RECOVERED = "habit_recovered"
    ROADMAP_CREATED = "roadmap_created"
    ROADMAP_MILESTONE = "roadmap_milestone"
    ROADMAP_COMPLETED = "roadmap_completed"
    ROADMAP_ALTERNATIVE = "roadmap_alternative"
    BENCHMARK_CHANGED = "benchmark_changed"
    RECOMMENDATION_ACCEPTED = "recommendation_accepted"
    RECOMMENDATION_REJECTED = "recommendation_rejected"
    ACHIEVEMENT_UNLOCKED = "achievement_unlocked"
    CHALLENGE_COMPLETED = "challenge_completed"
    MAJOR_IMPROVEMENT = "major_improvement"
    DECISION_MADE = "decision_made"
    SNAPSHOT_TAKEN = "snapshot_taken"
    MILESTONE_REACHED = "milestone_reached"
    PERIODIC_REPORT = "periodic_report"


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


class TimelinePeriod(Enum):
    """Period for timeline views."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ALL = "all"


@dataclass
class SustainabilityEvent:
    """
    Represents a sustainability event in the user's journey.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    event_type: EventType = EventType.GOAL_CREATED
    timestamp: datetime = field(default_factory=datetime.now)
    title: str = ""
    description: str = ""
    category: str = ""
    impact_score: float = 0.0  # 0-100
    metadata: Dict[str, Any] = field(default_factory=dict)
    related_entity_id: str = ""
    related_entity_type: str = ""
    importance: int = 1  # 1-5
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'impact_score': self.impact_score,
            'metadata': self.metadata,
            'related_entity_id': self.related_entity_id,
            'related_entity_type': self.related_entity_type,
            'importance': self.importance,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SustainabilityEvent':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            event_type=EventType(data.get('event_type', 'goal_created')),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            title=data.get('title', ''),
            description=data.get('description', ''),
            category=data.get('category', ''),
            impact_score=data.get('impact_score', 0.0),
            metadata=data.get('metadata', {}),
            related_entity_id=data.get('related_entity_id', ''),
            related_entity_type=data.get('related_entity_type', ''),
            importance=data.get('importance', 1),
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
    
    # Lifecycle stages
    created_at: datetime = field(default_factory=datetime.now)
    modified_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    postponed_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    
    # Status
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    
    # Progress
    initial_target: float = 0.0
    current_progress: float = 0.0
    final_achievement: float = 0.0
    
    # History
    history_entries: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    # Metrics
    total_duration_days: int = 0
    active_duration_days: int = 0
    postponed_duration_days: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'goal_name': self.goal_name,
            'category': self.category,
            'created_at': self.created_at.isoformat(),
            'modified_at': self.modified_at.isoformat() if self.modified_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'failed_at': self.failed_at.isoformat() if self.failed_at else None,
            'postponed_at': self.postponed_at.isoformat() if self.postponed_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'status': self.status.value,
            'initial_target': self.initial_target,
            'current_progress': self.current_progress,
            'final_achievement': self.final_achievement,
            'history_entries': self.history_entries,
            'dependencies': self.dependencies,
            'total_duration_days': self.total_duration_days,
            'active_duration_days': self.active_duration_days,
            'postponed_duration_days': self.postponed_duration_days
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GoalLifecycle':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            goal_id=data.get('goal_id', ''),
            goal_name=data.get('goal_name', ''),
            category=data.get('category', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            modified_at=datetime.fromisoformat(data['modified_at']) if data.get('modified_at') else None,
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else None,
            completed_at=datetime.fromisoformat(data['completed_at']) if data.get('completed_at') else None,
            failed_at=datetime.fromisoformat(data['failed_at']) if data.get('failed_at') else None,
            postponed_at=datetime.fromisoformat(data['postponed_at']) if data.get('postponed_at') else None,
            recovered_at=datetime.fromisoformat(data['recovered_at']) if data.get('recovered_at') else None,
            status=LifecycleStatus(data.get('status', 'active')),
            initial_target=data.get('initial_target', 0.0),
            current_progress=data.get('current_progress', 0.0),
            final_achievement=data.get('final_achievement', 0.0),
            history_entries=data.get('history_entries', []),
            dependencies=data.get('dependencies', []),
            total_duration_days=data.get('total_duration_days', 0),
            active_duration_days=data.get('active_duration_days', 0),
            postponed_duration_days=data.get('postponed_duration_days', 0)
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
    
    # Timeline
    adopted_at: datetime = field(default_factory=datetime.now)
    improved_at: Optional[datetime] = None
    regressed_at: Optional[datetime] = None
    broken_at: Optional[datetime] = None
    recovered_at: Optional[datetime] = None
    
    # Status
    status: LifecycleStatus = LifecycleStatus.ACTIVE
    
    # Performance metrics
    consistency_score: float = 0.0  # 0-100
    streak_days: int = 0
    longest_streak: int = 0
    break_days: int = 0
    improvement_rate: float = 0.0  # Percentage change
    
    # History
    daily_performance: List[Dict[str, Any]] = field(default_factory=list)
    weekly_summary: List[Dict[str, Any]] = field(default_factory=list)
    monthly_summary: List[Dict[str, Any]] = field(default_factory=list)
    
    # Recovery
    recovery_count: int = 0
    average_recovery_time_days: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'habit_id': self.habit_id,
            'habit_name': self.habit_name,
            'category': self.category,
            'adopted_at': self.adopted_at.isoformat(),
            'improved_at': self.improved_at.isoformat() if self.improved_at else None,
            'regressed_at': self.regressed_at.isoformat() if self.regressed_at else None,
            'broken_at': self.broken_at.isoformat() if self.broken_at else None,
            'recovered_at': self.recovered_at.isoformat() if self.recovered_at else None,
            'status': self.status.value,
            'consistency_score': self.consistency_score,
            'streak_days': self.streak_days,
            'longest_streak': self.longest_streak,
            'break_days': self.break_days,
            'improvement_rate': self.improvement_rate,
            'daily_performance': self.daily_performance,
            'weekly_summary': self.weekly_summary,
            'monthly_summary': self.monthly_summary,
            'recovery_count': self.recovery_count,
            'average_recovery_time_days': self.average_recovery_time_days
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HabitLifecycle':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            habit_id=data.get('habit_id', ''),
            habit_name=data.get('habit_name', ''),
            category=data.get('category', ''),
            adopted_at=datetime.fromisoformat(data['adopted_at']) if data.get('adopted_at') else datetime.now(),
            improved_at=datetime.fromisoformat(data['improved_at']) if data.get('improved_at') else None,
            regressed_at=datetime.fromisoformat(data['regressed_at']) if data.get('regressed_at') else None,
            broken_at=datetime.fromisoformat(data['broken_at']) if data.get('broken_at') else None,
            recovered_at=datetime.fromisoformat(data['recovered_at']) if data.get('recovered_at') else None,
            status=LifecycleStatus(data.get('status', 'active')),
            consistency_score=data.get('consistency_score', 0.0),
            streak_days=data.get('streak_days', 0),
            longest_streak=data.get('longest_streak', 0),
            break_days=data.get('break_days', 0),
            improvement_rate=data.get('improvement_rate', 0.0),
            daily_performance=data.get('daily_performance', []),
            weekly_summary=data.get('weekly_summary', []),
            monthly_summary=data.get('monthly_summary', []),
            recovery_count=data.get('recovery_count', 0),
            average_recovery_time_days=data.get('average_recovery_time_days', 0.0)
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
    
    # Sustainability metrics
    sustainability_score: float = 0.0
    carbon_footprint: float = 0.0
    energy_usage: float = 0.0
    water_usage: float = 0.0
    waste_generation: float = 0.0
    transportation_impact: float = 0.0
    food_impact: float = 0.0
    shopping_impact: float = 0.0
    household_performance: float = 0.0
    
    # Category breakdown
    category_scores: Dict[str, float] = field(default_factory=dict)
    
    # Goals
    goals_completed: int = 0
    goals_active: int = 0
    goals_total: int = 0
    
    # Habits
    habits_active: int = 0
    habits_completed: int = 0
    average_consistency: float = 0.0
    
    # Achievements
    achievements_unlocked: int = 0
    milestones_reached: int = 0
    
    # Metadata
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'snapshot_date': self.snapshot_date.isoformat(),
            'period': self.period,
            'sustainability_score': self.sustainability_score,
            'carbon_footprint': self.carbon_footprint,
            'energy_usage': self.energy_usage,
            'water_usage': self.water_usage,
            'waste_generation': self.waste_generation,
            'transportation_impact': self.transportation_impact,
            'food_impact': self.food_impact,
            'shopping_impact': self.shopping_impact,
            'household_performance': self.household_performance,
            'category_scores': self.category_scores,
            'goals_completed': self.goals_completed,
            'goals_active': self.goals_active,
            'goals_total': self.goals_total,
            'habits_active': self.habits_active,
            'habits_completed': self.habits_completed,
            'average_consistency': self.average_consistency,
            'achievements_unlocked': self.achievements_unlocked,
            'milestones_reached': self.milestones_reached,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
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
            carbon_footprint=data.get('carbon_footprint', 0.0),
            energy_usage=data.get('energy_usage', 0.0),
            water_usage=data.get('water_usage', 0.0),
            waste_generation=data.get('waste_generation', 0.0),
            transportation_impact=data.get('transportation_impact', 0.0),
            food_impact=data.get('food_impact', 0.0),
            shopping_impact=data.get('shopping_impact', 0.0),
            household_performance=data.get('household_performance', 0.0),
            category_scores=data.get('category_scores', {}),
            goals_completed=data.get('goals_completed', 0),
            goals_active=data.get('goals_active', 0),
            goals_total=data.get('goals_total', 0),
            habits_active=data.get('habits_active', 0),
            habits_completed=data.get('habits_completed', 0),
            average_consistency=data.get('average_consistency', 0.0),
            achievements_unlocked=data.get('achievements_unlocked', 0),
            milestones_reached=data.get('milestones_reached', 0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class LongTermAnalytics:
    """
    Long-term analytics for sustainability journey.
    """
    user_id: str = ""
    period: str = ""  # monthly, quarterly, yearly
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    sustainability_score_avg: float = 0.0
    sustainability_score_trend: float = 0.0
    
    # Category trends
    category_trends: Dict[str, float] = field(default_factory=dict)
    
    # Improvement metrics
    total_improvement_percentage: float = 0.0
    average_monthly_improvement: float = 0.0
    best_monthly_improvement: float = 0.0
    worst_monthly_improvement: float = 0.0
    
    # Environmental impact
    total_carbon_reduction: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    
    # Goal metrics
    goals_completed: int = 0
    goals_failed: int = 0
    goal_success_rate: float = 0.0
    
    # Habit metrics
    habit_consistency_avg: float = 0.0
    habit_improvement_rate: float = 0.0
    
    # Achievement metrics
    achievements_unlocked: int = 0
    milestones_reached: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'period': self.period,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'sustainability_score_avg': self.sustainability_score_avg,
            'sustainability_score_trend': self.sustainability_score_trend,
            'category_trends': self.category_trends,
            'total_improvement_percentage': self.total_improvement_percentage,
            'average_monthly_improvement': self.average_monthly_improvement,
            'best_monthly_improvement': self.best_monthly_improvement,
            'worst_monthly_improvement': self.worst_monthly_improvement,
            'total_carbon_reduction': self.total_carbon_reduction,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'goals_completed': self.goals_completed,
            'goals_failed': self.goals_failed,
            'goal_success_rate': self.goal_success_rate,
            'habit_consistency_avg': self.habit_consistency_avg,
            'habit_improvement_rate': self.habit_improvement_rate,
            'achievements_unlocked': self.achievements_unlocked,
            'milestones_reached': self.milestones_reached
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
    confidence_interval: Tuple[float, float] = (0.0, 0.0)
    
    # Projections
    projected_value: float = 0.0
    projected_value_lower: float = 0.0
    projected_value_upper: float = 0.0
    
    # Timeline
    projection_days_ahead: int = 0
    target_date: Optional[datetime] = None
    
    # Goal completion
    estimated_completion_date: Optional[datetime] = None
    estimated_completion_probability: float = 0.0
    
    # Long-term impact
    projected_carbon_savings: float = 0.0
    projected_cost_savings: float = 0.0
    
    # Metadata
    model_used: str = ""
    accuracy_score: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'projection_date': self.projection_date.isoformat(),
            'projection_type': self.projection_type,
            'current_trend': self.current_trend,
            'confidence_interval': self.confidence_interval,
            'projected_value': self.projected_value,
            'projected_value_lower': self.projected_value_lower,
            'projected_value_upper': self.projected_value_upper,
            'projection_days_ahead': self.projection_days_ahead,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'estimated_completion_date': self.estimated_completion_date.isoformat() if self.estimated_completion_date else None,
            'estimated_completion_probability': self.estimated_completion_probability,
            'projected_carbon_savings': self.projected_carbon_savings,
            'projected_cost_savings': self.projected_cost_savings,
            'model_used': self.model_used,
            'accuracy_score': self.accuracy_score,
            'notes': self.notes
        }


@dataclass
class AchievementHistory:
    """
    Tracks achievements and milestones.
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
    icon: str = ""
    related_entity_id: str = ""
    related_entity_type: str = ""
    is_shared: bool = False
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
            'related_entity_id': self.related_entity_id,
            'related_entity_type': self.related_entity_type,
            'is_shared': self.is_shared,
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
            icon=data.get('icon', ''),
            related_entity_id=data.get('related_entity_id', ''),
            related_entity_type=data.get('related_entity_type', ''),
            is_shared=data.get('is_shared', False),
            notes=data.get('notes', '')
        )


@dataclass
class DecisionHistory:
    """
    Tracks sustainability decisions and outcomes.
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
    
    # Outcome
    outcome_successful: bool = False
    outcome_impact_score: float = 0.0
    outcome_description: str = ""
    
    # Impact
    carbon_impact_kg: float = 0.0
    cost_impact: float = 0.0
    sustainability_impact: float = 0.0
    
    # Metadata
    related_recommendation_id: str = ""
    review_date: Optional[datetime] = None
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
            'outcome_successful': self.outcome_successful,
            'outcome_impact_score': self.outcome_impact_score,
            'outcome_description': self.outcome_description,
            'carbon_impact_kg': self.carbon_impact_kg,
            'cost_impact': self.cost_impact,
            'sustainability_impact': self.sustainability_impact,
            'related_recommendation_id': self.related_recommendation_id,
            'review_date': self.review_date.isoformat() if self.review_date else None,
            'notes': self.notes
        }


@dataclass
class RecommendationHistory:
    """
    Tracks recommendations received and their outcomes.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    recommendation_id: str = ""
    recommendation_text: str = ""
    category: str = ""
    
    # Status
    received_date: datetime = field(default_factory=datetime.now)
    accepted_at: Optional[datetime] = None
    rejected_at: Optional[datetime] = None
    implemented_at: Optional[datetime] = None
    
    # Outcome
    was_accepted: bool = False
    was_implemented: bool = False
    outcome_successful: bool = False
    
    # Impact
    actual_impact: float = 0.0
    expected_impact: float = 0.0
    impact_difference: float = 0.0
    
    # Metadata
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
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'implemented_at': self.implemented_at.isoformat() if self.implemented_at else None,
            'was_accepted': self.was_accepted,
            'was_implemented': self.was_implemented,
            'outcome_successful': self.outcome_successful,
            'actual_impact': self.actual_impact,
            'expected_impact': self.expected_impact,
            'impact_difference': self.impact_difference,
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
    completed_at: Optional[datetime] = None
    
    # Stages
    current_stage: int = 0
    total_stages: int = 0
    completed_stages: List[int] = field(default_factory=list)
    
    # Milestones
    milestones_completed: int = 0
    milestones_missed: int = 0
    milestones_total: int = 0
    
    # Alternative paths
    alternatives_taken: int = 0
    alternative_paths: List[Dict[str, Any]] = field(default_factory=list)
    
    # History
    stage_history: List[Dict[str, Any]] = field(default_factory=list)
    milestone_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Version
    versions: List[Dict[str, Any]] = field(default_factory=list)
    current_version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'roadmap_id': self.roadmap_id,
            'roadmap_name': self.roadmap_name,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'current_stage': self.current_stage,
            'total_stages': self.total_stages,
            'completed_stages': self.completed_stages,
            'milestones_completed': self.milestones_completed,
            'milestones_missed': self.milestones_missed,
            'milestones_total': self.milestones_total,
            'alternatives_taken': self.alternatives_taken,
            'alternative_paths': self.alternative_paths,
            'stage_history': self.stage_history,
            'milestone_history': self.milestone_history,
            'versions': self.versions,
            'current_version': self.current_version
        }


@dataclass
class SustainabilityReport:
    """
    Periodic sustainability report.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None    report_type: str = ""  # monthly, quarterly, yearly, personal, household
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
    
    # Impact
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_reduced_kg: float = 0.0
    cost_saved: float = 0.0
    
    # Goals
    goals_completed: int = 0
    goals_in_progress: int = 0
    goal_completion_rate: float = 0.0
    
    # Habits
    habit_consistency_avg: float = 0.0
    habits_adopted: int = 0
    habits_maintained: int = 0
    
    # Achievements
    achievements_unlocked: int = 0
    
    # Charts data
    chart_data: Dict[str, Any] = field(default_factory=dict)
    
    # Content
    content: str = ""
    file_path: str = ""
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
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_reduced_kg': self.waste_reduced_kg,
            'cost_saved': self.cost_saved,
            'goals_completed': self.goals_completed,
            'goals_in_progress': self.goals_in_progress,
            'goal_completion_rate': self.goal_completion_rate,
            'habit_consistency_avg': self.habit_consistency_avg,
            'habits_adopted': self.habits_adopted,
            'habits_maintained': self.habits_maintained,
            'achievements_unlocked': self.achievements_unlocked,
            'chart_data': self.chart_data,
            'content': self.content,
            'file_path': self.file_path,
            'notes': self.notes
        }