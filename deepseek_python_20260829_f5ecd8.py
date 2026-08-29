"""
Circular Economy & Waste Lifecycle Manager - Visualizations
Chart and visualization functions for circular economy data.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from circular_economy.models import (
    CircularItem, CircularityScore, HouseholdCircularity,
    WasteReduction, LifecycleStage
)

logger = logging.getLogger(__name__)


class CircularVisualizer:
    """
    Creates visualizations for circular economy data.
    """
    
    def __init__(self):
        """Initialize the visualizer."""
        logger.info("Circular Visualizer initialized")
    
    def create_circularity_radar(self, score: CircularityScore) -> go.Figure:
        """
        Create circularity radar chart.
        
        Args:
            score: Circularity score
        
        Returns:
            go.Figure: Radar chart
        """
        categories = ['Reuse', 'Repair', 'Recycle', 'Waste Reduction']
        values = [
            score.reuse_score,
            score.repair_score,
            score.recycle_score,
            score.waste_reduction_score
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name='Circularity',
            line_color='green'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="Circularity Score Breakdown",
            showlegend=True
        )
        
        return fig
    
    def create_circularity_gauge(self, score: float, title: str = "Circularity Score") -> go.Figure:
        """
        Create circularity gauge chart.
        
        Args:
            score: Circularity score (0-100)
            title: Chart title
        
        Returns:
            go.Figure: Gauge chart
        """
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            title={'text': title},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': self._get_score_color(score)},
                'steps': [
                    {'range': [0, 20], 'color': "lightgray"},
                    {'range': [20, 40], 'color': "gray"},
                    {'range': [40, 60], 'color': "lightblue"},
                    {'range': [60, 80], 'color': "lightgreen"},
                    {'range': [80, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 50
                }
            }
        ))
        
        fig.update_layout(height=300)
        
        return fig
    
    def create_waste_reduction_chart(self, reduction: WasteReduction) -> go.Figure:
        """
        Create waste reduction breakdown chart.
        
        Args:
            reduction: Waste reduction metrics
        
        Returns:
            go.Figure: Waste reduction chart
        """
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Waste Diversion by Action',
                'Diversion Rate'
            )
        )
        
        # Bar chart for diversion by action
        actions = ['Repair', 'Reuse', 'Donation', 'Resale', 'Recycling']
        values = [
            reduction.repair_diverted_kg,
            reduction.reuse_diverted_kg,
            reduction.donation_diverted_kg,
            reduction.resale_diverted_kg,
            reduction.recycling_diverted_kg
        ]
        
        fig.add_trace(
            go.Bar(
                x=actions,
                y=values,
                name='Waste Diverted (kg)',
                marker_color='green'
            ),
            row=1, col=1
        )
        
        # Gauge for diversion rate
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=reduction.diversion_rate,
                title={'text': "Diversion Rate (%)"},
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
        
        fig.update_layout(height=500, showlegend=False)
        
        return fig
    
    def create_lifecycle_timeline(self, item: CircularItem) -> go.Figure:
        """
        Create lifecycle timeline for an item.
        
        Args:
            item: The item
        
        Returns:
            go.Figure: Timeline chart
        """
        fig = go.Figure()
        
        # Get timeline data
        stages = []
        dates = []
        
        # Add purchase
        if item.purchase_date:
            stages.append('Purchase')
            dates.append(item.purchase_date)
        
        # Add lifecycle transitions
        for transition in item.lifecycle_history:
            stages.append(transition.to_stage.value.replace('_', ' ').title())
            dates.append(transition.transition_date)
        
        # Create horizontal bar chart
        y_positions = list(range(len(stages)))
        
        fig.add_trace(go.Bar(
            x=[1] * len(stages),
            y=y_positions,
            orientation='h',
            text=stages,
            textposition='inside',
            marker_color='lightblue',
            name='Lifecycle Stages'
        ))
        
        fig.update_layout(
            title=f"Lifecycle Timeline: {item.name}",
            xaxis=dict(
                title="",
                showticklabels=False,
                range=[0, 1.5]
            ),
            yaxis=dict(
                title="",
                tickvals=y_positions,
                ticktext=stages
            ),
            height=300 + len(stages) * 20,
            showlegend=False
        )
        
        return fig
    
    def create_household_dashboard(self, household: HouseholdCircularity) -> go.Figure:
        """
        Create household circularity dashboard.
        
        Args:
            household: Household circularity metrics
        
        Returns:
            go.Figure: Dashboard chart
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'Circularity Score',
                'Category Breakdown',
                'Action Distribution',
                'Member Contributions'
            )
        )
        
        # Circularity gauge
        fig.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=household.household_circularity_score,
                title={'text': "Household Score"},
                gauge={
                    'axis': {'range': [0, 100]},
                    'bar': {'color': self._get_score_color(household.household_circularity_score)}
                }
            ),
            row=1, col=1
        )
        
        # Category breakdown
        categories = list(household.category_metrics.keys())
        circularity_pct = []
        for cat in categories:
            metrics = household.category_metrics[cat]
            pct = (metrics['circular_items'] / metrics['count'] * 100) if metrics['count'] > 0 else 0
            circularity_pct.append(pct)
        
        fig.add_trace(
            go.Bar(
                x=categories,
                y=circularity_pct,
                name='Category Circularity',
                marker_color='green'
            ),
            row=1, col=2
        )
        
        # Action distribution
        actions = ['Reuse', 'Repair', 'Recycle', 'Donate', 'Resale']
        counts = [
            household.total_reuse,
            household.total_repair,
            household.total_recycle,
            household.total_donate,
            household.total_resale
        ]
        
        fig.add_trace(
            go.Pie(
                labels=actions,
                values=counts,
                name='Actions'
            ),
            row=2, col=1
        )
        
        # Member contributions
        members = list(household.member_contributions.keys())
        member_scores = []
        for member in members:
            contrib = household.member_contributions[member]
            # Calculate approximate score
            score = (contrib.get('repairs', 0) * 10 + 
                    contrib.get('reuses', 0) * 15 + 
                    contrib.get('recycles', 0) * 5)
            member_scores.append(min(100, score))
        
        if members:
            fig.add_trace(
                go.Bar(
                    x=members[:5],
                    y=member_scores[:5],
                    name='Member Contributions',
                    marker_color='blue'
                ),
                row=2, col=2
            )
        
        fig.update_layout(height=600, showlegend=False)
        
        return fig
    
    def create_trend_chart(self, trends: Dict[str, Any]) -> go.Figure:
        """
        Create trend chart.
        
        Args:
            trends: Trend analytics data
        
        Returns:
            go.Figure: Trend chart
        """
        if 'months' not in trends or not trends['months']:
            return go.Figure()
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Monthly Actions',
                'Impact Trends'
            )
        )
        
        months = trends['months']
        data = trends['data']
        
        # Extract action data
        repairs = [d['repairs'] for d in data]
        reuses = [d['reuses'] for d in data]
        recycles = [d['recycles'] for d in data]
        carbon_saved = [d['carbon_saved'] for d in data]
        waste_diverted = [d['waste_diverted'] for d in data]
        
        # Action trends
        fig.add_trace(
            go.Scatter(
                x=months,
                y=repairs,
                name='Repairs',
                mode='lines+markers',
                line_color='blue'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=reuses,
                name='Reuses',
                mode='lines+markers',
                line_color='green'
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=recycles,
                name='Recycles',
                mode='lines+markers',
                line_color='orange'
            ),
            row=1, col=1
        )
        
        # Impact trends
        fig.add_trace(
            go.Scatter(
                x=months,
                y=carbon_saved,
                name='Carbon Saved (kg)',
                mode='lines+markers',
                line_color='red'
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=months,
                y=waste_diverted,
                name='Waste Diverted (kg)',
                mode='lines+markers',
                line_color='purple'
            ),
            row=2, col=1
        )
        
        fig.update_layout(height=500, showlegend=True)
        
        return fig
    
    def create_category_comparison(self, items: List[CircularItem]) -> go.Figure:
        """
        Create category comparison chart.
        
        Args:
            items: List of items
        
        Returns:
            go.Figure: Comparison chart
        """
        # Group by category
        categories = {}
        for item in items:
            cat = item.category.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item.circularity_score)
        
        fig = go.Figure()
        
        for category, scores in categories.items():
            fig.add_trace(go.Box(
                y=scores,
                name=category,
                boxmean='sd'
            ))
        
        fig.update_layout(
            title="Circularity Scores by Category",
            xaxis_title="Category",
            yaxis_title="Circularity Score",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_lifecycle_flow(self, item: CircularItem) -> go.Figure:
        """
        Create lifecycle flow diagram.
        
        Args:
            item: The item
        
        Returns:
            go.Figure: Flow diagram
        """
        # Get all stages
        stages = set()
        stages.add(item.current_lifecycle_stage.value)
        
        for transition in item.lifecycle_history:
            stages.add(transition.from_stage.value)
            stages.add(transition.to_stage.value)
        
        # Create sankey diagram
        fig = go.Figure(data=[go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=list(stages),
                color="blue"
            ),
            link=dict(
                source=[],
                target=[],
                value=[]
            )
        )])
        
        # Add transitions
        for transition in item.lifecycle_history:
            source_idx = list(stages).index(transition.from_stage.value)
            target_idx = list(stages).index(transition.to_stage.value)
            fig.data[0].link.source.append(source_idx)
            fig.data[0].link.target.append(target_idx)
            fig.data[0].link.value.append(1)
        
        fig.update_layout(
            title=f"Lifecycle Flow: {item.name}",
            height=400
        )
        
        return fig
    
    def _get_score_color(self, score: float) -> str:
        """Get color based on score."""
        if score >= 75:
            return "#28a745"  # Green
        elif score >= 50:
            return "#ffc107"  # Yellow
        elif score >= 25:
            return "#fd7e14"  # Orange
        else:
            return "#dc3545"  # Red