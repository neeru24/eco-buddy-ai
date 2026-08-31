"""
Sustainability Gamification & Challenge Platform - Recommendation Engine
Recommends challenges based on user data.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from gamification.models import (
    Challenge, ChallengeRecommendation, ChallengeType,
    ChallengeDifficulty, ChallengeCategory, ChallengeStatus,
    ChallengeTemplate
)

logger = logging.getLogger(__name__)


class ChallengeRecommendationEngine:
    """
    Recommends challenges based on user data.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        self.recommendation_weights = {
            'habit_match': 0.3,
            'goal_match': 0.25,
            'roadmap_match': 0.2,
            'difficulty_appropriate': 0.15,
            'diversity': 0.1
        }
        logger.info("Challenge Recommendation Engine initialized")
    
    def generate_recommendations(self,
                                user_id: str,
                                available_challenges: List[Challenge],
                                completed_challenges: List[str],
                                user_habits: List[Dict[str, Any]],
                                user_goals: List[Dict[str, Any]],
                                roadmap_progress: Dict[str, Any],
                                user_level: int) -> List[ChallengeRecommendation]:
        """
        Generate challenge recommendations for a user.
        
        Args:
            user_id: User ID
            available_challenges: List of available challenges
            completed_challenges: List of completed challenge IDs
            user_habits: List of user habits
            user_goals: List of user goals
            roadmap_progress: Roadmap progress data
            user_level: User's current level
        
        Returns:
            List[ChallengeRecommendation]: Recommendations
        """
        recommendations = []
        
        # Filter out completed challenges
        available = [c for c in available_challenges if c.id not in completed_challenges]
        
        if not available:
            return recommendations
        
        for challenge in available:
            # Calculate recommendation score
            score = self._calculate_score(challenge, user_habits, user_goals, roadmap_progress, user_level)
            
            # Generate reason
            reason = self._generate_reason(challenge, user_habits, user_goals, roadmap_progress)
            
            # Determine priority
            priority = self._determine_priority(score)
            
            recommendation = ChallengeRecommendation(
                user_id=user_id,
                challenge_id=challenge.id,
                challenge_title=challenge.title,
                reason=reason,
                confidence=score / 100,
                priority=priority,
                based_on_habits=self._match_habits(challenge, user_habits),
                based_on_goals=self._match_goals(challenge, user_goals),
                based_on_roadmap=self._match_roadmap(challenge, roadmap_progress)
            )
            
            recommendations.append(recommendation)
        
        # Sort by confidence and priority
        recommendations.sort(key=lambda r: (r.confidence, r.priority), reverse=True)
        
        return recommendations[:10]  # Top 10 recommendations
    
    def _calculate_score(self,
                        challenge: Challenge,
                        user_habits: List[Dict[str, Any]],
                        user_goals: List[Dict[str, Any]],
                        roadmap_progress: Dict[str, Any],
                        user_level: int) -> float:
        """
        Calculate recommendation score.
        """
        score = 0.0
        
        # Habit match
        habit_score = self._calculate_habit_match(challenge, user_habits)
        score += habit_score * self.recommendation_weights['habit_match']
        
        # Goal match
        goal_score = self._calculate_goal_match(challenge, user_goals)
        score += goal_score * self.recommendation_weights['goal_match']
        
        # Roadmap match
        roadmap_score = self._calculate_roadmap_match(challenge, roadmap_progress)
        score += roadmap_score * self.recommendation_weights['roadmap_match']
        
        # Difficulty appropriateness
        difficulty_score = self._calculate_difficulty_score(challenge, user_level)
        score += difficulty_score * self.recommendation_weights['difficulty_appropriate']
        
        # Diversity
        diversity_score = self._calculate_diversity_score(challenge)
        score += diversity_score * self.recommendation_weights['diversity']
        
        return score
    
    def _calculate_habit_match(self,
                              challenge: Challenge,
                              user_habits: List[Dict[str, Any]]) -> float:
        """
        Calculate habit match score.
        """
        if not user_habits:
            return 0.0
        
        match_count = 0
        total = len(user_habits)
        
        for habit in user_habits:
            habit_category = habit.get('category', '')
            habit_name = habit.get('name', '').lower()
            
            # Check if habit matches challenge
            if challenge.category.value == habit_category:
                match_count += 1
            elif habit_name in challenge.title.lower():
                match_count += 0.5
        
        return min(100, (match_count / total) * 100) if total > 0 else 0
    
    def _calculate_goal_match(self,
                             challenge: Challenge,
                             user_goals: List[Dict[str, Any]]) -> float:
        """
        Calculate goal match score.
        """
        if not user_goals:
            return 0.0
        
        match_count = 0
        total = len(user_goals)
        
        for goal in user_goals:
            goal_category = goal.get('category', '')
            goal_title = goal.get('title', '').lower()
            
            if challenge.category.value == goal_category:
                match_count += 1
            elif goal_title in challenge.title.lower():
                match_count += 0.5
        
        return min(100, (match_count / total) * 100) if total > 0 else 0
    
    def _calculate_roadmap_match(self,
                               challenge: Challenge,
                               roadmap_progress: Dict[str, Any]) -> float:
        """
        Calculate roadmap match score.
        """
        if not roadmap_progress:
            return 50.0
        
        # If challenge matches current roadmap stage
        current_stage = roadmap_progress.get('current_stage', 0)
        total_stages = roadmap_progress.get('total_stages', 5)
        
        if total_stages > 0:
            stage_progress = (current_stage / total_stages) * 100
            
            # Challenges that match the current stage get higher scores
            if challenge.difficulty.value == self._get_difficulty_for_stage(current_stage, total_stages):
                return 80.0 + (stage_progress * 0.2)
        
        return 50.0
    
    def _get_difficulty_for_stage(self, current_stage: int, total_stages: int) -> str:
        """
        Get appropriate difficulty for a roadmap stage.
        """
        progress = current_stage / total_stages
        
        if progress < 0.3:
            return 'beginner'
        elif progress < 0.6:
            return 'intermediate'
        elif progress < 0.8:
            return 'advanced'
        else:
            return 'expert'
    
    def _calculate_difficulty_score(self,
                                   challenge: Challenge,
                                   user_level: int) -> float:
        """
        Calculate difficulty appropriateness score.
        """
        difficulty_levels = {
            ChallengeDifficulty.BEGINNER: 1,
            ChallengeDifficulty.INTERMEDIATE: 2,
            ChallengeDifficulty.ADVANCED: 3,
            ChallengeDifficulty.EXPERT: 4
        }
        
        challenge_level = difficulty_levels.get(challenge.difficulty, 1)
        
        # User level maps to difficulty
        if user_level <= 2:
            recommended = 1
        elif user_level <= 5:
            recommended = 2
        elif user_level <= 10:
            recommended = 3
        else:
            recommended = 4
        
        # Score based on how close the challenge difficulty is to recommended
        diff = abs(challenge_level - recommended)
        
        if diff == 0:
            return 100.0
        elif diff == 1:
            return 70.0
        elif diff == 2:
            return 40.0
        else:
            return 10.0
    
    def _calculate_diversity_score(self, challenge: Challenge) -> float:
        """
        Calculate diversity score to ensure varied recommendations.
        """
        # Randomize slightly to ensure diversity
        return 50.0 + (random.random() * 20)
    
    def _generate_reason(self,
                        challenge: Challenge,
                        user_habits: List[Dict[str, Any]],
                        user_goals: List[Dict[str, Any]],
                        roadmap_progress: Dict[str, Any]) -> str:
        """
        Generate recommendation reason.
        """
        reasons = []
        
        # Based on habits
        if user_habits:
            matched_habits = self._match_habits(challenge, user_habits)
            if matched_habits:
                reasons.append(f"Matches your habit: {matched_habits[0]}")
        
        # Based on goals
        if user_goals:
            matched_goals = self._match_goals(challenge, user_goals)
            if matched_goals:
                reasons.append(f"Aligns with your goal: {matched_goals[0]}")
        
        # Based on roadmap
        if roadmap_progress:
            reasons.append("Fits your current roadmap stage")
        
        # General reason
        if not reasons:
            reasons.append(f"Good challenge for your level ({challenge.difficulty.value})")
        
        return "; ".join(reasons[:2])
    
    def _match_habits(self,
                     challenge: Challenge,
                     user_habits: List[Dict[str, Any]]) -> List[str]:
        """
        Get matching habits for a challenge.
        """
        matches = []
        for habit in user_habits:
            if challenge.category.value == habit.get('category', ''):
                matches.append(habit.get('name', ''))
        return matches
    
    def _match_goals(self,
                    challenge: Challenge,
                    user_goals: List[Dict[str, Any]]) -> List[str]:
        """
        Get matching goals for a challenge.
        """
        matches = []
        for goal in user_goals:
            if challenge.category.value == goal.get('category', ''):
                matches.append(goal.get('title', ''))
        return matches
    
    def _match_roadmap(self,
                      challenge: Challenge,
                      roadmap_progress: Dict[str, Any]) -> List[str]:
        """
        Get matching roadmap items for a challenge.
        """
        matches = []
        if roadmap_progress:
            current_stage = roadmap_progress.get('current_stage', 0)
            if current_stage >= 0:
                matches.append(f"Stage {current_stage + 1}")
        return matches
    
    def _determine_priority(self, score: float) -> int:
        """
        Determine recommendation priority.
        """
        if score >= 80:
            return 1  # Highest
        elif score >= 60:
            return 2
        elif score >= 40:
            return 3
        else:
            return 4
    
    def get_top_recommendations(self,
                               recommendations: List[ChallengeRecommendation],
                               limit: int = 5) -> List[ChallengeRecommendation]:
        """
        Get top recommendations.
        
        Args:
            recommendations: List of recommendations
            limit: Number to return
        
        Returns:
            List[ChallengeRecommendation]: Top recommendations
        """
        sorted_recs = sorted(recommendations, key=lambda r: (r.confidence, -r.priority), reverse=True)
        return sorted_recs[:limit]