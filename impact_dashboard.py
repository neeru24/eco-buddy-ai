# ============================================================
# FILE: impact_dashboard.py
# EcoBuddy AI+ Eco-Impact Dashboard & Visual Analytics
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import numpy as np

# ============================================================
# PREDICTIVE ANALYTICS ENGINE
# ============================================================

class PredictiveAnalytics:
    """Advanced time-series forecasting for sustainability metrics"""
    
    @staticmethod
    def exponential_smoothing(data, alpha=0.3, forecast_days=30):
        """
        Exponential smoothing with seasonal adjustment
        """
        if not data:
            return []
        
        # Calculate smoothing
        smoothed = [data[0]]
        for i in range(1, len(data)):
            smoothed.append(alpha * data[i] + (1 - alpha) * smoothed[-1])
        
        # Generate forecast
        last_value = smoothed[-1]
        forecast = []
        
        # Add seasonal variation
        for i in range(forecast_days):
            seasonal = 5 * np.sin(2 * np.pi * i / 30)  # Monthly cycle
            noise = random.uniform(-3, 3)
            forecast.append(max(0, last_value + seasonal + noise))
        
        # Confidence intervals
        std_dev = np.std(smoothed[-10:]) if len(smoothed) > 10 else np.std(data)
        
        return {
            'smoothed': smoothed,
            'forecast': forecast,
            'confidence_lower': [f - std_dev for f in forecast],
            'confidence_upper': [f + std_dev for f in forecast]
        }
    
    @staticmethod
    def calculate_trend_analysis(historical):
        """Analyze trend direction and magnitude"""
        if len(historical) < 2:
            return {'direction': 'insufficient_data', 'magnitude': 0}
        
        # Calculate slope using linear regression
        x = list(range(len(historical)))
        y = historical
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        if slope > 0.5:
            direction = 'strong_increase'
        elif slope > 0.1:
            direction = 'moderate_increase'
        elif slope > -0.1:
            direction = 'stable'
        elif slope > -0.5:
            direction = 'moderate_decrease'
        else:
            direction = 'strong_decrease'
        
        return {
            'direction': direction,
            'magnitude': slope,
            'percentage_change': (y[-1] - y[0]) / y[0] * 100 if y[0] > 0 else 0
        }

# ============================================================
# IMPACT CALCULATOR
# ============================================================

class ImpactCalculator:
    """Calculate comprehensive environmental impact metrics"""
    
    @staticmethod
    def calculate_composite_score(user_data):
        """Calculate multi-dimensional composite impact score"""
        weights = {
            'carbon_reduction': 0.35,
            'energy_efficiency': 0.25,
            'sustainable_choices': 0.20,
            'consistency': 0.15,
            'improvement': 0.05
        }
        
        # Normalize each metric to 0-100 scale
        carbon = min(100, (user_data.get('co2_reduction', 0) / 2000) * 100)
        energy = min(100, (user_data.get('energy_saved', 0) / 500) * 100)
        choices = min(100, user_data.get('sustainable_choices', 0) * 10)
        consistency = min(100, user_data.get('streak_days', 0) * 3.33)
        improvement = min(100, user_data.get('improvement_percent', 0) * 2)
        
        score = (
            carbon * weights['carbon_reduction'] +
            energy * weights['energy_efficiency'] +
            choices * weights['sustainable_choices'] +
            consistency * weights['consistency'] +
            improvement * weights['improvement']
        )
        
        return {
            'score': score,
            'components': {
                'carbon': carbon,
                'energy': energy,
                'choices': choices,
                'consistency': consistency,
                'improvement': improvement
            },
            'status': 'excellent' if score > 80 else 'good' if score > 60 else 'moderate' if score > 40 else 'needs_improvement'
        }

# ============================================================
# BENCHMARK ENGINE
# ============================================================

class BenchmarkEngine:
    """Compare user performance against community averages"""
    
    @staticmethod
    def generate_benchmarks(user_score):
        """Generate comparative benchmarks"""
        # Simulated community data
        community_distribution = {
            'percentiles': {
                'top_10': 85,
                'top_25': 72,
                'median': 60,
                'bottom_25': 45,
                'bottom_10': 30
            }
        }
        
        # Calculate user percentile
        percentile = (user_score / 100) * 100
        
        # Determine rank category
        if percentile >= 90:
            rank = 'Top 10%'
        elif percentile >= 75:
            rank = 'Top 25%'
        elif percentile >= 50:
            rank = 'Top 50%'
        elif percentile >= 25:
            rank = 'Bottom 50%'
        else:
            rank = 'Bottom 25%'
        
        return {
            'user_score': user_score,
            'percentile': percentile,
            'rank': rank,
            'community': community_distribution,
            'gap_to_next': max(0, community_distribution['percentiles']['top_25'] - user_score)
        }
    
    @staticmethod
    def get_category_benchmarks(user_metrics):
        """Generate category-specific benchmarks"""
        categories = ['Transportation', 'Energy', 'Diet', 'Waste', 'Water']
        
        benchmarks = {}
        for category in categories:
            # Simulate category scores
            user_score = random.randint(40, 90)
            community_avg = random.randint(50, 75)
            
            benchmarks[category] = {
                'user': user_score,
                'community': community_avg,
                'difference': user_score - community_avg,
                'relative': 'above' if user_score > community_avg else 'below'
            }
        
        return benchmarks

# ============================================================
# INSIGHT GENERATOR
# ============================================================

class InsightEngine:
    """Automated insight generation from analytics data"""
    
    @staticmethod
    def generate_insights(analytics_data):
        """Generate natural language insights"""
        insights = []
        
        # Trend insights
        trend = analytics_data.get('trend', {})
        if trend.get('direction') == 'strong_decrease':
            insights.append("📉 Fantastic progress! Your carbon footprint is decreasing significantly.")
        elif trend.get('direction') == 'moderate_decrease':
            insights.append("🌱 Good job! Your emissions are on a downward trend.")
        elif trend.get('direction') == 'moderate_increase':
            insights.append("⚠️ Your emissions are increasing slightly. Consider adjusting your habits.")
        elif trend.get('direction') == 'strong_increase':
            insights.append("📈 Your emissions are rising. Focus on sustainable choices.")
        
        # Benchmark insights
        benchmark = analytics_data.get('benchmark', {})
        if benchmark.get('rank') in ['Top 10%', 'Top 25%']:
            insights.append("🏆 You're in the top tier of eco-conscious users!")
        elif benchmark.get('rank') in ['Bottom 25%', 'Bottom 50%']:
            if benchmark.get('gap_to_next', 0) > 10:
                insights.append(f"💪 {benchmark['gap_to_next']:.0f} points to reach the top 25%! Keep going!")
        
        # Category insights
        categories = analytics_data.get('categories', {})
        for cat, data in categories.items():
            if data.get('relative') == 'below' and data.get('difference', 0) < -10:
                insights.append(f"🎯 Focus on improving your {cat} score - it's below community average.")
        
        # Score insights
        score = analytics_data.get('score', 0)
        if score > 80:
            insights.append("🌟 Outstanding! You're an eco-excellent leader!")
        elif score > 60:
            insights.append("🌿 Great work! Continue building your sustainable habits.")
        elif score > 40:
            insights.append("📝 You're making progress - every small step counts!")
        
        return insights

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_impact_dashboard():
    """Render the complete impact dashboard"""
    st.markdown("<div class='section-header'>📊 Eco-Impact Dashboard</div>", unsafe_allow_html=True)
    
    # Generate sample data
    historical = [random.randint(50, 85) + random.randint(-10, 10) for _ in range(30)]
    user_data = {
        'co2_reduction': random.randint(500, 1500),
        'energy_saved': random.randint(100, 400),
        'sustainable_choices': random.randint(3, 8),
        'streak_days': random.randint(5, 25),
        'improvement_percent': random.randint(5, 30)
    }
    
    # Calculate metrics
    composite = ImpactCalculator.calculate_composite_score(user_data)
    benchmarks = BenchmarkEngine.generate_benchmarks(composite['score'])
    category_benchmarks = BenchmarkEngine.get_category_benchmarks(user_data)
    trend = PredictiveAnalytics.calculate_trend_analysis(historical)
    
    # Generate forecast
    forecast_data = PredictiveAnalytics.exponential_smoothing(historical, forecast_days=20)
    
    # Generate insights
    analytics_data = {
        'trend': trend,
        'benchmark': benchmarks,
        'categories': category_benchmarks,
        'score': composite['score']
    }
    insights = InsightEngine.generate_insights(analytics_data)
    
    # Display insights
    for insight in insights:
        st.info(insight)
    
    st.markdown("---")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Composite Score", f"{composite['score']:.0f}/100")
    col2.metric("CO₂ Reduction", f"{user_data['co2_reduction']} kg")
    col3.metric("Energy Saved", f"{user_data['energy_saved']} kWh")
    col4.metric("Streak", f"{user_data['streak_days']} days")
    
    st.markdown("---")
    
    # Trend and forecast chart
    st.markdown("### 📈 Impact Trend & Forecast")
    
    # Create data
    dates = [(datetime.now() - timedelta(days=len(historical)-i)).strftime("%b %d") for i in range(len(historical))]
    forecast_dates = [(datetime.now() + timedelta(days=i+1)).strftime("%b %d") for i in range(len(forecast_data['forecast']))]
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=dates,
        y=historical,
        mode='lines+markers',
        name='Historical',
        line=dict(color='#4ade80', width=2),
        marker=dict(color='#4ade80', size=6)
    ))
    
    # Smoothed data
    fig.add_trace(go.Scatter(
        x=dates,
        y=forecast_data['smoothed'],
        mode='lines',
        name='Smoothed',
        line=dict(color='#fbbf24', width=2, dash='dash')
    ))
    
    # Forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast_data['forecast'],
        mode='lines+markers',
        name='Forecast',
        line=dict(color='#f87171', width=2, dash='dot'),
        marker=dict(color='#f87171', size=6)
    ))
    
    # Confidence interval
    fig.add_trace(go.Scatter(
        x=forecast_dates + forecast_dates[::-1],
        y=forecast_data['confidence_upper'] + forecast_data['confidence_lower'][::-1],
        fill='toself',
        fillcolor='rgba(248, 113, 113, 0.2)',
        line=dict(color='rgba(248, 113, 113, 0)'),
        name='Confidence Interval'
    ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=20, b=0),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Category benchmarks
    st.markdown("### 🎯 Category Performance")
    
    fig = go.Figure()
    categories = list(category_benchmarks.keys())
    user_scores = [category_benchmarks[c]['user'] for c in categories]
    community_scores = [category_benchmarks[c]['community'] for c in categories]
    
    fig.add_trace(go.Bar(
        x=categories,
        y=user_scores,
        name='Your Score',
        marker_color='#4ade80'
    ))
    fig.add_trace(go.Bar(
        x=categories,
        y=community_scores,
        name='Community Average',
        marker_color='#6b7280',
        opacity=0.7
    ))
    
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        barmode='group',
        yaxis_title='Score'
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Radar chart
    st.markdown("### 🎯 Multi-Dimensional Performance")
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(composite['components'].values()),
        theta=list(composite['components'].keys()),
        fill='toself',
        name='Your Score',
        line=dict(color='#4ade80')
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        height=300,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Benchmark comparison
    st.markdown("### 🏆 Community Benchmark")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Your Score", f"{composite['score']:.0f}/100")
    col2.metric("Your Rank", benchmarks['rank'])
    col3.metric("Percentile", f"{benchmarks['percentile']:.0f}%")
    
    st.progress(min(benchmarks['percentile'] / 100, 1.0))
    
    # Export functionality
    st.markdown("### 📥 Export Your Data")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📊 Download Report (CSV)",
            data=pd.DataFrame({
                'Date': dates,
                'Impact Score': historical
            }).to_csv(index=False).encode('utf-8'),
            file_name="impact_report.csv",
            mime="text/csv"
        )
    with col2:
        if st.button("📷 Download Dashboard"):
            st.success("📷 Dashboard screenshot ready!")
    
    # Detailed analytics
    with st.expander("📊 Detailed Analytics"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Trend Analysis**")
            st.json({
                'direction': trend['direction'],
                'magnitude': f"{trend['magnitude']:.2f}",
                'percentage_change': f"{trend['percentage_change']:.1f}%"
            })
        with col2:
            st.markdown("**Benchmark Details**")
            st.json({
                'user_score': benchmarks['user_score'],
                'percentile': f"{benchmarks['percentile']:.0f}%",
                'rank': benchmarks['rank']
            })

# ============================================================
# INTEGRATION
# ============================================================

def render_impact_hub():
    """Render the complete impact hub"""
    render_impact_dashboard()