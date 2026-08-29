"""
Circular Economy & Waste Lifecycle Manager - Repair Analysis
Analyzes repair options and compares repair vs replace.
"""

import logging
import statistics
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple

from circular_economy.models import (
    CircularItem, RepairRecord, RepairOutcome, ItemCondition,
    LifecycleStage
)

logger = logging.getLogger(__name__)


class RepairAnalyzer:
    """
    Analyzes repair options for items.
    """
    
    def __init__(self):
        """Initialize the repair analyzer."""
        self.repair_factors = self._initialize_repair_factors()
        logger.info("Repair Analyzer initialized")
    
    def _initialize_repair_factors(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize repair factors for different categories.
        """
        return {
            'electronics': {
                'repairability_base': 60,
                'parts_availability': 0.6,
                'complexity_factor': 0.7,
                'cost_factor': 0.8
            },
            'appliances': {
                'repairability_base': 65,
                'parts_availability': 0.7,
                'complexity_factor': 0.6,
                'cost_factor': 0.7
            },
            'furniture': {
                'repairability_base': 75,
                'parts_availability': 0.8,
                'complexity_factor': 0.5,
                'cost_factor': 0.6
            },
            'clothing': {
                'repairability_base': 80,
                'parts_availability': 0.9,
                'complexity_factor': 0.4,
                'cost_factor': 0.5
            },
            'footwear': {
                'repairability_base': 70,
                'parts_availability': 0.7,
                'complexity_factor': 0.5,
                'cost_factor': 0.6
            },
            'vehicles': {
                'repairability_base': 55,
                'parts_availability': 0.7,
                'complexity_factor': 0.8,
                'cost_factor': 0.8
            },
            'tools': {
                'repairability_base': 70,
                'parts_availability': 0.8,
                'complexity_factor': 0.5,
                'cost_factor': 0.6
            }
        }
    
    def analyze_repair(self, item: CircularItem) -> Dict[str, Any]:
        """
        Analyze repair options for an item.
        
        Args:
            item: The item to analyze
        
        Returns:
            Dict: Repair analysis results
        """
        analysis = {
            'item_name': item.name,
            'is_repairable': item.is_repairable,
            'repairability_score': item.repairability_score,
            'repair_parts_available': item.repair_parts_available,
            'repair_instructions_available': item.repair_instructions_available,
            'repair_cost_estimate': self._estimate_repair_cost(item),
            'repair_vs_replace_analysis': self._repair_vs_replace_analysis(item),
            'environmental_savings': self._calculate_environmental_savings(item),
            'financial_savings': self._calculate_financial_savings(item),
            'difficulty_rating': self._assess_repair_difficulty(item),
            'time_required_hours': self._estimate_repair_time(item),
            'recommendation': self._generate_repair_recommendation(item)
        }
        
        return analysis
    
    def _estimate_repair_cost(self, item: CircularItem) -> float:
        """
        Estimate repair cost for an item.
        """
        base_cost = item.current_value * 0.15 if item.current_value > 0 else 20.0
        
        # Adjust based on condition
        if item.current_condition in [ItemCondition.POOR, ItemCondition.DAMAGED]:
            base_cost *= 1.5
        elif item.current_condition == ItemCondition.BROKEN:
            base_cost *= 2.0
        
        # Adjust based on category
        category_key = item.category.value
        if category_key in self.repair_factors:
            factor = self.repair_factors[category_key]['cost_factor']
            base_cost *= factor
        
        # Adjust based on repairability
        if item.repairability_score > 70:
            base_cost *= 0.8
        elif item.repairability_score < 40:
            base_cost *= 1.3
        
        return round(base_cost, 2)
    
    def _repair_vs_replace_analysis(self, item: CircularItem) -> Dict[str, Any]:
        """
        Compare repair vs replacement options.
        """
        repair_cost = self._estimate_repair_cost(item)
        replace_cost = item.current_value * 0.8 if item.current_value > 0 else 100.0
        
        # Estimate new item cost
        if item.purchase_price > 0:
            # Adjust for inflation
            years_old = item.get_age_years()
            replace_cost = item.purchase_price * (1 + 0.03 * years_old)
        
        # Calculate savings
        savings = replace_cost - repair_cost
        savings_percentage = (savings / replace_cost * 100) if replace_cost > 0 else 0
        
        # Environmental comparison
        carbon_repair = self._estimate_carbon_impact(repair_cost, 'repair')
        carbon_replace = self._estimate_carbon_impact(replace_cost, 'replace')
        carbon_savings = carbon_replace - carbon_repair
        
        return {
            'repair_cost': repair_cost,
            'replace_cost': replace_cost,
            'financial_savings': savings,
            'savings_percentage': savings_percentage,
            'carbon_savings_kg': carbon_savings,
            'is_repair_cheaper': repair_cost < replace_cost,
            'payback_period_months': self._calculate_payback_period(item, repair_cost, replace_cost),
            'recommendation': 'repair' if repair_cost < replace_cost * 0.7 else 'consider_both'
        }
    
    def _calculate_payback_period(self, item: CircularItem, repair_cost: float, replace_cost: float) -> float:
        """
        Calculate payback period for repair.
        """
        if repair_cost >= replace_cost:
            return float('inf')
        
        savings = replace_cost - repair_cost
        
        # Estimate monthly value of item (depreciation)
        monthly_value = (item.current_value / 12) if item.current_value > 0 else 10
        
        if monthly_value > 0:
            return savings / monthly_value
        
        return 12.0  # Default 1 year
    
    def _calculate_environmental_savings(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate environmental savings from repair.
        """
        # Estimate carbon saved vs buying new
        if item.carbon_footprint_kg > 0:
            carbon_saved = item.carbon_footprint_kg * 0.7  # 70% of new item's carbon
        else:
            carbon_saved = 10.0  # Default estimate
        
        # Water saved
        if item.water_footprint_liters > 0:
            water_saved = item.water_footprint_liters * 0.7
        else:
            water_saved = 50.0
        
        # Waste avoided
        waste_avoided = item.weight_kg * 0.9 if item.weight_kg > 0 else 2.0
        
        return {
            'carbon_saved_kg': carbon_saved,
            'water_saved_liters': water_saved,
            'waste_avoided_kg': waste_avoided
        }
    
    def _calculate_financial_savings(self, item: CircularItem) -> Dict[str, float]:
        """
        Calculate financial savings from repair.
        """
        repair_cost = self._estimate_repair_cost(item)
        
        # Estimate replacement cost
        if item.purchase_price > 0:
            replace_cost = item.purchase_price * (1 + 0.03 * item.get_age_years())
        else:
            replace_cost = 100.0
        
        # Add disposal cost savings
        disposal_cost = item.weight_kg * 0.5 if item.weight_kg > 0 else 5.0
        
        # Add new item shipping/tax savings
        additional_savings = replace_cost * 0.1
        
        total_savings = (replace_cost + disposal_cost + additional_savings) - repair_cost
        
        return {
            'repair_cost': repair_cost,
            'replacement_cost': replace_cost,
            'disposal_cost': disposal_cost,
            'additional_savings': additional_savings,
            'total_savings': total_savings,
            'percentage_saved': (total_savings / replace_cost * 100) if replace_cost > 0 else 0
        }
    
    def _assess_repair_difficulty(self, item: CircularItem) -> Dict[str, Any]:
        """
        Assess repair difficulty.
        """
        difficulty = 50.0  # Base difficulty
        
        # Adjust based on category
        category_key = item.category.value
        if category_key in self.repair_factors:
            difficulty += (self.repair_factors[category_key]['complexity_factor'] * 20)
        
        # Adjust based on condition
        if item.current_condition in [ItemCondition.BROKEN, ItemCondition.DAMAGED]:
            difficulty += 20
        
        # Adjust based on repairability
        if item.repairability_score > 70:
            difficulty -= 20
        elif item.repairability_score < 40:
            difficulty += 20
        
        # Determine skill level needed
        if difficulty < 30:
            skill_level = "beginner"
        elif difficulty < 50:
            skill_level = "intermediate"
        elif difficulty < 70:
            skill_level = "advanced"
        else:
            skill_level = "expert"
        
        return {
            'score': min(100, max(0, difficulty)),
            'skill_level': skill_level,
            'parts_required': self._identify_required_parts(item),
            'tools_required': self._identify_required_tools(item)
        }
    
    def _identify_required_parts(self, item: CircularItem) -> List[str]:
        """
        Identify parts that might need replacement.
        """
        parts = []
        
        if item.category.value == 'electronics':
            parts.extend(['battery', 'screen', 'connector', 'power_supply'])
        elif item.category.value == 'appliances':
            parts.extend(['motor', 'belt', 'heating_element', 'control_board'])
        elif item.category.value == 'furniture':
            parts.extend(['screws', 'hinges', 'legs', 'drawer_slides'])
        elif item.category.value == 'clothing':
            parts.extend(['buttons', 'zippers', 'thread', 'patches'])
        elif item.category.value == 'vehicles':
            parts.extend(['tires', 'brakes', 'filter', 'battery'])
        
        return parts
    
    def _identify_required_tools(self, item: CircularItem) -> List[str]:
        """
        Identify tools needed for repair.
        """
        tools = []
        
        if item.category.value in ['electronics', 'appliances']:
            tools.extend(['screwdriver', 'multimeter', 'soldering_iron'])
        elif item.category.value == 'furniture':
            tools.extend(['screwdriver', 'hammer', 'glue', 'clamps'])
        elif item.category.value in ['clothing', 'footwear']:
            tools.extend(['needle', 'thread', 'scissors', 'sewing_machine'])
        elif item.category.value == 'vehicles':
            tools.extend(['wrench', 'jack', 'tire_iron', 'jump_cables'])
        
        return tools
    
    def _estimate_repair_time(self, item: CircularItem) -> float:
        """
        Estimate repair time in hours.
        """
        base_time = 1.0  # Base hours
        
        # Adjust based on category
        if item.category.value == 'electronics':
            base_time *= 1.5
        elif item.category.value == 'vehicles':
            base_time *= 3.0
        elif item.category.value == 'appliances':
            base_time *= 2.0
        
        # Adjust based on condition
        if item.current_condition == ItemCondition.BROKEN:
            base_time *= 2.0
        elif item.current_condition == ItemCondition.DAMAGED:
            base_time *= 1.5
        
        # Adjust based on difficulty
        difficulty = self._assess_repair_difficulty(item)
        if difficulty['score'] > 70:
            base_time *= 1.5
        
        return round(base_time, 1)
    
    def _estimate_carbon_impact(self, cost: float, type: str) -> float:
        """
        Estimate carbon impact of repair vs replace.
        """
        if type == 'repair':
            return cost * 0.2  # 0.2 kg CO2 per dollar
        else:
            return cost * 0.5  # 0.5 kg CO2 per dollar
    
    def _generate_repair_recommendation(self, item: CircularItem) -> Dict[str, Any]:
        """
        Generate repair recommendation.
        """
        analysis = self.repair_vs_replace_analysis(item)
        difficulty = self._assess_repair_difficulty(item)
        time_required = self._estimate_repair_time(item)
        
        recommendation = {
            'action': '',
            'reason': '',
            'priority': '',
            'steps': []
        }
        
        # Determine action
        if not item.is_repairable:
            recommendation['action'] = 'do_not_repair'
            recommendation['reason'] = 'Item is not repairable'
            recommendation['priority'] = 'low'
        elif analysis['is_repair_cheaper'] and analysis['financial_savings'] > 50:
            recommendation['action'] = 'repair'
            recommendation['reason'] = f"Repair saves ${analysis['financial_savings']:.2f} compared to replacement"
            recommendation['priority'] = 'high'
        elif difficulty['score'] < 50 and time_required < 3:
            recommendation['action'] = 'repair'
            recommendation['reason'] = 'Repair is straightforward with low difficulty'
            recommendation['priority'] = 'high'
        elif analysis['is_repair_cheaper']:
            recommendation['action'] = 'consider_repair'
            recommendation['reason'] = 'Repair is slightly cheaper but may require effort'
            recommendation['priority'] = 'medium'
        else:
            recommendation['action'] = 'replace'
            recommendation['reason'] = 'Replacement is more cost-effective'
            recommendation['priority'] = 'low'
        
        # Generate steps
        if recommendation['action'] in ['repair', 'consider_repair']:
            recommendation['steps'] = [
                '1. Gather necessary tools and parts',
                '2. Review repair instructions',
                '3. Prepare work area',
                '4. Complete repair',
                '5. Test functionality',
                '6. Document repair for future reference'
            ]
        else:
            recommendation['steps'] = [
                '1. Consider replacement options',
                '2. Research sustainable alternatives',
                '3. Recycle or dispose of old item responsibly'
            ]
        
        return recommendation
    
    def add_repair_record(self, item: CircularItem, repair_data: Dict[str, Any]) -> Optional[RepairRecord]:
        """
        Add a repair record to an item.
        
        Args:
            item: The item
            repair_data: Repair information
        
        Returns:
            RepairRecord: Created repair record
        """
        repair = RepairRecord(
            item_id=item.id,
            repair_date=repair_data.get('repair_date', datetime.now()),
            repair_type=repair_data.get('repair_type', 'diy'),
            repair_cost=repair_data.get('repair_cost', 0.0),
            parts_cost=repair_data.get('parts_cost', 0.0),
            labor_cost=repair_data.get('labor_cost', 0.0),
            outcome=repair_data.get('outcome', RepairOutcome.SUCCESSFUL),
            description=repair_data.get('description', ''),
            parts_replaced=repair_data.get('parts_replaced', []),
            repair_shop=repair_data.get('repair_shop', ''),
            warranty_used=repair_data.get('warranty_used', False),
            extended_lifetime_years=repair_data.get('extended_lifetime_years', 0.0),
            repair_quality_score=repair_data.get('repair_quality_score', 80.0),
            notes=repair_data.get('notes', '')
        )
        
        # Calculate impact metrics
        savings = self._calculate_environmental_savings(item)
        repair.carbon_saved_kg = savings['carbon_saved_kg'] * 0.3
        repair.waste_avoided_kg = savings['waste_avoided_kg'] * 0.3
        repair.financial_savings = self._calculate_financial_savings(item)['total_savings'] * 0.3
        
        item.repair_history.append(repair)
        item.repair_count += 1
        item.updated_at = datetime.now()
        
        # Update item condition if repair was successful
        if repair.outcome == RepairOutcome.SUCCESSFUL:
            item.current_condition = ItemCondition.GOOD
        
        logger.info(f"Added repair record for item {item.name}")
        
        return repair
    
    def get_repair_statistics(self, items: List[CircularItem]) -> Dict[str, Any]:
        """
        Get repair statistics for a list of items.
        """
        if not items:
            return {'message': 'No items to analyze'}
        
        total_repairs = sum(item.repair_count for item in items)
        successful_repairs = 0
        total_repair_cost = 0.0
        total_carbon_saved = 0.0
        total_waste_avoided = 0.0
        
        repair_costs = []
        
        for item in items:
            for repair in item.repair_history:
                total_repair_cost += repair.repair_cost
                total_carbon_saved += repair.carbon_saved_kg
                total_waste_avoided += repair.waste_avoided_kg
                repair_costs.append(repair.repair_cost)
                
                if repair.outcome == RepairOutcome.SUCCESSFUL:
                    successful_repairs += 1
        
        return {
            'total_repairs': total_repairs,
            'successful_repairs': successful_repairs,
            'success_rate': (successful_repairs / total_repairs * 100) if total_repairs > 0 else 0,
            'average_repair_cost': statistics.mean(repair_costs) if repair_costs else 0,
            'total_repair_cost': total_repair_cost,
            'total_carbon_saved_kg': total_carbon_saved,
            'total_waste_avoided_kg': total_waste_avoided,
            'repairs_by_category': self._get_repairs_by_category(items)
        }
    
    def _get_repairs_by_category(self, items: List[CircularItem]) -> Dict[str, int]:
        """
        Group repairs by category.
        """
        repairs_by_category = {}
        for item in items:
            if item.category.value not in repairs_by_category:
                repairs_by_category[item.category.value] = 0
            repairs_by_category[item.category.value] += item.repair_count
        
        return repairs_by_category