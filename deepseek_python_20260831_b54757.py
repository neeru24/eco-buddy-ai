"""
Sustainability Lifecycle & Long-Term Progress Management - Timeline Generator
Generates interactive timelines of sustainability events.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from lifecycle.models import (
    SustainabilityEvent, EventType, EventCategory, TimelinePeriod,
    MilestoneEvent, SustainabilityReport
)

logger = logging.getLogger(__name__)


class TimelineGenerator:
    """
    Generates interactive timelines of sustainability events.
    """
    
    def __init__(self):
        """Initialize the timeline generator."""
        self.event_icons = self._initialize_event_icons()
        self.event_colors = self._initialize_event_colors()
        self.event_weights = self._initialize_event_weights()
        logger.info("Timeline Generator initialized")
    
    def _initialize_event_icons(self) -> Dict[EventType, str]:
        """Initialize icons for different event types."""
        return {
            # Goal events
            EventType.GOAL_CREATED: "🎯",
            EventType.GOAL_COMPLETED: "🏆",
            EventType.GOAL_MODIFIED: "📝",
            EventType.GOAL_POSTPONED: "⏸️",
            EventType.GOAL_FAILED: "❌",
            EventType.GOAL_RECOVERED: "🔄",
            EventType.GOAL_PROGRESS: "📈",
            
            # Habit events
            EventType.HABIT_ADOPTED: "🌟",
            EventType.HABIT_IMPROVED: "📈",
            EventType.HABIT_REGRESSED: "📉",
            EventType.HABIT_BROKEN: "💔",
            EventType.HABIT_RECOVERED: "❤️‍🩹",
            EventType.HABIT_STREAK: "🔥",
            
            # Roadmap events
            EventType.ROADMAP_CREATED: "🗺️",
            EventType.ROADMAP_MILESTONE: "📍",
            EventType.ROADMAP_COMPLETED: "✅",
            EventType.ROADMAP_ALTERNATIVE: "🔄",
            EventType.ROADMAP_STAGE: "📌",
            
            # Achievement events
            EventType.ACHIEVEMENT_UNLOCKED: "🎖️",
            EventType.MILESTONE_REACHED: "⭐",
            EventType.CHALLENGE_COMPLETED: "🏅",
            EventType.MAJOR_IMPROVEMENT: "🚀",
            EventType.PERSONAL_RECORD: "📊",
            
            # Decision events
            EventType.DECISION_MADE: "⚡",
            EventType.RECOMMENDATION_ACCEPTED: "💡",
            EventType.RECOMMENDATION_REJECTED: "🚫",
            EventType.RECOMMENDATION_IMPLEMENTED: "✅",
            
            # Progress events
            EventType.BENCHMARK_CHANGED: "📊",
            EventType.SNAPSHOT_TAKEN: "📸",
            EventType.PERIODIC_REPORT: "📄",
            EventType.TREND_CHANGED: "📈",
            
            # Other events
            EventType.EXPERIMENT_STARTED: "🧪",
            EventType.EXPERIMENT_COMPLETED: "🔬",
            EventType.OPTIMIZATION_APPLIED: "⚙️",
            EventType.RESOURCE_CHANGED: "🔄"
        }
    
    def _initialize_event_colors(self) -> Dict[EventType, str]:
        """Initialize colors for different event types."""
        return {
            EventType.GOAL_CREATED: "#4CAF50",
            EventType.GOAL_COMPLETED: "#00E676",
            EventType.GOAL_MODIFIED: "#FFA726",
            EventType.GOAL_POSTPONED: "#FFC107",
            EventType.GOAL_FAILED: "#F44336",
            EventType.GOAL_RECOVERED: "#FF7043",
            EventType.GOAL_PROGRESS: "#66BB6A",
            
            EventType.HABIT_ADOPTED: "#66BB6A",
            EventType.HABIT_IMPROVED: "#4CAF50",
            EventType.HABIT_REGRESSED: "#EF5350",
            EventType.HABIT_BROKEN: "#D32F2F",
            EventType.HABIT_RECOVERED: "#FF5722",
            EventType.HABIT_STREAK: "#FF6F00",
            
            EventType.ROADMAP_CREATED: "#2196F3",
            EventType.ROADMAP_MILESTONE: "#03A9F4",
            EventType.ROADMAP_COMPLETED: "#00BCD4",
            EventType.ROADMAP_ALTERNATIVE: "#4FC3F7",
            EventType.ROADMAP_STAGE: "#29B6F6",
            
            EventType.ACHIEVEMENT_UNLOCKED: "#FFD700",
            EventType.MILESTONE_REACHED: "#FFAB00",
            EventType.CHALLENGE_COMPLETED: "#FF6F00",
            EventType.MAJOR_IMPROVEMENT: "#00C853",
            EventType.PERSONAL_RECORD: "#FFA000",
            
            EventType.DECISION_MADE: "#1A237E",
            EventType.RECOMMENDATION_ACCEPTED: "#E91E63",
            EventType.RECOMMENDATION_REJECTED: "#7B1FA2",
            EventType.RECOMMENDATION_IMPLEMENTED: "#4CAF50",
            
            EventType.BENCHMARK_CHANGED: "#9C27B0",
            EventType.SNAPSHOT_TAKEN: "#607D8B",
            EventType.PERIODIC_REPORT: "#795548",
            EventType.TREND_CHANGED: "#0288D1",
            
            EventType.EXPERIMENT_STARTED: "#F57C00",
            EventType.EXPERIMENT_COMPLETED: "#388E3C",
            EventType.OPTIMIZATION_APPLIED: "#4527A0",
            EventType.RESOURCE_CHANGED: "#00897B"
        }
    
    def _initialize_event_weights(self) -> Dict[EventType, int]:
        """Initialize weights for event importance."""
        return {
            EventType.GOAL_CREATED: 2,
            EventType.GOAL_COMPLETED: 5,
            EventType.GOAL_MODIFIED: 2,
            EventType.GOAL_POSTPONED: 3,
            EventType.GOAL_FAILED: 4,
            EventType.GOAL_RECOVERED: 4,
            EventType.GOAL_PROGRESS: 2,
            
            EventType.HABIT_ADOPTED: 3,
            EventType.HABIT_IMPROVED: 3,
            EventType.HABIT_REGRESSED: 3,
            EventType.HABIT_BROKEN: 4,
            EventType.HABIT_RECOVERED: 4,
            EventType.HABIT_STREAK: 3,
            
            EventType.ROADMAP_CREATED: 3,
            EventType.ROADMAP_MILESTONE: 4,
            EventType.ROADMAP_COMPLETED: 5,
            EventType.ROADMAP_ALTERNATIVE: 3,
            EventType.ROADMAP_STAGE: 3,
            
            EventType.ACHIEVEMENT_UNLOCKED: 5,
            EventType.MILESTONE_REACHED: 5,
            EventType.CHALLENGE_COMPLETED: 4,
            EventType.MAJOR_IMPROVEMENT: 5,
            EventType.PERSONAL_RECORD: 4,
            
            EventType.DECISION_MADE: 3,
            EventType.RECOMMENDATION_ACCEPTED: 3,
            EventType.RECOMMENDATION_REJECTED: 2,
            EventType.RECOMMENDATION_IMPLEMENTED: 4,
            
            EventType.BENCHMARK_CHANGED: 3,
            EventType.SNAPSHOT_TAKEN: 2,
            EventType.PERIODIC_REPORT: 3,
            EventType.TREND_CHANGED: 3,
            
            EventType.EXPERIMENT_STARTED: 3,
            EventType.EXPERIMENT_COMPLETED: 4,
            EventType.OPTIMIZATION_APPLIED: 4,
            EventType.RESOURCE_CHANGED: 2
        }
    
    def generate_timeline(self, 
                         events: List[SustainabilityEvent],
                         period: TimelinePeriod = TimelinePeriod.ALL,
                         categories: List[EventCategory] = None) -> Dict[str, Any]:
        """
        Generate a timeline from events.
        
        Args:
            events: List of sustainability events
            period: Timeline period
            categories: Filter by categories
        
        Returns:
            Dict: Timeline data
        """
        if not events:
            return {'message': 'No events to display'}
        
        # Filter by categories
        filtered_events = events
        if categories:
            filtered_events = [e for e in events if e.category in categories]
        
        # Filter by period
        filtered_events = self._filter_by_period(filtered_events, period)
        
        # Sort by timestamp
        sorted_events = sorted(filtered_events, key=lambda e: e.timestamp)
        
        # Group by period
        grouped_events = self._group_by_period(sorted_events, period)
        
        # Build timeline
        timeline = {
            'events': sorted_events,
            'grouped_events': grouped_events,
            'total_events': len(sorted_events),
            'period': period.value,
            'date_range': self._get_date_range(sorted_events),
            'event_types': self._get_event_types(sorted_events),
            'category_breakdown': self._get_category_breakdown(sorted_events),
            'summary': self._generate_summary(sorted_events),
            'milestones': self._extract_milestones(sorted_events)
        }
        
        return timeline
    
    def _filter_by_period(self, 
                         events: List[SustainabilityEvent],
                         period: TimelinePeriod) -> List[SustainabilityEvent]:
        """
        Filter events by period.
        """
        if period == TimelinePeriod.ALL:
            return events
        
        now = datetime.now()
        cutoff = now
        
        if period == TimelinePeriod.DAILY:
            cutoff = now - timedelta(days=1)
        elif period == TimelinePeriod.WEEKLY:
            cutoff = now - timedelta(days=7)
        elif period == TimelinePeriod.MONTHLY:
            cutoff = now - timedelta(days=30)
        elif period == TimelinePeriod.QUARTERLY:
            cutoff = now - timedelta(days=90)
        elif period == TimelinePeriod.YEARLY:
            cutoff = now - timedelta(days=365)
        
        return [e for e in events if e.timestamp >= cutoff]
    
    def _group_by_period(self, 
                        events: List[SustainabilityEvent],
                        period: TimelinePeriod) -> Dict[str, List[SustainabilityEvent]]:
        """
        Group events by period.
        """
        grouped = defaultdict(list)
        
        for event in events:
            key = self._get_period_key(event.timestamp, period)
            grouped[key].append(event)
        
        return dict(sorted(grouped.items()))
    
    def _get_period_key(self, timestamp: datetime, period: TimelinePeriod) -> str:
        """
        Get period key for grouping.
        """
        if period == TimelinePeriod.DAILY:
            return timestamp.strftime('%Y-%m-%d')
        elif period == TimelinePeriod.WEEKLY:
            return f"{timestamp.year}-W{timestamp.isocalendar()[1]:02d}"
        elif period == TimelinePeriod.MONTHLY:
            return timestamp.strftime('%Y-%m')
        elif period == TimelinePeriod.QUARTERLY:
            quarter = (timestamp.month - 1) // 3 + 1
            return f"{timestamp.year}-Q{quarter}"
        elif period == TimelinePeriod.YEARLY:
            return str(timestamp.year)
        else:
            return timestamp.strftime('%Y-%m-%d')
    
    def _get_date_range(self, events: List[SustainabilityEvent]) -> Dict[str, Any]:
        """
        Get date range of events.
        """
        if not events:
            return {}
        
        dates = [e.timestamp for e in events]
        return {
            'start': min(dates).strftime('%Y-%m-%d'),
            'end': max(dates).strftime('%Y-%m-%d'),
            'days': (max(dates) - min(dates)).days
        }
    
    def _get_event_types(self, events: List[SustainabilityEvent]) -> Dict[str, int]:
        """
        Get count of each event type.
        """
        counts = defaultdict(int)
        for event in events:
            counts[event.event_type.value] += 1
        return dict(counts)
    
    def _get_category_breakdown(self, events: List[SustainabilityEvent]) -> Dict[str, int]:
        """
        Get breakdown by category.
        """
        breakdown = defaultdict(int)
        for event in events:
            breakdown[event.category.value] += 1
        return dict(breakdown)
    
    def _generate_summary(self, events: List[SustainabilityEvent]) -> Dict[str, Any]:
        """
        Generate summary of timeline.
        """
        if not events:
            return {}
        
        # Count by category
        categories = defaultdict(int)
        for event in events:
            if event.category:
                categories[event.category.value] += 1
        
        # Calculate average impact
        total_impact = sum(e.impact_score for e in events)
        avg_impact = total_impact / len(events) if events else 0
        
        # Calculate total importance
        total_importance = sum(e.importance for e in events)
        avg_importance = total_importance / len(events) if events else 0
        
        # Most important events
        important_events = sorted(events, key=lambda e: e.importance, reverse=True)[:5]
        
        return {
            'total_events': len(events),
            'categories': dict(categories),
            'average_impact_score': avg_impact,
            'average_importance': avg_importance,
            'highest_impact_event': max(events, key=lambda e: e.impact_score) if events else None,
            'most_important_events': important_events,
            'event_breakdown': self._get_event_types(events)
        }
    
    def _extract_milestones(self, events: List[SustainabilityEvent]) -> List[Dict[str, Any]]:
        """
        Extract milestone events from the timeline.
        """
        milestone_types = [
            EventType.GOAL_COMPLETED,
            EventType.ACHIEVEMENT_UNLOCKED,
            EventType.MILESTONE_REACHED,
            EventType.ROADMAP_COMPLETED,
            EventType.CHALLENGE_COMPLETED,
            EventType.MAJOR_IMPROVEMENT,
            EventType.PERSONAL_RECORD
        ]
        
        milestones = [e for e in events if e.event_type in milestone_types]
        sorted_milestones = sorted(milestones, key=lambda e: e.timestamp)
        
        return [
            {
                'date': e.timestamp.strftime('%Y-%m-%d'),
                'title': e.title,
                'description': e.description,
                'icon': self.event_icons.get(e.event_type, '⭐'),
                'impact_score': e.impact_score,
                'category': e.category.value,
                'importance': e.importance
            }
            for e in sorted_milestones
        ]
    
    def get_timeline_data_for_chart(self, 
                                   events: List[SustainabilityEvent]) -> Dict[str, Any]:
        """
        Get timeline data formatted for charting.
        
        Args:
            events: List of events
        
        Returns:
            Dict: Chart data
        """
        if not events:
            return {'message': 'No events to chart'}
        
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        return {
            'dates': [e.timestamp.strftime('%Y-%m-%d') for e in sorted_events],
            'titles': [e.title for e in sorted_events],
            'types': [e.event_type.value for e in sorted_events],
            'categories': [e.category.value for e in sorted_events],
            'impact_scores': [e.impact_score for e in sorted_events],
            'importance': [e.importance for e in sorted_events],
            'icons': [self.event_icons.get(e.event_type, '📌') for e in sorted_events],
            'colors': [self.event_colors.get(e.event_type, '#757575') for e in sorted_events]
        }
    
    def generate_milestone_timeline(self, 
                                   events: List[SustainabilityEvent]) -> List[Dict[str, Any]]:
        """
        Generate a timeline focused on major milestones.
        
        Args:
            events: List of events
        
        Returns:
            List[Dict]: Milestone timeline
        """
        milestones = self._extract_milestones(events)
        
        # Add milestone markers
        enhanced_milestones = []
        for i, milestone in enumerate(milestones):
            if i > 0:
                days_between = (datetime.fromisoformat(milestone['date']) - 
                               datetime.fromisoformat(milestones[i-1]['date'])).days
            else:
                days_between = 0
            
            enhanced_milestones.append({
                **milestone,
                'order': i + 1,
                'days_since_last': days_between,
                'is_major': milestone['importance'] >= 4
            })
        
        return enhanced_milestones
    
    def get_event_weight(self, event_type: EventType) -> int:
        """
        Get weight for an event type.
        
        Args:
            event_type: Event type
        
        Returns:
            int: Weight
        """
        return self.event_weights.get(event_type, 1)
    
    def get_event_color(self, event_type: EventType) -> str:
        """
        Get color for an event type.
        
        Args:
            event_type: Event type
        
        Returns:
            str: Color code
        """
        return self.event_colors.get(event_type, '#757575')
    
    def get_event_icon(self, event_type: EventType) -> str:
        """
        Get icon for an event type.
        
        Args:
            event_type: Event type
        
        Returns:
            str: Icon
        """
        return self.event_icons.get(event_type, '📌')