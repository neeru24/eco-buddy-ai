"""
Sustainability Lifecycle & Long-Term Progress Management - Roadmap History
Tracks roadmap progress and history.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    RoadmapHistory, SustainabilityEvent, EventType, EventCategory
)

logger = logging.getLogger(__name__)


class RoadmapHistoryManager:
    """
    Manages roadmap history and progress tracking.
    """
    
    def __init__(self):
        """Initialize the roadmap history manager."""
        self.stage_labels = {
            0: 'Discovery',
            1: 'Foundation',
            2: 'Growth',
            3: 'Optimization',
            4: 'Excellence',
            5: 'Leadership'
        }
        logger.info("Roadmap History Manager initialized")
    
    def create_roadmap_history(self,
                              user_id: str,
                              roadmap_id: str,
                              roadmap_name: str,
                              total_stages: int = 5) -> RoadmapHistory:
        """
        Create roadmap history tracking.
        
        Args:
            user_id: User ID
            roadmap_id: Roadmap ID
            roadmap_name: Roadmap name
            total_stages: Total number of stages
        
        Returns:
            RoadmapHistory: Created history
        """
        history = RoadmapHistory(
            user_id=user_id,
            roadmap_id=roadmap_id,
            roadmap_name=roadmap_name,
            total_stages=total_stages,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            status='active',
            current_version=1,
            versions=[{
                'version': 1,
                'created_at': datetime.now().isoformat(),
                'total_stages': total_stages,
                'status': 'created'
            }]
        )
        
        # Initialize stage progress
        for i in range(total_stages):
            history.stage_progress[self.stage_labels.get(i, f'Stage {i+1}')] = 0.0
        
        logger.info(f"Roadmap history created for {roadmap_name}")
        return history
    
    def update_stage_progress(self,
                             history: RoadmapHistory,
                             stage_index: int,
                             progress: float,
                             notes: str = "") -> RoadmapHistory:
        """
        Update progress of a roadmap stage.
        
        Args:
            history: Roadmap history
            stage_index: Stage index
            progress: Progress percentage (0-100)
            notes: Progress notes
        
        Returns:
            RoadmapHistory: Updated history
        """
        stage_label = self.stage_labels.get(stage_index, f'Stage {stage_index+1}')
        
        # Update stage progress
        history.stage_progress[stage_label] = min(100.0, max(0.0, progress))
        
        # Check if stage is completed
        if progress >= 100 and stage_index not in history.completed_stages:
            history.completed_stages.append(stage_index)
            history.milestones_completed += 1
            
            # Add to stage history
            history.stage_history.append({
                'stage': stage_index,
                'stage_name': stage_label,
                'completed_at': datetime.now().isoformat(),
                'progress': progress,
                'notes': notes or f'Stage {stage_label} completed'
            })
        
        # Update current stage
        if stage_index > history.current_stage:
            history.current_stage = stage_index
        
        # Calculate overall progress
        history.progress_percentage = self._calculate_overall_progress(history)
        
        history.updated_at = datetime.now()
        
        logger.info(f"Stage {stage_index} progress updated to {progress}%")
        return history
    
    def record_milestone(self,
                        history: RoadmapHistory,
                        milestone_name: str,
                        description: str = "",
                        stage_index: int = 0) -> RoadmapHistory:
        """
        Record a roadmap milestone.
        
        Args:
            history: Roadmap history
            milestone_name: Milestone name
            description: Milestone description
            stage_index: Associated stage index
        
        Returns:
            RoadmapHistory: Updated history
        """
        history.milestones_total += 1
        history.milestones_completed += 1
        
        history.milestone_details.append({
            'name': milestone_name,
            'description': description,
            'stage': stage_index,
            'completed_at': datetime.now().isoformat()
        })
        
        history.milestone_history.append({
            'milestone': milestone_name,
            'completed_at': datetime.now().isoformat(),
            'stage': stage_index,
            'progress_before': history.progress_percentage,
            'progress_after': self._calculate_overall_progress(history)
        })
        
        history.updated_at = datetime.now()
        
        logger.info(f"Milestone recorded: {milestone_name}")
        return history
    
    def record_alternative_path(self,
                               history: RoadmapHistory,
                               stage_index: int,
                               description: str,
                               reason: str = "") -> RoadmapHistory:
        """
        Record an alternative path taken.
        
        Args:
            history: Roadmap history
            stage_index: Stage where alternative was taken
            description: Alternative description
            reason: Reason for alternative
        
        Returns:
            RoadmapHistory: Updated history
        """
        history.alternatives_taken += 1
        
        history.alternative_paths.append({
            'stage': stage_index,
            'description': description,
            'reason': reason,
            'taken_at': datetime.now().isoformat()
        })
        
        history.updated_at = datetime.now()
        
        logger.info(f"Alternative path recorded at stage {stage_index}")
        return history
    
    def complete_roadmap(self, history: RoadmapHistory) -> RoadmapHistory:
        """
        Mark roadmap as completed.
        
        Args:
            history: Roadmap history
        
        Returns:
            RoadmapHistory: Updated history
        """
        history.status = 'completed'
        history.completed_at = datetime.now()
        
        # Update all remaining stages to 100%
        for stage_label in history.stage_progress:
            if history.stage_progress[stage_label] < 100:
                history.stage_progress[stage_label] = 100.0
        
        history.progress_percentage = 100.0
        history.updated_at = datetime.now()
        
        logger.info(f"Roadmap {history.roadmap_name} completed")
        return history
    
    def archive_roadmap(self, history: RoadmapHistory) -> RoadmapHistory:
        """
        Archive a roadmap.
        
        Args:
            history: Roadmap history
        
        Returns:
            RoadmapHistory: Updated history
        """
        history.status = 'archived'
        history.updated_at = datetime.now()
        
        logger.info(f"Roadmap {history.roadmap_name} archived")
        return history
    
    def _calculate_overall_progress(self, history: RoadmapHistory) -> float:
        """
        Calculate overall roadmap progress.
        """
        if not history.stage_progress:
            return 0.0
        
        total_progress = sum(history.stage_progress.values())
        max_progress = len(history.stage_progress) * 100
        
        return (total_progress / max_progress) * 100
    
    def get_roadmap_summary(self, history: RoadmapHistory) -> Dict[str, Any]:
        """
        Get roadmap summary.
        
        Args:
            history: Roadmap history
        
        Returns:
            Dict: Roadmap summary
        """
        stage_details = []
        for i, (stage_label, progress) in enumerate(history.stage_progress.items()):
            stage_details.append({
                'stage_index': i,
                'stage_name': stage_label,
                'progress': progress,
                'completed': progress >= 100,
                'milestones': [m for m in history.milestone_details if m.get('stage') == i]
            })
        
        return {
            'roadmap_name': history.roadmap_name,
            'status': history.status,
            'progress_percentage': history.progress_percentage,
            'current_stage': history.current_stage,
            'total_stages': history.total_stages,
            'completed_stages': len(history.completed_stages),
            'stages': stage_details,
            'milestones_completed': history.milestones_completed,
            'milestones_total': history.milestones_total,
            'alternatives_taken': history.alternatives_taken,
            'created_at': history.created_at.isoformat(),
            'completed_at': history.completed_at.isoformat() if history.completed_at else None,
            'current_version': history.current_version,
            'versions': history.versions
        }
    
    def get_version_history(self, history: RoadmapHistory) -> List[Dict[str, Any]]:
        """
        Get version history of the roadmap.
        
        Args:
            history: Roadmap history
        
        Returns:
            List[Dict]: Version history
        """
        return history.versions
    
    def generate_roadmap_event(self,
                              history: RoadmapHistory,
                              event_type: str,
                              stage_index: int = 0) -> Optional[SustainabilityEvent]:
        """
        Generate a sustainability event for roadmap progress.
        
        Args:
            history: Roadmap history
            event_type: Event type
            stage_index: Stage index
        
        Returns:
            Optional[SustainabilityEvent]: Generated event
        """
        event_map = {
            'created': EventType.ROADMAP_CREATED,
            'milestone': EventType.ROADMAP_MILESTONE,
            'completed': EventType.ROADMAP_COMPLETED,
            'alternative': EventType.ROADMAP_ALTERNATIVE,
            'stage': EventType.ROADMAP_STAGE
        }
        
        event_type_enum = event_map.get(event_type)
        if not event_type_enum:
            return None
        
        stage_label = self.stage_labels.get(stage_index, f'Stage {stage_index+1}')
        
        title_map = {
            'created': f"Roadmap Created: {history.roadmap_name}",
            'milestone': f"Milestone Reached: Stage {stage_label}",
            'completed': f"Roadmap Completed: {history.roadmap_name}",
            'alternative': f"Alternative Path Taken: {history.roadmap_name}",
            'stage': f"Stage {stage_label} Completed"
        }
        
        return SustainabilityEvent(
            user_id=history.user_id,
            event_type=event_type_enum,
            category=EventCategory.ROADMAP,
            title=title_map.get(event_type, 'Roadmap Update'),
            description=f"Roadmap '{history.roadmap_name}' - {event_type}",
            impact_score=history.progress_percentage,
            importance=4 if event_type in ['completed', 'milestone'] else 3,
            related_entity_id=history.roadmap_id,
            related_entity_type='roadmap',
            metadata={
                'roadmap_id': history.roadmap_id,
                'roadmap_name': history.roadmap_name,
                'stage': stage_index,
                'progress': history.progress_percentage,
                'total_stages': history.total_stages
            }
        )