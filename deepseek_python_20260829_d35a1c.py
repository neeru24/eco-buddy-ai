"""
Circular Economy & Waste Lifecycle Manager - Analytics
Analytics and reporting for circular economy data.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from collections import defaultdict

from circular_economy.models import (
    CircularItem, CircularityScore, HouseholdCircularity,
    WasteReduction, LifecycleStage, ItemCategory
)

logger = logging.getLogger(__name__)


class CircularAnalytics:
    """
    Analytics and reporting for circular economy data.
    """
    
    def __init__(self):
        """Initialize the analytics engine."""
        logger.info("Circular Analytics initialized")
    
    def analyze_waste_reduction(self, items: List[CircularItem]) -> WasteReduction:
        """
        Analyze waste reduction from circular actions.
        
        Args:
            items: List of items
        
        Returns:
            WasteReduction: Waste reduction metrics
        """
        reduction = WasteReduction(
            household_id=items[0].household_id if items else ""
        )
        
        if not items:
            return reduction
        
        # Calculate total waste
        total_weight = sum(item.weight_kg for item in items)
        reduction.total_waste_kg = total_weight
        
        # Calculate diverted waste
        diverted_by_action = defaultdict(float)
        
        for item in items:
            # Repairs
            for repair in item.repair_history:
                diverted_by_action['repair'] += repair.waste_avoided_kg
            
            # Reuse
            for reuse in item.reuse_history:
                diverted_by_action['reuse'] += reuse.waste_avoided_kg
            
            # Donation
            for donation in item.donation_history:
                diverted_by_action['donation'] += donation.waste_avoided_kg
            
            # Resale
            for resale in item.resale_history:
                diverted_by_action['resale'] += resale.waste_avoided_kg
            
            # Recycling
            for recycling in item.recycling_history:
                diverted_by_action['recycling'] += recycling.waste_avoided_kg
        
        # Set reduction metrics
        reduction.repair_diverted_kg = diverted_by_action['repair']
        reduction.reuse_diverted_kg = diverted_by_action['reuse']
        reduction.donation_diverted_kg = diverted_by_action['donation']
        reduction.resale_diverted_kg = diverted_by_action['resale']
        reduction.recycling_diverted_kg = diverted_by_action['recycling']
        
        reduction.total_waste_diverted_kg = sum(diverted_by_action.values())
        reduction.diversion_rate = (reduction.total_waste_diverted_kg / total_weight * 100) if total_weight > 0 else 0
        
        # Landfill avoided
        reduction.landfill_avoided_kg = reduction.total_waste_diverted_kg
        reduction.landfill_avoided_percentage = (reduction.landfill_avoided_kg / total_weight * 100) if total_weight > 0 else 0
        
        # Environmental impact
        reduction.carbon_saved_kg = self._calculate_total_carbon_saved(items)
        reduction.water_saved_liters = self._calculate_total_water_saved(items)
        reduction.energy_saved_kwh = self._calculate_total_energy_saved(items)
        
        return reduction
    
    def get_category_analytics(self, items: List[CircularItem]) -> Dict[str, Dict[str, Any]]:
        """
        Get analytics by category.
        
        Args:
            items: List of items
        
        Returns:
            Dict: Category analytics
        """
        category_analytics = {}
        
        for item in items:
            category = item.category.value
            if category not in category_analytics:
                category_analytics[category] = {
                    'count': 0,
                    'total_weight': 0.0,
                    'avg_circularity': 0.0,
                    'repairs': 0,
                    'reuses': 0,
                    'recycles': 0,
                    'donations': 0,
                    'resales': 0,
                    'circular_items': 0
                }
            
            stats = category_analytics[category]
            stats['count'] += 1
            stats['total_weight'] += item.weight_kg
            stats['avg_circularity'] += item.circularity_score
            stats['repairs'] += item.repair_count
            stats['reuses'] += item.reuse_count
            stats['recycles'] += len(item.recycling_history)
            stats['donations'] += len(item.donation_history)
            stats['resales'] += len(item.resale_history)
            
            if item.circularity_score >= 50:
                stats['circular_items'] += 1
        
        # Calculate averages
        for category, stats in category_analytics.items():
            if stats['count'] > 0:
                stats['avg_circularity'] = stats['avg_circularity'] / stats['count']
                stats['circularity_percentage'] = (stats['circular_items'] / stats['count'] * 100)
        
        return category_analytics
    
    def get_time_series_analytics(self, items: List[CircularItem]) -> Dict[str, Dict[str, Any]]:
        """
        Get time series analytics for circular actions.
        
        Args:
            items: List of items
        
        Returns:
            Dict: Time series analytics
        """
        # Group by month
        monthly_data = defaultdict(lambda: {
            'repairs': 0,
            'reuses': 0,
            'recycles': 0,
            'donations': 0,
            'resales': 0,
            'carbon_saved': 0.0,
            'waste_diverted': 0.0
        })
        
        for item in items:
            # Repairs
            for repair in item.repair_history:
                month_key = repair.repair_date.strftime('%Y-%m')
                monthly_data[month_key]['repairs'] += 1
                monthly_data[month_key]['carbon_saved'] += repair.carbon_saved_kg
                monthly_data[month_key]['waste_diverted'] += repair.waste_avoided_kg
            
            # Reuses
            for reuse in item.reuse_history:
                month_key = reuse.reuse_date.strftime('%Y-%m')
                monthly_data[month_key]['reuses'] += 1
                monthly_data[month_key]['carbon_saved'] += reuse.carbon_saved_kg
                monthly_data[month_key]['waste_diverted'] += reuse.waste_avoided_kg
            
            # Recycling
            for recycling in item.recycling_history:
                month_key = recycling.recycling_date.strftime('%Y-%m')
                monthly_data[month_key]['recycles'] += 1
                monthly_data[month_key]['carbon_saved'] += recycling.carbon_saved_kg
                monthly_data[month_key]['waste_diverted'] += recycling.waste_avoided_kg
        
        # Sort by date
        sorted_months = sorted(monthly_data.items())
        
        return {
            'months': [m[0] for m in sorted_months],
            'data': [m[1] for m in sorted_months]
        }
    
    def get_impact_summary(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Get overall impact summary.
        
        Args:
            items: List of items
        
        Returns:
            Dict: Impact summary
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        total_items = len(items)
        circular_items = sum(1 for item in items if item.circularity_score >= 50)
        
        total_carbon_saved = self._calculate_total_carbon_saved(items)
        total_waste_diverted = sum(item.get_total_waste_avoided() for item in items)
        total_financial_savings = sum(self._calculate_total_financial_savings(item) for item in items)
        
        avg_circularity = statistics.mean([item.circularity_score for item in items])
        
        return {
            'total_items': total_items,
            'circular_items': circular_items,
            'circularity_percentage': (circular_items / total_items * 100),
            'average_circularity_score': avg_circularity,
            'total_carbon_saved_kg': total_carbon_saved,
            'total_waste_diverted_kg': total_waste_diverted,
            'total_financial_savings': total_financial_savings,
            'landfill_diversion_rate': (total_waste_diverted / sum(item.weight_kg for item in items) * 100) if sum(item.weight_kg for item in items) > 0 else 0,
            'grade': self._get_impact_grade(avg_circularity)
        }
    
    def get_member_contributions(self, items: List[CircularItem]) -> Dict[str, Dict[str, Any]]:
        """
        Get contributions by member.
        
        Args:
            items: List of items
        
        Returns:
            Dict: Member contributions
        """
        contributions = {}
        
        for item in items:
            if not item.user_id:
                continue
            
            if item.user_id not in contributions:
                contributions[item.user_id] = {
                    'items': 0,
                    'repairs': 0,
                    'reuses': 0,
                    'donations': 0,
                    'resales': 0,
                    'recycles': 0,
                    'carbon_saved': 0.0,
                    'waste_diverted': 0.0,
                    'financial_savings': 0.0
                }
            
            contrib = contributions[item.user_id]
            contrib['items'] += 1
            contrib['repairs'] += item.repair_count
            contrib['reuses'] += item.reuse_count
            contrib['donations'] += len(item.donation_history)
            contrib['resales'] += len(item.resale_history)
            contrib['recycles'] += len(item.recycling_history)
            contrib['carbon_saved'] += self._calculate_total_carbon_saved(item)
            contrib['waste_diverted'] += item.get_total_waste_avoided()
            contrib['financial_savings'] += self._calculate_total_financial_savings(item)
        
        return contributions
    
    def _calculate_total_carbon_saved(self, items: List[CircularItem]) -> float:
        """Calculate total carbon saved."""
        total = 0.0
        for item in items:
            for repair in item.repair_history:
                total += repair.carbon_saved_kg
            for reuse in item.reuse_history:
                total += reuse.carbon_saved_kg
            for recycling in item.recycling_history:
                total += recycling.carbon_saved_kg
        return total
    
    def _calculate_total_water_saved(self, items: List[CircularItem]) -> float:
        """Calculate total water saved."""
        total = 0.0
        for item in items:
            for recycling in item.recycling_history:
                total += recycling.water_saved_liters
        return total
    
    def _calculate_total_energy_saved(self, items: List[CircularItem]) -> float:
        """Calculate total energy saved."""
        total = 0.0
        for item in items:
            for recycling in item.recycling_history:
                total += recycling.energy_saved_kwh
        return total
    
    def _calculate_total_financial_savings(self, item: CircularItem) -> float:
        """Calculate total financial savings for an item."""
        total = 0.0
        for repair in item.repair_history:
            total += repair.financial_savings
        for reuse in item.reuse_history:
            total += reuse.financial_savings
        for resale in item.resale_history:
            total += resale.net_profit
        return total
    
    def _get_impact_grade(self, score: float) -> str:
        """Get impact grade based on average score."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        else:
            return "Needs Improvement"
    
    def get_trend_analytics(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Get trend analytics for circular actions.
        
        Args:
            items: List of items
        
        Returns:
            Dict: Trend analytics
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        # Get time series data
        time_series = self.get_time_series_analytics(items)
        
        if not time_series['months']:
            return {'message': 'No historical data available'}
        
        # Calculate trends
        months = time_series['months']
        data = time_series['data']
        
        # Calculate growth rates
        if len(months) >= 2:
            first_month = data[0]
            last_month = data[-1]
            
            repair_growth = ((last_month['repairs'] - first_month['repairs']) / (first_month['repairs'] + 1) * 100)
            reuse_growth = ((last_month['reuses'] - first_month['reuses']) / (first_month['reuses'] + 1) * 100)
            recycle_growth = ((last_month['recycles'] - first_month['recycles']) / (first_month['recycles'] + 1) * 100)
            carbon_growth = ((last_month['carbon_saved'] - first_month['carbon_saved']) / (first_month['carbon_saved'] + 1) * 100)
            waste_growth = ((last_month['waste_diverted'] - first_month['waste_diverted']) / (first_month['waste_diverted'] + 1) * 100)
        else:
            repair_growth = 0
            reuse_growth = 0
            recycle_growth = 0
            carbon_growth = 0
            waste_growth = 0
        
        return {
            'months': months,
            'trends': {
                'repairs': repair_growth,
                'reuses': reuse_growth,
                'recycles': recycle_growth,
                'carbon_saved': carbon_growth,
                'waste_diverted': waste_growth
            },
            'latest_month': months[-1] if months else None,
            'total_months': len(months),
            'overall_trend': 'improving' if repair_growth > 0 or reuse_growth > 0 else 'declining'
        }