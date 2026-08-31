"""
Smart Household Resource Optimization Engine - Data Models
Comprehensive models for resource optimization.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
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


class ResourceCategory(Enum):
    """Categories for resource classification."""
    UTILITY = "utility"
    CONSUMABLE = "consumable"
    DURABLE = "durable"
    SERVICE = "service"
    TRANSPORT = "transport"
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
    ON_HOLD = "on_hold"


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
    LIFESTYLE_CHANGE = "lifestyle_change"
    OTHER = "other"


class EfficiencyGrade(Enum):
    """Efficiency grades."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class ImpactLevel(Enum):
    """Impact levels for recommendations."""
    VERY_HIGH = "very_high"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    VERY_LOW = "very_low"


class EffortLevel(Enum):
    """Effort levels for recommendations."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class ConsumptionPattern(Enum):
    """Consumption patterns."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"
    SEASONAL = "seasonal"
    CYCLICAL = "cyclical"


@dataclass
class HouseholdResource:
    """
    Represents a household resource with consumption data.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    resource_type: ResourceType = ResourceType.ENERGY
    category: ResourceCategory = ResourceCategory.UTILITY
    name: str = ""
    description: str = ""
    unit: str = ""
    
    # Consumption data
    current_usage: float = 0.0
    baseline_usage: float = 0.0
    historical_usage: List[Dict[str, Any]] = field(default_factory=list)
    monthly_averages: Dict[str, float] = field(default_factory=dict)
    yearly_averages: Dict[str, float] = field(default_factory=dict)
    
    # Cost data
    cost_per_unit: float = 0.0
    current_cost: float = 0.0
    baseline_cost: float = 0.0
    monthly_costs: Dict[str, float] = field(default_factory=dict)
    
    # Efficiency metrics
    efficiency_score: float = 0.0  # 0-100
    efficiency_grade: EfficiencyGrade = EfficiencyGrade.C
    optimization_potential: float = 0.0  # Percentage
    estimated_savings: float = 0.0
    estimated_impact: float = 0.0
    
    # Patterns
    consumption_pattern: ConsumptionPattern = ConsumptionPattern.STABLE
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    seasonal_variation: float = 0.0
    
    # Benchmarks
    benchmark_low: float = 0.0
    benchmark_medium: float = 0.0
    benchmark_high: float = 0.0
    
    # Member contributions
    member_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    last_updated: datetime = field(default_factory=datetime.now)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'resource_type': self.resource_type.value,
            'category': self.category.value,
            'name': self.name,
            'description': self.description,
            'unit': self.unit,
            'current_usage': self.current_usage,
            'baseline_usage': self.baseline_usage,
            'historical_usage': self.historical_usage,
            'monthly_averages': self.monthly_averages,
            'yearly_averages': self.yearly_averages,
            'cost_per_unit': self.cost_per_unit,
            'current_cost': self.current_cost,
            'baseline_cost': self.baseline_cost,
            'monthly_costs': self.monthly_costs,
            'efficiency_score': self.efficiency_score,
            'efficiency_grade': self.efficiency_grade.value,
            'optimization_potential': self.optimization_potential,
            'estimated_savings': self.estimated_savings,
            'estimated_impact': self.estimated_impact,
            'consumption_pattern': self.consumption_pattern.value,
            'peak_usage_times': self.peak_usage_times,
            'seasonal_variation': self.seasonal_variation,
            'benchmark_low': self.benchmark_low,
            'benchmark_medium': self.benchmark_medium,
            'benchmark_high': self.benchmark_high,
            'member_contributions': self.member_contributions,
            'last_updated': self.last_updated.isoformat(),
            'notes': self.notes,
            'tags': self.tags,
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'HouseholdResource':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            household_id=data.get('household_id', ''),
            resource_type=ResourceType(data.get('resource_type', 'energy')),
            category=ResourceCategory(data.get('category', 'utility')),
            name=data.get('name', ''),
            description=data.get('description', ''),
            unit=data.get('unit', ''),
            current_usage=data.get('current_usage', 0.0),
            baseline_usage=data.get('baseline_usage', 0.0),
            historical_usage=data.get('historical_usage', []),
            monthly_averages=data.get('monthly_averages', {}),
            yearly_averages=data.get('yearly_averages', {}),
            cost_per_unit=data.get('cost_per_unit', 0.0),
            current_cost=data.get('current_cost', 0.0),
            baseline_cost=data.get('baseline_cost', 0.0),
            monthly_costs=data.get('monthly_costs', {}),
            efficiency_score=data.get('efficiency_score', 0.0),
            efficiency_grade=EfficiencyGrade(data.get('efficiency_grade', 'C')),
            optimization_potential=data.get('optimization_potential', 0.0),
            estimated_savings=data.get('estimated_savings', 0.0),
            estimated_impact=data.get('estimated_impact', 0.0),
            consumption_pattern=ConsumptionPattern(data.get('consumption_pattern', 'stable')),
            peak_usage_times=data.get('peak_usage_times', []),
            seasonal_variation=data.get('seasonal_variation', 0.0),
            benchmark_low=data.get('benchmark_low', 0.0),
            benchmark_medium=data.get('benchmark_medium', 0.0),
            benchmark_high=data.get('benchmark_high', 0.0),
            member_contributions=data.get('member_contributions', {}),
            last_updated=datetime.fromisoformat(data['last_updated']) if data.get('last_updated') else datetime.now(),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
            source=data.get('source', '')
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
    
    def get_efficiency_grade(self) -> EfficiencyGrade:
        """Get efficiency grade based on score."""
        score = self.calculate_efficiency_score()
        if score >= 90:
            return EfficiencyGrade.A_PLUS
        elif score >= 80:
            return EfficiencyGrade.A
        elif score >= 65:
            return EfficiencyGrade.B
        elif score >= 50:
            return EfficiencyGrade.C
        elif score >= 35:
            return EfficiencyGrade.D
        else:
            return EfficiencyGrade.F
    
    def calculate_optimization_potential(self) -> float:
        """Calculate optimization potential."""
        if self.baseline_usage == 0:
            return 10.0
        
        ratio = self.current_usage / self.baseline_usage
        if ratio > 1.0:
            potential = min(50, (ratio - 1.0) * 50)
        else:
            potential = max(5, (1.0 - ratio) * 20)
        
        return min(100, potential)
    
    def get_consumption_pattern(self) -> ConsumptionPattern:
        """Determine consumption pattern from historical data."""
        if len(self.historical_usage) < 3:
            return ConsumptionPattern.STABLE
        
        values = [h.get('value', 0) for h in self.historical_usage]
        if len(values) >= 3:
            first = values[0]
            last = values[-1]
            change_pct = ((last - first) / (first + 0.001)) * 100
            
            if change_pct > 10:
                return ConsumptionPattern.INCREASING
            elif change_pct < -10:
                return ConsumptionPattern.DECREASING
            else:
                # Check volatility
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                if variance > mean * 0.5:
                    return ConsumptionPattern.VOLATILE
                return ConsumptionPattern.STABLE
        
        return ConsumptionPattern.STABLE


@dataclass
class BaselineAnalysis:
    """
    Baseline analysis of household resource consumption.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    period_days: int = 30
    household_size: int = 1
    
    # Consumption totals
    total_energy_kwh: float = 0.0
    total_water_liters: float = 0.0
    total_food_kg: float = 0.0
    total_waste_kg: float = 0.0
    total_transport_km: float = 0.0
    total_shopping_items: float = 0.0
    
    # Per capita averages
    per_capita_energy: float = 0.0
    per_capita_water: float = 0.0
    per_capita_food: float = 0.0
    per_capita_waste: float = 0.0
    per_capita_transport: float = 0.0
    per_capita_shopping: float = 0.0
    
    # Efficiency scores
    energy_efficiency: float = 0.0
    water_efficiency: float = 0.0
    waste_efficiency: float = 0.0
    food_efficiency: float = 0.0
    transport_efficiency: float = 0.0
    shopping_efficiency: float = 0.0
    overall_efficiency: float = 0.0
    
    # Category breakdown
    category_breakdown: Dict[str, float] = field(default_factory=dict)
    category_efficiencies: Dict[str, float] = field(default_factory=dict)
    
    # Member breakdown
    member_breakdown: Dict[str, Dict[str, float]] = field(default_factory=dict)
    
    # Benchmarks
    benchmarks: Dict[str, float] = field(default_factory=dict)
    national_averages: Dict[str, float] = field(default_factory=dict)
    
    # Patterns
    consumption_patterns: Dict[str, str] = field(default_factory=dict)
    peak_usage_periods: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    
    # Summary
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'period_days': self.period_days,
            'household_size': self.household_size,
            'total_energy_kwh': self.total_energy_kwh,
            'total_water_liters': self.total_water_liters,
            'total_food_kg': self.total_food_kg,
            'total_waste_kg': self.total_waste_kg,
            'total_transport_km': self.total_transport_km,
            'total_shopping_items': self.total_shopping_items,
            'per_capita_energy': self.per_capita_energy,
            'per_capita_water': self.per_capita_water,
            'per_capita_food': self.per_capita_food,
            'per_capita_waste': self.per_capita_waste,
            'per_capita_transport': self.per_capita_transport,
            'per_capita_shopping': self.per_capita_shopping,
            'energy_efficiency': self.energy_efficiency,
            'water_efficiency': self.water_efficiency,
            'waste_efficiency': self.waste_efficiency,
            'food_efficiency': self.food_efficiency,
            'transport_efficiency': self.transport_efficiency,
            'shopping_efficiency': self.shopping_efficiency,
            'overall_efficiency': self.overall_efficiency,
            'category_breakdown': self.category_breakdown,
            'category_efficiencies': self.category_efficiencies,
            'member_breakdown': self.member_breakdown,
            'benchmarks': self.benchmarks,
            'national_averages': self.national_averages,
            'consumption_patterns': self.consumption_patterns,
            'peak_usage_periods': self.peak_usage_periods,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses,
            'opportunities': self.opportunities,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaselineAnalysis':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            household_id=data.get('household_id', ''),
            analysis_date=datetime.fromisoformat(data['analysis_date']) if data.get('analysis_date') else datetime.now(),
            period_days=data.get('period_days', 30),
            household_size=data.get('household_size', 1),
            total_energy_kwh=data.get('total_energy_kwh', 0.0),
            total_water_liters=data.get('total_water_liters', 0.0),
            total_food_kg=data.get('total_food_kg', 0.0),
            total_waste_kg=data.get('total_waste_kg', 0.0),
            total_transport_km=data.get('total_transport_km', 0.0),
            total_shopping_items=data.get('total_shopping_items', 0.0),
            per_capita_energy=data.get('per_capita_energy', 0.0),
            per_capita_water=data.get('per_capita_water', 0.0),
            per_capita_food=data.get('per_capita_food', 0.0),
            per_capita_waste=data.get('per_capita_waste', 0.0),
            per_capita_transport=data.get('per_capita_transport', 0.0),
            per_capita_shopping=data.get('per_capita_shopping', 0.0),
            energy_efficiency=data.get('energy_efficiency', 0.0),
            water_efficiency=data.get('water_efficiency', 0.0),
            waste_efficiency=data.get('waste_efficiency', 0.0),
            food_efficiency=data.get('food_efficiency', 0.0),
            transport_efficiency=data.get('transport_efficiency', 0.0),
            shopping_efficiency=data.get('shopping_efficiency', 0.0),
            overall_efficiency=data.get('overall_efficiency', 0.0),
            category_breakdown=data.get('category_breakdown', {}),
            category_efficiencies=data.get('category_efficiencies', {}),
            member_breakdown=data.get('member_breakdown', {}),
            benchmarks=data.get('benchmarks', {}),
            national_averages=data.get('national_averages', {}),
            consumption_patterns=data.get('consumption_patterns', {}),
            peak_usage_periods=data.get('peak_usage_periods', {}),
            strengths=data.get('strengths', []),
            weaknesses=data.get('weaknesses', []),
            opportunities=data.get('opportunities', []),
            notes=data.get('notes', '')
        )


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
    consumption_change_percentage: float = 0.0
    
    # Appliance breakdown
    appliance_consumption: Dict[str, float] = field(default_factory=dict)
    appliance_efficiency: Dict[str, float] = field(default_factory=dict)
    
    # High consumption detection
    high_consumption_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Efficiency opportunities
    efficiency_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    reduction_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_energy_savings: float = 0.0
    estimated_cost_savings: float = 0.0
    estimated_carbon_savings: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Implementation plan
    implementation_phases: List[Dict[str, Any]] = field(default_factory=list)
    estimated_implementation_cost: float = 0.0
    payback_period_months: float = 0.0
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_consumption': self.total_consumption,
            'baseline_consumption': self.baseline_consumption,
            'consumption_difference': self.consumption_difference,
            'consumption_change_percentage': self.consumption_change_percentage,
            'appliance_consumption': self.appliance_consumption,
            'appliance_efficiency': self.appliance_efficiency,
            'high_consumption_areas': self.high_consumption_areas,
            'peak_usage_times': self.peak_usage_times,
            'efficiency_opportunities': self.efficiency_opportunities,
            'reduction_scenarios': self.reduction_scenarios,
            'estimated_energy_savings': self.estimated_energy_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_carbon_savings': self.estimated_carbon_savings,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'implementation_phases': self.implementation_phases,
            'estimated_implementation_cost': self.estimated_implementation_cost,
            'payback_period_months': self.payback_period_months,
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
    usage_change_percentage: float = 0.0
    
    # Usage breakdown
    fixture_usage: Dict[str, float] = field(default_factory=dict)
    fixture_efficiency: Dict[str, float] = field(default_factory=dict)
    
    # High usage detection
    high_usage_areas: List[Dict[str, Any]] = field(default_factory=list)
    peak_usage_times: List[Dict[str, Any]] = field(default_factory=list)
    
    # Reduction opportunities
    reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    efficiency_improvements: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_water_savings: float = 0.0
    estimated_cost_savings: float = 0.0
    estimated_environmental_impact: float = 0.0
    
    # Recommendations
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    # Implementation plan
    implementation_phases: List[Dict[str, Any]] = field(default_factory=list)
    estimated_implementation_cost: float = 0.0
    payback_period_months: float = 0.0
    
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'analysis_date': self.analysis_date.isoformat(),
            'total_usage': self.total_usage,
            'baseline_usage': self.baseline_usage,
            'usage_difference': self.usage_difference,
            'usage_change_percentage': self.usage_change_percentage,
            'fixture_usage': self.fixture_usage,
            'fixture_efficiency': self.fixture_efficiency,
            'high_usage_areas': self.high_usage_areas,
            'peak_usage_times': self.peak_usage_times,
            'reduction_opportunities': self.reduction_opportunities,
            'efficiency_improvements': self.efficiency_improvements,
            'estimated_water_savings': self.estimated_water_savings,
            'estimated_cost_savings': self.estimated_cost_savings,
            'estimated_environmental_impact': self.estimated_environmental_impact,
            'recommendations': self.recommendations,
            'priority_recommendations': self.priority_recommendations,
            'implementation_phases': self.implementation_phases,
            'estimated_implementation_cost': self.estimated_implementation_cost,
            'payback_period_months': self.payback_period_months,
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
    food_cost: float = 0.0
    food_waste_cost: float = 0.0
    
    # Food categories
    category_consumption: Dict[str, float] = field(default_factory=dict)
    category_waste: Dict[str, float] = field(default_factory=dict)
    category_waste_percentage: Dict[str, float] = field(default_factory=dict)
    
    # Waste analysis
    total_waste: float = 0.0
    recyclable_waste: float = 0.0
    compostable_waste: float = 0.0
    landfill_waste: float = 0.0
    recycling_rate: float = 0.0
    
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
    
    # Implementation plan
    implementation_phases: List[Dict[str, Any]] = field(default_factory=list)
    
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
    transportation_cost: float = 0.0
    
    # Mode breakdown
    mode_usage: Dict[str, float] = field(default_factory=dict)
    mode_emissions: Dict[str, float] = field(default_factory=dict)
    mode_costs: Dict[str, float] = field(default_factory=dict)
    
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
    priority_recommendations: List[Dict[str, Any]] = field(default_factory=list)
    
    notes: str = ""


@dataclass
class ShoppingOptimization:
    """
    Shopping optimization analysis.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    analysis_date: datetime = field(default_factory=datetime.now)
    
    # Shopping analysis
    total_spending: float = 0.0
    total_items: float = 0.0
    shopping_frequency: float = 0.0
    average_spend_per_trip: float = 0.0
    
    # Category breakdown
    category_spending: Dict[str, float] = field(default_factory=dict)
    category_items: Dict[str, float] = field(default_factory=dict)
    
    # Sustainability metrics
    sustainable_purchases: float = 0.0
    sustainable_percentage: float = 0.0
    packaging_waste: float = 0.0
    
    # Optimization opportunities
    reduction_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    sustainable_alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # Savings estimates
    estimated_cost_savings: float = 0.0
    estimated_waste_reduction: float = 0.0
    
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
    current_shopping_cost: float = 0.0
    total_current_cost: float = 0.0
    
    # Potential savings
    potential_energy_savings: float = 0.0
    potential_water_savings: float = 0.0
    potential_food_savings: float = 0.0
    potential_waste_savings: float = 0.0
    potential_transport_savings: float = 0.0
    potential_shopping_savings: float = 0.0
    total_potential_savings: float = 0.0
    
    # Environmental impact
    current_carbon_footprint: float = 0.0
    potential_carbon_reduction: float = 0.0
    current_water_footprint: float = 0.0
    potential_water_reduction: float = 0.0
    current_waste_generation: float = 0.0
    potential_waste_reduction: float = 0.0
    
    # ROI analysis
    investment_needed: float = 0.0
    payback_period_months: float = 0.0
    roi_percentage: float = 0.0
    roi_indicators: Dict[str, float] = field(default_factory=dict)
    
    # Effort vs impact
    effort_vs_impact: Dict[str, str] = field(default_factory=dict)
    
    # Projections
    five_year_savings: float = 0.0
    ten_year_savings: float = 0.0
    
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
    food_waste_reduction: float = 0.0
    shopping_reduction: float = 0.0
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
    
    # Implementation
    implementation_difficulty: str = ""  # easy, medium, hard
    implementation_cost: float = 0.0
    time_to_implement_days: int = 0
    
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
    progress_history: List[Dict[str, Any]] = field(default_factory=list)
    
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
            'achieved_date': self.achieved_date.isoformat() if self.achieved_date else None,
            'progress_history': self.progress_history
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
            achieved_date=datetime.fromisoformat(data['achieved_date']) if data.get('achieved_date') else None,
            progress_history=data.get('progress_history', [])
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
    individual_shopping: float = 0.0
    
    # Shared contributions
    shared_energy: float = 0.0
    shared_water: float = 0.0
    shared_food: float = 0.0
    shared_waste: float = 0.0
    shared_transport: float = 0.0
    shared_shopping: float = 0.0
    
    # Total contributions
    total_energy: float = 0.0
    total_water: float = 0.0
    total_food: float = 0.0
    total_waste: float = 0.0
    total_transport: float = 0.0
    total_shopping: float = 0.0
    
    # Category contributions
    category_contributions: Dict[str, float] = field(default_factory=dict)
    
    # Improvement opportunities
    improvement_opportunities: List[Dict[str, Any]] = field(default_factory=list)
    
    # Household impact
    household_impact_percentage: float = 0.0
    contribution_rank: int = 0
    
    notes: str = ""


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
    
    # Benchmarks
    benchmarks: Dict[str, float] = field(default_factory=dict)
    
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
            'benchmarks': self.benchmarks,
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
    achieved_carbon_reduction: float = 0.0
    
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
            'achieved_carbon_reduction': self.achieved_carbon_reduction,
            'on_track': self.on_track,
            'issues_detected': self.issues_detected,
            'notes': self.notes
        }