
# ============================================================
# FILE: certification_system.py
# EcoBuddy AI+ Eco-Certification & Achievement System
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math
import hashlib

# ============================================================
# ACHIEVEMENT DATABASE
# ============================================================

class AchievementDatabase:
    """Database of eco-achievements and badges"""
    
    ACHIEVEMENTS = [
        {
            "id": "a1",
            "name": "🌱 First Steps",
            "description": "Complete your first carbon footprint assessment",
            "category": "Assessment",
            "points": 50,
            "unlock_condition": "complete_assessment",
            "unlock_value": 1,
            "emoji": "🌱",
            "color": "#4ade80"
        },
        {
            "id": "a2",
            "name": "⭐ Eco Explorer",
            "description": "Complete 5 carbon footprint assessments",
            "category": "Assessment",
            "points": 100,
            "unlock_condition": "complete_assessment",
            "unlock_value": 5,
            "emoji": "⭐",
            "color": "#fbbf24"
        },
        {
            "id": "a3",
            "name": "🏆 Sustainability Champion",
            "description": "Complete 10 carbon footprint assessments",
            "category": "Assessment",
            "points": 200,
            "unlock_condition": "complete_assessment",
            "unlock_value": 10,
            "emoji": "🏆",
            "color": "#f87171"
        },
        {
            "id": "a4",
            "name": "🌿 Green Guardian",
            "description": "Achieve an Eco Score of 80 or higher",
            "category": "Score",
            "points": 150,
            "unlock_condition": "eco_score",
            "unlock_value": 80,
            "emoji": "🌿",
            "color": "#4ade80"
        },
        {
            "id": "a5",
            "name": "🌟 Eco Master",
            "description": "Achieve an Eco Score of 90 or higher",
            "category": "Score",
            "points": 250,
            "unlock_condition": "eco_score",
            "unlock_value": 90,
            "emoji": "🌟",
            "color": "#fbbf24"
        },
        {
            "id": "a6",
            "name": "🔥 Streak Warrior",
            "description": "Maintain a 7-day sustainability streak",
            "category": "Streak",
            "points": 75,
            "unlock_condition": "streak",
            "unlock_value": 7,
            "emoji": "🔥",
            "color": "#f87171"
        },
        {
            "id": "a7",
            "name": "💪 Streak Master",
            "description": "Maintain a 30-day sustainability streak",
            "category": "Streak",
            "points": 200,
            "unlock_condition": "streak",
            "unlock_value": 30,
            "emoji": "💪",
            "color": "#fbbf24"
        },
        {
            "id": "a8",
            "name": "🚲 Green Commuter",
            "description": "Choose sustainable transport for 10 assessments",
            "category": "Transport",
            "points": 100,
            "unlock_condition": "sustainable_transport",
            "unlock_value": 10,
            "emoji": "🚲",
            "color": "#60a5fa"
        },
        {
            "id": "a9",
            "name": "🥗 Plant-Powered",
            "description": "Choose vegetarian diet for 5 assessments",
            "category": "Diet",
            "points": 75,
            "unlock_condition": "vegetarian",
            "unlock_value": 5,
            "emoji": "🥗",
            "color": "#a78bfa"
        },
        {
            "id": "a10",
            "name": "🌍 Global Citizen",
            "description": "Reduce carbon footprint by 20%",
            "category": "Reduction",
            "points": 150,
            "unlock_condition": "reduction",
            "unlock_value": 20,
            "emoji": "🌍",
            "color": "#34d399"
        },
        {
            "id": "a11",
            "name": "💧 Water Saver",
            "description": "Reduce electricity usage by 20%",
            "category": "Energy",
            "points": 100,
            "unlock_condition": "energy_reduction",
            "unlock_value": 20,
            "emoji": "💧",
            "color": "#60a5fa"
        },
        {
            "id": "a12",
            "name": "♻️ Zero Waste Hero",
            "description": "Complete 3 waste reduction actions",
            "category": "Waste",
            "points": 75,
            "unlock_condition": "waste_actions",
            "unlock_value": 3,
            "emoji": "♻️",
            "color": "#4ade80"
        }
    ]
    
    @staticmethod
    def get_achievements(category=None):
        """Get achievements with filters"""
        achievements = AchievementDatabase.ACHIEVEMENTS.copy()
        if category and category != "All":
            achievements = [a for a in achievements if a["category"] == category]
        return achievements
    
    @staticmethod
    def get_categories():
        """Get achievement categories"""
        return ["All"] + sorted(set(a["category"] for a in AchievementDatabase.ACHIEVEMENTS))
    
    @staticmethod
    def get_achievement_by_id(achievement_id):
        """Get achievement by ID"""
        for achievement in AchievementDatabase.ACHIEVEMENTS:
            if achievement["id"] == achievement_id:
                return achievement
        return None

# ============================================================
# CERTIFICATION LEVELS
# ============================================================

class CertificationLevels:
    """Sustainability certification levels"""
    
    LEVELS = [
        {
            "id": "l1",
            "name": "Eco Beginner",
            "level": 1,
            "required_points": 0,
            "required_achievements": 0,
            "description": "Start your sustainability journey",
            "emoji": "🌱",
            "color": "#4ade80",
            "benefits": ["Access to basic features", "Progress tracking"]
        },
        {
            "id": "l2",
            "name": "Green Learner",
            "level": 2,
            "required_points": 150,
            "required_achievements": 3,
            "description": "Building sustainable habits",
            "emoji": "📚",
            "color": "#60a5fa",
            "benefits": ["Access to advanced analytics", "Personalized tips"]
        },
        {
            "id": "l3",
            "name": "Sustainability Star",
            "level": 3,
            "required_points": 400,
            "required_achievements": 6,
            "description": "Demonstrated commitment to sustainability",
            "emoji": "⭐",
            "color": "#fbbf24",
            "benefits": ["Early access to features", "Community leader status"]
        },
        {
            "id": "l4",
            "name": "Eco Champion",
            "level": 4,
            "required_points": 700,
            "required_achievements": 9,
            "description": "Exceptional sustainability leadership",
            "emoji": "🏆",
            "color": "#f87171",
            "benefits": ["Mentorship opportunities", "Featured in community"]
        },
        {
            "id": "l5",
            "name": "Green Guardian",
            "level": 5,
            "required_points": 1000,
            "required_achievements": 12,
            "description": "Master of sustainable living",
            "emoji": "🌍",
            "color": "#a855f7",
            "benefits": ["Certification badge", "Exclusive events", "Leadership role"]
        }
    ]
    
    @staticmethod
    def get_level(level_id):
        """Get certification level by ID"""
        for level in CertificationLevels.LEVELS:
            if level["id"] == level_id:
                return level
        return None
    
    @staticmethod
    def get_level_by_points(points):
        """Get level based on points"""
        current_level = CertificationLevels.LEVELS[0]
        for level in CertificationLevels.LEVELS:
            if points >= level["required_points"]:
                current_level = level
        return current_level

# ============================================================
# USER CERTIFICATION TRACKER
# ============================================================

class CertificationTracker:
    """Track user certifications and achievements"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load certification data from session"""
        if "certification_data" not in st.session_state:
            st.session_state.certification_data = {}
        return st.session_state.certification_data.get(self.user_id, {
            "achievements": [],
            "points": 0,
            "certifications": [],
            "activity_log": []
        })
    
    def save(self):
        """Save certification data"""
        st.session_state.certification_data[self.user_id] = self.data
    
    def unlock_achievement(self, achievement_id):
        """Unlock an achievement"""
        if achievement_id not in self.data["achievements"]:
            achievement = AchievementDatabase.get_achievement_by_id(achievement_id)
            if achievement:
                self.data["achievements"].append(achievement_id)
                self.data["points"] += achievement["points"]
                self.data["activity_log"].append({
                    "type": "achievement",
                    "achievement_id": achievement_id,
                    "timestamp": datetime.now().isoformat()
                })
                self.save()
                return True
        return False
    
    def check_achievements(self, user_stats):
        """Check and unlock achievements based on user stats"""
        unlocked = []
        
        for achievement in AchievementDatabase.ACHIEVEMENTS:
            if achievement["id"] in self.data["achievements"]:
                continue
            
            condition = achievement["unlock_condition"]
            value = achievement["unlock_value"]
            
            if condition == "complete_assessment":
                if user_stats.get("assessments_completed", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "eco_score":
                if user_stats.get("latest_eco_score", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "streak":
                if user_stats.get("current_streak", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "sustainable_transport":
                if user_stats.get("sustainable_transport_count", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "vegetarian":
                if user_stats.get("vegetarian_count", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "reduction":
                if user_stats.get("footprint_reduction_percent", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "energy_reduction":
                if user_stats.get("energy_reduction_percent", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
            
            elif condition == "waste_actions":
                if user_stats.get("waste_actions_count", 0) >= value:
                    if self.unlock_achievement(achievement["id"]):
                        unlocked.append(achievement["id"])
        
        return unlocked
    
    def get_certification_level(self):
        """Get current certification level"""
        points = self.data["points"]
        achievements_count = len(self.data["achievements"])
        
        for level in CertificationLevels.LEVELS:
            if points >= level["required_points"] and achievements_count >= level["required_achievements"]:
                return level
        
        return CertificationLevels.LEVELS[0]
    
    def get_stats(self):
        """Get certification statistics"""
        return {
            "total_achievements": len(AchievementDatabase.ACHIEVEMENTS),
            "unlocked_achievements": len(self.data["achievements"]),
            "total_points": self.data["points"],
            "certification_level": self.get_certification_level(),
            "achievement_ids": self.data["achievements"]
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_certification_system():
    """Render the complete certification system"""
    st.markdown("<div class='section-header'>🏅 Eco-Certification & Achievement System</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize tracker
    if "certification_tracker" not in st.session_state:
        st.session_state.certification_tracker = CertificationTracker(user_id)
    
    tracker = st.session_state.certification_tracker
    
    # Check for new achievements
    user_stats = _get_user_stats()
    new_achievements = tracker.check_achievements(user_stats)
    
    if new_achievements:
        for achievement_id in new_achievements:
            achievement = AchievementDatabase.get_achievement_by_id(achievement_id)
            if achievement:
                st.success(f"🎉 Achievement Unlocked: {achievement['name']}!")
                st.balloons()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏅 Achievements",
        "📜 Certifications",
        "📊 Progress",
        "🎯 Goals"
    ])
    
    with tab1:
        render_achievements(tracker)
    
    with tab2:
        render_certifications(tracker)
    
    with tab3:
        render_progress(tracker)
    
    with tab4:
        render_goals(tracker)

def _get_user_stats():
    """Get user statistics for achievement checking"""
    # This would normally pull from database
    # For demo, create simulated stats
    history = st.session_state.get("assessment_history", [])
    
    stats = {
        "assessments_completed": len(history),
        "latest_eco_score": st.session_state.get("eco_score", 50),
        "current_streak": st.session_state.get("streak", 3),
        "sustainable_transport_count": random.randint(0, 15),
        "vegetarian_count": random.randint(0, 10),
        "footprint_reduction_percent": random.randint(0, 30),
        "energy_reduction_percent": random.randint(0, 25),
        "waste_actions_count": random.randint(0, 5)
    }
    
    return stats

def render_achievements(tracker):
    """Render achievements section"""
    st.markdown("### 🏅 Your Achievements")
    
    stats = tracker.get_stats()
    
    # Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Unlocked", f"{stats['unlocked_achievements']}/{stats['total_achievements']}")
    col2.metric("Total Points", stats['total_points'])
    col3.metric("Completion", f"{(stats['unlocked_achievements']/stats['total_achievements']*100):.0f}%")
    
    st.progress(stats['unlocked_achievements'] / stats['total_achievements'])
    
    st.markdown("---")
    
    # Display achievements by category
    categories = AchievementDatabase.get_categories()
    
    for category in categories:
        if category == "All":
            continue
        
        st.markdown(f"#### {category}")
        
        achievements = AchievementDatabase.get_achievements(category)
        unlocked_ids = tracker.data["achievements"]
        
        cols = st.columns(3)
        for i, achievement in enumerate(achievements):
            is_unlocked = achievement["id"] in unlocked_ids
            
            with cols[i % 3]:
                if is_unlocked:
                    st.markdown(f"""
                    <div style='background: #1f2937; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid {achievement["color"]};'>
                        <div style='font-size: 32px;'>{achievement["emoji"]}</div>
                        <div style='font-weight: 700; font-size: 14px; color: #4ade80;'>{achievement["name"]}</div>
                        <div style='font-size: 11px; color: #6b7280;'>{achievement["description"]}</div>
                        <div style='font-size: 11px; color: #4ade80;'>+{achievement["points"]} pts</div>
                        <div style='font-size: 11px; color: #4ade80;'>✅ Unlocked</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style='background: #1f2937; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #374151;'>
                        <div style='font-size: 32px;'>🔒</div>
                        <div style='font-weight: 700; font-size: 14px; color: #6b7280;'>{achievement["name"]}</div>
                        <div style='font-size: 11px; color: #6b7280;'>{achievement["description"]}</div>
                        <div style='font-size: 11px; color: #fbbf24;'>Requires: {achievement["unlock_condition"]} = {achievement["unlock_value"]}</div>
                    </div>
                    """, unsafe_allow_html=True)

def render_certifications(tracker):
    """Render certifications section"""
    st.markdown("### 📜 Eco-Certifications")
    
    current_level = tracker.get_certification_level()
    stats = tracker.get_stats()
    
    # Current certification
    st.markdown("#### Your Current Certification")
    
    st.markdown(f"""
    <div class='card-highlight' style='text-align: center; padding: 30px;'>
        <div style='font-size: 64px;'>{current_level['emoji']}</div>
        <h2 style='color: #4ade80;'>{current_level['name']}</h2>
        <p style='color: #6b7280;'>{current_level['description']}</p>
        <div style='display: flex; justify-content: center; gap: 30px; margin-top: 10px;'>
            <div>
                <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{stats['total_points']}</div>
                <div style='font-size: 12px; color: #6b7280;'>Total Points</div>
            </div>
            <div>
                <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{stats['unlocked_achievements']}</div>
                <div style='font-size: 12px; color: #6b7280;'>Achievements</div>
            </div>
            <div>
                <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>Level {current_level['level']}</div>
                <div style='font-size: 12px; color: #6b7280;'>Certification</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # All certification levels
    st.markdown("#### 📈 Certification Path")
    
    for level in CertificationLevels.LEVELS:
        is_reached = level["level"] <= current_level["level"]
        status = "✅" if is_reached else "⏳"
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {level["color"] if is_reached else "#374151"};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 24px;'>{level["emoji"]}</span>
                        <div>
                            <div style='font-weight: 700;'>{level["name"]}</div>
                            <div style='font-size: 13px; color: #6b7280;'>{level["description"]}</div>
                        </div>
                    </div>
                    <div style='font-size: 12px; color: #6b7280; margin-top: 4px;'>
                        Requires: {level["required_points"]} pts • {level["required_achievements"]} achievements
                    </div>
                </div>
                <div style='font-size: 24px;'>{status}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Certification benefits
    st.markdown("#### 🎁 Certification Benefits")
    
    for level in CertificationLevels.LEVELS:
        with st.expander(f"Level {level['level']}: {level['name']} Benefits"):
            for benefit in level["benefits"]:
                st.markdown(f"• {benefit}")

def render_progress(tracker):
    """Render progress section"""
    st.markdown("### 📊 Your Progress")
    
    stats = tracker.get_stats()
    user_stats = _get_user_stats()
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Assessments", user_stats.get("assessments_completed", 0))
    col2.metric("Eco Score", f"{user_stats.get('latest_eco_score', 0)}/100")
    col3.metric("Current Streak", f"{user_stats.get('current_streak', 0)} days")
    col4.metric("Achievements", f"{stats['unlocked_achievements']}/{stats['total_achievements']}")
    
    # Progress to next level
    st.markdown("#### 🎯 Next Certification Level")
    
    current_level = tracker.get_certification_level()
    next_level = None
    
    for level in CertificationLevels.LEVELS:
        if level["level"] > current_level["level"]:
            next_level = level
            break
    
    if next_level:
        points_needed = max(0, next_level["required_points"] - stats["total_points"])
        achievements_needed = max(0, next_level["required_achievements"] - stats["unlocked_achievements"])
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: center; gap: 15px;'>
                <div style='font-size: 40px;'>{next_level['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='font-weight: 700; color: #4ade80;'>Next: {next_level['name']}</div>
                    <div style='color: #6b7280; font-size: 14px;'>{next_level['description']}</div>
                    <div style='display: flex; gap: 20px; margin-top: 6px; font-size: 13px;'>
                        <span>📌 {points_needed} points needed</span>
                        <span>🏅 {achievements_needed} achievements needed</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Progress to next level
        if next_level["required_points"] > 0:
            progress = min(stats["total_points"] / next_level["required_points"] * 100, 100)
            st.progress(progress / 100)
            st.caption(f"{progress:.0f}% complete")
    else:
        st.success("🌟 You've reached the highest certification level! Outstanding achievement!")
    
    # Achievement timeline
    st.markdown("#### 📅 Achievement Timeline")
    
    if tracker.data.get("activity_log"):
        recent_activities = tracker.data["activity_log"][-5:]
        
        for activity in recent_activities:
            if activity["type"] == "achievement":
                achievement = AchievementDatabase.get_achievement_by_id(activity["achievement_id"])
                if achievement:
                    date = datetime.fromisoformat(activity["timestamp"]).strftime("%b %d, %Y")
                    st.markdown(f"• {achievement['emoji']} **{achievement['name']}** - {date}")
    else:
        st.info("No achievements unlocked yet. Start your journey today!")

def render_goals(tracker):
    """Render goals section"""
    st.markdown("### 🎯 Your Goals")
    
    stats = tracker.get_stats()
    
    # Suggested goals
    st.markdown("#### 💡 Suggested Goals")
    
    goals = [
        {"name": "Complete 5 assessments", "progress": min(100, _get_user_stats().get("assessments_completed", 0) * 20), "emoji": "📝"},
        {"name": "Reach Eco Score 80", "progress": min(100, (_get_user_stats().get("latest_eco_score", 0) / 80) * 100), "emoji": "⭐"},
        {"name": "7-Day Streak", "progress": min(100, (_get_user_stats().get("current_streak", 0) / 7) * 100), "emoji": "🔥"},
        {"name": "Unlock 5 Achievements", "progress": min(100, (stats["unlocked_achievements"] / 5) * 100), "emoji": "🏅"}
    ]
    
    for goal in goals:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 20px;'>{goal['emoji']}</span>
                    <span style='font-weight: 600;'>{goal['name']}</span>
                </div>
                <span style='font-size: 14px; font-weight: 700; color: #4ade80;'>{min(100, int(goal['progress']))}%</span>
            </div>
            <div style='margin-top: 8px;'>
                <div class='progress-bar' style='height: 6px;'>
                    <div class='progress-fill' style='width: {min(100, goal['progress'])}%;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Custom goal
    st.markdown("#### ✏️ Custom Goal")
    
    with st.form("custom_goal_form"):
        custom_goal = st.text_input("Set a personal sustainability goal")
        target_date = st.date_input("Target Date", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("Set Goal"):
            if custom_goal:
                if "custom_goals" not in st.session_state:
                    st.session_state.custom_goals = []
                
                st.session_state.custom_goals.append({
                    "goal": custom_goal,
                    "target_date": target_date.isoformat(),
                    "created_at": datetime.now().isoformat(),
                    "status": "active"
                })
                
                st.success("✅ Goal set successfully!")
                st.rerun()
    
    # Display custom goals
    if "custom_goals" in st.session_state and st.session_state.custom_goals:
        st.markdown("#### 📋 Your Goals")
        
        for i, goal in enumerate(st.session_state.custom_goals):
            target_date = datetime.fromisoformat(goal["target_date"]).strftime("%b %d, %Y")
            created_date = datetime.fromisoformat(goal["created_at"]).strftime("%b %d, %Y")
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{goal['goal']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>Target: {target_date} • Created: {created_date}</div>
                    </div>
                    <div>
                        <span style='background: #fbbf24; padding: 2px 12px; border-radius: 12px; font-size: 12px; color: #111827;'>
                            {goal['status']}
                        </span>
                        <button onclick="st.session_state.custom_goals.pop({i})" style='background: none; border: none; color: #f87171; cursor: pointer;'>
                            ❌
                        </button>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_certification_hub():
    """Render the complete certification hub"""
    render_certification_system()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from certification_system import render_certification_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22, tab23, tab24 = st.tabs([
    "🌍 Carbon Footprint",
    "⚡ Home Energy Audit",
    "🎮 Gamification",
    "🗺️ Route Planning & Offsets",
    "🏆 Community Leaderboard",
    "🔮 Future Self",
    "🌿 Sustainability Hub",
    "🌍 Eco-Social",
    "📖 Eco-Stories",
    "♻️ Waste Manager",
    "💰 Eco-Finance",
    "🎤 Voice Assessment",
    "🌤️ Eco-Weather",
    "🌍 Eco-Travel",
    "🌱 Eco-Garden",
    "📚 Learning Center",
    "🧘 Eco-Wellness",
    "🏠 Eco-Home",
    "🐾 Pet Care",
    "📊 Community Analytics",
    "📰 Eco-News",
    "🤝 Volunteer",
    "👗 Fashion",
    "🏅 Certification"  # NEW
])

with tab24:
    render_certification_hub()
"""