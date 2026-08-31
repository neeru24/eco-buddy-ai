"""
Sustainability Analytics & Forecasting Engine - Data Models
Comprehensive models for analytics and forecasting.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
import uuid
import json


class TrendType(Enum):
    """Types of trends."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"
    VOLATILE = "volatile"
    CYCLICAL = "cyclical"
    EXPONENTIAL = "exponential"
    LOGARITHMIC = "logarithmic"
    S_CURVE = "s_curve"
    PLATEAU = "plateau"
    UNDEFINED = "undefined"


class ForecastModel(Enum):
    """Forecasting models."""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    ARIMA = "arima"
    MOVING_AVERAGE = "moving_average"
    HOLT_WINTERS = "holt_winters"
    NEURAL_NETWORK = "neural_network"
    ENSEMBLE = "ensemble"
    NAIVE = "naive"


class AnomalyType(Enum):
    """Types of anomalies."""
    SPIKE = "spike"  # Sudden increase
    DROP = "drop"  # Sudden decrease
    OUTLIER = "outlier"  # Unusual value
    TREND_CHANGE = "trend_change"  # Sudden trend change
    SEASONAL_SHIFT = "seasonal_shift"  # Seasonality change
    CYCLE_BREAK = "cycle_break"  # Cycle disruption
    INCONSISTENCY = "inconsistency"  # Inconsistent pattern


class ComparisonType(Enum):
    """Types of comparisons."""
    PERIOD_OVER_PERIOD = "period_over_period"
    CATEGORY_COMPARISON = "category_comparison"
    MEMBER_COMPARISON = "member_comparison"
    ACTUAL_VS_TARGET = "actual_vs_target"
    BENCHMARK_COMPARISON = "benchmark_comparison"
    YEAR_OVER_YEAR = "year_over_year"
    MONTH_OVER_MONTH = "month_over_month"


class AnalyticsPeriod(Enum):
    """Analytics time periods."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class DataGranularity(Enum):
    """Data granularity levels."""
    RAW = "raw"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ConfidenceLevel(Enum):
    """Confidence levels for forecasts."""
    HIGH = "high"  # 95%
    MEDIUM = "medium"  # 80%
    LOW = "low"  # 60%
    VERY_LOW = "very_low"  # 40%


class AnalyticsMetric(Enum):
    """Analytics metrics."""
    SUSTAINABILITY_SCORE = "sustainability_score"
    CARBON_FOOTPRINT = "carbon_footprint"
    ENERGY_CONSUMPTION = "energy_consumption"
    WATER_CONSUMPTION = "water_consumption"
    WASTE_GENERATION = "waste_generation"
    TRANSPORTATION_IMPACT = "transportation_impact"
    FOOD_IMPACT = "food_impact"
    SHOPPING_IMPACT = "shopping_impact"
    HOUSEHOLD_PERFORMANCE = "household_performance"
    GOAL_COMPLETION_RATE = "goal_completion_rate"
    HABIT_CONSISTENCY = "habit_consistency"
    RECYCLING_RATE = "recycling_rate"
    COMPOSTING_RATE = "composting_rate"


class AnalyticsCategory(Enum):
    """Analytics categories."""
    CARBON = "carbon"
    ENERGY = "energy"
    WATER = "water"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    FOOD = "food"
    SHOPPING = "shopping"
    HOUSEHOLD = "household"
    OVERALL = "overall"


@dataclass
class HistoricalData:
    """
    Represents historical sustainability data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    value: float = 0.0
    unit: str = ""
    category: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    is_verified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'timestamp': self.timestamp.isoformat(),
            'metric': self.metric.value,
            'value': self.value,
            'unit': self.unit,
            'category': self.category,
            'metadata': self.metadata,
            'source': self.source,
            'is_verified': self.is_verified
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HistoricalData':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            user_id=data.get('user_id', ''),
            household_id=data.get('household_id'),
            timestamp=datetime.fromisoformat(data['timestamp']) if data.get('timestamp') else datetime.now(),
            metric=AnalyticsMetric(data.get('metric', 'sustainability_score')),
            value=data.get('value', 0.0),
            unit=data.get('unit', ''),
            category=data.get('category', ''),
            metadata=data.get('metadata', {}),
            source=data.get('source', ''),
            is_verified=data.get('is_verified', False)
        )


@dataclass
class TrendAnalysis:
    """
    Represents trend analysis results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Trend data
    values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    granularity: DataGranularity = DataGranularity.DAILY
    
    # Trend statistics
    mean: float = 0.0
    median: float = 0.0
    variance: float = 0.0
    std_dev: float = 0.0
    min_value: float = 0.0
    max_value: float = 0.0
    
    # Trend direction
    trend_type: TrendType = TrendType.UNDEFINED
    slope: float = 0.0
    intercept: float = 0.0
    r_squared: float = 0.0
    p_value: float = 0.0
    
    # Seasonality
    has_seasonality: bool = False
    seasonality_period: int = 0
    seasonality_strength: float = 0.0
    
    # Change metrics
    absolute_change: float = 0.0
    percentage_change: float = 0.0
    daily_rate: float = 0.0
    monthly_rate: float = 0.0
    
    # Moving averages
    moving_average_7: List[float] = field(default_factory=list)
    moving_average_30: List[float] = field(default_factory=list)
    moving_average_90: List[float] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'values': self.values,
            'dates': self.dates,
            'granularity': self.granularity.value,
            'mean': self.mean,
            'median': self.median,
            'variance': self.variance,
            'std_dev': self.std_dev,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'trend_type': self.trend_type.value,
            'slope': self.slope,
            'intercept': self.intercept,
            'r_squared': self.r_squared,
            'p_value': self.p_value,
            'has_seasonality': self.has_seasonality,
            'seasonality_period': self.seasonality_period,
            'seasonality_strength': self.seasonality_strength,
            'absolute_change': self.absolute_change,
            'percentage_change': self.percentage_change,
            'daily_rate': self.daily_rate,
            'monthly_rate': self.monthly_rate,
            'moving_average_7': self.moving_average_7,
            'moving_average_30': self.moving_average_30,
            'moving_average_90': self.moving_average_90,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
        }


@dataclass
class ForecastResult:
    """
    Represents forecasting results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    model: ForecastModel = ForecastModel.LINEAR
    forecast_date: datetime = field(default_factory=datetime.now)
    horizon_days: int = 30
    
    # Forecast values
    forecasts: List[Dict[str, Any]] = field(default_factory=list)
    projected_values: List[float] = field(default_factory=list)
    confidence_intervals: List[Tuple[float, float]] = field(default_factory=list)
    
    # Statistics
    mean_forecast: float = 0.0
    median_forecast: float = 0.0
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    
    # Scenarios
    best_case: float = 0.0
    current_trend: float = 0.0
    worst_case: float = 0.0
    
    # Model performance
    model_accuracy: float = 0.0
    mape: float = 0.0  # Mean Absolute Percentage Error
    rmse: float = 0.0  # Root Mean Square Error
    
    # Metadata
    data_points_used: int = 0
    is_reliable: bool = False
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'model': self.model.value,
            'forecast_date': self.forecast_date.isoformat(),
            'horizon_days': self.horizon_days,
            'forecasts': self.forecasts,
            'projected_values': self.projected_values,
            'confidence_intervals': [(l, u) for l, u in self.confidence_intervals],
            'mean_forecast': self.mean_forecast,
            'median_forecast': self.median_forecast,
            'confidence_level': self.confidence_level.value,
            'best_case': self.best_case,
            'current_trend': self.current_trend,
            'worst_case': self.worst_case,
            'model_accuracy': self.model_accuracy,
            'mape': self.mape,
            'rmse': self.rmse,
            'data_points_used': self.data_points_used,
            'is_reliable': self.is_reliable,
            'notes': self.notes
        }


@dataclass
class AnomalyDetection:
    """
    Represents anomaly detection results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    detected_at: datetime = field(default_factory=datetime.now)
    anomaly_type: AnomalyType = AnomalyType.OUTLIER
    
    # Anomaly details
    value: float = 0.0
    expected_value: float = 0.0
    deviation: float = 0.0
    deviation_percentage: float = 0.0
    z_score: float = 0.0
    
    # Context
    context_value: float = 0.0
    context_range: Tuple[float, float] = (0.0, 0.0)
    
    # Explanation
    explanation: str = ""
    possible_causes: List[str] = field(default_factory=list)
    
    # Severity
    severity: str = ""  # low, medium, high, critical
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    # Metadata
    confidence: float = 0.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'metric': self.metric.value,
            'detected_at': self.detected_at.isoformat(),
            'anomaly_type': self.anomaly_type.value,
            'value': self.value,
            'expected_value': self.expected_value,
            'deviation': self.deviation,
            'deviation_percentage': self.deviation_percentage,
            'z_score': self.z_score,
            'context_value': self.context_value,
            'context_range': self.context_range,
            'explanation': self.explanation,
            'possible_causes': self.possible_causes,
            'severity': self.severity,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'confidence': self.confidence,
            'notes': self.notes
        }


@dataclass
class GoalTrajectory:
    """
    Represents goal trajectory analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    goal_id: str = ""
    goal_name: str = ""
    category: str = ""
    
    # Goal details
    target_value: float = 0.0
    current_value: float = 0.0
    start_value: float = 0.0
    
    # Trajectory
    is_on_track: bool = False
    estimated_completion: Optional[datetime] = None
    days_remaining: int = 0
    
    # Progress
    progress_percentage: float = 0.0
    expected_progress: float = 0.0
    progress_gap: float = 0.0
    
    # Risk assessment
    risk_level: str = ""  # low, medium, high
    risk_factors: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # History
    trajectory_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'goal_id': self.goal_id,
            'goal_name': self.goal_name,
            'category': self.category,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'start_value': self.start_value,
            'is_on_track': self.is_on_track,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'days_remaining': self.days_remaining,
            'progress_percentage': self.progress_percentage,
            'expected_progress': self.expected_progress,
            'progress_gap': self.progress_gap,
            'risk_level': self.risk_level,
            'risk_factors': self.risk_factors,
            'recommendations': self.recommendations,
            'trajectory_history': self.trajectory_history,
            'last_updated': self.last_updated.isoformat(),
            'notes': self.notes
        }


@dataclass
class ComparativeAnalysis:
    """
    Represents comparative analysis results.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    comparison_type: ComparisonType = ComparisonType.PERIOD_OVER_PERIOD
    metric: AnalyticsMetric = AnalyticsMetric.SUSTAINABILITY_SCORE
    
    # Comparison data
    current_period: Dict[str, Any] = field(default_factory=dict)
    previous_period: Dict[str, Any] = field(default_factory=dict)
    comparison_results: Dict[str, Any] = field(default_factory=dict)
    
    # Differences
    absolute_difference: float = 0.0
    percentage_difference: float = 0.0
    relative_performance: float = 0.0
    
    # Rankings
    rank: int = 0
    percentile: float = 0.0
    
    # Insights
    insights: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'comparison_type': self.comparison_type.value,
            'metric': self.metric.value,
            'current_period': self.current_period,
            'previous_period': self.previous_period,
            'comparison_results': self.comparison_results,
            'absolute_difference': self.absolute_difference,
            'percentage_difference': self.percentage_difference,
            'relative_performance': self.relative_performance,
            'rank': self.rank,
            'percentile': self.percentile,
            'insights': self.insights,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'notes': self.notes
        }


@dataclass
class CategoryAnalytics:
    """
    Represents category-specific analytics.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    category: AnalyticsCategory = AnalyticsCategory.OVERALL
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Performance metrics
    current_score: float = 0.0
    previous_score: float = 0.0
    change: float = 0.0
    change_percentage: float = 0.0
    
    # Trend
    trend_type: TrendType = TrendType.UNDEFINED
    trend_slope: float = 0.0
    
    # Breakdown
    subcategory_scores: Dict[str, float] = field(default_factory=dict)
    subcategory_trends: Dict[str, float] = field(default_factory=dict)
    
    # Ranking
    rank_among_categories: int = 0
    percentile: float = 0.0
    
    # Insights
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category.value,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'current_score': self.current_score,
            'previous_score': self.previous_score,
            'change': self.change,
            'change_percentage': self.change_percentage,
            'trend_type': self.trend_type.value,
            'trend_slope': self.trend_slope,
            'subcategory_scores': self.subcategory_scores,
            'subcategory_trends': self.subcategory_trends,
            'rank_among_categories': self.rank_among_categories,
            'percentile': self.percentile,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'opportunities': self.opportunities,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
        }


@dataclass
class HouseholdAnalytics:
    """
    Represents household-level analytics.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    start_date: datetime = field(default_factory=datetime.now)
    end_date: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    total_sustainability_score: float = 0.0
    average_sustainability_score: float = 0.0
    member_count: int = 0
    
    # Member breakdown
    member_scores: Dict[str, float] = field(default_factory=dict)
    member_rankings: List[Dict[str, Any]] = field(default_factory=list)
    
    # Category breakdown
    category_scores: Dict[str, float] = field(default_factory=dict)
    category_rankings: Dict[str, int] = field(default_factory=dict)
    
    # Trends
    household_trend: TrendType = TrendType.UNDEFINED
    member_trends: Dict[str, TrendType] = field(default_factory=dict)
    
    # Impact
    total_carbon_saved: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    
    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    confidence: float = 0.0
    data_points: int = 0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'period': self.period.value,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'total_sustainability_score': self.total_sustainability_score,
            'average_sustainability_score': self.average_sustainability_score,
            'member_count': self.member_count,
            'member_scores': self.member_scores,
            'member_rankings': self.member_rankings,
            'category_scores': self.category_scores,
            'category_rankings': self.category_rankings,
            'household_trend': self.household_trend.value,
            'member_trends': {k: v.value for k, v in self.member_trends.items()},
            'total_carbon_saved': self.total_carbon_saved,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'confidence': self.confidence,
            'data_points': self.data_points,
            'notes': self.notes
        }


@dataclass
class AnalyticsReport:
    """
    Represents a comprehensive analytics report.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    household_id: Optional[str] = None
    report_type: str = ""  # historical, forecast, comparative, comprehensive
    period: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Executive summary
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    
    # Trend analysis
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Forecasts
    forecasts: Dict[str, Any] = field(default_factory=dict)
    
    # Anomalies
    anomalies: List[Dict[str, Any]] = field(default_factory=list)
    
    # Trajectories
    trajectories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparisons
    comparisons: List[Dict[str, Any]] = field(default_factory=list)
    
    # Insights
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Charts
    charts: Dict[str, str] = field(default_factory=dict)  # Chart ID to URL
    
    # Metadata
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
            'key_findings': self.key_findings,
            'trend_analysis': self.trend_analysis,
            'forecasts': self.forecasts,
            'anomalies': self.anomalies,
            'trajectories': self.trajectories,
            'comparisons': self.comparisons,
            'insights': self.insights,
            'recommendations': self.recommendations,
            'charts': self.charts,
            'content': self.content,
            'file_path': self.file_path,
            'shareable': self.shareable,
            'notes': self.notes
        }


@dataclass
class AnalyticsInsight:
    """
    Represents an analytics insight.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    insight_type: str = ""  # trend, anomaly, opportunity, risk, achievement
    title: str = ""
    description: str = ""
    category: str = ""
    
    # Supporting data
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    
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
            'supporting_data': self.supporting_data,
            'confidence': self.confidence,
            'recommended_action': self.recommended_action,
            'priority': self.priority,
            'generated_at': self.generated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_actioned': self.is_actioned
        }


@dataclass
class AnalyticsSummary:
    """
    Comprehensive analytics summary.
    """
    user_id: str = ""
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    generated_at: datetime = field(default_factory=datetime.now)
    
    # Overall metrics
    current_sustainability_score: float = 0.0
    previous_sustainability_score: float = 0.0
    score_change: float = 0.0
    score_change_percentage: float = 0.0
    
    # Category summaries
    category_summaries: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Trend summary
    overall_trend: TrendType = TrendType.UNDEFINED
    improving_categories: List[str] = field(default_factory=list)
    declining_categories: List[str] = field(default_factory=list)
    stable_categories: List[str] = field(default_factory=list)
    
    # Impact summary
    total_carbon_saved: float = 0.0
    total_water_saved: float = 0.0
    total_waste_reduced: float = 0.0
    
    # Key metrics
    best_performing_category: str = ""
    worst_performing_category: str = ""
    fastest_improving_category: str = ""
    most_declining_category: str = ""
    
    # Goals
    goals_on_track: int = 0
    goals_at_risk: int = 0
    goals_completed: int = 0
    
    # Forecast
    forecast_30_day: float = 0.0
    forecast_30_day_confidence: float = 0.0
    
    # Anomalies
    anomaly_count: int = 0
    unresolved_anomalies: int = 0
    
    # Insights
    top_insights: List[str] = field(default_factory=list)
    top_recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'period': self.period.value,
            'generated_at': self.generated_at.isoformat(),
            'current_sustainability_score': self.current_sustainability_score,
            'previous_sustainability_score': self.previous_sustainability_score,
            'score_change': self.score_change,
            'score_change_percentage': self.score_change_percentage,
            'category_summaries': self.category_summaries,
            'overall_trend': self.overall_trend.value,
            'improving_categories': self.improving_categories,
            'declining_categories': self.declining_categories,
            'stable_categories': self.stable_categories,
            'total_carbon_saved': self.total_carbon_saved,
            'total_water_saved': self.total_water_saved,
            'total_waste_reduced': self.total_waste_reduced,
            'best_performing_category': self.best_performing_category,
            'worst_performing_category': self.worst_performing_category,
            'fastest_improving_category': self.fastest_improving_category,
            'most_declining_category': self.most_declining_category,
            'goals_on_track': self.goals_on_track,
            'goals_at_risk': self.goals_at_risk,
            'goals_completed': self.goals_completed,
            'forecast_30_day': self.forecast_30_day,
            'forecast_30_day_confidence': self.forecast_30_day_confidence,
            'anomaly_count': self.anomaly_count,
            'unresolved_anomalies': self.unresolved_anomalies,
            'top_insights': self.top_insights,
            'top_recommendations': self.top_recommendations
        }