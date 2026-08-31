"""
Sustainability Gamification & Challenge Platform - Challenge Manager
Manages challenge creation, validation, and lifecycle.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import random

from gamification.models import (
    Challenge, ChallengeType, ChallengeDifficulty, ChallengeStatus,
    ChallengeCategory, ChallengeProgress, ChallengeTemplate
)

logger = logging.getLogger(__name__)


class ChallengeManager:
    """
    Manages sustainability challenges.
    """
    
    def __init__(self):
        """Initialize the challenge manager."""
        self.valid_transitions = self._initialize_valid_transitions()
        logger.info("Challenge Manager initialized")
    
    def _initialize_valid_transitions(self) -> Dict[ChallengeStatus, List[ChallengeStatus]]:
        """
        Initialize valid status transitions.
        """
        return {
            ChallengeStatus.DRAFT: [ChallengeStatus.ACTIVE, ChallengeStatus.CANCELLED],
            ChallengeStatus.ACTIVE: [ChallengeStatus.IN_PROGRESS, ChallengeStatus.CANCELLED],
            ChallengeStatus.IN_PROGRESS: [ChallengeStatus.COMPLETED, ChallengeStatus.FAILED, ChallengeStatus.EXPIRED],
            ChallengeStatus.COMPLETED: [],
            ChallengeStatus.FAILED: [],
            ChallengeStatus.EXPIRED: [],
            ChallengeStatus.CANCELLED: []
        }
    
    def create_challenge(self,
                        title: str,
                        description: str,
                        category: ChallengeCategory,
                        challenge_type: ChallengeType,
                        difficulty: ChallengeDifficulty,
                        target_value: float,
                        unit: str,
                        duration_days: int = 7,
                        created_by: str = "",
                        **kwargs) -> Challenge:
        """
        Create a new challenge.
        
        Args:
            title: Challenge title
            description: Challenge description
            category: Challenge category
            challenge_type: Challenge type
            difficulty: Challenge difficulty
            target_value: Target value
            unit: Unit of measurement
            duration_days: Duration in days
            created_by: Creator user ID
            **kwargs: Additional fields
        
        Returns:
            Challenge: Created challenge
        """
        challenge = Challenge(
            title=title,
            description=description,
            category=category,
            challenge_type=challenge_type,
            difficulty=difficulty,
            target_value=target_value,
            unit=unit,
            duration_days=duration_days,
            start_date=kwargs.get('start_date', datetime.now()),
            end_date=kwargs.get('end_date', datetime.now() + timedelta(days=duration_days)),
            required_progress=target_value,
            base_points=kwargs.get('base_points', self._get_default_points(difficulty)),
            xp_reward=kwargs.get('xp_reward', self._get_default_xp(difficulty)),
            estimated_carbon_savings=kwargs.get('estimated_carbon_savings', 0.0),
            estimated_water_savings=kwargs.get('estimated_water_savings', 0.0),
            estimated_waste_reduction=kwargs.get('estimated_waste_reduction', 0.0),
            completion_criteria=kwargs.get('completion_criteria', f"Complete {target_value} {unit}"),
            requires_verification=kwargs.get('requires_verification', False),
            verification_method=kwargs.get('verification_method', ''),
            created_by=created_by,
            tags=kwargs.get('tags', []),
            notes=kwargs.get('notes', '')
        )
        
        logger.info(f"Created challenge: {title}")
        return challenge
    
    def _get_default_points(self, difficulty: ChallengeDifficulty) -> int:
        """
        Get default points based on difficulty.
        """
        points_map = {
            ChallengeDifficulty.BEGINNER: 10,
            ChallengeDifficulty.INTERMEDIATE: 25,
            ChallengeDifficulty.ADVANCED: 50,
            ChallengeDifficulty.EXPERT: 100
        }
        return points_map.get(difficulty, 10)
    
    def _get_default_xp(self, difficulty: ChallengeDifficulty) -> int:
        """
        Get default XP based on difficulty.
        """
        xp_map = {
            ChallengeDifficulty.BEGINNER: 20,
            ChallengeDifficulty.INTERMEDIATE: 50,
            ChallengeDifficulty.ADVANCED: 100,
            ChallengeDifficulty.EXPERT: 200
        }
        return xp_map.get(difficulty, 20)
    
    def validate_challenge(self, challenge: Challenge) -> Dict[str, Any]:
        """
        Validate a challenge.
        
        Args:
            challenge: Challenge to validate
        
        Returns:
            Dict: Validation results
        """
        errors = []
        warnings = []
        
        # Check required fields
        if not challenge.title:
            errors.append("Challenge title is required")
        
        if not challenge.description:
            warnings.append("Challenge description is recommended")
        
        if challenge.target_value <= 0:
            errors.append("Target value must be greater than 0")
        
        if challenge.duration_days < 1:
            errors.append("Duration must be at least 1 day")
        
        if challenge.end_date <= challenge.start_date:
            errors.append("End date must be after start date")
        
        if challenge.difficulty not in ChallengeDifficulty:
            errors.append("Invalid difficulty level")
        
        if challenge.category not in ChallengeCategory:
            errors.append("Invalid category")
        
        # Check for completion criteria
        if not challenge.completion_criteria:
            warnings.append("Completion criteria is recommended")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }
    
    def update_challenge_status(self,
                               challenge: Challenge,
                               new_status: ChallengeStatus,
                               notes: str = "") -> bool:
        """
        Update challenge status.
        
        Args:
            challenge: Challenge to update
            new_status: New status
            notes: Status change notes
        
        Returns:
            bool: True if status updated successfully
        """
        if not self._is_valid_transition(challenge.status, new_status):
            logger.warning(f"Invalid transition: {challenge.status.value} -> {new_status.value}")
            return False
        
        old_status = challenge.status
        challenge.status = new_status
        challenge.updated_at = datetime.now()
        
        if new_status == ChallengeStatus.COMPLETED:
            challenge.completed_at = datetime.now()
            challenge.progress_percentage = 100.0
        
        logger.info(f"Challenge status updated: {old_status.value} -> {new_status.value}")
        return True
    
    def _is_valid_transition(self, from_status: ChallengeStatus, to_status: ChallengeStatus) -> bool:
        """
        Check if status transition is valid.
        """
        if from_status not in self.valid_transitions:
            return False
        return to_status in self.valid_transitions[from_status]
    
    def update_challenge_progress(self,
                                 challenge: Challenge,
                                 progress: float,
                                 notes: str = "") -> Dict[str, Any]:
        """
        Update challenge progress.
        
        Args:
            challenge: Challenge to update
            progress: Current progress
            notes: Progress notes
        
        Returns:
            Dict: Progress update result
        """
        old_progress = challenge.current_progress
        challenge.current_progress = min(challenge.required_progress, progress)
        challenge.progress_percentage = challenge.calculate_progress()
        challenge.updated_at = datetime.now()
        
        # Check if completed
        if challenge.progress_percentage >= 100 and challenge.status != ChallengeStatus.COMPLETED:
            self.update_challenge_status(challenge, ChallengeStatus.COMPLETED, "Progress reached 100%")
        
        return {
            'old_progress': old_progress,
            'new_progress': challenge.current_progress,
            'progress_percentage': challenge.progress_percentage,
            'completed': challenge.progress_percentage >= 100
        }
    
    def get_active_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """
        Get active challenges.
        
        Args:
            challenges: List of challenges
        
        Returns:
            List[Challenge]: Active challenges
        """
        now = datetime.now()
        return [c for c in challenges if c.status in [ChallengeStatus.ACTIVE, ChallengeStatus.IN_PROGRESS] and c.start_date <= now <= c.end_date]
    
    def get_available_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """
        Get available challenges for participation.
        
        Args:
            challenges: List of challenges
        
        Returns:
            List[Challenge]: Available challenges
        """
        now = datetime.now()
        return [c for c in challenges if c.status in [ChallengeStatus.ACTIVE, ChallengeStatus.IN_PROGRESS] and c.start_date <= now and c.end_date >= now]
    
    def get_completed_challenges(self, challenges: List[Challenge]) -> List[Challenge]:
        """
        Get completed challenges.
        
        Args:
            challenges: List of challenges
        
        Returns:
            List[Challenge]: Completed challenges
        """
        return [c for c in challenges if c.status == ChallengeStatus.COMPLETED]
    
    def get_challenges_by_category(self, challenges: List[Challenge], category: ChallengeCategory) -> List[Challenge]:
        """
        Get challenges by category.
        
        Args:
            challenges: List of challenges
            category: Category to filter
        
        Returns:
            List[Challenge]: Filtered challenges
        """
        return [c for c in challenges if c.category == category]
    
    def get_challenges_by_difficulty(self, challenges: List[Challenge], difficulty: ChallengeDifficulty) -> List[Challenge]:
        """
        Get challenges by difficulty.
        
        Args:
            challenges: List of challenges
            difficulty: Difficulty to filter
        
        Returns:
            List[Challenge]: Filtered challenges
        """
        return [c for c in challenges if c.difficulty == difficulty]
    
    def get_challenges_by_type(self, challenges: List[Challenge], challenge_type: ChallengeType) -> List[Challenge]:
        """
        Get challenges by type.
        
        Args:
            challenges: List of challenges
            challenge_type: Type to filter
        
        Returns:
            List[Challenge]: Filtered challenges
        """
        return [c for c in challenges if c.challenge_type == challenge_type]
    
    def get_challenge_summary(self, challenge: Challenge) -> Dict[str, Any]:
        """
        Get challenge summary.
        
        Args:
            challenge: Challenge to summarize
        
        Returns:
            Dict: Challenge summary
        """
        days_remaining = (challenge.end_date - datetime.now()).days
        days_total = (challenge.end_date - challenge.start_date).days
        
        return {
            'id': challenge.id,
            'title': challenge.title,
            'category': challenge.category.value,
            'difficulty': challenge.difficulty.value,
            'status': challenge.status.value,
            'progress_percentage': challenge.progress_percentage,
            'current_progress': challenge.current_progress,
            'target_value': challenge.target_value,
            'unit': challenge.unit,
            'days_remaining': max(0, days_remaining),
            'days_total': days_total,
            'points': challenge.base_points + challenge.bonus_points,
            'xp': challenge.xp_reward,
            'estimated_impact': {
                'carbon': challenge.estimated_carbon_savings,
                'water': challenge.estimated_water_savings,
                'waste': challenge.estimated_waste_reduction
            },
            'completion_criteria': challenge.completion_criteria,
            'start_date': challenge.start_date.isoformat(),
            'end_date': challenge.end_date.isoformat()
        }
    
    def generate_daily_challenges(self, user_id: str, count: int = 5) -> List[Challenge]:
        """
        Generate daily challenges for a user.
        
        Args:
            user_id: User ID
            count: Number of challenges to generate
        
        Returns:
            List[Challenge]: Generated challenges
        """
        challenges = []
        
        # Challenge templates
        daily_templates = [
            {
                'title': 'Reduce Energy Usage',
                'description': 'Reduce your daily energy consumption by 10%',
                'category': ChallengeCategory.ENERGY,
                'target_value': 10.0,
                'unit': '%',
                'estimated_carbon_savings': 2.0
            },
            {
                'title': 'Save Water',
                'description': 'Reduce water usage by using 5 fewer liters today',
                'category': ChallengeCategory.WATER,
                'target_value': 5.0,
                'unit': 'liters',
                'estimated_water_savings': 5.0
            },
            {
                'title': 'Reduce Waste',
                'description': 'Create 20% less waste today through recycling and reuse',
                'category': ChallengeCategory.WASTE,
                'target_value': 20.0,
                'unit': '%',
                'estimated_waste_reduction': 0.5
            },
            {
                'title': 'Walk More',
                'description': 'Walk at least 2 km instead of driving',
                'category': ChallengeCategory.TRANSPORTATION,
                'target_value': 2.0,
                'unit': 'km',
                'estimated_carbon_savings': 1.5
            },
            {
                'title': 'Meatless Meal',
                'description': 'Have at least one meatless meal today',
                'category': ChallengeCategory.FOOD,
                'target_value': 1.0,
                'unit': 'meal',
                'estimated_carbon_savings': 3.0
            },
            {
                'title': 'Recycle Challenge',
                'description': 'Recycle at least 5 items today',
                'category': ChallengeCategory.RECYCLING,
                'target_value': 5.0,
                'unit': 'items',
                'estimated_waste_reduction': 1.0
            },
            {
                'title': 'Composting',
                'description': 'Add food waste to compost today',
                'category': ChallengeCategory.COMPOSTING,
                'target_value': 1.0,
                'unit': 'day',
                'estimated_waste_reduction': 0.3
            },
            {
                'title': 'Shop Local',
                'description': 'Buy at least one locally produced item today',
                'category': ChallengeCategory.SHOPPING,
                'target_value': 1.0,
                'unit': 'item',
                'estimated_carbon_savings': 1.0
            }
        ]
        
        # Randomly select templates
        selected = random.sample(daily_templates, min(count, len(daily_templates)))
        
        for template in selected:
            challenge = self.create_challenge(
                title=template['title'],
                description=template['description'],
                category=template['category'],
                challenge_type=ChallengeType.DAILY,
                difficulty=ChallengeDifficulty.BEGINNER,
                target_value=template['target_value'],
                unit=template['unit'],
                duration_days=1,
                created_by=user_id,
                base_points=10,
                xp_reward=20,
                estimated_carbon_savings=template.get('estimated_carbon_savings', 0.0),
                estimated_water_savings=template.get('estimated_water_savings', 0.0),
                estimated_waste_reduction=template.get('estimated_waste_reduction', 0.0),
                completion_criteria=f"Complete {template['target_value']} {template['unit']}"
            )
            challenge.status = ChallengeStatus.ACTIVE
            challenges.append(challenge)
        
        return challenges