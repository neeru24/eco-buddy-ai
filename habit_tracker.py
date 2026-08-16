
# ============================================================
# FILE: habit_tracker.py
# EcoBuddy AI+ Eco-Productivity & Habit Tracker
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json

# ============================================================
# HABIT DATABASE
# ============================================================

class HabitDatabase:
    """Pre-defined sustainable habits with impact metrics"""
    
    HABITS = {
        'transport': [
            {'name': '🚲 Walk/Bike instead of drive', 'carbon_saving': 2.5, 'ease': 4, 'category': 'Transport'},
            {'name': '🚌 Use public transit', 'carbon_saving': 1.8, 'ease': 3, 'category': 'Transport'},
            {'name': '🚗 Carpool to work', 'carbon_saving': 2.0, 'ease': 2, 'category': 'Transport'},
            {'name': '🚶 Walk for short trips', 'carbon_saving': 1.0, 'ease': 5, 'category': 'Transport'}
        ],
        'energy': [
            {'name': '💡 Turn off lights', 'carbon_saving': 0.5, 'ease': 5, 'category': 'Energy'},
            {'name': '🔌 Unplug unused electronics', 'carbon_saving': 0.3, 'ease': 4, 'category': 'Energy'},
            {'name': '👕 Air dry clothes', 'carbon_saving': 1.2, 'ease': 3, 'category': 'Energy'},
            {'name': '🌡️ Set thermostat 2° lower', 'carbon_saving': 0.8, 'ease': 3, 'category': 'Energy'}
        ],
        'food': [
            {'name': '🥗 Meatless Monday', 'carbon_saving': 3.0, 'ease': 3, 'category': 'Food'},
            {'name': '🌾 Eat locally sourced food', 'carbon_saving': 1.5, 'ease': 2, 'category': 'Food'},
            {'name': '🍽️ Zero food waste day', 'carbon_saving': 2.0, 'ease': 3, 'category': 'Food'},
            {'name': '🌱 Plant-based meal', 'carbon_saving': 2.5, 'ease': 3, 'category': 'Food'}
        ],
        'waste': [
            {'name': '♻️ Recycle all recyclables', 'carbon_saving': 1.0, 'ease': 4, 'category': 'Waste'},
            {'name': '🛍️ Reusable shopping bags', 'carbon_saving': 0.4, 'ease': 5, 'category': 'Waste'},
            {'name': '🧑‍🌾 Compost food scraps', 'carbon_saving': 1.8, 'ease': 2, 'category': 'Waste'},
            {'name': '💧 Reusable water bottle', 'carbon_saving': 0.6, 'ease': 5, 'category': 'Waste'}
        ],
        'water': [
            {'name': '🚿 Shorten showers by 2 min', 'carbon_saving': 0.6, 'ease': 4, 'category': 'Water'},
            {'name': '🔧 Fix leaky faucets', 'carbon_saving': 0.4, 'ease': 2, 'category': 'Water'},
            {'name': '🌧️ Use rainwater for plants', 'carbon_saving': 0.3, 'ease': 3, 'category': 'Water'},
            {'name': '🧺 Full loads only', 'carbon_saving': 0.5, 'ease': 4, 'category': 'Water'}
        ]
    }
    
    @staticmethod
    def get_all_habits():
        """Get all habits"""
        habits = []
        for category in HabitDatabase.HABITS.values():
            habits.extend(category)
        return habits
    
    @staticmethod
    def get_habits_by_category(category=None):
        """Get habits by category"""
        if category and category != "All":
            return HabitDatabase.HABITS.get(category.lower(), [])
        return HabitDatabase.get_all_habits()

# ============================================================
# HABIT TRACKER
# ============================================================

class HabitTracker:
    """Track user habits and streaks"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load habit data from session"""
        if "habit_data" not in st.session_state:
            st.session_state.habit_data = {}
        return st.session_state.habit_data.get(self.user_id, {
            'active_habits': [],
            'completed_today': [],
            'history': {},
            'streaks': {},
            'best_streaks': {},
            'last_completed': {}
        })
    
    def save(self):
        """Save habit data"""
        st.session_state.habit_data[self.user_id] = self.data
        st.session_state.habit_data_updated = True
    
    def add_habit(self, habit_name):
        """Add a habit to tracking"""
        if habit_name not in self.data['active_habits']:
            self.data['active_habits'].append(habit_name)
            self.data['streaks'][habit_name] = 0
            self.data['best_streaks'][habit_name] = 0
            self.data['history'][habit_name] = []
            self.save()
            return True
        return False
    
    def complete_habit(self, habit_name):
        """Mark a habit as completed today"""
        today = datetime.now().date().isoformat()
        today_habits = self.data.get('completed_today', [])
        
        if habit_name not in today_habits:
            today_habits.append(habit_name)
            self.data['completed_today'] = today_habits
            
            # Update streak
            last_completed = self.data['last_completed'].get(habit_name)
            if last_completed:
                last_date = datetime.fromisoformat(last_completed).date()
                today_date = datetime.now().date()
                day_diff = (today_date - last_date).days
                
                if day_diff == 1:
                    # Consecutive day - increase streak
                    self.data['streaks'][habit_name] += 1
                elif day_diff > 1:
                    # Streak broken - reset
                    self.data['streaks'][habit_name] = 1
                # If same day, don't update
            else:
                # First completion - start streak
                self.data['streaks'][habit_name] = 1
            
            # Update best streak
            current_streak = self.data['streaks'].get(habit_name, 0)
            if current_streak > self.data['best_streaks'].get(habit_name, 0):
                self.data['best_streaks'][habit_name] = current_streak
            
            # Record history
            self.data['history'][habit_name].append({
                'date': today,
                'streak': current_streak
            })
            
            self.data['last_completed'][habit_name] = datetime.now().isoformat()
            self.save()
            return True
        return False
    
    def get_stats(self):
        """Get habit statistics"""
        total_habits = len(self.data['active_habits'])
        completed_today = len(self.data.get('completed_today', []))
        
        total_streak = sum(self.data['streaks'].values()) if self.data['streaks'] else 0
        avg_streak = total_streak / total_habits if total_habits > 0 else 0
        
        return {
            'total_habits': total_habits,
            'completed_today': completed_today,
            'completion_rate': (completed_today / total_habits * 100) if total_habits > 0 else 0,
            'total_streak': total_streak,
            'avg_streak': avg_streak,
            'best_habit': max(self.data['streaks'].items(), key=lambda x: x[1])[0] if self.data['streaks'] else None
        }
    
    def get_streak_level(self, habit_name):
        """Get streak level for a habit"""
        streak = self.data['streaks'].get(habit_name, 0)
        if streak == 0:
            return {"emoji": "🌱", "label": "Seed", "description": "Just starting"}
        elif streak < 7:
            return {"emoji": "🌿", "label": "Sprout", "description": "Building momentum"}
        elif streak < 30:
            return {"emoji": "🌳", "label": "Tree", "description": "Strong habit forming"}
        elif streak < 100:
            return {"emoji": "🌲", "label": "Forest", "description": "Dedicated commitment"}
        else:
            return {"emoji": "🏆", "label": "Eco Champion", "description": "Master of sustainability"}

# ============================================================
# HABIT RECOMMENDER
# ============================================================

class HabitRecommender:
    """Recommend habits based on user profile"""
    
    @staticmethod
    def recommend_habits(user_id):
        """Personalized habit recommendations"""
        all_habits = HabitDatabase.get_all_habits()
        
        # Get user's active habits
        tracker = st.session_state.get('habit_tracker', HabitTracker(user_id))
        active = tracker.data['active_habits']
        
        # Filter out active habits
        available = [h for h in all_habits if h['name'] not in active]
        
        # Score habits
        for habit in available:
            # Higher score for habits with greater carbon saving
            carbon_score = habit['carbon_saving'] / 3 * 40
            
            # Higher score for easier habits
            ease_score = habit['ease'] / 5 * 30
            
            # Random variation for diversity
            variety_score = random.random() * 30
            
            habit['score'] = carbon_score + ease_score + variety_score
        
        # Sort by score
        available.sort(key=lambda x: x['score'], reverse=True)
        
        return available[:5]

# ============================================================
# CARBON SAVINGS CALCULATOR
# ============================================================

class CarbonSavingsCalculator:
    """Calculate carbon savings from habit completion"""
    
    @staticmethod
    def calculate_savings(habits):
        """Calculate total carbon saved"""
        total_carbon = 0
        habit_data = {}
        
        for habit in habits:
            # Find habit in database
            all_habits = HabitDatabase.get_all_habits()
            habit_info = next((h for h in all_habits if h['name'] == habit), None)
            
            if habit_info:
                saving = habit_info['carbon_saving']
                total_carbon += saving
                habit_data[habit] = saving
        
        return {
            'total_carbon': total_carbon,
            'habit_data': habit_data,
            'trees_equivalent': total_carbon / 22,
            'cars_equivalent': total_carbon / 5000  # Average car emits 5000kg CO2/year
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_habit_tracker():
    """Render the complete habit tracker"""
    st.markdown("<div class='section-header'>🌱 Eco-Productivity & Habit Tracker</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get('user_id', 1)
    
    # Initialize tracker
    if "habit_tracker" not in st.session_state:
        st.session_state.habit_tracker = HabitTracker(user_id)
    
    tracker = st.session_state.habit_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Today's Habits",
        "📊 Progress",
        "💡 Recommendations",
        "📈 Impact"
    ])
    
    with tab1:
        render_daily_habits(tracker)
    
    with tab2:
        render_progress(tracker)
    
    with tab3:
        render_recommendations(tracker)
    
    with tab4:
        render_impact(tracker)

def render_daily_habits(tracker):
    """Render daily habits"""
    st.markdown("### 📋 Today's Eco-Habits")
    
    # Stats overview
    stats = tracker.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active Habits", stats['total_habits'])
    col2.metric("Completed Today", f"{stats['completed_today']}/{stats['total_habits']}")
    col3.metric("Completion Rate", f"{stats['completion_rate']:.0f}%")
    col4.metric("Total Streak", f"{stats['total_streak']} days")
    
    st.progress(stats['completion_rate'] / 100)
    
    st.markdown("---")
    
    # Add new habit
    with st.expander("➕ Add New Habit", expanded=False):
        all_habits = HabitDatabase.get_all_habits()
        active_names = tracker.data['active_habits']
        available = [h for h in all_habits if h['name'] not in active_names]
        
        if available:
            habit_options = [h['name'] for h in available]
            selected_habit = st.selectbox("Choose a habit to add", habit_options)
            
            if st.button("Add Habit", use_container_width=True):
                tracker.add_habit(selected_habit)
                st.success(f"✅ Added {selected_habit}!")
                st.rerun()
        else:
            st.info("🎉 You're already tracking all available habits!")
    
    # Display habits
    st.markdown("#### Your Habits")
    
    active_habits = tracker.data['active_habits']
    completed_today = tracker.data.get('completed_today', [])
    
    if active_habits:
        for habit in active_habits:
            is_completed = habit in completed_today
            streak_info = tracker.get_streak_level(habit)
            streak_value = tracker.data['streaks'].get(habit, 0)
            
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    status_icon = "✅" if is_completed else "⬜"
                    st.markdown(f"{status_icon} **{habit}**")
                    st.caption(f"{streak_info['emoji']} {streak_info['label']} - {streak_value} day streak")
                
                with col2:
                    st.caption(f"{streak_info['description']}")
                
                with col3:
                    if not is_completed:
                        if st.button("✅ Complete", key=f"complete_{habit}"):
                            tracker.complete_habit(habit)
                            st.success(f"🌟 Great job! {habit} completed!")
                            st.rerun()
                    else:
                        st.success("✅ Done")
                
                with col4:
                    if st.button("🗑️ Remove", key=f"remove_{habit}"):
                        if habit in tracker.data['active_habits']:
                            tracker.data['active_habits'].remove(habit)
                            tracker.save()
                            st.rerun()
    else:
        st.info("🌱 No habits added yet. Add your first sustainable habit above!")
    
    # Daily motivation
    st.markdown("---")
    st.markdown("### 💪 Daily Motivation")
    
    if stats['completion_rate'] == 100:
        st.success("🌟 Perfect day! You've completed all your habits!")
        st.balloons()
    elif stats['completion_rate'] >= 50:
        st.info("🌿 Great progress! Keep going!")
    else:
        st.info("🌱 Every step counts. Start with one habit today!")

def render_progress(tracker):
    """Render progress visualization"""
    st.markdown("### 📊 Habit Progress")
    
    stats = tracker.get_stats()
    
    # Streak visualization
    st.markdown("#### 🔥 Streak Overview")
    
    if tracker.data['streaks']:
        # Create streak data
        habits = list(tracker.data['streaks'].keys())
        streaks = list(tracker.data['streaks'].values())
        best_streaks = list(tracker.data['best_streaks'].values())
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=habits,
            y=streaks,
            name='Current Streak',
            marker_color='#4ade80'
        ))
        fig.add_trace(go.Bar(
            x=habits,
            y=best_streaks,
            name='Best Streak',
            marker_color='#fbbf24',
            opacity=0.7
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            barmode='group',
            yaxis_title='Days'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Start completing habits to see your streaks!")
    
    # Completion heatmap
    st.markdown("#### 📅 Habit Completion History")
    
    if tracker.data['history']:
        # Create heatmap data
        habits = list(tracker.data['history'].keys())
        dates = []
        values = []
        
        for habit in habits:
            history = tracker.data['history'][habit]
            for entry in history[-30:]:  # Last 30 days
                dates.append(entry['date'])
                values.append(1)
        
        if dates:
            df = pd.DataFrame({
                'Date': pd.to_datetime(dates),
                'Completed': values,
                'Habit': [habit.split()[0] for habit in habits for _ in range(len([h for h in tracker.data['history'][habit] if h in tracker.data['history'][habit][-30:]]))]
            })
            
            fig = px.density_heatmap(
                df,
                x='Date',
                y='Habit',
                z='Completed',
                color_continuous_scale='Greens',
                title="Habit Completion Pattern"
            )
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig, use_container_width=True)
    
    # Achievement milestones
    st.markdown("#### 🏆 Milestone Achievements")
    
    milestones = []
    for habit, streak in tracker.data['streaks'].items():
        if streak >= 30:
            milestones.append(f"🌟 {habit} - 30+ day streak!")
        elif streak >= 7:
            milestones.append(f"🌿 {habit} - 7+ day streak!")
    
    if milestones:
        for milestone in milestones:
            st.success(milestone)
    else:
        st.info("💪 Complete habits for 7 days to start earning milestones!")

def render_recommendations(tracker):
    """Render habit recommendations"""
    st.markdown("### 💡 Habit Recommendations")
    
    # Get recommendations
    recommendations = HabitRecommender.recommend_habits(st.session_state.get('user_id', 1))
    
    if recommendations:
        st.markdown("#### 🌱 Suggested Habits for You")
        
        for habit in recommendations:
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"**{habit['name']}**")
                    st.caption(f"Category: {habit['category']}")
                
                with col2:
                    st.metric("Carbon Saving", f"{habit['carbon_saving']} kg/day")
                
                with col3:
                    if st.button("➕ Add", key=f"rec_{habit['name']}"):
                        tracker.add_habit(habit['name'])
                        st.success(f"✅ Added {habit['name']}!")
                        st.rerun()
        
        st.markdown("---")
        st.markdown("### 📊 Recommendation Breakdown")
        
        # Show recommendation scores
        scores_df = pd.DataFrame([
            {
                "Habit": h['name'],
                "Carbon Score": (h['carbon_saving'] / 3) * 40,
                "Ease Score": (h['ease'] / 5) * 30,
                "Variety": h.get('score', 0) - ((h['carbon_saving'] / 3) * 40) - ((h['ease'] / 5) * 30),
                "Total": h['score']
            }
            for h in recommendations
        ])
        
        fig = go.Figure()
        for col in ['Carbon Score', 'Ease Score', 'Variety']:
            if col in scores_df.columns:
                fig.add_trace(go.Bar(
                    x=scores_df['Habit'],
                    y=scores_df[col],
                    name=col
                ))
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=20, b=0),
            barmode='stack',
            yaxis_title='Score'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.success("🎉 You're already tracking all available habits!")

def render_impact(tracker):
    """Render environmental impact"""
    st.markdown("### 📈 Environmental Impact")
    
    # Calculate impact
    active_habits = tracker.data['active_habits']
    completed_today = tracker.data.get('completed_today', [])
    
    if completed_today:
        savings = CarbonSavingsCalculator.calculate_savings(completed_today)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CO₂ Saved Today", f"{savings['total_carbon']:.1f} kg")
        col2.metric("Trees Equivalent", f"{savings['trees_equivalent']:.1f}")
        col3.metric("Cars Equivalent", f"{savings['cars_equivalent']:.2f}")
        col4.metric("Habits Completed", len(completed_today))
        
        # Breakdown by habit
        if savings['habit_data']:
            st.markdown("#### Breakdown by Habit")
            
            fig = go.Figure(data=[go.Pie(
                labels=list(savings['habit_data'].keys()),
                values=list(savings['habit_data'].values()),
                hole=0.3,
                marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171'])
            )])
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        
        # Projected annual impact
        daily_avg = savings['total_carbon']
        annual_projection = daily_avg * 365
        
        st.markdown("#### 📊 Projected Annual Impact")
        
        col1, col2 = st.columns(2)
        col1.metric("Annual CO₂ Saved", f"{annual_projection:.0f} kg")
        col2.metric("Annual Trees Equivalent", f"{annual_projection / 22:.1f}")
        
        st.progress(min(annual_projection / 5000, 1.0))
        
        if annual_projection > 1000:
            st.success("🌟 Excellent! You're making a significant environmental impact!")
        elif annual_projection > 500:
            st.info("🌿 Good progress! Keep building your sustainable habits!")
        else:
            st.info("🌱 Every habit counts. Add more habits to increase your impact!")
    
    else:
        st.info("📋 Complete some habits today to see your environmental impact!")
        st.markdown("""
        <div style='text-align: center; padding: 40px;'>
            <div style='font-size: 48px;'>🌍</div>
            <h4>Start Your Impact Journey</h4>
            <p>Complete a habit today and track your carbon savings!</p>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_habit_hub():
    """Render the complete habit hub"""
    render_habit_tracker()

# ============================================================