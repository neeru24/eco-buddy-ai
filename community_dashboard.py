# ============================================================
# FILE: community_dashboard.py
# EcoBuddy AI+ Community Dashboard & Analytics
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import json
import math
from collections import Counter

# ============================================================
# COMMUNITY METRICS
# ============================================================

class CommunityMetrics:
    """Track and analyze community sustainability metrics"""
    
    def __init__(self):
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        """Load metrics from session"""
        if "community_metrics" not in st.session_state:
            st.session_state.community_metrics = {
                "total_users": 0,
                "active_users": 0,
                "total_assessments": 0,
                "total_co2_reduced": 0,
                "total_trees_planted": 0,
                "daily_activity": [],
                "user_growth": [],
                "challenges_completed": 0,
                "leaderboard_updates": []
            }
        stored = st.session_state.community_metrics
        if isinstance(stored, CommunityMetrics):
            return stored.metrics
        return stored
    
    def save(self):
        """Save metrics"""
        st.session_state.community_metrics = self
    
    def update_metrics(self, user_data):
        """Update community metrics with new user data"""
        self.metrics["total_users"] += 1
        
        # Update daily activity
        today = datetime.now().date().isoformat()
        if not self.metrics["daily_activity"] or self.metrics["daily_activity"][-1]["date"] != today:
            self.metrics["daily_activity"].append({
                "date": today,
                "assessments": 1,
                "users": 1
            })
        else:
            self.metrics["daily_activity"][-1]["assessments"] += 1
            self.metrics["daily_activity"][-1]["users"] += 1
        
        # Update user growth (weekly)
        week = datetime.now().isocalendar()[1]
        if not self.metrics["user_growth"] or self.metrics["user_growth"][-1]["week"] != week:
            self.metrics["user_growth"].append({
                "week": week,
                "new_users": 1,
                "date": datetime.now().isoformat()
            })
        else:
            self.metrics["user_growth"][-1]["new_users"] += 1
        
        # Update CO2 reduction
        if "total_co2_reduced" in user_data:
            self.metrics["total_co2_reduced"] += user_data["total_co2_reduced"]
        
        self.save()
    
    def get_summary(self):
        """Get community summary statistics"""
        return {
            "total_users": self.metrics["total_users"],
            "active_users": self.metrics["active_users"],
            "total_assessments": self.metrics["total_assessments"],
            "total_co2_reduced": self.metrics["total_co2_reduced"],
            "total_trees_planted": self.metrics["total_trees_planted"],
            "challenges_completed": self.metrics["challenges_completed"]
        }
    
    def get_daily_trends(self, days=30):
        """Get daily activity trends"""
        return self.metrics["daily_activity"][-days:]
    
    def get_growth_trends(self, weeks=12):
        """Get user growth trends"""
        return self.metrics["user_growth"][-weeks:]

# ============================================================
# COMMUNITY CHALLENGES
# ============================================================

class CommunityChallenges:
    """Community-wide sustainability challenges"""
    
    CHALLENGES = [
        {
            "id": "cc1",
            "title": "🌍 Carbon Reduction Week",
            "description": "Reduce your carbon footprint by 20% this week",
            "target": 20,
            "unit": "%",
            "duration": "7 days",
            "difficulty": "Medium",
            "participants": 0,
            "completed": 0,
            "reward": "Eco Champion Badge"
        },
        {
            "id": "cc2",
            "title": "🌱 Plant 100 Trees",
            "description": "Collectively plant 100 trees in your community",
            "target": 100,
            "unit": "trees",
            "duration": "30 days",
            "difficulty": "Hard",
            "participants": 0,
            "completed": 0,
            "reward": "Forest Guardian Badge"
        },
        {
            "id": "cc3",
            "title": "💧 Water Saving Challenge",
            "description": "Reduce daily water usage by 20%",
            "target": 20,
            "unit": "%",
            "duration": "14 days",
            "difficulty": "Easy",
            "participants": 0,
            "completed": 0,
            "reward": "Water Saver Badge"
        },
        {
            "id": "cc4",
            "title": "♻️ Zero Waste Week",
            "description": "Produce less than 2kg of waste per person",
            "target": 2,
            "unit": "kg",
            "duration": "7 days",
            "difficulty": "Hard",
            "participants": 0,
            "completed": 0,
            "reward": "Zero Hero Badge"
        },
        {
            "id": "cc5",
            "title": "🚲 Active Commute Challenge",
            "description": "Commute without driving for 5 days",
            "target": 5,
            "unit": "days",
            "duration": "7 days",
            "difficulty": "Medium",
            "participants": 0,
            "completed": 0,
            "reward": "Green Commuter Badge"
        }
    ]
    
    def __init__(self):
        self.challenges = self._load_challenges()
    
    def _load_challenges(self):
        """Load challenges from session"""
        if "community_challenges" not in st.session_state:
            st.session_state.community_challenges = self.CHALLENGES.copy()
        stored = st.session_state.community_challenges
        if isinstance(stored, CommunityChallenges):
            return stored.challenges
        return stored
    
    def save(self):
        """Save challenges"""
        st.session_state.community_challenges = self
    
    def get_challenges(self):
        """Get all challenges"""
        return self.challenges
    
    def join_challenge(self, challenge_id, user_id):
        """Join a community challenge"""
        for challenge in self.challenges:
            if challenge["id"] == challenge_id:
                challenge["participants"] += 1
                self.save()
                return True
        return False
    
    def complete_challenge(self, challenge_id):
        """Mark a challenge as completed"""
        for challenge in self.challenges:
            if challenge["id"] == challenge_id:
                challenge["completed"] += 1
                self.save()
                return True
        return False
    
    def get_stats(self):
        """Get challenge statistics"""
        total = len(self.challenges)
        active = sum(1 for c in self.challenges if c["participants"] > 0)
        completed = sum(c["completed"] for c in self.challenges)
        
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "participation_rate": (completed / total * 100) if total > 0 else 0
        }

# ============================================================
# COMMUNITY RANKINGS
# ============================================================

class CommunityRankings:
    """Community rankings and achievements"""
    
    RANKS = [
        {"name": "Eco Novice", "min_score": 0, "emoji": "🌱"},
        {"name": "Green Learner", "min_score": 25, "emoji": "📚"},
        {"name": "Sustainability Star", "min_score": 50, "emoji": "⭐"},
        {"name": "Eco Champion", "min_score": 75, "emoji": "🏆"},
        {"name": "Green Guardian", "min_score": 90, "emoji": "🌍"}
    ]
    
    def __init__(self):
        self.rankings = self._load_rankings()
    
    def _load_rankings(self):
        """Load rankings from session"""
        if "community_rankings" not in st.session_state:
            st.session_state.community_rankings = {}
        stored = st.session_state.community_rankings
        if isinstance(stored, CommunityRankings):
            return stored.rankings
        return stored
    
    def save(self):
        """Save rankings"""
        st.session_state.community_rankings = self
    
    def add_user_ranking(self, user_id, username, eco_score, assessments_count):
        """Add or update user ranking"""
        rank = self._calculate_rank(eco_score)
        self.rankings[user_id] = {
            "username": username,
            "eco_score": eco_score,
            "assessments": assessments_count,
            "rank": rank,
            "last_updated": datetime.now().isoformat()
        }
        self.save()
    
    def _calculate_rank(self, score):
        """Calculate rank based on score"""
        for rank in self.RANKS:
            if score >= rank["min_score"]:
                return rank
        return self.RANKS[0]
    
    def get_top_users(self, limit=10):
        """Get top ranked users"""
        if not self.rankings:
            return []
        
        sorted_users = sorted(
            self.rankings.items(),
            key=lambda x: x[1]["eco_score"],
            reverse=True
        )
        return sorted_users[:limit]
    
    def get_ranking_distribution(self):
        """Get distribution of ranks"""
        if not self.rankings:
            return {}
        
        rank_counts = Counter()
        for user in self.rankings.values():
            rank_counts[user["rank"]["name"]] += 1
        
        return dict(rank_counts)

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_community_dashboard():
    """Render the complete community dashboard"""
    st.markdown("<div class='section-header'>🌍 Community Dashboard & Analytics</div>", unsafe_allow_html=True)
    
    # Initialize components
    if "community_metrics" not in st.session_state:
        st.session_state.community_metrics = CommunityMetrics()
    if "community_challenges" not in st.session_state:
        st.session_state.community_challenges = CommunityChallenges()
    if "community_rankings" not in st.session_state:
        st.session_state.community_rankings = CommunityRankings()
    
    # Add sample data if empty
    _initialize_sample_data()
    
    metrics = st.session_state.community_metrics
    challenges = st.session_state.community_challenges
    rankings = st.session_state.community_rankings
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🏆 Rankings",
        "🎯 Challenges",
        "📈 Analytics",
        "🏅 Achievements"
    ])
    
    with tab1:
        render_dashboard_overview(metrics, challenges, rankings)
    
    with tab2:
        render_rankings(rankings)
    
    with tab3:
        render_challenges(challenges)
    
    with tab4:
        render_analytics(metrics)
    
    with tab5:
        render_achievements(rankings)

def _initialize_sample_data():
    """Initialize sample community data"""
    metrics = st.session_state.community_metrics
    rankings = st.session_state.community_rankings
    
    if metrics.metrics["total_users"] == 0:
        # Add sample users
        sample_users = [
            {"name": "EcoWarrior", "score": 92},
            {"name": "GreenGuru", "score": 88},
            {"name": "SustainabilityStar", "score": 85},
            {"name": "CarbonCrusader", "score": 78},
            {"name": "PlanetProtector", "score": 72},
            {"name": "EcoChampion", "score": 68},
            {"name": "GreenThumb", "score": 60},
            {"name": "ZeroWasteHero", "score": 55},
            {"name": "ClimateAction", "score": 50},
            {"name": "EcoLearner", "score": 45}
        ]
        
        for user in sample_users:
            metrics.metrics["total_users"] += 1
            rankings.add_user_ranking(
                len(rankings.rankings) + 1,
                user["name"],
                user["score"],
                random.randint(3, 15)
            )
        
        # Add sample CO2 reduction
        metrics.metrics["total_co2_reduced"] = random.randint(5000, 15000)
        metrics.metrics["total_trees_planted"] = random.randint(200, 800)
        metrics.metrics["challenges_completed"] = random.randint(50, 200)
        
        # Add sample daily activity
        for i in range(30):
            date = (datetime.now() - timedelta(days=29-i)).date().isoformat()
            metrics.metrics["daily_activity"].append({
                "date": date,
                "assessments": random.randint(2, 15),
                "users": random.randint(1, 8)
            })
        
        # Add sample user growth
        for i in range(12):
            week = (datetime.now() - timedelta(weeks=11-i)).isocalendar()[1]
            metrics.metrics["user_growth"].append({
                "week": week,
                "new_users": random.randint(1, 10),
                "date": (datetime.now() - timedelta(weeks=11-i)).isoformat()
            })
        
        metrics.save()
        rankings.save()

def render_dashboard_overview(metrics, challenges, rankings):
    """Render dashboard overview"""
    st.markdown("### 📊 Community Overview")
    
    # Key metrics
    summary = metrics.get_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Users", f"{summary['total_users']:,}")
    col2.metric("🌍 CO₂ Reduced", f"{summary['total_co2_reduced']:,} kg")
    col3.metric("🌳 Trees Planted", f"{summary['total_trees_planted']:,}")
    col4.metric("🏆 Challenges Done", f"{summary['challenges_completed']:,}")
    
    # Second row of metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate active users (last 7 days)
    daily = metrics.get_daily_trends(7)
    active_users = sum(d["users"] for d in daily) if daily else 0
    col1.metric("📊 Active Users (7d)", active_users)
    
    # Average daily assessments
    avg_daily = sum(d["assessments"] for d in daily) / len(daily) if daily else 0
    col2.metric("📝 Avg Daily Assessments", f"{avg_daily:.1f}")
    
    # Challenge participation
    challenge_stats = challenges.get_stats()
    col3.metric("🎯 Active Challenges", challenge_stats["active"])
    col4.metric("💪 Participation Rate", f"{challenge_stats['participation_rate']:.0f}%")
    
    # Community growth chart
    st.markdown("---")
    st.markdown("### 📈 Community Growth")
    
    growth_data = metrics.get_growth_trends(12)
    if growth_data:
        df_growth = pd.DataFrame(growth_data)
        df_growth['date'] = pd.to_datetime(df_growth['date'])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_growth['date'],
            y=df_growth['new_users'],
            name='New Users',
            marker_color='#4ade80'
        ))
        fig.update_layout(
            title="New Users Per Week",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis_title="Week",
            yaxis_title="New Users"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Community growth data coming soon!")
    
    # Daily activity heatmap
    st.markdown("### 📊 Daily Activity")
    
    daily_data = metrics.get_daily_trends(30)
    if daily_data:
        df_daily = pd.DataFrame(daily_data)
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        df_daily['day_name'] = df_daily['date'].dt.day_name()
        df_daily['week'] = df_daily['date'].dt.isocalendar().week
        
        # Create heatmap
        pivot = df_daily.pivot_table(
            values='assessments',
            index='day_name',
            columns='week',
            aggfunc='sum',
            fill_value=0
        )
        
        fig = px.imshow(
            pivot.values,
            x=pivot.columns,
            y=pivot.index,
            color_continuous_scale='Greens',
            title="Activity Heatmap (Last 30 Days)"
        )
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 Activity data coming soon!")

def render_rankings(rankings):
    """Render community rankings"""
    st.markdown("### 🏆 Community Rankings")
    
    # Ranking distribution
    distribution = rankings.get_ranking_distribution()
    if distribution:
        st.markdown("#### Ranking Distribution")
        
        fig = go.Figure(data=[go.Pie(
            labels=list(distribution.keys()),
            values=list(distribution.values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Top users
    st.markdown("#### 🏅 Top 10 Users")
    
    top_users = rankings.get_top_users(10)
    if top_users:
        # Create leaderboard
        leaderboard_data = []
        for i, (user_id, data) in enumerate(top_users, 1):
            rank_emoji = data["rank"]["emoji"]
            leaderboard_data.append({
                "Rank": i,
                "User": f"{rank_emoji} {data['username']}",
                "Eco Score": data["eco_score"],
                "Assessments": data["assessments"],
                "Level": data["rank"]["name"]
            })
        
        df_leaderboard = pd.DataFrame(leaderboard_data)
        st.dataframe(df_leaderboard, use_container_width=True, hide_index=True)
    else:
        st.info("🏆 No users ranked yet. Complete assessments to appear on the leaderboard!")
    
    # User rank search
    st.markdown("---")
    st.markdown("#### 🔍 Find Your Rank")
    
    # Simulated user input
    username = st.text_input("Enter your username", placeholder="Your username...")
    if username:
        # Search for user
        found = False
        for user_id, data in rankings.rankings.items():
            if data["username"].lower() == username.lower():
                found = True
                st.markdown(f"""
                <div class='card-highlight'>
                    <div style='text-align: center;'>
                        <div style='font-size: 48px;'>{data['rank']['emoji']}</div>
                        <h3 style='color: #4ade80;'>{data['username']}</h3>
                        <p>Eco Score: {data['eco_score']}</p>
                        <p>Rank: {data['rank']['name']}</p>
                        <p>Assessments: {data['assessments']}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                break
        
        if not found:
            st.warning("👤 User not found. Complete an assessment to join the rankings!")

def render_challenges(challenges):
    """Render community challenges"""
    st.markdown("### 🎯 Community Challenges")
    
    # Challenge stats
    stats = challenges.get_stats()
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Challenges", stats["total"])
    col2.metric("Active", stats["active"])
    col3.metric("Completed", stats["completed"])
    
    st.markdown("---")
    
    # Display challenges
    for challenge in challenges.get_challenges():
        with st.container():
            # Progress calculation
            progress = (challenge["completed"] / max(challenge["participants"], 1)) * 100
            progress = min(progress, 100)
            
            difficulty_colors = {
                "Easy": "#4ade80",
                "Medium": "#fbbf24",
                "Hard": "#f87171"
            }
            color = difficulty_colors.get(challenge["difficulty"], "#6b7280")
            
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div>
                        <h4 style='margin: 0; color: #4ade80;'>{challenge['title']}</h4>
                        <p style='color: #6b7280; font-size: 14px; margin: 4px 0;'>{challenge['description']}</p>
                        <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>
                            <span>🎯 Target: {challenge['target']} {challenge['unit']}</span>
                            <span>⏱️ {challenge['duration']}</span>
                            <span style='color: {color};'>🎯 {challenge['difficulty']}</span>
                            <span>👥 {challenge['participants']} participants</span>
                            <span>🏆 Reward: {challenge['reward']}</span>
                        </div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>
                            {challenge['completed']}/{challenge['participants']}
                        </div>
                        <div style='font-size: 12px; color: #6b7280;'>Completed</div>
                    </div>
                </div>
                <div style='margin-top: 10px;'>
                    <div class='progress-bar' style='height: 8px;'>
                        <div class='progress-fill' style='width: {progress}%;'></div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button(f"🚀 Join Challenge", key=f"join_{challenge['id']}"):
                    challenges.join_challenge(challenge["id"], st.session_state.get("user_id", 1))
                    st.success(f"✅ Joined {challenge['title']}!")
                    st.rerun()

def render_analytics(metrics):
    """Render detailed analytics"""
    st.markdown("### 📈 Community Analytics")
    
    # Time period selector
    period = st.selectbox(
        "Select Time Period",
        ["Last 7 Days", "Last 30 Days", "Last 90 Days"]
    )
    
    days = {"Last 7 Days": 7, "Last 30 Days": 30, "Last 90 Days": 90}[period]
    
    # Get data
    daily_data = metrics.get_daily_trends(days)
    
    if daily_data:
        df = pd.DataFrame(daily_data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Activity trends
        st.markdown("#### 📊 Activity Trends")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['assessments'],
            name='Assessments',
            line=dict(color='#4ade80', width=2),
            fill='tozeroy',
            fillcolor='rgba(74, 222, 128, 0.2)'
        ))
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['users'],
            name='Active Users',
            line=dict(color='#60a5fa', width=2)
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistics
        st.markdown("#### 📊 Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Assessments", df['assessments'].sum())
        col2.metric("Average Daily", f"{df['assessments'].mean():.1f}")
        col3.metric("Total Users", df['users'].sum())
        col4.metric("Average Users", f"{df['users'].mean():.1f}")
        
        # Engagement metrics
        st.markdown("#### 💪 Engagement Metrics")
        
        engagement_data = {
            "Metric": ["Assessments per User", "Weekly Active Users", "Retention Rate"],
            "Value": [
                f"{df['assessments'].sum() / max(df['users'].sum(), 1):.1f}",
                f"{df['users'].tail(7).sum():.0f}",
                f"{min(100, (df['users'].tail(7).sum() / df['users'].tail(14).sum()) * 100):.0f}%"
            ]
        }
        
        df_engagement = pd.DataFrame(engagement_data)
        st.dataframe(df_engagement, use_container_width=True, hide_index=True)
        
        # Export data
        st.markdown("#### 📥 Export Data")
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Download Analytics (CSV)",
            data=csv,
            file_name=f"community_analytics_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    else:
        st.info("📊 No analytics data available yet")

def render_achievements(rankings):
    """Render community achievements"""
    st.markdown("### 🏅 Community Achievements")
    
    # User progress
    user_id = st.session_state.get("user_id", 1)
    user_data = rankings.rankings.get(user_id)
    
    if user_data:
        st.markdown("#### 🎯 Your Progress")
        
        rank = user_data["rank"]
        score = user_data["eco_score"]
        assessments = user_data["assessments"]
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Current Rank", f"{rank['emoji']} {rank['name']}")
        col2.metric("Eco Score", f"{score}/100")
        col3.metric("Assessments", assessments)
        
        # Progress to next rank
        current_rank_idx = 0
        for i, r in enumerate(CommunityRankings.RANKS):
            if r["name"] == rank["name"]:
                current_rank_idx = i
                break
        
        if current_rank_idx < len(CommunityRankings.RANKS) - 1:
            next_rank = CommunityRankings.RANKS[current_rank_idx + 1]
            progress_to_next = (score / next_rank["min_score"]) * 100
            progress_to_next = min(progress_to_next, 100)
            
            st.markdown(f"#### Progress to {next_rank['emoji']} {next_rank['name']}")
            st.progress(progress_to_next / 100)
            st.caption(f"{score}/{next_rank['min_score']} points needed")
        
        # Badges
        st.markdown("#### 🎖️ Your Badges")
        
        badges = [
            {"name": "First Assessment", "unlocked": assessments >= 1, "emoji": "🌟"},
            {"name": "Eco Explorer", "unlocked": assessments >= 5, "emoji": "🌍"},
            {"name": "Sustainability Star", "unlocked": score >= 50, "emoji": "⭐"},
            {"name": "Eco Champion", "unlocked": score >= 75, "emoji": "🏆"},
            {"name": "Green Guardian", "unlocked": score >= 90, "emoji": "🌿"},
            {"name": "Carbon Crusher", "unlocked": assessments >= 10, "emoji": "💪"}
        ]
        
        cols = st.columns(3)
        for i, badge in enumerate(badges):
            with cols[i % 3]:
                if badge["unlocked"]:
                    st.success(f"{badge['emoji']} {badge['name']} ✅")
                else:
                    st.markdown(f"🔒 {badge['name']}")
        
        # Community milestones
        st.markdown("#### 🌍 Community Milestones")
        
        milestones = [
            {"name": "🌳 1000 Trees Planted", "progress": 78},
            {"name": "💧 10,000 Liters Saved", "progress": 65},
            {"name": "♻️ 5,000 kg Waste Reduced", "progress": 42},
            {"name": "🚲 10,000 km Active Commute", "progress": 55}
        ]
        
        for milestone in milestones:
            st.markdown(f"**{milestone['name']}**")
            st.progress(milestone["progress"] / 100)
            st.caption(f"{milestone['progress']}% complete")
    else:
        st.info("🏅 Complete your first assessment to earn achievements and badges!")

# ============================================================
# INTEGRATION
# ============================================================

def render_community_analytics():
    """Render the complete community analytics"""
    render_community_dashboard()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from community_dashboard import render_community_analytics

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20 = st.tabs([
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
    "📊 Community Analytics"  # NEW
])

with tab20:
    render_community_analytics()
"""