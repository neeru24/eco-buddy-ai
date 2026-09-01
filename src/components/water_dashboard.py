"""
Water Dashboard Component for EcoBuddy AI
Displays water footprint, usage breakdown, and conservation tips.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from src.lib.water_calculator import WaterCalculator, WaterActivity
from src.lib.water_tips import WaterTips
from src.lib.water_analytics import WaterAnalytics


class WaterDashboard:
    """
    Interactive dashboard for water footprint tracking.
    """

    @staticmethod
    def render(user_id: str = None):
        """
        Render the water dashboard.
        
        Args:
            user_id: User ID for personalized data
        """
        # Initialize calculator
        if 'water_calculator' not in st.session_state:
            st.session_state.water_calculator = WaterCalculator(user_id)
        
        calculator = st.session_state.water_calculator
        analytics = WaterAnalytics()
        
        st.markdown("""
        <style>
            .water-card {
                background: rgba(15, 23, 42, 0.6);
                padding: 16px 20px;
                border-radius: 10px;
                border: 1px solid rgba(59, 130, 246, 0.2);
                text-align: center;
                margin-bottom: 12px;
            }
            .water-value {
                font-size: 28px;
                font-weight: 700;
                color: #3b82f6;
            }
            .water-label {
                font-size: 13px;
                color: #94a3b8;
            }
            .water-status {
                display: inline-block;
                padding: 2px 12px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 600;
            }
            .water-status.excellent { background: #dcfce7; color: #16a34a; }
            .water-status.good { background: #dbeafe; color: #2563eb; }
            .water-status.average { background: #fef3c7; color: #d97706; }
            .water-status.poor { background: #fee2e2; color: #dc2626; }
            .tip-card {
                background: rgba(59, 130, 246, 0.05);
                padding: 12px 16px;
                border-radius: 8px;
                border-left: 4px solid #3b82f6;
                margin-bottom: 8px;
            }
            .activity-card {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 8px 12px;
                background: rgba(15, 23, 42, 0.4);
                border-radius: 6px;
                margin-bottom: 4px;
                border: 1px solid rgba(255,255,255,0.05);
            }
        </style>
        """, unsafe_allow_html=True)

        # Get footprint
        footprint = calculator.calculate_footprint()
        
        # Tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Overview",
            "🚿 Activities",
            "💡 Tips",
            "📈 Analytics"
        ])

        with tab1:
            WaterDashboard._render_overview(footprint, calculator)
        
        with tab2:
            WaterDashboard._render_activities(calculator)
        
        with tab3:
            WaterDashboard._render_tips(footprint)
        
        with tab4:
            WaterDashboard._render_analytics(calculator, analytics)

    @staticmethod
    def _render_overview(footprint, calculator):
        """Render overview tab."""
        st.markdown("#### 💧 Water Footprint Overview")
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class="water-card">
                <div class="water-value">{footprint.total_daily_liters:.1f}</div>
                <div class="water-label">📅 Daily (L)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="water-card">
                <div class="water-value">{footprint.total_weekly_liters:.1f}</div>
                <div class="water-label">📆 Weekly (L)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="water-card">
                <div class="water-value">{footprint.total_monthly_liters:.1f}</div>
                <div class="water-label">📊 Monthly (L)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="water-card">
                <div class="water-value">{footprint.total_yearly_liters:.1f}</div>
                <div class="water-label">📈 Yearly (L)</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Efficiency score
        st.markdown("#### 🎯 Efficiency Score")
        
        efficiency = footprint.efficiency_score
        level = calculator.get_efficiency_level(efficiency)
        
        status_class = level['level']
        status_map = {
            'excellent': '🌟 Excellent',
            'good': '🌿 Good',
            'average': '💧 Average',
            'needs_improvement': '⚠️ Needs Improvement',
            'critical': '🔴 Critical'
        }
        
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);padding:20px;border-radius:10px;border:1px solid rgba(59,130,246,0.2);text-align:center;">
            <div style="font-size:48px;margin-bottom:8px;">{level['level'][0].upper()}</div>
            <div style="font-size:24px;font-weight:700;color:#3b82f6;">{efficiency}/100</div>
            <div style="font-size:16px;color:#94a3b8;margin-top:4px;">{status_map.get(level['level'], 'Average')}</div>
            <div style="font-size:14px;color:#e2e8f0;margin-top:8px;">{level['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Category breakdown
        st.markdown("#### 📊 Usage Breakdown")
        
        if footprint.by_category:
            # Create data for chart
            cat_data = []
            category_names = {
                'shower': '🚿 Shower',
                'toilet': '🚽 Toilet',
                'washing_machine': '👕 Laundry',
                'dishwasher': '🍽️ Dishes',
                'garden_watering': '🌿 Garden',
                'car_wash': '🚗 Car Wash',
                'drinking': '💧 Drinking',
                'cooking': '🍳 Cooking',
                'cleaning': '🧹 Cleaning'
            }
            
            for cat, usage in footprint.by_category.items():
                cat_data.append({
                    'Category': category_names.get(cat, cat.title()),
                    'Usage': usage
                })
            
            df = pd.DataFrame(cat_data).sort_values('Usage', ascending=True)
            
            fig = px.bar(
                df,
                x='Usage',
                y='Category',
                orientation='h',
                title='Daily Water Usage by Category',
                color='Usage',
                color_continuous_scale='Blues',
                text='Usage'
            )
            fig.update_layout(
                height=300,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Liters per Day',
                yaxis_title=''
            )
            fig.update_traces(texttemplate='%{text:.1f}L', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No water usage data yet. Add your activities to see the breakdown! 💧")

    @staticmethod
    def _render_activities(calculator):
        """Render activities tab."""
        st.markdown("#### 🚿 Water Activities")
        
        categories = calculator.get_activity_categories()
        
        # Add activity form
        with st.form("add_water_activity"):
            col1, col2 = st.columns(2)
            
            with col1:
                category = st.selectbox(
                    "Activity Type",
                    options=list(categories.keys()),
                    format_func=lambda x: f"{categories[x]['icon']} {categories[x]['name']}"
                )
                
                custom_name = st.text_input("Custom Name (optional)", placeholder="e.g., Morning Shower")
            
            with col2:
                usage = st.number_input(
                    f"Usage (liters)",
                    min_value=0.0,
                    value=categories[category]['default_usage'],
                    step=5.0
                )
                frequency = st.selectbox(
                    "Frequency",
                    options=['daily', 'weekly', 'monthly', 'occasional']
                )
                count = st.number_input("Count", min_value=1, value=1, step=1)
            
            notes = st.text_area("Notes (optional)", placeholder="Additional details...")
            
            if st.form_submit_button("💧 Add Activity", use_container_width=True):
                if usage > 0:
                    activity = WaterActivity(
                        name=custom_name or categories[category]['name'],
                        category=category,
                        usage_liters=usage,
                        frequency=frequency,
                        count=count,
                        notes=notes
                    )
                    result = calculator.add_activity(activity)
                    if result['success']:
                        st.success(result['message'])
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(result.get('error', 'Failed to add activity'))
                else:
                    st.warning("Please enter a usage value greater than 0")
        
        # Display existing activities
        st.markdown("---")
        st.markdown("#### 📋 Your Activities")
        
        activities = calculator._activities
        
        if activities:
            for activity in activities[-10:]:  # Show last 10
                cat_info = categories.get(activity.category, {})
                st.markdown(f"""
                <div class="activity-card">
                    <div>
                        <span>{cat_info.get('icon', '💧')}</span>
                        <span style="font-weight:500;margin-left:8px;">{activity.name}</span>
                        <span style="font-size:13px;color:#94a3b8;margin-left:8px;">({activity.frequency})</span>
                    </div>
                    <div>
                        <span style="color:#3b82f6;font-weight:600;">{activity.usage_liters:.0f}L</span>
                        <span style="font-size:12px;color:#94a3b8;margin-left:4px;">× {activity.count}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(activities) > 10:
                st.caption(f"Showing last 10 of {len(activities)} activities")
        else:
            st.info("No activities added yet. Start tracking your water usage above! 💧")

    @staticmethod
    def _render_tips(footprint):
        """Render tips tab."""
        st.markdown("#### 💡 Water Saving Tips")
        
        # Daily tip
        st.markdown("##### 🌟 Daily Tip")
        daily_tip = WaterTips.get_daily_tip()
        st.markdown(f"""
        <div class="tip-card">
            {daily_tip}
        </div>
        """, unsafe_allow_html=True)
        
        # Personalized tips
        st.markdown("##### 🎯 Personalized Tips")
        personalized_tips = WaterTips.get_personalized_tips(footprint.by_category)
        
        for tip in personalized_tips:
            st.markdown(f"""
            <div class="tip-card">
                {tip}
            </div>
            """, unsafe_allow_html=True)
        
        # Challenge tips
        st.markdown("##### 🏆 Challenges")
        challenges = WaterTips.get_challenge_tips()
        
        cols = st.columns(2)
        for i, challenge in enumerate(challenges):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background:rgba(15,23,42,0.6);padding:12px 16px;border-radius:8px;border:1px solid rgba(59,130,246,0.1);margin-bottom:8px;">
                    <div style="font-weight:600;color:#3b82f6;">{challenge['title']}</div>
                    <div style="font-size:13px;color:#94a3b8;">{challenge['description']}</div>
                    <div style="font-size:12px;color:#4ade80;margin-top:4px;">{challenge['saving']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Quick tips
        st.markdown("##### 💧 Quick Tips")
        quick_tips = WaterTips.get_quick_tips(3)
        for tip in quick_tips:
            st.markdown(f"• {tip}")

    @staticmethod
    def _render_analytics(calculator, analytics):
        """Render analytics tab."""
        st.markdown("#### 📈 Water Analytics")
        
        # Get activities
        activities = calculator._activities
        
        if not activities:
            st.info("Add some water activities to see analytics! 📊")
            return
        
        # Prepare data
        data = []
        for activity in activities:
            data.append({
                'date': activity.date,
                'daily_usage': activity.usage_liters * activity.count,
                'category': activity.category,
                'name': activity.name
            })
        
        # Trends
        trends = analytics.analyze_trends(data)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Trend", trends['trend'].title())
        with col2:
            st.metric("📈 Change", f"{trends['change_percentage']:.1f}%")
        with col3:
            st.metric("📉 Volatility", f"{trends['volatility']:.1f}")
        
        # Usage summary
        summary = analytics.get_usage_summary(data)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📅 Days", summary['total_days'])
        with col2:
            st.metric("💧 Avg Daily", f"{summary['average_daily']:.1f}L")
        with col3:
            st.metric("📈 Max Daily", f"{summary['max_daily']:.1f}L")
        with col4:
            st.metric("📉 Min Daily", f"{summary['min_daily']:.1f}L")
        
        # Anomalies
        anomalies = analytics.detect_anomalies(data)
        if anomalies:
            st.markdown("#### ⚠️ Anomalies Detected")
            for anomaly in anomalies[:3]:
                st.warning(f"📅 {anomaly['date']}: {anomaly['value']:.1f}L (Z-score: {anomaly['z_score']:.2f})")