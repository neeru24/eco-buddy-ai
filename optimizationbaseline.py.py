"""
Smart Household Resource Optimization Engine - Baseline Analysis
Establishes household consumption baselines.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    BaselineAnalysis, HouseholdResource, ResourceType,
    ConsumptionPattern
)

logger = logging.getLogger(__name__)


class BaselineAnalyzer:
    """
    Analyzes and establishes household consumption baselines.
    """
    
    def __init__(self):
        """Initialize the baseline analyzer."""
        self.national_averages = self._initialize_national_averages()
        self.efficiency_benchmarks = self._initialize_efficiency_benchmarks()
        self.pattern_indicators = self._initialize_pattern_indicators()
        logger.info("Baseline Analyzer initialized")
    
    def _initialize_national_averages(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize national average consumption data.
        """
        return {
            'energy': {
                'per_capita_monthly': 350.0,  # kWh
                'per_household_monthly': 900.0,
                'low_usage': 250.0,
                'high_usage': 600.0
            },
            'water': {
                'per_capita_monthly': 3000.0,  # liters
                'per_household_monthly': 8000.0,
                'low_usage': 2000.0,
                'high_usage': 5000.0
            },
            'waste': {
                'per_capita_monthly': 30.0,   # kg
                'per_household_monthly': 80.0,
                'low_usage': 20.0,
                'high_usage': 50.0
            },
            'food': {
                'per_capita_monthly': 80.0,   # kg
                'per_household_monthly': 200.0,
                'low_usage': 60.0,
                'high_usage': 120.0
            },
            'transportation': {
                'per_capita_monthly': 400.0,  # km
                'per_household_monthly': 1000.0,
                'low_usage': 300.0,
                'high_usage': 600.0
            },
            'shopping': {
                'per_capita_monthly': 20.0,   # items
                'per_household_monthly': 50.0,
                'low_usage': 15.0,
                'high_usage': 35.0
            }
        }
    
    def _initialize_efficiency_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize efficiency benchmarks.
        """
        return {
            'energy': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0},
            'water': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0},
            'waste': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0},
            'food': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0},
            'transportation': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0},
            'shopping': {'efficient': 80.0, 'average': 50.0, 'inefficient': 30.0}
        }
    
    def _initialize_pattern_indicators(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize pattern indicators.
        """
        return {
            'increasing': {'threshold': 10.0, 'label': 'Usage is increasing'},
            'decreasing': {'threshold': -10.0, 'label': 'Usage is decreasing'},
            'stable': {'threshold': 5.0, 'label': 'Usage is stable'},
            'volatile': {'cv': 0.3, 'label': 'Usage is volatile'}
        }
    
    def establish_baseline(self, 
                          resources: List[HouseholdResource],
                          household_size: int,
                          period_days: int = 30) -> BaselineAnalysis:
        """
        Establish baseline analysis for a household.
        
        Args:
            resources: List of household resources
            household_size: Number of household members
            period_days: Analysis period in days
        
        Returns:
            BaselineAnalysis: Baseline analysis
        """
        baseline = BaselineAnalysis(
            household_id=resources[0].household_id if resources else "",
            period_days=period_days,
            household_size=household_size
        )
        
        # Calculate totals from resources
        totals = self._calculate_resource_totals(resources)
        
        baseline.total_energy_kwh = totals.get('energy', 0.0)
        baseline.total_water_liters = totals.get('water', 0.0)
        baseline.total_food_kg = totals.get('food', 0.0)
        baseline.total_waste_kg = totals.get('waste', 0.0)
        baseline.total_transport_km = totals.get('transportation', 0.0)
        baseline.total_shopping_items = totals.get('shopping', 0.0)
        
        # Calculate per capita
        if household_size > 0:
            baseline.per_capita_energy = baseline.total_energy_kwh / household_size
            baseline.per_capita_water = baseline.total_water_liters / household_size
            baseline.per_capita_food = baseline.total_food_kg / household_size
            baseline.per_capita_waste = baseline.total_waste_kg / household_size
            baseline.per_capita_transport = baseline.total_transport_km / household_size
            baseline.per_capita_shopping = baseline.total_shopping_items / household_size
        
        # Calculate efficiency scores
        baseline.energy_efficiency = self._calculate_category_efficiency(
            baseline.total_energy_kwh, 'energy', household_size
        )
        baseline.water_efficiency = self._calculate_category_efficiency(
            baseline.total_water_liters, 'water', household_size
        )
        baseline.food_efficiency = self._calculate_category_efficiency(
            baseline.total_food_kg, 'food', household_size
        )
        baseline.waste_efficiency = self._calculate_category_efficiency(
            baseline.total_waste_kg, 'waste', household_size
        )
        baseline.transport_efficiency = self._calculate_category_efficiency(
            baseline.total_transport_km, 'transportation', household_size
        )
        baseline.shopping_efficiency = self._calculate_category_efficiency(
            baseline.total_shopping_items, 'shopping', household_size
        )
        
        # Calculate overall efficiency
        efficiencies = [
            baseline.energy_efficiency,
            baseline.water_efficiency,
            baseline.food_efficiency,
            baseline.waste_efficiency,
            baseline.transport_efficiency,
            baseline.shopping_efficiency
        ]
        baseline.overall_efficiency = statistics.mean(efficiencies)
        
        # Category breakdown
        baseline.category_breakdown = self._create_category_breakdown(resources)
        baseline.category_efficiencies = self._create_category_efficiencies(resources, household_size)
        
        # Member breakdown
        baseline.member_breakdown = self._create_member_breakdown(resources)
        
        # Benchmarks
        baseline.benchmarks = self._get_benchmarks(resources, household_size)
        baseline.national_averages = self._get_national_averages(resources, household_size)
        
        # Consumption patterns
        baseline.consumption_patterns = self._detect_consumption_patterns(resources)
        baseline.peak_usage_periods = self._detect_peak_periods(resources)
        
        # Strengths, weaknesses, opportunities
        baseline.strengths = self._identify_strengths(baseline)
        baseline.weaknesses = self._identify_weaknesses(baseline)
        baseline.opportunities = self._identify_opportunities(baseline)
        
        logger.info(f"Baseline established for household {baseline.household_id}")
        return baseline
    
    def _calculate_resource_totals(self, 
                                  resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate totals by resource type.
        """
        totals = {}
        for resource in resources:
            key = resource.resource_type.value
            totals[key] = totals.get(key, 0.0) + resource.current_usage
        return totals
    
    def _calculate_category_efficiency(self, 
                                      total_usage: float,
                                      category: str,
                                      household_size: int) -> float:
        """
        Calculate efficiency score for a category.
        """
        if household_size == 0:
            return 50.0
        
        # Get national average for this category
        avg_data = self.national_averages.get(category, {})
        per_capita_avg = avg_data.get('per_capita_monthly', 0)
        
        if per_capita_avg == 0:
            return 50.0
        
        # Calculate per capita usage
        per_capita_usage = total_usage / household_size
        
        # Calculate efficiency (lower is better for most resources)
        ratio = per_capita_usage / per_capita_avg
        
        if ratio <= 0.5:
            return 90
        elif ratio <= 0.8:
            return 75
        elif ratio <= 1.0:
            return 60
        elif ratio <= 1.5:
            return 40
        elif ratio <= 2.0:
            return 20
        else:
            return 10
    
    def _create_category_breakdown(self, 
                                  resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Create category breakdown.
        """
        breakdown = {}
        for resource in resources:
            breakdown[resource.resource_type.value] = resource.current_usage
        return breakdown
    
    def _create_category_efficiencies(self, 
                                     resources: List[HouseholdResource],
                                     household_size: int) -> Dict[str, float]:
        """
        Create category efficiencies.
        """
        efficiencies = {}
        for resource in resources:
            key = resource.resource_type.value
            efficiencies[key] = resource.calculate_efficiency_score()
        return efficiencies
    
    def _create_member_breakdown(self, 
                                resources: List[HouseholdResource]) -> Dict[str, Dict[str, float]]:
        """
        Create member contribution breakdown.
        """
        if not resources:
            return {}
        
        breakdown = {}
        for resource in resources:
            if resource.member_contributions:
                for member_id, contribution in resource.member_contributions.items():
                    if member_id not in breakdown:
                        breakdown[member_id] = {}
                    breakdown[member_id][resource.resource_type.value] = contribution
        
        return breakdown
    
    def _get_benchmarks(self, 
                       resources: List[HouseholdResource],
                       household_size: int) -> Dict[str, float]:
        """
        Get benchmark values for each category.
        """
        benchmarks = {}
        
        for resource in resources:
            key = resource.resource_type.value
            avg_data = self.national_averages.get(key, {})
            
            if household_size > 0:
                benchmarks[f"{key}_per_capita"] = avg_data.get('per_capita_monthly', 0)
                benchmarks[f"{key}_per_household"] = avg_data.get('per_household_monthly', 0) or (
                    avg_data.get('per_capita_monthly', 0) * household_size
                )
                benchmarks[f"{key}_low"] = avg_data.get('low_usage', 0)
                benchmarks[f"{key}_high"] = avg_data.get('high_usage', 0)
        
        return benchmarks
    
    def _get_national_averages(self, 
                              resources: List[HouseholdResource],
                              household_size: int) -> Dict[str, float]:
        """
        Get national averages for each category.
        """
        averages = {}
        
        for resource in resources:
            key = resource.resource_type.value
            avg_data = self.national_averages.get(key, {})
            
            if household_size > 0:
                averages[key] = avg_data.get('per_capita_monthly', 0) * household_size
        
        return averages
    
    def _detect_consumption_patterns(self, 
                                    resources: List[HouseholdResource]) -> Dict[str, str]:
        """
        Detect consumption patterns.
        """
        patterns = {}
        
        for resource in resources:
            patterns[resource.resource_type.value] = resource.get_consumption_pattern().value
        
        return patterns
    
    def _detect_peak_periods(self, 
                            resources: List[HouseholdResource]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect peak usage periods.
        """
        peak_periods = {}
        
        for resource in resources:
            if resource.peak_usage_times:
                peak_periods[resource.resource_type.value] = resource.peak_usage_times
        
        return peak_periods
    
    def _identify_strengths(self, baseline: BaselineAnalysis) -> List[str]:
        """
        Identify baseline strengths.
        """
        strengths = []
        
        if baseline.energy_efficiency > 70:
            strengths.append(f"Energy efficiency is above average ({baseline.energy_efficiency:.1f}%)")
        
        if baseline.water_efficiency > 70:
            strengths.append(f"Water efficiency is above average ({baseline.water_efficiency:.1f}%)")
        
        if baseline.waste_efficiency > 70:
            strengths.append(f"Waste management is efficient ({baseline.waste_efficiency:.1f}%)")
        
        if baseline.overall_efficiency > 70:
            strengths.append(f"Overall household efficiency is good ({baseline.overall_efficiency:.1f}%)")
        
        return strengths
    
    def _identify_weaknesses(self, baseline: BaselineAnalysis) -> List[str]:
        """
        Identify baseline weaknesses.
        """
        weaknesses = []
        
        if baseline.energy_efficiency < 40:
            weaknesses.append(f"Energy efficiency needs improvement ({baseline.energy_efficiency:.1f}%)")
        
        if baseline.water_efficiency < 40:
            weaknesses.append(f"Water efficiency needs improvement ({baseline.water_efficiency:.1f}%)")
        
        if baseline.waste_efficiency < 40:
            weaknesses.append(f"Waste management needs improvement ({baseline.waste_efficiency:.1f}%)")
        
        if baseline.overall_efficiency < 40:
            weaknesses.append(f"Overall household efficiency needs significant improvement ({baseline.overall_efficiency:.1f}%)")
        
        return weaknesses
    
    def _identify_opportunities(self, baseline: BaselineAnalysis) -> List[str]:
        """
        Identify improvement opportunities.
        """
        opportunities = []
        
        # Find categories with highest improvement potential
        efficiencies = {
            'energy': baseline.energy_efficiency,
            'water': baseline.water_efficiency,
            'waste': baseline.waste_efficiency,
            'food': baseline.food_efficiency,
            'transport': baseline.transport_efficiency,
            'shopping': baseline.shopping_efficiency
        }
        
        for category, efficiency in sorted(efficiencies.items(), key=lambda x: x[1]):
            if efficiency < 50:
                opportunities.append(f"Focus on improving {category} efficiency (currently {efficiency:.1f}%)")
        
        return opportunities[:3]
    
    def compare_to_baseline(self, 
                           analysis: BaselineAnalysis,
                           new_resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Compare new consumption to baseline.
        
        Args:
            analysis: Baseline analysis
            new_resources: New resource data
        
        Returns:
            Dict: Comparison results
        """
        new_totals = self._calculate_resource_totals(new_resources)
        
        comparison = {
            'date': datetime.now().isoformat(),
            'differences': {},
            'percentage_changes': {},
            'overall_improvement': 0.0,
            'improved_categories': [],
            'declined_categories': [],
            'savings': {}
        }
        
        baseline_totals = {
            'energy': analysis.total_energy_kwh,
            'water': analysis.total_water_liters,
            'food': analysis.total_food_kg,
            'waste': analysis.total_waste_kg,
            'transportation': analysis.total_transport_km,
            'shopping': analysis.total_shopping_items
        }
        
        for category, baseline_value in baseline_totals.items():
            if category in new_totals:
                new_value = new_totals[category]
                diff = new_value - baseline_value
                pct_change = (diff / (baseline_value + 0.001)) * 100
                
                comparison['differences'][category] = diff
                comparison['percentage_changes'][category] = pct_change
                comparison['savings'][category] = -diff if diff < 0 else 0
                
                # Determine if improved (decrease for most categories)
                if category in ['energy', 'water', 'waste']:
                    if pct_change < 0:
                        comparison['improved_categories'].append(category)
                    else:
                        comparison['declined_categories'].append(category)
                else:
                    if pct_change < 0:
                        comparison['declined_categories'].append(category)
                    else:
                        comparison['improved_categories'].append(category)
        
        # Calculate overall improvement
        if comparison['improved_categories'] or comparison['declined_categories']:
            total_improved = len(comparison['improved_categories'])
            total_declined = len(comparison['declined_categories'])
            total_categories = total_improved + total_declined
            
            if total_categories > 0:
                comparison['overall_improvement'] = (
                    (total_improved / total_categories) * 100
                ) - ((total_declined / total_categories) * 100)
        
        return comparison
    
    def get_baseline_summary(self, 
                            analysis: BaselineAnalysis) -> Dict[str, Any]:
        """
        Get summary of baseline analysis.
        
        Args:
            analysis: Baseline analysis
        
        Returns:
            Dict: Summary
        """
        return {
            'period_days': analysis.period_days,
            'household_size': analysis.household_size,
            'total_energy_kwh': analysis.total_energy_kwh,
            'total_water_liters': analysis.total_water_liters,
            'total_food_kg': analysis.total_food_kg,
            'total_waste_kg': analysis.total_waste_kg,
            'total_transport_km': analysis.total_transport_km,
            'per_capita_energy': analysis.per_capita_energy,
            'per_capita_water': analysis.per_capita_water,
            'overall_efficiency': analysis.overall_efficiency,
            'overall_grade': self._get_efficiency_grade(analysis.overall_efficiency),
            'category_efficiencies': {
                'energy': analysis.energy_efficiency,
                'water': analysis.water_efficiency,
                'food': analysis.food_efficiency,
                'waste': analysis.waste_efficiency,
                'transport': analysis.transport_efficiency,
                'shopping': analysis.shopping_efficiency
            },
            'category_grades': {
                'energy': self._get_efficiency_grade(analysis.energy_efficiency),
                'water': self._get_efficiency_grade(analysis.water_efficiency),
                'food': self._get_efficiency_grade(analysis.food_efficiency),
                'waste': self._get_efficiency_grade(analysis.waste_efficiency),
                'transport': self._get_efficiency_grade(analysis.transport_efficiency),
                'shopping': self._get_efficiency_grade(analysis.shopping_efficiency)
            },
            'strongest_category': self._get_strongest_category(analysis),
            'weakest_category': self._get_weakest_category(analysis),
            'strengths': analysis.strengths,
            'weaknesses': analysis.weaknesses,
            'opportunities': analysis.opportunities,
            'consumption_patterns': analysis.consumption_patterns
        }
    
    def _get_efficiency_grade(self, score: float) -> str:
        """
        Get efficiency grade.
        """
        if score >= 85:
            return "A+"
        elif score >= 75:
            return "A"
        elif score >= 60:
            return "B"
        elif score >= 45:
            return "C"
        elif score >= 30:
            return "D"
        else:
            return "F"
    
    def _get_strongest_category(self, analysis: BaselineAnalysis) -> str:
        """
        Get strongest category.
        """
        categories = {
            'energy': analysis.energy_efficiency,
            'water': analysis.water_efficiency,
            'food': analysis.food_efficiency,
            'waste': analysis.waste_efficiency,
            'transport': analysis.transport_efficiency,
            'shopping': analysis.shopping_efficiency
        }
        
        if categories:
            return max(categories.items(), key=lambda x: x[1])[0]
        return ""
    
    def _get_weakest_category(self, analysis: BaselineAnalysis) -> str:
        """
        Get weakest category.
        """
        categories = {
            'energy': analysis.energy_efficiency,
            'water': analysis.water_efficiency,
            'food': analysis.food_efficiency,
            'waste': analysis.waste_efficiency,
            'transport': analysis.transport_efficiency,
            'shopping': analysis.shopping_efficiency
        }
        
        if categories:
            return min(categories.items(), key=lambda x: x[1])[0]
        return ""