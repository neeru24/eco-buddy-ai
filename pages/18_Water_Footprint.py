"""
Water Footprint Page - Full page interface for water tracking
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from src.lib.water_calculator import WaterCalculator
from src.lib.water_tips import WaterTips
from src.components.water_dashboard import WaterDashboard


def render_water_footprint(user_id: str = None):
    """
    Render the Water Footprint page.
    
    Args:
        user_id: User ID for personalized data
    """
    
    st.markdown("""
    <style>
        .page-header {
            background: linear-gradient(135deg, #0f172a, #1a2e3a);
            padding: 24px 32px;
            border-radius: 12px;
            margin-bottom: 24px;
            border: 1px solid rgba(59, 130, 246, 0.2);
        }
        .page-header h1 {
            color: #3b82f6;
            font-size: 28px;
            font-weight: 700;
            margin: 0;
        }
        .page-header p {
            color: #94a3b8;
            margin: 8px 0 0 0;
            font-size: 15px;
        }
        .page-header .badge {
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            margin-top: 8px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="page-header">
        <h1>💧 Water Footprint Calculator</h1>
        <p>Track your water usage across daily activities and discover ways to conserve water!</p>
        <span class="badge">🌊 Water Conservation</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize calculator
    if 'water_calculator' not in st.session_state:
        st.session_state.water_calculator = WaterCalculator(user_id)
    
    # Dashboard
    WaterDashboard.render(user_id)
    
    # Quick comparison
    st.markdown("---")
    st.markdown("#### 📊 Water Usage Comparison")
    
    calculator = st.session_state.water_calculator
    footprint = calculator.calculate_footprint()
    
    comparison = calculator.get_comparison_data(footprint)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=comparison['your_daily'],
            title={'text': "Your Daily Usage (L)"},
            delta={'reference': comparison['average_daily']},
            gauge={
                'axis': {'range': [0, 200]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(34, 197, 94, 0.3)"},
                    {'range': [50, 100], 'color': "rgba(251, 191, 36, 0.3)"},
                    {'range': [100, 200], 'color': "rgba(239, 68, 68, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': comparison['average_daily']
                }
            }
        ))
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);padding:20px;border-radius:10px;border:1px solid rgba(59,130,246,0.2);">
            <h4 style="color:#e2e8f0;margin-bottom:12px;">📊 Comparison Details</h4>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                <span style="color:#94a3b8;">Your Daily Usage</span>
                <span style="color:#3b82f6;font-weight:600;">{comparison['your_daily']:.1f} L</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                <span style="color:#94a3b8;">Average Daily Usage</span>
                <span style="color:#4ade80;font-weight:600;">{comparison['average_daily']:.1f} L</span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                <span style="color:#94a3b8;">Difference</span>
                <span style="color:{'#4ade80' if comparison['difference'] < 0 else '#f87171'};font-weight:600;">
                    {comparison['difference']:+.1f} L
                </span>
            </div>
            <div style="display:flex;justify-content:space-between;padding:8px 0;">
                <span style="color:#94a3b8;">Status</span>
                <span style="color:{'#4ade80' if comparison['status'] == 'below' else '#f87171'};font-weight:600;">
                    {comparison['status'].title()}
                </span>
            </div>
            <div style="margin-top:12px;padding:8px 12px;background:rgba(59,130,246,0.1);border-radius:6px;color:#94a3b8;font-size:13px;">
                {comparison['insight']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Water Saving Calculator
    st.markdown("---")
    st.markdown("#### 🧮 Water Saving Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        current_usage = st.number_input(
            "Current Daily Usage (L)",
            min_value=0.0,
            value=footprint.total_daily_liters,
            step=5.0
        )
        target_percentage = st.slider(
            "Target Reduction (%)",
            min_value=5,
            max_value=50,
            value=20,
            step=5
        )
    
    with col2:
        if st.button("📊 Calculate Savings", use_container_width=True):
            goal = calculator.get_reduction_goal(current_usage, target_percentage)
            
            st.markdown(f"""
            <div style="background:rgba(15,23,42,0.6);padding:16px 20px;border-radius:10px;border:1px solid rgba(59,130,246,0.2);">
                <h4 style="color:#e2e8f0;margin-bottom:12px;">🎯 Reduction Goal</h4>
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#94a3b8;">Current Usage</span>
                    <span style="color:#f87171;font-weight:600;">{goal['current_usage']:.1f} L/day</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#94a3b8;">Target Usage</span>
                    <span style="color:#4ade80;font-weight:600;">{goal['target_usage']:.1f} L/day</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#94a3b8;">Reduction Needed</span>
                    <span style="color:#3b82f6;font-weight:600;">{goal['reduction_needed']:.1f} L/day</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:6px 0;">
                    <span style="color:#94a3b8;">Yearly Saving</span>
                    <span style="color:#4ade80;font-weight:600;">{goal['yearly_saving']:.0f} L/year</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick tips section
    st.markdown("---")
    st.markdown("#### 💡 Quick Water Saving Tips")
    
    quick_tips = WaterTips.get_quick_tips(4)
    cols = st.columns(2)
    for i, tip in enumerate(quick_tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div style="background:rgba(15,23,42,0.6);padding:10px 14px;border-radius:6px;border:1px solid rgba(59,130,246,0.1);margin-bottom:6px;">
                {tip}
            </div>
            """, unsafe_allow_html=True)


def main():
    """Main entry point for the Water Footprint page."""
    user_id = st.session_state.get('user_id')
    render_water_footprint(user_id)


if __name__ == "__main__":
    main()