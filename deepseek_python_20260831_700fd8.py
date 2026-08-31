"""
Smart Household Resource Optimization Engine - Optimization Planner
Creates and manages optimization plans.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from optimization.models import (
    OptimizationPlan, OptimizationTarget, OptimizationStatus,
    OptimizationCategory, OptimizationProgress, RecommendationPriority
)

logger = logging.getLogger(__name__)


class OptimizationPlanner:
    """
    Creates and manages optimization plans.
    """
    
    def __init__(self):
        """Initialize the optimization planner."""
        logger.info("Optimization Planner initialized")
    
    def create_optimization_plan(self,
                                household_id: str,
                                name: str,
                                description: str = "",
                                targets: List[Dict[str, Any]] = None) -> OptimizationPlan:
        """
        Create an optimization plan.
        
        Args:
            household_id: Household ID
            name: Plan name
            description: Plan description
            targets: List of targets
        
        Returns:
            OptimizationPlan: Created plan
        """
        plan = OptimizationPlan(
            household_id=household_id,
            name=name,
            description=description,
            status=OptimizationStatus.DRAFT,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if targets:
            for target_data in targets:
                target = OptimizationTarget(
                    plan_id=plan.id,
                    category=target_data.get('category', OptimizationCategory.OTHER),
                    target_value=target_data.get('target_value', 0.0),
                    current_value=target_data.get('current_value', 0.0),
                    unit=target_data.get('unit', ''),
                    deadline=target_data.get('deadline')
                )
                plan.targets.append(target)
        
        logger.info(f"Created optimization plan: {name}")
        return plan
    
    def add_target(self, 
                  plan: OptimizationPlan,
                  category: OptimizationCategory,
                  target_value: float,
                  current_value: float = 0.0,
                  unit: str = "",
                  deadline: Optional[datetime] = None) -> None:
        """
        Add a target to the plan.
        
        Args:
            plan: Optimization plan
            category: Target category
            target_value: Target value
            current_value: Current value
            unit: Unit of measurement
            deadline: Target deadline
        """
        target = OptimizationTarget(
            plan_id=plan.id,
            category=category,
            target_value=target_value,
            current_value=current_value,
            unit=unit,
            deadline=deadline
        )
        plan.targets.append(target)
        plan.updated_at = datetime.now()
        logger.info(f"Added target to plan: {category.value}")
    
    def update_target_progress(self, 
                              target: OptimizationTarget,
                              current_value: float) -> Dict[str, Any]:
        """
        Update target progress.
        
        Args:
            target: Optimization target
            current_value: Current value
        
        Returns:
            Dict: Progress update
        """
        old_value = target.current_value
        target.current_value = current_value
        
        # Check if target is achieved
        if target.target_value > 0:
            if current_value >= target.target_value:
                target.achieved = True
                target.achieved_date = datetime.now()
        
        progress = {
            'old_value': old_value,
            'new_value': current_value,
            'progress_percentage': (current_value / target.target_value * 100) if target.target_value > 0 else 0,
            'achieved': target.achieved
        }
        
        return progress
    
    def calculate_plan_progress(self, plan: OptimizationPlan) -> Dict[str, Any]:
        """
        Calculate overall plan progress.
        
        Args:
            plan: Optimization plan
        
        Returns:
            Dict: Progress metrics
        """
        if not plan.targets:
            return {
                'overall_progress': 0,
                'completed_targets': 0,
                'total_targets': 0,
                'on_track': True,
                'actions_completed': 0,
                'total_actions': 0
            }
        
        completed_targets = sum(1 for t in plan.targets if t.achieved)
        total_targets = len(plan.targets)
        
        # Calculate progress percentage
        progress_percentage = (completed_targets / total_targets) * 100
        
        # Check if on track (assuming targets have deadlines)
        on_track = True
        now = datetime.now()
        
        for target in plan.targets:
            if target.deadline and not target.achieved:
                if target.deadline < now:
                    on_track = False
        
        # Update plan progress
        plan.overall_progress = progress_percentage
        plan.completed_actions = completed_targets
        plan.total_actions = total_targets
        plan.updated_at = datetime.now()
        
        return {
            'overall_progress': progress_percentage,
            'completed_targets': completed_targets,
            'total_targets': total_targets,
            'on_track': on_track,
            'actions_completed': completed_targets,
            'total_actions': total_targets
        }
    
    def generate_progress_report(self, 
                                plan: OptimizationPlan) -> Dict[str, Any]:
        """
        Generate progress report for the plan.
        
        Args:
            plan: Optimization plan
        
        Returns:
            Dict: Progress report
        """
        progress = self.calculate_plan_progress(plan)
        
        target_details = []
        for target in plan.targets:
            target_details.append({
                'category': target.category.value,
                'target_value': target.target_value,
                'current_value': target.current_value,
                'progress': (target.current_value / target.target_value * 100) if target.target_value > 0 else 0,
                'achieved': target.achieved,
                'deadline': target.deadline.isoformat() if target.deadline else None,
                'days_remaining': (target.deadline - datetime.now()).days if target.deadline else None
            })
        
        return {
            'plan_name': plan.name,
            'status': plan.status.value,
            'overall_progress': progress['overall_progress'],
            'completed_targets': progress['completed_targets'],
            'total_targets': progress['total_targets'],
            'on_track': progress['on_track'],
            'targets': target_details,
            'estimated_completion_date': self._estimate_completion_date(plan),
            'estimated_savings': plan.estimated_savings,
            'achieved_savings': plan.achieved_savings
        }
    
    def _estimate_completion_date(self, plan: OptimizationPlan) -> Optional[datetime]:
        """
        Estimate completion date based on progress.
        
        Args:
            plan: Optimization plan
        
        Returns:
            Optional[datetime]: Estimated completion date
        """
        if plan.overall_progress >= 100:
            return datetime.now()
        
        if plan.overall_progress <= 0:
            return None
        
        # Calculate average progress rate per day
        days_since_start = (datetime.now() - plan.created_at).days if plan.created_at else 1
        progress_rate = plan.overall_progress / days_since_start
        
        if progress_rate <= 0:
            return None
        
        remaining_progress = 100 - plan.overall_progress
        days_needed = remaining_progress / progress_rate
        
        return datetime.now() + timedelta(days=days_needed)
    
    def prioritize_actions(self, 
                          plan: OptimizationPlan) -> List[Dict[str, Any]]:
        """
        Prioritize actions in the plan.
        
        Args:
            plan: Optimization plan
        
        Returns:
            List[Dict]: Prioritized actions
        """
        actions = []
        
        for target in plan.targets:
            # Calculate priority score
            urgency = 0
            if target.deadline:
                days_remaining = (target.deadline - datetime.now()).days
                if days_remaining < 7:
                    urgency = 100
                elif days_remaining < 14:
                    urgency = 75
                elif days_remaining < 30:
                    urgency = 50
                else:
                    urgency = 25
            
            importance = 0
            if target.category in [OptimizationCategory.ENERGY_EFFICIENCY, OptimizationCategory.WATER_CONSERVATION]:
                importance = 80
            elif target.category in [OptimizationCategory.WASTE_REDUCTION, OptimizationCategory.TRANSPORTATION_OPTIMIZATION]:
                importance = 60
            else:
                importance = 40
            
            priority_score = (urgency * 0.6) + (importance * 0.4)
            
            actions.append({
                'target_id': target.id,
                'category': target.category.value,
                'target_value': target.target_value,
                'current_value': target.current_value,
                'deadline': target.deadline.isoformat() if target.deadline else None,
                'priority_score': priority_score,
                'priority_label': self._get_priority_label(priority_score),
                'recommended_action': self._get_recommended_action(target)
            })
        
        return sorted(actions, key=lambda x: x['priority_score'], reverse=True)
    
    def _get_priority_label(self, score: float) -> str:
        """
        Get priority label from score.
        """
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_recommended_action(self, target: OptimizationTarget) -> str:
        """
        Get recommended action for a target.
        """
        actions = {
            OptimizationCategory.ENERGY_EFFICIENCY: "Implement energy efficiency measures",
            OptimizationCategory.WATER_CONSERVATION: "Adopt water conservation practices",
            OptimizationCategory.WASTE_REDUCTION: "Increase recycling and reduce waste",
            OptimizationCategory.FOOD_OPTIMIZATION: "Optimize food consumption and reduce waste",
            OptimizationCategory.TRANSPORTATION_OPTIMIZATION: "Switch to sustainable transportation",
            OptimizationCategory.BEHAVIORAL_CHANGE: "Adopt sustainable habits",
            OptimizationCategory.TECHNOLOGY_UPGRADE: "Upgrade to efficient technology"
        }
        return actions.get(target.category, "Take action to achieve target")
    
    def update_plan_status(self, 
                          plan: OptimizationPlan,
                          new_status: OptimizationStatus) -> None:
        """
        Update plan status.
        
        Args:
            plan: Optimization plan
            new_status: New status
        """
        plan.status = new_status
        plan.updated_at = datetime.now()
        
        if new_status == OptimizationStatus.COMPLETED:
            plan.actual_completion_date = datetime.now()
        
        logger.info(f"Updated plan status to {new_status.value}")
    
    def handle_missed_targets(self, plan: OptimizationPlan) -> List[Dict[str, Any]]:
        """
        Handle missed targets in the plan.
        
        Args:
            plan: Optimization plan
        
        Returns:
            List[Dict]: Missed target actions
        """
        missed_actions = []
        
        now = datetime.now()
        
        for target in plan.targets:
            if target.deadline and not target.achieved:
                if target.deadline < now:
                    # Target missed
                    days_overdue = (now - target.deadline).days
                    
                    missed_actions.append({
                        'target_id': target.id,
                        'category': target.category.value,
                        'deadline': target.deadline.isoformat(),
                        'days_overdue': days_overdue,
                        'recommended_action': 'Extend deadline or adjust target',
                        'alternative': self._get_alternative_target(target)
                    })
        
        return missed_actions
    
    def _get_alternative_target(self, target: OptimizationTarget) -> Dict[str, Any]:
        """
        Get alternative target if original is missed.
        """
        # Reduce target by 20%
        new_target = target.target_value * 0.8
        
        return {
            'category': target.category.value,
            'new_target': new_target,
            'original_target': target.target_value,
            'unit': target.unit,
            'reason': 'Original target not achievable within deadline'
        }
    
    def get_plan_summary(self, plan: OptimizationPlan) -> Dict[str, Any]:
        """
        Get plan summary.
        
        Args:
            plan: Optimization plan
        
        Returns:
            Dict: Plan summary
        """
        progress = self.calculate_plan_progress(plan)
        
        return {
            'name': plan.name,
            'description': plan.description,
            'status': plan.status.value,
            'created_at': plan.created_at.isoformat(),
            'updated_at': plan.updated_at.isoformat(),
            'progress': progress['overall_progress'],
            'targets_completed': progress['completed_targets'],
            'targets_total': progress['total_targets'],
            'on_track': progress['on_track'],
            'estimated_completion': self._estimate_completion_date(plan),
            'top_priority': self.prioritize_actions(plan)[:3] if plan.targets else [],
            'missed_targets': len(self.handle_missed_targets(plan)),
            'estimated_savings': plan.estimated_savings,
            'achieved_savings': plan.achieved_savings
        }