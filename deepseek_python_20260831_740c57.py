"""
Sustainability Lifecycle & Long-Term Progress Management - Timeline Generator
Generates interactive timelines of sustainability events.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from lifecycle.models import (
    SustainabilityEvent, EventType, TimelinePeriod, ProgressSnapshot
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
        logger.info("Timeline Generator initialized")
    
    def _initialize_event_icons(self) -> Dict[EventType, str]:
        """Initialize icons for different event types."""
        return {
            EventType.GOAL_CREATED: "🎯",
            EventType.GOAL_COMPLETED: "🏆",
            EventType.GOAL_MODIFIED: "📝",
            EventType.GOAL_POSTPONED: "⏸️",
            EventType.GOAL_FAILED: "❌",
            EventType.GOAL_RECOVERED: "🔄",
            EventType.HABIT_ADOPTED: "🌟",
            EventType.HABIT_IMPROVED: "📈",
            EventType.HABIT_REGRESSED: "📉",
            EventType.HABIT_BROKEN: "💔",
            EventType.HABIT_RECOVERED: "❤️‍🩹",
            EventType.ROADMAP_CREATED: "🗺️",
            EventType.ROADMAP_MILESTONE: "📍",
            EventType.ROADMAP_COMPLETED: "✅",
            EventType.ROADMAP_ALTERNATIVE: "🔄",
            EventType.BENCHMARK_CHANGED: "📊",
            EventType.RECOMMENDATION_ACCEPTED: "💡",
            EventType.RECOMMENDATION_REJECTED: "🚫",
            EventType.ACHIEVEMENT_UNLOCKED: "🎖️",
            EventType.CHALLENGE_COMPLETED: "🏅",
            EventType.MAJOR_IMPROVEMENT: "🚀",
            EventType.DECISION_MADE: "⚡",
            EventType.SNAPSHOT_TAKEN: "📸",
            EventType.MILESTONE_REACHED: "⭐",
            EventType.PERIODIC_REPORT: "📄"
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
            EventType.HABIT_ADOPTED: "#66BB6A",
            EventType.HABIT_IMPROVED: "#4CAF50",
            EventType.HABIT_REGRESSED: "#EF5350",
            EventType.HABIT_BROKEN: "#D32F2F",
            EventType.HABIT_RECOVERED: "#FF5722",
            EventType.ROADMAP_CREATED: "#2196F3",
            EventType.ROADMAP_MILESTONE: "#03A9F4",
            EventType.ROADMAP_COMPLETED: "#00BCD4",
            EventType.ROADMAP_ALTERNATIVE: "#4FC3F7",
            EventType.BENCHMARK_CHANGED: "#9C27B0",
            EventType.RECOMMENDATION_ACCEPTED: "#E91E63",
            EventType.RECOMMENDATION_REJECTED: "#7B1FA2",
            EventType.ACHIEVEMENT_UNLOCKED: "#FFD700",
            EventType.CHALLENGE_COMPLETED: "#FF6F00",
            EventType.MAJOR_IMPROVEMENT: "#00C853",
            EventType.DECISION_MADE: "#1A237E",
            EventType.SNAPSHOT_TAKEN: "#607D8B",
            EventType.MILESTONE_REACHED: "#FFAB00",
            EventType.PERIODIC_REPORT: "#795548"
        }
    
    def generate_timeline(self, 
                         events: List[SustainabilityEvent],
                         period: TimelinePeriod = TimelinePeriod.ALL) -> Dict[str, Any]:
        """
        Generate a timeline from events.
        
        Args:
            events: List of sustainability events
            period: Timeline period
        
        Returns:
            Dict: Timeline data
        """
        if not events:
            return {'message': 'No events to display'}
        
        # Filter by period
        filtered_events = self._filter_by_period(events, period)
        
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
            'summary': self._generate_summary(sorted_events)
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
                categories[event.category] += 1
        
        # Average impact
        total_impact = sum(e.impact_score for e in events)
        avg_impact = total_impact / len(events) if events else 0
        
        # Most important events
        important_events = sorted(events, key=lambda e: e.importance, reverse=True)[:5]
        
        return {
            'total_events': len(events),
            'categories': dict(categories),
            'average_impact_score': avg_impact,
            'highest_impact_event': max(events, key=lambda e: e.impact_score) if events else None,
            'most_important_events': important_events,
            'event_breakdown': self._get_event_types(events)
        }
    
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
            'impact_scores': [e.impact_score for e in sorted_events],
            'importance': [e.importance for e in sorted_events],
            'categories': [e.category for e in sorted_events],
            'icons': [self.event_icons.get(e.event_type, '📌') for e in sorted_events],
            'colors': [self.event_colors.get(e.event_type, '#757575') for e in sorted_events]
        }
    
    def get_milestone_timeline(self, 
                              events: List[SustainabilityEvent]) -> List[Dict[str, Any]]:
        """
        Get milestone events for the timeline.
        
        Args:
            events: List of events
        
        Returns:
            List[Dict]: Milestone events
        """
        milestone_types = [
            EventType.GOAL_COMPLETED,
            EventType.ACHIEVEMENT_UNLOCKED,
            EventType.MILESTONE_REACHED,
            EventType.ROADMAP_COMPLETED,
            EventType.CHALLENGE_COMPLETED,
            EventType.MAJOR_IMPROVEMENT
        ]
        
        milestones = [e for e in events if e.event_type in milestone_types]
        sorted_milestones = sorted(milestones, key=lambda e: e.timestamp)
        
        return [
            {
                'date': e.timestamp.strftime('%Y-%m-%d'),
                'title': e.title,
                'description': e.description,
                'icon': self.event_icons.get(e.event_type, '⭐'),
                'impact_score': e.impact_score
            }
            for e in sorted_milestones
        ]