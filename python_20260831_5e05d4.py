"""
Sustainability Gamification & Challenge Platform - Templates
Manages challenge templates for easy creation.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import (
    ChallengeTemplate, ChallengeCategory, ChallengeType,
    ChallengeDifficulty
)

logger = logging.getLogger(__name__)


class TemplateManager:
    """
    Manages challenge templates.
    """
    
    def __init__(self):
        """Initialize the template manager."""
        self.templates = self._initialize_templates()
        logger.info("Template Manager initialized")
    
    def _initialize_templates(self) -> List[ChallengeTemplate]:
        """
        Initialize default challenge templates.
        """
        templates = []
        
        # Energy templates
        templates.append(ChallengeTemplate(
            name="Reduce Energy Usage",
            description="Reduce your daily energy consumption by 10%",
            category=ChallengeCategory.ENERGY,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=10.0,
            default_unit="%",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_carbon_savings=2.0,
            instructions="Track your energy usage daily. Aim to use 10% less than your baseline.",
            tips=[
                "Turn off lights when not in use",
                "Unplug electronics when not in use",
                "Use energy-efficient appliances"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Energy Efficiency Month",
            description="Reduce energy consumption by 20% over 30 days",
            category=ChallengeCategory.ENERGY,
            challenge_type=ChallengeType.MONTHLY,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            default_target=20.0,
            default_unit="%",
            default_duration=30,
            default_points=50,
            default_xp=100,
            estimated_carbon_savings=30.0,
            instructions="Track monthly energy usage. Implement efficiency measures to reduce consumption.",
            tips=[
                "Install LED bulbs",
                "Use smart power strips",
                "Weatherproof windows and doors",
                "Set thermostat efficiently"
            ]
        ))
        
        # Water templates
        templates.append(ChallengeTemplate(
            name="Save Water",
            description="Reduce daily water usage by 20 liters",
            category=ChallengeCategory.WATER,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=20.0,
            default_unit="liters",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_water_savings=20.0,
            instructions="Track your daily water usage. Aim to save 20 liters.",
            tips=[
                "Take shorter showers",
                "Fix any leaks",
                "Turn off tap when brushing teeth"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Water Conservation Challenge",
            description="Reduce water usage by 30% over 14 days",
            category=ChallengeCategory.WATER,
            challenge_type=ChallengeType.WEEKLY,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            default_target=30.0,
            default_unit="%",
            default_duration=14,
            default_points=40,
            default_xp=80,
            estimated_water_savings=100.0,
            instructions="Track water usage for 14 days. Aim to reduce by 30% from baseline.",
            tips=[
                "Install low-flow fixtures",
                "Collect rainwater",
                "Use drought-tolerant plants"
            ]
        ))
        
        # Waste templates
        templates.append(ChallengeTemplate(
            name="Reduce Waste",
            description="Reduce daily waste by 0.5 kg",
            category=ChallengeCategory.WASTE,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=0.5,
            default_unit="kg",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_waste_reduction=0.5,
            instructions="Track your daily waste. Aim to reduce by 0.5 kg.",
            tips=[
                "Recycle more",
                "Compost food waste",
                "Reduce packaging waste"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Zero Waste Week",
            description="Achieve zero waste for one week",
            category=ChallengeCategory.WASTE,
            challenge_type=ChallengeType.WEEKLY,
            difficulty=ChallengeDifficulty.ADVANCED,
            default_target=7.0,
            default_unit="days",
            default_duration=7,
            default_points=60,
            default_xp=120,
            estimated_waste_reduction=5.0,
            instructions="Try to create no waste for 7 days.",
            tips=[
                "Plan meals carefully",
                "Use reusable containers",
                "Buy in bulk",
                "Compost everything possible"
            ]
        ))
        
        # Transportation templates
        templates.append(ChallengeTemplate(
            name="Walk More",
            description="Walk 2 km instead of driving",
            category=ChallengeCategory.TRANSPORTATION,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=2.0,
            default_unit="km",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_carbon_savings=1.5,
            instructions="Walk 2 km today instead of using a car.",
            tips=[
                "Plan walking routes",
                "Walk with a friend",
                "Enjoy the fresh air"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Public Transit Challenge",
            description="Use public transit for 5 days",
            category=ChallengeCategory.TRANSPORTATION,
            challenge_type=ChallengeType.WEEKLY,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            default_target=5.0,
            default_unit="days",
            default_duration=7,
            default_points=35,
            default_xp=70,
            estimated_carbon_savings=10.0,
            instructions="Use public transit for 5 days instead of driving.",
            tips=[
                "Plan routes ahead",
                "Get a transit pass",
                "Explore your city"
            ]
        ))
        
        # Food templates
        templates.append(ChallengeTemplate(
            name="Meatless Meal",
            description="Have one meatless meal today",
            category=ChallengeCategory.FOOD,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=1.0,
            default_unit="meal",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_carbon_savings=3.0,
            instructions="Have at least one meal without meat today.",
            tips=[
                "Try plant-based proteins",
                "Explore new recipes",
                "Enjoy vegetarian cuisine"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Plant-Based Challenge",
            description="Eat plant-based for 7 days",
            category=ChallengeCategory.FOOD,
            challenge_type=ChallengeType.WEEKLY,
            difficulty=ChallengeDifficulty.ADVANCED,
            default_target=7.0,
            default_unit="days",
            default_duration=7,
            default_points=50,
            default_xp=100,
            estimated_carbon_savings=20.0,
            instructions="Follow a plant-based diet for 7 days.",
            tips=[
                "Plan meals in advance",
                "Get enough protein",
                "Try new recipes"
            ]
        ))
        
        # Recycling templates
        templates.append(ChallengeTemplate(
            name="Recycling Challenge",
            description="Recycle 5 items today",
            category=ChallengeCategory.RECYCLING,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=5.0,
            default_unit="items",
            default_duration=1,
            default_points=10,
            default_xp=20,
            estimated_waste_reduction=1.0,
            instructions="Recycle at least 5 items today.",
            tips=[
                "Check recycling guidelines",
                "Rinse containers",
                "Separate materials"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Recycling Master",
            description="Recycle 50 items over 14 days",
            category=ChallengeCategory.RECYCLING,
            challenge_type=ChallengeType.MONTHLY,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            default_target=50.0,
            default_unit="items",
            default_duration=14,
            default_points=40,
            default_xp=80,
            estimated_waste_reduction=5.0,
            instructions="Recycle 50 items over 2 weeks.",
            tips=[
                "Set up a recycling station",
                "Keep containers",
                "Track progress daily"
            ]
        ))
        
        # Household templates
        templates.append(ChallengeTemplate(
            name="Household Energy Challenge",
            description="Reduce household energy by 15% over 30 days",
            category=ChallengeCategory.HOUSEHOLD,
            challenge_type=ChallengeType.MONTHLY,
            difficulty=ChallengeDifficulty.ADVANCED,
            default_target=15.0,
            default_unit="%",
            default_duration=30,
            default_points=60,
            default_xp=120,
            estimated_carbon_savings=40.0,
            instructions="Work as a household to reduce energy usage by 15%.",
            tips=[
                "Get the whole family involved",
                "Track usage together",
                "Celebrate achievements"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Household Waste Challenge",
            description="Reduce household waste by 25% over 30 days",
            category=ChallengeCategory.HOUSEHOLD,
            challenge_type=ChallengeType.MONTHLY,
            difficulty=ChallengeDifficulty.ADVANCED,
            default_target=25.0,
            default_unit="%",
            default_duration=30,
            default_points=60,
            default_xp=120,
            estimated_waste_reduction=8.0,
            instructions="Work as a household to reduce waste by 25%.",
            tips=[
                "Start composting",
                "Buy in bulk",
                "Use reusable bags"
            ]
        ))
        
        # Education templates
        templates.append(ChallengeTemplate(
            name="Sustainability Learning",
            description="Read one sustainability article today",
            category=ChallengeCategory.EDUCATION,
            challenge_type=ChallengeType.DAILY,
            difficulty=ChallengeDifficulty.BEGINNER,
            default_target=1.0,
            default_unit="article",
            default_duration=1,
            default_points=10,
            default_xp=20,
            instructions="Read one article about sustainability today.",
            tips=[
                "Follow sustainability news",
                "Share what you learn",
                "Apply new knowledge"
            ]
        ))
        
        templates.append(ChallengeTemplate(
            name="Eco-Education Week",
            description="Learn about 5 sustainability topics over 7 days",
            category=ChallengeCategory.EDUCATION,
            challenge_type=ChallengeType.WEEKLY,
            difficulty=ChallengeDifficulty.INTERMEDIATE,
            default_target=5.0,
            default_unit="topics",
            default_duration=7,
            default_points=35,
            default_xp=70,
            instructions="Learn about 5 different sustainability topics this week.",
            tips=[
                "Watch documentaries",
                "Take online courses",
                "Read books",
                "Join webinars"
            ]
        ))
        
        return templates
    
    def get_all_templates(self) -> List[ChallengeTemplate]:
        """
        Get all available templates.
        
        Returns:
            List[ChallengeTemplate]: All templates
        """
        return [t for t in self.templates if t.is_active]
    
    def get_template(self, template_id: str) -> Optional[ChallengeTemplate]:
        """
        Get a specific template by ID.
        
        Args:
            template_id: Template ID
        
        Returns:
            Optional[ChallengeTemplate]: Template if found
        """
        for template in self.templates:
            if template.id == template_id:
                return template
        return None
    
    def get_templates_by_category(self, category: ChallengeCategory) -> List[ChallengeTemplate]:
        """
        Get templates by category.
        
        Args:
            category: Challenge category
        
        Returns:
            List[ChallengeTemplate]: Templates in category
        """
        return [t for t in self.templates if t.category == category and t.is_active]
    
    def get_templates_by_difficulty(self, difficulty: ChallengeDifficulty) -> List[ChallengeTemplate]:
        """
        Get templates by difficulty.
        
        Args:
            difficulty: Challenge difficulty
        
        Returns:
            List[ChallengeTemplate]: Templates with difficulty
        """
        return [t for t in self.templates if t.difficulty == difficulty and t.is_active]
    
    def get_templates_by_type(self, challenge_type: ChallengeType) -> List[ChallengeTemplate]:
        """
        Get templates by challenge type.
        
        Args:
            challenge_type: Challenge type
        
        Returns:
            List[ChallengeTemplate]: Templates with type
        """
        return [t for t in self.templates if t.challenge_type == challenge_type and t.is_active]
    
    def get_popular_templates(self, limit: int = 5) -> List[ChallengeTemplate]:
        """
        Get most popular templates by usage count.
        
        Args:
            limit: Number of templates to return
        
        Returns:
            List[ChallengeTemplate]: Popular templates
        """
        sorted_templates = sorted(self.templates, key=lambda t: t.usage_count, reverse=True)
        return sorted_templates[:limit]
    
    def create_custom_template(self,
                              name: str,
                              category: ChallengeCategory,
                              challenge_type: ChallengeType,
                              difficulty: ChallengeDifficulty,
                              description: str = "",
                              default_target: float = 0.0,
                              default_unit: str = "",
                              default_duration: int = 7,
                              default_points: int = 10,
                              default_xp: int = 20,
                              tips: List[str] = None,
                              instructions: str = "") -> ChallengeTemplate:
        """
        Create a custom template.
        
        Args:
            name: Template name
            category: Challenge category
            challenge_type: Challenge type
            difficulty: Challenge difficulty
            description: Template description
            default_target: Default target value
            default_unit: Default unit
            default_duration: Default duration in days
            default_points: Default points
            default_xp: Default XP
            tips: Tips list
            instructions: Instructions
        
        Returns:
            ChallengeTemplate: Created template
        """
        template = ChallengeTemplate(
            name=name,
            description=description,
            category=category,
            challenge_type=challenge_type,
            difficulty=difficulty,
            default_target=default_target,
            default_unit=default_unit,
            default_duration=default_duration,
            default_points=default_points,
            default_xp=default_xp,
            tips=tips or [],
            instructions=instructions
        )
        
        self.templates.append(template)
        logger.info(f"Created custom template: {name}")
        
        return template