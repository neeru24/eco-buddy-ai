"""
Circular Economy & Waste Lifecycle Manager - Decision Engine
Compares lifecycle alternatives and recommends optimal paths.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from circular_economy.models import (
    CircularItem, LifecycleAlternative, LifecycleStage,
    ItemCondition, RepairOutcome
)

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    Compares lifecycle alternatives and recommends optimal paths.
    """
    
    def __init__(self):
        """Initialize the decision engine."""
        self.alternative_weights = {
            'repair': 0.30,
            'reuse': 0.25,
            'donate': 0.20,
            'resell': 0.15,
            'recycle': 0.10
        }
        logger.info("Decision Engine initialized")
    
    def compare_alternatives(self, item: CircularItem) -> List[LifecycleAlternative]:
        """
        Compare lifecycle alternatives for an item.
        
        Args:
            item: The item to analyze
        
        Returns:
            List[LifecycleAlternative]: Sorted alternatives
        """
        alternatives = []
        
        # Get current stage
        current = item.current_lifecycle_stage
        
        # Generate alternatives based on current stage
        if current in [LifecycleStage.ACTIVE_USE, LifecycleStage.MAINTENANCE]:
            alternatives.extend(self._generate_use_alternatives(item))
        elif current == LifecycleStage.PURCHASE:
            alternatives.extend(self._generate_purchase_alternatives(item))
        elif current in [LifecycleStage.REPAIR, LifecycleStage.REUSE]:
            alternatives.extend(self._generate_repair_alternatives(item))
        
        # Add disposal as baseline (if not already at disposal)
        if current != LifecycleStage.DISPOSAL:
            alternatives.append(self._create_disposal_alternative(item))
        
        # Calculate scores and sort
        for alt in alternatives:
            alt = self._score_alternative(alt, item)
        
        # Sort by circularity score (descending)
        alternatives.sort(key=lambda x: x.circularity_score, reverse=True)
        
        # Mark best option
        if alternatives:
            alternatives[0].is_best_option = True
        
        return alternatives
    
    def _generate_use_alternatives(self, item: CircularItem) -> List[LifecycleAlternative]:
        """
        Generate alternatives for items in active use.
        """
        alternatives = []
        
        # Repair alternative
        if item.is_repairable:
            repair_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='repair',
                description='Repair the item to extend its life',
                financial_cost=self._estimate_repair_cost(item),
                financial_benefit=item.current_value * 0.3 if item.current_value > 0 else 20,
                carbon_impact_kg=item.carbon_footprint_kg * 0.1,
                waste_impact_kg=item.weight_kg * 0.1
            )
            alternatives.append(repair_alt)
        
        # Reuse alternative
        if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT]:
            reuse_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='reuse',
                description='Find a new use for the item',
                financial_cost=0,
                financial_benefit=item.current_value * 0.2 if item.current_value > 0 else 10,
                carbon_impact_kg=item.carbon_footprint_kg * 0.05,
                waste_impact_kg=0
            )
            alternatives.append(reuse_alt)
        
        # Donate alternative
        if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT]:
            donate_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='donate',
                description='Donate to a charity',
                financial_cost=0,
                financial_benefit=item.current_value * 0.15 if item.current_value > 0 else 5,
                carbon_impact_kg=item.carbon_footprint_kg * 0.02,
                waste_impact_kg=0
            )
            alternatives.append(donate_alt)
        
        # Resell alternative
        if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT, ItemCondition.FAIR]:
            resell_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='resell',
                description='Sell the item',
                financial_cost=item.current_value * 0.1 if item.current_value > 0 else 2,
                financial_benefit=item.current_value * 0.5 if item.current_value > 0 else 10,
                carbon_impact_kg=item.carbon_footprint_kg * 0.03,
                waste_impact_kg=0
            )
            alternatives.append(resell_alt)
        
        # Recycle alternative
        if item.is_recyclable:
            recycle_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='recycle',
                description='Recycle the item',
                financial_cost=item.weight_kg * 0.5 if item.weight_kg > 0 else 5,
                financial_benefit=0,
                carbon_impact_kg=item.carbon_footprint_kg * 0.05,
                waste_impact_kg=item.weight_kg * 0.1
            )
            alternatives.append(recycle_alt)
        
        return alternatives
    
    def _generate_purchase_alternatives(self, item: CircularItem) -> List[LifecycleAlternative]:
        """
        Generate alternatives for newly purchased items.
        """
        alternatives = []
        
        # New vs refurbished comparison
        if item.purchase_price > 0:
            refurbished_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='refurbished',
                description='Consider refurbished version instead',
                financial_cost=item.purchase_price * 0.7,
                financial_benefit=item.purchase_price * 0.3,
                carbon_impact_kg=item.carbon_footprint_kg * 0.5
            )
            alternatives.append(refurbished_alt)
        
        # Rent/lease alternative
        rent_alt = LifecycleAlternative(
            item_id=item.id,
            alternative_type='rent',
            description='Rent or lease instead of buying',
            financial_cost=item.purchase_price * 0.2,
            financial_benefit=item.purchase_price * 0.5,
            carbon_impact_kg=item.carbon_footprint_kg * 0.3
        )
        alternatives.append(rent_alt)
        
        # Used alternative
        used_alt = LifecycleAlternative(
            item_id=item.id,
            alternative_type='used',
            description='Buy used instead of new',
            financial_cost=item.purchase_price * 0.5,
            financial_benefit=item.purchase_price * 0.5,
            carbon_impact_kg=item.carbon_footprint_kg * 0.4
        )
        alternatives.append(used_alt)
        
        return alternatives
    
    def _generate_repair_alternatives(self, item: CircularItem) -> List[LifecycleAlternative]:
        """
        Generate alternatives for items being repaired.
        """
        alternatives = []
        
        # DIY repair
        diy_alt = LifecycleAlternative(
            item_id=item.id,
            alternative_type='diy_repair',
            description='Repair yourself',
            financial_cost=self._estimate_repair_cost(item) * 0.5,
            financial_benefit=item.current_value * 0.2,
            carbon_impact_kg=item.carbon_footprint_kg * 0.05
        )
        alternatives.append(diy_alt)
        
        # Professional repair
        pro_alt = LifecycleAlternative(
            item_id=item.id,
            alternative_type='professional_repair',
            description='Use a professional repair service',
            financial_cost=self._estimate_repair_cost(item),
            financial_benefit=item.current_value * 0.3,
            carbon_impact_kg=item.carbon_footprint_kg * 0.08
        )
        alternatives.append(pro_alt)
        
        # Replace
        if item.current_value > 0:
            replace_alt = LifecycleAlternative(
                item_id=item.id,
                alternative_type='replace',
                description='Replace with a newer model',
                financial_cost=item.current_value * 0.8,
                financial_benefit=item.current_value * 0.2,
                carbon_impact_kg=item.carbon_footprint_kg * 0.5
            )
            alternatives.append(replace_alt)
        
        return alternatives
    
    def _create_disposal_alternative(self, item: CircularItem) -> LifecycleAlternative:
        """
        Create disposal baseline alternative.
        """
        return LifecycleAlternative(
            item_id=item.id,
            alternative_type='disposal',
            description='Dispose in landfill',
            financial_cost=item.weight_kg * 0.2 if item.weight_kg > 0 else 2,
            financial_benefit=0,
            carbon_impact_kg=item.carbon_footprint_kg * 0.2,
            water_impact_liters=item.water_footprint_liters * 0.1,
            waste_impact_kg=item.weight_kg
        )
    
    def _score_alternative(self, alt: LifecycleAlternative, item: CircularItem) -> LifecycleAlternative:
        """
        Score an alternative based on multiple factors.
        """
        # Calculate circularity score
        circularity_score = 0.0
        
        if alt.alternative_type == 'repair':
            circularity_score = 70 + (item.repairability_score * 0.3)
        elif alt.alternative_type == 'reuse':
            circularity_score = 80 + (item.current_condition.value * 10)
        elif alt.alternative_type == 'donate':
            circularity_score = 75
        elif alt.alternative_type == 'resell':
            circularity_score = 60 + (item.current_value / 100)
        elif alt.alternative_type == 'recycle':
            circularity_score = item.recyclability_score
        elif alt.alternative_type == 'disposal':
            circularity_score = 0
        else:
            circularity_score = 50
        
        alt.circularity_score = min(100, max(0, circularity_score))
        
        # Calculate feasibility
        feasibility = self._calculate_feasibility(alt, item)
        alt.feasibility_score = feasibility['score']
        alt.effort_required = feasibility['effort']
        
        # Calculate compared to disposal
        if alt.alternative_type != 'disposal':
            alt.compared_to_disposal = (alt.circularity_score / 100) * 100
        
        # Calculate net financial impact
        alt.net_financial_impact = alt.financial_benefit - alt.financial_cost
        
        # Calculate landfill diversion
        if alt.alternative_type == 'disposal':
            alt.landfill_diversion_kg = 0
        elif alt.alternative_type == 'recycle':
            alt.landfill_diversion_kg = item.weight_kg * 0.8
        else:
            alt.landfill_diversion_kg = item.weight_kg * 0.9
        
        return alt
    
    def _calculate_feasibility(self, alt: LifecycleAlternative, item: CircularItem) -> Dict[str, Any]:
        """
        Calculate feasibility of an alternative.
        """
        score = 50.0
        effort = "medium"
        
        if alt.alternative_type == 'repair':
            score = item.repairability_score
            effort = "high" if item.repairability_score < 50 else "medium"
        elif alt.alternative_type == 'reuse':
            score = 70 if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT] else 40
            effort = "low"
        elif alt.alternative_type == 'donate':
            score = 80 if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT] else 50
            effort = "medium"
        elif alt.alternative_type == 'resell':
            score = 60 if item.current_value > 10 else 30
            effort = "medium"
        elif alt.alternative_type == 'recycle':
            score = item.recyclability_score
            effort = "low"
        elif alt.alternative_type == 'disposal':
            score = 90
            effort = "low"
        
        return {
            'score': min(100, max(0, score)),
            'effort': effort
        }
    
    def _estimate_repair_cost(self, item: CircularItem) -> float:
        """Estimate repair cost for an item."""
        base_cost = item.current_value * 0.15 if item.current_value > 0 else 20.0
        
        if item.current_condition in [ItemCondition.POOR, ItemCondition.DAMAGED]:
            base_cost *= 1.5
        elif item.current_condition == ItemCondition.BROKEN:
            base_cost *= 2.0
        
        return round(base_cost, 2)
    
    def get_recommendation(self, item: CircularItem) -> Dict[str, Any]:
        """
        Get the best lifecycle recommendation for an item.
        
        Args:
            item: The item
        
        Returns:
            Dict: Recommendation
        """
        alternatives = self.compare_alternatives(item)
        
        if not alternatives:
            return {
                'recommendation': 'continue_use',
                'reason': 'Continue using the item',
                'confidence': 0.5
            }
        
        best = alternatives[0]
        
        # Get recommendation
        rec = {
            'recommendation': best.alternative_type,
            'reason': best.description,
            'confidence': best.circularity_score / 100,
            'savings': {
                'financial': best.net_financial_impact,
                'carbon': best.carbon_impact_kg * -1 if best.carbon_impact_kg > 0 else 0,
                'waste': best.landfill_diversion_kg
            },
            'feasibility': best.feasibility_score,
            'effort': best.effort_required,
            'alternatives': [
                {
                    'type': alt.alternative_type,
                    'score': alt.circularity_score,
                    'description': alt.description
                }
                for alt in alternatives[1:4]  # Top 3 alternatives
            ]
        }
        
        return rec