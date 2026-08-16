# ============================================================
# FILE: eco_news.py
# EcoBuddy AI+ Eco-News & Sustainability Updates
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
import random
import json
import math
import hashlib

# ============================================================
# NEWS DATABASE
# ============================================================

class EcoNewsDatabase:
    """Database of sustainability news and articles"""
    
    NEWS = [
        {
            "id": "n1",
            "title": "Global Renewable Energy Capacity Hits Record High",
            "category": "Energy",
            "source": "EcoWatch",
            "date": datetime.now() - timedelta(days=1),
            "summary": "Renewable energy capacity grew by 10% globally in 2024, with solar leading the way.",
            "content": "Solar and wind power installations reached record levels, with China and US leading the growth. Renewable sources now account for 30% of global electricity generation.",
            "impact": "Positive",
            "tags": ["Renewable Energy", "Solar", "Wind"],
            "emoji": "☀️",
            "read_time": 3,
            "url": "https://example.com/news/1"
        },
        {
            "id": "n2",
            "title": "New Ocean Cleanup Technology Removes 10,000kg of Plastic",
            "category": "Environment",
            "source": "Ocean Cleanup",
            "date": datetime.now() - timedelta(days=2),
            "summary": "Innovative ocean cleanup system successfully removed 10,000kg of plastic from the Great Pacific Garbage Patch.",
            "content": "The system uses advanced filtration to capture microplastics and larger debris. This milestone marks significant progress in ocean conservation.",
            "impact": "Positive",
            "tags": ["Ocean", "Plastic", "Cleanup"],
            "emoji": "🌊",
            "read_time": 4,
            "url": "https://example.com/news/2"
        },
        {
            "id": "n3",
            "title": "Electric Vehicle Sales Surpass 20 Million Globally",
            "category": "Transport",
            "source": "EV News",
            "date": datetime.now() - timedelta(days=3),
            "summary": "Global EV sales reached 20 million units, marking a 35% increase from the previous year.",
            "content": "The transition to electric vehicles is accelerating, with major automakers committing to electric fleets by 2030.",
            "impact": "Positive",
            "tags": ["Electric Vehicles", "Transport", "Climate"],
            "emoji": "🚗",
            "read_time": 3,
            "url": "https://example.com/news/3"
        },
        {
            "id": "n4",
            "title": "Amazon Deforestation Rate Decreases by 20%",
            "category": "Environment",
            "source": "Rainforest Alliance",
            "date": datetime.now() - timedelta(days=4),
            "summary": "Deforestation in the Amazon has decreased by 20% due to increased conservation efforts.",
            "content": "Brazil's new conservation policies and international pressure have contributed to the decline in deforestation rates.",
            "impact": "Positive",
            "tags": ["Amazon", "Deforestation", "Conservation"],
            "emoji": "🌳",
            "read_time": 4,
            "url": "https://example.com/news/4"
        },
        {
            "id": "n5",
            "title": "Plant-Based Meat Market to Reach $35 Billion by 2027",
            "category": "Food",
            "source": "Food Business News",
            "date": datetime.now() - timedelta(days=5),
            "summary": "The plant-based meat market is projected to grow to $35 billion, driven by consumer demand.",
            "content": "Investment in plant-based alternatives has increased, with major food companies expanding their product lines.",
            "impact": "Positive",
            "tags": ["Plant-Based", "Food", "Sustainability"],
            "emoji": "🥩",
            "read_time": 3,
            "url": "https://example.com/news/5"
        },
        {
            "id": "n6",
            "title": "Green Building Certifications Rise 40% in Developing Countries",
            "category": "Business",
            "source": "Green Building Council",
            "date": datetime.now() - timedelta(days=6),
            "summary": "Green building certifications have increased by 40% in developing economies.",
            "content": "Sustainable construction is becoming more accessible globally, with new technologies reducing costs.",
            "impact": "Positive",
            "tags": ["Green Building", "Construction", "Energy Efficiency"],
            "emoji": "🏗️",
            "read_time": 4,
            "url": "https://example.com/news/6"
        },
        {
            "id": "n7",
            "title": "Global CO2 Emissions Could Peak by 2025",
            "category": "Climate",
            "source": "Climate Action",
            "date": datetime.now() - timedelta(days=7),
            "summary": "Global CO2 emissions are projected to peak by 2025 as renewable energy adoption accelerates.",
            "content": "The transition to clean energy is happening faster than expected, with many countries achieving their climate targets early.",
            "impact": "Positive",
            "tags": ["CO2", "Climate Change", "Emissions"],
            "emoji": "🌍",
            "read_time": 5,
            "url": "https://example.com/news/7"
        },
        {
            "id": "n8",
            "title": "Ocean Acidification Threatens Coral Reefs Worldwide",
            "category": "Environment",
            "source": "Marine Conservation",
            "date": datetime.now() - timedelta(days=8),
            "summary": "Rising ocean acidity is causing widespread coral bleaching and reef degradation.",
            "content": "Scientists warn that urgent action is needed to reduce carbon emissions and protect marine ecosystems.",
            "impact": "Negative",
            "tags": ["Ocean", "Coral Reefs", "Acidification"],
            "emoji": "🐠",
            "read_time": 5,
            "url": "https://example.com/news/8"
        },
        {
            "id": "n9",
            "title": "World's Largest Solar Farm Goes Online in India",
            "category": "Energy",
            "source": "Solar Today",
            "date": datetime.now() - timedelta(days=9),
            "summary": "India has completed the world's largest solar farm, covering 50 square kilometers.",
            "content": "The facility can power 2 million homes and reduce CO2 emissions by 3 million tons annually.",
            "impact": "Positive",
            "tags": ["Solar", "Renewable Energy", "India"],
            "emoji": "☀️",
            "read_time": 4,
            "url": "https://example.com/news/9"
        },
        {
            "id": "n10",
            "title": "Plastic Waste Recycling Technology Breakthrough",
            "category": "Waste",
            "source": "Waste Management",
            "date": datetime.now() - timedelta(days=10),
            "summary": "New chemical recycling process can recycle all types of plastic waste.",
            "content": "The breakthrough technology can break down plastic into its original components, enabling infinite recycling.",
            "impact": "Positive",
            "tags": ["Recycling", "Plastic", "Technology"],
            "emoji": "♻️",
            "read_time": 4,
            "url": "https://example.com/news/10"
        }
    ]
    
    @staticmethod
    def get_news(category=None, days=30):
        """Get news with filters"""
        cutoff = datetime.now() - timedelta(days=days)
        news = [n for n in EcoNewsDatabase.NEWS if n["date"] >= cutoff]
        
        if category and category != "All":
            news = [n for n in news if n["category"] == category]
        
        return sorted(news, key=lambda x: x["date"], reverse=True)
    
    @staticmethod
    def get_categories():
        """Get news categories"""
        return ["All"] + sorted(set(n["category"] for n in EcoNewsDatabase.NEWS))
    
    @staticmethod
    def get_category_stats():
        """Get category statistics"""
        stats = {}
        for news in EcoNewsDatabase.NEWS:
            category = news["category"]
            if category not in stats:
                stats[category] = 0
            stats[category] += 1
        return stats
    
    @staticmethod
    def get_impact_stats():
        """Get impact statistics"""
        impact_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for news in EcoNewsDatabase.NEWS:
            impact = news["impact"]
            if impact in impact_counts:
                impact_counts[impact] += 1
        return impact_counts

# ============================================================
# USER PREFERENCES
# ============================================================

class UserNewsPreferences:
    """User preferences for news"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.preferences = self._load_preferences()
    
    def _load_preferences(self):
        """Load preferences from session"""
        if "news_preferences" not in st.session_state:
            st.session_state.news_preferences = {}
        return st.session_state.news_preferences.get(self.user_id, {
            "categories": ["All"],
            "saved_articles": [],
            "read_later": [],
            "bookmarks": []
        })
    
    def save(self):
        """Save preferences"""
        st.session_state.news_preferences[self.user_id] = self.preferences
    
    def toggle_category(self, category):
        """Toggle category preference"""
        if "All" in self.preferences["categories"]:
            self.preferences["categories"] = []
        
        if category in self.preferences["categories"]:
            self.preferences["categories"].remove(category)
        else:
            self.preferences["categories"].append(category)
        
        if not self.preferences["categories"]:
            self.preferences["categories"] = ["All"]
        
        self.save()
    
    def add_bookmark(self, article_id):
        """Add article to bookmarks"""
        if article_id not in self.preferences["bookmarks"]:
            self.preferences["bookmarks"].append(article_id)
            self.save()
            return True
        return False
    
    def remove_bookmark(self, article_id):
        """Remove article from bookmarks"""
        if article_id in self.preferences["bookmarks"]:
            self.preferences["bookmarks"].remove(article_id)
            self.save()
            return True
        return False
    
    def add_read_later(self, article_id):
        """Add article to read later"""
        if article_id not in self.preferences["read_later"]:
            self.preferences["read_later"].append(article_id)
            self.save()
            return True
        return False
    
    def remove_read_later(self, article_id):
        """Remove article from read later"""
        if article_id in self.preferences["read_later"]:
            self.preferences["read_later"].remove(article_id)
            self.save()
            return True
        return False

# ============================================================
# NEWS ANALYTICS
# ============================================================

class NewsAnalytics:
    """News analytics and insights"""
    
    @staticmethod
    def generate_insights(news_list):
        """Generate insights from news"""
        if not news_list:
            return []
        
        insights = []
        
        # Category breakdown
        categories = {}
        for news in news_list:
            cat = news["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        top_category = max(categories.items(), key=lambda x: x[1])
        insights.append(f"📊 Most discussed topic: {top_category[0]} ({top_category[1]} articles)")
        
        # Impact analysis
        impacts = {"Positive": 0, "Negative": 0, "Neutral": 0}
        for news in news_list:
            impacts[news["impact"]] = impacts.get(news["impact"], 0) + 1
        
        if impacts["Positive"] > impacts["Negative"]:
            insights.append("🌱 Positive sustainability news outweighs negative coverage")
        else:
            insights.append("⚠️ More negative news articles than positive ones")
        
        # Total CO2 impact
        total_impact = len(news_list) * 10  # Simulated metric
        insights.append(f"🌍 Collective impact: {total_impact} metric tons of CO2 equivalent")
        
        return insights

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_news():
    """Render the complete eco-news section"""
    st.markdown("<div class='section-header'>📰 Eco-News & Sustainability Updates</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize preferences
    if "news_prefs" not in st.session_state:
        st.session_state.news_prefs = UserNewsPreferences(user_id)
    
    prefs = st.session_state.news_prefs
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📰 Latest News",
        "📊 Analytics",
        "📚 My Library"
    ])
    
    with tab1:
        render_news_feed(prefs)
    
    with tab2:
        render_news_analytics()
    
    with tab3:
        render_news_library(prefs)

def render_news_feed(prefs):
    """Render news feed"""
    st.markdown("### 📰 Latest Sustainability News")
    
    # Category filter
    categories = EcoNewsDatabase.get_categories()
    selected_category = st.selectbox(
        "Filter by Category",
        categories,
        key="news_category_filter"
    )
    
    # Time filter
    time_filters = ["All", "Last 7 Days", "Last 14 Days", "Last 30 Days"]
    time_map = {"All": 365, "Last 7 Days": 7, "Last 14 Days": 14, "Last 30 Days": 30}
    selected_time = st.selectbox("Time Period", time_filters, key="news_time_filter")
    
    # Get news
    days = time_map.get(selected_time, 365)
    news = EcoNewsDatabase.get_news(selected_category, days)
    
    # Display count
    st.caption(f"📰 {len(news)} articles found")
    
    # Display news
    for article in news:
        with st.container():
            # Calculate time ago
            days_ago = (datetime.now() - article["date"]).days
            time_str = f"{days_ago} days ago" if days_ago > 0 else "Today"
            
            impact_color = "#4ade80" if article["impact"] == "Positive" else "#f87171" if article["impact"] == "Negative" else "#fbbf24"
            
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {impact_color};'>
                <div style='display: flex; align-items: start; gap: 15px;'>
                    <div style='font-size: 32px;'>{article['emoji']}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: start;'>
                            <div>
                                <h4 style='margin: 0; color: #4ade80;'>{article['title']}</h4>
                                <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                    <span>📂 {article['category']}</span>
                                    <span>📅 {time_str}</span>
                                    <span>📰 {article['source']}</span>
                                    <span>⏱️ {article['read_time']} min read</span>
                                    <span style='color: {impact_color};'>
                                        {article['impact']} Impact
                                    </span>
                                </div>
                            </div>
                            <div style='display: flex; gap: 8px;'>
                                <span style='background: #1f2937; padding: 2px 8px; border-radius: 12px; font-size: 11px;'>
                                    {article['tags'][0] if article['tags'] else ''}
                                </span>
                            </div>
                        </div>
                        <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{article['summary']}</p>
                        <div style='display: flex; gap: 10px; margin-top: 8px;'>
                            <button onclick="st.session_state.news_expanded['{article['id']}'] = True" style='background: #4ade80; border: none; padding: 4px 16px; border-radius: 8px; cursor: pointer;'>
                                📖 Read More
                            </button>
                            <button onclick="st.session_state.news_bookmark['{article['id']}'] = True" style='background: transparent; border: 1px solid #4ade80; padding: 4px 16px; border-radius: 8px; cursor: pointer;'>
                                🔖 Save
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Expandable content
            if st.button(f"📖 Read More - {article['title']}", key=f"readmore_{article['id']}"):
                with st.expander("Full Article", expanded=True):
                    st.markdown(article['content'])
                    st.caption(f"Source: {article['source']} • {article['date'].strftime('%B %d, %Y')}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🔖 Bookmark", key=f"bookmark_{article['id']}"):
                            prefs.add_bookmark(article['id'])
                            st.success("✅ Bookmarked!")
                    with col2:
                        if st.button("📅 Read Later", key=f"readlater_{article['id']}"):
                            prefs.add_read_later(article['id'])
                            st.success("✅ Added to read later!")
                    with col3:
                        st.button("🔗 Share", key=f"share_{article['id']}")
            
            st.markdown("---")

def render_news_analytics():
    """Render news analytics"""
    st.markdown("### 📊 News Analytics")
    
    # Category statistics
    category_stats = EcoNewsDatabase.get_category_stats()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Category Distribution")
        
        fig = go.Figure(data=[go.Pie(
            labels=list(category_stats.keys()),
            values=list(category_stats.values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#fbbf24', '#f87171', '#60a5fa', '#a78bfa', '#34d399'])
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🌍 Impact Distribution")
        
        impact_stats = EcoNewsDatabase.get_impact_stats()
        
        fig = go.Figure(data=[go.Bar(
            x=list(impact_stats.keys()),
            y=list(impact_stats.values()),
            marker_color=['#4ade80', '#fbbf24', '#f87171']
        )])
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title="Number of Articles"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    st.markdown("### 💡 News Insights")
    
    all_news = EcoNewsDatabase.get_news()
    insights = NewsAnalytics.generate_insights(all_news)
    
    for insight in insights:
        st.info(insight)
    
    # Trend over time
    st.markdown("### 📈 News Trend")
    
    # Create trend data
    news_dates = {}
    for news in all_news:
        date_key = news["date"].strftime("%Y-%m-%d")
        news_dates[date_key] = news_dates.get(date_key, 0) + 1
    
    if news_dates:
        df_trend = pd.DataFrame(
            list(news_dates.items()),
            columns=["Date", "Count"]
        )
        df_trend['Date'] = pd.to_datetime(df_trend['Date'])
        df_trend = df_trend.sort_values('Date')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_trend['Date'],
            y=df_trend['Count'],
            mode='lines+markers',
            fill='tozeroy',
            name='News Count',
            line=dict(color='#4ade80', width=2)
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title="Articles per Day"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top tags
    st.markdown("### 🏷️ Popular Topics")
    
    all_tags = []
    for news in all_news:
        all_tags.extend(news["tags"])
    
    tag_counts = Counter(all_tags)
    top_tags = tag_counts.most_common(10)
    
    if top_tags:
        tags_df = pd.DataFrame(top_tags, columns=["Topic", "Count"])
        
        fig = go.Figure(data=[go.Bar(
            x=tags_df['Count'],
            y=tags_df['Topic'],
            orientation='h',
            marker_color='#4ade80'
        )])
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis_title="Number of Articles"
        )
        st.plotly_chart(fig, use_container_width=True)

def render_news_library(prefs):
    """Render user's news library"""
    st.markdown("### 📚 My News Library")
    
    # Get all news
    all_news = {n["id"]: n for n in EcoNewsDatabase.get_news()}
    
    # Bookmarks
    st.markdown("#### 🔖 Bookmarks")
    bookmarks = prefs.preferences.get("bookmarks", [])
    
    if bookmarks:
        for article_id in bookmarks:
            article = all_news.get(article_id)
            if article:
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600;'>{article['emoji']} {article['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>{article['source']} • {article['date'].strftime('%b %d, %Y')}</div>
                        </div>
                        <button onclick="st.session_state.remove_bookmark['{article_id}'] = True" style='background: none; border: none; color: #f87171; cursor: pointer;'>
                            ❌
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📖 Read {article['title']}", key=f"lib_read_{article_id}"):
                    with st.expander("Read Article", expanded=True):
                        st.markdown(article['content'])
                
                if st.button(f"🗑️ Remove Bookmark", key=f"lib_remove_{article_id}"):
                    prefs.remove_bookmark(article_id)
                    st.rerun()
    else:
        st.info("📖 No bookmarks yet. Save articles you find interesting!")
    
    # Read Later
    st.markdown("#### 📅 Read Later")
    read_later = prefs.preferences.get("read_later", [])
    
    if read_later:
        for article_id in read_later:
            article = all_news.get(article_id)
            if article:
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600;'>{article['emoji']} {article['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>{article['source']} • {article['date'].strftime('%b %d, %Y')}</div>
                        </div>
                        <button onclick="st.session_state.remove_readlater['{article_id}'] = True" style='background: none; border: none; color: #f87171; cursor: pointer;'>
                            ❌
                        </button>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"📖 Read Now", key=f"rl_read_{article_id}"):
                    with st.expander("Read Article", expanded=True):
                        st.markdown(article['content'])
                
                if st.button(f"✅ Mark as Read", key=f"rl_complete_{article_id}"):
                    prefs.remove_read_later(article_id)
                    st.rerun()
    else:
        st.info("📖 No articles in your read later list")
    
    # Reading statistics
    st.markdown("---")
    st.markdown("#### 📊 Reading Statistics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Bookmarks", len(bookmarks))
    col2.metric("Read Later", len(read_later))
    col3.metric("Total Saved", len(bookmarks) + len(read_later))

# ============================================================
# INTEGRATION
# ============================================================

def render_news_hub():
    """Render the complete news hub"""
    render_eco_news()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_news import render_news_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21 = st.tabs([
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
    "📰 Eco-News"  # NEW
])

with tab21:
    render_news_hub()
"""