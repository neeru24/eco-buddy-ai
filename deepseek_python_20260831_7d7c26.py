"""
Smart Household Resource Optimization Engine - Data Models
Comprehensive models for resource optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid
import json


class ResourceType(Enum):
    """Types of household resources."""
    ENERGY = "energy"
    WATER = "water"
    FOOD = "food"
    WASTE = "waste"
    TRANSPORTATION = "transportation"
    SHOPPING = "shopping"
    TRAVEL = "travel"
    OTHER = "other"


class RecommendationPriority(Enum):
    """Priority levels for optimization recommendations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFORMATIONAL = "informational"


class OptimizationStatus(Enum):
    """Status of optimization plans."""
    DRAFT = "draft"
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class OptimizationCategory(Enum):
    """Categories of optimization opportunities."""
    ENERGY_EFFICIENCY = "energy_efficiency"
    WATER_CONSERVATION = "water_conservation"
    WASTE_REDUCTION = "waste_reduction"
    FOOD_OPTIMIZATION = "food_optimization"
    TRANSPORTATION_OPTIMIZATION = "transportation_optimization"
    SHOPPING_OPTIMIZATION = "shopping_optimization"
    BEHAVIORAL_CHANGE = "behavioral_change"
    TECHNOLOGY_UPGRADE = "technology_upgrade"
    MAINTENANCE = "maintenance"
    OTHER = "other"


@dataclass
class HouseholdResource:
    """
    Represents a household resource with consumption data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    resource_type: ResourceType = ResourceType.ENERGY
    name: str = ""
    description: str = ""
    
    # Consumption data
    current_usage: float = 0.0
    baseline_usage: float = 0.0
    unit: str = ""
    cost_per_unit: float = 0.0
    
    # Historical data
    historical_usage: List[Dict[str, Any]] = field(default_factory=list)
    monthly_averages: Dict[str, float] = field(default_factory=dict)
    yearly_averages: Dict[str, float] = field(default_factory=dict)
    
    # Efficiency metrics
    efficiency_score: float = 0.0  # 0-100
    efficiency_grade: str = ""  # A, B, C, D, F
    
    # Optimization potential
    optimization_potential: float = 0.0  # Percentage
    estimated_savings: float = 0.0
    estimated_impact: float = 0.0
    
    # Member contributions
    member_contributions: Dict[str, float] = field(default_factory=dict)  # member_id -> percentage
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'resource_type': self.resource_type.value,
            'name': self.name,
            'description': self.description,
            'current_usage': self.current_usage,
            'baseline_usage': self.baseline_usage,
            'unit': self.unit,
            'cost_per_unit': self.cost_per_unit,
            'historical_usage': self.historical_usage,
            'monthly_averages': self.monthly_averages,
            'yearly_averages': self.yearly_averages,
            'efficiency_score': self.efficiency_score,
            'efficiency_grade': self.efficiency_grade,
            'optimization_potential': self.optimization_potential,
            'estimated_savings': self.estimated_savings,
            'estimated_impact': self.estimated_impact,
            'member_contributions': self.member_contributions,
            'last_updated': self.last_updated.isoformat(),
            'notes': self.notes,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HouseholdResource':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            household_id=data.get('household_id', ''),
            resource_type=ResourceType(data.get('resource_type', 'energy')),
            name=data.get('name', ''),
            description=data.get('description', ''),
            current_usage=data.get('current_usage', 0.0),
            baseline_usage=data.get('baseline_usage', 0.0),
            unit=data.get('unit', ''),
            cost_per_unit=data.get('cost_per_unit', 0.0),
            historical_usage=data.get('historical_usage', []),
            monthly_averages=data.get('monthly_averages', {}),
            yearly_averages=data.get('yearly_averages', {}),
            efficiency_score=data.get('efficiency_score', 0.0),
            efficiency_grade=data.get('efficiency_grade', ''),
            optimization_potential=data.get('optimization_potential', 0.0),
            estimated_savings=data.get('estimated_savings', 0.0),
            estimated_impact=data.get('estimated_impact', 0.0),
            member_contributions=data.get('member_contributions', {}),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            notes=data.get('notes', ''),
            tags=data.get('tags', [])
        )
    
    def calculate_efficiency_score(self) -> float:
        """Calculate efficiency score based on usage vs baseline."""
        if self.baseline_usage == 0:
            return 50.0
        
        ratio = self.current_usage / self.baseline_usage
        if ratio <= 0.5:
            score = 90 + (1 - ratio) * 20
        elif ratio <= 0.8:
            score = 70 + (0.8 - ratio) * 66.67
        elif ratio <= 1.0:
            score = 50 + (1 - ratio) * 100
        elif ratio <= 1.2:
            score = 30 + (1.2 - ratio) * 100
        else:
            score = max(0, 30 - (ratio - 1.2) * 50)
        
        return min(100, max(0, score))
    
    def get_efficiency_grade(self) -> str:
        """Get efficiency grade based on score."""
        score = self.calculate_efficiency_score()
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"


@dataclass
class BaselineAnalysis:
    """
    Baseline analysis of household resource consumption.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    period_days: int = 30
    
    # Consumption averages
    total_energy_kwh: float = 0.0
    total_water_liters: float = 0.0
    total_food_kg: float = 0.0
    total_waste_kg: float = 0.0
    total_transport_km: float = 0.0
    
    # Per capita averages
    per_capita_energy: float = 0.0
    per_capita_water: float = 0.0
    per_capita_food: float = 0.0
    per_capita_waste: float = 0.0
    per_capita_transport: float = 0.0
    
    # Efficiency scores
    energy_efficiency: float = 0.0
    water_efficiency: float = 0.0
    waste_efficiency: float = 0.0
    food_efficiency: float = 0.0
    transport_efficiency: float = 0.0
    overall_efficiency: float = 0.0
    
    # Category breakdown
    category_breakdown: Dict[str, float] = field(default_factory=dict)
    
    # Member breakdown
    member_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Benchmarks
    benchmarks: Dict[str, float] = field(default_factory=dict)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'period_days': self.period_days,
            'total_energy_kwh': self.total_energy_kwh,
            'total_water_liters': self.total_water_liters,
            'total_food_kg': self.total_food_kg,
            'total_waste_kg': self.total_waste_kg,
            'total_transport_km': self.total_transport_km,
            'per_capita_energy': self.per_capita_energy,
            'per_capita_water': self.per_capita_water,
            'per_capita_food': self.per_capita_food,
            'per_capita_waste': self.per_capita_waste,
            'per_capita_transport': self.per_capita_transport,
            'energy_efficiency': self.energy_efficiency,
            'water_efficiency': self.water_efficiency,
            'waste_efficiency': self.waste_efficiency,
            'food_efficiency': self.food_efficiency,
            'transport_efficiency': self.transport_efficiency,
            'overall_efficiency': self.overall_efficiency,
            'category_breakdown': self.category_breakdown,
            'member_breakdown': self.member_breakdown,
            'benchmarks': self.benchmarks,
            'notes': self.notes
        }


@dataclass
class EnergyOptimization:
    """
    Energy optimization analysis and recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Consumption analysis
    total_consumption: float = 0.0
    baseline_consumption: float = 0.0
    consumption_difference: float = 0.0
    
    # High consumption detection
    high_consumption_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Efficiency opportunities
    efficiency_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    reduction_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_energy_savings: float = 0.0  # kWh
    estimated_cost_savings: float = 0.0
    estimated_carbon_savings: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_consumption': self.total_consumption,
            'baseline_consumption': self.baseline_consumption,
            'consumption_difference': self.consumption_difference,
            'high_consumption_areas': self.high_consumption_areas,
            'peak_usage_times': self.peak_usage_times,
            'efficiency_opportunities': self.efficiency_opportunities,
            'reduction_scenarios': self.reduction_scenarios,
            'estimated_energy_savings': self.estimated_energy_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_carbon_savings': self.estimated_carbon_savings,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'notes': self.notes
        }


@dataclass
class WaterOptimization:
    """
    Water optimization analysis and recommendations.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Usage analysis
    total_usage: float = 0.0
    baseline_usage: float = 0.0
    usage_difference: float = 0.0
    
    # High usage detection
    high_usage_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reduction opportunities
    reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    efficiency_improvements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_water_savings: float = 0.0  # liters
    estimated_cost_savings: float = 0.0
    estimated_environmental_impact: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_usage': self.total_usage,
            'baseline_usage': self.baseline_usage,
            'usage_difference': self.usage_difference,
            'high_usage_areas': self.high_usage_areas,
            'peak_usage_times': self.peak_usage_times,
            'reduction_opportunities': self.reduction_opportunities,
            'efficiency_improvements': self.efficiency_improvements,
            'estimated_water_savings': self.estimated_water_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_environmental_impact': self.estimated_environmental_impact,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'notes': self.notes
        }


@dataclass
class FoodWasteOptimization:
    """
    Food and waste optimization analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Food consumption
    total_food_consumption: float = 0.0
    food_waste_amount: float = 0.0
    food_waste_percentage: float = 0.0
    
    # Waste analysis
    total_waste: float = 0.0
    recyclable_waste: float = 0.0
    compostable_waste: float = 0.0
    landfill_waste: float = 0.0
    
    # Reduction opportunities
    food_waste_reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    recycling_improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    composting_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_waste_reduction: float = 0.0
    estimated_cost_savings: float = 0.0
    estimated_environmental_impact: float = 0.0
    
    # Recommendations
    food_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    waste_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""


@dataclass
class TransportationOptimization:
    """
    Transportation optimization analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Transportation analysis
    total_distance: float = 0.0
    primary_modes: List[Dict[str, Any]] = field(default_factory=list)
    carbon_emissions: float = 0.0
    
    # Optimization opportunities
    shared_transport_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    lower_impact_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Comparison
    cost_comparison: Dict[str, float] = field(default_factory=dict)
    carbon_comparison: Dict[str, float] = field(default_factory=dict)
    
    # Savings estimates
    estimated_carbon_savings: float = 0.0
    estimated_cost_savings: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""


@dataclass
class CostImpactAnalysis:
    """
    Cost and impact analysis of household optimization.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Current costs
    current_energy_cost: float = 0.0
    current_water_cost: float = 0.0
    current_food_cost: float = 0.0
    current_waste_cost: float = 0.0
    current_transport_cost: float = 0.0
    total_current_cost: float = 0.0
    
    # Potential savings
    potential_energy_savings: float = 0.0
    potential_water_savings: float = 0.0
    potential_food_savings: float = 0.0
    potential_waste_savings: float = 0.0
    potential_transport_savings: float = 0.0
    total_potential_savings: float = 0.0
    
    # Environmental impact
    current_carbon_footprint: float = 0.0
    potential_carbon_reduction: float = 0.0
    current_water_footprint: float = 0.0
    potential_water_reduction: float = 0.0
    
    # Return on effort
    roi_indicators: Dict[str, float] = field(default_factory=dict)
    effort_vs_impact: Dict[str, str] = field(default_factory=dict)  # high, medium, low
    
    notes: str = ""


@dataclass
class WhatIfScenario:
    """
    What-if scenario for optimization simulation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    # Scenario parameters
    energy_reduction_percentage: float = 0.0
    water_reduction_percentage: float = 0.0
    waste_reduction_percentage: float = 0.0
    transport_shift_percentage: float = 0.0
    behavioral_changes: List[str] = field(default_factory=list)
    
    # Results
    projected_energy_savings: float = 0.0
    projected_water_savings: float = 0.0
    projected_waste_reduction: float = 0.0
    projected_cost_savings: float = 0.0
    projected_carbon_reduction: float = 0.0
    
    # Comparison to baseline
    improvement_percentage: float = 0.0
    efficiency_gain: float = 0.0
    
    notes: str = ""


@dataclass
class OptimizationPlan:
    """
    Comprehensive optimization plan for a household.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    name: str = ""
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    status: OptimizationStatus = OptimizationStatus.DRAFT
    
    # Targets
    targets: List['OptimizationTarget'] = field(default_factory=list)
    deadlines: Dict[str, datetime] = field(default_factory=dict)
    
    # Actions
    actions: List[Dict[str, Any]] = field(default_factory=list)
    prioritized_actions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Progress
    overall_progress: float = 0.0
    completed_actions: int = 0
    total_actions: int = 0
    
    # Impact
    estimated_savings: float = 0.0
    estimated_impact: float = 0.0
    achieved_savings: float = 0.0
    
    # Timeline
    start_date: Optional[datetime] = None
    target_completion_date: Optional[datetime] = None
    actual_completion_date: Optional[datetime] = None
    
    notes: str = ""


@dataclass
class OptimizationTarget:
    """
    Target for optimization plan.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    category: OptimizationCategory = OptimizationCategory.OTHER
    target_value: float = 0.0
    current_value: float = 0.0
    unit: str = ""
    deadline: Optional[datetime] = None
    achieved: bool = False
    achieved_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'category': self.category.value,
            'target_value': self.target_value,
            'current_value': self.current_value,
            'unit': self.unit,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'achieved': self.achieved,
            'achieved_date': self.achieved_date.isoformat() if self.achieved_date else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizationTarget':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            plan_id=data.get('plan_id', ''),
            category=OptimizationCategory(data.get('category', 'other')),
            target_value=data.get('target_value', 0.0),
            current_value=data.get('current_value', 0.0),
            unit=data.get('unit', ''),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            achieved=data.get('achieved', False),
            achieved_date=datetime.fromisoformat(data['achieved_date']) if data.get('achieved_date') else None
        )


@dataclass
class MemberContribution:
    """
    Member contribution analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    member_id: str = ""
    member_name: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Individual contributions
    individual_energy: float = 0.0
    individual_water: float = 0.0
    individual_food: float = 0.0
    individual_waste: float = 0.0
    individual_transport: float = 0.0
    
    # Shared contributions
    shared_energy: float = 0.0
    shared_water: float = 0.0
    shared_food: float = 0.0
    shared_waste: float = 0.0
    shared_transport: float = 0.0
    
    # Total contributions
    total_energy: float = 0.0
    total_water: float = 0.0
    total_food: float = 0.0
    total_waste: float = 0.0
    total_transport: float = 0.0
    
    # Category contributions
    category_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Improvement opportunities
    improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Household impact
    household_impact_percentage: float = 0.0
    
    notes: str = ""


@dataclass
class ResourceOptimization:
    """
    Complete resource optimization result.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    optimization_date: datetime = field(default_factory=datetime.now)
    
    # Analyses
    baseline: Optional[BaselineAnalysis] = None
    energy_optimization: Optional[EnergyOptimization] = None
    water_optimization: Optional[WaterOptimization] = None
    food_waste_optimization: Optional[FoodWasteOptimization] = None
    transportation_optimization: Optional[TransportationOptimization] = None
    cost_impact: Optional[CostImpactAnalysis] = None
    
    # Member analysis
    member_contributions: List[MemberContribution] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Summary
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Optimization plan
    optimization_plan: Optional[OptimizationPlan] = None
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'optimization_date': self.optimization_date.isoformat(),
            'baseline': self.baseline.to_dict() if self.baseline else None,
            'energy_optimization': self.energy_optimization.to_dict() if self.energy_optimization else None,
            'water_optimization': self.water_optimization.to_dict() if self.water_optimization else None,
            'food_waste_optimization': self.food_waste_optimization.to_dict() if self.food_waste_optimization else None,
            'transportation_optimization': self.transportation_optimization.to_dict() if self.transportation_optimization else None,
            'cost_impact': self.cost_impact.to_dict() if self.cost_impact else None,
            'member_contributions': [m.to_dict() for m in self.member_contributions],
            'recommendations': self.recommendations,
            'summary': self.summary,
            'optimization_plan': self.optimization_plan.to_dict() if self.optimization_plan else None,
            'notes': self.notes
        }


@dataclass
class EfficiencyScore:
    """
    Efficiency score for household or category.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    category: str = ""
    score: float = 0.0
    grade: str = ""
    benchmark: float = 0.0
    percentile: float = 0.0
    improvement_potential: float = 0.0
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'category': self.category,
            'score': self.score,
            'grade': self.grade,
            'benchmark': self.benchmark,
            'percentile': self.percentile,
            'improvement_potential': self.improvement_potential,
            'calculated_at': self.calculated_at.isoformat()
        }


@dataclass
class HouseholdEfficiency:
    """
    Overall household efficiency.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    overall_score: float = 0.0
    overall_grade: str = ""
    
    # Category scores
    energy_score: float = 0.0
    water_score: float = 0.0
    waste_score: float = 0.0
    food_score: float = 0.0
    transport_score: float = 0.0
    shopping_score: float = 0.0
    
    # Rankings
    category_rankings: Dict[str, int] = field(default_factory=dict)
    
    # Improvement
    improvement_potential: float = 0.0
    recommended_actions: List[str] = field(default_factory=list)
    
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'overall_score': self.overall_score,
            'overall_grade': self.overall_grade,
            'energy_score': self.energy_score,
            'water_score': self.water_score,
            'waste_score': self.waste_score,
            'food_score': self.food_score,
            'transport_score': self.transport_score,
            'shopping_score': self.shopping_score,
            'category_rankings': self.category_rankings,
            'improvement_potential': self.improvement_potential,
            'recommended_actions': self.recommended_actions,
            'calculated_at': self.calculated_at.isoformat()
        }


@dataclass
class OptimizationProgress:
    """
    Progress tracking for optimization plans.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plan_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Progress metrics
    overall_progress: float = 0.0
    completed_actions: int = 0
    total_actions: int = 0
    achieved_targets: int = 0
    total_targets: int = 0
    
    # Savings achieved
    achieved_energy_savings: float = 0.0
    achieved_water_savings: float = 0.0
    achieved_waste_reduction: float = 0.0
    achieved_cost_savings: float = 0.0
    
    # Status
    on_track: bool = True
    issues_detected: List[str] = field(default_factory=list)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'plan_id': self.plan_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_progress': self.overall_progress,
            'completed_actions': self.completed_actions,
            'total_actions': self.total_actions,
            'achieved_targets': self.achieved_targets,
            'total_targets': self.total_targets,
            'achieved_energy_savings': self.achieved_energy_savings,
            'achieved_water_savings': self.achieved_water_savings,
            'achieved_waste_reduction': self.achieved_waste_reduction,
            'achieved_cost_savings': self.achieved_cost_savings,
            'on_track': self.on_track,
            'issues_detected': self.issues_detected,
            'notes': self.notes
        }