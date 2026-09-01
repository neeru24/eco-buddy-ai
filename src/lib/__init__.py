"""
EcoBuddy AI Library Package
Contains utility modules for the application.
"""

# Export Manager
from .export_manager import (
    ExportManager,
    ExportConfig,
    ExportResult,
    get_export_manager,
    export_assessments,
    export_summary,
    get_supported_formats
)

# History Manager
from .history_manager import (
    HistoryManager,
    HistoryFilter,
    get_history_manager,
    clear_history_manager
)

# Analytics Engine
from .analytics_engine import (
    AnalyticsEngine,
    AnalyticsConfig,
    AnalyticsResult,
    get_analytics_engine,
    analyze_assessments,
    get_analysis_summary
)

# Predictive Model
from .predictive_model import (
    PredictiveModel,
    ModelConfig,
    PredictionResult,
    get_predictive_model,
    train_predictive_model,
    generate_predictions,
    evaluate_predictions
)

# Trend Analyzer
from .trend_analyzer import (
    TrendAnalyzer,
    TrendResult,
    get_trend_analyzer,
    analyze_trends,
    get_trend_forecast
)

# Insight Generator
from .insight_generator import (
    InsightGenerator,
    Insight,
    InsightResult,
    get_insight_generator,
    generate_insights
)

# Notification Manager
from .notification_manager import (
    NotificationManager,
    Notification,
    NotificationPreferences,
    NotificationPriority,
    NotificationType,
    get_notification_manager,
    create_notification,
    get_user_notifications,
    get_unread_count,
    mark_as_read,
    mark_all_as_read,
    dismiss_notification,
    dismiss_all
)

# Alert Rules Engine
from .alert_rules_engine import (
    AlertRulesEngine,
    AlertRule,
    AlertResult,
    AlertSeverity,
    AlertCategory,
    get_alert_rules_engine,
    evaluate_alerts
)

# Reminder Scheduler
from .reminder_scheduler import (
    ReminderScheduler,
    Reminder,
    ReminderType,
    ReminderFrequency,
    get_reminder_scheduler,
    create_reminder,
    get_user_reminders
)

# Notification Templates
from .notification_templates import (
    NotificationTemplateManager,
    NotificationTemplate,
    get_template_manager,
    render_template
)

# Challenge Manager
from .challenge_manager import (
    ChallengeManager,
    Challenge,
    ChallengeProgress,
    ChallengeStatus,
    ChallengeType,
    ChallengeCategory,
    get_challenge_manager,
    create_challenge,
    get_challenge,
    get_active_challenges,
    join_challenge,
    update_challenge_progress
)

# Team Manager
from .team_manager import (
    TeamManager,
    Team,
    TeamMember,
    TeamRole,
    TeamStatus,
    get_team_manager,
    create_team,
    join_team,
    get_user_teams
)

# Leaderboard Engine
from .leaderboard_engine import (
    LeaderboardEngine,
    LeaderboardEntry,
    TeamLeaderboardEntry,
    LeaderboardPeriod,
    LeaderboardType,
    get_leaderboard_engine,
    get_individual_leaderboard,
    get_team_leaderboard,
    get_user_rank
)

# Challenge Rewards
from .challenge_rewards import (
    ChallengeRewards,
    Reward,
    RewardClaim,
    RewardType,
    RewardTier,
    get_challenge_rewards,
    check_and_award_rewards,
    get_user_rewards
)

# Gamification V2
from .gamification_v2 import (
    GamificationV2,
    Quest,
    UserQuest,
    UserLevel,
    QuestType,
    QuestStatus,
    QuestDifficulty,
    get_gamification_v2,
    accept_quest,
    update_quest_progress,
    add_xp,
    add_coins,
    get_user_level,
    get_user_coins,
    get_gamification_stats
)

# Achievement Tracker
from .achievement_tracker import (
    AchievementTracker,
    Achievement,
    UserAchievement,
    AchievementCategory,
    AchievementTier,
    get_achievement_tracker,
    check_achievements,
    get_unlocked_achievements
)

# Quest Manager
from .quest_manager import (
    QuestManager,
    QuestTemplate,
    get_quest_manager,
    get_user_quests
)

# Reward Catalog
from .reward_catalog import (
    RewardCatalog,
    CatalogItem,
    ItemType,
    ItemRarity,
    PurchaseRecord,
    get_reward_catalog,
    purchase_item,
    use_item,
    get_user_inventory,
    get_user_items
)

# Budget Manager
from .budget_manager import (
    BudgetManager,
    CarbonBudget,
    BudgetTransaction,
    BudgetPeriod,
    BudgetStatus,
    get_budget_manager,
    create_budget,
    get_user_budgets,
    get_active_budget,
    update_budget_usage,
    get_budget_progress
)

# Goal Tracker
from .goal_tracker import (
    GoalTracker,
    Goal,
    GoalProgress,
    GoalType,
    GoalStatus,
    get_goal_tracker,
    create_goal,
    get_user_goals,
    update_goal_progress,
    get_goal_recommendations
)

# Carbon Forecaster
from .carbon_forecaster import (
    CarbonForecaster,
    ForecastResult,
    get_carbon_forecaster,
    forecast_carbon,
    forecast_goal
)

__all__ = [
    # Export Manager
    'ExportManager',
    'ExportConfig',
    'ExportResult',
    'get_export_manager',
    'export_assessments',
    'export_summary',
    'get_supported_formats',
    
    # History Manager
    'HistoryManager',
    'HistoryFilter',
    'get_history_manager',
    'clear_history_manager',
    
    # Analytics Engine
    'AnalyticsEngine',
    'AnalyticsConfig',
    'AnalyticsResult',
    'get_analytics_engine',
    'analyze_assessments',
    'get_analysis_summary',
    
    # Predictive Model
    'PredictiveModel',
    'ModelConfig',
    'PredictionResult',
    'get_predictive_model',
    'train_predictive_model',
    'generate_predictions',
    'evaluate_predictions',
    
    # Trend Analyzer
    'TrendAnalyzer',
    'TrendResult',
    'get_trend_analyzer',
    'analyze_trends',
    'get_trend_forecast',
    
    # Insight Generator
    'InsightGenerator',
    'Insight',
    'InsightResult',
    'get_insight_generator',
    'generate_insights',
    
    # Notification Manager
    'NotificationManager',
    'Notification',
    'NotificationPreferences',
    'NotificationPriority',
    'NotificationType',
    'get_notification_manager',
    'create_notification',
    'get_user_notifications',
    'get_unread_count',
    'mark_as_read',
    'mark_all_as_read',
    'dismiss_notification',
    'dismiss_all',
    
    # Alert Rules Engine
    'AlertRulesEngine',
    'AlertRule',
    'AlertResult',
    'AlertSeverity',
    'AlertCategory',
    'get_alert_rules_engine',
    'evaluate_alerts',
    
    # Reminder Scheduler
    'ReminderScheduler',
    'Reminder',
    'ReminderType',
    'ReminderFrequency',
    'get_reminder_scheduler',
    'create_reminder',
    'get_user_reminders',
    
    # Notification Templates
    'NotificationTemplateManager',
    'NotificationTemplate',
    'get_template_manager',
    'render_template',
    
    # Challenge Manager
    'ChallengeManager',
    'Challenge',
    'ChallengeProgress',
    'ChallengeStatus',
    'ChallengeType',
    'ChallengeCategory',
    'get_challenge_manager',
    'create_challenge',
    'get_challenge',
    'get_active_challenges',
    'join_challenge',
    'update_challenge_progress',
    
    # Team Manager
    'TeamManager',
    'Team',
    'TeamMember',
    'TeamRole',
    'TeamStatus',
    'get_team_manager',
    'create_team',
    'join_team',
    'get_user_teams',
    
    # Leaderboard Engine
    'LeaderboardEngine',
    'LeaderboardEntry',
    'TeamLeaderboardEntry',
    'LeaderboardPeriod',
    'LeaderboardType',
    'get_leaderboard_engine',
    'get_individual_leaderboard',
    'get_team_leaderboard',
    'get_user_rank',
    
    # Challenge Rewards
    'ChallengeRewards',
    'Reward',
    'RewardClaim',
    'RewardType',
    'RewardTier',
    'get_challenge_rewards',
    'check_and_award_rewards',
    'get_user_rewards',
    
    # Gamification V2
    'GamificationV2',
    'Quest',
    'UserQuest',
    'UserLevel',
    'QuestType',
    'QuestStatus',
    'QuestDifficulty',
    'get_gamification_v2',
    'accept_quest',
    'update_quest_progress',
    'add_xp',
    'add_coins',
    'get_user_level',
    'get_user_coins',
    'get_gamification_stats',
    
    # Achievement Tracker
    'AchievementTracker',
    'Achievement',
    'UserAchievement',
    'AchievementCategory',
    'AchievementTier',
    'get_achievement_tracker',
    'check_achievements',
    'get_unlocked_achievements',
    
    # Quest Manager
    'QuestManager',
    'QuestTemplate',
    'get_quest_manager',
    'get_user_quests',
    
    # Reward Catalog
    'RewardCatalog',
    'CatalogItem',
    'ItemType',
    'ItemRarity',
    'PurchaseRecord',
    'get_reward_catalog',
    'purchase_item',
    'use_item',
    'get_user_inventory',
    'get_user_items',
    
    # Budget Manager
    'BudgetManager',
    'CarbonBudget',
    'BudgetTransaction',
    'BudgetPeriod',
    'BudgetStatus',
    'get_budget_manager',
    'create_budget',
    'get_user_budgets',
    'get_active_budget',
    'update_budget_usage',
    'get_budget_progress',
    
    # Goal Tracker
    'GoalTracker',
    'Goal',
    'GoalProgress',
    'GoalType',
    'GoalStatus',
    'get_goal_tracker',
    'create_goal',
    'get_user_goals',
    'update_goal_progress',
    'get_goal_recommendations',
    
    # Carbon Forecaster
    'CarbonForecaster',
    'ForecastResult',
    'get_carbon_forecaster',
    'forecast_carbon',
    'forecast_goal',
    
    # Budget Alerts
    'BudgetAlertManager',
    'BudgetAlert',
    'get_budget_alert_manager',
    'create_budget_alert',
    'get_user_alerts'
    'get_user_items'
]

# Add to existing imports 
from .water_calculator import WaterCalculator, WaterActivity, WaterFootprint
from .water_tips import WaterTips
from .water_analytics import WaterAnalytics


from .investment_tracker import InvestmentTracker, Investment, InvestmentPortfolio, InvestmentGoal
from .savings_calculator import SavingsCalculator
from .impact_calculator import ImpactCalculator
from .investment_reports import InvestmentReports

from .challenge_calendar import ChallengeCalendar, ChallengeDay, ChallengeMonth
from .challenge_generator import ChallengeGenerator
from .streak_tracker import StreakTracker, StreakData
from .challenge_rewards import ChallengeRewards, Reward


# Update __all__
__all__ = [
    # ... existing exports ...
 
    'WaterCalculator',
    'WaterActivity',
    'WaterFootprint',
    'WaterTips',
    'WaterAnalytics'


    'InvestmentTracker',
    'Investment',
    'InvestmentPortfolio',
    'InvestmentGoal',
    'SavingsCalculator',
    'ImpactCalculator',
    'InvestmentRepo
 
    'ChallengeCalendar',
    'ChallengeDay',
    'ChallengeMonth',
    'ChallengeGenerator',
    'StreakTracker',
    'StreakData',
    'ChallengeRewards',
    'Reward'
]