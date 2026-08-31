"""
Smart Household Resource Optimization Engine - Recommendation Engine
Generates optimization recommendations.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    HouseholdResource, OptimizationCategory, RecommendationPriority,
    ImpactLevel, EffortLevel
)

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generates optimization recommendations.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendation_templates = self._initialize_templates()
        logger.info("Recommendation Engine initialized")
    
    def _initialize_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Initialize recommendation templates.
        """
        return {
            'energy': [
                {
                    'title': 'Switch to LED lighting',
                    'description': 'Replace all incandescent bulbs with LED bulbs',
                    'impact': 'high',
                    'effort': 'low',
                    'category': OptimizationCategory.ENERGY_EFFICIENCY,
                    'estimated_savings': 15.0
                },
                {
                    'title': 'Install smart thermostat',
                    'description': 'Use programmable thermostat to optimize heating and cooling',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.TECHNOLOGY_UPGRADE,
                    'estimated_savings': 20.0
                },
                {
                    'title': 'Unplug electronics when not in use',
                    'description': 'Eliminate phantom energy usage by unplugging devices',
                    'impact': 'medium',
                    'effort': 'low',
                    'category': OptimizationCategory.BEHAVIORAL_CHANGE,
                    'estimated_savings': 10.0
                }
            ],
            'water': [
                {
                    'title': 'Fix leaky faucets',
                    'description': 'Repair all leaking faucets and pipes',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.WATER_CONSERVATION,
                    'estimated_savings': 25.0
                },
                {
                    'title': 'Install low-flow showerheads',
                    'description': 'Replace existing showerheads with water-efficient models',
                    'impact': 'high',
                    'effort': 'low',
                    'category': OptimizationCategory.WATER_CONSERVATION,
                    'estimated_savings': 20.0
                },
                {
                    'title': 'Take shorter showers',
                    'description': 'Reduce shower time to 5 minutes or less',
                    'impact': 'medium',
                    'effort': 'low',
                    'category': OptimizationCategory.BEHAVIORAL_CHANGE,
                    'estimated_savings': 15.0
                }
            ],
            'waste': [
                {
                    'title': 'Start composting',
                    'description': 'Compost food waste and yard trimmings',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.WASTE_REDUCTION,
                    'estimated_savings': 30.0
                },
                {
                    'title': 'Set up recycling station',
                    'description': 'Create a dedicated recycling area with proper sorting',
                    'impact': 'medium',
                    'effort': 'low',
                    'category': OptimizationCategory.WASTE_REDUCTION,
                    'estimated_savings': 20.0
                }
            ],
            'food': [
                {
                    'title': 'Plan weekly meals',
                    'description': 'Create meal plans to reduce food waste',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.FOOD_OPTIMIZATION,
                    'estimated_savings': 25.0
                },
                {
                    'title': 'Shop with a list',
                    'description': 'Always use a shopping list to avoid impulse buys',
                    'impact': 'medium',
                    'effort': 'low',
                    'category': OptimizationCategory.SHOPPING_OPTIMIZATION,
                    'estimated_savings': 15.0
                }
            ],
            'transportation': [
                {
                    'title': 'Use public transit',
                    'description': 'Switch to public transportation for commute',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.TRANSPORTATION_OPTIMIZATION,
                    'estimated_savings': 30.0
                },
                {
                    'title': 'Carpool to work',
                    'description': 'Share rides with colleagues',
                    'impact': 'high',
                    'effort': 'medium',
                    'category': OptimizationCategory.TRANSPORTATION_OPTIMIZATION,
                    'estimated_savings': 25.0
                }
            ]
        }
    
    def generate_recommendations(self, 
                                resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate optimization recommendations.
        
        Args:
            resources: List of household resources
        
        Returns:
            List[Dict]: Recommendations
        """
        recommendations = []
        
        for resource in resources:
            key = resource.resource_type.value
            templates = self.recommendation_templates.get(key, [])
            
            for template in templates:
                recommendation = {
                    'title': template['title'],
                    'description': template['description'],
                    'resource_type': key,
                    'impact': template['impact'],
                    'effort': template['effort'],
                    'category': template['category'].value,
                    'estimated_savings': template['estimated_savings'] * (resource.current_usage / 100),
                    'priority': self._get_priority(template['impact'], template['effort']),
                    'resource_name': resource.name
                }
                recommendations.append(recommendation)
        
        # Sort by priority and impact
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        impact_order = {'high': 0, 'medium': 1, 'low': 2}
        
        return sorted(
            recommendations,
            key=lambda x: (priority_order.get(x['priority'], 2), impact_order.get(x['impact'], 1))
        )
    
    def _get_priority(self, impact: str, effort: str) -> str:
        """
        Get priority based on impact and effort.
        """
        if impact == 'high' and effort == 'low':
            return 'critical'
        elif impact == 'high' and effort == 'medium':
            return 'high'
        elif impact == 'medium' and effort == 'low':
            return 'high'
        elif impact == 'high' and effort == 'high':
            return 'medium'
        else:
            return 'low'
    
    def get_quick_wins(self, 
                      resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Get quick win recommendations.
        
        Args:
            resources: List of resources
        
        Returns:
            List[Dict]: Quick win recommendations
        """
        all_recommendations = self.generate_recommendations(resources)
        return [r for r in all_recommendations if r['priority'] in ['critical', 'high']][:5]