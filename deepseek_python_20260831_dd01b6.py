"""
Sustainability Lifecycle & Long-Term Progress Management - Report Generator
Generates periodic sustainability reports.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from lifecycle.models import (
    SustainabilityReport, ProgressSnapshot, SustainabilityEvent,
    GoalLifecycle, HabitLifecycle, AchievementHistory
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """
    Generates periodic sustainability reports.
    """
    
    def __init__(self):
        """Initialize the report generator."""
        self.report_templates = self._initialize_report_templates()
        logger.info("Report Generator initialized")
    
    def _initialize_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize report templates.
        """
        return {
            'monthly': {
                'name': 'Monthly Sustainability Report',
                'description': 'Monthly summary of sustainability progress',
                'period': 'monthly',
                'sections': ['summary', 'metrics', 'goals', 'habits', 'achievements', 'recommendations']
            },
            'quarterly': {
                'name': 'Quarterly Sustainability Report',
                'description': 'Quarterly review of sustainability progress',
                'period': 'quarterly',
                'sections': ['summary', 'metrics', 'goals', 'habits', 'achievements', 'trends', 'projections', 'recommendations']
            },
            'yearly': {
                'name': 'Annual Sustainability Report',
                'description': 'Annual review of sustainability progress',
                'period': 'yearly',
                'sections': ['summary', 'metrics', 'goals', 'habits', 'achievements', 'trends', 'projections', 'impact', 'recommendations']
            },
            'personal': {
                'name': 'Personal Sustainability Summary',
                'description': 'Personal summary of sustainability journey',
                'period': 'custom',
                'sections': ['summary', 'metrics', 'goals', 'habits', 'achievements', 'recommendations']
            },
            'household': {
                'name': 'Household Sustainability Report',
                'description': 'Household sustainability summary',
                'period': 'custom',
                'sections': ['summary', 'metrics', 'member_contributions', 'goals', 'habits', 'recommendations']
            }
        }
    
    def generate_report(self,
                       user_id: str,
                       report_type: str,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       snapshots: List[ProgressSnapshot] = None,
                       events: List[SustainabilityEvent] = None,
                       goals: List[GoalLifecycle] = None,
                       habits: List[HabitLifecycle] = None,
                       achievements: List[AchievementHistory] = None,
                       household_id: Optional[str] = None) -> SustainabilityReport:
        """
        Generate a sustainability report.
        
        Args:
            user_id: User ID
            report_type: Report type
            start_date: Start date
            end_date: End date
            snapshots: Progress snapshots
            events: Sustainability events
            goals: Goals
            habits: Habits
            achievements: Achievements
            household_id: Optional household ID
        
        Returns:
            SustainabilityReport: Generated report
        """
        template = self.report_templates.get(report_type, {})
        period = self._get_period_string(report_type, start_date, end_date)
        
        report = SustainabilityReport(
            user_id=user_id,
            household_id=household_id,
            report_type=report_type,
            period=period,
            generated_at=datetime.now()
        )
        
        # Filter data for the period
        filtered_snapshots = self._filter_by_date(snapshots, start_date, end_date)
        filtered_events = self._filter_by_date(events, start_date, end_date)
        
        # Populate report sections
        report.summary = self._generate_summary(filtered_snapshots, filtered_events)
        report.key_achievements = self._generate_key_achievements(filtered_events, achievements)
        report.areas_for_improvement = self._generate_areas_for_improvement(filtered_snapshots)
        
        # Metrics
        if filtered_snapshots:
            last = filtered_snapshots[-1]
            first = filtered_snapshots[0] if len(filtered_snapshots) > 1 else last
            
            report.current_sustainability_score = last.sustainability_score
            report.previous_sustainability_score = first.sustainability_score
            report.score_change = report.current_sustainability_score - report.previous_sustainability_score
            report.score_change_percentage = (report.score_change / (report.previous_sustainability_score + 0.001)) * 100
            
            # Impact metrics
            if len(filtered_snapshots) >= 2:
                report.carbon_saved_kg = max(0, first.carbon_footprint - last.carbon_footprint)
                report.water_saved_liters = max(0, first.water_usage - last.water_usage)
                report.waste_reduced_kg = max(0, first.waste_generation - last.waste_generation)
                report.energy_saved_kwh = max(0, first.energy_usage - last.energy_usage)
        
        # Goals
        if goals:
            completed_goals = [g for g in goals if g.status.value == 'completed']
            in_progress_goals = [g for g in goals if g.status.value in ['active', 'in_progress']]
            failed_goals = [g for g in goals if g.status.value == 'failed']
            
            report.goals_completed = len(completed_goals)
            report.goals_in_progress = len(in_progress_goals)
            report.goals_failed = len(failed_goals)
            report.goal_completion_rate = (len(completed_goals) / len(goals) * 100) if goals else 0
        
        # Habits
        if habits:
            active_habits = [h for h in habits if h.status.value in ['active', 'improving']]
            completed_habits = [h for h in habits if h.status.value == 'completed']
            regressed_habits = [h for h in habits if h.status.value in ['regressed', 'declining']]
            
            report.habits_adopted = len(habits)
            report.habits_maintained = len(active_habits)
            report.habits_regressed = len(regressed_habits)
            report.habit_consistency_avg = sum(h.consistency_score for h in habits) / len(habits) if habits else 0
        
        # Achievements
        if achievements:
            recent_achievements = [a for a in achievements if a.unlocked_at >= (start_date or datetime.now() - timedelta(days=30))]
            report.achievements_unlocked = len(recent_achievements)
        
        # Generate content
        report.content = self._generate_report_content(report, template)
        
        # Generate chart data
        report.chart_data = self._generate_chart_data(filtered_snapshots, report_type)
        
        logger.info(f"Report generated for user {user_id}: {report_type}")
        return report
    
    def _get_period_string(self, report_type: str, start_date: Optional[datetime], end_date: Optional[datetime]) -> str:
        """
        Get period string for the report.
        """
        if report_type == 'monthly':
            return datetime.now().strftime('%B %Y')
        elif report_type == 'quarterly':
            quarter = (datetime.now().month - 1) // 3 + 1
            return f"Q{quarter} {datetime.now().year}"
        elif report_type == 'yearly':
            return str(datetime.now().year)
        elif start_date and end_date:
            return f"{start_date.strftime('%b %d, %Y')} - {end_date.strftime('%b %d, %Y')}"
        return "Custom Period"
    
    def _filter_by_date(self, items: List, start_date: Optional[datetime], end_date: Optional[datetime]) -> List:
        """
        Filter items by date range.
        """
        if not items:
            return []
        
        filtered = []
        for item in items:
            # Try to get date from item
            if hasattr(item, 'timestamp'):
                date = item.timestamp
            elif hasattr(item, 'created_at'):
                date = item.created_at
            elif hasattr(item, 'snapshot_date'):
                date = item.snapshot_date
            else:
                continue
            
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                continue
            filtered.append(item)
        
        return filtered
    
    def _generate_summary(self, snapshots: List[ProgressSnapshot], events: List[SustainabilityEvent]) -> str:
        """
        Generate report summary.
        """
        if not snapshots:
            return "No data available for this period."
        
        last = snapshots[-1]
        first = snapshots[0] if len(snapshots) > 1 else last
        
        change = last.sustainability_score - first.sustainability_score
        if change > 5:
            trend = "improved significantly"
        elif change > 0:
            trend = "improved slightly"
        elif change < -5:
            trend = "declined significantly"
        elif change < 0:
            trend = "declined slightly"
        else:
            trend = "remained stable"
        
        summary = f"Your sustainability score {trend} from {first.sustainability_score:.1f}% to {last.sustainability_score:.1f}%."
        
        if events:
            summary += f" During this period, you recorded {len(events)} sustainability events."
        
        return summary
    
    def _generate_key_achievements(self, events: List[SustainabilityEvent], achievements: List[AchievementHistory]) -> List[str]:
        """
        Generate key achievements list.
        """
        achievements_list = []
        
        # From achievements
        if achievements:
            for ach in achievements[:5]:
                achievements_list.append(f"🏆 {ach.title}: {ach.description}")
        
        # From events
        if events:
            completed_events = [e for e in events if e.event_type in [EventType.GOAL_COMPLETED, EventType.ACHIEVEMENT_UNLOCKED]]
            for event in completed_events[:3]:
                achievements_list.append(f"✅ {event.title}")
        
        return achievements_list[:5]
    
    def _generate_areas_for_improvement(self, snapshots: List[ProgressSnapshot]) -> List[str]:
        """
        Generate areas for improvement.
        """
        if not snapshots or len(snapshots) < 2:
            return ["Continue tracking your sustainability to identify improvement areas."]
        
        areas = []
        first = snapshots[0]
        last = snapshots[-1]
        
        # Check each category
        categories = [
            ('carbon_footprint', 'Carbon Footprint'),
            ('energy_usage', 'Energy Usage'),
            ('water_usage', 'Water Usage'),
            ('waste_generation', 'Waste Generation'),
            ('transportation_impact', 'Transportation Impact'),
            ('food_impact', 'Food Impact'),
            ('shopping_impact', 'Shopping Impact')
        ]
        
        for key, label in categories:
            v1 = getattr(first, key, 0.0)
            v2 = getattr(last, key, 0.0)
            
            if v1 > 0 and v2 > v1 * 1.1:
                areas.append(f"🔴 {label} increased by {((v2 - v1) / v1) * 100:.1f}%")
            elif v1 > 0 and v2 < v1 * 0.9:
                areas.append(f"🟢 {label} decreased by {((v1 - v2) / v1) * 100:.1f}%")
        
        if not areas:
            areas.append("All categories are stable. Continue maintaining your good habits.")
        
        return areas[:5]
    
    def _generate_report_content(self, report: SustainabilityReport, template: Dict[str, Any]) -> str:
        """
        Generate report content.
        """
        sections = template.get('sections', ['summary'])
        content = []
        
        # Header
        content.append(f"# {template.get('name', 'Sustainability Report')}")
        content.append(f"**Period:** {report.period}")
        content.append(f"**Generated:** {report.generated_at.strftime('%B %d, %Y')}")
        content.append("")
        
        # Summary
        if 'summary' in sections:
            content.append("## Executive Summary")
            content.append(report.summary)
            content.append("")
        
        # Metrics
        if 'metrics' in sections:
            content.append("## Key Metrics")
            content.append(f"- **Sustainability Score:** {report.current_sustainability_score:.1f}% (Change: {report.score_change:+.1f}%)")
            content.append(f"- **Carbon Saved:** {report.carbon_saved_kg:.1f} kg CO2e")
            content.append(f"- **Water Saved:** {report.water_saved_liters:.1f} liters")
            content.append(f"- **Waste Reduced:** {report.waste_reduced_kg:.1f} kg")
            content.append(f"- **Energy Saved:** {report.energy_saved_kwh:.1f} kWh")
            content.append("")
        
        # Goals
        if 'goals' in sections:
            content.append("## Goals")
            content.append(f"- **Completed:** {report.goals_completed}")
            content.append(f"- **In Progress:** {report.goals_in_progress}")
            content.append(f"- **Failed:** {report.goals_failed}")
            content.append(f"- **Completion Rate:** {report.goal_completion_rate:.1f}%")
            content.append("")
        
        # Habits
        if 'habits' in sections:
            content.append("## Habits")
            content.append(f"- **Adopted:** {report.habits_adopted}")
            content.append(f"- **Maintained:** {report.habits_maintained}")
            content.append(f"- **Regressed:** {report.habits_regressed}")
            content.append(f"- **Avg Consistency:** {report.habit_consistency_avg:.1f}%")
            content.append("")
        
        # Achievements
        if 'achievements' in sections:
            content.append("## Achievements")
            content.append(f"- **Unlocked:** {report.achievements_unlocked}")
            if report.key_achievements:
                for achievement in report.key_achievements:
                    content.append(f"  - {achievement}")
            content.append("")
        
        # Recommendations
        if 'recommendations' in sections:
            content.append("## Recommendations")
            if report.areas_for_improvement:
                for area in report.areas_for_improvement:
                    content.append(f"  - {area}")
            else:
                content.append("  - Continue your current practices. You're doing great!")
            content.append("")
        
        return '\n'.join(content)
    
    def _generate_chart_data(self, snapshots: List[ProgressSnapshot], report_type: str) -> Dict[str, Any]:
        """
        Generate chart data for the report.
        """
        if not snapshots:
            return {}
        
        sorted_snapshots = sorted(snapshots, key=lambda s: s.snapshot_date)
        
        return {
            'dates': [s.snapshot_date.strftime('%Y-%m-%d') for s in sorted_snapshots],
            'sustainability_scores': [s.sustainability_score for s in sorted_snapshots],
            'carbon_footprints': [s.carbon_footprint for s in sorted_snapshots],
            'energy_usage': [s.energy_usage for s in sorted_snapshots],
            'water_usage': [s.water_usage for s in sorted_snapshots],
            'waste_generation': [s.waste_generation for s in sorted_snapshots]
        }