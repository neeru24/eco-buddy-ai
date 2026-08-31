"""
Smart Household Resource Optimization Engine - What-If Simulator
Simulates different optimization scenarios.
"""

import logging
import copy
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    WhatIfScenario, HouseholdResource, ResourceType,
    CostImpactAnalysis
)

logger = logging.getLogger(__name__)


class WhatIfSimulator:
    """
    Simulates different optimization scenarios.
    """
    
    def __init__(self):
        """Initialize the what-if simulator."""
        self.scenario_templates = self._initialize_scenario_templates()
        self.simulation_models = self._initialize_simulation_models()
        logger.info("What-If Simulator initialized")
    
    def _initialize_scenario_templates(self) -> List[Dict[str, Any]]:
        """
        Initialize scenario templates.
        """
        return [
            {
                'name': 'Reduce Energy 20%',
                'description': 'Reduce energy consumption by 20% through efficiency measures',
                'params': {
                    'energy_reduction_percentage': 20,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 0,
                    'food_waste_reduction': 0,
                    'shopping_reduction': 0
                }
            },
            {
                'name': 'Reduce Water 30%',
                'description': 'Reduce water consumption by 30% through conservation',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 30,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 0,
                    'food_waste_reduction': 0,
                    'shopping_reduction': 0
                }
            },
            {
                'name': 'Reduce Waste 40%',
                'description': 'Reduce waste by 40% through recycling and composting',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 40,
                    'transport_shift_percentage': 0,
                    'food_waste_reduction': 0,
                    'shopping_reduction': 0
                }
            },
            {
                'name': 'Sustainable Transport Shift',
                'description': 'Shift 30% of car trips to public transit or cycling',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 30,
                    'food_waste_reduction': 0,
                    'shopping_reduction': 0
                }
            },
            {
                'name': 'Reduce Food Waste 50%',
                'description': 'Reduce food waste by 50% through meal planning and composting',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 0,
                    'food_waste_reduction': 50,
                    'shopping_reduction': 0
                }
            },
            {
                'name': 'Sustainable Shopping',
                'description': 'Shift to sustainable shopping practices',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 0,
                    'food_waste_reduction': 0,
                    'shopping_reduction': 20
                }
            },
            {
                'name': 'Comprehensive Sustainability',
                'description': 'Apply all optimizations together',
                'params': {
                    'energy_reduction_percentage': 20,
                    'water_reduction_percentage': 30,
                    'waste_reduction_percentage': 40,
                    'transport_shift_percentage': 30,
                    'food_waste_reduction': 50,
                    'shopping_reduction': 20
                }
            }
        ]
    
    def _initialize_simulation_models(self) -> Dict[str, Any]:
        """
        Initialize simulation models.
        """
        return {
            'linear': {
                'type': 'linear',
                'description': 'Linear reduction model'
            },
            'exponential': {
                'type': 'exponential',
                'description': 'Exponential improvement model'
            },
            's_curve': {
                'type': 's_curve',
                'description': 'S-curve adoption model'
            }
        }
    
    def simulate_scenario(self, 
                         resources: List[HouseholdResource],
                         scenario_params: Dict[str, Any]) -> WhatIfScenario:
        """
        Simulate a what-if scenario.
        
        Args:
            resources: Current resources
            scenario_params: Scenario parameters
        
        Returns:
            WhatIfScenario: Simulation results
        """
        # Create scenario
        scenario = WhatIfScenario(
            household_id=resources[0].household_id if resources else "",
            name=scenario_params.get('name', 'Custom Scenario'),
            description=scenario_params.get('description', ''),
            energy_reduction_percentage=scenario_params.get('energy_reduction_percentage', 0),
            water_reduction_percentage=scenario_params.get('water_reduction_percentage', 0),
            waste_reduction_percentage=scenario_params.get('waste_reduction_percentage', 0),
            transport_shift_percentage=scenario_params.get('transport_shift_percentage', 0),
            food_waste_reduction=scenario_params.get('food_waste_reduction', 0),
            shopping_reduction=scenario_params.get('shopping_reduction', 0)
        )
        
        # Apply reductions
        projected_usage = self._apply_reductions(resources, scenario)
        
        # Calculate projections
        scenario.projected_energy_savings = self._calculate_projected_savings(
            resources, projected_usage, 'energy'
        )
        scenario.projected_water_savings = self._calculate_projected_savings(
            resources, projected_usage, 'water'
        )
        scenario.projected_waste_reduction = self._calculate_projected_savings(
            resources, projected_usage, 'waste'
        )
        
        # Calculate cost and carbon savings
        scenario.projected_cost_savings = self._calculate_cost_savings(
            resources, projected_usage
        )
        scenario.projected_carbon_reduction = self._calculate_carbon_savings(
            resources, projected_usage
        )
        
        # Calculate improvement percentage
        total_original = sum(r.current_usage for r in resources)
        total_projected = sum(r.current_usage for r in projected_usage)
        scenario.improvement_percentage = ((total_original - total_projected) / (total_original + 0.001)) * 100
        
        # Calculate efficiency gain
        scenario.efficiency_gain = self._calculate_efficiency_gain(
            resources, projected_usage
        )
        
        # Calculate implementation difficulty
        scenario.implementation_difficulty = self._calculate_implementation_difficulty(scenario)
        scenario.implementation_cost = self._calculate_implementation_cost(scenario, resources)
        scenario.time_to_implement_days = self._calculate_time_to_implement(scenario)
        
        return scenario
    
    def _apply_reductions(self, 
                         resources: List[HouseholdResource],
                         scenario: WhatIfScenario) -> List[HouseholdResource]:
        """
        Apply reductions to resources.
        """
        projected = copy.deepcopy(resources)
        
        for resource in projected:
            key = resource.resource_type.value
            
            if key == 'energy':
                reduction = scenario.energy_reduction_percentage
            elif key == 'water':
                reduction = scenario.water_reduction_percentage
            elif key == 'waste':
                reduction = scenario.waste_reduction_percentage
            elif key == 'transportation':
                reduction = scenario.transport_shift_percentage
            elif key == 'food':
                reduction = scenario.food_waste_reduction
            elif key == 'shopping':
                reduction = scenario.shopping_reduction
            else:
                reduction = 0
            
            if reduction > 0:
                resource.current_usage = resource.current_usage * (1 - reduction / 100)
                resource.optimization_potential = max(0, resource.optimization_potential - reduction)
        
        return projected
    
    def _calculate_projected_savings(self, 
                                    original: List[HouseholdResource],
                                    projected: List[HouseholdResource],
                                    resource_type: str) -> float:
        """
        Calculate projected savings for a resource type.
        """
        original_total = sum(r.current_usage for r in original if r.resource_type.value == resource_type)
        projected_total = sum(r.current_usage for r in projected if r.resource_type.value == resource_type)
        
        return max(0, original_total - projected_total)
    
    def _calculate_cost_savings(self, 
                               original: List[HouseholdResource],
                               projected: List[HouseholdResource]) -> float:
        """
        Calculate cost savings.
        """
        cost_rates = {
            'energy': 0.15,
            'water': 0.005,
            'waste': 0.05,
            'food': 5.0,
            'transportation': 0.30,
            'shopping': 25.0
        }
        
        total_savings = 0.0
        
        for o, p in zip(original, projected):
            key = o.resource_type.value
            rate = cost_rates.get(key, 0)
            savings = (o.current_usage - p.current_usage) * rate
            total_savings += max(0, savings)
        
        return total_savings
    
    def _calculate_carbon_savings(self, 
                                 original: List[HouseholdResource],
                                 projected: List[HouseholdResource]) -> float:
        """
        Calculate carbon savings.
        """
        emission_factors = {
            'energy': 0.5,
            'water': 0.001,
            'waste': 0.2,
            'food': 0.5,
            'transportation': 0.18,
            'shopping': 2.0
        }
        
        total_savings = 0.0
        
        for o, p in zip(original, projected):
            key = o.resource_type.value
            factor = emission_factors.get(key, 0)
            savings = (o.current_usage - p.current_usage) * factor
            total_savings += max(0, savings)
        
        return total_savings
    
    def _calculate_efficiency_gain(self, 
                                  original: List[HouseholdResource],
                                  projected: List[HouseholdResource]) -> float:
        """
        Calculate efficiency gain.
        """
        original_scores = [r.calculate_efficiency_score() for r in original]
        projected_scores = [r.calculate_efficiency_score() for r in projected]
        
        if original_scores:
            original_avg = statistics.mean(original_scores)
            projected_avg = statistics.mean(projected_scores)
            return projected_avg - original_avg
        
        return 0.0
    
    def _calculate_implementation_difficulty(self, scenario: WhatIfScenario) -> str:
        """
        Calculate implementation difficulty.
        """
        total_reduction = (
            scenario.energy_reduction_percentage +
            scenario.water_reduction_percentage +
            scenario.waste_reduction_percentage +
            scenario.transport_shift_percentage +
            scenario.food_waste_reduction +
            scenario.shopping_reduction
        )
        
        if total_reduction > 100:
            return "hard"
        elif total_reduction > 60:
            return "medium"
        else:
            return "easy"
    
    def _calculate_implementation_cost(self, 
                                      scenario: WhatIfScenario,
                                      resources: List[HouseholdResource]) -> float:
        """
        Calculate implementation cost.
        """
        base_cost = 0.0
        
        if scenario.energy_reduction_percentage > 0:
            base_cost += 200 * (scenario.energy_reduction_percentage / 20)
        if scenario.water_reduction_percentage > 0:
            base_cost += 100 * (scenario.water_reduction_percentage / 30)
        if scenario.waste_reduction_percentage > 0:
            base_cost += 150 * (scenario.waste_reduction_percentage / 40)
        if scenario.transport_shift_percentage > 0:
            base_cost += 50 * (scenario.transport_shift_percentage / 30)
        if scenario.food_waste_reduction > 0:
            base_cost += 80 * (scenario.food_waste_reduction / 50)
        if scenario.shopping_reduction > 0:
            base_cost += 60 * (scenario.shopping_reduction / 20)
        
        return base_cost
    
    def _calculate_time_to_implement(self, scenario: WhatIfScenario) -> int:
        """
        Calculate time to implement in days.
        """
        total_reduction = (
            scenario.energy_reduction_percentage +
            scenario.water_reduction_percentage +
            scenario.waste_reduction_percentage +
            scenario.transport_shift_percentage +
            scenario.food_waste_reduction +
            scenario.shopping_reduction
        )
        
        if total_reduction > 100:
            return 90
        elif total_reduction > 60:
            return 60
        else:
            return 30
    
    def run_multiple_scenarios(self, 
                              resources: List[HouseholdResource]) -> List[WhatIfScenario]:
        """
        Run multiple preset scenarios.
        
        Args:
            resources: Current resources
        
        Returns:
            List[WhatIfScenario]: All scenario results
        """
        results = []
        
        for template in self.scenario_templates:
            result = self.simulate_scenario(resources, template['params'])
            result.name = template['name']
            result.description = template['description']
            results.append(result)
        
        return sorted(results, key=lambda x: x.improvement_percentage, reverse=True)
    
    def compare_scenarios(self, 
                         scenarios: List[WhatIfScenario]) -> Dict[str, Any]:
        """
        Compare multiple scenarios.
        
        Args:
            scenarios: List of scenarios
        
        Returns:
            Dict: Comparison results
        """
        if not scenarios:
            return {'message': 'No scenarios to compare'}
        
        # Find best in each category
        best_energy = max(scenarios, key=lambda x: x.projected_energy_savings)
        best_water = max(scenarios, key=lambda x: x.projected_water_savings)
        best_waste = max(scenarios, key=lambda x: x.projected_waste_reduction)
        best_cost = max(scenarios, key=lambda x: x.projected_cost_savings)
        best_carbon = max(scenarios, key=lambda x: x.projected_carbon_reduction)
        best_overall = max(scenarios, key=lambda x: x.improvement_percentage)
        best_efficiency = max(scenarios, key=lambda x: x.efficiency_gain)
        
        return {
            'best_energy': {'name': best_energy.name, 'savings': best_energy.projected_energy_savings},
            'best_water': {'name': best_water.name, 'savings': best_water.projected_water_savings},
            'best_waste': {'name': best_waste.name, 'reduction': best_waste.projected_waste_reduction},
            'best_cost': {'name': best_cost.name, 'savings': best_cost.projected_cost_savings},
            'best_carbon': {'name': best_carbon.name, 'reduction': best_carbon.projected_carbon_reduction},
            'best_overall': {'name': best_overall.name, 'improvement': best_overall.improvement_percentage},
            'best_efficiency': {'name': best_efficiency.name, 'gain': best_efficiency.efficiency_gain},
            'scenario_comparison': [
                {
                    'name': s.name,
                    'energy_savings': s.projected_energy_savings,
                    'water_savings': s.projected_water_savings,
                    'waste_reduction': s.projected_waste_reduction,
                    'cost_savings': s.projected_cost_savings,
                    'carbon_reduction': s.projected_carbon_reduction,
                    'improvement': s.improvement_percentage,
                    'efficiency_gain': s.efficiency_gain,
                    'difficulty': s.implementation_difficulty,
                    'cost': s.implementation_cost,
                    'time_days': s.time_to_implement_days
                }
                for s in scenarios
            ]
        }
    
    def get_recommended_scenario(self, 
                                resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Get recommended scenario based on current resources.
        
        Args:
            resources: Current resources
        
        Returns:
            Dict: Recommended scenario
        """
        # Run all scenarios
        scenarios = self.run_multiple_scenarios(resources)
        
        if not scenarios:
            return {'message': 'No scenarios available'}
        
        # Sort by improvement percentage
        sorted_scenarios = sorted(scenarios, key=lambda x: x.improvement_percentage, reverse=True)
        best = sorted_scenarios[0]
        
        # Find the most cost-effective scenario
        cost_effective = min(scenarios, key=lambda x: x.implementation_cost / (x.improvement_percentage + 0.001))
        
        return {
            'recommended_scenario': best.name,
            'description': best.description,
            'improvement_percentage': best.improvement_percentage,
            'cost_savings': best.projected_cost_savings,
            'carbon_reduction': best.projected_carbon_reduction,
            'energy_savings': best.projected_energy_savings,
            'water_savings': best.projected_water_savings,
            'waste_reduction': best.projected_waste_reduction,
            'efficiency_gain': best.efficiency_gain,
            'implementation_cost': best.implementation_cost,
            'time_to_implement_days': best.time_to_implement_days,
            'difficulty': best.implementation_difficulty,
            'most_cost_effective': cost_effective.name,
            'all_scenarios': [
                {
                    'name': s.name,
                    'improvement': s.improvement_percentage,
                    'savings': s.projected_cost_savings,
                    'priority': idx + 1
                }
                for idx, s in enumerate(sorted_scenarios[:5])
            ]
        }
    
    def get_custom_scenario_recommendations(self, 
                                           resources: List[HouseholdResource],
                                           target_improvement: float) -> List[Dict[str, Any]]:
        """
        Get recommendations to achieve a target improvement.
        
        Args:
            resources: Current resources
            target_improvement: Target improvement percentage
        
        Returns:
            List[Dict]: Recommendations
        """
        recommendations = []
        current_total = sum(r.current_usage for r in resources)
        target_total = current_total * (1 - target_improvement / 100)
        current_savings_needed = current_total - target_total
        
        # Find best combination of measures
        measures = []
        
        for resource in resources:
            key = resource.resource_type.value
            
            # Calculate maximum reduction possible
            if key == 'energy':
                max_reduction = resource.current_usage * 0.3
                effort = 'medium'
                cost = resource.current_usage * 0.5
            elif key == 'water':
                max_reduction = resource.current_usage * 0.4
                effort = 'medium'
                cost = resource.current_usage * 0.1
            elif key == 'waste':
                max_reduction = resource.current_usage * 0.5
                effort = 'low'
                cost = resource.current_usage * 0.2
            elif key == 'food':
                max_reduction = resource.current_usage * 0.4
                effort = 'medium'
                cost = resource.current_usage * 0.3
            else:
                max_reduction = resource.current_usage * 0.2
                effort = 'medium'
                cost = resource.current_usage * 0.2
            
            measures.append({
                'resource': resource.name,
                'type': key,
                'current_usage': resource.current_usage,
                'max_reduction': max_reduction,
                'effort': effort,
                'cost': cost,
                'priority': 'high' if effort == 'low' else 'medium'
            })
        
        # Sort by effort (lowest first) and reduction potential
        measures = sorted(measures, key=lambda x: (x['effort'] == 'low', -x['max_reduction']))
        
        # Build recommendations
        for measure in measures:
            if current_savings_needed <= 0:
                break
            
            reduction = min(measure['max_reduction'], current_savings_needed)
            if reduction > 0:
                recommendations.append({
                    'resource': measure['resource'],
                    'type': measure['type'],
                    'reduction_needed': reduction,
                    'reduction_percentage': (reduction / (measure['current_usage'] + 0.001)) * 100,
                    'effort': measure['effort'],
                    'priority': measure['priority'],
                    'cost': measure['cost'] * (reduction / (measure['max_reduction'] + 0.001)),
                    'action': self._get_action_for_resource(measure['resource'], measure['type'])
                })
                current_savings_needed -= reduction
        
        return recommendations
    
    def _get_action_for_resource(self, resource_name: str, resource_type: str) -> str:
        """
        Get action for a resource.
        """
        actions = {
            'energy': 'Implement energy efficiency measures',
            'water': 'Conserve water, fix leaks, install efficient fixtures',
            'waste': 'Increase recycling, start composting, reduce packaging',
            'food': 'Meal planning, reduce food waste',
            'transportation': 'Use public transit, carpool, bike more',
            'shopping': 'Buy sustainable, reduce unnecessary purchases'
        }
        return actions.get(resource_type, 'Optimize consumption')