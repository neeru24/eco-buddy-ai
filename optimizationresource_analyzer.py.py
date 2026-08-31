"""
Smart Household Resource Optimization Engine - Resource Analyzer
Analyzes household resource consumption patterns.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from optimization.models import (
    HouseholdResource, ResourceType, ResourceCategory,
    ConsumptionPattern, EfficiencyScore
)

logger = logging.getLogger(__name__)


class ResourceAnalyzer:
    """
    Analyzes household resource consumption and efficiency.
    """
    
    def __init__(self):
        """Initialize the resource analyzer."""
        self.resource_benchmarks = self._initialize_benchmarks()
        self.efficiency_thresholds = self._initialize_thresholds()
        self.consumption_patterns = self._initialize_patterns()
        logger.info("Resource Analyzer initialized")
    
    def _initialize_benchmarks(self) -> Dict[str, Dict[str, float]]:
        """
        Initialize benchmark values for different resources.
        """
        return {
            'energy': {
                'low': 200.0,    # kWh per month
                'medium': 400.0,
                'high': 800.0,
                'very_high': 1500.0,
                'efficient': 150.0
            },
            'water': {
                'low': 2000.0,   # liters per month
                'medium': 4000.0,
                'high': 8000.0,
                'very_high': 15000.0,
                'efficient': 1500.0
            },
            'waste': {
                'low': 20.0,     # kg per month
                'medium': 40.0,
                'high': 80.0,
                'very_high': 150.0,
                'efficient': 10.0
            },
            'food': {
                'low': 50.0,     # kg per month
                'medium': 100.0,
                'high': 200.0,
                'very_high': 350.0,
                'efficient': 40.0
            },
            'transportation': {
                'low': 100.0,    # km per month
                'medium': 300.0,
                'high': 600.0,
                'very_high': 1200.0,
                'efficient': 80.0
            },
            'shopping': {
                'low': 10.0,     # items per month
                'medium': 25.0,
                'high': 50.0,
                'very_high': 100.0,
                'efficient': 8.0
            }
        }
    
    def _initialize_thresholds(self) -> Dict[str, float]:
        """
        Initialize efficiency thresholds.
        """
        return {
            'excellent': 85.0,
            'good': 70.0,
            'fair': 55.0,
            'poor': 40.0
        }
    
    def _initialize_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize consumption pattern detection.
        """
        return {
            'increasing': {'threshold': 10.0, 'direction': 'up'},
            'decreasing': {'threshold': -10.0, 'direction': 'down'},
            'volatile': {'cv_threshold': 0.5},
            'seasonal': {'period': 12, 'strength': 0.3}
        }
    
    def analyze_resources(self, 
                         resources: List[HouseholdResource],
                         period_days: int = 30) -> Dict[str, Any]:
        """
        Analyze household resources.
        
        Args:
            resources: List of household resources
            period_days: Analysis period in days
        
        Returns:
            Dict: Resource analysis results
        """
        if not resources:
            return {'message': 'No resources to analyze'}
        
        analysis = {
            'total_resources': len(resources),
            'by_type': self._group_by_type(resources),
            'by_category': self._group_by_category(resources),
            'consumption_totals': self._calculate_totals(resources),
            'efficiency_scores': self._calculate_efficiency_scores(resources),
            'efficiency_grades': self._calculate_efficiency_grades(resources),
            'high_consumption_areas': self._detect_high_consumption(resources),
            'optimization_potential': self._calculate_optimization_potential(resources),
            'benchmark_comparison': self._compare_to_benchmarks(resources),
            'trends': self._analyze_trends(resources),
            'consumption_patterns': self._detect_patterns(resources),
            'peak_usage': self._detect_peak_usage(resources),
            'quick_wins': self._identify_quick_wins(resources)
        }
        
        return analysis
    
    def _group_by_type(self, 
                      resources: List[HouseholdResource]) -> Dict[str, List[HouseholdResource]]:
        """
        Group resources by type.
        """
        grouped = defaultdict(list)
        for resource in resources:
            grouped[resource.resource_type.value].append(resource)
        return dict(grouped)
    
    def _group_by_category(self, 
                          resources: List[HouseholdResource]) -> Dict[str, List[HouseholdResource]]:
        """
        Group resources by category.
        """
        grouped = defaultdict(list)
        for resource in resources:
            grouped[resource.category.value].append(resource)
        return dict(grouped)
    
    def _calculate_totals(self, resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate total consumption by type.
        """
        totals = {}
        costs = {}
        
        for resource in resources:
            key = resource.resource_type.value
            totals[key] = totals.get(key, 0.0) + resource.current_usage
            costs[key] = costs.get(key, 0.0) + resource.current_cost
        
        return {'usage': totals, 'cost': costs}
    
    def _calculate_efficiency_scores(self, 
                                    resources: List[HouseholdResource]) -> List[EfficiencyScore]:
        """
        Calculate efficiency scores for resources.
        """
        scores = []
        for resource in resources:
            score_value = resource.calculate_efficiency_score()
            grade = resource.get_efficiency_grade()
            
            scores.append(EfficiencyScore(
                household_id=resource.household_id,
                category=resource.resource_type.value,
                score=score_value,
                grade=grade.value,
                benchmark=self.resource_benchmarks.get(resource.resource_type.value, {}).get('medium', 0),
                improvement_potential=max(0, 100 - score_value)
            ))
        return scores
    
    def _calculate_efficiency_grades(self, 
                                    resources: List[HouseholdResource]) -> Dict[str, str]:
        """
        Calculate efficiency grades for resources.
        """
        grades = {}
        for resource in resources:
            grades[resource.resource_type.value] = resource.get_efficiency_grade().value
        return grades
    
    def _detect_high_consumption(self, 
                                resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Detect high consumption areas.
        """
        high_areas = []
        
        for resource in resources:
            benchmark = self.resource_benchmarks.get(resource.resource_type.value, {})
            high_threshold = benchmark.get('high', 0)
            very_high_threshold = benchmark.get('very_high', 0)
            
            if resource.current_usage > very_high_threshold:
                high_areas.append({
                    'resource': resource.name,
                    'type': resource.resource_type.value,
                    'usage': resource.current_usage,
                    'unit': resource.unit,
                    'severity': 'very_high',
                    'recommendation': 'Immediate attention required',
                    'potential_savings': resource.current_usage - high_threshold
                })
            elif resource.current_usage > high_threshold:
                high_areas.append({
                    'resource': resource.name,
                    'type': resource.resource_type.value,
                    'usage': resource.current_usage,
                    'unit': resource.unit,
                    'severity': 'high',
                    'recommendation': 'Significant improvement possible',
                    'potential_savings': resource.current_usage - high_threshold
                })
        
        return sorted(high_areas, key=lambda x: x['usage'], reverse=True)
    
    def _calculate_optimization_potential(self, 
                                         resources: List[HouseholdResource]) -> Dict[str, float]:
        """
        Calculate optimization potential for each resource type.
        """
        potential = {}
        
        for resource in resources:
            key = resource.resource_type.value
            potential[key] = resource.calculate_optimization_potential()
        
        return potential
    
    def _compare_to_benchmarks(self, 
                              resources: List[HouseholdResource]) -> Dict[str, Dict[str, Any]]:
        """
        Compare resource usage to benchmarks.
        """
        comparison = {}
        
        for resource in resources:
            key = resource.resource_type.value
            benchmarks = self.resource_benchmarks.get(key, {})
            
            comparison[key] = {
                'current': resource.current_usage,
                'unit': resource.unit,
                'low': benchmarks.get('low', 0),
                'medium': benchmarks.get('medium', 0),
                'high': benchmarks.get('high', 0),
                'very_high': benchmarks.get('very_high', 0),
                'benchmark_level': self._get_benchmark_level(
                    resource.current_usage, benchmarks
                ),
                'above_benchmark': resource.current_usage > benchmarks.get('medium', 0),
                'gap_to_efficient': max(0, resource.current_usage - benchmarks.get('efficient', 0))
            }
        
        return comparison
    
    def _get_benchmark_level(self, value: float, benchmarks: Dict[str, float]) -> str:
        """
        Get benchmark level for a value.
        """
        if value <= benchmarks.get('low', 0):
            return 'low'
        elif value <= benchmarks.get('medium', 0):
            return 'medium'
        elif value <= benchmarks.get('high', 0):
            return 'high'
        else:
            return 'very_high'
    
    def _analyze_trends(self, 
                       resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Analyze consumption trends.
        """
        trends = {}
        
        for resource in resources:
            if not resource.historical_usage:
                continue
            
            history = resource.historical_usage[-12:]  # Last 12 months
            if len(history) < 2:
                continue
            
            values = [h.get('value', 0.0) for h in history]
            dates = [h.get('date', '') for h in history]
            
            if len(values) >= 2:
                first = values[0]
                last = values[-1]
                change = last - first
                change_pct = (change / (first + 0.001)) * 100 if first > 0 else 0
                
                trends[resource.resource_type.value] = {
                    'values': values,
                    'dates': dates,
                    'change': change,
                    'change_percentage': change_pct,
                    'direction': 'improving' if change_pct < 0 else 'declining',
                    'average': statistics.mean(values),
                    'min': min(values),
                    'max': max(values),
                    'volatility': statistics.stdev(values) if len(values) > 1 else 0
                }
        
        return trends
    
    def _detect_patterns(self, 
                        resources: List[HouseholdResource]) -> Dict[str, str]:
        """
        Detect consumption patterns.
        """
        patterns = {}
        
        for resource in resources:
            patterns[resource.resource_type.value] = resource.get_consumption_pattern().value
        
        return patterns
    
    def _detect_peak_usage(self, 
                          resources: List[HouseholdResource]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect peak usage times.
        """
        peak_usage = {}
        
        for resource in resources:
            if resource.peak_usage_times:
                peak_usage[resource.resource_type.value] = resource.peak_usage_times
        
        return peak_usage
    
    def _identify_quick_wins(self, 
                            resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Identify quick win optimization opportunities.
        """
        quick_wins = []
        
        for resource in resources:
            # Check for easy improvements
            if resource.efficiency_score < 60 and resource.optimization_potential > 30:
                quick_wins.append({
                    'resource': resource.name,
                    'type': resource.resource_type.value,
                    'current_efficiency': resource.efficiency_score,
                    'potential_improvement': resource.optimization_potential,
                    'estimated_savings': resource.estimated_savings,
                    'effort': 'low',
                    'impact': 'high',
                    'recommendation': self._get_quick_win_recommendation(resource)
                })
        
        return sorted(quick_wins, key=lambda x: x['potential_improvement'], reverse=True)[:5]
    
    def _get_quick_win_recommendation(self, resource: HouseholdResource) -> str:
        """
        Get quick win recommendation for a resource.
        """
        recommendations = {
            'energy': 'Switch to LED lighting and use smart power strips',
            'water': 'Fix leaky faucets and install low-flow showerheads',
            'waste': 'Start composting and increase recycling',
            'food': 'Plan meals and create shopping lists to reduce waste',
            'transportation': 'Combine trips and carpool when possible',
            'shopping': 'Buy in bulk and choose sustainable products'
        }
        return recommendations.get(resource.resource_type.value, 'Implement efficiency measures')
    
    def get_resource_efficiency_grades(self, 
                                      resources: List[HouseholdResource]) -> Dict[str, str]:
        """
        Get efficiency grades for resources.
        
        Args:
            resources: List of resources
        
        Returns:
            Dict: Efficiency grades
        """
        grades = {}
        for resource in resources:
            grades[resource.resource_type.value] = resource.get_efficiency_grade().value
        return grades
    
    def get_optimization_ranking(self, 
                                resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Rank resources by optimization potential.
        
        Args:
            resources: List of resources
        
        Returns:
            List[Dict]: Optimization ranking
        """
        rankings = []
        
        for resource in resources:
            rankings.append({
                'resource': resource.name,
                'type': resource.resource_type.value,
                'current_usage': resource.current_usage,
                'efficiency_score': resource.efficiency_score,
                'optimization_potential': resource.optimization_potential,
                'estimated_savings': resource.estimated_savings,
                'priority_score': resource.optimization_potential * (100 - resource.efficiency_score) / 100
            })
        
        return sorted(rankings, key=lambda x: x['priority_score'], reverse=True)