"""
Sustainability Lifecycle & Long-Term Progress Management - Decision History
Tracks sustainability decisions and their outcomes.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    DecisionHistory, RecommendationHistory, SustainabilityEvent,
    EventType, EventCategory
)

logger = logging.getLogger(__name__)


class DecisionHistoryManager:
    """
    Manages decision and recommendation history.
    """
    
    def __init__(self):
        """Initialize the decision history manager."""
        self.decision_categories = self._initialize_decision_categories()
        logger.info("Decision History Manager initialized")
    
    def _initialize_decision_categories(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize decision categories.
        """
        return {
            'purchase': {
                'name': 'Purchase Decision',
                'icon': '🛒',
                'impact_areas': ['carbon', 'cost', 'waste']
            },
            'habit_change': {
                'name': 'Habit Change',
                'icon': '🔄',
                'impact_areas': ['carbon', 'water', 'waste']
            },
            'lifestyle': {
                'name': 'Lifestyle Change',
                'icon': '🧘',
                'impact_areas': ['carbon', 'water', 'waste', 'cost']
            },
            'investment': {
                'name': 'Investment',
                'icon': '💰',
                'impact_areas': ['carbon', 'cost']
            },
            'transportation': {
                'name': 'Transportation Choice',
                'icon': '🚗',
                'impact_areas': ['carbon', 'cost']
            },
            'energy': {
                'name': 'Energy Decision',
                'icon': '⚡',
                'impact_areas': ['carbon', 'cost']
            },
            'food': {
                'name': 'Food Choice',
                'icon': '🥗',
                'impact_areas': ['carbon', 'water', 'waste']
            }
        }
    
    def record_decision(self,
                       user_id: str,
                       decision_type: str,
                       title: str,
                       description: str,
                       chosen_option: str,
                       alternatives: List[str] = None,
                       reason: str = "",
                       **kwargs) -> DecisionHistory:
        """
        Record a sustainability decision.
        
        Args:
            user_id: User ID
            decision_type: Type of decision
            title: Decision title
            description: Decision description
            chosen_option: Chosen option
            alternatives: Alternatives considered
            reason: Decision reason
            **kwargs: Additional fields
        
        Returns:
            DecisionHistory: Recorded decision
        """
        decision = DecisionHistory(
            user_id=user_id,
            decision_type=decision_type,
            title=title,
            description=description,
            category=kwargs.get('category', 'general'),
            decision_date=kwargs.get('decision_date', datetime.now()),
            alternatives_considered=alternatives or [],
            chosen_option=chosen_option,
            reason=reason,
            decision_context=kwargs.get('context', ''),
            related_recommendation_id=kwargs.get('recommendation_id', ''),
            related_goal_id=kwargs.get('goal_id', ''),
            is_recurring=kwargs.get('is_recurring', False),
            recurrence_frequency=kwargs.get('recurrence_frequency', ''),
            notes=kwargs.get('notes', '')
        )
        
        logger.info(f"Decision recorded: {title} for user {user_id}")
        return decision
    
    def update_decision_outcome(self,
                               decision: DecisionHistory,
                               successful: bool,
                               impact_score: float,
                               carbon_impact: float = 0.0,
                               water_impact: float = 0.0,
                               waste_impact: float = 0.0,
                               cost_impact: float = 0.0,
                               description: str = "") -> DecisionHistory:
        """
        Update decision outcome.
        
        Args:
            decision: Decision to update
            successful: Whether outcome was successful
            impact_score: Impact score (0-100)
            carbon_impact: Carbon impact (kg)
            water_impact: Water impact (liters)
            waste_impact: Waste impact (kg)
            cost_impact: Cost impact ($)
            description: Outcome description
        
        Returns:
            DecisionHistory: Updated decision
        """
        decision.outcome_successful = successful
        decision.outcome_impact_score = impact_score
        decision.outcome_description = description
        decision.outcome_date = datetime.now()
        decision.carbon_impact_kg = carbon_impact
        decision.water_impact_liters = water_impact
        decision.waste_impact_kg = waste_impact
        decision.cost_impact = cost_impact
        decision.sustainability_impact = impact_score
        
        # Calculate effectiveness rating
        if successful:
            decision.effectiveness_rating = min(100, impact_score * 0.8 + 20)
        else:
            decision.effectiveness_rating = max(0, impact_score * 0.5)
        
        logger.info(f"Decision outcome updated: {decision.title}")
        return decision
    
    def record_recommendation(self,
                             user_id: str,
                             recommendation_id: str,
                             recommendation_text: str,
                             category: str,
                             source: str = "system",
                             confidence: float = 0.5,
                             expected_impact: float = 0.0) -> RecommendationHistory:
        """
        Record a recommendation received.
        
        Args:
            user_id: User ID
            recommendation_id: Recommendation ID
            recommendation_text: Recommendation text
            category: Recommendation category
            source: Recommendation source
            confidence: Confidence level
            expected_impact: Expected impact
        
        Returns:
            RecommendationHistory: Recorded recommendation
        """
        rec = RecommendationHistory(
            user_id=user_id,
            recommendation_id=recommendation_id,
            recommendation_text=recommendation_text,
            category=category,
            received_date=datetime.now(),
            expected_impact=expected_impact,
            source=source,
            confidence=confidence,
            effectiveness_rating=0.0
        )
        
        logger.info(f"Recommendation recorded: {recommendation_text[:30]}...")
        return rec
    
    def accept_recommendation(self, rec: RecommendationHistory) -> RecommendationHistory:
        """
        Mark a recommendation as accepted.
        
        Args:
            rec: Recommendation to accept
        
        Returns:
            RecommendationHistory: Updated recommendation
        """
        rec.was_accepted = True
        rec.accepted_at = datetime.now()
        rec.reviewed_at = datetime.now()
        
        logger.info(f"Recommendation accepted: {rec.recommendation_text[:30]}...")
        return rec
    
    def reject_recommendation(self, rec: RecommendationHistory) -> RecommendationHistory:
        """
        Mark a recommendation as rejected.
        
        Args:
            rec: Recommendation to reject
        
        Returns:
            RecommendationHistory: Updated recommendation
        """
        rec.was_accepted = False
        rec.rejected_at = datetime.now()
        
        logger.info(f"Recommendation rejected: {rec.recommendation_text[:30]}...")
        return rec
    
    def implement_recommendation(self, rec: RecommendationHistory, notes: str = "") -> RecommendationHistory:
        """
        Mark a recommendation as implemented.
        
        Args:
            rec: Recommendation to implement
            notes: Implementation notes
        
        Returns:
            RecommendationHistory: Updated recommendation
        """
        rec.was_implemented = True
        rec.implemented_at = datetime.now()
        rec.implementation_notes = notes
        
        logger.info(f"Recommendation implemented: {rec.recommendation_text[:30]}...")
        return rec
    
    def update_recommendation_outcome(self,
                                     rec: RecommendationHistory,
                                     successful: bool,
                                     actual_impact: float,
                                     outcome_score: float = 0.0) -> RecommendationHistory:
        """
        Update recommendation outcome.
        
        Args:
            rec: Recommendation to update
            successful: Whether outcome was successful
            actual_impact: Actual impact achieved
            outcome_score: Outcome score (0-100)
        
        Returns:
            RecommendationHistory: Updated recommendation
        """
        rec.outcome_successful = successful
        rec.outcome_score = outcome_score or (actual_impact / (rec.expected_impact + 0.001)) * 100
        rec.actual_impact = actual_impact
        rec.impact_difference = actual_impact - rec.expected_impact
        rec.impact_difference_percentage = (rec.impact_difference / (rec.expected_impact + 0.001)) * 100
        rec.effectiveness_rating = min(100, rec.outcome_score)
        
        logger.info(f"Recommendation outcome updated: {rec.recommendation_text[:30]}...")
        return rec
    
    def get_decision_summary(self, decisions: List[DecisionHistory]) -> Dict[str, Any]:
        """
        Get summary of decisions.
        
        Args:
            decisions: List of decisions
        
        Returns:
            Dict: Decision summary
        """
        if not decisions:
            return {'total': 0, 'success_rate': 0}
        
        successful = sum(1 for d in decisions if d.outcome_successful)
        total = len(decisions)
        
        # Group by type
        by_type = {}
        for decision in decisions:
            if decision.decision_type not in by_type:
                by_type[decision.decision_type] = {'total': 0, 'successful': 0}
            by_type[decision.decision_type]['total'] += 1
            if decision.outcome_successful:
                by_type[decision.decision_type]['successful'] += 1
        
        # Calculate impact totals
        total_carbon = sum(d.carbon_impact_kg for d in decisions)
        total_water = sum(d.water_impact_liters for d in decisions)
        total_waste = sum(d.waste_impact_kg for d in decisions)
        total_cost = sum(d.cost_impact for d in decisions)
        
        return {
            'total': total,
            'successful': successful,
            'success_rate': (successful / total * 100) if total > 0 else 0,
            'by_type': by_type,
            'total_carbon_saved': total_carbon,
            'total_water_saved': total_water,
            'total_waste_reduced': total_waste,
            'total_cost_saved': total_cost,
            'average_effectiveness': sum(d.effectiveness_rating for d in decisions) / total if total > 0 else 0
        }
    
    def get_recommendation_summary(self, recommendations: List[RecommendationHistory]) -> Dict[str, Any]:
        """
        Get summary of recommendations.
        
        Args:
            recommendations: List of recommendations
        
        Returns:
            Dict: Recommendation summary
        """
        if not recommendations:
            return {'total': 0, 'acceptance_rate': 0}
        
        accepted = sum(1 for r in recommendations if r.was_accepted)
        implemented = sum(1 for r in recommendations if r.was_implemented)
        successful = sum(1 for r in recommendations if r.outcome_successful)
        
        # Group by category
        by_category = {}
        for rec in recommendations:
            if rec.category not in by_category:
                by_category[rec.category] = {'total': 0, 'accepted': 0, 'successful': 0}
            by_category[rec.category]['total'] += 1
            if rec.was_accepted:
                by_category[rec.category]['accepted'] += 1
            if rec.outcome_successful:
                by_category[rec.category]['successful'] += 1
        
        return {
            'total': len(recommendations),
            'accepted': accepted,
            'acceptance_rate': (accepted / len(recommendations) * 100) if recommendations else 0,
            'implemented': implemented,
            'implementation_rate': (implemented / len(recommendations) * 100) if recommendations else 0,
            'successful': successful,
            'success_rate': (successful / len(recommendations) * 100) if recommendations else 0,
            'by_category': by_category,
            'average_effectiveness': sum(r.effectiveness_rating for r in recommendations) / len(recommendations) if recommendations else 0
        }
    
    def generate_decision_event(self, decision: DecisionHistory) -> SustainabilityEvent:
        """
        Generate a sustainability event from a decision.
        
        Args:
            decision: Decision to convert
        
        Returns:
            SustainabilityEvent: Generated event
        """
        return SustainabilityEvent(
            user_id=decision.user_id,
            event_type=EventType.DECISION_MADE,
            category=EventCategory.DECISIONS,
            title=f"Decision Made: {decision.title}",
            description=decision.description,
            impact_score=decision.outcome_impact_score if decision.outcome_impact_score else 50,
            importance=3,
            related_entity_id=decision.id,
            related_entity_type='decision',
            metadata={
                'decision_type': decision.decision_type,
                'chosen_option': decision.chosen_option,
                'alternatives': decision.alternatives_considered,
                'successful': decision.outcome_successful
            }
        )