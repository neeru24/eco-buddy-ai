"""
Smart Household Resource Optimization Engine - Food & Waste Optimizer
Optimizes food consumption and waste management.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    FoodWasteOptimization, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class FoodWasteOptimizer:
    """
    Analyzes and optimizes food consumption and waste.
    """
    
    def __init__(self):
        """Initialize the food and waste optimizer."""
        self.food_benchmarks = self._initialize_food_benchmarks()
        self.waste_benchmarks = self._initialize_waste_benchmarks()
        self.reduction_strategies = self._initialize_reduction_strategies()
        logger.info("Food & Waste Optimizer initialized")
    
    def _initialize_food_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize food consumption benchmarks.
        """
        return {
            'vegetables': {
                'avg_kg_per_person_month': 15.0,
                'waste_percentage': 20.0,
                'saving_strategy': 'Plan meals, buy only what is needed'
            },
            'fruits': {
                'avg_kg_per_person_month': 10.0,
                'waste_percentage': 25.0,
                'saving_strategy': 'Store properly, eat before expiry'
            },
            'meat': {
                'avg_kg_per_person_month': 5.0,
                'waste_percentage': 10.0,
                'saving_strategy': 'Reduce portions, freeze leftovers'
            },
            'dairy': {
                'avg_kg_per_person_month': 8.0,
                'waste_percentage': 15.0,
                'saving_strategy': 'Check expiry dates, buy smaller quantities'
            },
            'grains': {
                'avg_kg_per_person_month': 10.0,
                'waste_percentage': 10.0,
                'saving_strategy': 'Store in airtight containers'
            },
            'processed_foods': {
                'avg_kg_per_person_month': 5.0,
                'waste_percentage': 15.0,
                'saving_strategy': 'Plan meals around fresh ingredients'
            }
        }
    
    def _initialize_waste_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize waste benchmarks.
        """
        return {
            'food_waste': {
                'avg_kg_per_person_month': 8.0,
                'recyclable_percentage': 30.0,
                'compostable_percentage': 40.0
            },
            'paper_waste': {
                'avg_kg_per_person_month': 5.0,
                'recyclable_percentage': 70.0,
                'compostable_percentage': 10.0
            },
            'plastic_waste': {
                'avg_kg_per_person_month': 4.0,
                'recyclable_percentage': 30.0,
                'compostable_percentage': 0.0
            },
            'glass_waste': {
                'avg_kg_per_person_month': 2.0,
                'recyclable_percentage': 80.0,
                'compostable_percentage': 0.0
            },
            'metal_waste': {
                'avg_kg_per_person_month': 1.0,
                'recyclable_percentage': 90.0,
                'compostable_percentage': 0.0
            }
        }
    
    def _initialize_reduction_strategies(self) -> List[Dict[str, Any]]:
        """
        Initialize waste reduction strategies.
        """
        return [
            {
                'strategy': 'Meal planning',
                'waste_reduction_percentage': 30,
                'effort': 'medium',
                'cost_savings_percent': 20
            },
            {
                'strategy': 'Composting',
                'waste_reduction_percentage': 40,
                'effort': 'medium',
                'cost_savings_percent': 10
            },
            {
                'strategy': 'Proper food storage',
                'waste_reduction_percentage': 25,
                'effort': 'low',
                'cost_savings_percent': 15
            },
            {
                'strategy': 'Recycling optimization',
                'waste_reduction_percentage': 20,
                'effort': 'low',
                'cost_savings_percent': 5
            },
            {
                'strategy': 'Buy in bulk',
                'waste_reduction_percentage': 15,
                'effort': 'medium',
                'cost_savings_percent': 25
            },
            {
                'strategy': 'Use leftovers creatively',
                'waste_reduction_percentage': 35,
                'effort': 'medium',
                'cost_savings_percent': 30
            },
            {
                'strategy': 'Shop with a list',
                'waste_reduction_percentage': 20,
                'effort': 'low',
                'cost_savings_percent': 15
            },
            {
                'strategy': 'Check fridge temperature',
                'waste_reduction_percentage': 10,
                'effort': 'low',
                'cost_savings_percent': 5
            },
            {
                'strategy': 'Use first-in-first-out',
                'waste_reduction_percentage': 20,
                'effort': 'low',
                'cost_savings_percent': 10
            },
            {
                'strategy': 'Canning and preserving',
                'waste_reduction_percentage': 30,
                'effort': 'high',
                'cost_savings_percent': 20
            }
        ]
    
    def analyze_food_waste(self, 
                          resources: List[HouseholdResource],
                          household_size: int) -> FoodWasteOptimization:
        """
        Analyze food consumption and waste.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            FoodWasteOptimization: Food and waste optimization analysis
        """
        optimization = FoodWasteOptimization(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Get food and waste resources
        food_resources = [r for r in resources if r.resource_type == ResourceType.FOOD]
        waste_resources = [r for r in resources if r.resource_type == ResourceType.WASTE]
        
        # Analyze food consumption
        if food_resources:
            optimization.total_food_consumption = sum(r.current_usage for r in food_resources)
            optimization.food_waste_amount = self._estimate_food_waste(food_resources)
            optimization.food_waste_percentage = (
                (optimization.food_waste_amount / optimization.total_food_consumption) * 100
                if optimization.total_food_consumption > 0 else 0
            )
            
            # Find food waste reduction opportunities
            optimization.food_waste_reduction_opportunities = self._find_food_waste_opportunities(
                food_resources, household_size
            )
        
        # Analyze waste
        if waste_resources:
            optimization.total_waste = sum(r.current_usage for r in waste_resources)
            optimization.recyclable_waste = self._estimate_recyclable_waste(waste_resources)
            optimization.compostable_waste = self._estimate_compostable_waste(waste_resources)
            optimization.landfill_waste = (
                optimization.total_waste - 
                optimization.recyclable_waste - 
                optimization.compostable_waste
            )
            
            # Find recycling improvement opportunities
            optimization.recycling_improvement_opportunities = self._find_recycling_opportunities(
                waste_resources
            )
            
            # Find composting opportunities
            optimization.composting_opportunities = self._find_composting_opportunities(
                waste_resources
            )
        
        # Calculate savings estimates
        optimization.estimated_waste_reduction = self._calculate_waste_reduction(
            optimization, household_size
        )
        optimization.estimated_cost_savings = self._calculate_cost_savings(
            optimization, household_size
        )
        optimization.estimated_environmental_impact = self._calculate_environmental_impact(
            optimization
        )
        
        # Generate recommendations
        optimization.food_recommendations = self._generate_food_recommendations(
            optimization, household_size
        )
        optimization.waste_recommendations = self._generate_waste_recommendations(
            optimization, household_size
        )
        
        return optimization
    
    def _estimate_food_waste(self, 
                            resources: List[HouseholdResource]) -> float:
        """
        Estimate food waste.
        """
        total_waste = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.food_benchmarks.get(name, {})
            waste_pct = benchmark.get('waste_percentage', 15.0)
            
            total_waste += resource.current_usage * (waste_pct / 100)
        
        return total_waste
    
    def _find_food_waste_opportunities(self, 
                                      resources: List[HouseholdResource],
                                      household_size: int) -> List[Dict[str, Any]]:
        """
        Find food waste reduction opportunities.
        """
        opportunities = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.food_benchmarks.get(name, {})
            
            if benchmark:
                avg_consumption = benchmark.get('avg_kg_per_person_month', 0) * household_size
                waste_pct = benchmark.get('waste_percentage', 15.0)
                estimated_waste = resource.current_usage * (waste_pct / 100)
                
                opportunities.append({
                    'category': name,
                    'current_consumption': resource.current_usage,
                    'estimated_waste': estimated_waste,
                    'waste_percentage': waste_pct,
                    'saving_strategy': benchmark.get('saving_strategy', 'Reduce waste'),
                    'potential_savings': estimated_waste * 0.5  # Can reduce waste by 50%
                })
        
        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)
    
    def _estimate_recyclable_waste(self, 
                                  resources: List[HouseholdResource]) -> float:
        """
        Estimate recyclable waste.
        """
        total_recyclable = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.waste_benchmarks.get(name, {})
            recyclable_pct = benchmark.get('recyclable_percentage', 0)
            
            total_recyclable += resource.current_usage * (recyclable_pct / 100)
        
        return total_recyclable
    
    def _estimate_compostable_waste(self, 
                                   resources: List[HouseholdResource]) -> float:
        """
        Estimate compostable waste.
        """
        total_compostable = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.waste_benchmarks.get(name, {})
            compostable_pct = benchmark.get('compostable_percentage', 0)
            
            total_compostable += resource.current_usage * (compostable_pct / 100)
        
        return total_compostable
    
    def _find_recycling_opportunities(self, 
                                     resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find recycling improvement opportunities.
        """
        opportunities = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.waste_benchmarks.get(name, {})
            recyclable_pct = benchmark.get('recyclable_percentage', 0)
            max_recyclable = 100.0  # Maximum achievable recycling rate
            
            if recyclable_pct < max_recyclable:
                improvement_potential = max_recyclable - recyclable_pct
                
                opportunities.append({
                    'category': name,
                    'current_recyclable': resource.current_usage * (recyclable_pct / 100),
                    'potential_recyclable': resource.current_usage * (max_recyclable / 100),
                    'improvement_potential': improvement_potential,
                    'recommendation': self._get_recycling_recommendation(name)
                })
        
        return sorted(opportunities, key=lambda x: x['improvement_potential'], reverse=True)
    
    def _get_recycling_recommendation(self, category: str) -> str:
        """
        Get recycling recommendation.
        """
        recommendations = {
            'food_waste': 'Start composting food waste',
            'paper_waste': 'Recycle all paper and cardboard',
            'plastic_waste': 'Check recycling symbols, clean before recycling',
            'glass_waste': 'Rinse and separate by color',
            'metal_waste': 'Clean and crush if possible'
        }
        return recommendations.get(category, 'Check local recycling guidelines')
    
    def _find_composting_opportunities(self, 
                                      resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find composting opportunities.
        """
        opportunities = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.waste_benchmarks.get(name, {})
            compostable_pct = benchmark.get('compostable_percentage', 0)
            
            if compostable_pct > 0:
                opportunities.append({
                    'category': name,
                    'compostable_amount': resource.current_usage * (compostable_pct / 100),
                    'recommendation': 'Start composting ' + name,
                    'effort': 'medium',
                    'impact': 'high'
                })
        
        return sorted(opportunities, key=lambda x: x['compostable_amount'], reverse=True)
    
    def _calculate_waste_reduction(self, 
                                  optimization: FoodWasteOptimization,
                                  household_size: int) -> float:
        """
        Calculate potential waste reduction.
        """
        # Based on reduction strategies
        total_reduction = 0.0
        
        for strategy in self.reduction_strategies:
            reduction_pct = strategy['waste_reduction_percentage'] / 100
            total_reduction += optimization.total_waste * reduction_pct
        
        # Average the reductions
        if self.reduction_strategies:
            total_reduction = total_reduction / len(self.reduction_strategies)
        
        return min(total_reduction, optimization.total_waste * 0.5)  # Max 50% reduction
    
    def _calculate_cost_savings(self, 
                              optimization: FoodWasteOptimization,
                              household_size: int) -> float:
        """
        Calculate cost savings from food waste reduction.
        """
        # Estimate cost of wasted food
        avg_food_cost_per_kg = 5.0  # Average USD per kg
        food_cost_savings = optimization.food_waste_amount * avg_food_cost_per_kg * 0.5
        
        # Waste disposal savings
        avg_disposal_cost_per_kg = 0.05
        disposal_savings = optimization.total_waste * avg_disposal_cost_per_kg
        
        return food_cost_savings + disposal_savings
    
    def _calculate_environmental_impact(self, 
                                      optimization: FoodWasteOptimization) -> float:
        """
        Calculate environmental impact of food waste.
        """
        # Carbon impact of food waste (kg CO2 per kg food)
        carbon_per_kg_food = 0.5
        carbon_from_food = optimization.food_waste_amount * carbon_per_kg_food
        
        # Carbon impact of waste disposal
        carbon_per_kg_waste = 0.2
        carbon_from_waste = optimization.total_waste * carbon_per_kg_waste
        
        return carbon_from_food + carbon_from_waste
    
    def _generate_food_recommendations(self, 
                                      optimization: FoodWasteOptimization,
                                      household_size: int) -> List[Dict[str, Any]]:
        """
        Generate food recommendations.
        """
        recommendations = []
        
        if optimization.food_waste_percentage > 15:
            for opportunity in optimization.food_waste_reduction_opportunities[:3]:
                recommendations.append({
                    'category': opportunity['category'],
                    'recommendation': opportunity['saving_strategy'],
                    'potential_savings': opportunity['potential_savings'],
                    'priority': 'high' if opportunity['potential_savings'] > 5 else 'medium',
                    'effort': 'medium'
                })
        
        # Add general food recommendations
        general_recs = [
            {
                'category': 'General',
                'recommendation': 'Plan weekly meals and create a shopping list',
                'potential_savings': optimization.food_waste_amount * 0.15,
                'priority': 'high',
                'effort': 'medium'
            },
            {
                'category': 'General',
                'recommendation': 'Store food properly to extend shelf life',
                'potential_savings': optimization.food_waste_amount * 0.10,
                'priority': 'medium',
                'effort': 'low'
            },
            {
                'category': 'General',
                'recommendation': 'Use leftovers for next day\'s meals',
                'potential_savings': optimization.food_waste_amount * 0.12,
                'priority': 'high',
                'effort': 'low'
            }
        ]
        
        recommendations.extend(general_recs)
        
        return sorted(recommendations, key=lambda x: x.get('potential_savings', 0), reverse=True)
    
    def _generate_waste_recommendations(self, 
                                       optimization: FoodWasteOptimization,
                                       household_size: int) -> List[Dict[str, Any]]:
        """
        Generate waste recommendations.
        """
        recommendations = []
        
        # Recycling recommendations
        for opportunity in optimization.recycling_improvement_opportunities[:3]:
            recommendations.append({
                'category': opportunity['category'],
                'recommendation': opportunity['recommendation'],
                'potential_savings': opportunity['improvement_potential'],
                'priority': 'high' if opportunity['improvement_potential'] > 30 else 'medium',
                'effort': 'low'
            })
        
        # Composting recommendations
        for opportunity in optimization.composting_opportunities[:2]:
            recommendations.append({
                'category': opportunity['category'],
                'recommendation': opportunity['recommendation'],
                'potential_savings': opportunity['compostable_amount'],
                'priority': 'high',
                'effort': opportunity['effort']
            })
        
        # Add general waste recommendations
        general_recs = [
            {
                'category': 'General',
                'recommendation': 'Set up a recycling station at home',
                'potential_savings': optimization.total_waste * 0.15,
                'priority': 'high',
                'effort': 'low'
            },
            {
                'category': 'General',
                'recommendation': 'Start a compost bin for organic waste',
                'potential_savings': optimization.total_waste * 0.20,
                'priority': 'high',
                'effort': 'medium'
            },
            {
                'category': 'General',
                'recommendation': 'Reduce packaging waste by buying in bulk',
                'potential_savings': optimization.total_waste * 0.10,
                'priority': 'medium',
                'effort': 'medium'
            }
        ]
        
        recommendations.extend(general_recs)
        
        return sorted(recommendations, key=lambda x: x.get('potential_savings', 0), reverse=True)