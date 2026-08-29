"""
Circular Economy & Waste Lifecycle Manager
A comprehensive system for tracking items throughout their lifecycle.
"""

from circular_economy.models import (
    CircularItem, LifecycleStage, ItemCategory, ItemCondition,
    RepairRecord, ReuseRecord, DonationRecord, ResaleRecord,
    RecyclingRecord, DisposalRecord, CircularityScore,
    LifecycleTransition, WasteReduction, LifecycleAlternative,
    HouseholdCircularity, MaterialComposition
)
from circular_economy.lifecycle import LifecycleManager
from circular_economy.repair_analyzer import RepairAnalyzer
from circular_economy.reuse_manager import ReuseManager
from circular_economy.recycling_manager import RecyclingManager
from circular_economy.circularity_scorer import CircularityScorer
from circular_economy.decision_engine import DecisionEngine
from circular_economy.analytics import CircularAnalytics
from circular_economy.database import CircularDatabase
from circular_economy.visualizations import CircularVisualizer

__all__ = [
    'CircularItem',
    'LifecycleStage',
    'ItemCategory',
    'ItemCondition',
    'RepairRecord',
    'ReuseRecord',
    'DonationRecord',
    'ResaleRecord',
    'RecyclingRecord',
    'DisposalRecord',
    'CircularityScore',
    'LifecycleTransition',
    'WasteReduction',
    'LifecycleAlternative',
    'HouseholdCircularity',
    'MaterialComposition',
    'LifecycleManager',
    'RepairAnalyzer',
    'ReuseManager',
    'RecyclingManager',
    'CircularityScorer',
    'DecisionEngine',
    'CircularAnalytics',
    'CircularDatabase',
    'CircularVisualizer'
]