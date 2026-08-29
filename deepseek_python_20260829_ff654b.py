"""
Circular Economy & Waste Lifecycle Manager - Lifecycle Management
Manages item lifecycle transitions and tracking.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any, Set
from enum import Enum

from circular_economy.models import (
    CircularItem, LifecycleStage, LifecycleTransition,
    ItemCategory, ItemCondition
)

logger = logging.getLogger(__name__)


class LifecycleManager:
    """
    Manages the lifecycle of items.
    """
    
    def __init__(self):
        """Initialize the lifecycle manager."""
        self.valid_transitions = self._initialize_valid_transitions()
        logger.info("Lifecycle Manager initialized")
    
    def _initialize_valid_transitions(self) -> Dict[LifecycleStage, Set[LifecycleStage]]:
        """
        Initialize valid lifecycle stage transitions.
        """
        return {
            LifecycleStage.PURCHASE: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.REPAIR,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.ACTIVE_USE: {
                LifecycleStage.MAINTENANCE,
                LifecycleStage.REPAIR,
                LifecycleStage.REUSE,
                LifecycleStage.DONATION,
                LifecycleStage.RESALE,
                LifecycleStage.RECYCLING,
                LifecycleStage.DISPOSAL,
                LifecycleStage.REPURPOSED,
                LifecycleStage.UPGRADED,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.MAINTENANCE: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.REPAIR,
                LifecycleStage.REUSE,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.REPAIR: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.REUSE,
                LifecycleStage.DONATION,
                LifecycleStage.RESALE,
                LifecycleStage.RECYCLING,
                LifecycleStage.DISPOSAL,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.REUSE: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.REPAIR,
                LifecycleStage.DONATION,
                LifecycleStage.RESALE,
                LifecycleStage.RECYCLING,
                LifecycleStage.DISPOSAL,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.DONATION: {
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.RESALE: {
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.RECYCLING: {
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.COMPOSTING: {
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.DISPOSAL: {
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.UPGRADED: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.REPURPOSED: {
                LifecycleStage.ACTIVE_USE,
                LifecycleStage.ARCHIVED
            },
            LifecycleStage.ARCHIVED: set()
        }
    
    def transition_item(self, 
                       item: CircularItem,
                       to_stage: LifecycleStage,
                       reason: str = "",
                       performed_by: str = "",
                       notes: str = "") -> Optional[LifecycleTransition]:
        """
        Transition an item to a new lifecycle stage.
        
        Args:
            item: The item to transition
            to_stage: Target lifecycle stage
            reason: Reason for transition
            performed_by: User performing the transition
            notes: Additional notes
        
        Returns:
            LifecycleTransition: The transition record or None if invalid
        """
        from_stage = item.current_lifecycle_stage
        
        # Validate transition
        if not self.is_valid_transition(from_stage, to_stage):
            logger.warning(f"Invalid transition: {from_stage.value} -> {to_stage.value}")
            return None
        
        # Create transition record
        transition = LifecycleTransition(
            item_id=item.id,
            from_stage=from_stage,
            to_stage=to_stage,
            reason=reason,
            performed_by=performed_by,
            notes=notes
        )
        
        # Update item
        item.current_lifecycle_stage = to_stage
        item.lifecycle_history.append(transition)
        item.updated_at = datetime.now()
        
        # Update specific counters
        if to_stage == LifecycleStage.REPAIR:
            item.repair_count += 1
        elif to_stage == LifecycleStage.REUSE:
            item.reuse_count += 1
        
        logger.info(f"Item {item.name} transitioned: {from_stage.value} -> {to_stage.value}")
        
        return transition
    
    def is_valid_transition(self, 
                           from_stage: LifecycleStage,
                           to_stage: LifecycleStage) -> bool:
        """
        Check if a transition is valid.
        
        Args:
            from_stage: Current stage
            to_stage: Target stage
        
        Returns:
            bool: True if transition is valid
        """
        if from_stage not in self.valid_transitions:
            return False
        
        return to_stage in self.valid_transitions[from_stage]
    
    def get_possible_transitions(self, 
                                 item: CircularItem) -> List[LifecycleStage]:
        """
        Get possible lifecycle transitions for an item.
        
        Args:
            item: The item
        
        Returns:
            List[LifecycleStage]: Possible target stages
        """
        current = item.current_lifecycle_stage
        if current not in self.valid_transitions:
            return []
        
        return list(self.valid_transitions[current])
    
    def get_item_timeline(self, item: CircularItem) -> List[Dict[str, Any]]:
        """
        Get a timeline of item lifecycle events.
        
        Args:
            item: The item
        
        Returns:
            List[Dict]: Timeline events
        """
        timeline = []
        
        # Add purchase event
        if item.purchase_date:
            timeline.append({
                'date': item.purchase_date,
                'stage': LifecycleStage.PURCHASE.value,
                'event': f"Purchased {item.name}",
                'details': f"Price: ${item.purchase_price:.2f}"
            })
        
        # Add lifecycle transitions
        for transition in item.lifecycle_history:
            timeline.append({
                'date': transition.transition_date,
                'stage': transition.to_stage.value,
                'event': f"Transitioned to {transition.to_stage.value.replace('_', ' ').title()}",
                'details': transition.reason or transition.notes or "No details provided"
            })
        
        # Add repair events
        for repair in item.repair_history:
            timeline.append({
                'date': repair.repair_date,
                'stage': LifecycleStage.REPAIR.value,
                'event': f"Repaired {item.name}",
                'details': f"Cost: ${repair.repair_cost:.2f}, Outcome: {repair.outcome.value}"
            })
        
        # Add reuse events
        for reuse in item.reuse_history:
            timeline.append({
                'date': reuse.reuse_date,
                'stage': LifecycleStage.REUSE.value,
                'event': f"Reused {item.name}",
                'details': f"Type: {reuse.reuse_type}"
            })
        
        # Add donation events
        for donation in item.donation_history:
            timeline.append({
                'date': donation.donation_date,
                'stage': LifecycleStage.DONATION.value,
                'event': f"Donated {item.name}",
                'details': f"To: {donation.organization}"
            })
        
        # Add resale events
        for resale in item.resale_history:
            timeline.append({
                'date': resale.resale_date,
                'stage': LifecycleStage.RESALE.value,
                'event': f"Resold {item.name}",
                'details': f"Price: ${resale.sale_price:.2f}, Platform: {resale.platform}"
            })
        
        # Add recycling events
        for recycling in item.recycling_history:
            timeline.append({
                'date': recycling.recycling_date,
                'stage': LifecycleStage.RECYCLING.value,
                'event': f"Recycled {item.name}",
                'details': f"Method: {recycling.recycling_method.value}"
            })
        
        # Add disposal events
        for disposal in item.disposal_records:
            timeline.append({
                'date': disposal.disposal_date,
                'stage': LifecycleStage.DISPOSAL.value,
                'event': f"Disposed {item.name}",
                'details': f"Method: {disposal.disposal_method}"
            })
        
        # Sort by date
        timeline.sort(key=lambda x: x['date'])
        
        return timeline
    
    def get_lifecycle_summary(self, item: CircularItem) -> Dict[str, Any]:
        """
        Get a summary of item lifecycle.
        
        Args:
            item: The item
        
        Returns:
            Dict: Lifecycle summary
        """
        return {
            'item_name': item.name,
            'current_stage': item.current_lifecycle_stage.value,
            'age_days': item.get_age_days(),
            'age_years': item.get_age_years(),
            'remaining_lifetime_years': item.get_remaining_lifetime(),
            'total_transitions': len(item.lifecycle_history),
            'repair_count': item.repair_count,
            'reuse_count': item.reuse_count,
            'total_waste_avoided_kg': item.get_total_waste_avoided(),
            'stages_visited': self._get_visited_stages(item),
            'percent_lifetime_used': self._calculate_percent_lifetime_used(item),
            'circularity_score': item.circularity_score
        }
    
    def _get_visited_stages(self, item: CircularItem) -> List[str]:
        """
        Get all stages the item has visited.
        """
        stages = set()
        stages.add(item.current_lifecycle_stage.value)
        
        for transition in item.lifecycle_history:
            stages.add(transition.from_stage.value)
            stages.add(transition.to_stage.value)
        
        return list(stages)
    
    def _calculate_percent_lifetime_used(self, item: CircularItem) -> float:
        """
        Calculate percentage of lifetime used.
        """
        if item.estimated_lifetime_years <= 0:
            return 0.0
        
        age = item.get_age_years()
        return (age / item.estimated_lifetime_years) * 100
    
    def get_recommended_next_stage(self, item: CircularItem) -> Optional[LifecycleStage]:
        """
        Recommend the next lifecycle stage based on item condition.
        
        Args:
            item: The item
        
        Returns:
            Optional[LifecycleStage]: Recommended stage
        """
        current = item.current_lifecycle_stage
        
        if current in [LifecycleStage.ARCHIVED, LifecycleStage.DISPOSAL]:
            return None
        
        possible = self.get_possible_transitions(item)
        
        # If item is broken, recommend repair
        if item.current_condition in [ItemCondition.DAMAGED, ItemCondition.BROKEN]:
            if LifecycleStage.REPAIR in possible:
                return LifecycleStage.REPAIR
            elif LifecycleStage.RECYCLING in possible:
                return LifecycleStage.RECYCLING
        
        # If item is in good condition but not being used, recommend reuse or donation
        if (item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT] and
            current in [LifecycleStage.ACTIVE_USE, LifecycleStage.MAINTENANCE]):
            if LifecycleStage.REUSE in possible:
                return LifecycleStage.REUSE
            elif LifecycleStage.DONATION in possible:
                return LifecycleStage.DONATION
        
        # If item is worn, recommend resale or recycling
        if item.current_condition in [ItemCondition.WORN, ItemCondition.FAIR]:
            if LifecycleStage.RESALE in possible:
                return LifecycleStage.RESALE
            elif LifecycleStage.RECYCLING in possible:
                return LifecycleStage.RECYCLING
        
        # If item is old, recommend recycling
        if item.get_age_years() > item.estimated_lifetime_years * 0.8:
            if LifecycleStage.RECYCLING in possible:
                return LifecycleStage.RECYCLING
        
        return None
    
    def validate_item_condition(self, item: CircularItem) -> Dict[str, Any]:
        """
        Validate item condition and provide recommendations.
        
        Args:
            item: The item
        
        Returns:
            Dict: Condition assessment
        """
        assessment = {
            'item_name': item.name,
            'current_condition': item.current_condition.value,
            'condition_notes': item.condition_notes,
            'is_repairable': item.is_repairable,
            'repairability_score': item.repairability_score,
            'is_recyclable': item.is_recyclable,
            'recyclability_score': item.recyclability_score,
            'age_years': item.get_age_years(),
            'expected_lifetime_years': item.estimated_lifetime_years,
            'recommendations': []
        }
        
        # Condition-based recommendations
        if item.current_condition in [ItemCondition.DAMAGED, ItemCondition.BROKEN]:
            if item.is_repairable:
                assessment['recommendations'].append({
                    'action': 'repair',
                    'description': 'Item can be repaired',
                    'priority': 'high'
                })
            elif item.is_recyclable:
                assessment['recommendations'].append({
                    'action': 'recycle',
                    'description': 'Item cannot be repaired but can be recycled',
                    'priority': 'high'
                })
            else:
                assessment['recommendations'].append({
                    'action': 'disposal',
                    'description': 'Item cannot be repaired or recycled',
                    'priority': 'high'
                })
        
        if item.current_condition in [ItemCondition.GOOD, ItemCondition.EXCELLENT]:
            if item.get_age_years() > item.estimated_lifetime_years * 0.5:
                assessment['recommendations'].append({
                    'action': 'reuse_or_donate',
                    'description': 'Item is still in good condition but approaching end of expected lifetime',
                    'priority': 'medium'
                })
            else:
                assessment['recommendations'].append({
                    'action': 'continue_use',
                    'description': 'Item is in good condition and within expected lifetime',
                    'priority': 'low'
                })
        
        if item.current_condition in [ItemCondition.WORN, ItemCondition.FAIR]:
            assessment['recommendations'].append({
                'action': 'resell_or_recycle',
                'description': 'Item is worn but could be resold or recycled',
                'priority': 'medium'
            })
        
        return assessment