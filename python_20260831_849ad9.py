"""
Sustainability Gamification & Challenge Platform - Analytics
Provides analytics for gamification data.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from collections import defaultdict

from gamification.models import (
    Challenge, ChallengeProgress, UserXP, Achievement,
    Streak, GamificationEvent, ChallengeStatus
)

logger = logging.getLogger(__name__)


class GamificationAnalytics:
    """
    Provides analytics for gamification data.
    """
    
    def __init__(self):
        """Initialize the analytics engine."""
        logger.info("Gamification Analytics initialized")
    
    def analyze_user_performance(self,
                                 challenges: List[Challenge],
                                 progress: List[ChallengeProgress],
                                 user_xp: UserXP,
                                 achievements: List[Achievement],
                                 streak: Optional[Streak] = None) -> Dict[str, Any]:
        """
        Analyze user gamification performance.
        
        Args:
            challenges: List of challenges
            progress: List of challenge progress
            user_xp: User XP object
            achievements: List of achievements
            streak: User streak object
        
        Returns:
            Dict: Performance analysis
        """
        completed = [c for c in challenges if c.status == ChallengeStatus.COMPLETED]
        active = [c for c in challenges if c.status in [ChallengeStatus.ACTIVE, ChallengeStatus.IN_PROGRESS]]
        failed = [c for c in challenges if c.status == ChallengeStatus.FAILED]
        
        total_challenges = len(challenges)
        completed_count = len(completed)
        active_count = len(active)
        
        completion_rate = (completed_count / total_challenges * 100) if total_challenges > 0 else 0
        
        # Calculate average progress
        avg_progress = 0.0
        if progress:
            avg_progress = statistics.mean([p.progress_percentage for p in progress])
        
        # Calculate points and XP
        total_points = sum(p.points_earned for p in progress)
        total_xp = user_xp.total_xp_earned if user_xp else 0
        
        # Calculate streaks
        streak_days = streak.current_streak if streak else 0
        longest_streak = streak.longest_streak if streak else 0
        
        # Category performance
        category_performance = self._analyze_category_performance(challenges, progress)
        
        # Difficulty breakdown
        difficulty_breakdown = self._analyze_difficulty_breakdown(challenges, progress)
        
        return {
            'total_challenges': total_challenges,
            'completed_challenges': completed_count,
            'active_challenges': active_count,
            'failed_challenges': len(failed),
            'completion_rate': completion_rate,
            'average_progress': avg_progress,
            'total_points': total_points,
            'total_xp': total_xp,
            'current_level': user_xp.current_level if user_xp else 0,
            'current_streak': streak_days,
            'longest_streak': longest_streak,
            'achievements_unlocked': len(achievements),
            'category_performance': category_performance,
            'difficulty_breakdown': difficulty_breakdown
        }
    
    def _analyze_category_performance(self,
                                     challenges: List[Challenge],
                                     progress: List[ChallengeProgress]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance by category.
        """
        category_data = defaultdict(lambda: {'total': 0, 'completed': 0, 'progress': []})
        
        for challenge in challenges:
            category_data[challenge.category.value]['total'] += 1
            if challenge.status == ChallengeStatus.COMPLETED:
                category_data[challenge.category.value]['completed'] += 1
        
        # Add progress data
        for p in progress:
            # Find the challenge
            challenge = next((c for c in challenges if c.id == p.challenge_id), None)
            if challenge:
                category_data[challenge.category.value]['progress'].append(p.progress_percentage)
        
        # Calculate metrics
        result = {}
        for category, data in category_data.items():
            total = data['total']
            completed = data['completed']
            avg_progress = statistics.mean(data['progress']) if data['progress'] else 0
            
            result[category] = {
                'total': total,
                'completed': completed,
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'average_progress': avg_progress,
                'best_category': completed == max([d['completed'] for d in category_data.values()]) if category_data else False
            }
        
        return result
    
    def _analyze_difficulty_breakdown(self,
                                     challenges: List[Challenge],
                                     progress: List[ChallengeProgress]) -> Dict[str, Dict[str, Any]]:
        """
        Analyze performance by difficulty.
        """
        difficulty_data = defaultdict(lambda: {'total': 0, 'completed': 0, 'progress': []})
        
        for challenge in challenges:
            difficulty_data[challenge.difficulty.value]['total'] += 1
            if challenge.status == ChallengeStatus.COMPLETED:
                difficulty_data[challenge.difficulty.value]['completed'] += 1
        
        for p in progress:
            challenge = next((c for c in challenges if c.id == p.challenge_id), None)
            if challenge:
                difficulty_data[challenge.difficulty.value]['progress'].append(p.progress_percentage)
        
        result = {}
        for difficulty, data in difficulty_data.items():
            total = data['total']
            completed = data['completed']
            avg_progress = statistics.mean(data['progress']) if data['progress'] else 0
            
            result[difficulty] = {
                'total': total,
                'completed': completed,
                'completion_rate': (completed / total * 100) if total > 0 else 0,
                'average_progress': avg_progress
            }
        
        return result
    
    def get_progress_trend(self,
                          progress: List[ChallengeProgress],
                          days: int = 30) -> Dict[str, Any]:
        """
        Get progress trend over time.
        
        Args:
            progress: List of challenge progress
            days: Number of days to include
        
        Returns:
            Dict: Progress trend
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Filter progress entries by date
        daily_progress = defaultdict(float)
        
        for p in progress:
            for entry in p.progress_history:
                try:
                    date = datetime.fromisoformat(entry['date'])
                    if date >= cutoff:
                        date_key = date.strftime('%Y-%m-%d')
                        if entry['percentage'] > daily_progress[date_key]:
                            daily_progress[date_key] = entry['percentage']
                except:
                    pass
        
        sorted_dates = sorted(daily_progress.keys())
        
        return {
            'dates': sorted_dates,
            'values': [daily_progress[d] for d in sorted_dates],
            'trend': self._calculate_trend([daily_progress[d] for d in sorted_dates]) if sorted_dates else 0
        }
    
    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend from values.
        """
        if len(values) < 2:
            return 0
        
        n = len(values)
        x = list(range(n))
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(values)
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
    
    def get_engagement_metrics(self,
                              events: List[GamificationEvent],
                              days: int = 30) -> Dict[str, Any]:
        """
        Get engagement metrics.
        
        Args:
            events: List of gamification events
            days: Number of days to include
        
        Returns:
            Dict: Engagement metrics
        """
        cutoff = datetime.now() - timedelta(days=days)
        filtered_events = [e for e in events if e.created_at >= cutoff]
        
        # Group by day
        daily_events = defaultdict(int)
        for event in filtered_events:
            date_key = event.created_at.strftime('%Y-%m-%d')
            daily_events[date_key] += 1
        
        # Group by type
        type_counts = defaultdict(int)
        for event in filtered_events:
            type_counts[event.event_type] += 1
        
        return {
            'total_events': len(filtered_events),
            'active_days': len(daily_events),
            'daily_average': len(filtered_events) / max(1, len(daily_events)),
            'event_type_breakdown': dict(type_counts),
            'longest_active_streak': self._calculate_active_streak(daily_events)
        }
    
    def _calculate_active_streak(self, daily_events: Dict[str, int]) -> int:
        """
        Calculate active streak from daily events.
        """
        sorted_dates = sorted(daily_events.keys())
        if not sorted_dates:
            return 0
        
        current_streak = 0
        for i, date in enumerate(reversed(sorted_dates)):
            if i == 0:
                current_streak = 1
            else:
                # Check if dates are consecutive
                prev_date = datetime.strptime(sorted_dates[-i], '%Y-%m-%d')
                curr_date = datetime.strptime(sorted_dates[-i-1], '%Y-%m-%d')
                if (curr_date - prev_date).days == -1:
                    current_streak += 1
                else:
                    break
        
        return current_streak
    
    def get_impact_metrics(self,
                          challenges: List[Challenge]) -> Dict[str, float]:
        """
        Get environmental impact metrics from challenges.
        
        Args:
            challenges: List of challenges
        
        Returns:
            Dict: Impact metrics
        """
        completed = [c for c in challenges if c.status == ChallengeStatus.COMPLETED]
        
        total_carbon = sum(c.estimated_carbon_savings for c in completed)
        total_water = sum(c.estimated_water_savings for c in completed)
        total_waste = sum(c.estimated_waste_reduction for c in completed)
        
        return {
            'total_carbon_saved_kg': total_carbon,
            'total_water_saved_liters': total_water,
            'total_waste_reduced_kg': total_waste,
            'average_carbon_per_challenge': total_carbon / len(completed) if completed else 0,
            'best_category': self._get_best_impact_category(completed)
        }
    
    def _get_best_impact_category(self, completed_challenges: List[Challenge]) -> str:
        """
        Get category with highest impact.
        """
        if not completed_challenges:
            return "None"
        
        category_impacts = defaultdict(float)
        for challenge in completed_challenges:
            impact = challenge.estimated_carbon_savings + challenge.estimated_water_savings + challenge.estimated_waste_reduction
            category_impacts[challenge.category.value] += impact
        
        if category_impacts:
            return max(category_impacts, key=category_impacts.get)
        
        return "None"