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
                    'transport_shift_percentage': 0
                }
            },
            {
                'name': 'Reduce Water 30%',
                'description': 'Reduce water consumption by 30% through conservation',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 30,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 0
                }
            },
            {
                'name': 'Reduce Waste 40%',
                'description': 'Reduce waste by 40% through recycling and composting',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 40,
                    'transport_shift_percentage': 0
                }
            },
            {
                'name': 'Sustainable Transport Shift',
                'description': 'Shift 30% of car trips to public transit or cycling',
                'params': {
                    'energy_reduction_percentage': 0,
                    'water_reduction_percentage': 0,
                    'waste_reduction_percentage': 0,
                    'transport_shift_percentage': 30
                }
            },
            {
                'name': 'Comprehensive Sustainability',
                'description': 'Apply all optimizations together',
                'params': {
                    'energy_reduction_percentage': 20,
                    'water_reduction_percentage': 30,
                    'waste_reduction_percentage': 40,
                    'transport_shift_percentage': 30
                }
            }
        ]
    
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
            transport_shift_percentage=scenario_params.get('transport_shift_percentage', 0)
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
        scenario.improvement_percentage = ((total_original - total_projected) / total_original) * 100 if total_original > 0 else 0
        
        # Calculate efficiency gain
        scenario.efficiency_gain = self._calculate_efficiency_gain(
            resources, projected_usage
        )
        
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
            'transportation': 0.30
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
            'transportation': 0.18
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
        
        return {
            'best_energy': {'name': best_energy.name, 'savings': best_energy.projected_energy_savings},
            'best_water': {'name': best_water.name, 'savings': best_water.projected_water_savings},
            'best_waste': {'name': best_waste.name, 'reduction': best_waste.projected_waste_reduction},
            'best_cost': {'name': best_cost.name, 'savings': best_cost.projected_cost_savings},
            'best_carbon': {'name': best_carbon.name, 'reduction': best_carbon.projected_carbon_reduction},
            'best_overall': {'name': best_overall.name, 'improvement': best_overall.improvement_percentage},
            'scenario_comparison': [
                {
                    'name': s.name,
                    'energy_savings': s.projected_energy_savings,
                    'water_savings': s.projected_water_savings,
                    'waste_reduction': s.projected_waste_reduction,
                    'cost_savings': s.projected_cost_savings,
                    'carbon_reduction': s.projected_carbon_reduction,
                    'improvement': s.improvement_percentage,
                    'efficiency_gain': s.efficiency_gain
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
                max_reduction = resource.current_usage * 0.3  # 30% max
                effort = 'medium'
            elif key == 'water':
                max_reduction = resource.current_usage * 0.4  # 40% max
                effort = 'medium'
            elif key == 'waste':
                max_reduction = resource.current_usage * 0.5  # 50% max
                effort = 'low'
            else:
                max_reduction = resource.current_usage * 0.2
                effort = 'medium'
            
            measures.append({
                'resource': resource.name,
                'type': key,
                'current_usage': resource.current_usage,
                'max_reduction': max_reduction,
                'effort': effort,
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
                    'reduction_percentage': (reduction / measure['current_usage']) * 100,
                    'effort': measure['effort'],
                    'priority': measure['priority'],
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
            'transportation': 'Use public transit, carpool, bike more'
        }
        return actions.get(resource_type, 'Optimize consumption')