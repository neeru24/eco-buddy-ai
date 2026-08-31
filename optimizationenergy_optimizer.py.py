"""
Smart Household Resource Optimization Engine - Energy Optimizer
Optimizes household energy consumption.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    EnergyOptimization, HouseholdResource, ResourceType,
    OptimizationCategory, RecommendationPriority
)

logger = logging.getLogger(__name__)


class EnergyOptimizer:
    """
    Analyzes and optimizes household energy consumption.
    """
    
    def __init__(self):
        """Initialize the energy optimizer."""
        self.appliance_benchmarks = self._initialize_appliance_benchmarks()
        self.efficiency_measures = self._initialize_efficiency_measures()
        self.peak_hours = {'morning': (6, 9), 'evening': (17, 21)}
        logger.info("Energy Optimizer initialized")
    
    def _initialize_appliance_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize appliance energy consumption benchmarks.
        """
        return {
            'refrigerator': {
                'avg_kwh_monthly': 50.0,
                'efficient_kwh_monthly': 30.0,
                'inefficient_kwh_monthly': 80.0,
                'lifetime_years': 12,
                'replacement_cost': 800.0,
                'common_issues': ['door seals', 'temperature setting', 'coils']
            },
            'air_conditioner': {
                'avg_kwh_monthly': 100.0,
                'efficient_kwh_monthly': 60.0,
                'inefficient_kwh_monthly': 150.0,
                'lifetime_years': 10,
                'replacement_cost': 1500.0,
                'common_issues': ['filters', 'refrigerant', 'thermostat']
            },
            'heater': {
                'avg_kwh_monthly': 80.0,
                'efficient_kwh_monthly': 50.0,
                'inefficient_kwh_monthly': 120.0,
                'lifetime_years': 12,
                'replacement_cost': 1200.0,
                'common_issues': ['insulation', 'thermostat', 'filters']
            },
            'water_heater': {
                'avg_kwh_monthly': 40.0,
                'efficient_kwh_monthly': 25.0,
                'inefficient_kwh_monthly': 60.0,
                'lifetime_years': 10,
                'replacement_cost': 600.0,
                'common_issues': ['insulation', 'temperature', 'leaks']
            },
            'washing_machine': {
                'avg_kwh_monthly': 30.0,
                'efficient_kwh_monthly': 18.0,
                'inefficient_kwh_monthly': 45.0,
                'lifetime_years': 10,
                'replacement_cost': 500.0,
                'common_issues': ['water temperature', 'load size']
            },
            'dryer': {
                'avg_kwh_monthly': 35.0,
                'efficient_kwh_monthly': 20.0,
                'inefficient_kwh_monthly': 55.0,
                'lifetime_years': 10,
                'replacement_cost': 600.0,
                'common_issues': ['lint filter', 'overloading']
            },
            'dishwasher': {
                'avg_kwh_monthly': 25.0,
                'efficient_kwh_monthly': 15.0,
                'inefficient_kwh_monthly': 40.0,
                'lifetime_years': 10,
                'replacement_cost': 500.0,
                'common_issues': ['load size', 'drying cycle']
            },
            'television': {
                'avg_kwh_monthly': 15.0,
                'efficient_kwh_monthly': 8.0,
                'inefficient_kwh_monthly': 25.0,
                'lifetime_years': 8,
                'replacement_cost': 400.0,
                'common_issues': ['brightness', 'standby']
            },
            'computer': {
                'avg_kwh_monthly': 20.0,
                'efficient_kwh_monthly': 10.0,
                'inefficient_kwh_monthly': 35.0,
                'lifetime_years': 5,
                'replacement_cost': 600.0,
                'common_issues': ['sleep mode', 'peripherals']
            },
            'lighting': {
                'avg_kwh_monthly': 20.0,
                'efficient_kwh_monthly': 5.0,
                'inefficient_kwh_monthly': 40.0,
                'lifetime_years': 5,
                'replacement_cost': 100.0,
                'common_issues': ['bulb type', 'unused lights']
            },
            'other': {
                'avg_kwh_monthly': 50.0,
                'efficient_kwh_monthly': 30.0,
                'inefficient_kwh_monthly': 80.0,
                'lifetime_years': 8,
                'replacement_cost': 300.0,
                'common_issues': ['phantom loads', 'old appliances']
            }
        }
    
    def _initialize_efficiency_measures(self) -> List[Dict[str, Any]]:
        """
        Initialize energy efficiency measures.
        """
        return [
            {
                'measure': 'Switch to LED lighting',
                'savings_percentage': 75,
                'cost': 100,
                'effort': 'low',
                'payback_months': 3,
                'lifetime_years': 10,
                'applicable_to': ['lighting']
            },
            {
                'measure': 'Install smart thermostat',
                'savings_percentage': 20,
                'cost': 250,
                'effort': 'medium',
                'payback_months': 12,
                'lifetime_years': 10,
                'applicable_to': ['heater', 'air_conditioner']
            },
            {
                'measure': 'Upgrade to Energy Star appliances',
                'savings_percentage': 30,
                'cost': 1000,
                'effort': 'high',
                'payback_months': 24,
                'lifetime_years': 15,
                'applicable_to': ['refrigerator', 'washing_machine', 'dishwasher', 'dryer']
            },
            {
                'measure': 'Add insulation',
                'savings_percentage': 25,
                'cost': 800,
                'effort': 'high',
                'payback_months': 36,
                'lifetime_years': 20,
                'applicable_to': ['heater', 'air_conditioner']
            },
            {
                'measure': 'Install solar panels',
                'savings_percentage': 50,
                'cost': 5000,
                'effort': 'high',
                'payback_months': 60,
                'lifetime_years': 25,
                'applicable_to': ['all']
            },
            {
                'measure': 'Use smart power strips',
                'savings_percentage': 10,
                'cost': 50,
                'effort': 'low',
                'payback_months': 6,
                'lifetime_years': 5,
                'applicable_to': ['television', 'computer', 'other']
            },
            {
                'measure': 'Seal windows and doors',
                'savings_percentage': 15,
                'cost': 200,
                'effort': 'medium',
                'payback_months': 12,
                'lifetime_years': 10,
                'applicable_to': ['heater', 'air_conditioner']
            },
            {
                'measure': 'Use energy monitoring system',
                'savings_percentage': 15,
                'cost': 150,
                'effort': 'medium',
                'payback_months': 8,
                'lifetime_years': 5,
                'applicable_to': ['all']
            },
            {
                'measure': 'Reduce standby power usage',
                'savings_percentage': 8,
                'cost': 20,
                'effort': 'low',
                'payback_months': 2,
                'lifetime_years': 3,
                'applicable_to': ['television', 'computer', 'other']
            },
            {
                'measure': 'Install programmable timer',
                'savings_percentage': 12,
                'cost': 30,
                'effort': 'low',
                'payback_months': 4,
                'lifetime_years': 5,
                'applicable_to': ['heater', 'air_conditioner', 'water_heater']
            }
        ]
    
    def analyze_energy_consumption(self, 
                                  resources: List[HouseholdResource],
                                  household_size: int) -> EnergyOptimization:
        """
        Analyze household energy consumption.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            EnergyOptimization: Energy optimization analysis
        """
        optimization = EnergyOptimization(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Get energy resources
        energy_resources = [r for r in resources if r.resource_type == ResourceType.ENERGY]
        
        if not energy_resources:
            logger.warning("No energy resources found")
            return optimization
        
        # Calculate totals
        optimization.total_consumption = sum(r.current_usage for r in energy_resources)
        optimization.baseline_consumption = sum(r.baseline_usage for r in energy_resources)
        optimization.consumption_difference = (
            optimization.total_consumption - optimization.baseline_consumption
        )
        optimization.consumption_change_percentage = (
            (optimization.consumption_difference / (optimization.baseline_consumption + 0.001)) * 100
        )
        
        # Appliance breakdown
        optimization.appliance_consumption = {
            r.name: r.current_usage for r in energy_resources
        }
        optimization.appliance_efficiency = {
            r.name: r.calculate_efficiency_score() for r in energy_resources
        }
        
        # Detect high consumption areas
        optimization.high_consumption_areas = self._detect_high_consumption(energy_resources)
        
        # Detect peak usage times
        optimization.peak_usage_times = self._detect_peak_times(energy_resources)
        
        # Find efficiency opportunities
        optimization.efficiency_opportunities = self._find_efficiency_opportunities(energy_resources)
        
        # Generate reduction scenarios
        optimization.reduction_scenarios = self._generate_reduction_scenarios(energy_resources)
        
        # Calculate savings estimates
        optimization.estimated_energy_savings = self._calculate_energy_savings(energy_resources)
        optimization.estimated_cost_savings = self._calculate_cost_savings(energy_resources)
        optimization.estimated_carbon_savings = self._calculate_carbon_savings(energy_resources)
        
        # Calculate implementation costs
        optimization.estimated_implementation_cost = self._calculate_implementation_cost(energy_resources)
        optimization.payback_period_months = self._calculate_payback_period(
            optimization.estimated_implementation_cost,
            optimization.estimated_cost_savings
        )
        
        # Generate implementation phases
        optimization.implementation_phases = self._generate_implementation_phases(
            energy_resources, optimization.efficiency_opportunities
        )
        
        # Generate recommendations
        optimization.recommendations = self._generate_recommendations(energy_resources)
        optimization.priority_recommendations = self._prioritize_recommendations(
            optimization.recommendations
        )
        
        return optimization
    
    def _detect_high_consumption(self, 
                                resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Detect high energy consumption areas.
        """
        high_areas = []
        
        for resource in resources:
            benchmark = self.appliance_benchmarks.get(resource.name.lower(), {})
            avg_usage = benchmark.get('avg_kwh_monthly', 20.0)
            high_threshold = avg_usage * 1.5
            
            if resource.current_usage > high_threshold:
                high_areas.append({
                    'appliance': resource.name,
                    'current_usage': resource.current_usage,
                    'benchmark': avg_usage,
                    'excess': resource.current_usage - avg_usage,
                    'excess_percentage': ((resource.current_usage - avg_usage) / (avg_usage + 0.001)) * 100,
                    'recommendation': self._get_high_consumption_recommendation(resource),
                    'common_issues': benchmark.get('common_issues', [])
                })
        
        return sorted(high_areas, key=lambda x: x['excess'], reverse=True)
    
    def _get_high_consumption_recommendation(self, 
                                            resource: HouseholdResource) -> str:
        """
        Get recommendation for high consumption appliance.
        """
        name = resource.name.lower()
        
        if 'refrigerator' in name:
            return "Check door seals, clean coils, set temperature to 4°C"
        elif 'air' in name and ('conditioner' in name or 'ac' in name):
            return "Service AC, clean filters, set temperature to 24°C"
        elif 'heater' in name:
            return "Insulate, use timer, set temperature to 20°C"
        elif 'water' in name and 'heater' in name:
            return "Insulate tank, set temperature to 60°C, fix leaks"
        elif 'washing' in name:
            return "Use cold water, full loads, eco mode"
        elif 'dryer' in name:
            return "Air dry when possible, clean lint filter"
        elif 'dishwasher' in name:
            return "Full loads, eco mode, air dry"
        elif 'lighting' in name:
            return "Switch to LED bulbs, use natural light"
        elif 'television' in name:
            return "Reduce brightness, use sleep timer"
        else:
            return "Consider energy-efficient upgrade"
    
    def _detect_peak_times(self, 
                          resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Detect peak usage times.
        """
        peaks = []
        
        for resource in resources:
            if resource.historical_usage:
                usage_by_hour = {}
                
                for entry in resource.historical_usage:
                    if 'hour' in entry and 'value' in entry:
                        hour = entry['hour']
                        value = entry['value']
                        usage_by_hour[hour] = usage_by_hour.get(hour, 0) + value
                
                if usage_by_hour:
                    sorted_hours = sorted(usage_by_hour.items(), key=lambda x: x[1], reverse=True)
                    peak_hours = sorted_hours[:3]
                    
                    peaks.append({
                        'resource': resource.name,
                        'peak_hours': [{'hour': h, 'usage': v} for h, v in peak_hours],
                        'recommendation': f"Shift usage away from peak hours"
                    })
        
        return peaks
    
    def _find_efficiency_opportunities(self, 
                                      resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find energy efficiency opportunities.
        """
        opportunities = []
        
        for resource in resources:
            benchmark = self.appliance_benchmarks.get(resource.name.lower(), {})
            efficient_usage = benchmark.get('efficient_kwh_monthly', 0)
            
            if efficient_usage > 0 and resource.current_usage > efficient_usage:
                savings = resource.current_usage - efficient_usage
                
                opportunities.append({
                    'appliance': resource.name,
                    'current_usage': resource.current_usage,
                    'target_usage': efficient_usage,
                    'potential_savings': savings,
                    'savings_percentage': (savings / (resource.current_usage + 0.001)) * 100,
                    'measure': self._get_efficiency_measure(resource),
                    'estimated_cost': self._estimate_measure_cost(resource),
                    'payback_months': self._calculate_measure_payback(resource, savings)
                })
        
        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)
    
    def _get_efficiency_measure(self, resource: HouseholdResource) -> str:
        """
        Get efficiency measure for an appliance.
        """
        name = resource.name.lower()
        
        for measure in self.efficiency_measures:
            if 'lighting' in name and 'LED' in measure['measure']:
                return measure['measure']
            elif 'thermostat' in name and 'thermostat' in measure['measure']:
                return measure['measure']
            elif 'appliance' in measure['measure'] and any(app in name for app in ['refrigerator', 'washing', 'dishwasher', 'dryer']):
                return measure['measure']
            elif 'insulation' in measure['measure'] and 'heater' in name:
                return measure['measure']
        
        return "Upgrade to energy-efficient model"
    
    def _estimate_measure_cost(self, resource: HouseholdResource) -> float:
        """
        Estimate cost of efficiency measure.
        """
        name = resource.name.lower()
        
        if 'lighting' in name:
            return 100.0
        elif 'thermostat' in name:
            return 250.0
        elif 'refrigerator' in name or 'washing' in name or 'dishwasher' in name or 'dryer' in name:
            return 800.0
        elif 'heater' in name and 'water' in name:
            return 600.0
        elif 'heater' in name:
            return 1200.0
        elif 'air' in name:
            return 1500.0
        else:
            return 200.0
    
    def _calculate_measure_payback(self, resource: HouseholdResource, savings: float) -> int:
        """
        Calculate payback period for a measure.
        """
        cost = self._estimate_measure_cost(resource)
        monthly_savings = savings * 0.15  # Assuming $0.15 per kWh
        
        if monthly_savings > 0:
            return int(cost / monthly_savings)
        return 12
    
    def _generate_reduction_scenarios(self, 
                                     resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate energy reduction scenarios.
        """
        scenarios = []
        total_current = sum(r.current_usage for r in resources)
        
        # Scenario 1: 10% reduction
        scenarios.append({
            'name': '10% Reduction',
            'reduction_percentage': 10,
            'reduction_amount': total_current * 0.1,
            'target_usage': total_current * 0.9,
            'effort': 'low',
            'implementation': 'Behavioral changes, LED lighting'
        })
        
        # Scenario 2: 25% reduction
        scenarios.append({
            'name': '25% Reduction',
            'reduction_percentage': 25,
            'reduction_amount': total_current * 0.25,
            'target_usage': total_current * 0.75,
            'effort': 'medium',
            'implementation': 'Appliance upgrades, smart thermostats'
        })
        
        # Scenario 3: 50% reduction
        scenarios.append({
            'name': '50% Reduction',
            'reduction_percentage': 50,
            'reduction_amount': total_current * 0.5,
            'target_usage': total_current * 0.5,
            'effort': 'high',
            'implementation': 'Solar panels, major appliance replacement'
        })
        
        return scenarios
    
    def _calculate_energy_savings(self, 
                                 resources: List[HouseholdResource]) -> float:
        """
        Calculate potential energy savings.
        """
        total_savings = 0.0
        
        for resource in resources:
            benchmark = self.appliance_benchmarks.get(resource.name.lower(), {})
            efficient_usage = benchmark.get('efficient_kwh_monthly', 0)
            
            if efficient_usage > 0 and resource.current_usage > efficient_usage:
                total_savings += resource.current_usage - efficient_usage
            else:
                total_savings += resource.current_usage * 0.1
        
        return total_savings
    
    def _calculate_cost_savings(self, 
                               resources: List[HouseholdResource]) -> float:
        """
        Calculate potential cost savings.
        """
        energy_savings = self._calculate_energy_savings(resources)
        return energy_savings * 0.15
    
    def _calculate_carbon_savings(self, 
                                 resources: List[HouseholdResource]) -> float:
        """
        Calculate potential carbon savings.
        """
        energy_savings = self._calculate_energy_savings(resources)
        return energy_savings * 0.5
    
    def _calculate_implementation_cost(self, 
                                      resources: List[HouseholdResource]) -> float:
        """
        Calculate implementation cost.
        """
        total_cost = 0.0
        for resource in resources:
            if resource.calculate_optimization_potential() > 20:
                total_cost += self._estimate_measure_cost(resource)
        return total_cost
    
    def _calculate_payback_period(self, implementation_cost: float, monthly_savings: float) -> float:
        """
        Calculate payback period.
        """
        if monthly_savings > 0:
            return implementation_cost / monthly_savings
        return float('inf')
    
    def _generate_implementation_phases(self, 
                                       resources: List[HouseholdResource],
                                       opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate implementation phases.
        """
        phases = []
        
        # Phase 1: Quick wins (low effort, high impact)
        quick_wins = [o for o in opportunities if o.get('payback_months', 99) < 6]
        if quick_wins:
            phases.append({
                'phase': 1,
                'name': 'Quick Wins',
                'description': 'Implement low-effort, high-impact measures',
                'items': [o['appliance'] for o in quick_wins[:3]],
                'estimated_cost': sum(o.get('estimated_cost', 0) for o in quick_wins[:3]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in quick_wins[:3])
            })
        
        # Phase 2: Medium impact
        medium = [o for o in opportunities if 6 <= o.get('payback_months', 99) <= 18]
        if medium:
            phases.append({
                'phase': 2,
                'name': 'Medium Impact',
                'description': 'Implement moderate-effort measures',
                'items': [o['appliance'] for o in medium[:3]],
                'estimated_cost': sum(o.get('estimated_cost', 0) for o in medium[:3]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in medium[:3])
            })
        
        # Phase 3: Major upgrades
        major = [o for o in opportunities if o.get('payback_months', 99) > 18]
        if major:
            phases.append({
                'phase': 3,
                'name': 'Major Upgrades',
                'description': 'Implement high-effort, high-impact measures',
                'items': [o['appliance'] for o in major[:2]],
                'estimated_cost': sum(o.get('estimated_cost', 0) for o in major[:2]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in major[:2])
            })
        
        return phases
    
    def _generate_recommendations(self, 
                                 resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate energy optimization recommendations.
        """
        recommendations = []
        
        for resource in resources:
            efficiency = resource.calculate_efficiency_score()
            if efficiency < 60:
                recommendations.append({
                    'resource': resource.name,
                    'type': 'energy',
                    'current_efficiency': efficiency,
                    'grade': resource.get_efficiency_grade().value,
                    'recommendation': self._get_efficiency_recommendation(resource),
                    'estimated_savings': resource.current_usage * 0.2,
                    'estimated_cost': self._estimate_measure_cost(resource),
                    'payback_months': self._calculate_measure_payback(resource, resource.current_usage * 0.2),
                    'priority': self._get_priority(efficiency),
                    'effort': 'medium'
                })
        
        # Add general recommendations
        general_recs = [
            {
                'resource': 'General',
                'type': 'energy',
                'current_efficiency': 50,
                'grade': 'C',
                'recommendation': 'Install smart thermostat for automated temperature control',
                'estimated_savings': 0,
                'estimated_cost': 250,
                'payback_months': 12,
                'priority': 'high',
                'effort': 'medium'
            },
            {
                'resource': 'General',
                'type': 'energy',
                'current_efficiency': 50,
                'grade': 'C',
                'recommendation': 'Replace all bulbs with LED lighting',
                'estimated_savings': 0,
                'estimated_cost': 100,
                'payback_months': 3,
                'priority': 'critical',
                'effort': 'low'
            },
            {
                'resource': 'General',
                'type': 'energy',
                'current_efficiency': 50,
                'grade': 'C',
                'recommendation': 'Use power strips to eliminate phantom loads',
                'estimated_savings': 0,
                'estimated_cost': 50,
                'payback_months': 6,
                'priority': 'high',
                'effort': 'low'
            }
        ]
        
        recommendations.extend(general_recs)
        
        return sorted(recommendations, key=lambda x: x.get('estimated_savings', 0), reverse=True)
    
    def _get_efficiency_recommendation(self, resource: HouseholdResource) -> str:
        """
        Get efficiency recommendation for a resource.
        """
        name = resource.name.lower()
        
        if 'refrigerator' in name:
            return "Clean coils and check door seals"
        elif 'air' in name or 'ac' in name:
            return "Service AC and clean filters regularly"
        elif 'heater' in name and 'water' not in name:
            return "Insulate home and use programmable thermostat"
        elif 'water' in name and 'heater' in name:
            return "Insulate water heater and lower temperature"
        elif 'washing' in name:
            return "Use cold water and full loads"
        elif 'dryer' in name:
            return "Clean lint filter and air dry when possible"
        elif 'lighting' in name:
            return "Switch to LED bulbs"
        else:
            return "Consider upgrading to energy-efficient model"
    
    def _get_priority(self, efficiency: float) -> str:
        """
        Get priority based on efficiency.
        """
        if efficiency < 30:
            return 'critical'
        elif efficiency < 50:
            return 'high'
        elif efficiency < 70:
            return 'medium'
        else:
            return 'low'
    
    def _prioritize_recommendations(self, 
                                   recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize recommendations.
        """
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return sorted(recommendations, key=lambda x: priority_order.get(x.get('priority', 'medium'), 2))
    
    def get_energy_score(self, 
                        resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Get overall energy score.
        
        Args:
            resources: List of energy resources
        
        Returns:
            Dict: Energy score
        """
        if not resources:
            return {'score': 0, 'grade': 'F'}
        
        scores = [r.calculate_efficiency_score() for r in resources]
        avg_score = statistics.mean(scores)
        grade = self._get_grade(avg_score)
        
        return {
            'score': avg_score,
            'grade': grade,
            'category_scores': {r.name: r.efficiency_score for r in resources},
            'total_consumption': sum(r.current_usage for r in resources),
            'total_baseline': sum(r.baseline_usage for r in resources),
            'optimization_potential': sum(r.calculate_optimization_potential() for r in resources) / len(resources)
        }
    
    def _get_grade(self, score: float) -> str:
        """Get grade from score."""
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
    
    def get_energy_savings_potential(self, 
                                    resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Calculate energy savings potential.
        
        Args:
            resources: List of resources
        
        Returns:
            Dict: Savings potential
        """
        current_total = sum(r.current_usage for r in resources)
        
        potential_savings = 0.0
        measures_applied = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.appliance_benchmarks.get(name, {})
            efficient_usage = benchmark.get('efficient_kwh_monthly', 0)
            
            if efficient_usage > 0 and resource.current_usage > efficient_usage:
                savings = resource.current_usage - efficient_usage
                potential_savings += savings
                measures_applied.append({
                    'appliance': resource.name,
                    'savings': savings,
                    'measure': self._get_efficiency_measure(resource),
                    'cost': self._estimate_measure_cost(resource)
                })
        
        return {
            'current_monthly_usage': current_total,
            'potential_monthly_savings': potential_savings,
            'potential_savings_percentage': (potential_savings / (current_total + 0.001)) * 100,
            'annual_savings_kwh': potential_savings * 12,
            'annual_cost_savings': potential_savings * 12 * 0.15,
            'annual_carbon_savings_kg': potential_savings * 12 * 0.5,
            'measures': measures_applied,
            'implementation_cost': sum(m['cost'] for m in measures_applied),
            'payback_years': (sum(m['cost'] for m in measures_applied) / (potential_savings * 12 * 0.15)) if potential_savings > 0 else float('inf')
        }