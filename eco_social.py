# ============================================================
# FILE: eco_social.py
# EcoBuddy AI+ Social Community Features
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import hashlib
from typing import Any

# ============================================================
# CHALLENGE SYSTEM
# ============================================================

class EcoChallenges:
    """Daily and weekly eco-challenges for users"""
    
    DAILY_CHALLENGES = [
        {
            "id": "d1",
            "title": "Meat-Free Monday",
            "description": "Go completely meat-free for one day",
            "category": "Diet",
            "xp_reward": 50,
            "difficulty": "Easy"
        },
        {
            "id": "d2",
            "title": "Walk 10,000 Steps",
            "description": "Walk 10,000 steps instead of driving",
            "category": "Transportation",
            "xp_reward": 75,
            "difficulty": "Medium"
        },
        {
            "id": "d3",
            "title": "Power Down Hour",
            "description": "Turn off all non-essential electronics for 1 hour",
            "category": "Energy",
            "xp_reward": 40,
            "difficulty": "Easy"
        },
        {
            "id": "d4",
            "title": "Recycle Everything",
            "description": "Ensure all recyclable waste is properly sorted",
            "category": "Waste",
            "xp_reward": 30,
            "difficulty": "Easy"
        },
        {
            "id": "d5",
            "title": "Local Food Day",
            "description": "Eat only locally sourced food today",
            "category": "Diet",
            "xp_reward": 60,
            "difficulty": "Medium"
        }
    ]
    
    WEEKLY_CHALLENGES = [
        {
            "id": "w1",
            "title": "Zero Waste Week",
            "description": "Produce less than 1kg of non-recyclable waste",
            "category": "Waste",
            "xp_reward": 200,
            "difficulty": "Hard"
        },
        {
            "id": "w2",
            "title": "Public Transport Week",
            "description": "Use public transport for all trips over 3km",
            "category": "Transportation",
            "xp_reward": 150,
            "difficulty": "Medium"
        },
        {
            "id": "w3",
            "title": "Energy Audit Week",
            "description": "Reduce electricity usage by 15% compared to last week",
            "category": "Energy",
            "xp_reward": 180,
            "difficulty": "Hard"
        }
    ]
    
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.completed = self._load_completed()
    
    def _load_completed(self) -> list[str]:
        """Load completed challenges from session"""
        if "completed_challenges" not in st.session_state:
            st.session_state.completed_challenges = {}
        return st.session_state.completed_challenges.get(self.user_id, [])
    
    def save(self) -> None:
        """Save completed challenges"""
        st.session_state.completed_challenges[self.user_id] = self.completed
    
    def get_daily(self) -> list[dict[str, Any]]:
        """Get today's daily challenges"""
        today = datetime.now().date()
        return [c for c in self.DAILY_CHALLENGES if f"{c['id']}_{today}" not in self.completed]
    
    def get_weekly(self) -> list[dict[str, Any]]:
        """Get this week's weekly challenges"""
        week = datetime.now().isocalendar()[1]
        return [c for c in self.WEEKLY_CHALLENGES if f"{c['id']}_{week}" not in self.completed]
    
    def complete_challenge(self, challenge_id: str, is_daily: bool = True) -> bool:
        """Mark a challenge as completed"""
        if is_daily:
            key = f"{challenge_id}_{datetime.now().date()}"
        else:
            key = f"{challenge_id}_{datetime.now().isocalendar()[1]}"
        
        if key not in self.completed:
            self.completed.append(key)
            self.save()
            return True
        return False
    
    def get_stats(self) -> dict[str, Any]:
        """Get challenge statistics"""
        total_daily = len(self.DAILY_CHALLENGES)
        total_weekly = len(self.WEEKLY_CHALLENGES)
        completed_daily = len([c for c in self.completed if c.startswith("d")])
        completed_weekly = len([c for c in self.completed if c.startswith("w")])
        
        return {
            "total_daily": total_daily,
            "total_weekly": total_weekly,
            "completed_daily": completed_daily,
            "completed_weekly": completed_weekly,
            "daily_completion_rate": (completed_daily / total_daily * 100) if total_daily > 0 else 0,
            "weekly_completion_rate": (completed_weekly / total_weekly * 100) if total_weekly > 0 else 0
        }

# ============================================================
# FRIEND SYSTEM
# ============================================================

class EcoFriends:
    """Friend system for EcoBuddy"""
    
    FRIEND_NAMES = [
        "EcoWarrior", "GreenGuru", "SustainabilityStar", 
        "CarbonCrusader", "PlanetProtector", "EcoChampion",
        "GreenThumb", "ZeroWasteHero", "ClimateAction"
    ]
    
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.friends = self._load_friends()
    
    def _load_friends(self) -> list[str]:
        """Load friends from session"""
        if "eco_friends" not in st.session_state:
            st.session_state.eco_friends = {}
        return st.session_state.eco_friends.get(self.user_id, [])
    
    def save(self) -> None:
        """Save friends"""
        st.session_state.eco_friends[self.user_id] = self.friends
    
    def add_friend(self, friend_name: str) -> bool:
        """Add a friend"""
        if friend_name not in self.friends:
            self.friends.append(friend_name)
            self.save()
            return True
        return False
    
    def remove_friend(self, friend_name: str) -> bool:
        """Remove a friend"""
        if friend_name in self.friends:
            self.friends.remove(friend_name)
            self.save()
            return True
        return False
    
    def get_suggestions(self) -> list[str]:
        """Get friend suggestions"""
        # Generate random suggestions
        suggestions = random.sample(self.FRIEND_NAMES, min(3, len(self.FRIEND_NAMES)))
        return [s for s in suggestions if s not in self.friends]
    
    def get_leaderboard(self) -> list[dict[str, Any]]:
        """Get friends leaderboard"""
        # Mock leaderboard data
        leaderboard = []
        for friend in self.friends[:5]:
            leaderboard.append({
                "name": friend,
                "score": random.randint(50, 95),
                "level": random.randint(1, 10),
                "streak": random.randint(0, 30)
            })
        
        # Add current user
        leaderboard.append({
            "name": st.session_state.get("username", "You"),
            "score": st.session_state.get("eco_score", 70),
            "level": st.session_state.get("level", 5),
            "streak": st.session_state.get("streak", 7)
        })
        
        return sorted(leaderboard, key=lambda x: x["score"], reverse=True)

# ============================================================
# ECO-FACTS & TIPS
# ============================================================

class EcoFacts:
    """Daily eco-facts and tips"""
    
    FACTS = [
        "🌍 One tree can absorb up to 22kg of CO2 per year",
        "💡 LED bulbs use 75% less energy than incandescent bulbs",
        "🚗 Taking public transport can reduce your carbon footprint by 30%",
        "🥩 Producing 1kg of beef generates 27kg of CO2",
        "♻️ Recycling one aluminum can saves enough energy to power a TV for 3 hours",
        "🌊 8 million tons of plastic enter the ocean every year",
        "🌱 Planting trees is the most cost-effective way to fight climate change",
        "💧 Turning off the tap while brushing saves up to 8 gallons of water per day",
        "☀️ Solar energy is the most abundant energy source on Earth",
        "🚲 Cycling instead of driving saves 150g of CO2 per kilometer"
    ]
    
    TIPS = [
        "💡 Tip: Unplug electronics when not in use to save energy",
        "🌿 Tip: Start a compost bin for food waste",
        "🚲 Tip: Bike or walk for trips under 3km",
        "🌱 Tip: Plant native species in your garden",
        "💧 Tip: Fix leaky faucets to save water",
        "♻️ Tip: Carry a reusable water bottle and coffee cup",
        "🥗 Tip: Try Meatless Monday to reduce your carbon footprint",
        "🔌 Tip: Use smart power strips to eliminate phantom power"
    ]
    
    @staticmethod
    def get_random_fact() -> str:
        """Get a random eco-fact"""
        return random.choice(EcoFacts.FACTS)
    
    @staticmethod
    def get_random_tip() -> str:
        """Get a random eco-tip"""
        return random.choice(EcoFacts.TIPS)
    
    @staticmethod
    def get_daily_fact() -> str:
        """Get a fact of the day (based on date)"""
        day = datetime.now().day
        return EcoFacts.FACTS[day % len(EcoFacts.FACTS)]
    
    @staticmethod
    def get_daily_tip() -> str:
        """Get a tip of the day (based on date)"""
        day = datetime.now().day
        return EcoFacts.TIPS[day % len(EcoFacts.TIPS)]

# ============================================================
# COMMUNITY POSTS
# ============================================================

class CommunityPosts:
    """Community post system"""
    
    def __init__(self) -> None:
        self.posts = self._load_posts()
    
    def _load_posts(self) -> list[dict[str, Any]]:
        """Load posts from session"""
        if "community_posts" not in st.session_state:
            # Initialize with sample posts
            st.session_state.community_posts = [
                {
                    "id": 1,
                    "user": "EcoWarrior",
                    "content": "Just completed my first zero-waste week! ♻️ Feeling great about reducing my waste by 80%!",
                    "timestamp": (datetime.now() - timedelta(days=1)).isoformat(),
                    "likes": 12,
                    "comments": [
                        {"user": "GreenGuru", "text": "Amazing work! Keep it up! 🌱", "timestamp": (datetime.now() - timedelta(hours=5)).isoformat()},
                        {"user": "EcoChampion", "text": "This is inspiring! I'm trying to do the same 💪", "timestamp": (datetime.now() - timedelta(hours=3)).isoformat()}
                    ]
                },
                {
                    "id": 2,
                    "user": "GreenThumb",
                    "content": "Planted 10 trees in my community today! 🌳 Together we can make a difference!",
                    "timestamp": (datetime.now() - timedelta(days=2)).isoformat(),
                    "likes": 8,
                    "comments": [
                        {"user": "SustainabilityStar", "text": "That's fantastic! 🌿", "timestamp": (datetime.now() - timedelta(days=1)).isoformat()}
                    ]
                }
            ]
        return st.session_state.community_posts
    
    def save(self) -> None:
        """Save posts"""
        st.session_state.community_posts = self.posts
    
    def add_post(self, user: str, content: str) -> dict[str, Any]:
        """Add a new post"""
        post = {
            "id": len(self.posts) + 1,
            "user": user,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "likes": 0,
            "comments": []
        }
        self.posts.insert(0, post)
        self.save()
        return post
    
    def like_post(self, post_id: int) -> bool:
        """Like a post"""
        for post in self.posts:
            if post["id"] == post_id:
                post["likes"] += 1
                self.save()
                return True
        return False
    
    def add_comment(self, post_id: int, user: str, text: str) -> bool:
        """Add a comment to a post"""
        for post in self.posts:
            if post["id"] == post_id:
                comment = {
                    "user": user,
                    "text": text,
                    "timestamp": datetime.now().isoformat()
                }
                post["comments"].append(comment)
                self.save()
                return True
        return False
    
    def get_trending(self) -> list[dict[str, Any]]:
        """Get trending posts"""
        return sorted(self.posts, key=lambda x: x["likes"], reverse=True)[:3]

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_social() -> None:
    """Render the eco-social community section"""
    st.markdown("<div class='section-header'>🌍 Eco-Social Community</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    username = st.session_state.get("username", "EcoUser")
    
    # Initialize managers
    if "challenges" not in st.session_state:
        st.session_state.challenges = EcoChallenges(user_id)
    if "friends" not in st.session_state:
        st.session_state.friends = EcoFriends(user_id)
    if "community" not in st.session_state:
        st.session_state.community = CommunityPosts()
    
    # Display daily fact
    st.info(f"💡 **Daily Eco-Fact:** {EcoFacts.get_daily_fact()}")
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Challenges", "👥 Friends", "📝 Community"])
    
    with tab1:
        render_challenges()
    
    with tab2:
        render_friends()
    
    with tab3:
        render_community()

def render_challenges() -> None:
    """Render the challenges section"""
    st.markdown("### 🎯 Daily & Weekly Challenges")
    
    challenges = st.session_state.challenges
    
    # Stats
    stats = challenges.get_stats()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Daily Challenges", f"{stats['completed_daily']}/{stats['total_daily']}")
    col2.metric("Weekly Challenges", f"{stats['completed_weekly']}/{stats['total_weekly']}")
    col3.metric("Daily Rate", f"{stats['daily_completion_rate']:.0f}%")
    col4.metric("Weekly Rate", f"{stats['weekly_completion_rate']:.0f}%")
    
    st.markdown("---")
    
    # Daily Challenges
    st.markdown("### 📅 Today's Challenges")
    daily = challenges.get_daily()
    if daily:
        for challenge in daily:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{challenge['title']}**")
                    st.caption(challenge['description'])
                    st.caption(f"🏷️ {challenge['category']} • Difficulty: {challenge['difficulty']}")
                with col2:
                    st.metric("XP", challenge['xp_reward'])
                with col3:
                    if st.button("✅ Complete", key=f"complete_d_{challenge['id']}"):
                        if challenges.complete_challenge(challenge['id'], is_daily=True):
                            st.success(f"🎉 Challenge completed! +{challenge['xp_reward']} XP!")
                            st.rerun()
                st.markdown("---")
    else:
        st.success("🎉 You've completed all daily challenges for today!")
    
    # Weekly Challenges
    st.markdown("### 📅 This Week's Challenges")
    weekly = challenges.get_weekly()
    if weekly:
        for challenge in weekly:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{challenge['title']}**")
                    st.caption(challenge['description'])
                    st.caption(f"🏷️ {challenge['category']} • Difficulty: {challenge['difficulty']}")
                with col2:
                    st.metric("XP", challenge['xp_reward'])
                with col3:
                    if st.button("✅ Complete", key=f"complete_w_{challenge['id']}"):
                        if challenges.complete_challenge(challenge['id'], is_daily=False):
                            st.success(f"🎉 Weekly challenge completed! +{challenge['xp_reward']} XP!")
                            st.rerun()
                st.markdown("---")
    else:
        st.success("🎉 You've completed all weekly challenges for this week!")

def render_friends() -> None:
    """Render the friends section"""
    st.markdown("### 👥 Friends & Leaderboard")
    
    friends = st.session_state.friends
    
    # Add friend
    with st.expander("➕ Add Friend"):
        suggestions = friends.get_suggestions()
        if suggestions:
            for suggestion in suggestions:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"👤 {suggestion}")
                with col2:
                    if st.button("Add", key=f"add_{suggestion}"):
                        friends.add_friend(suggestion)
                        st.success(f"✅ {suggestion} added as friend!")
                        st.rerun()
        else:
            st.info("No friend suggestions available")
        
        # Manual add
        manual_friend = st.text_input("Or enter username:", placeholder="Enter username...")
        if st.button("Add Friend", key="add_manual"):
            if manual_friend:
                friends.add_friend(manual_friend)
                st.success(f"✅ {manual_friend} added as friend!")
                st.rerun()
    
    # Leaderboard
    st.markdown("### 🏆 Friends Leaderboard")
    leaderboard = friends.get_leaderboard()
    
    if leaderboard:
        df = pd.DataFrame(leaderboard)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Friends list
    st.markdown("### 👥 Your Friends")
    if friends.friends:
        for friend in friends.friends:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"👤 {friend}")
            with col2:
                if st.button("Remove", key=f"remove_{friend}"):
                    friends.remove_friend(friend)
                    st.rerun()
    else:
        st.info("You don't have any friends yet. Add some friends above!")

def render_community() -> None:
    """Render the community section"""
    st.markdown("### 📝 Community Posts")
    
    community = st.session_state.community
    username = st.session_state.get("username", "EcoUser")
    
    # Create post
    with st.expander("✍️ Share Your Progress"):
        post_content = st.text_area("What's your sustainability win today?", 
                                   placeholder="Share your eco-achievements...", 
                                   height=100)
        if st.button("📤 Post", key="create_post"):
            if post_content.strip():
                community.add_post(username, post_content)
                st.success("✅ Post shared with the community!")
                st.rerun()
            else:
                st.warning("Please write something to share")
    
    # Trending posts
    st.markdown("### 🔥 Trending Posts")
    trending = community.get_trending()
    for post in trending:
        with st.container():
            st.markdown(f"**👤 {post['user']}** • {post['timestamp'][:10]}")
            st.markdown(f"*{post['content']}*")
            
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button(f"❤️ {post['likes']}", key=f"like_{post['id']}"):
                    community.like_post(post['id'])
                    st.rerun()
            
            with col2:
                if st.button("💬 Comment", key=f"comment_btn_{post['id']}"):
                    st.session_state[f"show_comments_{post['id']}"] = True
            
            # Show comments
            if st.session_state.get(f"show_comments_{post['id']}", False):
                for comment in post['comments']:
                    st.caption(f"**{comment['user']}**: {comment['text']}")
                
                new_comment = st.text_input("Write a comment...", key=f"comment_input_{post['id']}")
                if st.button("Post Comment", key=f"post_comment_{post['id']}"):
                    if new_comment.strip():
                        community.add_comment(post['id'], username, new_comment)
                        st.rerun()
            
            st.markdown("---")

def render_eco_tip() -> None:
    """Render a daily eco-tip in sidebar"""
    tip = EcoFacts.get_daily_tip()
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 💡 Daily Eco-Tip")
    st.sidebar.info(tip)

# ============================================================
# SAMPLE USAGE IN MAIN APP
# ============================================================

"""
# To add to your main app.py:

# Import
from eco_social import render_eco_social, render_eco_tip

# In sidebar (add after theme selector)
render_eco_tip()

# Add as a new tab (modify existing tabs)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🌍 Carbon Footprint",
    "⚡ Home Energy Audit",
    "🎮 Gamification",
    "🗺️ Route Planning & Offsets",
    "🏆 Community Leaderboard",
    "🔮 Future Self",
    "🌿 Sustainability Hub",
    "🌍 Eco-Social"  # NEW
])

with tab8:
    render_eco_social()
"""