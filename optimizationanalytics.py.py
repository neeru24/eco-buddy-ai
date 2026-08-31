"""
Smart Household Resource Optimization Engine - Analytics
Provides analytics for optimization data.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from optimization.models import (
    HouseholdResource, OptimizationPlan, OptimizationProgress,
    EfficiencyScore, HouseholdEfficiency
)

logger = logging.getLogger(__name__)


class OptimizationAnalytics:
    """
    Provides analytics for optimization data.
    """
    
    def __init__(self):
        """Initialize the analytics engine."""
        logger.info("Optimization Analytics initialized")
    
    def analyze_household_efficiency(self, 
                                    resources: List[HouseholdResource]) -> HouseholdEfficiency:
        """
        Analyze household efficiency.
        
        Args:
            resources: List of resources
        
        Returns:
            HouseholdEfficiency: Household efficiency analysis
        """
        efficiency = HouseholdEfficiency(
            household_id=resources[0].household_id if resources else ""
        )
        
        if not resources:
            return efficiency
        
        # Calculate category scores
        scores = {}
        for resource in resources:
            key = resource.resource_type.value
            if key not in scores:
                scores[key] = []
            scores[key].append(resource.calculate_efficiency_score())
        
        # Calculate averages
        efficiency.energy_score = statistics.mean(scores.get('energy', [50])) if scores.get('energy') else 50
        efficiency.water_score = statistics.mean(scores.get('water', [50])) if scores.get('water') else 50
        efficiency.waste_score = statistics.mean(scores.get('waste', [50])) if scores.get('waste') else 50
        efficiency.food_score = statistics.mean(scores.get('food', [50])) if scores.get('food') else 50
        efficiency.transport_score = statistics.mean(scores.get('transportation', [50])) if scores.get('transportation') else 50
        efficiency.shopping_score = statistics.mean(scores.get('shopping', [50])) if scores.get('shopping') else 50
        
        # Calculate overall score
        all_scores = [
            efficiency.energy_score,
            efficiency.water_score,
            efficiency.waste_score,
            efficiency.food_score,
            efficiency.transport_score,
            efficiency.shopping_score
        ]
        efficiency.overall_score = statistics.mean(all_scores)
        efficiency.overall_grade = self._get_grade(efficiency.overall_score)
        
        # Calculate rankings
        category_scores = {
            'energy': efficiency.energy_score,
            'water': efficiency.water_score,
            'waste': efficiency.waste_score,
            'food': efficiency.food_score,
            'transport': efficiency.transport_score,
            'shopping': efficiency.shopping_score
        }
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        for i, (category, _) in enumerate(sorted_categories):
            efficiency.category_rankings[category] = i + 1
        
        # Calculate improvement potential
        efficiency.improvement_potential = 100 - efficiency.overall_score
        
        # Generate recommended actions
        for category, score in sorted_categories:
            if score < 60:
                efficiency.recommended_actions.append(f"Improve {category} efficiency (current: {score:.1f}%)")
        
        # Set benchmarks
        efficiency.benchmarks = {
            'excellent': 85,
            'good': 70,
            'fair': 55,
            'poor': 40
        }
        
        efficiency.calculated_at = datetime.now()
        
        return efficiency
    
    def _get_grade(self, score: float) -> str:
        """
        Get grade from score.
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
    
    def get_resource_trends(self, 
                           resources: List[HouseholdResource],
                           days: int = 30) -> Dict[str, Any]:
        """
        Get resource trends.
        
        Args:
            resources: List of resources
            days: Number of days to include
        
        Returns:
            Dict: Trend analysis
        """
        trends = {}
        
        for resource in resources:
            if resource.historical_usage:
                values = [h.get('value', 0) for h in resource.historical_usage[-days:]]
                dates = [h.get('date', '') for h in resource.historical_usage[-days:]]
                
                if values:
                    trends[resource.resource_type.value] = {
                        'values': values,
                        'dates': dates,
                        'current': values[-1] if values else 0,
                        'average': statistics.mean(values) if values else 0,
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'change': values[-1] - values[0] if len(values) > 1 else 0,
                        'change_percentage': ((values[-1] - values[0]) / (values[0] + 0.001) * 100) if values and values[0] > 0 else 0
                    }
        
        return trends
    
    def get_savings_analytics(self, 
                             resources: List[HouseholdResource],
                             optimization_potential: Dict[str, float]) -> Dict[str, Any]:
        """
        Get savings analytics.
        
        Args:
            resources: List of resources
            optimization_potential: Optimization potential by category
        
        Returns:
            Dict: Savings analytics
        """
        total_savings = 0.0
        category_savings = {}
        
        for resource in resources:
            key = resource.resource_type.value
            potential = optimization_potential.get(key, 0)
            savings = resource.current_usage * (potential / 100)
            category_savings[key] = savings
            total_savings += savings
        
        return {
            'total_savings': total_savings,
            'category_savings': category_savings,
            'top_category': max(category_savings.items(), key=lambda x: x[1])[0] if category_savings else None,
            'estimated_annual_savings': total_savings * 12,
            'estimated_cost_savings': self._calculate_cost_savings(category_savings)
        }
    
    def _calculate_cost_savings(self, category_savings: Dict[str, float]) -> float:
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
        
        total = 0.0
        for category, savings in category_savings.items():
            rate = cost_rates.get(category, 0)
            total += savings * rate
        
        return total
    
    def get_progress_metrics(self, 
                            plans: List[OptimizationPlan]) -> Dict[str, Any]:
        """
        Get progress metrics for optimization plans.
        
        Args:
            plans: List of optimization plans
        
        Returns:
            Dict: Progress metrics
        """
        if not plans:
            return {'message': 'No plans available'}
        
        active_plans = [p for p in plans if p.status.value in ['active', 'in_progress']]
        completed_plans = [p for p in plans if p.status.value == 'completed']
        
        total_savings = sum(p.achieved_savings for p in plans)
        total_targets = sum(p.total_actions for p in plans)
        completed_targets = sum(p.completed_actions for p in plans)
        
        return {
            'total_plans': len(plans),
            'active_plans': len(active_plans),
            'completed_plans': len(completed_plans),
            'completion_rate': (len(completed_plans) / len(plans) * 100) if plans else 0,
            'total_savings': total_savings,
            'total_targets': total_targets,
            'completed_targets': completed_targets,
            'target_completion_rate': (completed_targets / total_targets * 100) if total_targets > 0 else 0,
            'average_progress': statistics.mean([p.overall_progress for p in plans]) if plans else 0
        }