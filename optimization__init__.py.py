"""
Smart Household Resource Optimization Engine
A comprehensive system for optimizing household resource consumption.
"""

from optimization.models import (
    HouseholdResource, ResourceType, OptimizationOpportunity,
    BaselineAnalysis, EnergyOptimization, WaterOptimization,
    FoodWasteOptimization, TransportationOptimization,
    ShoppingOptimization, CostImpactAnalysis, WhatIfScenario,
    OptimizationPlan, MemberContribution, RecommendationPriority,
    OptimizationTarget, ResourceOptimization, EfficiencyScore,
    HouseholdEfficiency, OptimizationProgress, ResourceCategory,
    ConsumptionPattern, EfficiencyGrade, OptimizationStatus,
    RecommendationCategory, ImpactLevel, EffortLevel
)
from optimization.resource_analyzer import ResourceAnalyzer
from optimization.baseline import BaselineAnalyzer
from optimization.energy_optimizer import EnergyOptimizer
from optimization.water_optimizer import WaterOptimizer
from optimization.food_waste_optimizer import FoodWasteOptimizer
from optimization.transportation_optimizer import TransportationOptimizer
from optimization.shopping_optimizer import ShoppingOptimizer
from optimization.cost_impact_analyzer import CostImpactAnalyzer
from optimization.what_if_simulator import WhatIfSimulator
from optimization.member_analyzer import MemberAnalyzer
from optimization.optimization_planner import OptimizationPlanner
from optimization.recommendations import RecommendationEngine
from optimization.analytics import OptimizationAnalytics
from optimization.database import OptimizationDatabase
from optimization.visualizations import OptimizationVisualizer

__all__ = [
    'HouseholdResource',
    'ResourceType',
    'OptimizationOpportunity',
    'BaselineAnalysis',
    'EnergyOptimization',
    'WaterOptimization',
    'FoodWasteOptimization',
    'TransportationOptimization',
    'ShoppingOptimization',
    'CostImpactAnalysis',
    'WhatIfScenario',
    'OptimizationPlan',
    'MemberContribution',
    'RecommendationPriority',
    'OptimizationTarget',
    'ResourceOptimization',
    'EfficiencyScore',
    'HouseholdEfficiency',
    'OptimizationProgress',
    'ResourceCategory',
    'ConsumptionPattern',
    'EfficiencyGrade',
    'OptimizationStatus',
    'RecommendationCategory',
    'ImpactLevel',
    'EffortLevel',
    'ResourceAnalyzer',
    'BaselineAnalyzer',
    'EnergyOptimizer',
    'WaterOptimizer',
    'FoodWasteOptimizer',
    'TransportationOptimizer',
    'ShoppingOptimizer',
    'CostImpactAnalyzer',
    'WhatIfSimulator',
    'MemberAnalyzer',
    'OptimizationPlanner',
    'RecommendationEngine',
    'OptimizationAnalytics',
    'OptimizationDatabase',
    'OptimizationVisualizer'
]