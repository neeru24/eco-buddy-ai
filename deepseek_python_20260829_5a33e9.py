"""
Circular Economy & Waste Lifecycle Manager - Circularity Scorer
Calculates circularity scores for items and households.
"""

import logging
import statistics
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from circular_economy.models import (
    CircularItem, CircularityScore, HouseholdCircularity,
    LifecycleStage, ItemCondition
)

logger = logging.getLogger(__name__)


class CircularityScorer:
    """
    Calculates circularity scores for items and households.
    """
    
    def __init__(self):
        """Initialize the circularity scorer."""
        self.weight_factors = {
            'reuse': 0.30,
            'repair': 0.25,
            'recycle': 0.20,
            'donate': 0.15,
            'resale': 0.10
        }
        logger.info("Circularity Scorer initialized")
    
    def calculate_item_circularity(self, item: CircularItem) -> CircularityScore:
        """
        Calculate circularity score for a single item.
        
        Args:
            item: The item to score
        
        Returns:
            CircularityScore: Circularity score
        """
        score = CircularityScore(
            item_id=item.id
        )
        
        # Calculate component scores
        score.reuse_score = self._calculate_reuse_score(item)
        score.repair_score = self._calculate_repair_score(item)
        score.recycle_score = self._calculate_recycle_score(item)
        score.waste_reduction_score = self._calculate_waste_reduction_score(item)
        
        # Calculate overall score
        score.overall_circularity_score = (
            score.reuse_score * self.weight_factors['reuse'] +
            score.repair_score * self.weight_factors['repair'] +
            score.recycle_score * self.weight_factors['recycle'] +
            score.waste_reduction_score * 0.10
        )
        
        # Add metrics
        score.landfill_diversion_kg = item.landfill_avoided_kg
        score.landfill_diversion_percentage = self._calculate_diversion_percentage(item)
        score.carbon_saved_kg = self._calculate_total_carbon_saved(item)
        score.financial_savings = self._calculate_total_financial_savings(item)
        
        # Add event counts
        score.reuse_events = item.reuse_count
        score.repair_events = item.repair_count
        score.recycle_events = len(item.recycling_history)
        score.donation_events = len(item.donation_history)
        score.resale_events = len(item.resale_history)
        
        # Store on item
        item.circularity_score = score.overall_circularity_score
        
        return score
    
    def calculate_household_circularity(self, items: List[CircularItem], 
                                       household_id: str) -> HouseholdCircularity:
        """
        Calculate circularity score for a household.
        
        Args:
            items: List of items in the household
            household_id: Household ID
        
        Returns:
            HouseholdCircularity: Household circularity metrics
        """
        household = HouseholdCircularity(
            household_id=household_id,
            total_items=len(items)
        )
        
        if not items:
            return household
        
        # Calculate circular items count
        circular_items = 0
        for item in items:
            if item.circularity_score >= 50:
                circular_items += 1
            # Update category metrics
            category = item.category.value
            if category not in household.category_metrics:
                household.category_metrics[category] = {
                    'count': 0,
                    'circular_items': 0,
                    'total_score': 0.0
                }
            household.category_metrics[category]['count'] += 1
            if item.circularity_score >= 50:
                household.category_metrics[category]['circular_items'] += 1
            household.category_metrics[category]['total_score'] += item.circularity_score
        
        household.circular_items = circular_items
        household.circularity_percentage = (circular_items / len(items) * 100) if items else 0
        
        # Calculate action metrics
        household.total_reuse = sum(item.reuse_count for item in items)
        household.total_repair = sum(item.repair_count for item in items)
        household.total_recycle = sum(len(item.recycling_history) for item in items)
        household.total_donate = sum(len(item.donation_history) for item in items)
        household.total_resale = sum(len(item.resale_history) for item in items)
        
        # Calculate impact metrics
        household.total_landfill_diverted_kg = sum(item.landfill_avoided_kg for item in items)
        household.total_carbon_saved_kg = sum(self._calculate_total_carbon_saved(item) for item in items)
        household.total_financial_savings = sum(self._calculate_total_financial_savings(item) for item in items)
        
        # Calculate scores
        household.household_circularity_score = statistics.mean(
            [item.circularity_score for item in items]
        ) if items else 0
        
        household.waste_reduction_score = self._calculate_household_waste_reduction(items)
        
        return household
    
    def _calculate_reuse_score(self, item: CircularItem) -> float:
        """Calculate reuse score for an item."""
        score = 0.0
        
        # Check if item has been reused
        if item.reuse_count > 0:
            score += min(50, item.reuse_count * 10)
        
        # Check if item is reusable
        if item.current_lifecycle_stage in [LifecycleStage.REUSE, LifecycleStage.ACTIVE_USE]:
            score += 20
        
        # Check condition
        if item.current_condition in [ItemCondition.EXCELLENT, ItemCondition.GOOD]:
            score += 20
        elif item.current_condition == ItemCondition.FAIR:
            score += 10
        
        # Check age
        age_ratio = item.get_age_years() / item.estimated_lifetime_years if item.estimated_lifetime_years > 0 else 0
        if age_ratio < 0.3:
            score += 10
        elif age_ratio < 0.6:
            score += 5
        
        return min(100, score)
    
    def _calculate_repair_score(self, item: CircularItem) -> float:
        """Calculate repair score for an item."""
        score = 0.0
        
        # Check if item has been repaired
        if item.repair_count > 0:
            score += min(40, item.repair_count * 20)
        
        # Check repairability
        score += item.repairability_score * 0.3
        
        # Check repair history quality
        for repair in item.repair_history:
            if repair.outcome.value == 'successful':
                score += 10
                if repair.repair_quality_score > 70:
                    score += 10
        
        # Check if repair parts are available
        if item.repair_parts_available:
            score += 10
        
        # Check if repair instructions are available
        if item.repair_instructions_available:
            score += 10
        
        return min(100, score)
    
    def _calculate_recycle_score(self, item: CircularItem) -> float:
        """Calculate recycle score for an item."""
        score = 0.0
        
        # Check if item has been recycled
        if len(item.recycling_history) > 0:
            score += 30
        
        # Check recyclability
        score += item.recyclability_score * 0.4
        
        # Check materials recyclability
        if item.materials:
            recyclable_materials = sum(1 for m in item.materials if m.is_recyclable)
            total_materials = len(item.materials)
            if total_materials > 0:
                score += (recyclable_materials / total_materials) * 30
        
        # Check if recycled materials used
        if any(m.is_recycled for m in item.materials):
            score += 10
        
        return min(100, score)
    
    def _calculate_waste_reduction_score(self, item: CircularItem) -> float:
        """Calculate waste reduction score for an item."""
        score = 0.0
        
        # Check landfill diversion
        if item.landfill_avoided_kg > 0:
            score += min(50, item.landfill_avoided_kg * 5)
        
        # Check if item avoided disposal
        if item.current_lifecycle_stage != LifecycleStage.DISPOSAL:
            score += 20
        
        # Check if item has been diverted through circular actions
        if item.reuse_count > 0 or item.repair_count > 0:
            score += 20
        
        # Check if item is currently being used
        if item.current_lifecycle_stage in [LifecycleStage.ACTIVE_USE, LifecycleStage.REUSE]:
            score += 10
        
        return min(100, score)
    
    def _calculate_diversion_percentage(self, item: CircularItem) -> float:
        """Calculate landfill diversion percentage for an item."""
        if item.weight_kg <= 0:
            return 0.0
        
        diverted = item.landfill_avoided_kg
        return (diverted / item.weight_kg * 100) if item.weight_kg > 0 else 0
    
    def _calculate_total_carbon_saved(self, item: CircularItem) -> float:
        """Calculate total carbon saved from all circular actions."""
        total = 0.0
        
        # From repairs
        for repair in item.repair_history:
            total += repair.carbon_saved_kg
        
        # From reuse
        for reuse in item.reuse_history:
            total += reuse.carbon_saved_kg
        
        # From recycling
        for recycling in item.recycling_history:
            total += recycling.carbon_saved_kg
        
        return total
    
    def _calculate_total_financial_savings(self, item: CircularItem) -> float:
        """Calculate total financial savings from all circular actions."""
        total = 0.0
        
        # From repairs
        for repair in item.repair_history:
            total += repair.financial_savings
        
        # From reuse
        for reuse in item.reuse_history:
            total += reuse.financial_savings
        
        # From resale
        for resale in item.resale_history:
            total += resale.net_profit
        
        return total
    
    def _calculate_household_waste_reduction(self, items: List[CircularItem]) -> float:
        """Calculate household waste reduction score."""
        if not items:
            return 0.0
        
        total_waste = sum(item.weight_kg for item in items)
        total_diverted = sum(item.landfill_avoided_kg for item in items)
        
        if total_waste == 0:
            return 0.0
        
        return (total_diverted / total_waste * 100)
    
    def get_circularity_grade(self, score: float) -> str:
        """
        Get circularity grade based on score.
        
        Args:
            score: Circularity score (0-100)
        
        Returns:
            str: Grade (A+, A, B, C, D, F)
        """
        if score >= 95:
            return "A+"
        elif score >= 85:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"
    
    def get_circularity_color(self, score: float) -> str:
        """
        Get color for circularity score.
        
        Args:
            score: Circularity score (0-100)
        
        Returns:
            str: Color code
        """
        if score >= 75:
            return "#28a745"  # Green
        elif score >= 50:
            return "#ffc107"  # Yellow
        elif score >= 25:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red
    
    def get_circularity_level(self, score: float) -> str:
        """
        Get circularity level description.
        
        Args:
            score: Circularity score (0-100)
        
        Returns:
            str: Level description
        """
        if score >= 80:
            return "Exceptional Circularity"
        elif score >= 60:
            return "Good Circularity"
        elif score >= 40:
            return "Moderate Circularity"
        elif score >= 20:
            return "Low Circularity"
        else:
            return "Needs Improvement"
    
    def get_improvement_suggestions(self, item: CircularItem) -> List[str]:
        """
        Get suggestions for improving circularity score.
        
        Args:
            item: The item
        
        Returns:
            List[str]: Improvement suggestions
        """
        suggestions = []
        
        # Reuse suggestions
        if item.reuse_count == 0:
            suggestions.append("Find new ways to reuse this item instead of discarding it.")
        
        # Repair suggestions
        if item.repair_count == 0 and item.is_repairable:
            suggestions.append("Consider repairing this item to extend its life.")
        
        # Recycle suggestions
        if len(item.recycling_history) == 0 and item.is_recyclable:
            suggestions.append("Recycle this item when it reaches end of life.")
        
        # Donation suggestions
        if len(item.donation_history) == 0 and item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT]:
            suggestions.append("Consider donating this item to someone who needs it.")
        
        # Resale suggestions
        if len(item.resale_history) == 0 and item.current_value > 10:
            suggestions.append("You could resell this item to recover some value.")
        
        # Condition suggestions
        if item.current_condition in [ItemCondition.POOR, ItemCondition.DAMAGED]:
            suggestions.append("Improve the condition of this item through repair or maintenance.")
        
        # Lifetime suggestions
        if item.get_age_years() < item.estimated_lifetime_years * 0.3:
            suggestions.append("This item has plenty of life left. Keep using it!")
        elif item.get_age_years() > item.estimated_lifetime_years * 0.7:
            suggestions.append("This item is approaching end of life. Plan for its circular transition.")
        
        return suggestions[:5]  # Return top 5 suggestions