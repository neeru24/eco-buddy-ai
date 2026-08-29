"""
Circular Economy & Waste Lifecycle Manager - Data Models
Comprehensive models for circular economy tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any, Set
import uuid
import json


class LifecycleStage(Enum):
    """Stages in an item's lifecycle."""
    PURCHASE = "purchase"
    ACTIVE_USE = "active_use"
    MAINTENANCE = "maintenance"
    REPAIR = "repair"
    REUSE = "reuse"
    DONATION = "donation"
    RESALE = "resale"
    RECYCLING = "recycling"
    COMPOSTING = "composting"
    DISPOSAL = "disposal"
    UPGRADED = "upgraded"
    REPURPOSED = "repurposed"
    ARCHIVED = "archived"


class ItemCategory(Enum):
    """Categories of items."""
    ELECTRONICS = "electronics"
    APPLIANCES = "appliances"
    FURNITURE = "furniture"
    CLOTHING = "clothing"
    FOOTWEAR = "footwear"
    BOOKS = "books"
    TOYS = "toys"
    SPORTS = "sports"
    GARDENING = "gardening"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    DECORATION = "decoration"
    TOOLS = "tools"
    VEHICLES = "vehicles"
    FOOD = "food"
    BEVERAGES = "beverages"
    PACKAGING = "packaging"
    ELECTRONIC_WASTE = "electronic_waste"
    HAZARDOUS = "hazardous"
    OTHER = "other"


class ItemCondition(Enum):
    """Condition of an item."""
    NEW = "new"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DAMAGED = "damaged"
    BROKEN = "broken"
    WORN = "worn"
    UNUSABLE = "unusable"


class RepairOutcome(Enum):
    """Outcome of a repair attempt."""
    SUCCESSFUL = "successful"
    PARTIALLY_SUCCESSFUL = "partially_successful"
    UNSUCCESSFUL = "unsuccessful"
    NOT_ATTEMPTED = "not_attempted"


class RecyclingMethod(Enum):
    """Methods of recycling."""
    CURBSIDE = "curbside"
    DROP_OFF = "drop_off"
    MAIL_IN = "mail_in"
    SPECIALIZED = "specialized"
    COMPOST = "compost"
    UPCYCLE = "upcycle"


@dataclass
class MaterialComposition:
    """Material composition of an item."""
    material: str = ""
    percentage: float = 0.0
    is_recyclable: bool = False
    is_compostable: bool = False
    is_hazardous: bool = False
    recycling_code: str = ""
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'material': self.material,
            'percentage': self.percentage,
            'is_recyclable': self.is_recyclable,
            'is_compostable': self.is_compostable,
            'is_hazardous': self.is_hazardous,
            'recycling_code': self.recycling_code,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MaterialComposition':
        return cls(
            material=data.get('material', ''),
            percentage=data.get('percentage', 0.0),
            is_recyclable=data.get('is_recyclable', False),
            is_compostable=data.get('is_compostable', False),
            is_hazardous=data.get('is_hazardous', False),
            recycling_code=data.get('recycling_code', ''),
            notes=data.get('notes', '')
        )


@dataclass
class CircularItem:
    """
    Represents an item in the circular economy system.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    category: ItemCategory = ItemCategory.OTHER
    description: str = ""
    brand: str = ""
    model: str = ""
    
    # Ownership
    user_id: str = ""
    household_id: Optional[str] = None
    owned_by: str = ""  # User ID or "household"
    is_shared: bool = False
    
    # Acquisition
    purchase_date: Optional[datetime] = None
    purchase_price: float = 0.0
    purchase_location: str = ""
    condition_at_purchase: ItemCondition = ItemCondition.NEW
    
    # Item details
    weight_kg: float = 0.0
    dimensions: str = ""
    materials: List[MaterialComposition] = field(default_factory=list)
    serial_number: str = ""
    
    # Lifetime
    estimated_lifetime_years: float = 0.0
    current_lifecycle_stage: LifecycleStage = LifecycleStage.PURCHASE
    lifecycle_start_date: datetime = field(default_factory=datetime.now)
    current_value: float = 0.0
    
    # Condition
    current_condition: ItemCondition = ItemCondition.GOOD
    condition_notes: str = ""
    last_inspection_date: Optional[datetime] = None
    
    # Repairability
    is_repairable: bool = True
    repairability_score: float = 0.0  # 0-100
    repair_parts_available: bool = False
    repair_instructions_available: bool = False
    
    # Recyclability
    is_recyclable: bool = True
    recyclability_score: float = 0.0  # 0-100
    recycling_instructions: str = ""
    
    # Sustainability metrics
    carbon_footprint_kg: float = 0.0
    water_footprint_liters: float = 0.0
    waste_generation_kg: float = 0.0
    landfill_avoided_kg: float = 0.0
    
    # Circularity
    circularity_score: float = 0.0  # 0-100
    reuse_count: int = 0
    repair_count: int = 0
    
    # History
    lifecycle_history: List['LifecycleTransition'] = field(default_factory=list)
    repair_history: List['RepairRecord'] = field(default_factory=list)
    reuse_history: List['ReuseRecord'] = field(default_factory=list)
    donation_history: List['DonationRecord'] = field(default_factory=list)
    resale_history: List['ResaleRecord'] = field(default_factory=list)
    recycling_history: List['RecyclingRecord'] = field(default_factory=list)
    disposal_records: List['DisposalRecord'] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'brand': self.brand,
            'model': self.model,
            'user_id': self.user_id,
            'household_id': self.household_id,
            'owned_by': self.owned_by,
            'is_shared': self.is_shared,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'purchase_price': self.purchase_price,
            'purchase_location': self.purchase_location,
            'condition_at_purchase': self.condition_at_purchase.value,
            'weight_kg': self.weight_kg,
            'dimensions': self.dimensions,
            'materials': [m.to_dict() for m in self.materials],
            'serial_number': self.serial_number,
            'estimated_lifetime_years': self.estimated_lifetime_years,
            'current_lifecycle_stage': self.current_lifecycle_stage.value,
            'lifecycle_start_date': self.lifecycle_start_date.isoformat(),
            'current_value': self.current_value,
            'current_condition': self.current_condition.value,
            'condition_notes': self.condition_notes,
            'last_inspection_date': self.last_inspection_date.isoformat() if self.last_inspection_date else None,
            'is_repairable': self.is_repairable,
            'repairability_score': self.repairability_score,
            'repair_parts_available': self.repair_parts_available,
            'repair_instructions_available': self.repair_instructions_available,
            'is_recyclable': self.is_recyclable,
            'recyclability_score': self.recyclability_score,
            'recycling_instructions': self.recycling_instructions,
            'carbon_footprint_kg': self.carbon_footprint_kg,
            'water_footprint_liters': self.water_footprint_liters,
            'waste_generation_kg': self.waste_generation_kg,
            'landfill_avoided_kg': self.landfill_avoided_kg,
            'circularity_score': self.circularity_score,
            'reuse_count': self.reuse_count,
            'repair_count': self.repair_count,
            'lifecycle_history': [t.to_dict() for t in self.lifecycle_history],
            'repair_history': [r.to_dict() for r in self.repair_history],
            'reuse_history': [r.to_dict() for r in self.reuse_history],
            'donation_history': [d.to_dict() for d in self.donation_history],
            'resale_history': [r.to_dict() for r in self.resale_history],
            'recycling_history': [r.to_dict() for r in self.recycling_history],
            'disposal_records': [d.to_dict() for d in self.disposal_records],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'notes': self.notes,
            'tags': self.tags,
            'images': self.images
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CircularItem':
        item = cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            category=ItemCategory(data.get('category', 'other')),
            description=data.get('description', ''),
            brand=data.get('brand', ''),
            model=data.get('model', ''),
            user_id=data.get('user_id', ''),
            household_id=data.get('household_id'),
            owned_by=data.get('owned_by', ''),
            is_shared=data.get('is_shared', False),
            purchase_date=datetime.fromisoformat(data['purchase_date']) if data.get('purchase_date') else None,
            purchase_price=data.get('purchase_price', 0.0),
            purchase_location=data.get('purchase_location', ''),
            condition_at_purchase=ItemCondition(data.get('condition_at_purchase', 'new')),
            weight_kg=data.get('weight_kg', 0.0),
            dimensions=data.get('dimensions', ''),
            serial_number=data.get('serial_number', ''),
            estimated_lifetime_years=data.get('estimated_lifetime_years', 0.0),
            current_lifecycle_stage=LifecycleStage(data.get('current_lifecycle_stage', 'purchase')),
            lifecycle_start_date=datetime.fromisoformat(data['lifecycle_start_date']) if data.get('lifecycle_start_date') else datetime.now(),
            current_value=data.get('current_value', 0.0),
            current_condition=ItemCondition(data.get('current_condition', 'good')),
            condition_notes=data.get('condition_notes', ''),
            last_inspection_date=datetime.fromisoformat(data['last_inspection_date']) if data.get('last_inspection_date') else None,
            is_repairable=data.get('is_repairable', True),
            repairability_score=data.get('repairability_score', 0.0),
            repair_parts_available=data.get('repair_parts_available', False),
            repair_instructions_available=data.get('repair_instructions_available', False),
            is_recyclable=data.get('is_recyclable', True),
            recyclability_score=data.get('recyclability_score', 0.0),
            recycling_instructions=data.get('recycling_instructions', ''),
            carbon_footprint_kg=data.get('carbon_footprint_kg', 0.0),
            water_footprint_liters=data.get('water_footprint_liters', 0.0),
            waste_generation_kg=data.get('waste_generation_kg', 0.0),
            landfill_avoided_kg=data.get('landfill_avoided_kg', 0.0),
            circularity_score=data.get('circularity_score', 0.0),
            reuse_count=data.get('reuse_count', 0),
            repair_count=data.get('repair_count', 0),
            notes=data.get('notes', ''),
            tags=data.get('tags', []),
            images=data.get('images', [])
        )
        
        # Load materials
        for material_data in data.get('materials', []):
            item.materials.append(MaterialComposition.from_dict(material_data))
        
        # Load history
        for transition_data in data.get('lifecycle_history', []):
            item.lifecycle_history.append(LifecycleTransition.from_dict(transition_data))
        
        for repair_data in data.get('repair_history', []):
            item.repair_history.append(RepairRecord.from_dict(repair_data))
        
        for reuse_data in data.get('reuse_history', []):
            item.reuse_history.append(ReuseRecord.from_dict(reuse_data))
        
        for donation_data in data.get('donation_history', []):
            item.donation_history.append(DonationRecord.from_dict(donation_data))
        
        for resale_data in data.get('resale_history', []):
            item.resale_history.append(ResaleRecord.from_dict(resale_data))
        
        for recycling_data in data.get('recycling_history', []):
            item.recycling_history.append(RecyclingRecord.from_dict(recycling_data))
        
        for disposal_data in data.get('disposal_records', []):
            item.disposal_records.append(DisposalRecord.from_dict(disposal_data))
        
        return item
    
    def get_age_days(self) -> int:
        """Get the age of the item in days."""
        if self.purchase_date:
            return (datetime.now() - self.purchase_date).days
        return 0
    
    def get_age_years(self) -> float:
        """Get the age of the item in years."""
        return self.get_age_days() / 365.25
    
    def get_remaining_lifetime(self) -> float:
        """Get estimated remaining lifetime in years."""
        age = self.get_age_years()
        remaining = self.estimated_lifetime_years - age
        return max(0, remaining)
    
    def get_total_waste_avoided(self) -> float:
        """Calculate total waste avoided through circular actions."""
        total = self.landfill_avoided_kg
        
        # Add waste avoided from repairs
        for repair in self.repair_history:
            total += repair.waste_avoided_kg or 0
        
        # Add waste avoided from reuse
        for reuse in self.reuse_history:
            total += reuse.waste_avoided_kg or 0
        
        return total


@dataclass
class LifecycleTransition:
    """
    Records a transition between lifecycle stages.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    from_stage: LifecycleStage = LifecycleStage.PURCHASE
    to_stage: LifecycleStage = LifecycleStage.ACTIVE_USE
    transition_date: datetime = field(default_factory=datetime.now)
    reason: str = ""
    notes: str = ""
    performed_by: str = ""
    
    # Impact metrics
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_avoided_kg: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'from_stage': self.from_stage.value,
            'to_stage': self.to_stage.value,
            'transition_date': self.transition_date.isoformat(),
            'reason': self.reason,
            'notes': self.notes,
            'performed_by': self.performed_by,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_avoided_kg': self.waste_avoided_kg
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LifecycleTransition':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            from_stage=LifecycleStage(data.get('from_stage', 'purchase')),
            to_stage=LifecycleStage(data.get('to_stage', 'active_use')),
            transition_date=datetime.fromisoformat(data['transition_date']) if data.get('transition_date') else datetime.now(),
            reason=data.get('reason', ''),
            notes=data.get('notes', ''),
            performed_by=data.get('performed_by', ''),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0)
        )


@dataclass
class RepairRecord:
    """
    Records a repair performed on an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    repair_date: datetime = field(default_factory=datetime.now)
    repair_type: str = ""  # diy, professional, warranty
    repair_cost: float = 0.0
    parts_cost: float = 0.0
    labor_cost: float = 0.0
    outcome: RepairOutcome = RepairOutcome.SUCCESSFUL
    description: str = ""
    parts_replaced: List[str] = field(default_factory=list)
    repair_shop: str = ""
    warranty_used: bool = False
    
    # Impact metrics
    carbon_saved_kg: float = 0.0  # vs buying new
    water_saved_liters: float = 0.0
    waste_avoided_kg: float = 0.0
    financial_savings: float = 0.0  # vs buying new
    
    # Extending life
    extended_lifetime_years: float = 0.0
    repair_quality_score: float = 0.0  # 0-100
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'repair_date': self.repair_date.isoformat(),
            'repair_type': self.repair_type,
            'repair_cost': self.repair_cost,
            'parts_cost': self.parts_cost,
            'labor_cost': self.labor_cost,
            'outcome': self.outcome.value,
            'description': self.description,
            'parts_replaced': self.parts_replaced,
            'repair_shop': self.repair_shop,
            'warranty_used': self.warranty_used,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_avoided_kg': self.waste_avoided_kg,
            'financial_savings': self.financial_savings,
            'extended_lifetime_years': self.extended_lifetime_years,
            'repair_quality_score': self.repair_quality_score,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RepairRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            repair_date=datetime.fromisoformat(data['repair_date']) if data.get('repair_date') else datetime.now(),
            repair_type=data.get('repair_type', ''),
            repair_cost=data.get('repair_cost', 0.0),
            parts_cost=data.get('parts_cost', 0.0),
            labor_cost=data.get('labor_cost', 0.0),
            outcome=RepairOutcome(data.get('outcome', 'successful')),
            description=data.get('description', ''),
            parts_replaced=data.get('parts_replaced', []),
            repair_shop=data.get('repair_shop', ''),
            warranty_used=data.get('warranty_used', False),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0),
            financial_savings=data.get('financial_savings', 0.0),
            extended_lifetime_years=data.get('extended_lifetime_years', 0.0),
            repair_quality_score=data.get('repair_quality_score', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class ReuseRecord:
    """
    Records a reuse of an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    reuse_date: datetime = field(default_factory=datetime.now)
    reuse_type: str = ""  # personal, shared, gifted
    new_owner_id: Optional[str] = None
    reuse_duration_days: int = 0
    description: str = ""
    
    # Impact metrics
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_avoided_kg: float = 0.0
    financial_savings: float = 0.0
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'reuse_date': self.reuse_date.isoformat(),
            'reuse_type': self.reuse_type,
            'new_owner_id': self.new_owner_id,
            'reuse_duration_days': self.reuse_duration_days,
            'description': self.description,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_avoided_kg': self.waste_avoided_kg,
            'financial_savings': self.financial_savings,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReuseRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            reuse_date=datetime.fromisoformat(data['reuse_date']) if data.get('reuse_date') else datetime.now(),
            reuse_type=data.get('reuse_type', ''),
            new_owner_id=data.get('new_owner_id'),
            reuse_duration_days=data.get('reuse_duration_days', 0),
            description=data.get('description', ''),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0),
            financial_savings=data.get('financial_savings', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class DonationRecord:
    """
    Records a donation of an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    donation_date: datetime = field(default_factory=datetime.now)
    organization: str = ""
    organization_type: str = ""  # charity, thrift, church, school
    tax_deductible: bool = False
    estimated_value: float = 0.0
    description: str = ""
    receipt_url: str = ""
    
    # Impact metrics
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_avoided_kg: float = 0.0
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'donation_date': self.donation_date.isoformat(),
            'organization': self.organization,
            'organization_type': self.organization_type,
            'tax_deductible': self.tax_deductible,
            'estimated_value': self.estimated_value,
            'description': self.description,
            'receipt_url': self.receipt_url,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_avoided_kg': self.waste_avoided_kg,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DonationRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            donation_date=datetime.fromisoformat(data['donation_date']) if data.get('donation_date') else datetime.now(),
            organization=data.get('organization', ''),
            organization_type=data.get('organization_type', ''),
            tax_deductible=data.get('tax_deductible', False),
            estimated_value=data.get('estimated_value', 0.0),
            description=data.get('description', ''),
            receipt_url=data.get('receipt_url', ''),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class ResaleRecord:
    """
    Records a resale of an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    resale_date: datetime = field(default_factory=datetime.now)
    platform: str = ""  # ebay, facebook, craigslist, etc.
    sale_price: float = 0.0
    fees: float = 0.0
    shipping_cost: float = 0.0
    net_profit: float = 0.0
    buyer_info: str = ""
    description: str = ""
    
    # Impact metrics
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    waste_avoided_kg: float = 0.0
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'resale_date': self.resale_date.isoformat(),
            'platform': self.platform,
            'sale_price': self.sale_price,
            'fees': self.fees,
            'shipping_cost': self.shipping_cost,
            'net_profit': self.net_profit,
            'buyer_info': self.buyer_info,
            'description': self.description,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'waste_avoided_kg': self.waste_avoided_kg,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResaleRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            resale_date=datetime.fromisoformat(data['resale_date']) if data.get('resale_date') else datetime.now(),
            platform=data.get('platform', ''),
            sale_price=data.get('sale_price', 0.0),
            fees=data.get('fees', 0.0),
            shipping_cost=data.get('shipping_cost', 0.0),
            net_profit=data.get('net_profit', 0.0),
            buyer_info=data.get('buyer_info', ''),
            description=data.get('description', ''),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class RecyclingRecord:
    """
    Records recycling of an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    recycling_date: datetime = field(default_factory=datetime.now)
    recycling_method: RecyclingMethod = RecyclingMethod.CURBSIDE
    facility_name: str = ""
    materials_recycled: List[str] = field(default_factory=list)
    weight_recycled_kg: float = 0.0
    
    # Impact metrics
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    energy_saved_kwh: float = 0.0
    waste_avoided_kg: float = 0.0
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'recycling_date': self.recycling_date.isoformat(),
            'recycling_method': self.recycling_method.value,
            'facility_name': self.facility_name,
            'materials_recycled': self.materials_recycled,
            'weight_recycled_kg': self.weight_recycled_kg,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'energy_saved_kwh': self.energy_saved_kwh,
            'waste_avoided_kg': self.waste_avoided_kg,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RecyclingRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            recycling_date=datetime.fromisoformat(data['recycling_date']) if data.get('recycling_date') else datetime.now(),
            recycling_method=RecyclingMethod(data.get('recycling_method', 'curbside')),
            facility_name=data.get('facility_name', ''),
            materials_recycled=data.get('materials_recycled', []),
            weight_recycled_kg=data.get('weight_recycled_kg', 0.0),
            carbon_saved_kg=data.get('carbon_saved_kg', 0.0),
            water_saved_liters=data.get('water_saved_liters', 0.0),
            energy_saved_kwh=data.get('energy_saved_kwh', 0.0),
            waste_avoided_kg=data.get('waste_avoided_kg', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class DisposalRecord:
    """
    Records disposal of an item (last resort).
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    disposal_date: datetime = field(default_factory=datetime.now)
    disposal_method: str = ""  # landfill, incineration, etc.
    facility_name: str = ""
    weight_kg: float = 0.0
    
    # Impact metrics
    carbon_footprint_kg: float = 0.0
    water_footprint_liters: float = 0.0
    
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'disposal_date': self.disposal_date.isoformat(),
            'disposal_method': self.disposal_method,
            'facility_name': self.facility_name,
            'weight_kg': self.weight_kg,
            'carbon_footprint_kg': self.carbon_footprint_kg,
            'water_footprint_liters': self.water_footprint_liters,
            'notes': self.notes,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DisposalRecord':
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            item_id=data.get('item_id', ''),
            disposal_date=datetime.fromisoformat(data['disposal_date']) if data.get('disposal_date') else datetime.now(),
            disposal_method=data.get('disposal_method', ''),
            facility_name=data.get('facility_name', ''),
            weight_kg=data.get('weight_kg', 0.0),
            carbon_footprint_kg=data.get('carbon_footprint_kg', 0.0),
            water_footprint_liters=data.get('water_footprint_liters', 0.0),
            notes=data.get('notes', ''),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


@dataclass
class CircularityScore:
    """
    Comprehensive circularity score for an item or household.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: Optional[str] = None
    household_id: Optional[str] = None
    
    # Component scores
    reuse_score: float = 0.0  # 0-100
    repair_score: float = 0.0  # 0-100
    recycle_score: float = 0.0  # 0-100
    waste_reduction_score: float = 0.0  # 0-100
    
    # Overall score
    overall_circularity_score: float = 0.0  # 0-100
    
    # Metrics
    landfill_diversion_kg: float = 0.0
    landfill_diversion_percentage: float = 0.0
    carbon_saved_kg: float = 0.0
    financial_savings: float = 0.0
    
    # Breakdown
    reuse_events: int = 0
    repair_events: int = 0
    recycle_events: int = 0
    donation_events: int = 0
    resale_events: int = 0
    
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'household_id': self.household_id,
            'reuse_score': self.reuse_score,
            'repair_score': self.repair_score,
            'recycle_score': self.recycle_score,
            'waste_reduction_score': self.waste_reduction_score,
            'overall_circularity_score': self.overall_circularity_score,
            'landfill_diversion_kg': self.landfill_diversion_kg,
            'landfill_diversion_percentage': self.landfill_diversion_percentage,
            'carbon_saved_kg': self.carbon_saved_kg,
            'financial_savings': self.financial_savings,
            'reuse_events': self.reuse_events,
            'repair_events': self.repair_events,
            'recycle_events': self.recycle_events,
            'donation_events': self.donation_events,
            'resale_events': self.resale_events,
            'calculated_at': self.calculated_at.isoformat()
        }


@dataclass
class LifecycleAlternative:
    """
    Represents a possible lifecycle alternative for an item.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str = ""
    alternative_type: str = ""  # repair, reuse, donate, resell, recycle, dispose
    description: str = ""
    
    # Costs
    financial_cost: float = 0.0
    financial_benefit: float = 0.0
    net_financial_impact: float = 0.0
    
    # Environmental impact
    carbon_impact_kg: float = 0.0
    water_impact_liters: float = 0.0
    waste_impact_kg: float = 0.0
    
    # Circularity
    circularity_score: float = 0.0  # 0-100
    landfill_diversion_kg: float = 0.0
    
    # Feasibility
    feasibility_score: float = 0.0  # 0-100
    effort_required: str = ""  # low, medium, high
    
    # Comparison
    is_best_option: bool = False
    compared_to_disposal: float = 0.0  # Percentage improvement
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'item_id': self.item_id,
            'alternative_type': self.alternative_type,
            'description': self.description,
            'financial_cost': self.financial_cost,
            'financial_benefit': self.financial_benefit,
            'net_financial_impact': self.net_financial_impact,
            'carbon_impact_kg': self.carbon_impact_kg,
            'water_impact_liters': self.water_impact_liters,
            'waste_impact_kg': self.waste_impact_kg,
            'circularity_score': self.circularity_score,
            'landfill_diversion_kg': self.landfill_diversion_kg,
            'feasibility_score': self.feasibility_score,
            'effort_required': self.effort_required,
            'is_best_option': self.is_best_option,
            'compared_to_disposal': self.compared_to_disposal
        }


@dataclass
class HouseholdCircularity:
    """
    Circularity metrics for an entire household.
    """
    household_id: str = ""
    
    # Overall metrics
    total_items: int = 0
    circular_items: int = 0
    circularity_percentage: float = 0.0
    
    # Category breakdown
    category_metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Action metrics
    total_reuse: int = 0
    total_repair: int = 0
    total_recycle: int = 0
    total_donate: int = 0
    total_resale: int = 0
    
    # Impact metrics
    total_landfill_diverted_kg: float = 0.0
    total_carbon_saved_kg: float = 0.0
    total_water_saved_liters: float = 0.0
    total_financial_savings: float = 0.0
    
    # Member contributions
    member_contributions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Scores
    household_circularity_score: float = 0.0
    waste_reduction_score: float = 0.0
    
    calculated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'household_id': self.household_id,
            'total_items': self.total_items,
            'circular_items': self.circular_items,
            'circularity_percentage': self.circularity_percentage,
            'category_metrics': self.category_metrics,
            'total_reuse': self.total_reuse,
            'total_repair': self.total_repair,
            'total_recycle': self.total_recycle,
            'total_donate': self.total_donate,
            'total_resale': self.total_resale,
            'total_landfill_diverted_kg': self.total_landfill_diverted_kg,
            'total_carbon_saved_kg': self.total_carbon_saved_kg,
            'total_water_saved_liters': self.total_water_saved_liters,
            'total_financial_savings': self.total_financial_savings,
            'member_contributions': self.member_contributions,
            'household_circularity_score': self.household_circularity_score,
            'waste_reduction_score': self.waste_reduction_score,
            'calculated_at': self.calculated_at.isoformat()
        }


@dataclass
class WasteReduction:
    """
    Waste reduction metrics from circular economy actions.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    household_id: str = ""
    date: datetime = field(default_factory=datetime.now)
    
    # Total waste
    total_waste_kg: float = 0.0
    total_waste_diverted_kg: float = 0.0
    diversion_rate: float = 0.0
    
    # Breakdown by action
    repair_diverted_kg: float = 0.0
    reuse_diverted_kg: float = 0.0
    donation_diverted_kg: float = 0.0
    resale_diverted_kg: float = 0.0
    recycling_diverted_kg: float = 0.0
    composting_diverted_kg: float = 0.0
    
    # Landfill avoided
    landfill_avoided_kg: float = 0.0
    landfill_avoided_percentage: float = 0.0
    
    # Environmental impact
    carbon_saved_kg: float = 0.0
    water_saved_liters: float = 0.0
    energy_saved_kwh: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'household_id': self.household_id,
            'date': self.date.isoformat(),
            'total_waste_kg': self.total_waste_kg,
            'total_waste_diverted_kg': self.total_waste_diverted_kg,
            'diversion_rate': self.diversion_rate,
            'repair_diverted_kg': self.repair_diverted_kg,
            'reuse_diverted_kg': self.reuse_diverted_kg,
            'donation_diverted_kg': self.donation_diverted_kg,
            'resale_diverted_kg': self.resale_diverted_kg,
            'recycling_diverted_kg': self.recycling_diverted_kg,
            'composting_diverted_kg': self.composting_diverted_kg,
            'landfill_avoided_kg': self.landfill_avoided_kg,
            'landfill_avoided_percentage': self.landfill_avoided_percentage,
            'carbon_saved_kg': self.carbon_saved_kg,
            'water_saved_liters': self.water_saved_liters,
            'energy_saved_kwh': self.energy_saved_kwh,
            'created_at': self.created_at.isoformat()
        }