"""
Smart Household Resource Optimization Engine - Water Optimizer
Optimizes household water consumption.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    WaterOptimization, HouseholdResource, ResourceType
)

logger = logging.getLogger(__name__)


class WaterOptimizer:
    """
    Analyzes and optimizes household water consumption.
    """
    
    def __init__(self):
        """Initialize the water optimizer."""
        self.water_usage_benchmarks = self._initialize_water_benchmarks()
        self.water_saving_measures = self._initialize_water_measures()
        logger.info("Water Optimizer initialized")
    
    def _initialize_water_benchmarks(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize water usage benchmarks.
        """
        return {
            'shower': {
                'avg_liters_per_minute': 12.0,
                'efficient_liters_per_minute': 7.0,
                'avg_minutes_per_day': 8.0,
                'saving_measure': 'Install low-flow showerhead'
            },
            'toilet': {
                'avg_liters_per_flush': 6.0,
                'efficient_liters_per_flush': 3.0,
                'flushes_per_day': 5.0,
                'saving_measure': 'Install dual-flush toilet'
            },
            'faucet': {
                'avg_liters_per_minute': 8.0,
                'efficient_liters_per_minute': 4.0,
                'avg_minutes_per_day': 10.0,
                'saving_measure': 'Install aerators'
            },
            'washing_machine': {
                'avg_liters_per_load': 80.0,
                'efficient_liters_per_load': 50.0,
                'loads_per_week': 5.0,
                'saving_measure': 'Use front-loading machine'
            },
            'dishwasher': {
                'avg_liters_per_load': 40.0,
                'efficient_liters_per_load': 25.0,
                'loads_per_week': 3.0,
                'saving_measure': 'Use efficient dishwasher'
            },
            'garden': {
                'avg_liters_per_sq_meter': 10.0,
                'efficient_liters_per_sq_meter': 5.0,
                'saving_measure': 'Install drip irrigation'
            },
            'leaks': {
                'avg_liters_per_day': 20.0,
                'efficient_liters_per_day': 0.0,
                'saving_measure': 'Fix all leaks promptly'
            }
        }
    
    def _initialize_water_measures(self) -> List[Dict[str, Any]]:
        """
        Initialize water saving measures.
        """
        return [
            {
                'measure': 'Install low-flow showerheads',
                'savings_liters_per_day': 50.0,
                'cost': 30.0,
                'effort': 'low',
                'payback_months': 2
            },
            {
                'measure': 'Install faucet aerators',
                'savings_liters_per_day': 30.0,
                'cost': 10.0,
                'effort': 'low',
                'payback_months': 1
            },
            {
                'measure': 'Fix all leaks',
                'savings_liters_per_day': 40.0,
                'cost': 50.0,
                'effort': 'medium',
                'payback_months': 2
            },
            {
                'measure': 'Install dual-flush toilets',
                'savings_liters_per_day': 60.0,
                'cost': 300.0,
                'effort': 'high',
                'payback_months': 18
            },
            {
                'measure': 'Install rain barrel',
                'savings_liters_per_day': 80.0,
                'cost': 100.0,
                'effort': 'medium',
                'payback_months': 6
            },
            {
                'measure': 'Install drip irrigation',
                'savings_liters_per_day': 100.0,
                'cost': 150.0,
                'effort': 'medium',
                'payback_months': 8
            },
            {
                'measure': 'Use dishwasher full loads only',
                'savings_liters_per_day': 20.0,
                'cost': 0.0,
                'effort': 'low',
                'payback_months': 0
            },
            {
                'measure': 'Use washing machine full loads only',
                'savings_liters_per_day': 30.0,
                'cost': 0.0,
                'effort': 'low',
                'payback_months': 0
            }
        ]
    
    def analyze_water_consumption(self, 
                                 resources: List[HouseholdResource],
                                 household_size: int) -> WaterOptimization:
        """
        Analyze household water consumption.
        
        Args:
            resources: List of resources
            household_size: Number of household members
        
        Returns:
            WaterOptimization: Water optimization analysis
        """
        optimization = WaterOptimization(
            household_id=resources[0].household_id if resources else ""
        )
        
        # Get water resources
        water_resources = [r for r in resources if r.resource_type == ResourceType.WATER]
        
        if not water_resources:
            logger.warning("No water resources found")
            return optimization
        
        # Calculate totals
        optimization.total_usage = sum(r.current_usage for r in water_resources)
        optimization.baseline_usage = sum(r.baseline_usage for r in water_resources)
        optimization.usage_difference = (
            optimization.total_usage - optimization.baseline_usage
        )
        
        # Detect high usage areas
        optimization.high_usage_areas = self._detect_high_usage(water_resources, household_size)
        
        # Detect peak usage times
        optimization.peak_usage_times = self._detect_peak_times(water_resources)
        
        # Find reduction opportunities
        optimization.reduction_opportunities = self._find_reduction_opportunities(water_resources)
        
        # Find efficiency improvements
        optimization.efficiency_improvements = self._find_efficiency_improvements(water_resources)
        
        # Calculate savings estimates
        optimization.estimated_water_savings = self._calculate_water_savings(water_resources)
        optimization.estimated_cost_savings = self._calculate_cost_savings(water_resources)
        optimization.estimated_environmental_impact = self._calculate_environmental_impact(water_resources)
        
        # Generate recommendations
        optimization.recommendations = self._generate_recommendations(water_resources)
        optimization.priority_recommendations = self._prioritize_recommendations(optimization.recommendations)
        
        return optimization
    
    def _detect_high_usage(self, 
                          resources: List[HouseholdResource],
                          household_size: int) -> List[Dict[str, Any]]:
        """
        Detect high water usage areas.
        """
        high_areas = []
        
        # National average water usage per person per day
        avg_liters_per_person_day = 150.0
        
        total_daily_usage = sum(r.current_usage for r in resources) / 30  # Monthly to daily
        expected_daily = avg_liters_per_person_day * household_size
        
        if total_daily_usage > expected_daily * 1.5:
            high_areas.append({
                'area': 'Overall',
                'current_daily': total_daily_usage,
                'expected_daily': expected_daily,
                'excess': total_daily_usage - expected_daily,
                'excess_percentage': ((total_daily_usage - expected_daily) / expected_daily) * 100,
                'recommendation': 'Reduce overall water usage through conservation'
            })
        
        for resource in resources:
            benchmark = self.water_usage_benchmarks.get(resource.name.lower(), {})
            
            if benchmark:
                # Calculate daily usage
                daily_usage = resource.current_usage / 30
                benchmark_daily = benchmark.get('avg_liters_per_minute', 0) * benchmark.get('avg_minutes_per_day', 0)
                
                if benchmark_daily > 0 and daily_usage > benchmark_daily * 1.5:
                    high_areas.append({
                        'area': resource.name,
                        'current_daily': daily_usage,
                        'expected_daily': benchmark_daily,
                        'excess': daily_usage - benchmark_daily,
                        'excess_percentage': ((daily_usage - benchmark_daily) / benchmark_daily) * 100,
                        'recommendation': benchmark.get('saving_measure', 'Conserve water'),
                        'saving_measure': benchmark.get('saving_measure', '')
                    })
        
        return sorted(high_areas, key=lambda x: x.get('excess', 0), reverse=True)
    
    def _detect_peak_times(self, 
                          resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Detect peak water usage times.
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
                    peak_hours = sorted_hours[:2]
                    
                    peaks.append({
                        'resource': resource.name,
                        'peak_hours': [{'hour': h, 'usage': v} for h, v in peak_hours],
                        'recommendation': 'Shift water usage to off-peak hours'
                    })
        
        return peaks
    
    def _find_reduction_opportunities(self, 
                                     resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find water reduction opportunities.
        """
        opportunities = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.water_usage_benchmarks.get(name, {})
            efficient_value = benchmark.get('efficient_liters_per_minute', 0)
            avg_value = benchmark.get('avg_liters_per_minute', 0)
            
            if efficient_value > 0 and avg_value > 0:
                current_daily = resource.current_usage / 30
                efficient_daily = efficient_value * benchmark.get('avg_minutes_per_day', 0)
                
                if current_daily > efficient_daily:
                    savings = current_daily - efficient_daily
                    
                    opportunities.append({
                        'resource': resource.name,
                        'current_daily': current_daily,
                        'efficient_daily': efficient_daily,
                        'potential_savings': savings,
                        'savings_percentage': (savings / current_daily) * 100,
                        'measure': benchmark.get('saving_measure', 'Conserve water')
                    })
        
        return sorted(opportunities, key=lambda x: x['potential_savings'], reverse=True)
    
    def _find_efficiency_improvements(self, 
                                     resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Find water efficiency improvements.
        """
        improvements = []
        
        for measure in self.water_saving_measures:
            improvements.append({
                'measure': measure['measure'],
                'daily_savings': measure['savings_liters_per_day'],
                'monthly_savings': measure['savings_liters_per_day'] * 30,
                'cost': measure['cost'],
                'effort': measure['effort'],
                'payback_months': measure['payback_months'],
                'impact': 'high' if measure['savings_liters_per_day'] > 50 else 'medium'
            })
        
        return sorted(improvements, key=lambda x: x['daily_savings'], reverse=True)
    
    def _calculate_water_savings(self, 
                                resources: List[HouseholdResource]) -> float:
        """
        Calculate potential water savings.
        """
        total_savings = 0.0
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.water_usage_benchmarks.get(name, {})
            efficient_value = benchmark.get('efficient_liters_per_minute', 0)
            avg_value = benchmark.get('avg_liters_per_minute', 0)
            
            if efficient_value > 0 and avg_value > 0:
                current_monthly = resource.current_usage
                efficient_monthly = efficient_value * benchmark.get('avg_minutes_per_day', 0) * 30
                
                if current_monthly > efficient_monthly:
                    total_savings += current_monthly - efficient_monthly
        
        return total_savings
    
    def _calculate_cost_savings(self, 
                               resources: List[HouseholdResource]) -> float:
        """
        Calculate potential cost savings.
        """
        water_savings = self._calculate_water_savings(resources)
        # Assuming average water cost of $0.005 per liter
        return water_savings * 0.005
    
    def _calculate_environmental_impact(self, 
                                      resources: List[HouseholdResource]) -> float:
        """
        Calculate environmental impact of water usage.
        """
        water_savings = self._calculate_water_savings(resources)
        # Rough estimate: 1 liter water saved = 0.001 kg CO2 saved
        return water_savings * 0.001
    
    def _generate_recommendations(self, 
                                 resources: List[HouseholdResource]) -> List[Dict[str, Any]]:
        """
        Generate water optimization recommendations.
        """
        recommendations = []
        
        for resource in resources:
            name = resource.name.lower()
            benchmark = self.water_usage_benchmarks.get(name, {})
            
            if benchmark:
                current_daily = resource.current_usage / 30
                benchmark_daily = benchmark.get('avg_liters_per_minute', 0) * benchmark.get('avg_minutes_per_day', 0)
                
                if benchmark_daily > 0 and current_daily > benchmark_daily:
                    recommendations.append({
                        'area': resource.name,
                        'current_daily': current_daily,
                        'benchmark': benchmark_daily,
                        'recommendation': benchmark.get('saving_measure', 'Conserve water'),
                        'potential_savings': current_daily - benchmark_daily,
                        'priority': 'high' if (current_daily - benchmark_daily) > 30 else 'medium',
                        'effort': 'medium'
                    })
        
        # Add general recommendations
        general_recs = [
            {
                'area': 'General',
                'recommendation': 'Take shorter showers (5 minutes or less)',
                'potential_savings': 20,
                'priority': 'high',
                'effort': 'low'
            },
            {
                'area': 'General',
                'recommendation': 'Turn off tap while brushing teeth',
                'potential_savings': 10,
                'priority': 'medium',
                'effort': 'low'
            },
            {
                'area': 'General',
                'recommendation': 'Use a bucket to collect shower water for plants',
                'potential_savings': 15,
                'priority': 'medium',
                'effort': 'low'
            },
            {
                'area': 'General',
                'recommendation': 'Install a water meter to track usage',
                'potential_savings': 5,
                'priority': 'low',
                'effort': 'medium'
            }
        ]
        
        recommendations.extend(general_recs)
        
        return sorted(recommendations, key=lambda x: x.get('potential_savings', 0), reverse=True)
    
    def _prioritize_recommendations(self, 
                                   recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Prioritize water recommendations.
        """
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return sorted(recommendations, key=lambda x: priority_order.get(x.get('priority', 'medium'), 2))
    
    def get_water_score(self, 
                       resources: List[HouseholdResource]) -> Dict[str, Any]:
        """
        Get overall water score.
        
        Args:
            resources: List of water resources
        
        Returns:
            Dict: Water score
        """
        if not resources:
            return {'score': 0, 'grade': 'F'}
        
        total_usage = sum(r.current_usage for r in resources)
        total_baseline = sum(r.baseline_usage for r in resources)
        
        if total_baseline > 0:
            efficiency = (1 - (total_usage - total_baseline) / total_baseline) * 100
            efficiency = max(0, min(100, efficiency))
        else:
            efficiency = 50.0
        
        return {
            'score': efficiency,
            'grade': self._get_grade(efficiency),
            'total_usage': total_usage,
            'total_baseline': total_baseline,
            'savings_potential': max(0, total_usage - total_baseline)
        }
    
    def _get_grade(self, score: float) -> str:
        """Get grade from score."""
        if score >= 85:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 55:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"