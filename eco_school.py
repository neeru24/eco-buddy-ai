

# ============================================================
# FILE: eco_school.py
# EcoBuddy AI+ Eco-School & Youth Sustainability Education
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# CURRICULUM DATABASE
# ============================================================

class CurriculumDatabase:
    """Sustainability education curriculum modules"""
    
    MODULES = {
        "beginner": [
            {
                "id": "b1",
                "title": "🌱 What is Sustainability?",
                "description": "Learn the basics of sustainability and why it matters",
                "duration": "15 min",
                "type": "Lesson",
                "activities": ["Quiz", "Discussion", "Drawing"],
                "age_group": "8-12",
                "emoji": "🌍"
            },
            {
                "id": "b2",
                "title": "♻️ Reduce, Reuse, Recycle",
                "description": "Understand the 3 R's and how to apply them",
                "duration": "20 min",
                "type": "Lesson",
                "activities": ["Sorting Game", "Pledge", "Art Project"],
                "age_group": "8-12",
                "emoji": "♻️"
            },
            {
                "id": "b3",
                "title": "🌳 Trees & Our Planet",
                "description": "Learn why trees are important for our environment",
                "duration": "15 min",
                "type": "Lesson",
                "activities": ["Tree ID", "Leaf Art", "Planting"],
                "age_group": "8-12",
                "emoji": "🌳"
            },
            {
                "id": "b4",
                "title": "💧 Water Conservation",
                "description": "Understanding water and why we need to save it",
                "duration": "20 min",
                "type": "Lesson",
                "activities": ["Water Audit", "Poster Making", "Pledge"],
                "age_group": "8-12",
                "emoji": "💧"
            }
        ],
        "intermediate": [
            {
                "id": "i1",
                "title": "🌍 Climate Change Explained",
                "description": "Understanding climate change and its effects",
                "duration": "25 min",
                "type": "Lesson",
                "activities": ["Experiment", "Research", "Presentation"],
                "age_group": "13-17",
                "emoji": "🌡️"
            },
            {
                "id": "i2",
                "title": "☀️ Renewable Energy",
                "description": "Explore different types of renewable energy",
                "duration": "30 min",
                "type": "Lesson",
                "activities": ["Model Building", "Design", "Debate"],
                "age_group": "13-17",
                "emoji": "☀️"
            },
            {
                "id": "i3",
                "title": "🌿 Biodiversity & Ecosystems",
                "description": "Learn about ecosystems and why biodiversity matters",
                "duration": "25 min",
                "type": "Lesson",
                "activities": ["Ecosystem Map", "Research", "Conservation Plan"],
                "age_group": "13-17",
                "emoji": "🌿"
            },
            {
                "id": "i4",
                "title": "♻️ Circular Economy",
                "description": "Understanding the circular economy concept",
                "duration": "30 min",
                "type": "Lesson",
                "activities": ["Design Challenge", "Analysis", "Innovation Project"],
                "age_group": "13-17",
                "emoji": "🔄"
            }
        ],
        "advanced": [
            {
                "id": "a1",
                "title": "🌍 Sustainable Development Goals",
                "description": "Deep dive into the UN SDGs and how they apply locally",
                "duration": "40 min",
                "type": "Lesson",
                "activities": ["SDG Project", "Community Action", "Report Writing"],
                "age_group": "16-18",
                "emoji": "🎯"
            },
            {
                "id": "a2",
                "title": "📊 Environmental Policy",
                "description": "Understanding environmental policy and advocacy",
                "duration": "45 min",
                "type": "Lesson",
                "activities": ["Policy Analysis", "Letter Writing", "Debate"],
                "age_group": "16-18",
                "emoji": "📋"
            },
            {
                "id": "a3",
                "title": "💡 Innovation for Sustainability",
                "description": "Developing solutions for environmental challenges",
                "duration": "50 min",
                "type": "Project",
                "activities": ["Prototyping", "Business Case", "Pitch"],
                "age_group": "16-18",
                "emoji": "💡"
            },
            {
                "id": "a4",
                "title": "🌱 Sustainable Agriculture",
                "description": "Exploring sustainable food production systems",
                "duration": "40 min",
                "type": "Lesson",
                "activities": ["Garden Design", "Research", "Presentation"],
                "age_group": "16-18",
                "emoji": "🌾"
            }
        ]
    }
    
    @staticmethod
    def get_modules(level=None):
        """Get curriculum modules"""
        if level and level != "All":
            return CurriculumDatabase.MODULES.get(level.lower(), [])
        all_modules = []
        for modules in CurriculumDatabase.MODULES.values():
            all_modules.extend(modules)
        return all_modules
    
    @staticmethod
    def get_levels():
        """Get available levels"""
        return ["All", "Beginner", "Intermediate", "Advanced"]

# ============================================================
# STUDENT TRACKER
# ============================================================

class StudentTracker:
    """Track student progress and achievements"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load student data from session"""
        if "student_data" not in st.session_state:
            st.session_state.student_data = {}
        return st.session_state.student_data.get(self.user_id, {
            "completed_modules": [],
            "points": 0,
            "badges": [],
            "projects": [],
            "start_date": datetime.now().isoformat()
        })
    
    def save(self):
        """Save student data"""
        st.session_state.student_data[self.user_id] = self.data
    
    def complete_module(self, module_id):
        """Mark module as completed"""
        if module_id not in self.data["completed_modules"]:
            self.data["completed_modules"].append(module_id)
            self.data["points"] += 25
            self._check_badges()
            self.save()
            return True
        return False
    
    def _check_badges(self):
        """Check and award badges"""
        completed = len(self.data["completed_modules"])
        badges = []
        
        if completed >= 1:
            badges.append("🌱 First Step")
        if completed >= 4:
            badges.append("📚 Eco Learner")
        if completed >= 8:
            badges.append("🌟 Eco Explorer")
        if completed >= 12:
            badges.append("🏆 Eco Champion")
        if self.data["points"] >= 300:
            badges.append("💪 Eco Master")
        
        for badge in badges:
            if badge not in self.data["badges"]:
                self.data["badges"].append(badge)
    
    def get_stats(self):
        """Get student statistics"""
        return {
            "completed": len(self.data["completed_modules"]),
            "total_modules": len(CurriculumDatabase.get_modules()),
            "points": self.data["points"],
            "badges": self.data["badges"],
            "start_date": self.data["start_date"]
        }

# ============================================================
# ECO-CHALLENGES
# ============================================================

class EcoChallenges:
    """Youth eco-challenges for real-world action"""
    
    CHALLENGES = [
        {
            "id": "c1",
            "title": "🌱 Plant a Seed",
            "description": "Plant a seed and watch it grow. Track its progress",
            "points": 50,
            "duration": "30 days",
            "emoji": "🌱",
            "category": "Garden"
        },
        {
            "id": "c2",
            "title": "♻️ Zero Waste Day",
            "description": "Go one day without creating any non-recyclable waste",
            "points": 75,
            "duration": "1 day",
            "emoji": "♻️",
            "category": "Waste"
        },
        {
            "id": "c3",
            "title": "🔍 Energy Detective",
            "description": "Find and fix 5 things that waste energy at home",
            "points": 60,
            "duration": "7 days",
            "emoji": "🔍",
            "category": "Energy"
        },
        {
            "id": "c4",
            "title": "🌳 Tree Champion",
            "description": "Plant or care for a tree in your community",
            "points": 100,
            "duration": "30 days",
            "emoji": "🌳",
            "category": "Environment"
        },
        {
            "id": "c5",
            "title": "💧 Water Saver",
            "description": "Reduce your water usage by 20% for one week",
            "points": 50,
            "duration": "7 days",
            "emoji": "💧",
            "category": "Water"
        },
        {
            "id": "c6",
            "title": "🥗 Meatless Week",
            "description": "Try a plant-based diet for one week",
            "points": 80,
            "duration": "7 days",
            "emoji": "🥗",
            "category": "Food"
        }
    ]
    
    @staticmethod
    def get_challenges(category=None):
        """Get challenges by category"""
        if category and category != "All":
            return [c for c in EcoChallenges.CHALLENGES if c["category"] == category]
        return EcoChallenges.CHALLENGES
    
    @staticmethod
    def get_categories():
        """Get challenge categories"""
        return ["All"] + sorted(set(c["category"] for c in EcoChallenges.CHALLENGES))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_school():
    """Render the complete eco-school platform"""
    st.markdown("<div class='section-header'>📚 Eco-School & Youth Sustainability Education</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize student tracker
    if "student_tracker" not in st.session_state:
        st.session_state.student_tracker = StudentTracker(user_id)
    
    tracker = st.session_state.student_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📚 Learn",
        "🎯 Challenges",
        "🏆 Progress",
        "📊 Dashboard"
    ])
    
    with tab1:
        render_curriculum(tracker)
    
    with tab2:
        render_challenges(tracker)
    
    with tab3:
        render_progress(tracker)
    
    with tab4:
        render_dashboard(tracker)

def render_curriculum(tracker):
    """Render curriculum"""
    st.markdown("### 📚 Learn About Sustainability")
    
    # Level selector
    levels = CurriculumDatabase.get_levels()
    selected_level = st.selectbox("Select Learning Level", levels)
    
    # Get modules
    modules = CurriculumDatabase.get_modules(selected_level)
    
    # Display modules
    for module in modules:
        is_completed = module["id"] in tracker.data["completed_modules"]
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {"#4ade80" if is_completed else "#6b7280"};'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{module['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700;'>{module['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {module['type']} • {module['duration']} • Ages {module['age_group']}
                            </div>
                        </div>
                        <div>
                            {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;">✅ Completed</span>' if is_completed else 
                             f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #6b7280;">📚 Start</span>'}
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 4px 0;'>{module['description']}</p>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{activity}</span>' for activity in module['activities'][:3]])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if not is_completed:
                if st.button(f"Start", key=f"start_{module['id']}"):
                    # Show lesson content in expander
                    st.session_state.selected_module = module['id']
                    st.rerun()
        
        if st.session_state.get("selected_module") == module["id"]:
            with st.expander("📖 Lesson Content", expanded=True):
                st.markdown(f"### {module['title']}")
                st.markdown(f"**Description:** {module['description']}")
                st.markdown(f"**Duration:** {module['duration']}")
                st.markdown(f"**Activities:**")
                for activity in module['activities']:
                    st.markdown(f"• {activity}")
                
                # Quick quiz
                st.markdown("#### Quick Check")
                st.markdown("What did you learn?")
                if st.button("✅ I've completed this lesson", key=f"complete_{module['id']}"):
                    tracker.complete_module(module["id"])
                    st.success("🎉 Great job! Module completed! +25 points")
                    st.balloons()
                    st.session_state.selected_module = None
                    st.rerun()
        
        st.markdown("---")

def render_challenges(tracker):
    """Render eco-challenges"""
    st.markdown("### 🎯 Eco-Challenges")
    
    st.markdown("""
    <div class='subtitle'>
        Take real-world action and earn points
    </div>
    """, unsafe_allow_html=True)
    
    # Category filter
    categories = EcoChallenges.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get challenges
    challenges = EcoChallenges.get_challenges(selected_category)
    
    # Display challenges
    for challenge in challenges:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{challenge['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700;'>{challenge['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {challenge['category']} • {challenge['duration']}
                            </div>
                        </div>
                        <div>
                            <span style='background: #fbbf24; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;'>
                                +{challenge['points']} pts
                            </span>
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 4px 0;'>{challenge['description']}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🎯 Take Challenge", key=f"challenge_{challenge['id']}"):
            st.session_state.selected_challenge = challenge['id']
            st.rerun()
        
        if st.session_state.get("selected_challenge") == challenge["id"]:
            with st.expander("Challenge Details", expanded=True):
                st.markdown(f"### {challenge['title']}")
                st.markdown(f"**Description:** {challenge['description']}")
                st.markdown(f"**Duration:** {challenge['duration']}")
                st.markdown(f"**Points:** +{challenge['points']}")
                
                st.markdown("#### Steps")
                steps = [
                    "1. Plan your challenge",
                    "2. Take action",
                    "3. Track your progress",
                    "4. Share your results",
                    "5. Earn points"
                ]
                for step in steps:
                    st.markdown(f"• {step}")
                
                if st.button("✅ Start Challenge", key=f"start_challenge_{challenge['id']}"):
                    st.success(f"🎉 You've started the {challenge['title']} challenge!")
                    st.session_state.selected_challenge = None
                    st.rerun()
        
        st.markdown("---")

def render_progress(tracker):
    """Render student progress"""
    st.markdown("### 🏆 Your Progress")
    
    stats = tracker.get_stats()
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Modules Completed", f"{stats['completed']}/{stats['total_modules']}")
    col2.metric("Points Earned", stats['points'])
    col3.metric("Badges", len(stats['badges']))
    col4.metric("Started", datetime.fromisoformat(stats['start_date']).strftime("%b %d"))
    
    # Progress bar
    st.markdown("#### 📊 Learning Progress")
    progress = stats['completed'] / stats['total_modules'] if stats['total_modules'] > 0 else 0
    st.progress(progress)
    st.caption(f"{progress*100:.0f}% complete")
    
    # Badges
    st.markdown("#### 🎖️ Your Badges")
    
    if stats['badges']:
        cols = st.columns(3)
        for i, badge in enumerate(stats['badges']):
            with cols[i % 3]:
                st.markdown(f"""
                <div style='background: #1f2937; padding: 15px; border-radius: 10px; text-align: center;'>
                    <div style='font-size: 32px;'>{badge.split()[0]}</div>
                    <div style='font-size: 14px; font-weight: 600;'>{badge}</div>
                    <div style='font-size: 11px; color: #6b7280;'>Achievement</div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("🌟 Complete modules to earn badges!")
    
    # Recent activity
    st.markdown("#### 📅 Recent Activity")
    
    # Simulated activity
    activities = [
        {"date": datetime.now() - timedelta(days=0), "text": "Completed a module", "emoji": "📚"},
        {"date": datetime.now() - timedelta(days=2), "text": "Started a challenge", "emoji": "🎯"},
        {"date": datetime.now() - timedelta(days=5), "text": "Earned Eco Learner badge", "emoji": "🌟"}
    ]
    
    for activity in activities:
        date_str = activity["date"].strftime("%B %d, %Y")
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 20px;'>{activity['emoji']}</span>
                <div>
                    <div style='font-size: 14px;'>{activity['text']}</div>
                    <div style='font-size: 12px; color: #6b7280;'>{date_str}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def render_dashboard(tracker):
    """Render education dashboard"""
    st.markdown("### 📊 Education Dashboard")
    
    # Learning stats
    stats = tracker.get_stats()
    
    # Module completion chart
    module_data = []
    for level in ["beginner", "intermediate", "advanced"]:
        modules = CurriculumDatabase.get_modules(level)
        completed = sum(1 for m in modules if m["id"] in tracker.data["completed_modules"])
        total = len(modules)
        module_data.append({
            "Level": level.title(),
            "Completed": completed,
            "Total": total
        })
    
    df_modules = pd.DataFrame(module_data)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_modules['Level'],
        y=df_modules['Completed'],
        name='Completed',
        marker_color='#4ade80'
    ))
    fig.add_trace(go.Bar(
        x=df_modules['Level'],
        y=df_modules['Total'],
        name='Total Available',
        marker_color='#6b7280',
        opacity=0.5
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        barmode='group',
        yaxis_title="Modules"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Points trend
    st.markdown("#### 📈 Points Progress")
    
    # Simulated points history
    points_history = []
    for i in range(10):
        points_history.append({
            "Day": i + 1,
            "Points": random.randint(0, 50) + (i * 3)
        })
    
    df_points = pd.DataFrame(points_history)
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_points['Day'],
        y=df_points['Points'],
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#4ade80', width=2)
    ))
    fig.update_layout(
        height=200,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_title="Points"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    
    completed = len(tracker.data["completed_modules"])
    
    if completed < 4:
        st.info("📚 Start with Beginner modules to build your foundation")
    elif completed < 8:
        st.info("🌟 You're ready for Intermediate modules - keep going!")
    else:
        st.info("🏆 You're making great progress! Try Advanced modules and challenges")
    
    # Share progress
    st.markdown("---")
    st.markdown("#### 📤 Share Your Progress")
    
    if st.button("📱 Share Your Eco-School Progress", use_container_width=True):
        st.success("📤 Share your achievements with friends and family!")

# ============================================================
# INTEGRATION
# ============================================================

def render_eco_school_hub():
    """Render the complete eco-school hub"""
    render_eco_school()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_school import render_eco_school_hub

# Add as a new tab
with tab32:
    render_eco_school_hub()
"""