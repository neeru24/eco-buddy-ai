
# ============================================================
# FILE: community_marketplace.py
# EcoBuddy AI+ Community Marketplace & Sustainable Exchange
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import hashlib

# ============================================================
# MARKETPLACE DATABASE
# ============================================================

class MarketplaceDatabase:
    """Database of community listings and exchanges"""
    
    LISTINGS = [
        {
            "id": "l1",
            "user": "EcoWarrior",
            "title": "Gardening Tools Set",
            "category": "Garden",
            "condition": "Good",
            "description": "Complete set of gardening tools - gently used",
            "type": "Free",
            "location": "Central Park Area",
            "posted": datetime.now() - timedelta(days=2),
            "image": "🌱",
            "status": "available"
        },
        {
            "id": "l2",
            "user": "GreenGuru",
            "title": "Bicycle - Commuter",
            "category": "Transport",
            "condition": "Like New",
            "description": "7-speed commuter bike, perfect for daily use",
            "type": "Swap",
            "location": "Downtown",
            "posted": datetime.now() - timedelta(days=5),
            "image": "🚲",
            "status": "available"
        },
        {
            "id": "l3",
            "user": "SustainabilityStar",
            "title": "Glass Storage Containers",
            "category": "Kitchen",
            "condition": "Excellent",
            "description": "Set of 12 glass containers with lids",
            "type": "Free",
            "location": "East Side",
            "posted": datetime.now() - timedelta(days=1),
            "image": "🍶",
            "status": "available"
        },
        {
            "id": "l4",
            "user": "EcoChampion",
            "title": "Solar Panel - Portable",
            "category": "Energy",
            "condition": "Good",
            "description": "50W portable solar panel for camping",
            "type": "Swap",
            "location": "West End",
            "posted": datetime.now() - timedelta(days=7),
            "image": "☀️",
            "status": "available"
        },
        {
            "id": "l5",
            "user": "GreenThumb",
            "title": "Plant Collection",
            "category": "Garden",
            "condition": "Very Good",
            "description": "Various indoor plants - great for beginners",
            "type": "Free",
            "location": "North District",
            "posted": datetime.now() - timedelta(days=3),
            "image": "🌿",
            "status": "available"
        },
        {
            "id": "l6",
            "user": "ZeroWasteHero",
            "title": "Reusable Shopping Bags",
            "category": "Kitchen",
            "condition": "New",
            "description": "10 reusable canvas shopping bags",
            "type": "Free",
            "location": "South Side",
            "posted": datetime.now() - timedelta(days=4),
            "image": "🛍️",
            "status": "available"
        },
        {
            "id": "l7",
            "user": "ClimateAction",
            "title": "Electric Scooter",
            "category": "Transport",
            "condition": "Like New",
            "description": "Electric scooter with 25km range",
            "type": "Swap",
            "location": "Central",
            "posted": datetime.now() - timedelta(days=10),
            "image": "🛴",
            "status": "available"
        }
    ]
    
    WISHLIST = [
        {
            "id": "w1",
            "user": "EcoLearner",
            "item": "Books on Sustainability",
            "category": "Education",
            "description": "Looking for used sustainability books",
            "posted": datetime.now() - timedelta(days=1)
        },
        {
            "id": "w2",
            "user": "PlanetProtector",
            "item": "Seedlings for Garden",
            "category": "Garden",
            "description": "Need vegetable seedlings for community garden",
            "posted": datetime.now() - timedelta(days=3)
        },
        {
            "id": "w3",
            "user": "EcoWarrior",
            "item": "Bicycle Helmet",
            "category": "Transport",
            "description": "Used bicycle helmet in good condition",
            "posted": datetime.now() - timedelta(days=5)
        }
    ]
    
    @staticmethod
    def get_listings(category=None, type_filter=None):
        """Get listings with filters"""
        listings = MarketplaceDatabase.LISTINGS.copy()
        if category and category != "All":
            listings = [l for l in listings if l["category"] == category]
        if type_filter and type_filter != "All":
            listings = [l for l in listings if l["type"] == type_filter]
        return sorted(listings, key=lambda x: x["posted"], reverse=True)
    
    @staticmethod
    def get_wishlist(category=None):
        """Get wishlist items with filters"""
        wishlist = MarketplaceDatabase.WISHLIST.copy()
        if category and category != "All":
            wishlist = [w for w in wishlist if w["category"] == category]
        return sorted(wishlist, key=lambda x: x["posted"], reverse=True)
    
    @staticmethod
    def get_categories():
        """Get listing categories"""
        return ["All"] + sorted(set(l["category"] for l in MarketplaceDatabase.LISTINGS))
    
    @staticmethod
    def get_types():
        """Get listing types"""
        return ["All", "Free", "Swap", "Rent"]
    
    @staticmethod
    def add_listing(title, category, condition, description, listing_type, location, image):
        """Add a new listing"""
        listing = {
            "id": f"l{len(MarketplaceDatabase.LISTINGS) + 1}",
            "user": st.session_state.get("username", "Community Member"),
            "title": title,
            "category": category,
            "condition": condition,
            "description": description,
            "type": listing_type,
            "location": location,
            "posted": datetime.now(),
            "image": image,
            "status": "available"
        }
        MarketplaceDatabase.LISTINGS.append(listing)
        return listing

# ============================================================
# COMMUNITY POINTS SYSTEM
# ============================================================

class CommunityPoints:
    """Reward system for marketplace participation"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.points = self._load_points()
    
    def _load_points(self):
        """Load points from session"""
        if "community_points" not in st.session_state:
            st.session_state.community_points = {}
        return st.session_state.community_points.get(self.user_id, {
            "total": 0,
            "listings": 0,
            "exchanges": 0,
            "helpful": 0,
            "reputation": 0
        })
    
    def save(self):
        """Save points"""
        st.session_state.community_points[self.user_id] = self.points
    
    def add_listing_points(self):
        """Add points for creating a listing"""
        self.points["total"] += 10
        self.points["listings"] += 1
        self.save()
        return 10
    
    def add_exchange_points(self):
        """Add points for completing an exchange"""
        self.points["total"] += 20
        self.points["exchanges"] += 1
        self.save()
        return 20
    
    def add_helpful_points(self):
        """Add points for being helpful"""
        self.points["total"] += 5
        self.points["helpful"] += 1
        self.save()
        return 5
    
    def get_level(self):
        """Get user level based on points"""
        points = self.points["total"]
        if points >= 500:
            return {"name": "Eco Master", "emoji": "🏆", "color": "#fbbf24"}
        elif points >= 200:
            return {"name": "Eco Supporter", "emoji": "🌟", "color": "#4ade80"}
        elif points >= 50:
            return {"name": "Eco Contributor", "emoji": "🌿", "color": "#60a5fa"}
        else:
            return {"name": "Eco Beginner", "emoji": "🌱", "color": "#a78bfa"}

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_community_marketplace():
    """Render the complete community marketplace"""
    st.markdown("<div class='section-header'>🔄 Community Marketplace & Sustainable Exchange</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize points system
    if "community_points" not in st.session_state:
        st.session_state.community_points = CommunityPoints(user_id)
    
    points = st.session_state.community_points
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Browse Listings",
        "✨ Add Listing",
        "💚 Wishlist",
        "🏆 Community Points"
    ])
    
    with tab1:
        render_browse_listings(points)
    
    with tab2:
        render_add_listing(points)
    
    with tab3:
        render_wishlist()
    
    with tab4:
        render_points_dashboard(points)

def render_browse_listings(points):
    """Render browse listings"""
    st.markdown("### 📋 Browse Available Items")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = MarketplaceDatabase.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        types = MarketplaceDatabase.get_types()
        selected_type = st.selectbox("Type", types)
    
    with col3:
        search = st.text_input("🔍 Search", placeholder="Search items...")
    
    # Get listings
    listings = MarketplaceDatabase.get_listings(selected_category, selected_type)
    
    if search:
        listings = [l for l in listings if search.lower() in l["title"].lower() or search.lower() in l["description"].lower()]
    
    st.caption(f"📋 {len(listings)} items found")
    
    # Display listings
    for listing in listings:
        days_ago = (datetime.now() - listing["posted"]).days
        time_str = f"{days_ago} days ago" if days_ago > 0 else "Today"
        
        type_colors = {
            "Free": "#4ade80",
            "Swap": "#fbbf24",
            "Rent": "#60a5fa"
        }
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 48px;'>{listing['image']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{listing['title']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>👤 {listing['user']}</span>
                                <span>📂 {listing['category']}</span>
                                <span>📅 {time_str}</span>
                                <span>📍 {listing['location']}</span>
                                <span>🏷️ {listing['condition']}</span>
                            </div>
                        </div>
                        <span style='background: {type_colors.get(listing["type"], "#6b7280")}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 13px;'>
                            {listing['type']}
                        </span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{listing['description']}</p>
                    <div style='display: flex; gap: 10px;'>
                        <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;'>
                            {listing['status']}
                        </span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button(f"📩 Contact", key=f"contact_{listing['id']}"):
                st.success(f"✅ Message sent to {listing['user']}!")
        
        with col2:
            if st.button(f"💚 Interested", key=f"interest_{listing['id']}"):
                points.add_helpful_points()
                st.success("✅ Interest noted! Points +5")
                st.rerun()
        
        st.markdown("---")

def render_add_listing(points):
    """Render add listing form"""
    st.markdown("### ✨ Share an Item")
    
    st.markdown("""
    <div class='subtitle'>
        Give items a new life by sharing with your community
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("add_listing_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Item Title", placeholder="e.g., Gardening Tools Set")
            category = st.selectbox("Category", ["Garden", "Kitchen", "Transport", "Energy", "Education", "Other"])
            condition = st.selectbox("Condition", ["New", "Like New", "Excellent", "Good", "Fair"])
        
        with col2:
            listing_type = st.selectbox("Type", ["Free", "Swap", "Rent"])
            location = st.text_input("Location", placeholder="Neighborhood or area")
            image = st.selectbox("Emoji", ["🌱", "🚲", "🍶", "☀️", "🌿", "🛍️", "🛴", "📚", "💻", "🎨"])
        
        description = st.text_area("Description", placeholder="Describe your item...", height=100)
        
        if st.form_submit_button("📤 Share Item", use_container_width=True):
            if title and description and location:
                points.add_listing_points()
                MarketplaceDatabase.add_listing(
                    title, category, condition, description,
                    listing_type, location, image
                )
                st.success("✅ Item shared successfully! +10 points")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please fill in all required fields")

def render_wishlist():
    """Render wishlist"""
    st.markdown("### 💚 Community Wishlist")
    
    # Categories
    categories = ["All"] + sorted(set(w["category"] for w in MarketplaceDatabase.WISHLIST))
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get wishlist
    wishlist = MarketplaceDatabase.get_wishlist(selected_category)
    
    st.caption(f"📋 {len(wishlist)} requests")
    
    # Display wishlist
    for item in wishlist:
        days_ago = (datetime.now() - item["posted"]).days
        time_str = f"{days_ago} days ago" if days_ago > 0 else "Today"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>📌 {item['item']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        👤 {item['user']} • 📂 {item['category']} • 📅 {time_str}
                    </div>
                    <div style='font-size: 14px; color: #6b7280;'>{item['description']}</div>
                </div>
                <div>
                    <span style='background: #fbbf24; padding: 4px 12px; border-radius: 20px; font-size: 12px; color: #111827;'>
                        Requested
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🤝 Can Help", key=f"help_{item['id']}"):
            st.success(f"✅ You've offered to help {item['user']} with their request!")
    
    # Add to wishlist
    st.markdown("---")
    st.markdown("#### ➕ Add to Wishlist")
    
    with st.form("wishlist_form"):
        wish_item = st.text_input("What are you looking for?", placeholder="e.g., Used bicycle")
        wish_category = st.selectbox("Category", ["Garden", "Kitchen", "Transport", "Energy", "Education", "Other"], key="wish_cat")
        wish_description = st.text_area("Description", placeholder="Describe what you need...")
        
        if st.form_submit_button("📌 Add to Wishlist"):
            if wish_item:
                st.success("✅ Added to wishlist! Community members will see your request.")
                st.rerun()
            else:
                st.warning("Please describe what you need")

def render_points_dashboard(points):
    """Render points dashboard"""
    st.markdown("### 🏆 Community Points Dashboard")
    
    level = points.get_level()
    
    # User level
    st.markdown(f"""
    <div class='card-highlight' style='text-align: center;'>
        <div style='font-size: 48px;'>{level['emoji']}</div>
        <h2 style='color: #4ade80;'>{level['name']}</h2>
        <p style='color: #6b7280;'>Your community impact level</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Points breakdown
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Points", points.points["total"])
    col2.metric("Listings Shared", points.points["listings"])
    col3.metric("Exchanges Made", points.points["exchanges"])
    col4.metric("Helpful Actions", points.points["helpful"])
    
    # Points progress
    st.markdown("#### 📊 Points Progress")
    
    # Calculate progress to next level
    current = points.points["total"]
    next_level = 500 if current < 500 else None
    
    if next_level:
        progress = (current / next_level) * 100
        st.progress(min(progress / 100, 1.0))
        st.caption(f"{current}/{next_level} points to reach Eco Master")
    else:
        st.success("🏆 You've reached the highest level! Keep contributing!")
    
    # Achievements
    st.markdown("#### 🎖️ Achievements")
    
    achievements = []
    if points.points["listings"] >= 1:
        achievements.append("📤 First Share")
    if points.points["exchanges"] >= 1:
        achievements.append("🔄 First Exchange")
    if points.points["helpful"] >= 5:
        achievements.append("🤝 Community Helper")
    if points.points["total"] >= 50:
        achievements.append("🌱 Eco Contributor")
    if points.points["total"] >= 200:
        achievements.append("🌟 Eco Supporter")
    if points.points["total"] >= 500:
        achievements.append("🏆 Eco Master")
    
    if achievements:
        for achievement in achievements:
            st.success(f"✅ {achievement}")
    else:
        st.info("🌟 Start sharing items to earn achievements!")
    
    # Leaderboard
    st.markdown("#### 🏅 Community Leaderboard")
    
    # Simulated leaderboard
    leaderboard = [
        {"user": "EcoWarrior", "points": 450},
        {"user": "GreenGuru", "points": 380},
        {"user": "SustainabilityStar", "points": 320},
        {"user": "EcoChampion", "points": 280},
        {"user": "ZeroWasteHero", "points": 250}
    ]
    
    df_leaderboard = pd.DataFrame(leaderboard)
    
    fig = go.Figure(data=[go.Bar(
        x=df_leaderboard['points'],
        y=df_leaderboard['user'],
        orientation='h',
        marker_color=['#fbbf24', '#fbbf24', '#fbbf24', '#fbbf24', '#fbbf24'],
        text=df_leaderboard['points'],
        textposition='auto'
    )])
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        xaxis_title="Points"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_marketplace_hub():
    """Render the complete marketplace hub"""
    render_community_marketplace()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from community_marketplace import render_marketplace_hub

# Add as a new tab
with tab31:
    render_marketplace_hub()
"""