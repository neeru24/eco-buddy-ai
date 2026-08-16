"""Optimized recommendation generation engine for EcoBuddy AI."""

import time
import threading
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
from functools import lru_cache
import hashlib
import json

logger = logging.getLogger(__name__)


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Recommendation:
    """Recommendation data structure."""
    id: str
    title: str
    description: str
    category: str
    priority: Priority
    impact_score: float  # 0-100
    effort_score: float  # 0-100 (lower = easier)
    co2_savings: float  # kg CO2 per year
    cost_savings: float  # $ per year
    implementation_steps: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    estimated_time: str = "1 week"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "priority": self.priority.value,
            "priority_label": self.priority.name,
            "impact_score": self.impact_score,
            "effort_score": self.effort_score,
            "co2_savings": self.co2_savings,
            "cost_savings": self.cost_savings,
            "implementation_steps": self.implementation_steps,
            "resources": self.resources,
            "tags": self.tags,
            "prerequisites": self.prerequisites,
            "estimated_time": self.estimated_time,
            "roi": round((self.co2_savings / max(self.effort_score, 1)) * 10, 2)
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        return cls(
            id=data["id"],
            title=data["title"],
            description=data["description"],
            category=data["category"],
            priority=Priority(data["priority"]),
            impact_score=data["impact_score"],
            effort_score=data["effort_score"],
            co2_savings=data["co2_savings"],
            cost_savings=data["cost_savings"],
            implementation_steps=data.get("implementation_steps", []),
            resources=data.get("resources", []),
            tags=data.get("tags", []),
            prerequisites=data.get("prerequisites", []),
            estimated_time=data.get("estimated_time", "1 week")
        )


class RecommendationCache:
    """Thread-safe cache for recommendations."""
    
    def __init__(self, max_size: int = 500, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0
        }
    
    def _generate_key(self, footprint_data: Dict[str, Any]) -> str:
        """Generate cache key from footprint data."""
        key_data = {
            "categories": footprint_data.get("categories", {}),
            "total_footprint": footprint_data.get("total_footprint", 0),
            "user_type": footprint_data.get("user_type", "individual")
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, footprint_data: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Get cached recommendations."""
        key = self._generate_key(footprint_data)
        
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expiry"] > time.time():
                    self.stats["hits"] += 1
                    logger.debug("Recommendation cache hit")
                    return entry["recommendations"]
                else:
                    del self._cache[key]
                    self.stats["evictions"] += 1
            
            self.stats["misses"] += 1
            return None
    
    def set(self, footprint_data: Dict[str, Any], recommendations: List[Dict[str, Any]], 
            ttl: Optional[int] = None) -> None:
        """Cache recommendations."""
        key = self._generate_key(footprint_data)
        ttl = ttl or self.default_ttl
        
        with self._lock:
            if len(self._cache) >= self.max_size:
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
                self.stats["evictions"] += 1
            
            self._cache[key] = {
                "recommendations": recommendations,
                "expiry": time.time() + ttl,
                "created_at": time.time()
            }
            self.stats["size"] = len(self._cache)
    
    def invalidate(self, footprint_data: Optional[Dict[str, Any]] = None) -> None:
        """Invalidate cache entries."""
        with self._lock:
            if footprint_data is None:
                self._cache.clear()
                logger.info("Cleared recommendation cache")
                return
            
            key = self._generate_key(footprint_data)
            if key in self._cache:
                del self._cache[key]
                logger.debug("Invalidated recommendation cache entry")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
            return {
                **self.stats,
                "hit_rate": round(hit_rate, 2),
                "current_size": len(self._cache)
            }


class RecommendationEngine:
    """Optimized recommendation engine with caching and priority scoring."""
    
    def __init__(self):
        self.cache = RecommendationCache()
        self._recommendation_db: Dict[str, Recommendation] = {}
        self._category_index: Dict[str, List[str]] = defaultdict(list)
        self._tag_index: Dict[str, List[str]] = defaultdict(list)
        self._load_default_recommendations()
        self._lock = threading.RLock()
        
    def _load_default_recommendations(self):
        """Load default recommendations."""
        defaults = [
            Recommendation(
                id="rec_001",
                title="Switch to LED Lighting",
                description="Replace all incandescent bulbs with energy-efficient LED bulbs",
                category="energy",
                priority=Priority.HIGH,
                impact_score=75,
                effort_score=20,
                co2_savings=200,
                cost_savings=150,
                implementation_steps=[
                    "Count all light fixtures",
                    "Purchase LED replacements",
                    "Replace bulbs room by room",
                    "Dispose of old bulbs properly"
                ],
                resources=["Local hardware store", "Energy company rebates"],
                tags=["lighting", "energy", "easy"],
                estimated_time="1 day"
            ),
            Recommendation(
                id="rec_002",
                title="Install Smart Thermostat",
                description="Install a programmable smart thermostat to optimize heating and cooling",
                category="energy",
                priority=Priority.HIGH,
                impact_score=85,
                effort_score=40,
                co2_savings=350,
                cost_savings=250,
                implementation_steps=[
                    "Research compatible thermostats",
                    "Purchase smart thermostat",
                    "Install or hire professional",
                    "Configure schedules",
                    "Connect to phone app"
                ],
                resources=["HVAC professional", "Energy company rebates"],
                tags=["heating", "cooling", "smart", "energy"],
                estimated_time="2 days"
            ),
            Recommendation(
                id="rec_003",
                title="Reduce Food Waste",
                description="Implement meal planning and proper food storage to reduce waste",
                category="food",
                priority=Priority.HIGH,
                impact_score=70,
                effort_score=30,
                co2_savings=150,
                cost_savings=200,
                implementation_steps=[
                    "Plan weekly meals",
                    "Create shopping lists",
                    "Store food properly",
                    "Use leftovers creatively",
                    "Compost food scraps"
                ],
                resources=["Meal planning apps", "Compost bin"],
                tags=["food", "waste", "composting"],
                estimated_time="1 week"
            ),
            Recommendation(
                id="rec_004",
                title="Switch to Plant-Based Meals",
                description="Incorporate more plant-based meals into your diet",
                category="food",
                priority=Priority.MEDIUM,
                impact_score=90,
                effort_score=50,
                co2_savings=450,
                cost_savings=100,
                implementation_steps=[
                    "Start with 1-2 plant-based days per week",
                    "Learn plant-based recipes",
                    "Explore meat alternatives",
                    "Gradually increase frequency"
                ],
                resources=["Plant-based cookbooks", "Online recipes"],
                tags=["food", "diet", "plant-based"],
                estimated_time="2 weeks"
            ),
            Recommendation(
                id="rec_005",
                title="Use Public Transportation",
                description="Switch to public transport for daily commute",
                category="transport",
                priority=Priority.HIGH,
                impact_score=80,
                effort_score=45,
                co2_savings=500,
                cost_savings=300,
                implementation_steps=[
                    "Research local routes",
                    "Get public transport card",
                    "Plan commute times",
                    "Try for 1 week trial"
                ],
                resources=["Public transport app", "Local transit authority"],
                tags=["transport", "commute", "public"],
                estimated_time="1 week"
            ),
            Recommendation(
                id="rec_006",
                title="Carpool to Work",
                description="Share rides with colleagues to reduce emissions",
                category="transport",
                priority=Priority.MEDIUM,
                impact_score=65,
                effort_score=35,
                co2_savings=300,
                cost_savings=200,
                implementation_steps=[
                    "Find carpool partners",
                    "Set up schedule",
                    "Agree on pickup points",
                    "Share costs"
                ],
                resources=["Carpool apps", "Workplace bulletin"],
                tags=["transport", "carpool", "commute"],
                estimated_time="1 day"
            ),
            Recommendation(
                id="rec_007",
                title="Install Solar Panels",
                description="Install solar panels for renewable energy generation",
                category="energy",
                priority=Priority.MEDIUM,
                impact_score=95,
                effort_score=80,
                co2_savings=800,
                cost_savings=400,
                implementation_steps=[
                    "Get solar assessment",
                    "Research installers",
                    "Get quotes",
                    "Apply for permits",
                    "Schedule installation"
                ],
                resources=["Solar installers", "Government incentives"],
                tags=["solar", "renewable", "investment"],
                estimated_time="1 month"
            ),
            Recommendation(
                id="rec_008",
                title="Reduce Water Usage",
                description="Install water-saving fixtures and change habits",
                category="water",
                priority=Priority.MEDIUM,
                impact_score=60,
                effort_score=25,
                co2_savings=80,
                cost_savings=50,
                implementation_steps=[
                    "Install low-flow showerheads",
                    "Fix leaks promptly",
                    "Take shorter showers",
                    "Collect rainwater"
                ],
                resources=["Plumbing supplies", "Water company tips"],
                tags=["water", "conservation"],
                estimated_time="2 days"
            ),
            Recommendation(
                id="rec_009",
                title="Recycle More Effectively",
                description="Improve recycling habits and reduce landfill waste",
                category="waste",
                priority=Priority.HIGH,
                impact_score=55,
                effort_score=20,
                co2_savings=100,
                cost_savings=20,
                implementation_steps=[
                    "Learn local recycling rules",
                    "Set up separate bins",
                    "Clean recyclables",
                    "Track progress weekly"
                ],
                resources=["Local recycling guide", "Recycling bins"],
                tags=["waste", "recycling"],
                estimated_time="1 day"
            ),
            Recommendation(
                id="rec_010",
                title="Buy Energy-Efficient Appliances",
                description="Replace old appliances with Energy Star rated models",
                category="energy",
                priority=Priority.MEDIUM,
                impact_score=70,
                effort_score=60,
                co2_savings=300,
                cost_savings=150,
                implementation_steps=[
                    "Check Energy Star ratings",
                    "Compare models",
                    "Calculate ROI",
                    "Purchase and install"
                ],
                resources=["Energy Star website", "Appliance retailers"],
                tags=["appliances", "energy", "efficiency"],
                estimated_time="1 week"
            ),
            Recommendation(
                id="rec_011",
                title="Switch to Electric Vehicle",
                description="Transition to an electric vehicle for lower emissions",
                category="transport",
                priority=Priority.LOW,
                impact_score=90,
                effort_score=85,
                co2_savings=600,
                cost_savings=200,
                implementation_steps=[
                    "Research EV models",
                    "Check charging options",
                    "Calculate total cost",
                    "Test drive",
                    "Make purchase"
                ],
                resources=["EV dealerships", "Charging network"],
                tags=["transport", "electric", "vehicle"],
                estimated_time="2 weeks"
            ),
            Recommendation(
                id="rec_012",
                title="Plant Trees",
                description="Participate in tree planting to offset carbon emissions",
                category="offset",
                priority=Priority.MEDIUM,
                impact_score=50,
                effort_score=30,
                co2_savings=100,
                cost_savings=0,
                implementation_steps=[
                    "Join tree planting events",
                    "Plant in own yard",
                    "Support reforestation projects"
                ],
                resources=["Local environmental groups", "Tree saplings"],
                tags=["trees", "offset", "nature"],
                estimated_time="1 day"
            ),
            Recommendation(
                id="rec_013",
                title="Use Reusable Bags",
                description="Eliminate single-use plastic bags with reusable alternatives",
                category="waste",
                priority=Priority.HIGH,
                impact_score=40,
                effort_score=5,
                co2_savings=30,
                cost_savings=10,
                implementation_steps=[
                    "Purchase reusable bags",
                    "Keep bags in car/backpack",
                    "Use for all shopping",
                    "Clean regularly"
                ],
                resources=["Reusable bag sets"],
                tags=["waste", "plastic", "reusable"],
                estimated_time="1 hour"
            ),
            Recommendation(
                id="rec_014",
                title="Remote Work Option",
                description="Work from home to reduce commute emissions",
                category="transport",
                priority=Priority.HIGH,
                impact_score=75,
                effort_score=25,
                co2_savings=400,
                cost_savings=350,
                implementation_steps=[
                    "Discuss with employer",
                    "Set up home office",
                    "Establish routine",
                    "Use collaboration tools"
                ],
                resources=["Video conferencing", "Team chat apps"],
                tags=["transport", "remote", "work"],
                estimated_time="1 week"
            ),
            Recommendation(
                id="rec_015",
                title="Air Dry Clothes",
                description="Use clothesline instead of dryer to save energy",
                category="energy",
                priority=Priority.LOW,
                impact_score=35,
                effort_score=10,
                co2_savings=50,
                cost_savings=40,
                implementation_steps=[
                    "Install clothesline or rack",
                    "Wash and hang clothes",
                    "Wait to dry naturally"
                ],
                resources=["Clothesline", "Drying rack"],
                tags=["energy", "laundry"],
                estimated_time="1 day"
            )
        ]
        
        for rec in defaults:
            self._recommendation_db[rec.id] = rec
            self._category_index[rec.category].append(rec.id)
            for tag in rec.tags:
                self._tag_index[tag].append(rec.id)
        
        logger.info(f"Loaded {len(defaults)} default recommendations")
    
    def _calculate_priority_score(self, footprint_data: Dict[str, Any], 
                                   recommendation: Recommendation) -> float:
        """Calculate priority score for a recommendation based on user context."""
        score = 0.0
        
        score += recommendation.impact_score * 0.4
        
        effort_score = 100 - recommendation.effort_score
        score += effort_score * 0.3
        
        category_footprint = footprint_data.get("categories", {}).get(recommendation.category, 0)
        if category_footprint > 0:
            total = footprint_data.get("total_footprint", 1)
            category_weight = min(category_footprint / total * 2, 1.0)
            score += category_weight * 20
        
        roi = recommendation.roi
        score += min(roi / 10, 10) * 2
        
        return round(score, 2)
    
    def generate_recommendations(self, footprint_data: Dict[str, Any], 
                                 limit: int = 10,
                                 use_cache: bool = True) -> List[Dict[str, Any]]:
        """Generate optimized recommendations for given footprint data."""
        
        if use_cache:
            cached = self.cache.get(footprint_data)
            if cached is not None:
                return cached[:limit]
        
        start_time = time.time()
        
        with self._lock:
            relevant_ids = set()
            
            categories = footprint_data.get("categories", {})
            for category, amount in categories.items():
                if amount > 0 and category in self._category_index:
                    relevant_ids.update(self._category_index[category])
            
            if len(relevant_ids) < 10:
                all_ids = set(self._recommendation_db.keys())
                relevant_ids.update(all_ids)
            
            scored_recs = []
            for rec_id in relevant_ids:
                rec = self._recommendation_db.get(rec_id)
                if rec:
                    score = self._calculate_priority_score(footprint_data, rec)
                    scored_recs.append((score, rec))
            
            scored_recs.sort(key=lambda x: x[0], reverse=True)
            
            recommendations = [rec.to_dict() for _, rec in scored_recs]
            
            if use_cache:
                self.cache.set(footprint_data, recommendations)
            
            elapsed = (time.time() - start_time) * 1000
            logger.info(f"Generated {len(recommendations)} recommendations in {elapsed:.2f}ms")
            
            return recommendations[:limit]
    
    def get_recommendation_by_id(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific recommendation by ID."""
        rec = self._recommendation_db.get(rec_id)
        return rec.to_dict() if rec else None
    
    def get_recommendations_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all recommendations in a category."""
        rec_ids = self._category_index.get(category, [])
        return [self._recommendation_db[rec_id].to_dict() 
                for rec_id in rec_ids if rec_id in self._recommendation_db]
    
    def get_recommendations_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all recommendations with a specific tag."""
        rec_ids = self._tag_index.get(tag, [])
        return [self._recommendation_db[rec_id].to_dict() 
                for rec_id in rec_ids if rec_id in self._recommendation_db]
    
    def add_recommendation(self, recommendation: Recommendation) -> None:
        """Add a new recommendation to the engine."""
        with self._lock:
            self._recommendation_db[recommendation.id] = recommendation
            self._category_index[recommendation.category].append(recommendation.id)
            for tag in recommendation.tags:
                self._tag_index[tag].append(recommendation.id)
            logger.info(f"Added recommendation: {recommendation.id}")
            self.cache.invalidate()
    
    def update_recommendation(self, rec_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing recommendation."""
        with self._lock:
            rec = self._recommendation_db.get(rec_id)
            if not rec:
                return None
            
            for key, value in updates.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            
            logger.info(f"Updated recommendation: {rec_id}")
            self.cache.invalidate()
            return rec.to_dict()
    
    def delete_recommendation(self, rec_id: str) -> bool:
        """Delete a recommendation."""
        with self._lock:
            rec = self._recommendation_db.get(rec_id)
            if not rec:
                return False
            
            del self._recommendation_db[rec_id]
            self._category_index[rec.category].remove(rec_id)
            for tag in rec.tags:
                if rec_id in self._tag_index.get(tag, []):
                    self._tag_index[tag].remove(rec_id)
            
            self.cache.invalidate()
            logger.info(f"Deleted recommendation: {rec_id}")
            return True
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    def get_all_categories(self) -> List[str]:
        """Get all recommendation categories."""
        return list(self._category_index.keys())
    
    def get_all_tags(self) -> List[str]:
        """Get all recommendation tags."""
        return list(self._tag_index.keys())


# Global engine instance
_engine = None
_engine_lock = threading.Lock()

def get_recommendation_engine() -> RecommendationEngine:
    """Get the global recommendation engine instance."""
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = RecommendationEngine()
        return _engine


# Convenience functions
def generate_recommendations(footprint_data: Dict[str, Any], 
                             limit: int = 10) -> List[Dict[str, Any]]:
    """Generate recommendations for a user's footprint."""
    engine = get_recommendation_engine()
    return engine.generate_recommendations(footprint_data, limit)


def get_recommendation(rec_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific recommendation."""
    engine = get_recommendation_engine()
    return engine.get_recommendation_by_id(rec_id)


def get_recommendations_by_category(category: str) -> List[Dict[str, Any]]:
    """Get recommendations by category."""
    engine = get_recommendation_engine()
    return engine.get_recommendations_by_category(category)


def get_recommendation_stats() -> Dict[str, Any]:
    """Get recommendation engine statistics."""
    engine = get_recommendation_engine()
    return {
        "total_recommendations": len(engine._recommendation_db),
        "categories": engine.get_all_categories(),
        "tags": engine.get_all_tags(),
        "cache_stats": engine.get_cache_stats()
    }


def warm_recommendation_cache(footprint_data: Dict[str, Any]) -> None:
    """Warm the cache with recommendations for common footprint patterns."""
    engine = get_recommendation_engine()
    engine.generate_recommendations(footprint_data)
    logger.info("Recommendation cache warmed")