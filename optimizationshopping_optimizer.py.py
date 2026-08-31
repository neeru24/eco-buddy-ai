"""
Smart Household Resource Optimization Engine - Shopping Optimizer
Optimizes household shopping and consumption.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    ShoppingOptimization, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class ShoppingOptimizer:
    """
    Analyzes and optimizes household shopping.
    """
    
    def __init__(self):
        """Initialize the shopping optimizer."""
        self.shopping_benchmarks = self._initialize_shopping_benchmarks()
        self.sustainable_alternatives = self._initialize_sustainable_alternatives()
        self.reduction_strategies = self._initialize_reduction_strategies()
        logger.info("Shopping Optimizer initialized")
    
    def _initialize_shopping_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize shopping benchmarks.
        """
        return {
            'groceries': {
                'avg_monthly_spend': 400.0,
                'avg_items_per_month': 30.0,
                'sustainable_alternative': 'Buy local and seasonal',
                'reduction_strategy': 'Meal planning and shopping lists'
            },
            'clothing': {
                'avg_monthly_spend': 100.0,
                'avg_items_per_month': 3.0,
                'sustainable_alternative': 'Second-hand and sustainable brands',
                'reduction_strategy': 'Buy quality over quantity'
            },
            'electronics': {
                'avg_monthly_spend': 50.0,
                'avg_items_per_month': 0.5,
                'sustainable_alternative': 'Refurbished and energy-efficient',
                'reduction_strategy': 'Repair instead of replace'
            },
            'household': {
                'avg_monthly_spend': 75.0,
                'avg_items_per_month': 5.0,
                'sustainable_alternative': 'Eco-friendly products',
                'reduction_strategy': 'Use reusable alternatives'
            },
            'personal_care': {
                'avg_monthly_spend': 50.0,
                'avg_items_per_month': 4.0,
                'sustainable_alternative': 'Zero-waste and natural products',
                'reduction_strategy': 'Buy in bulk'
            },
            'entertainment': {
                'avg_monthly_spend': 100.0,
                'avg_items_per_month': 2.0,
                'sustainable_alternative': 'Digital and experience-based',
                'reduction_strategy': 'Prioritize experiences over items'
            }
        }
    
    def _initialize_sustainable_alternatives(self) -> List[Dict[str, Any]]:
        """
        Initialize sustainable shopping alternatives.
        """
        return [
            {
                'category': 'groceries',
                'alternative': 'Buy from local farmers markets',
                'savings_percentage': 10,
                'environmental_benefit': 'Reduced transport emissions',
                'effort': 'medium'
            },
            {
                'category': 'groceries',
                'alternative': 'Choose organic and sustainable products',
                'savings_percentage': 5,
                'environmental_benefit': 'Reduced chemical usage',
                'effort': 'low'
            },
            {
                'category': 'clothing',
                'alternative': 'Buy second-hand clothing',
                'savings_percentage': 50,
                'environmental_benefit': 'Reduced textile waste',
                'effort': 'medium'
            },
            {
                'category': 'clothing',
                'alternative': 'Choose sustainable fashion brands',
                'savings_percentage': 20,
                'environmental_benefit': 'Ethical production',
                'effort': 'medium'
            },
            {
                'category': 'electronics',
                'alternative': 'Buy refurbished electronics',
                'savings_percentage': 30,
                'environmental_benefit': 'Reduced e-waste',
                'effort': 'low'
            },
            {
                'category': 'household',
                'alternative': 'Use eco-friendly cleaning products',
                'savings_percentage': 10,
                'environmental_benefit': 'Reduced chemical pollution',
                'effort': 'low'
            },
            {
                'category': 'household',
                'alternative': 'Use reusable alternatives (bags, bottles, etc.)',
                'savings_percentage': 15,
                'environmental_benefit': 'Reduced plastic waste',
                'effort': 'low'
            },
            {
                'category': 'personal_care',
                'alternative': 'Choose zero-waste personal care products',
                'savings_percentage': 10,
                'environmental_benefit': 'Reduced packaging waste',
                'effort': 'medium'
            }
        ]
    
    def _initialize_reduction_strategies(self) -> List[Dict[str, Any]]:
        """
        Initialize shopping reduction strategies.
        """
        return [
            {
                'strategy': 'Create shopping lists and stick to them',
                'reduction_percentage': 15,
                'effort': 'low',
                'category': 'all'
            },
            {
                'strategy': 'Buy in bulk to reduce packaging',
                'reduction_percentage': 10,
                'effort': 'medium',
                'category': 'groceries, household'
            },
            {
                'strategy': 'Plan meals weekly',
                'reduction_percentage': 20,
                'effort': 'medium',
                'category': 'groceries'
            },
            {
                'strategy': 'Wait 24 hours before non-essential purchases',
                'reduction_percentage': 25,
                'effort': 'low',
                'category': 'all'
            },
            {
                'strategy': 'Buy quality items that last longer',
                'reduction_percentage': 30,
                'effort': 'medium',
                'category': 'clothing, electronics'
            },
            {
                'strategy': 'Use the library for entertainment',
                'reduction_percentage': 40,
                'effort': 'low',
                'category': 'entertainment'
            },
            {
                'strategy': 'Repair instead of replace',
                'reduction_percentage': 50,
                'effort': 'high',
                'category': 'electronics, clothing'
            }
        ]
    
    def analyze_shopping(self, 
                        resources: List[HouseholdResource],
                        household_size: int) -> ShoppingOptimization:
        """
        Analyze household shopping.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            ShoppingOptimization: Shopping optimization analysis
        """
        optimization = ShoppingOptimization(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Get shopping resources
        shopping_resources = [r for r in resources if r.resource_type == ResourceType.SHOPPING]
        
        if not shopping_resources:
            logger.warning("No shopping resources found")
            return optimization
        
        # Calculate totals
        optimization.total_spending = sum(r.current_usage for r in shopping_resources)
        optimization.total_items = sum(r.current_usage for r in shopping_resources) / 10  # Estimate
        optimization.shopping_frequency = len(shopping_resources) * 4  # Estimate
        
        if optimization.shopping_frequency > 0:
            optimization.average_spend_per_trip = optimization.total_spending / optimization.shopping_frequency
        
        # Category breakdown
        optimization.category_spending = {
            r.name: r.current_usage for r in shopping_resources
        }
        optimization.category_items = {
            r.name: r.current_usage / 10 for r in shopping_resources
        }
        
        # Sustainability metrics
        optimization.sustainable_purchases = sum(
            r.current_usage * 0.2 for r in shopping_resources
        )
        optimization.sustainable_percentage = (
            (optimization.sustainable_purchases / (optimization.total_spending + 0.001)) * 100
        )
        optimization.packaging_waste = optimization.total_items * 0.1  # Estimate
        
        # Find reduction opportunities
        optimization.reduction_opportunities = self._find_reduction_opportunities(
            shopping_resources, household_size
        )
        
        # Find sustainable alternatives
        optimization.sustainable_alternatives = self._find_sustainable_alternatives(
            shopping_resources
        )
        
        # Calculate savings estimates
        optimization.estimated_cost_savings = self._calculate_cost_savings(shopping_resources)
        optimization.estimated_waste_reduction = self._calculate_waste_reduction(shopping_resources)
        
        # Generate recommendations
        optimization.recommendations = self._generate_recommendations(shopping_resources)
        
        return optimization
    
    def _find_reduction_opportunities(self, 
                                     resources: List[HouseholdResource],
                                     household_size: int) -> List[Dict[str, Any]]:
        """
        Find shopping reduction opportunities.
        """
        opportunities = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.shopping_benchmarks.get(name, {})
            
            if benchmark:
                avg_spend = benchmark.get('avg_monthly_spend', 0) * household_size
                current_spend = resource.current_usage
                
                if current_spend > avg_spend:
                    opportunities.append({
                        'category': name,
                        'current_spend': current_spend,
                        'benchmark': avg_spend,
                        'potential_savings': current_spend - avg_spend,
                        'savings_percentage': ((current_spend - avg_spend) / (current_spend + 0.001)) * 100,
                        'strategy': benchmark.get('reduction_strategy', 'Reduce spending'),
                        'sustainable_alternative': benchmark.get('sustainable_alternative', '')
                    })
        
        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)
    
    def _find_sustainable_alternatives(self, 
                                      resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find sustainable shopping alternatives.
        """
        alternatives = []
        
        for resource in resources:
            name = resource.name.lower()
            
            for alt in self.sustainable_alternatives:
                if alt['category'] == name or alt['category'] == 'all':
                    alternatives.append({
                        'category': name,
                        'alternative': alt['alternative'],
                        'savings_percentage': alt['savings_percentage'],
                        'environmental_benefit': alt['environmental_benefit'],
                        'effort': alt['effort']
                    })
        
        return alternatives
    
    def _calculate_cost_savings(self, 
                               resources: List[HouseholdResource]) -> float:
        """
        Calculate potential cost savings.
        """
        total_savings = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.shopping_benchmarks.get(name, {})
            
            if benchmark:
                reduction_pct = 15.0  # Default reduction
                total_savings += resource.current_usage * (reduction_pct / 100)
        
        return total_savings
    
    def _calculate_waste_reduction(self, 
                                  resources: List[HouseholdResource]) -> float:
        """
        Calculate potential waste reduction.
        """
        total_reduction = 0.0
        
        for resource in resources:
            total_reduction += resource.current_usage * 0.05  # 5% waste reduction
        
        return total_reduction
    
    def _generate_recommendations(self, 
                                 resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate shopping recommendations.
        """
        recommendations = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.shopping_benchmarks.get(name, {})
            
            if benchmark:
                current_spend = resource.current_usage
                avg_spend = benchmark.get('avg_monthly_spend', 0)
                
                if current_spend > avg_spend:
                    recommendations.append({
                        'category': name,
                        'recommendation': benchmark.get('reduction_strategy', 'Reduce spending'),
                        'sustainable_alternative': benchmark.get('sustainable_alternative', ''),
                        'current_spend': current_spend,
                        'target_spend': avg_spend,
                        'potential_savings': current_spend - avg_spend,
                        'priority': 'high' if (current_spend - avg_spend) > 50 else 'medium',
                        'effort': 'medium'
                    })
        
        # Add general recommendations
        general_recs = [
            {
                'category': 'General',
                'recommendation': 'Create and stick to shopping lists',
                'potential_savings': sum(r.current_usage for r in resources) * 0.05,
                'priority': 'high',
                'effort': 'low'
            },
            {
                'category': 'General',
                'recommendation': 'Wait 24 hours before non-essential purchases',
                'potential_savings': sum(r.current_usage for r in resources) * 0.10,
                'priority': 'high',
                'effort': 'low'
            },
            {
                'category': 'General',
                'recommendation': 'Buy quality items that last longer',
                'potential_savings': sum(r.current_usage for r in resources) * 0.15,
                'priority': 'medium',
                'effort': 'medium'
            }
        ]
        
        recommendations.extend(general_recs)
        
        return sorted(recommendations, key=lambda x: x.get('potential_savings', 0), reverse=True)