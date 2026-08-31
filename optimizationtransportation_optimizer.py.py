"""
Smart Household Resource Optimization Engine - Transportation Optimizer
Optimizes household transportation and mobility.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    TransportationOptimization, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class TransportationOptimizer:
    """
    Analyzes and optimizes household transportation.
    """
    
    def __init__(self):
        """Initialize the transportation optimizer."""
        self.transport_benchmarks = self._initialize_transport_benchmarks()
        self.emission_factors = self._initialize_emission_factors()
        self.alternative_modes = self._initialize_alternative_modes()
        self.cost_factors = self._initialize_cost_factors()
        logger.info("Transportation Optimizer initialized")
    
    def _initialize_transport_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize transportation benchmarks.
        """
        return {
            'car': {
                'avg_km_per_month': 1000.0,
                'avg_kg_co2_per_km': 0.18,
                'avg_cost_per_km': 0.30,
                'efficiency_improvement': 'Carpool, use public transit',
                'environmental_score': 30
            },
            'public_transit': {
                'avg_km_per_month': 500.0,
                'avg_kg_co2_per_km': 0.05,
                'avg_cost_per_km': 0.15,
                'efficiency_improvement': 'Use more often',
                'environmental_score': 70
            },
            'bicycle': {
                'avg_km_per_month': 200.0,
                'avg_kg_co2_per_km': 0.0,
                'avg_cost_per_km': 0.02,
                'efficiency_improvement': 'Use for short trips',
                'environmental_score': 95
            },
            'walking': {
                'avg_km_per_month': 100.0,
                'avg_kg_co2_per_km': 0.0,
                'avg_cost_per_km': 0.0,
                'efficiency_improvement': 'Walk more for short distances',
                'environmental_score': 100
            },
            'electric_vehicle': {
                'avg_km_per_month': 800.0,
                'avg_kg_co2_per_km': 0.05,
                'avg_cost_per_km': 0.12,
                'efficiency_improvement': 'Charge during off-peak hours',
                'environmental_score': 75
            },
            'rideshare': {
                'avg_km_per_month': 200.0,
                'avg_kg_co2_per_km': 0.15,
                'avg_cost_per_km': 0.50,
                'efficiency_improvement': 'Combine trips',
                'environmental_score': 50
            },
            'train': {
                'avg_km_per_month': 300.0,
                'avg_kg_co2_per_km': 0.04,
                'avg_cost_per_km': 0.20,
                'efficiency_improvement': 'Use for long-distance travel',
                'environmental_score': 80
            },
            'bus': {
                'avg_km_per_month': 400.0,
                'avg_kg_co2_per_km': 0.06,
                'avg_cost_per_km': 0.12,
                'efficiency_improvement': 'Use for city travel',
                'environmental_score': 65
            },
            'motorcycle': {
                'avg_km_per_month': 300.0,
                'avg_kg_co2_per_km': 0.10,
                'avg_cost_per_km': 0.20,
                'efficiency_improvement': 'More efficient than cars',
                'environmental_score': 55
            }
        }
    
    def _initialize_emission_factors(self) -> Dict[str, float]:
        """
        Initialize emission factors for different transport modes.
        """
        return {
            'car': 0.18,
            'public_transit': 0.05,
            'bicycle': 0.0,
            'walking': 0.0,
            'electric_vehicle': 0.05,
            'rideshare': 0.15,
            'train': 0.04,
            'bus': 0.06,
            'carpool': 0.09,
            'motorcycle': 0.10,
            'taxi': 0.20,
            'scooter': 0.04,
            'shuttle': 0.07,
            'ferry': 0.12
        }
    
    def _initialize_alternative_modes(self) -> List[Dict[str, Any]]:
        """
        Initialize alternative transportation modes.
        """
        return [
            {
                'mode': 'Carpool',
                'carbon_savings_percentage': 50,
                'cost_savings_percentage': 40,
                'effort': 'medium',
                'recommendation': 'Share rides with coworkers or neighbors',
                'environmental_score': 65
            },
            {
                'mode': 'Public Transit',
                'carbon_savings_percentage': 70,
                'cost_savings_percentage': 50,
                'effort': 'medium',
                'recommendation': 'Use bus or train for commute',
                'environmental_score': 70
            },
            {
                'mode': 'Bicycle',
                'carbon_savings_percentage': 100,
                'cost_savings_percentage': 90,
                'effort': 'high',
                'recommendation': 'Bike for short trips and commute',
                'environmental_score': 95
            },
            {
                'mode': 'Electric Vehicle',
                'carbon_savings_percentage': 70,
                'cost_savings_percentage': 60,
                'effort': 'high',
                'recommendation': 'Switch to electric vehicle',
                'environmental_score': 75
            },
            {
                'mode': 'Walking',
                'carbon_savings_percentage': 100,
                'cost_savings_percentage': 100,
                'effort': 'low',
                'recommendation': 'Walk for trips under 2 km',
                'environmental_score': 100
            },
            {
                'mode': 'Train',
                'carbon_savings_percentage': 75,
                'cost_savings_percentage': 45,
                'effort': 'medium',
                'recommendation': 'Use train for long-distance travel',
                'environmental_score': 80
            },
            {
                'mode': 'Bus',
                'carbon_savings_percentage': 65,
                'cost_savings_percentage': 55,
                'effort': 'medium',
                'recommendation': 'Use bus for city travel',
                'environmental_score': 65
            },
            {
                'mode': 'Telecommute',
                'carbon_savings_percentage': 100,
                'cost_savings_percentage': 80,
                'effort': 'low',
                'recommendation': 'Work from home when possible',
                'environmental_score': 100
            },
            {
                'mode': 'Scooter',
                'carbon_savings_percentage': 75,
                'cost_savings_percentage': 70,
                'effort': 'medium',
                'recommendation': 'Use scooter for short urban trips',
                'environmental_score': 85
            }
        ]
    
    def _initialize_cost_factors(self) -> Dict[str, float]:
        """
        Initialize cost factors (USD per km).
        """
        return {
            'car': 0.30,
            'public_transit': 0.15,
            'bicycle': 0.02,
            'walking': 0.0,
            'electric_vehicle': 0.12,
            'rideshare': 0.50,
            'train': 0.20,
            'bus': 0.12,
            'carpool': 0.15,
            'motorcycle': 0.20,
            'taxi': 1.00,
            'scooter': 0.15,
            'shuttle': 0.18,
            'ferry': 0.25
        }
    
    def analyze_transportation(self, 
                              resources: List[HouseholdResource],
                              household_size: int) -> TransportationOptimization:
        """
        Analyze household transportation.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            TransportationOptimization: Transportation optimization analysis
        """
        optimization = TransportationOptimization(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Get transportation resources
        transport_resources = [r for r in resources if r.resource_type == ResourceType.TRANSPORTATION]
        
        if not transport_resources:
            logger.warning("No transportation resources found")
            return optimization
        
        # Calculate total distance
        optimization.total_distance = sum(r.current_usage for r in transport_resources)
        
        # Analyze primary modes
        optimization.primary_modes = self._analyze_primary_modes(transport_resources)
        
        # Calculate carbon emissions
        optimization.carbon_emissions = self._calculate_carbon_emissions(transport_resources)
        
        # Calculate transportation cost
        optimization.transportation_cost = self._calculate_transportation_cost(transport_resources)
        
        # Mode breakdown
        optimization.mode_usage = {
            r.name: r.current_usage for r in transport_resources
        }
        optimization.mode_emissions = {
            r.name: r.current_usage * self.emission_factors.get(r.name.lower(), 0.15)
            for r in transport_resources
        }
        optimization.mode_costs = {
            r.name: r.current_usage * self.cost_factors.get(r.name.lower(), 0.25)
            for r in transport_resources
        }
        
        # Find shared transport opportunities
        optimization.shared_transport_opportunities = self._find_shared_transport_opportunities(
            transport_resources, household_size
        )
        
        # Find lower impact alternatives
        optimization.lower_impact_alternatives = self._find_lower_impact_alternatives(
            transport_resources
        )
        
        # Calculate cost comparison
        optimization.cost_comparison = self._calculate_cost_comparison(transport_resources)
        
        # Calculate carbon comparison
        optimization.carbon_comparison = self._calculate_carbon_comparison(transport_resources)
        
        # Calculate savings estimates
        optimization.estimated_carbon_savings = self._calculate_carbon_savings(transport_resources)
        optimization.estimated_cost_savings = self._calculate_cost_savings(transport_resources)
        
        # Generate recommendations
        optimization.recommendations = self._generate_recommendations(transport_resources)
        optimization.priority_recommendations = self._prioritize_recommendations(
            optimization.recommendations
        )
        
        return optimization
    
    def _analyze_primary_modes(self, 
                              resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Analyze primary transportation modes.
        """
        modes = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.transport_benchmarks.get(name, {})
            
            if benchmark:
                modes.append({
                    'mode': name,
                    'monthly_distance': resource.current_usage,
                    'carbon_emissions': resource.current_usage * benchmark.get('avg_kg_co2_per_km', 0),
                    'cost': resource.current_usage * benchmark.get('avg_cost_per_km', 0),
                    'environmental_score': benchmark.get('environmental_score', 50),
                    'efficiency_improvement': benchmark.get('efficiency_improvement', '')
                })
        
        return sorted(modes, key=lambda x: x['monthly_distance'], reverse=True)
    
    def _calculate_carbon_emissions(self, 
                                   resources: List[HouseholdResource]) -> float:
        """
        Calculate total carbon emissions from transportation.
        """
        total_emissions = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            emission_factor = self.emission_factors.get(name, 0.15)
            total_emissions += resource.current_usage * emission_factor
        
        return total_emissions
    
    def _calculate_transportation_cost(self, 
                                      resources: List[HouseholdResource]) -> float:
        """
        Calculate total transportation cost.
        """
        total_cost = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            cost_factor = self.cost_factors.get(name, 0.25)
            total_cost += resource.current_usage * cost_factor
        
        return total_cost
    
    def _find_shared_transport_opportunities(self, 
                                            resources: List[HouseholdResource],
                                            household_size: int) -> List[Dict[str, Any]]:
        """
        Find shared transportation opportunities.
        """
        opportunities = []
        
        # Check if car usage is high
        car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
        
        if car_resource and car_resource.current_usage > 500 and household_size >= 2:
            opportunities.append({
                'opportunity': 'Carpool to work/school',
                'potential_savings': car_resource.current_usage * 0.3,
                'carbon_reduction': car_resource.current_usage * 0.18 * 0.3,
                'cost_savings': car_resource.current_usage * 0.30 * 0.3,
                'effort': 'medium',
                'benefit': 'High'
            })
        
        # Check if multiple cars
        cars = [r for r in resources if r.name.lower() == 'car']
        if len(cars) >= 2:
            opportunities.append({
                'opportunity': 'Reduce number of cars',
                'potential_savings': sum(c.current_usage for c in cars) * 0.2,
                'carbon_reduction': sum(c.current_usage for c in cars) * 0.18 * 0.2,
                'cost_savings': sum(c.current_usage for c in cars) * 0.30 * 0.2,
                'effort': 'high',
                'benefit': 'Very High'
            })
        
        return opportunities
    
    def _find_lower_impact_alternatives(self, 
                                       resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find lower impact transportation alternatives.
        """
        alternatives = []
        
        for alternative in self.alternative_modes:
            # Check if this alternative would work
            if alternative['mode'] in ['Telecommute']:
                car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
                if car_resource:
                    savings = car_resource.current_usage * 0.2
                    alternatives.append({
                        'alternative': alternative['mode'],
                        'recommendation': alternative['recommendation'],
                        'carbon_savings': savings * 0.18,
                        'cost_savings': savings * 0.30,
                        'effort': alternative['effort'],
                        'carbon_savings_percentage': alternative['carbon_savings_percentage'],
                        'cost_savings_percentage': alternative['cost_savings_percentage'],
                        'environmental_score': alternative['environmental_score']
                    })
            
            elif alternative['mode'] in ['Public Transit', 'Train', 'Bus']:
                car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
                if car_resource and car_resource.current_usage > 300:
                    savings = car_resource.current_usage * 0.4
                    alternatives.append({
                        'alternative': alternative['mode'],
                        'recommendation': alternative['recommendation'],
                        'carbon_savings': savings * 0.18,
                        'cost_savings': savings * 0.30,
                        'effort': alternative['effort'],
                        'carbon_savings_percentage': alternative['carbon_savings_percentage'],
                        'cost_savings_percentage': alternative['cost_savings_percentage'],
                        'environmental_score': alternative['environmental_score']
                    })
            
            elif alternative['mode'] in ['Bicycle', 'Walking']:
                car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
                if car_resource:
                    savings = car_resource.current_usage * 0.1
                    alternatives.append({
                        'alternative': alternative['mode'],
                        'recommendation': alternative['recommendation'],
                        'carbon_savings': savings * 0.18,
                        'cost_savings': savings * 0.30,
                        'effort': alternative['effort'],
                        'carbon_savings_percentage': alternative['carbon_savings_percentage'],
                        'cost_savings_percentage': alternative['cost_savings_percentage'],
                        'environmental_score': alternative['environmental_score']
                    })
            
            elif alternative['mode'] in ['Electric Vehicle']:
                car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
                if car_resource:
                    savings = car_resource.current_usage * 0.7
                    alternatives.append({
                        'alternative': alternative['mode'],
                        'recommendation': alternative['recommendation'],
                        'carbon_savings': savings * 0.18,
                        'cost_savings': savings * 0.30,
                        'effort': alternative['effort'],
                        'carbon_savings_percentage': alternative['carbon_savings_percentage'],
                        'cost_savings_percentage': alternative['cost_savings_percentage'],
                        'environmental_score': alternative['environmental_score']
                    })
        
        return sorted(alternatives, key=lambda x: x['carbon_savings'], reverse=True)
    
    def _calculate_cost_comparison(self, 
                                  resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate cost comparison between modes.
        """
        comparison = {}
        
        for resource in resources:
            name = resource.name.lower()
            cost_factor = self.cost_factors.get(name, 0.25)
            cost = resource.current_usage * cost_factor
            
            comparison[name] = {
                'monthly_cost': cost,
                'yearly_cost': cost * 12,
                'cost_per_km': cost_factor
            }
        
        return comparison
    
    def _calculate_carbon_comparison(self, 
                                    resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate carbon comparison between modes.
        """
        comparison = {}
        
        for resource in resources:
            name = resource.name.lower()
            emission_factor = self.emission_factors.get(name, 0.15)
            emissions = resource.current_usage * emission_factor
            
            comparison[name] = {
                'monthly_emissions': emissions,
                'yearly_emissions': emissions * 12,
                'emissions_per_km': emission_factor
            }
        
        return comparison
    
    def _calculate_carbon_savings(self, 
                                 resources: List[HouseholdResource]) -> float:
        """
        Calculate potential carbon savings.
        """
        total_savings = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            
            if name == 'car':
                savings = resource.current_usage * 0.3 * (0.18 - 0.05)
                total_savings += savings
            elif name in ['rideshare', 'taxi']:
                savings = resource.current_usage * 0.2 * 0.15
                total_savings += savings
        
        return total_savings
    
    def _calculate_cost_savings(self, 
                               resources: List[HouseholdResource]) -> float:
        """
        Calculate potential cost savings.
        """
        total_savings = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            
            if name == 'car':
                savings = resource.current_usage * 0.3 * (0.30 - 0.15)
                total_savings += savings
            elif name in ['rideshare', 'taxi']:
                savings = resource.current_usage * 0.2 * 0.20
                total_savings += savings
        
        return total_savings
    
    def _generate_recommendations(self, 
                                 resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate transportation recommendations.
        """
        recommendations = []
        
        # Check for high car usage
        car_resource = next((r for r in resources if r.name.lower() == 'car'), None)
        
        if car_resource and car_resource.current_usage > 500:
            recommendations.append({
                'mode': 'Car',
                'recommendation': 'Reduce car usage by 20%',
                'current_usage': car_resource.current_usage,
                'target_usage': car_resource.current_usage * 0.8,
                'savings': car_resource.current_usage * 0.2,
                'carbon_savings': car_resource.current_usage * 0.2 * 0.18,
                'cost_savings': car_resource.current_usage * 0.2 * 0.30,
                'priority': 'high',
                'effort': 'medium',
                'actions': [
                    'Use public transit for commute',
                    'Carpool with colleagues',
                    'Work from home 1 day/week'
                ]
            })
        
        # Add alternative recommendations
        for alt in self.alternative_modes[:4]:
            recommendations.append({
                'mode': alt['mode'],
                'recommendation': alt['recommendation'],
                'carbon_savings_percentage': alt['carbon_savings_percentage'],
                'cost_savings_percentage': alt['cost_savings_percentage'],
                'effort': alt['effort'],
                'priority': 'medium' if alt['effort'] in ['low', 'medium'] else 'low',
                'environmental_score': alt['environmental_score'],
                'actions': [f'Try using {alt["mode"]} for short trips']
            })
        
        return sorted(recommendations, key=lambda x: x.get('carbon_savings', 0), reverse=True)
    
    def _prioritize_recommendations(self, 
                                   recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize transportation recommendations.
        """
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return sorted(recommendations, key=lambda x: priority_order.get(x.get('priority', 'medium'), 2))
    
    def get_transportation_score(self, 
                                resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Get overall transportation score.
        
        Args:
            resources: List of transportation resources
        
        Returns:
            Dict: Transportation score
        """
        if not resources:
            return {'score': 0, 'grade': 'F'}
        
        # Calculate score based on emissions
        total_emissions = self._calculate_carbon_emissions(resources)
        total_distance = sum(r.current_usage for r in resources)
        
        if total_distance > 0:
            emissions_per_km = total_emissions / total_distance
            # Scale: 0.18 is average car emissions
            if emissions_per_km <= 0.02:
                score = 90
            elif emissions_per_km <= 0.05:
                score = 75
            elif emissions_per_km <= 0.10:
                score = 60
            elif emissions_per_km <= 0.15:
                score = 40
            else:
                score = 20
        else:
            score = 50
        
        grade = self._get_grade(score)
        
        return {
            'score': score,
            'grade': grade,
            'total_emissions': total_emissions,
            'total_distance': total_distance,
            'emissions_per_km': emissions_per_km if total_distance > 0 else 0,
            'primary_modes': self._analyze_primary_modes(resources),
            'mode_scores': {r.name: r.efficiency_score for r in resources}
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