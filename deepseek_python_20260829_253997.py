"""
Circular Economy & Waste Lifecycle Manager - Reuse Manager
Manages reuse, donation, and resale of items.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from circular_economy.models import (
    CircularItem, ReuseRecord, DonationRecord, ResaleRecord,
    LifecycleStage, ItemCondition
)

logger = logging.getLogger(__name__)


class ReuseManager:
    """
    Manages reuse, donation, and resale of items.
    """
    
    def __init__(self):
        """Initialize the reuse manager."""
        logger.info("Reuse Manager initialized")
    
    def record_reuse(self, item: CircularItem, reuse_data: Dict[str, Any]) -> Optional[ReuseRecord]:
        """
        Record a reuse event for an item.
        
        Args:
            item: The item
            reuse_data: Reuse information
        
        Returns:
            ReuseRecord: Created reuse record
        """
        reuse = ReuseRecord(
            item_id=item.id,
            reuse_date=reuse_data.get('reuse_date', datetime.now()),
            reuse_type=reuse_data.get('reuse_type', 'personal'),
            new_owner_id=reuse_data.get('new_owner_id'),
            reuse_duration_days=reuse_data.get('reuse_duration_days', 0),
            description=reuse_data.get('description', ''),
            notes=reuse_data.get('notes', '')
        )
        
        # Calculate impact metrics
        impact = self._calculate_reuse_impact(item)
        reuse.carbon_saved_kg = impact['carbon_saved_kg']
        reuse.waste_avoided_kg = impact['waste_avoided_kg']
        reuse.financial_savings = impact['financial_savings']
        
        item.reuse_history.append(reuse)
        item.reuse_count += 1
        item.updated_at = datetime.now()
        
        # Update lifecycle stage if needed
        if item.current_lifecycle_stage != LifecycleStage.REUSE:
            from circular_economy.lifecycle import LifecycleManager
            lifecycle = LifecycleManager()
            lifecycle.transition_item(item, LifecycleStage.REUSE, "Reused item")
        
        logger.info(f"Recorded reuse for item {item.name}")
        
        return reuse
    
    def record_donation(self, item: CircularItem, donation_data: Dict[str, Any]) -> Optional[DonationRecord]:
        """
        Record a donation event for an item.
        
        Args:
            item: The item
            donation_data: Donation information
        
        Returns:
            DonationRecord: Created donation record
        """
        donation = DonationRecord(
            item_id=item.id,
            donation_date=donation_data.get('donation_date', datetime.now()),
            organization=donation_data.get('organization', ''),
            organization_type=donation_data.get('organization_type', 'charity'),
            tax_deductible=donation_data.get('tax_deductible', False),
            estimated_value=donation_data.get('estimated_value', item.current_value * 0.5),
            description=donation_data.get('description', ''),
            receipt_url=donation_data.get('receipt_url', ''),
            notes=donation_data.get('notes', '')
        )
        
        # Calculate impact metrics
        impact = self._calculate_donation_impact(item)
        donation.carbon_saved_kg = impact['carbon_saved_kg']
        donation.waste_avoided_kg = impact['waste_avoided_kg']
        
        item.donation_history.append(donation)
        item.updated_at = datetime.now()
        
        # Update lifecycle stage
        from circular_economy.lifecycle import LifecycleManager
        lifecycle = LifecycleManager()
        lifecycle.transition_item(item, LifecycleStage.DONATION, f"Donated to {donation.organization}")
        
        logger.info(f"Recorded donation for item {item.name}")
        
        return donation
    
    def record_resale(self, item: CircularItem, resale_data: Dict[str, Any]) -> Optional[ResaleRecord]:
        """
        Record a resale event for an item.
        
        Args:
            item: The item
            resale_data: Resale information
        
        Returns:
            ResaleRecord: Created resale record
        """
        sale_price = resale_data.get('sale_price', 0.0)
        fees = resale_data.get('fees', 0.0)
        shipping_cost = resale_data.get('shipping_cost', 0.0)
        
        resale = ResaleRecord(
            item_id=item.id,
            resale_date=resale_data.get('resale_date', datetime.now()),
            platform=resale_data.get('platform', ''),
            sale_price=sale_price,
            fees=fees,
            shipping_cost=shipping_cost,
            net_profit=sale_price - fees - shipping_cost,
            buyer_info=resale_data.get('buyer_info', ''),
            description=resale_data.get('description', ''),
            notes=resale_data.get('notes', '')
        )
        
        # Calculate impact metrics
        impact = self._calculate_resale_impact(item)
        resale.carbon_saved_kg = impact['carbon_saved_kg']
        resale.waste_avoided_kg = impact['waste_avoided_kg']
        
        item.resale_history.append(resale)
        item.updated_at = datetime.now()
        
        # Update lifecycle stage
        from circular_economy.lifecycle import LifecycleManager
        lifecycle = LifecycleManager()
        lifecycle.transition_item(item, LifecycleStage.RESALE, f"Resold on {resale.platform}")
        
        logger.info(f"Recorded resale for item {item.name} for ${sale_price:.2f}")
        
        return resale
    
    def _calculate_reuse_impact(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate impact of reuse.
        """
        # Estimate carbon saved (avoided new product manufacturing)
        if item.carbon_footprint_kg > 0:
            carbon_saved = item.carbon_footprint_kg * 0.8
        else:
            carbon_saved = 15.0
        
        # Estimate waste avoided
        if item.weight_kg > 0:
            waste_avoided = item.weight_kg * 0.9
        else:
            waste_avoided = 3.0
        
        # Estimate financial savings
        if item.current_value > 0:
            financial_savings = item.current_value * 0.5
        elif item.purchase_price > 0:
            financial_savings = item.purchase_price * 0.4
        else:
            financial_savings = 20.0
        
        return {
            'carbon_saved_kg': carbon_saved,
            'waste_avoided_kg': waste_avoided,
            'financial_savings': financial_savings
        }
    
    def _calculate_donation_impact(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate impact of donation.
        """
        # Estimate carbon saved
        if item.carbon_footprint_kg > 0:
            carbon_saved = item.carbon_footprint_kg * 0.7
        else:
            carbon_saved = 12.0
        
        # Estimate waste avoided
        if item.weight_kg > 0:
            waste_avoided = item.weight_kg * 0.8
        else:
            waste_avoided = 2.0
        
        return {
            'carbon_saved_kg': carbon_saved,
            'waste_avoided_kg': waste_avoided
        }
    
    def _calculate_resale_impact(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate impact of resale.
        """
        # Estimate carbon saved
        if item.carbon_footprint_kg > 0:
            carbon_saved = item.carbon_footprint_kg * 0.6
        else:
            carbon_saved = 10.0
        
        # Estimate waste avoided
        if item.weight_kg > 0:
            waste_avoided = item.weight_kg * 0.7
        else:
            waste_avoided = 2.0
        
        return {
            'carbon_saved_kg': carbon_saved,
            'waste_avoided_kg': waste_avoided
        }
    
    def get_reuse_statistics(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Get reuse statistics for a list of items.
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        total_reuse = sum(item.reuse_count for item in items)
        total_donations = sum(len(item.donation_history) for item in items)
        total_resales = sum(len(item.resale_history) for item in items)
        
        total_carbon_saved = 0.0
        total_waste_avoided = 0.0
        total_financial_recovery = 0.0
        
        for item in items:
            for reuse in item.reuse_history:
                total_carbon_saved += reuse.carbon_saved_kg
                total_waste_avoided += reuse.waste_avoided_kg
                total_financial_recovery += reuse.financial_savings
            
            for resale in item.resale_history:
                total_financial_recovery += resale.net_profit
        
        return {
            'total_reuse_events': total_reuse,
            'total_donations': total_donations,
            'total_resales': total_resales,
            'total_carbon_saved_kg': total_carbon_saved,
            'total_waste_avoided_kg': total_waste_avoided,
            'total_financial_recovery': total_financial_recovery,
            'landfill_diversion_kg': total_waste_avoided,
            'reuse_by_type': self._get_reuse_by_type(items)
        }
    
    def _get_reuse_by_type(self, items: List[CircularItem]) -> Dict[str, int]:
        """
        Group reuse events by type.
        """
        reuse_by_type = {}
        for item in items:
            for reuse in item.reuse_history:
                if reuse.reuse_type not in reuse_by_type:
                    reuse_by_type[reuse.reuse_type] = 0
                reuse_by_type[reuse.reuse_type] += 1
        
        return reuse_by_type
    
    def find_reusable_items(self, items: List[CircularItem]) -> List[CircularItem]:
        """
        Find items that are candidates for reuse.
        """
        reusable = []
        
        for item in items:
            # Check if item is in good condition and not already in reuse stage
            if (item.current_condition in [ItemCondition.EXCELLENT, ItemCondition.GOOD] and
                item.current_lifecycle_stage != LifecycleStage.REUSE and
                item.current_lifecycle_stage != LifecycleStage.DONATION):
                reusable.append(item)
        
        return reusable
    
    def suggest_reuse_options(self, item: CircularItem) -> List[Dict[str, Any]]:
        """
        Suggest reuse options for an item.
        """
        options = []
        
        # Check if item is in good condition
        if item.current_condition in [ItemCondition.EXCELLENT, ItemCondition.GOOD]:
            options.append({
                'option': 'personal_reuse',
                'description': 'Keep using the item or find a new use for it at home',
                'effort': 'low',
                'impact': 'medium'
            })
            
            options.append({
                'option': 'donate',
                'description': 'Donate to a charity or organization',
                'effort': 'medium',
                'impact': 'high'
            })
            
            options.append({
                'option': 'resell',
                'description': f'Sell on platforms like eBay, Facebook Marketplace, etc.',
                'effort': 'medium',
                'impact': 'high'
            })
        
        # Check if item is in fair condition
        if item.current_condition == ItemCondition.FAIR:
            options.append({
                'option': 'repair_then_reuse',
                'description': 'Repair the item before reusing or donating',
                'effort': 'high',
                'impact': 'high'
            })
            
            options.append({
                'option': 'recycle',
                'description': 'Recycle the item instead of disposal',
                'effort': 'low',
                'impact': 'medium'
            })
        
        # Add community options
        options.append({
            'option': 'community_share',
            'description': 'Share with neighbors or community groups',
            'effort': 'low',
            'impact': 'high'
        })
        
        # Add upcycling option
        options.append({
            'option': 'upcycle',
            'description': 'Transform into something new and useful',
            'effort': 'high',
            'impact': 'high'
        })
        
        return options