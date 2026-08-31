"""
Smart Household Resource Optimization Engine - Cost & Impact Analyzer
Analyzes costs and environmental impact of household consumption.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    CostImpactAnalysis, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class CostImpactAnalyzer:
    """
    Analyzes costs and environmental impact.
    """
    
    def __init__(self):
        """Initialize the cost and impact analyzer."""
        self.cost_rates = self._initialize_cost_rates()
        self.emission_factors = self._initialize_emission_factors()
        self.impact_weights = self._initialize_impact_weights()
        logger.info("Cost & Impact Analyzer initialized")
    
    def _initialize_cost_rates(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize cost rates for different resources.
        """
        return {
            'energy': {
                'per_kwh': 0.15,
                'monthly_fixed': 10.0,
                'unit': 'kWh'
            },
            'water': {
                'per_liter': 0.005,
                'monthly_fixed': 15.0,
                'unit': 'liters'
            },
            'waste': {
                'per_kg': 0.05,
                'monthly_fixed': 10.0,
                'unit': 'kg'
            },
            'food': {
                'per_kg': 5.0,
                'monthly_fixed': 0.0,
                'unit': 'kg'
            },
            'transportation': {
                'per_km': 0.30,
                'monthly_fixed': 0.0,
                'unit': 'km'
            },
            'shopping': {
                'per_item': 25.0,
                'monthly_fixed': 0.0,
                'unit': 'items'
            }
        }
    
    def _initialize_emission_factors(self) -> Dict[str, float]:
        """
        Initialize emission factors.
        """
        return {
            'energy': 0.5,  # kg CO2 per kWh
            'water': 0.001,  # kg CO2 per liter
            'waste': 0.2,  # kg CO2 per kg
            'food': 0.5,  # kg CO2 per kg
            'transportation': 0.18,  # kg CO2 per km
            'shopping': 2.0  # kg CO2 per item
        }
    
    def _initialize_impact_weights(self) -> Dict[str, float]:
        """
        Initialize impact weights for scoring.
        """
        return {
            'energy': 0.25,
            'water': 0.20,
            'waste': 0.20,
            'food': 0.15,
            'transportation': 0.15,
            'shopping': 0.05
        }
    
    def analyze_costs_impact(self, 
                            resources: List[HouseholdResource],
                            household_size: int) -> CostImpactAnalysis:
        """
        Analyze costs and environmental impact.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            CostImpactAnalysis: Cost and impact analysis
        """
        analysis = CostImpactAnalysis(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Calculate current costs by category
        for resource in resources:
            key = resource.resource_type.value
            cost_rates = self.cost_rates.get(key, {})
            cost = resource.current_usage * cost_rates.get('per_' + cost_rates.get('unit', 'kwh'), 0)
            fixed = cost_rates.get('monthly_fixed', 0)
            
            if key == 'energy':
                analysis.current_energy_cost = cost + fixed
            elif key == 'water':
                analysis.current_water_cost = cost + fixed
            elif key == 'food':
                analysis.current_food_cost = cost
            elif key == 'waste':
                analysis.current_waste_cost = cost + fixed
            elif key == 'transportation':
                analysis.current_transport_cost = cost
        
        # Calculate total current cost
        analysis.total_current_cost = (
            analysis.current_energy_cost +
            analysis.current_water_cost +
            analysis.current_food_cost +
            analysis.current_waste_cost +
            analysis.current_transport_cost
        )
        
        # Calculate potential savings
        savings = self._calculate_potential_savings(resources)
        analysis.potential_energy_savings = savings.get('energy', 0)
        analysis.potential_water_savings = savings.get('water', 0)
        analysis.potential_food_savings = savings.get('food', 0)
        analysis.potential_waste_savings = savings.get('waste', 0)
        analysis.potential_transport_savings = savings.get('transportation', 0)
        analysis.total_potential_savings = sum(savings.values())
        
        # Calculate environmental impact
        impact = self._calculate_environmental_impact(resources)
        analysis.current_carbon_footprint = impact.get('carbon', 0)
        analysis.potential_carbon_reduction = impact.get('potential_carbon_reduction', 0)
        analysis.current_water_footprint = impact.get('water', 0)
        analysis.potential_water_reduction = impact.get('potential_water_reduction', 0)
        
        # Calculate ROI indicators
        analysis.roi_indicators = self._calculate_roi_indicators(resources, savings)
        
        # Calculate effort vs impact
        analysis.effort_vs_impact = self._calculate_effort_vs_impact(resources, savings)
        
        return analysis
    
    def _calculate_potential_savings(self, 
                                    resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate potential savings by category.
        """
        savings = {}
        
        for resource in resources:
            key = resource.resource_type.value
            
            # Calculate potential savings based on efficiency
            if resource.optimization_potential > 0:
                potential = resource.current_usage * (resource.optimization_potential / 100)
                cost_rates = self.cost_rates.get(key, {})
                cost_per_unit = cost_rates.get('per_' + cost_rates.get('unit', 'kwh'), 0)
                savings[key] = savings.get(key, 0) + (potential * cost_per_unit)
            else:
                # Default 10% savings
                potential = resource.current_usage * 0.1
                cost_rates = self.cost_rates.get(key, {})
                cost_per_unit = cost_rates.get('per_' + cost_rates.get('unit', 'kwh'), 0)
                savings[key] = savings.get(key, 0) + (potential * cost_per_unit)
        
        return savings
    
    def _calculate_environmental_impact(self, 
                                      resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate environmental impact.
        """
        impact = {
            'carbon': 0.0,
            'water': 0.0,
            'potential_carbon_reduction': 0.0,
            'potential_water_reduction': 0.0
        }
        
        for resource in resources:
            key = resource.resource_type.value
            emission_factor = self.emission_factors.get(key, 0)
            
            # Current carbon
            impact['carbon'] += resource.current_usage * emission_factor
            
            # Potential carbon reduction (assuming 20% reduction possible)
            impact['potential_carbon_reduction'] += resource.current_usage * emission_factor * 0.2
            
            # Water impact (mainly from water and energy)
            if key == 'water':
                impact['water'] += resource.current_usage
                impact['potential_water_reduction'] += resource.current_usage * 0.2
            elif key == 'energy':
                # Energy production uses water
                impact['water'] += resource.current_usage * 0.5  # 0.5 liters per kWh
                impact['potential_water_reduction'] += resource.current_usage * 0.5 * 0.2
        
        return impact
    
    def _calculate_roi_indicators(self, 
                                 resources: List[HouseholdResource],
                                 savings: Dict[str, float]) -> Dict[str, float]:
        """
        Calculate ROI indicators.
        """
        roi = {}
        
        for key, saving in savings.items():
            # Estimate investment needed (rough)
            if key == 'energy':
                investment = saving * 5  # 5x monthly savings
            elif key == 'water':
                investment = saving * 8
            elif key == 'food':
                investment = saving * 2
            elif key == 'waste':
                investment = saving * 3
            elif key == 'transportation':
                investment = saving * 6
            else:
                investment = saving * 4
            
            if investment > 0:
                roi[key] = (saving / investment) * 100  # ROI percentage
            else:
                roi[key] = 0
        
        return roi
    
    def _calculate_effort_vs_impact(self, 
                                   resources: List[HouseholdResource],
                                   savings: Dict[str, float]) -> Dict[str, str]:
        """
        Calculate effort vs impact rating.
        """
        effort_vs_impact = {}
        
        for key, saving in savings.items():
            # Determine effort based on category
            if key in ['energy', 'water']:
                effort = 'medium'
            elif key in ['waste', 'food']:
                effort = 'low'
            else:
                effort = 'medium'
            
            # Determine impact based on savings
            if saving > 50:
                impact = 'high'
            elif saving > 20:
                impact = 'medium'
            else:
                impact = 'low'
            
            # Combine
            if effort == 'low' and impact == 'high':
                rating = 'excellent'
            elif effort == 'low' and impact == 'medium':
                rating = 'good'
            elif effort == 'medium' and impact == 'high':
                rating = 'good'
            elif effort == 'high' and impact == 'high':
                rating = 'moderate'
            elif effort == 'high' and impact == 'low':
                rating = 'poor'
            else:
                rating = 'moderate'
            
            effort_vs_impact[key] = rating
        
        return effort_vs_impact
    
    def generate_summary(self, 
                        analysis: CostImpactAnalysis) -> Dict[str, Any]:
        """
        Generate summary of cost and impact analysis.
        
        Args:
            analysis: Cost impact analysis
        
        Returns:
            Dict: Summary
        """
        return {
            'total_current_cost': analysis.total_current_cost,
            'total_potential_savings': analysis.total_potential_savings,
            'savings_percentage': (analysis.total_potential_savings / analysis.total_current_cost * 100) if analysis.total_current_cost > 0 else 0,
            'current_carbon_footprint': analysis.current_carbon_footprint,
            'potential_carbon_reduction': analysis.potential_carbon_reduction,
            'carbon_reduction_percentage': (analysis.potential_carbon_reduction / analysis.current_carbon_footprint * 100) if analysis.current_carbon_footprint > 0 else 0,
            'monthly_breakdown': {
                'energy': analysis.current_energy_cost,
                'water': analysis.current_water_cost,
                'food': analysis.current_food_cost,
                'waste': analysis.current_waste_cost,
                'transport': analysis.current_transport_cost
            },
            'savings_breakdown': {
                'energy': analysis.potential_energy_savings,
                'water': analysis.potential_water_savings,
                'food': analysis.potential_food_savings,
                'waste': analysis.potential_waste_savings,
                'transport': analysis.potential_transport_savings
            },
            'best_roi': max(analysis.roi_indicators.items(), key=lambda x: x[1]) if analysis.roi_indicators else None,
            'best_effort_vs_impact': self._get_best_effort_vs_impact(analysis.effort_vs_impact),
            'annual_savings': analysis.total_potential_savings * 12,
            'annual_carbon_reduction': analysis.potential_carbon_reduction * 12
        }
    
    def _get_best_effort_vs_impact(self, 
                                  effort_vs_impact: Dict[str, str]) -> str:
        """
        Get best effort vs impact category.
        """
        priority = {'excellent': 0, 'good': 1, 'moderate': 2, 'poor': 3}
        best = min(effort_vs_impact.items(), key=lambda x: priority.get(x[1], 4))
        return f"{best[0]}: {best[1]}"
    
    def get_financial_forecast(self, 
                              analysis: CostImpactAnalysis,
                              months: int = 12) -> Dict[str, Any]:
        """
        Get financial forecast.
        
        Args:
            analysis: Cost impact analysis
            months: Number of months to forecast
        
        Returns:
            Dict: Financial forecast
        """
        return {
            'current_cost_forecast': analysis.total_current_cost * months,
            'optimized_cost_forecast': (analysis.total_current_cost - analysis.total_potential_savings) * months,
            'total_savings_forecast': analysis.total_potential_savings * months,
            'monthly_savings': analysis.total_potential_savings,
            'payback_period_months': self._calculate_payback_period(analysis),
            'year_1_savings': analysis.total_potential_savings * 12,
            'year_2_savings': analysis.total_potential_savings * 24,
            'year_3_savings': analysis.total_potential_savings * 36
        }
    
    def _calculate_payback_period(self, 
                                 analysis: CostImpactAnalysis) -> float:
        """
        Calculate payback period.
        """
        if analysis.total_potential_savings <= 0:
            return float('inf')
        
        # Estimate initial investment (rough)
        investment = analysis.total_current_cost * 0.5  # 50% of monthly cost
        return investment / analysis.total_potential_savings
    
    def get_impact_per_category(self, 
                               resources: List[HouseholdResource]) -> Dict[str, Dict[str, Any]]:
        """
        Get impact per category.
        
        Args:
            resources: List of resources
        
        Returns:
            Dict: Impact per category
        """
        impact_per_category = {}
        
        for resource in resources:
            key = resource.resource_type.value
            
            if key not in impact_per_category:
                impact_per_category[key] = {
                    'carbon': 0.0,
                    'water': 0.0,
                    'cost': 0.0,
                    'usage': 0.0
                }
            
            # Carbon impact
            emission_factor = self.emission_factors.get(key, 0)
            impact_per_category[key]['carbon'] += resource.current_usage * emission_factor
            
            # Water impact
            if key == 'water':
                impact_per_category[key]['water'] += resource.current_usage
            
            # Cost
            cost_rates = self.cost_rates.get(key, {})
            cost_per_unit = cost_rates.get('per_' + cost_rates.get('unit', 'kwh'), 0)
            impact_per_category[key]['cost'] += resource.current_usage * cost_per_unit
            
            # Usage
            impact_per_category[key]['usage'] += resource.current_usage
        
        # Add weights
        for key in impact_per_category:
            impact_per_category[key]['weight'] = self.impact_weights.get(key, 0)
        
        return impact_per_category