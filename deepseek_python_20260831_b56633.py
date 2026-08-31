"""
Sustainability Gamification & Challenge Platform - Visualizations
Provides chart and visualization functions for gamification data.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from gamification.models import (
    Challenge, ChallengeProgress, UserXP, Achievement,
    Streak, Leaderboard, GamificationEvent
)

logger = logging.getLogger(__name__)


class GamificationVisualizer:
    """
    Creates visualizations for gamification data.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        logger.info("Gamification Visualizer initialized")
    
    def create_challenge_progress_chart(self,
                                       progress: ChallengeProgress) -> go.Figure:
        """
        Create challenge progress chart.
        
        Args:
            progress: Challenge progress
        
        Returns:
            go.Figure: Progress chart
        """
        history = progress.progress_history
        
        if not history:
            fig = go.Figure()
            fig.add_annotation(text="No progress data available")
            return fig
        
        dates = [h.get('date', '') for h in history]
        values = [h.get('percentage', 0) for h in history]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            name='Progress',
            line=dict(color='green', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_hline(y=100, line_dash="dash", line_color="red", 
                     annotation_text="Target")
        
        fig.update_layout(
            title=f"Progress: {progress.challenge_title}",
            xaxis_title="Date",
            yaxis_title="Progress (%)",
            yaxis_range=[0, 110],
            height=400,
            hovermode='x'
        )
        
        return fig
    
    def create_challenge_dashboard(self,
                                  challenges: List[Challenge],
                                  progress: List[ChallengeProgress]) -> go.Figure:
        """
        Create challenge dashboard.
        
        Args:
            challenges: List of challenges
            progress: List of progress
        
        Returns:
            go.Figure: Dashboard
        """
        completed = [c for c in challenges if c.status.value == 'completed']
        active = [c for c in challenges if c.status.value in ['active', 'in_progress']]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Challenge Status Distribution',
                'Progress by Category',
                'Completion Rate',
                'Weekly Challenge Activity'
            )
        )
        
        # Challenge status distribution
        status_counts = {
            'Completed': len(completed),
            'Active': len(active),
            'Failed': len([c for c in challenges if c.status.value == 'failed']),
            'Expired': len([c for c in challenges if c.status.value == 'expired'])
        }
        
        fig.add_trace(
            go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.3
            ),
            row=1, col=1
        )
        
        # Progress by category
        categories = {}
        for p in progress:
            challenge = next((c for c in challenges if c.id == p.challenge_id), None)
            if challenge:
                cat = challenge.category.value
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(p.progress_percentage)
        
        category_avg = {cat: sum(vals)/len(vals) for cat, vals in categories.items() if vals}
        
        if category_avg:
            fig.add_trace(
                go.Bar(
                    x=list(category_avg.keys()),
                    y=list(category_avg.values()),
                    name='Average Progress',
                    marker_color='green'
                ),
                row=1, col=2
            )
        
        # Completion rate
        total = len(challenges)
        if total > 0:
            completion_rate = len(completed) / total * 100
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number",
                    value=completion_rate,
                    title={'text': "Completion Rate (%)"},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "green"},
                        'steps': [
                            {'range': [0, 30], 'color': "red"},
                            {'range': [30, 60], 'color': "yellow"},
                            {'range': [60, 80], 'color': "lightgreen"},
                            {'range': [80, 100], 'color': "green"}
                        ]
                    }
                ),
                row=2, col=1
            )
        
        # Weekly activity (simplified)
        fig.add_trace(
            go.Bar(
                x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                y=[0, 0, 0, 0, 0, 0, 0],
                name='Weekly Activity'
            ),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=True)
        
        return fig
    
    def create_xp_progression_chart(self, user_xp: UserXP) -> go.Figure:
        """
        Create XP progression chart.
        
        Args:
            user_xp: User XP object
        
        Returns:
            go.Figure: XP progression chart
        """
        history = user_xp.xp_history
        
        if not history:
            fig = go.Figure()
            fig.add_annotation(text="No XP history available")
            return fig
        
        dates = [h['date'] for h in history]
        cumulative_xp = []
        total = 0
        for h in history:
            total += h['amount']
            cumulative_xp.append(total)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative_xp,
            mode='lines+markers',
            name='Cumulative XP',
            line=dict(color='purple', width=3),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=[user_xp.xp_to_next_level] * len(dates),
            mode='lines',
            name='XP to Next Level',
            line=dict(color='red', dash='dash')
        ))
        
        fig.update_layout(
            title="XP Progression",
            xaxis_title="Date",
            yaxis_title="XP",
            height=400,
            hovermode='x'
        )
        
        return fig
    
    def create_achievement_unlock_chart(self,
                                       achievements: List[Achievement]) -> go.Figure:
        """
        Create achievement unlock chart.
        
        Args:
            achievements: List of achievements
        
        Returns:
            go.Figure: Achievement chart
        """
        if not achievements:
            fig = go.Figure()
            fig.add_annotation(text="No achievements unlocked")
            return fig
        
        # Group by category
        categories = {}
        for ach in achievements:
            cat = ach.category or 'General'
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=list(categories.keys()),
            y=list(categories.values()),
            marker_color='gold',
            text=list(categories.values()),
            textposition='auto'
        ))
        
        fig.update_layout(
            title="Achievements by Category",
            xaxis_title="Category",
            yaxis_title="Count",
            height=400
        )
        
        return fig
    
    def create_streak_chart(self, streak: Streak) -> go.Figure:
        """
        Create streak chart.
        
        Args:
            streak: Streak object
        
        Returns:
            go.Figure: Streak chart
        """
        history = streak.streak_history[-30:]  # Last 30 days
        
        if not history:
            fig = go.Figure()
            fig.add_annotation(text="No streak history available")
            return fig
        
        dates = [h['date'] for h in history]
        streaks = [h['streak'] for h in history]
        completed = [h['completed'] for h in history]
        
        fig = make_subplots(rows=2, cols=1)
        
        # Streak chart
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=streaks,
                mode='lines+markers',
                name='Streak',
                line=dict(color='orange', width=3)
            ),
            row=1, col=1
        )
        
        # Completion chart
        fig.add_trace(
            go.Bar(
                x=dates,
                y=completed,
                name='Completed',
                marker_color='green'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=500,
            showlegend=True,
            title="Streak History"
        )
        
        fig.update_yaxes(title_text="Streak Days", row=1, col=1)
        fig.update_yaxes(title_text="Completed", row=2, col=1)
        
        return fig
    
    def create_leaderboard_chart(self, leaderboard: Leaderboard) -> go.Figure:
        """
        Create leaderboard chart.
        
        Args:
            leaderboard: Leaderboard object
        
        Returns:
            go.Figure: Leaderboard chart
        """
        entries = leaderboard.entries[:10]  # Top 10
        
        if not entries:
            fig = go.Figure()
            fig.add_annotation(text="No leaderboard entries")
            return fig
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=[e.user_name for e in entries],
            y=[e.score for e in entries],
            marker_color=['gold', 'silver', '#CD7F32'] + ['lightblue'] * (len(entries) - 3),
            text=[f"#{e.rank}" for e in entries],
            textposition='auto'
        ))
        
        fig.update_layout(
            title=f"Leaderboard: {leaderboard.name}",
            xaxis_title="User",
            yaxis_title="Score",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_impact_chart(self, challenges: List[Challenge]) -> go.Figure:
        """
        Create environmental impact chart.
        
        Args:
            challenges: List of challenges
        
        Returns:
            go.Figure: Impact chart
        """
        completed = [c for c in challenges if c.status.value == 'completed']
        
        if not completed:
            fig = go.Figure()
            fig.add_annotation(text="No completed challenges for impact analysis")
            return fig
        
        # Calculate impact by category
        categories = {}
        for challenge in completed:
            cat = challenge.category.value
            if cat not in categories:
                categories[cat] = {
                    'carbon': 0.0,
                    'water': 0.0,
                    'waste': 0.0
                }
            categories[cat]['carbon'] += challenge.estimated_carbon_savings
            categories[cat]['water'] += challenge.estimated_water_savings
            categories[cat]['waste'] += challenge.estimated_waste_reduction
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Impact by Category', 'Total Impact')
        )
        
        # Impact by category (stacked bar)
        cats = list(categories.keys())
        carbon_vals = [categories[c]['carbon'] for c in cats]
        water_vals = [categories[c]['water'] for c in cats]
        waste_vals = [categories[c]['waste'] for c in cats]
        
        fig.add_trace(
            go.Bar(
                x=cats,
                y=carbon_vals,
                name='Carbon (kg CO2e)',
                marker_color='red'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=cats,
                y=water_vals,
                name='Water (liters)',
                marker_color='blue'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=cats,
                y=waste_vals,
                name='Waste (kg)',
                marker_color='brown'
            ),
            row=1, col=1
        )
        
        # Total impact gauge
        total_carbon = sum(c.estimated_carbon_savings for c in completed)
        total_water = sum(c.estimated_water_savings for c in completed)
        total_waste = sum(c.estimated_waste_reduction for c in completed)
        
        fig.add_trace(
            go.Indicator(
                mode="number+gauge",
                value=total_carbon,
                title={'text': "Total Carbon Saved (kg)"},
                gauge={
                    'axis': {'range': [0, max(100, total_carbon * 1.2)]},
                    'bar': {'color': "green"}
                }
            ),
            row=1, col=2
        )
        
        fig.update_layout(height=400, showlegend=True)
        
        return fig