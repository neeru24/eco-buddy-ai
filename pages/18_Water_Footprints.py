"""
Water Footprint Page - Full page interface for water tracking
Complete water management system with tracking, analytics, and conservation tools.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, date
import time
import json

from src.lib.water_calculator import WaterCalculator, WaterActivity, WaterFootprint
from src.lib.water_tips import WaterTips
from src.lib.water_analytics import WaterAnalytics
from src.components.water_dashboard import WaterDashboard


def render_water_footprint(user_id: str = None):
    """
    Render the Water Footprint page.
    
    Args:
        user_id: User ID for personalized data
    """
    
    # Custom CSS
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
        .water-card {
            background: rgba(15, 23, 42, 0.6);
            padding: 16px 20px;
            border-radius: 10px;
            border: 1px solid rgba(59, 130, 246, 0.2);
            text-align: center;
            margin-bottom: 12px;
            transition: all 0.2s;
        }
        .water-card:hover {
            border-color: rgba(59, 130, 246, 0.5);
            transform: translateY(-2px);
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
        .activity-card {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 14px;
            background: rgba(15, 23, 42, 0.4);
            border-radius: 8px;
            margin-bottom: 6px;
            border: 1px solid rgba(255,255,255,0.05);
            transition: all 0.2s;
        }
        .activity-card:hover {
            border-color: rgba(59, 130, 246, 0.3);
            background: rgba(59, 130, 246, 0.05);
        }
        .tip-card {
            background: rgba(59, 130, 246, 0.05);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            margin-bottom: 8px;
            transition: all 0.2s;
        }
        .tip-card:hover {
            background: rgba(59, 130, 246, 0.1);
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 12px;
            margin: 12px 0;
        }
        .comparison-card {
            background: rgba(15, 23, 42, 0.6);
            padding: 16px 20px;
            border-radius: 10px;
            border: 1px solid rgba(59, 130, 246, 0.15);
        }
        .efficiency-ring {
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        .challenge-card {
            background: rgba(15, 23, 42, 0.6);
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid rgba(59, 130, 246, 0.1);
            margin-bottom: 8px;
            transition: all 0.2s;
        }
        .challenge-card:hover {
            border-color: rgba(59, 130, 246, 0.3);
        }
        .progress-label {
            display: flex;
            justify-content: space-between;
            font-size: 13px;
            color: #94a3b8;
        }
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            overflow: hidden;
            margin: 4px 0;
        }
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            background: linear-gradient(90deg, #3b82f6, #4ade80);
            transition: width 0.5s ease;
        }
        .activity-form {
            background: rgba(15, 23, 42, 0.4);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(59, 130, 246, 0.1);
            margin-bottom: 16px;
        }
        .insight-box {
            background: rgba(59, 130, 246, 0.05);
            padding: 12px 16px;
            border-radius: 8px;
            border-left: 4px solid #3b82f6;
            margin: 8px 0;
        }
        .insight-box .icon {
            font-size: 20px;
            margin-right: 8px;
        }
        .insight-box .text {
            color: #e2e8f0;
            font-size: 14px;
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
    
    if 'water_activities' not in st.session_state:
        st.session_state.water_activities = []
    
    calculator = st.session_state.water_calculator
    analytics = WaterAnalytics()
    
    # Get footprint
    footprint = calculator.calculate_footprint()
    
    # Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Dashboard",
        "🚿 Activities",
        "💡 Tips & Challenges",
        "📈 Analytics",
        "🎯 Goals"
    ])
    
    with tab1:
        render_dashboard(footprint, calculator)
    
    with tab2:
        render_activities(calculator)
    
    with tab3:
        render_tips_challenges(footprint)
    
    with tab4:
        render_analytics(calculator, analytics)
    
    with tab5:
        render_goals(footprint, calculator)


def render_dashboard(footprint: WaterFootprint, calculator: WaterCalculator):
    """Render the dashboard tab."""
    st.markdown("#### 💧 Water Footprint Overview")
    
    # Main metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="water-card">
            <div class="water-value">{footprint.total_daily_liters:.1f}</div>
            <div class="water-label">📅 Daily Usage (L)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="water-card">
            <div class="water-value">{footprint.total_weekly_liters:.1f}</div>
            <div class="water-label">📆 Weekly Usage (L)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="water-card">
            <div class="water-value">{footprint.total_monthly_liters:.1f}</div>
            <div class="water-label">📊 Monthly Usage (L)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="water-card">
            <div class="water-value">{footprint.total_yearly_liters:.1f}</div>
            <div class="water-label">📈 Yearly Usage (L)</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Efficiency Score
    st.markdown("#### 🎯 Water Efficiency Score")
    
    efficiency = footprint.efficiency_score
    level = calculator.get_efficiency_level(efficiency)
    
    status_map = {
        'excellent': {'icon': '🌟', 'label': 'Excellent', 'color': '#4ade80'},
        'good': {'icon': '🌿', 'label': 'Good', 'color': '#3b82f6'},
        'average': {'icon': '💧', 'label': 'Average', 'color': '#fbbf24'},
        'needs_improvement': {'icon': '⚠️', 'label': 'Needs Improvement', 'color': '#f97316'},
        'critical': {'icon': '🔴', 'label': 'Critical', 'color': '#ef4444'}
    }
    
    status = status_map.get(level['level'], status_map['average'])
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div style="text-align:center;padding:20px;background:rgba(15,23,42,0.6);border-radius:10px;border:1px solid rgba(59,130,246,0.2);">
            <div style="font-size:48px;">{status['icon']}</div>
            <div style="font-size:32px;font-weight:700;color:{status['color']};">{efficiency}/100</div>
            <div style="font-size:16px;color:#e2e8f0;font-weight:600;">{status['label']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);padding:16px 20px;border-radius:10px;border:1px solid rgba(59,130,246,0.15);height:100%;display:flex;flex-direction:column;justify-content:center;">
            <div style="font-size:14px;color:#94a3b8;">{level['description']}</div>
            <div style="margin-top:8px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;color:#94a3b8;">
                    <span>0</span>
                    <span>50</span>
                    <span>100</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" style="width:{efficiency}%;"></div>
                </div>
            </div>
            <div style="margin-top:8px;font-size:12px;color:#64748b;">
                {footprint.tips[0] if footprint.tips else 'Keep tracking your water usage!'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Category Breakdown
    st.markdown("#### 📊 Usage Breakdown")
    
    if footprint.by_category:
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
        
        cat_data = []
        for cat, usage in footprint.by_category.items():
            cat_data.append({
                'Category': category_names.get(cat, cat.title()),
                'Usage': usage,
                'Percentage': (usage / footprint.total_daily_liters) * 100 if footprint.total_daily_liters > 0 else 0
            })
        
        df = pd.DataFrame(cat_data).sort_values('Usage', ascending=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                df,
                x='Usage',
                y='Category',
                orientation='h',
                title='Daily Usage by Category',
                color='Usage',
                color_continuous_scale='Blues',
                text='Usage'
            )
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                xaxis_title='Liters per Day',
                yaxis_title=''
            )
            fig.update_traces(texttemplate='%{text:.1f}L', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.pie(
                df,
                values='Usage',
                names='Category',
                title='Usage Distribution',
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.Blues_r
            )
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No water usage data yet. Add your activities to see the breakdown! 💧")


def render_activities(calculator: WaterCalculator):
    """Render the activities tab."""
    st.markdown("#### 🚿 Water Activities")
    
    categories = calculator.get_activity_categories()
    
    # Add activity form
    with st.expander("➕ Add New Activity", expanded=True):
        st.markdown('<div class="activity-form">', unsafe_allow_html=True)
        
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
                count = st.number_input("Count per occurrence", min_value=1, value=1, step=1)
            
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
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(result.get('error', 'Failed to add activity'))
                else:
                    st.warning("Please enter a usage value greater than 0")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Display existing activities
    st.markdown("#### 📋 Your Activities")
    
    activities = calculator._activities
    
    if activities:
        # Filter and sort
        filter_cat = st.selectbox(
            "Filter by Category",
            options=['All'] + list(categories.keys()),
            format_func=lambda x: 'All Categories' if x == 'All' else categories[x]['name']
        )
        
        filtered = activities
        if filter_cat != 'All':
            filtered = [a for a in activities if a.category == filter_cat]
        
        # Stats
        st.markdown(f"""
        <div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap;">
            <span style="color:#94a3b8;">📊 Total Activities: <strong style="color:#e2e8f0;">{len(filtered)}</strong></span>
            <span style="color:#94a3b8;">💧 Total Daily Usage: <strong style="color:#3b82f6;">{sum(a.usage_liters * a.count for a in filtered):.0f} L</strong></span>
        </div>
        """, unsafe_allow_html=True)
        
        for activity in filtered[-20:]:
            cat_info = categories.get(activity.category, {})
            st.markdown(f"""
            <div class="activity-card">
                <div>
                    <span>{cat_info.get('icon', '💧')}</span>
                    <span style="font-weight:500;margin-left:8px;color:#e2e8f0;">{activity.name}</span>
                    <span style="font-size:12px;color:#64748b;margin-left:8px;">({activity.frequency})</span>
                </div>
                <div>
                    <span style="color:#3b82f6;font-weight:600;">{activity.usage_liters:.0f}L</span>
                    <span style="font-size:12px;color:#94a3b8;margin-left:4px;">× {activity.count}</span>
                    <span style="font-size:12px;color:#64748b;margin-left:8px;">{activity.date[:10]}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(filtered) > 20:
            st.caption(f"Showing last 20 of {len(filtered)} activities")
    else:
        st.info("No activities added yet. Start tracking your water usage above! 💧")


def render_tips_challenges(footprint: WaterFootprint):
    """Render the tips and challenges tab."""
    st.markdown("#### 💡 Water Saving Tips & Challenges")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 🌟 Daily Tip")
        daily_tip = WaterTips.get_daily_tip()
        st.markdown(f"""
        <div class="tip-card">
            {daily_tip}
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("##### 🎯 Personalized Tips")
        personalized_tips = WaterTips.get_personalized_tips(footprint.by_category)
        
        for tip in personalized_tips[:3]:
            st.markdown(f"""
            <div class="tip-card">
                {tip}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("##### 💧 Quick Tips")
        quick_tips = WaterTips.get_quick_tips(3)
        for tip in quick_tips:
            st.markdown(f"• {tip}")
    
    with col2:
        st.markdown("##### 🏆 Water Challenges")
        challenges = WaterTips.get_challenge_tips()
        
        for challenge in challenges:
            st.markdown(f"""
            <div class="challenge-card">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <div style="font-weight:600;color:#3b82f6;">{challenge['title']}</div>
                        <div style="font-size:13px;color:#94a3b8;">{challenge['description']}</div>
                    </div>
                    <div style="font-size:12px;color:#4ade80;white-space:nowrap;margin-left:8px;">{challenge['saving']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Water saving calculator
        st.markdown("##### 🧮 Water Saving Calculator")
        
        current = st.number_input(
            "Current Daily Usage (L)",
            min_value=0.0,
            value=footprint.total_daily_liters,
            step=5.0,
            key="calc_current"
        )
        
        target_pct = st.slider(
            "Target Reduction (%)",
            min_value=5,
            max_value=50,
            value=20,
            step=5,
            key="calc_target"
        )
        
        if current > 0:
            target = current * (1 - target_pct / 100)
            saving = current - target
            
            st.markdown(f"""
            <div style="background:rgba(15,23,42,0.6);padding:12px 16px;border-radius:8px;border:1px solid rgba(59,130,246,0.15);margin-top:8px;">
                <div style="display:flex;justify-content:space-between;padding:4px 0;">
                    <span style="color:#94a3b8;">Current</span>
                    <span style="color:#f87171;">{current:.1f} L/day</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;">
                    <span style="color:#94a3b8;">Target</span>
                    <span style="color:#4ade80;">{target:.1f} L/day</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;border-top:1px solid rgba(255,255,255,0.05);">
                    <span style="color:#94a3b8;">💧 Daily Saving</span>
                    <span style="color:#3b82f6;font-weight:600;">{saving:.1f} L</span>
                </div>
                <div style="display:flex;justify-content:space-between;padding:4px 0;">
                    <span style="color:#94a3b8;">🌊 Yearly Saving</span>
                    <span style="color:#3b82f6;font-weight:600;">{saving * 365:.0f} L</span>
                </div>
            </div>
            """, unsafe_allow_html=True)


def render_analytics(calculator: WaterCalculator, analytics: WaterAnalytics):
    """Render the analytics tab."""
    st.markdown("#### 📈 Water Analytics")
    
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Trend", trends['trend'].title())
    with col2:
        st.metric("📈 Change", f"{trends['change_percentage']:.1f}%")
    with col3:
        st.metric("📉 Volatility", f"{trends['volatility']:.1f}")
    with col4:
        st.metric("📅 Data Points", trends['data_points'])
    
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
    
    # Weekly pattern
    if len(data) >= 7:
        st.markdown("#### 📅 Weekly Pattern")
        pattern = analytics.get_weekly_pattern(data)
        
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        values = [pattern.get(i, 0) for i in range(7)]
        
        fig = px.bar(
            x=days,
            y=values,
            title='Water Usage by Day of Week',
            labels={'x': 'Day', 'y': 'Liters'},
            color=values,
            color_continuous_scale='Blues'
        )
        fig.update_layout(
            height=300,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Anomalies
    anomalies = analytics.detect_anomalies(data)
    if anomalies:
        st.markdown("#### ⚠️ Anomalies Detected")
        for anomaly in anomalies[:3]:
            st.warning(f"📅 {anomaly['date'][:10]}: {anomaly['value']:.1f}L (Z-score: {anomaly['z_score']:.2f})")


def render_goals(footprint: WaterFootprint, calculator: WaterCalculator):
    """Render the goals tab."""
    st.markdown("#### 🎯 Water Reduction Goals")
    
    current = footprint.total_daily_liters
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("##### 📊 Current Status")
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);padding:16px;border-radius:10px;border:1px solid rgba(59,130,246,0.15);">
            <div style="font-size:14px;color:#94a3b8;">Current Daily Usage</div>
            <div style="font-size:32px;font-weight:700;color:#3b82f6;">{current:.1f} L</div>
            <div style="font-size:13px;color:#94a3b8;margin-top:4px;">
                {footprint.total_yearly_liters:.0f} L per year
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("##### 🎯 Set New Goal")
        
        target_usage = st.number_input(
            "Target Daily Usage (L)",
            min_value=0.0,
            value=max(10, current * 0.7),
            step=5.0,
            key="goal_target"
        )
        
        deadline = st.date_input(
            "Deadline",
            value=date.today() + timedelta(days=30),
            key="goal_deadline"
        )
        
        if st.button("🎯 Set Goal", use_container_width=True):
            if target_usage > 0 and target_usage < current:
                st.success(f"✅ Goal set! Reduce water usage to {target_usage:.1f}L/day by {deadline.strftime('%b %d, %Y')}")
                st.balloons()
            else:
                st.warning("Please set a target lower than your current usage")
    
    # Progress tracking
    if 'goal_target' in st.session_state:
        st.markdown("##### 📈 Goal Progress")
        
        target = st.session_state.goal_target
        progress = ((current - target) / current) * 100 if current > 0 else 0
        progress = max(0, min(100, progress))
        
        st.markdown(f"""
        <div style="background:rgba(15,23,42,0.6);padding:16px 20px;border-radius:10px;border:1px solid rgba(59,130,246,0.15);">
            <div class="progress-label">
                <span>Progress to Goal</span>
                <span>{progress:.0f}%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" style="width:{progress}%;"></div>
            </div>
            <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:13px;color:#94a3b8;">
                <span>Current: {current:.1f} L</span>
                <span>Target: {target:.1f} L</span>
            </div>
            <div style="margin-top:8px;font-size:13px;color:#94a3b8;">
                📅 Deadline: {deadline.strftime('%b %d, %Y') if 'deadline' in locals() else '30 days'}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips for reaching goal
        st.markdown("##### 💡 Tips to Reach Your Goal")
        reduction_needed = current - target
        if reduction_needed > 0:
            tips = WaterTips.get_personalized_tips(footprint.by_category)
            for tip in tips[:2]:
                st.markdown(f"""
                <div class="insight-box">
                    <span class="icon">💡</span>
                    <span class="text">{tip}</span>
                </div>
                """, unsafe_allow_html=True)


def main():
    """Main entry point for the Water Footprint page."""
    user_id = st.session_state.get('user_id')
    render_water_footprint(user_id)


if __name__ == "__main__":
    main()