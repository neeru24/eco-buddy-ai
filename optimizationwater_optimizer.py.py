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
        self.water_usage_patterns = self._initialize_usage_patterns()
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
                'saving_measure': 'Install low-flow showerhead',
                'potential_savings': 40.0
            },
            'toilet': {
                'avg_liters_per_flush': 6.0,
                'efficient_liters_per_flush': 3.0,
                'flushes_per_day': 5.0,
                'saving_measure': 'Install dual-flush toilet',
                'potential_savings': 60.0
            },
            'faucet': {
                'avg_liters_per_minute': 8.0,
                'efficient_liters_per_minute': 4.0,
                'avg_minutes_per_day': 10.0,
                'saving_measure': 'Install aerators',
                'potential_savings': 40.0
            },
            'washing_machine': {
                'avg_liters_per_load': 80.0,
                'efficient_liters_per_load': 50.0,
                'loads_per_week': 5.0,
                'saving_measure': 'Use front-loading machine',
                'potential_savings': 30.0
            },
            'dishwasher': {
                'avg_liters_per_load': 40.0,
                'efficient_liters_per_load': 25.0,
                'loads_per_week': 3.0,
                'saving_measure': 'Use efficient dishwasher',
                'potential_savings': 20.0
            },
            'garden': {
                'avg_liters_per_sq_meter': 10.0,
                'efficient_liters_per_sq_meter': 5.0,
                'saving_measure': 'Install drip irrigation',
                'potential_savings': 50.0
            },
            'leaks': {
                'avg_liters_per_day': 20.0,
                'efficient_liters_per_day': 0.0,
                'saving_measure': 'Fix all leaks promptly',
                'potential_savings': 100.0
            },
            'pool': {
                'avg_liters_per_month': 1000.0,
                'efficient_liters_per_month': 500.0,
                'saving_measure': 'Use pool cover and reduce evaporation',
                'potential_savings': 50.0
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
                'payback_months': 2,
                'impact': 'high'
            },
            {
                'measure': 'Install faucet aerators',
                'savings_liters_per_day': 30.0,
                'cost': 10.0,
                'effort': 'low',
                'payback_months': 1,
                'impact': 'medium'
            },
            {
                'measure': 'Fix all leaks',
                'savings_liters_per_day': 40.0,
                'cost': 50.0,
                'effort': 'medium',
                'payback_months': 2,
                'impact': 'high'
            },
            {
                'measure': 'Install dual-flush toilets',
                'savings_liters_per_day': 60.0,
                'cost': 300.0,
                'effort': 'high',
                'payback_months': 18,
                'impact': 'high'
            },
            {
                'measure': 'Install rain barrel',
                'savings_liters_per_day': 80.0,
                'cost': 100.0,
                'effort': 'medium',
                'payback_months': 6,
                'impact': 'high'
            },
            {
                'measure': 'Install drip irrigation',
                'savings_liters_per_day': 100.0,
                'cost': 150.0,
                'effort': 'medium',
                'payback_months': 8,
                'impact': 'high'
            },
            {
                'measure': 'Use dishwasher full loads only',
                'savings_liters_per_day': 20.0,
                'cost': 0.0,
                'effort': 'low',
                'payback_months': 0,
                'impact': 'medium'
            },
            {
                'measure': 'Use washing machine full loads only',
                'savings_liters_per_day': 30.0,
                'cost': 0.0,
                'effort': 'low',
                'payback_months': 0,
                'impact': 'medium'
            },
            {
                'measure': 'Install pool cover',
                'savings_liters_per_day': 30.0,
                'cost': 80.0,
                'effort': 'low',
                'payback_months': 4,
                'impact': 'medium'
            },
            {
                'measure': 'Use greywater for garden',
                'savings_liters_per_day': 60.0,
                'cost': 200.0,
                'effort': 'high',
                'payback_months': 12,
                'impact': 'high'
            }
        ]
    
    def _initialize_usage_patterns(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize usage pattern detection.
        """
        return {
            'morning_peak': {'hours': (6, 9), 'label': 'Morning peak usage'},
            'evening_peak': {'hours': (18, 21), 'label': 'Evening peak usage'},
            'weekend_pattern': {'days': ['Saturday', 'Sunday'], 'label': 'Weekend usage pattern'}
        }
    
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
        optimization.usage_change_percentage = (
            (optimization.usage_difference / (optimization.baseline_usage + 0.001)) * 100
        )
        
        # Fixture breakdown
        optimization.fixture_usage = {
            r.name: r.current_usage for r in water_resources
        }
        optimization.fixture_efficiency = {
            r.name: r.calculate_efficiency_score() for r in water_resources
        }
        
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
        
        # Calculate implementation costs
        optimization.estimated_implementation_cost = self._calculate_implementation_cost(water_resources)
        optimization.payback_period_months = self._calculate_payback_period(
            optimization.estimated_implementation_cost,
            optimization.estimated_cost_savings
        )
        
        # Generate implementation phases
        optimization.implementation_phases = self._generate_implementation_phases(
            water_resources, optimization.reduction_opportunities
        )
        
        # Generate recommendations
        optimization.recommendations = self._generate_recommendations(water_resources)
        optimization.priority_recommendations = self._prioritize_recommendations(
            optimization.recommendations
        )
        
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
        
        total_daily_usage = sum(r.current_usage for r in resources) / 30
        expected_daily = avg_liters_per_person_day * household_size
        
        if total_daily_usage > expected_daily * 1.5:
            high_areas.append({
                'area': 'Overall',
                'current_daily': total_daily_usage,
                'expected_daily': expected_daily,
                'excess': total_daily_usage - expected_daily,
                'excess_percentage': ((total_daily_usage - expected_daily) / (expected_daily + 0.001)) * 100,
                'recommendation': 'Reduce overall water usage through conservation'
            })
        
        for resource in resources:
            benchmark = self.water_usage_benchmarks.get(resource.name.lower(), {})
            
            if benchmark:
                daily_usage = resource.current_usage / 30
                benchmark_daily = benchmark.get('avg_liters_per_minute', 0) * benchmark.get('avg_minutes_per_day', 0)
                
                if benchmark_daily > 0 and daily_usage > benchmark_daily * 1.5:
                    high_areas.append({
                        'area': resource.name,
                        'current_daily': daily_usage,
                        'expected_daily': benchmark_daily,
                        'excess': daily_usage - benchmark_daily,
                        'excess_percentage': ((daily_usage - benchmark_daily) / (benchmark_daily + 0.001)) * 100,
                        'recommendation': benchmark.get('saving_measure', 'Conserve water'),
                        'saving_measure': benchmark.get('saving_measure', ''),
                        'potential_savings': benchmark.get('potential_savings', 0)
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
                        'savings_percentage': (savings / (current_daily + 0.001)) * 100,
                        'measure': benchmark.get('saving_measure', 'Conserve water'),
                        'cost': self._estimate_measure_cost(resource),
                        'payback_months': self._calculate_measure_payback(resource, savings)
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
                'impact': measure['impact']
            })
        
        return sorted(improvements, key=lambda x: x['daily_savings'], reverse=True)
    
    def _estimate_measure_cost(self, resource: HouseholdResource) -> float:
        """
        Estimate cost of a water-saving measure.
        """
        name = resource.name.lower()
        
        if 'shower' in name:
            return 30.0
        elif 'toilet' in name:
            return 300.0
        elif 'faucet' in name:
            return 10.0
        elif 'washing' in name:
            return 500.0
        elif 'dishwasher' in name:
            return 500.0
        elif 'garden' in name or 'irrigation' in name:
            return 150.0
        elif 'pool' in name:
            return 80.0
        else:
            return 50.0
    
    def _calculate_measure_payback(self, resource: HouseholdResource, savings: float) -> int:
        """
        Calculate payback period for a water-saving measure.
        """
        cost = self._estimate_measure_cost(resource)
        monthly_savings = savings * 30 * 0.005  # Assuming $0.005 per liter
        
        if monthly_savings > 0:
            return int(cost / monthly_savings)
        return 12
    
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
        return water_savings * 0.005
    
    def _calculate_environmental_impact(self, 
                                      resources: List[HouseholdResource]) -> float:
        """
        Calculate environmental impact of water usage.
        """
        water_savings = self._calculate_water_savings(resources)
        return water_savings * 0.001
    
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
        
        # Phase 1: Quick wins
        quick_wins = [o for o in opportunities if o.get('payback_months', 99) < 3]
        if quick_wins:
            phases.append({
                'phase': 1,
                'name': 'Quick Water Savings',
                'description': 'Implement low-cost, high-impact water-saving measures',
                'items': [o['resource'] for o in quick_wins[:3]],
                'estimated_cost': sum(o.get('cost', 0) for o in quick_wins[:3]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in quick_wins[:3])
            })
        
        # Phase 2: Medium investments
        medium = [o for o in opportunities if 3 <= o.get('payback_months', 99) <= 12]
        if medium:
            phases.append({
                'phase': 2,
                'name': 'Medium Water Investments',
                'description': 'Implement cost-effective water-saving measures',
                'items': [o['resource'] for o in medium[:3]],
                'estimated_cost': sum(o.get('cost', 0) for o in medium[:3]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in medium[:3])
            })
        
        # Phase 3: Major upgrades
        major = [o for o in opportunities if o.get('payback_months', 99) > 12]
        if major:
            phases.append({
                'phase': 3,
                'name': 'Major Water Upgrades',
                'description': 'Implement high-impact water-saving upgrades',
                'items': [o['resource'] for o in major[:2]],
                'estimated_cost': sum(o.get('cost', 0) for o in major[:2]),
                'estimated_savings': sum(o.get('potential_savings', 0) for o in major[:2])
            })
        
        return phases
    
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
                        'effort': 'medium',
                        'cost': self._estimate_measure_cost(resource)
                    })
        
        # Add general recommendations
        general_recs = [
            {
                'area': 'General',
                'recommendation': 'Take shorter showers (5 minutes or less)',
                'potential_savings': 20,
                'priority': 'high',
                'effort': 'low',
                'cost': 0
            },
            {
                'area': 'General',
                'recommendation': 'Turn off tap while brushing teeth',
                'potential_savings': 10,
                'priority': 'medium',
                'effort': 'low',
                'cost': 0
            },
            {
                'area': 'General',
                'recommendation': 'Use a bucket to collect shower water for plants',
                'potential_savings': 15,
                'priority': 'medium',
                'effort': 'low',
                'cost': 5
            },
            {
                'area': 'General',
                'recommendation': 'Check for and fix all water leaks',
                'potential_savings': 40,
                'priority': 'critical',
                'effort': 'medium',
                'cost': 50
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
            efficiency = (1 - (total_usage - total_baseline) / (total_baseline + 0.001)) * 100
            efficiency = max(0, min(100, efficiency))
        else:
            efficiency = 50.0
        
        grade = self._get_grade(efficiency)
        
        return {
            'score': efficiency,
            'grade': grade,
            'total_usage': total_usage,
            'total_baseline': total_baseline,
            'savings_potential': max(0, total_usage - total_baseline),
            'fixture_scores': {r.name: r.efficiency_score for r in resources}
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