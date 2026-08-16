
# ============================================================
# FILE: eco_gamification.py
# EcoBuddy AI+ Eco-Gamification & Rewards Engine
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# ACTION DATABASE
# ============================================================

class ActionDatabase:
    """Actions that earn points"""
    
    ACTIONS = [
        {"id": "a1", "name": "Complete Carbon Assessment", "points": 50, "category": "Assessment", "daily_limit": 1},
        {"id": "a2", "name": "Log Sustainable Habit", "points": 10, "category": "Habit", "daily_limit": 10},
        {"id": "a3", "name": "Complete Challenge", "points": 75, "category": "Challenge", "daily_limit": 3},
        {"id": "a4", "name": "Share Progress", "points": 15, "category": "Social", "daily_limit": 3},
        {"id": "a5", "name": "Join Community Event", "points": 30, "category": "Community", "daily_limit": 2},
        {"id": "a6", "name": "Volunteer Action", "points": 40, "category": "Volunteer", "daily_limit": 1},
        {"id": "a7", "name": "Daily Login", "points": 5, "category": "Engagement", "daily_limit": 1},
        {"id": "a8", "name": "Refer a Friend", "points": 100, "category": "Social", "daily_limit": 5},
        {"id": "a9", "name": "Complete Learning Module", "points": 25, "category": "Learning", "daily_limit": 5},
        {"id": "a10", "name": "Share Eco Story", "points": 20, "category": "Social", "daily_limit": 2},
        {"id": "a11", "name": "Plant a Tree", "points": 150, "category": "Environment", "daily_limit": 1},
        {"id": "a12", "name": "Reduce Waste by 50%", "points": 80, "category": "Waste", "daily_limit": 1},
        {"id": "a13", "name": "Energy Saving Challenge", "points": 60, "category": "Energy", "daily_limit": 1},
        {"id": "a14", "name": "Water Conservation Day", "points": 55, "category": "Water", "daily_limit": 1},
        {"id": "a15", "name": "Zero Plastic Day", "points": 70, "category": "Waste", "daily_limit": 1}
    ]
    
    @staticmethod
    def get_actions(category=None):
        """Get actions with filters"""
        actions = ActionDatabase.ACTIONS.copy()
        if category and category != "All":
            actions = [a for a in actions if a["category"] == category]
        return actions
    
    @staticmethod
    def get_categories():
        """Get action categories"""
        return ["All"] + sorted(set(a["category"] for a in ActionDatabase.ACTIONS))

# ============================================================
# ACHIEVEMENT DATABASE
# ============================================================

class AchievementDatabase:
    """Achievement badges and milestones"""
    
    BADGES = [
        {"id": "b1", "name": "🌟 First Steps", "description": "Complete your first action", "points": 25, "icon": "🌟", "required": 1},
        {"id": "b2", "name": "🔥 Rising Star", "description": "Earn 500 total points", "points": 50, "icon": "🔥", "required": 500},
        {"id": "b3", "name": "⚡ Eco Warrior", "description": "Earn 1000 total points", "points": 75, "icon": "⚡", "required": 1000},
        {"id": "b4", "name": "🏆 Eco Champion", "description": "Earn 5000 total points", "points": 150, "icon": "🏆", "required": 5000},
        {"id": "b5", "name": "🌍 Earth Guardian", "description": "Earn 10000 total points", "points": 250, "icon": "🌍", "required": 10000},
        {"id": "b6", "name": "🎯 7-Day Streak", "description": "Complete 7 consecutive days", "points": 50, "icon": "🎯", "required": 7},
        {"id": "b7", "name": "💪 30-Day Streak", "description": "Complete 30 consecutive days", "points": 100, "icon": "💪", "required": 30},
        {"id": "b8", "name": "🎯 100-Day Streak", "description": "Complete 100 consecutive days", "points": 200, "icon": "🏅", "required": 100},
        {"id": "b9", "name": "📚 Learning Master", "description": "Complete 10 learning modules", "points": 50, "icon": "📚", "required": 10},
        {"id": "b10", "name": "🌿 Green Thumb", "description": "Log 50 sustainable habits", "points": 50, "icon": "🌿", "required": 50},
        {"id": "b11", "name": "♻️ Zero Waste Hero", "description": "Reduce waste by 75%", "points": 75, "icon": "♻️", "required": 1},
        {"id": "b12", "name": "🚲 Green Commuter", "description": "Log 30 sustainable commutes", "points": 60, "icon": "🚲", "required": 30},
        {"id": "b13", "name": "🌟 Community Leader", "description": "Refer 5 friends", "points": 100, "icon": "🌟", "required": 5},
        {"id": "b14", "name": "🌎 Global Impact", "description": "Complete 50 actions", "points": 100, "icon": "🌎", "required": 50},
        {"id": "b15", "name": "🏅 Eco Legend", "description": "Unlock all badges", "points": 500, "icon": "🏅", "required": 15}
    ]
    
    @staticmethod
    def get_badges():
        """Get all badges"""
        return AchievementDatabase.BADGES

# ============================================================
# REWARD MARKETPLACE
# ============================================================

class RewardMarketplace:
    """Rewards redeemable with points"""
    
    REWARDS = [
        {
            "id": "r1",
            "name": "🌳 Plant a Tree",
            "description": "We'll plant a tree in your honor",
            "points": 500,
            "category": "Environmental",
            "available": True
        },
        {
            "id": "r2",
            "name": "🌱 Eco Mug",
            "description": "Reusable bamboo coffee mug",
            "points": 800,
            "category": "Product",
            "available": True
        },
        {
            "id": "r3",
            "name": "📚 Sustainability E-Book",
            "description": "Digital guide to sustainable living",
            "points": 300,
            "category": "Digital",
            "available": True
        },
        {
            "id": "r4",
            "name": "♻️ Reusable Bag Set",
            "description": "Set of 5 eco-friendly shopping bags",
            "points": 600,
            "category": "Product",
            "available": True
        },
        {
            "id": "r5",
            "name": "💡 LED Light Pack",
            "description": "5 energy-efficient LED bulbs",
            "points": 700,
            "category": "Product",
            "available": True
        },
        {
            "id": "r6",
            "name": "🎯 1-on-1 Sustainability Coach",
            "description": "30-minute coaching session",
            "points": 1000,
            "category": "Service",
            "available": True
        },
        {
            "id": "r7",
            "name": "🌿 Plant Care Guide",
            "description": "Digital guide to indoor plants",
            "points": 200,
            "category": "Digital",
            "available": True
        },
        {
            "id": "r8",
            "name": "💚 Donate to Cause",
            "description": "Donate $10 to an environmental cause",
            "points": 1500,
            "category": "Environmental",
            "available": True
        }
    ]
    
    @staticmethod
    def get_rewards(category=None):
        """Get rewards with filters"""
        rewards = RewardMarketplace.REWARDS.copy()
        if category and category != "All":
            rewards = [r for r in rewards if r["category"] == category]
        return rewards
    
    @staticmethod
    def get_categories():
        """Get reward categories"""
        return ["All"] + sorted(set(r["category"] for r in RewardMarketplace.REWARDS))

# ============================================================
# GAMIFICATION ENGINE
# ============================================================

class GamificationEngine:
    """Core gamification engine"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load gamification data from session"""
        if "gamification_data" not in st.session_state:
            st.session_state.gamification_data = {}
        return st.session_state.gamification_data.get(self.user_id, {
            "points": 0,
            "actions": [],
            "badges": [],
            "streak": 0,
            "last_action": None,
            "rewards_claimed": [],
            "level": 1
        })
    
    def save(self):
        """Save gamification data"""
        st.session_state.gamification_data[self.user_id] = self.data
    
    def earn_points(self, action_id):
        """Earn points for an action"""
        action = next((a for a in ActionDatabase.ACTIONS if a["id"] == action_id), None)
        if not action:
            return False, "Action not found"
        
        # Check daily limit
        today = datetime.now().date().isoformat()
        today_actions = [a for a in self.data["actions"] if a.startswith(f"{today}_{action_id}")]
        if len(today_actions) >= action["daily_limit"]:
            return False, f"Daily limit reached for {action['name']}"
        
        # Add points
        points_earned = action["points"]
        self.data["points"] += points_earned
        self.data["actions"].append(f"{today}_{action_id}")
        
        # Update streak
        self._update_streak()
        
        # Check for level up
        self._check_level_up()
        
        self.save()
        return True, f"Earned {points_earned} points for {action['name']}!"
    
    def _update_streak(self):
        """Update user streak"""
        today = datetime.now().date()
        last = self.data["last_action"]
        
        if last:
            last_date = datetime.fromisoformat(last).date()
            diff = (today - last_date).days
            
            if diff == 1:
                self.data["streak"] += 1
            elif diff > 1:
                self.data["streak"] = 0
        else:
            self.data["streak"] = 1
        
        self.data["last_action"] = today.isoformat()
    
    def _check_level_up(self):
        """Check if user should level up"""
        points = self.data["points"]
        new_level = math.floor(math.sqrt(points / 100)) + 1
        
        if new_level > self.data["level"]:
            self.data["level"] = new_level
    
    def check_achievements(self):
        """Check and unlock achievements"""
        unlocked = []
        
        for badge in AchievementDatabase.get_badges():
            if badge["id"] in self.data["badges"]:
                continue
            
            # Check requirements
            if self._check_badge_requirement(badge):
                self.data["badges"].append(badge["id"])
                self.data["points"] += badge["points"]
                unlocked.append(badge)
                self.save()
        
        return unlocked
    
    def _check_badge_requirement(self, badge):
        """Check if badge requirements are met"""
        # Different requirement types
        if "required" in badge:
            if "points" in str(badge["required"]):
                return self.data["points"] >= badge["required"]
            elif "streak" in str(badge["required"]):
                return self.data["streak"] >= badge["required"]
            elif "actions" in str(badge["required"]):
                return len(self.data["actions"]) >= badge["required"]
            elif "badges" in str(badge["required"]):
                return len(self.data["badges"]) >= badge["required"]
        
        return False
    
    def get_stats(self):
        """Get gamification statistics"""
        return {
            "points": self.data["points"],
            "level": self.data["level"],
            "streak": self.data["streak"],
            "actions_count": len(self.data["actions"]),
            "badges_count": len(self.data["badges"]),
            "rewards_claimed": len(self.data["rewards_claimed"])
        }
    
    def redeem_reward(self, reward_id):
        """Redeem a reward"""
        reward = next((r for r in RewardMarketplace.REWARDS if r["id"] == reward_id), None)
        if not reward:
            return False, "Reward not found"
        
        if reward["id"] in self.data["rewards_claimed"]:
            return False, "Reward already claimed"
        
        if self.data["points"] < reward["points"]:
            return False, f"Not enough points. Need {reward['points']} points"
        
        self.data["points"] -= reward["points"]
        self.data["rewards_claimed"].append(reward["id"])
        self.save()
        return True, f"Redeemed {reward['name']}!"

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_gamification():
    """Render the complete gamification system"""
    st.markdown("<div class='section-header'>🎮 Eco-Gamification & Rewards</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize gamification engine
    if "gamification_engine" not in st.session_state:
        st.session_state.gamification_engine = GamificationEngine(user_id)
    
    engine = st.session_state.gamification_engine
    
    # Check for new achievements
    new_badges = engine.check_achievements()
    if new_badges:
        for badge in new_badges:
            st.success(f"🎉 Achievement Unlocked: {badge['icon']} {badge['name']}!")
            st.balloons()
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Dashboard",
        "🎯 Actions",
        "🏅 Achievements",
        "🎁 Rewards"
    ])
    
    with tab1:
        render_gamification_dashboard(engine)
    
    with tab2:
        render_actions(engine)
    
    with tab3:
        render_achievements(engine)
    
    with tab4:
        render_rewards(engine)

def render_gamification_dashboard(engine):
    """Render gamification dashboard"""
    st.markdown("### 📊 Your Eco-Gamification Dashboard")
    
    stats = engine.get_stats()
    
    # Level display
    st.markdown(f"""
    <div class='card-highlight' style='text-align: center;'>
        <div style='font-size: 48px;'>🎮</div>
        <h1 style='color: #4ade80;'>Level {stats['level']}</h1>
        <p style='color: #6b7280;'>Eco Warrior</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("⭐ Points", stats["points"])
    col2.metric("🔥 Streak", f"{stats['streak']} days")
    col3.metric("🎯 Actions", stats["actions_count"])
    col4.metric("🏅 Badges", stats["badges_count"])
    
    # Points progress to next level
    current_level_points = 100 * ((stats["level"] - 1) ** 2)
    next_level_points = 100 * (stats["level"] ** 2)
    progress = (stats["points"] - current_level_points) / (next_level_points - current_level_points) * 100 if next_level_points > current_level_points else 0
    
    st.markdown("#### 📈 Progress to Next Level")
    st.progress(min(progress / 100, 1.0))
    st.caption(f"{stats['points']} / {next_level_points} points")
    
    # Recent activity
    st.markdown("#### 📋 Recent Activity")
    
    if engine.data["actions"]:
        recent = engine.data["actions"][-5:]
        for action in recent[::-1]:
            date_part, action_id = action.split("_")
            action_name = next((a["name"] for a in ActionDatabase.ACTIONS if a["id"] == action_id), "Unknown")
            date = datetime.fromisoformat(date_part).strftime("%b %d, %Y")
            st.markdown(f"• {date}: Completed **{action_name}**")
    else:
        st.info("Complete actions to start your journey!")

def render_actions(engine):
    """Render actions"""
    st.markdown("### 🎯 Earn Points")
    
    st.markdown("""
    <div class='subtitle'>
        Complete actions to earn points and level up!
    </div>
    """, unsafe_allow_html=True)
    
    # Category filter
    categories = ActionDatabase.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get actions
    actions = ActionDatabase.get_actions(selected_category)
    
    # Display actions
    for action in actions:
        today = datetime.now().date().isoformat()
        today_actions = [a for a in engine.data["actions"] if a.startswith(f"{today}_{action['id']}")]
        remaining = action["daily_limit"] - len(today_actions)
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{action['name']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        {action['category']} • +{action['points']} points • {action['daily_limit']}/day
                    </div>
                </div>
                <div style='text-align: right;'>
                    <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;'>
                        {remaining} remaining
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if remaining > 0:
            if st.button(f"✅ Complete {action['name']}", key=f"action_{action['id']}"):
                success, message = engine.earn_points(action["id"])
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.warning(message)
        
        st.markdown("---")

def render_achievements(engine):
    """Render achievements"""
    st.markdown("### 🏅 Achievements")
    
    stats = engine.get_stats()
    total_badges = len(AchievementDatabase.get_badges())
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Badges Earned", f"{stats['badges_count']}/{total_badges}")
    col2.metric("Progress", f"{(stats['badges_count']/total_badges*100):.0f}%")
    col3.metric("Points from Badges", sum(
        b["points"] for b in AchievementDatabase.get_badges() 
        if b["id"] in engine.data["badges"]
    ))
    
    st.progress(stats['badges_count'] / total_badges)
    
    st.markdown("---")
    
    # Display badges
    badges = AchievementDatabase.get_badges()
    cols = st.columns(3)
    
    for i, badge in enumerate(badges):
        unlocked = badge["id"] in engine.data["badges"]
        
        with cols[i % 3]:
            if unlocked:
                st.markdown(f"""
                <div style='background: #1f2937; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #4ade80;'>
                    <div style='font-size: 40px;'>{badge['icon']}</div>
                    <div style='font-weight: 700; color: #4ade80;'>{badge['name']}</div>
                    <div style='font-size: 11px; color: #6b7280;'>{badge['description']}</div>
                    <div style='font-size: 11px; color: #4ade80;'>✅ Unlocked</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: #1f2937; padding: 15px; border-radius: 10px; text-align: center; border: 2px solid #374151;'>
                    <div style='font-size: 40px;'>🔒</div>
                    <div style='font-weight: 700; color: #6b7280;'>{badge['name']}</div>
                    <div style='font-size: 11px; color: #6b7280;'>{badge['description']}</div>
                    <div style='font-size: 11px; color: #fbbf24;'>+{badge['points']} pts</div>
                </div>
                """, unsafe_allow_html=True)

def render_rewards(engine):
    """Render rewards marketplace"""
    st.markdown("### 🎁 Reward Marketplace")
    
    stats = engine.get_stats()
    
    col1, col2 = st.columns(2)
    col1.metric("Available Points", stats["points"])
    col2.metric("Rewards Claimed", stats["rewards_claimed"])
    
    st.markdown("---")
    
    # Category filter
    categories = RewardMarketplace.get_categories()
    selected_category = st.selectbox("Filter Rewards", categories)
    
    # Get rewards
    rewards = RewardMarketplace.get_rewards(selected_category)
    
    # Display rewards
    for reward in rewards:
        claimed = reward["id"] in engine.data["rewards_claimed"]
        can_afford = stats["points"] >= reward["points"]
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {"#4ade80" if can_afford else "#6b7280"};'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{reward['name']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>{reward['description']}</div>
                    <div style='display: flex; gap: 15px; font-size: 12px;'>
                        <span>📂 {reward['category']}</span>
                        <span>⭐ {reward['points']} points</span>
                    </div>
                </div>
                <div style='text-align: right;'>
                    {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;">✅ Claimed</span>' if claimed else 
                     f'<span style="background: {"#4ade80" if can_afford else "#6b7280"}; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;">{"Available" if can_afford else "Need more points"}</span>'}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not claimed and can_afford:
            if st.button(f"🎁 Redeem {reward['name']}", key=f"redeem_{reward['id']}"):
                success, message = engine.redeem_reward(reward["id"])
                if success:
                    st.success(message)
                    st.balloons()
                    st.rerun()
                else:
                    st.warning(message)
        
        st.markdown("---")

# ============================================================
# INTEGRATION
# ============================================================

def render_gamification_hub():
    """Render the complete gamification hub"""
    render_eco_gamification()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_gamification import render_gamification_hub

# Add as a new tab
with tab37:
    render_gamification_hub()
"""