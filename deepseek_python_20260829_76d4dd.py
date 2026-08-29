"""
Circular Economy & Waste Lifecycle Manager - Recycling Manager
Manages recycling and disposal of items.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from circular_economy.models import (
    CircularItem, RecyclingRecord, DisposalRecord,
    RecyclingMethod, LifecycleStage, ItemCategory
)

logger = logging.getLogger(__name__)


class RecyclingManager:
    """
    Manages recycling and disposal of items.
    """
    
    def __init__(self):
        """Initialize the recycling manager."""
        self.recycling_guidance = self._initialize_recycling_guidance()
        logger.info("Recycling Manager initialized")
    
    def _initialize_recycling_guidance(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize recycling guidance for different materials and categories.
        """
        return {
            'electronics': {
                'methods': ['drop_off', 'mail_in', 'specialized'],
                'recyclable': True,
                'hazardous': True,
                'notes': 'Take to e-waste recycling center. Do not dispose in regular trash.'
            },
            'plastic': {
                'methods': ['curbside', 'drop_off'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Check local recycling guidelines. Rinse before recycling.'
            },
            'glass': {
                'methods': ['curbside', 'drop_off'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Do not break. Rinse and remove labels if possible.'
            },
            'paper': {
                'methods': ['curbside', 'drop_off'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Keep dry and clean. Remove plastic windows from envelopes.'
            },
            'metal': {
                'methods': ['curbside', 'drop_off'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Clean and separate different types of metal.'
            },
            'clothing': {
                'methods': ['drop_off', 'mail_in'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Donate or take to textile recycling facilities.'
            },
            'organic': {
                'methods': ['compost'],
                'recyclable': True,
                'hazardous': False,
                'notes': 'Compost food waste and organic materials.'
            },
            'hazardous': {
                'methods': ['specialized'],
                'recyclable': False,
                'hazardous': True,
                'notes': 'Must be disposed at specialized hazardous waste facilities.'
            }
        }
    
    def record_recycling(self, item: CircularItem, recycling_data: Dict[str, Any]) -> Optional[RecyclingRecord]:
        """
        Record recycling of an item.
        
        Args:
            item: The item
            recycling_data: Recycling information
        
        Returns:
            RecyclingRecord: Created recycling record
        """
        method = recycling_data.get('recycling_method', RecyclingMethod.CURBSIDE)
        
        recycling = RecyclingRecord(
            item_id=item.id,
            recycling_date=recycling_data.get('recycling_date', datetime.now()),
            recycling_method=method,
            facility_name=recycling_data.get('facility_name', ''),
            materials_recycled=recycling_data.get('materials_recycled', []),
            weight_recycled_kg=recycling_data.get('weight_recycled_kg', item.weight_kg),
            notes=recycling_data.get('notes', '')
        )
        
        # Calculate impact metrics
        impact = self._calculate_recycling_impact(item, method)
        recycling.carbon_saved_kg = impact['carbon_saved_kg']
        recycling.water_saved_liters = impact['water_saved_liters']
        recycling.energy_saved_kwh = impact['energy_saved_kwh']
        recycling.waste_avoided_kg = impact['waste_avoided_kg']
        
        item.recycling_history.append(recycling)
        item.updated_at = datetime.now()
        
        # Update lifecycle stage
        from circular_economy.lifecycle import LifecycleManager
        lifecycle = LifecycleManager()
        lifecycle.transition_item(item, LifecycleStage.RECYCLING, f"Recycled using {method.value}")
        
        logger.info(f"Recorded recycling for item {item.name}")
        
        return recycling
    
    def record_disposal(self, item: CircularItem, disposal_data: Dict[str, Any]) -> Optional[DisposalRecord]:
        """
        Record disposal of an item.
        
        Args:
            item: The item
            disposal_data: Disposal information
        
        Returns:
            DisposalRecord: Created disposal record
        """
        disposal = DisposalRecord(
            item_id=item.id,
            disposal_date=disposal_data.get('disposal_date', datetime.now()),
            disposal_method=disposal_data.get('disposal_method', 'landfill'),
            facility_name=disposal_data.get('facility_name', ''),
            weight_kg=disposal_data.get('weight_kg', item.weight_kg),
            notes=disposal_data.get('notes', '')
        )
        
        # Calculate impact
        impact = self._calculate_disposal_impact(item)
        disposal.carbon_footprint_kg = impact['carbon_footprint_kg']
        disposal.water_footprint_liters = impact['water_footprint_liters']
        
        item.disposal_records.append(disposal)
        item.updated_at = datetime.now()
        
        # Update lifecycle stage
        from circular_economy.lifecycle import LifecycleManager
        lifecycle = LifecycleManager()
        lifecycle.transition_item(item, LifecycleStage.DISPOSAL, f"Disposed using {disposal.disposal_method}")
        
        logger.info(f"Recorded disposal for item {item.name}")
        
        return disposal
    
    def _calculate_recycling_impact(self, item: CircularItem, method: RecyclingMethod) -> Dict[str, float]:
        """
        Calculate impact of recycling.
        """
        # Base carbon savings (avoided manufacturing)
        if item.carbon_footprint_kg > 0:
            carbon_saved = item.carbon_footprint_kg * 0.6
        else:
            carbon_saved = 5.0
        
        # Water savings
        if item.water_footprint_liters > 0:
            water_saved = item.water_footprint_liters * 0.5
        else:
            water_saved = 20.0
        
        # Energy savings
        if item.weight_kg > 0:
            energy_saved = item.weight_kg * 2.5  # kWh per kg
        else:
            energy_saved = 5.0
        
        # Waste avoided
        if item.weight_kg > 0:
            waste_avoided = item.weight_kg * 0.8
        else:
            waste_avoided = 1.0
        
        # Adjust based on method
        if method == RecyclingMethod.COMPOST:
            carbon_saved *= 0.8
            water_saved *= 0.7
        elif method == RecyclingMethod.SPECIALIZED:
            carbon_saved *= 0.9
            water_saved *= 0.8
        
        return {
            'carbon_saved_kg': carbon_saved,
            'water_saved_liters': water_saved,
            'energy_saved_kwh': energy_saved,
            'waste_avoided_kg': waste_avoided
        }
    
    def _calculate_disposal_impact(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate impact of disposal.
        """
        # Carbon footprint
        if item.carbon_footprint_kg > 0:
            carbon = item.carbon_footprint_kg * 0.2
        else:
            carbon = 2.0
        
        # Water footprint
        if item.water_footprint_liters > 0:
            water = item.water_footprint_liters * 0.1
        else:
            water = 5.0
        
        return {
            'carbon_footprint_kg': carbon,
            'water_footprint_liters': water
        }
    
    def get_recycling_guidance(self, item: CircularItem) -> Dict[str, Any]:
        """
        Get recycling guidance for an item.
        
        Args:
            item: The item
        
        Returns:
            Dict: Recycling guidance
        """
        guidance = {
            'item_name': item.name,
            'category': item.category.value,
            'materials': [m.material for m in item.materials],
            'recyclable': item.is_recyclable,
            'recyclability_score': item.recyclability_score,
            'methods': [],
            'steps': [],
            'notes': '',
            'warning': ''
        }
        
        # Check for specific material guidance
        for material in item.materials:
            material_guidance = self.recycling_guidance.get(material.material)
            if material_guidance:
                guidance['methods'].extend(material_guidance['methods'])
                if material_guidance.get('hazardous'):
                    guidance['warning'] = '⚠️ Contains hazardous materials. Handle with care.'
        
        # Category-specific guidance
        if item.category.value in self.recycling_guidance:
            category_guidance = self.recycling_guidance[item.category.value]
            guidance['notes'] = category_guidance.get('notes', '')
            
            if category_guidance.get('hazardous'):
                guidance['warning'] = '⚠️ This item may contain hazardous materials.'
        
        # Determine recycling steps
        if item.is_recyclable:
            guidance['steps'] = self._get_recycling_steps(item)
        else:
            guidance['steps'] = [
                'Check if item can be donated or reused instead',
                'Check local recycling guidelines',
                'If not recyclable, consider specialized recycling programs'
            ]
        
        # Remove duplicates
        guidance['methods'] = list(set(guidance['methods']))
        
        return guidance
    
    def _get_recycling_steps(self, item: CircularItem) -> List[str]:
        """
        Get recycling steps for an item.
        """
        steps = []
        
        # Prepare item
        steps.append('1. Clean and prepare the item for recycling')
        
        # Check materials
        if any(m.material == 'electronics' for m in item.materials):
            steps.append('2. Remove batteries and store separately')
        
        # Check for hazardous materials
        if any(m.is_hazardous for m in item.materials):
            steps.append('3. Identify hazardous materials and handle with care')
        
        # Determine recycling method
        if item.category.value == 'electronics':
            steps.append('4. Take to an e-waste recycling center')
            steps.append('5. Consider mail-in recycling programs')
        elif any(m.material == 'plastic' for m in item.materials):
            steps.append('4. Check local curbside recycling guidelines')
            steps.append('5. Rinse and dry before placing in recycling bin')
        elif any(m.material == 'organic' for m in item.materials):
            steps.append('4. Add to compost pile or green waste bin')
        else:
            steps.append('4. Follow local recycling guidelines')
        
        steps.append('✅ Confirm item is properly recycled')
        
        return steps
    
    def calculate_landfill_diversion(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Calculate landfill diversion for a list of items.
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        total_weight = 0.0
        diverted_weight = 0.0
        recycled_weight = 0.0
        composted_weight = 0.0
        disposed_weight = 0.0
        
        for item in items:
            total_weight += item.weight_kg
            
            # Check if item has been recycled
            if item.recycling_history:
                for recycling in item.recycling_history:
                    diverted_weight += recycling.weight_recycled_kg
                    recycled_weight += recycling.weight_recycled_kg
            
            # Check if item has been composted
            for record in item.disposal_records:
                if record.disposal_method == 'compost':
                    diverted_weight += record.weight_kg
                    composted_weight += record.weight_kg
                else:
                    disposed_weight += record.weight_kg
        
        diversion_rate = (diverted_weight / total_weight * 100) if total_weight > 0 else 0
        
        return {
            'total_weight_kg': total_weight,
            'diverted_weight_kg': diverted_weight,
            'recycled_weight_kg': recycled_weight,
            'composted_weight_kg': composted_weight,
            'disposed_weight_kg': disposed_weight,
            'diversion_rate_percentage': diversion_rate,
            'landfill_avoided_kg': diverted_weight
        }
    
    def get_recycling_statistics(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Get recycling statistics for a list of items.
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        total_recycled = sum(len(item.recycling_history) for item in items)
        total_disposed = sum(len(item.disposal_records) for item in items)
        
        total_carbon_saved = 0.0
        total_energy_saved = 0.0
        total_waste_avoided = 0.0
        
        for item in items:
            for recycling in item.recycling_history:
                total_carbon_saved += recycling.carbon_saved_kg
                total_energy_saved += recycling.energy_saved_kwh
                total_waste_avoided += recycling.waste_avoided_kg
        
        return {
            'total_recycled_items': total_recycled,
            'total_disposed_items': total_disposed,
            'recycling_rate': (total_recycled / (total_recycled + total_disposed) * 100) if (total_recycled + total_disposed) > 0 else 0,
            'total_carbon_saved_kg': total_carbon_saved,
            'total_energy_saved_kwh': total_energy_saved,
            'total_waste_avoided_kg': total_waste_avoided,
            'by_method': self._get_recycling_by_method(items)
        }
    
    def _get_recycling_by_method(self, items: List[CircularItem]) -> Dict[str, int]:
        """
        Group recycling events by method.
        """
        recycling_by_method = {}
        for item in items:
            for recycling in item.recycling_history:
                method = recycling.recycling_method.value
                if method not in recycling_by_method:
                    recycling_by_method[method] = 0
                recycling_by_method[method] += 1
        
        return recycling_by_method