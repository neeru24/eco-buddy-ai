
# ============================================================
# FILE: urban_farming.py
# EcoBuddy AI+ Urban Farming & Sustainable City Living
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# PLANT DATABASE
# ============================================================

class UrbanPlantDatabase:
    """Urban-friendly plant database"""
    
    PLANTS = [
        {
            "id": "p1",
            "name": "Tomato",
            "type": "Vegetable",
            "space_required": "Medium",
            "container_size": "5 gallon",
            "sunlight": "Full sun (6-8 hours)",
            "water_needs": "Regular",
            "growing_season": "Spring-Summer",
            "harvest_time": "60-80 days",
            "difficulty": "Easy",
            "indoor_friendly": False,
            "emoji": "🍅",
            "benefits": "Rich in Vitamin C and antioxidants"
        },
        {
            "id": "p2",
            "name": "Lettuce",
            "type": "Vegetable",
            "space_required": "Small",
            "container_size": "1 gallon",
            "sunlight": "Partial shade (4-6 hours)",
            "water_needs": "Regular",
            "growing_season": "Spring-Fall",
            "harvest_time": "40-60 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🥬",
            "benefits": "Low calorie, high in Vitamin A"
        },
        {
            "id": "p3",
            "name": "Basil",
            "type": "Herb",
            "space_required": "Small",
            "container_size": "1 gallon",
            "sunlight": "Full sun (6+ hours)",
            "water_needs": "Moderate",
            "growing_season": "Spring-Summer",
            "harvest_time": "40-60 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🌿",
            "benefits": "Anti-inflammatory properties"
        },
        {
            "id": "p4",
            "name": "Strawberry",
            "type": "Fruit",
            "space_required": "Medium",
            "container_size": "5 gallon",
            "sunlight": "Full sun (6-8 hours)",
            "water_needs": "Regular",
            "growing_season": "Spring-Summer",
            "harvest_time": "90-110 days",
            "difficulty": "Medium",
            "indoor_friendly": False,
            "emoji": "🍓",
            "benefits": "Rich in Vitamin C and manganese"
        },
        {
            "id": "p5",
            "name": "Mint",
            "type": "Herb",
            "space_required": "Small",
            "container_size": "1 gallon",
            "sunlight": "Partial shade (4-6 hours)",
            "water_needs": "High",
            "growing_season": "Spring-Fall",
            "harvest_time": "30-40 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🍃",
            "benefits": "Aids digestion, rich in antioxidants"
        },
        {
            "id": "p6",
            "name": "Pepper",
            "type": "Vegetable",
            "space_required": "Medium",
            "container_size": "5 gallon",
            "sunlight": "Full sun (6-8 hours)",
            "water_needs": "Regular",
            "growing_season": "Spring-Summer",
            "harvest_time": "70-90 days",
            "difficulty": "Medium",
            "indoor_friendly": False,
            "emoji": "🌶️",
            "benefits": "High in Vitamin C and antioxidants"
        },
        {
            "id": "p7",
            "name": "Carrot",
            "type": "Vegetable",
            "space_required": "Small",
            "container_size": "2 gallon",
            "sunlight": "Full sun (6+ hours)",
            "water_needs": "Moderate",
            "growing_season": "Spring-Fall",
            "harvest_time": "70-80 days",
            "difficulty": "Easy",
            "indoor_friendly": False,
            "emoji": "🥕",
            "benefits": "Rich in beta-carotene and fiber"
        },
        {
            "id": "p8",
            "name": "Rosemary",
            "type": "Herb",
            "space_required": "Medium",
            "container_size": "3 gallon",
            "sunlight": "Full sun (6-8 hours)",
            "water_needs": "Low",
            "growing_season": "Spring-Fall",
            "harvest_time": "80-100 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🌿",
            "benefits": "Improves memory and concentration"
        },
        {
            "id": "p9",
            "name": "Kale",
            "type": "Vegetable",
            "space_required": "Medium",
            "container_size": "3 gallon",
            "sunlight": "Full sun to partial shade",
            "water_needs": "Regular",
            "growing_season": "Fall-Spring",
            "harvest_time": "50-70 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🥬",
            "benefits": "Superfood rich in vitamins A, C, K"
        },
        {
            "id": "p10",
            "name": "Lavender",
            "type": "Herb",
            "space_required": "Medium",
            "container_size": "3 gallon",
            "sunlight": "Full sun (6+ hours)",
            "water_needs": "Low",
            "growing_season": "Spring-Summer",
            "harvest_time": "90-120 days",
            "difficulty": "Easy",
            "indoor_friendly": True,
            "emoji": "🌸",
            "benefits": "Stress relief and sleep aid"
        }
    ]
    
    @staticmethod
    def get_plants(plant_type=None, difficulty=None, indoor=False):
        """Get plants with filters"""
        plants = UrbanPlantDatabase.PLANTS.copy()
        if plant_type and plant_type != "All":
            plants = [p for p in plants if p["type"] == plant_type]
        if difficulty and difficulty != "All":
            plants = [p for p in plants if p["difficulty"] == difficulty]
        if indoor:
            plants = [p for p in plants if p["indoor_friendly"]]
        return plants
    
    @staticmethod
    def get_types():
        """Get plant types"""
        return ["All"] + sorted(set(p["type"] for p in UrbanPlantDatabase.PLANTS))
    
    @staticmethod
    def get_difficulties():
        """Get difficulty levels"""
        return ["All"] + sorted(set(p["difficulty"] for p in UrbanPlantDatabase.PLANTS))

# ============================================================
# URBAN GARDEN TRACKER
# ============================================================

class UrbanGardenTracker:
    """Track urban garden progress"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load garden data from session"""
        if "urban_garden" not in st.session_state:
            st.session_state.urban_garden = {}
        return st.session_state.urban_garden.get(self.user_id, {
            "plants": [],
            "harvests": [],
            "space_available": 10,
            "space_used": 0,
            "total_harvest": 0,
            "start_date": datetime.now().isoformat()
        })
    
    def save(self):
        """Save garden data"""
        st.session_state.urban_garden[self.user_id] = self.data
    
    def add_plant(self, plant_id, planting_date=None):
        """Add a plant to garden"""
        plant = next((p for p in UrbanPlantDatabase.PLANTS if p["id"] == plant_id), None)
        if not plant:
            return False
        
        if planting_date is None:
            planting_date = datetime.now()
        
        space_needed = 1 if plant["space_required"] == "Small" else 2 if plant["space_required"] == "Medium" else 3
        
        if self.data["space_used"] + space_needed > self.data["space_available"]:
            return False, "Not enough space"
        
        garden_plant = {
            "plant_id": plant_id,
            "name": plant["name"],
            "planting_date": planting_date.isoformat(),
            "status": "Growing",
            "space_needed": space_needed,
            "harvest_count": 0,
            "notes": []
        }
        
        self.data["plants"].append(garden_plant)
        self.data["space_used"] += space_needed
        self.save()
        return True, "Plant added successfully!"
    
    def harvest_plant(self, plant_index, amount):
        """Harvest from a plant"""
        if plant_index < len(self.data["plants"]):
            plant = self.data["plants"][plant_index]
            plant["harvest_count"] += 1
            plant["status"] = "Growing"  # Reset status
            self.data["total_harvest"] += amount
            self.save()
            return True
        return False
    
    def get_stats(self):
        """Get garden statistics"""
        return {
            "total_plants": len(self.data["plants"]),
            "space_used": self.data["space_used"],
            "space_available": self.data["space_available"],
            "space_remaining": self.data["space_available"] - self.data["space_used"],
            "total_harvest": self.data["total_harvest"],
            "start_date": self.data["start_date"]
        }

# ============================================================
# COMMUNITY GARDEN DATABASE
# ============================================================

class CommunityGardenDatabase:
    """Database of community gardens"""
    
    GARDENS = [
        {
            "id": "g1",
            "name": "Green City Garden",
            "location": "Central District",
            "size": "Large",
            "plots_available": 5,
            "total_plots": 20,
            "features": ["Water access", "Composting", "Tools available"],
            "contact": "community.garden@email.com",
            "active": True,
            "emoji": "🌳"
        },
        {
            "id": "g2",
            "name": "Urban Harvest",
            "location": "East Side",
            "size": "Medium",
            "plots_available": 3,
            "total_plots": 15,
            "features": ["Water access", "Workshop space"],
            "contact": "urban.harvest@email.com",
            "active": True,
            "emoji": "🌿"
        },
        {
            "id": "g3",
            "name": "Rooftop Gardens Initiative",
            "location": "West End",
            "size": "Small",
            "plots_available": 0,
            "total_plots": 10,
            "features": ["Vertical growing", "Composting"],
            "contact": "rooftop.init@email.com",
            "active": True,
            "emoji": "🏙️"
        },
        {
            "id": "g4",
            "name": "Community Food Forest",
            "location": "North District",
            "size": "Large",
            "plots_available": 2,
            "total_plots": 25,
            "features": ["Water access", "Education programs", "Events"],
            "contact": "food.forest@email.com",
            "active": True,
            "emoji": "🌲"
        }
    ]
    
    @staticmethod
    def get_gardens(available_only=False):
        """Get community gardens"""
        gardens = CommunityGardenDatabase.GARDENS.copy()
        if available_only:
            gardens = [g for g in gardens if g["plots_available"] > 0]
        return gardens
    
    @staticmethod
    def get_garden(garden_id):
        """Get specific garden"""
        for garden in CommunityGardenDatabase.GARDENS:
            if garden["id"] == garden_id:
                return garden
        return None

# ============================================================
# CITY SUSTAINABILITY TIPS
# ============================================================

class CitySustainabilityTips:
    """Tips for sustainable city living"""
    
    TIPS = {
        "Transportation": [
            "🚲 Bike or walk for short trips",
            "🚌 Use public transportation",
            "🚗 Carpool with neighbors",
            "⚡ Consider electric vehicles"
        ],
        "Energy": [
            "💡 Use LED bulbs throughout your home",
            "🔌 Unplug electronics when not in use",
            "🌡️ Use programmable thermostats",
            "☀️ Install solar panels if possible"
        ],
        "Water": [
            "💧 Install low-flow showerheads",
            "🚿 Take shorter showers",
            "🌧️ Collect rainwater for plants",
            "🔧 Fix leaky faucets immediately"
        ],
        "Waste": [
            "♻️ Recycle all recyclable materials",
            "🧑‍🌾 Start a compost bin",
            "🛍️ Use reusable shopping bags",
            "📦 Buy in bulk to reduce packaging"
        ],
        "Food": [
            "🌱 Grow your own herbs and vegetables",
            "🥗 Buy locally sourced food",
            "♻️ Reduce food waste",
            "🌿 Support urban farms"
        ]
    }
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category and category != "All":
            return CitySustainabilityTips.TIPS.get(category, [])
        all_tips = []
        for tips in CitySustainabilityTips.TIPS.values():
            all_tips.extend(tips)
        return all_tips
    
    @staticmethod
    def get_categories():
        """Get tip categories"""
        return ["All"] + list(CitySustainabilityTips.TIPS.keys())

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_urban_farming():
    """Render the complete urban farming hub"""
    st.markdown("<div class='section-header'>🌱 Urban Farming & Sustainable City Living</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize garden tracker
    if "urban_garden_tracker" not in st.session_state:
        st.session_state.urban_garden_tracker = UrbanGardenTracker(user_id)
    
    tracker = st.session_state.urban_garden_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌿 Plant Guide",
        "🌱 My Urban Garden",
        "🏙️ City Living Tips",
        "🌳 Community Gardens",
        "📊 Dashboard"
    ])
    
    with tab1:
        render_plant_guide(tracker)
    
    with tab2:
        render_urban_garden(tracker)
    
    with tab3:
        render_city_tips()
    
    with tab4:
        render_community_gardens()
    
    with tab5:
        render_urban_dashboard(tracker)

def render_plant_guide(tracker):
    """Render plant guide"""
    st.markdown("### 🌿 Urban Plant Guide")
    
    st.markdown("""
    <div class='subtitle'>
        Find plants perfect for urban living
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        plant_types = UrbanPlantDatabase.get_types()
        selected_type = st.selectbox("Plant Type", plant_types)
    
    with col2:
        difficulties = UrbanPlantDatabase.get_difficulties()
        selected_difficulty = st.selectbox("Difficulty", difficulties)
    
    with col3:
        indoor_friendly = st.checkbox("Indoor Friendly Only")
    
    # Get plants
    plants = UrbanPlantDatabase.get_plants(selected_type, selected_difficulty, indoor_friendly)
    
    # Search
    search = st.text_input("🔍 Search Plants", placeholder="Search by name...")
    if search:
        plants = [p for p in plants if search.lower() in p["name"].lower()]
    
    st.caption(f"🌿 {len(plants)} plants found")
    
    # Display plants
    for plant in plants:
        difficulty_colors = {"Easy": "#4ade80", "Medium": "#fbbf24", "Hard": "#f87171"}
        color = difficulty_colors.get(plant["difficulty"], "#6b7280")
        
        in_garden = any(p["plant_id"] == plant["id"] for p in tracker.data["plants"])
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {color};'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{plant['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <div style='font-weight: 700;'>{plant['name']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {plant['type']} • {plant['difficulty']} • {plant['space_required']} space
                            </div>
                        </div>
                        <span style='background: {color}; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;'>
                            {plant['difficulty']}
                        </span>
                    </div>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px;'>
                        <span>📏 {plant['container_size']}</span>
                        <span>☀️ {plant['sunlight']}</span>
                        <span>💧 {plant['water_needs']}</span>
                        <span>🌱 {plant['growing_season']}</span>
                    </div>
                    <div style='font-size: 12px; color: #4ade80;'>
                        💚 {plant['benefits']}
                        {f' • 🏠 Indoor Friendly' if plant['indoor_friendly'] else ''}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if not in_garden:
                if st.button(f"🌱 Add", key=f"add_{plant['id']}"):
                    success, message = tracker.add_plant(plant["id"])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.warning(message)
            else:
                st.button("✅ In Garden", key=f"added_{plant['id']}", disabled=True)
        
        with col2:
            if st.button(f"📖 Details", key=f"details_{plant['id']}"):
                with st.expander("Growing Guide", expanded=True):
                    st.markdown(f"**Name:** {plant['name']}")
                    st.markdown(f"**Type:** {plant['type']}")
                    st.markdown(f"**Difficulty:** {plant['difficulty']}")
                    st.markdown(f"**Space Required:** {plant['space_required']}")
                    st.markdown(f"**Container Size:** {plant['container_size']}")
                    st.markdown(f"**Sunlight:** {plant['sunlight']}")
                    st.markdown(f"**Water Needs:** {plant['water_needs']}")
                    st.markdown(f"**Growing Season:** {plant['growing_season']}")
                    st.markdown(f"**Harvest Time:** {plant['harvest_time']}")
                    st.markdown(f"**Benefits:** {plant['benefits']}")
                    st.markdown(f"**Indoor Friendly:** {'Yes' if plant['indoor_friendly'] else 'No'}")
        
        st.markdown("---")

def render_urban_garden(tracker):
    """Render urban garden"""
    st.markdown("### 🌱 My Urban Garden")
    
    stats = tracker.get_stats()
    
    # Space overview
    col1, col2, col3 = st.columns(3)
    col1.metric("Plants", stats["total_plants"])
    col2.metric("Space Used", f"{stats['space_used']}/{stats['space_available']} units")
    col3.metric("Total Harvest", f"{stats['total_harvest']:.1f} kg")
    
    st.progress(stats['space_used'] / stats['space_available'] if stats['space_available'] > 0 else 0)
    st.caption(f"{stats['space_remaining']} units available")
    
    st.markdown("---")
    
    # Garden plants
    if tracker.data["plants"]:
        st.markdown("#### 🌿 Your Plants")
        
        for i, plant_data in enumerate(tracker.data["plants"]):
            plant = next((p for p in UrbanPlantDatabase.PLANTS if p["id"] == plant_data["plant_id"]), None)
            if plant:
                planting_date = datetime.fromisoformat(plant_data["planting_date"]).strftime("%b %d, %Y")
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600;'>{plant['emoji']} {plant['name']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                Planted: {planting_date} • Status: {plant_data['status']}
                            </div>
                            <div style='font-size: 12px; color: #4ade80;'>
                                Harvests: {plant_data['harvest_count']}
                            </div>
                        </div>
                        <div style='display: flex; gap: 10px;'>
                            <button onclick="st.session_state.harvest_{i} = True" style='background: #4ade80; border: none; padding: 4px 12px; border-radius: 8px; cursor: pointer;'>
                                🌾 Harvest
                            </button>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🌾 Harvest {plant['name']}", key=f"harvest_{i}"):
                    tracker.harvest_plant(i, random.uniform(0.5, 2.0))
                    st.success("✅ Harvested successfully!")
                    st.rerun()
                
                if st.button(f"📝 Add Note", key=f"note_{i}"):
                    note = st.text_input(f"Note for {plant['name']}", key=f"note_input_{i}")
                    if note:
                        plant_data["notes"].append(note)
                        tracker.save()
                        st.success("✅ Note added!")
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info("🌱 Your garden is empty. Add plants from the Plant Guide!")
        
        # Quick start suggestions
        st.markdown("#### 💡 Quick Start Suggestions")
        suggestions = ["Lettuce", "Basil", "Mint", "Tomato"]
        cols = st.columns(4)
        for i, plant_name in enumerate(suggestions):
            plant = next((p for p in UrbanPlantDatabase.PLANTS if p["name"] == plant_name), None)
            if plant:
                with cols[i]:
                    if st.button(f"🌱 Add {plant_name}", key=f"quick_{plant_name}"):
                        success, message = tracker.add_plant(plant["id"])
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.warning(message)

def render_city_tips():
    """Render city living tips"""
    st.markdown("### 🏙️ Sustainable City Living Tips")
    
    # Category filter
    categories = CitySustainabilityTips.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    tips = CitySustainabilityTips.get_tips(selected_category)
    
    # Display tips
    cols = st.columns(2)
    for i, tip in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class='card' style='height: 100%;'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='font-size: 20px;'>💚</div>
                    <div style='font-size: 14px;'>{tip}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Challenge of the day
    st.markdown("---")
    st.markdown("#### 🎯 Challenge of the Day")
    
    daily_challenges = [
        "🚲 Bike or walk for your next short trip",
        "💡 Turn off lights in empty rooms all day",
        "♻️ Collect and sort all recyclables for the week",
        "🌱 Plant an herb in a small container",
        "💧 Track your water usage and try to reduce by 10%"
    ]
    
    challenge = random.choice(daily_challenges)
    st.markdown(f"""
    <div class='card-highlight' style='text-align: center;'>
        <div style='font-size: 32px;'>🏆</div>
        <h4 style='color: #4ade80;'>Today's Challenge</h4>
        <p style='font-size: 18px;'>{challenge}</p>
    </div>
    """, unsafe_allow_html=True)

def render_community_gardens():
    """Render community gardens"""
    st.markdown("### 🌳 Community Gardens")
    
    st.markdown("""
    <div class='subtitle'>
        Connect with local urban gardening communities
    </div>
    """, unsafe_allow_html=True)
    
    # Filter
    available_only = st.checkbox("Show Only Gardens with Available Plots")
    
    gardens = CommunityGardenDatabase.get_gardens(available_only)
    
    for garden in gardens:
        availability_color = "#4ade80" if garden["plots_available"] > 0 else "#f87171"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 24px;'>{garden['emoji']}</span>
                        <div>
                            <div style='font-weight: 700; font-size: 16px;'>{garden['name']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>{garden['location']} • {garden['size']} garden</div>
                        </div>
                    </div>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{feature}</span>' for feature in garden['features']])}
                    </div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        📞 Contact: {garden['contact']}
                    </div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 20px; font-weight: 700; color: {availability_color};'>
                        {garden['plots_available']}/{garden['total_plots']}
                    </div>
                    <div style='font-size: 12px; color: #6b7280;'>Plots Available</div>
                    {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;">Active</span>' if garden['active'] else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if garden["plots_available"] > 0:
            if st.button(f"🌱 Request Plot at {garden['name']}", key=f"plot_{garden['id']}"):
                st.success(f"✅ Request sent to {garden['name']}! The community will contact you.")
        
        st.markdown("---")
    
    # Add a garden
    st.markdown("#### ➕ Add Your Community Garden")
    
    with st.form("add_garden_form"):
        col1, col2 = st.columns(2)
        with col1:
            garden_name = st.text_input("Garden Name")
            garden_location = st.text_input("Location")
            garden_size = st.selectbox("Size", ["Small", "Medium", "Large"])
        with col2:
            garden_plots = st.number_input("Total Plots", min_value=1, value=10)
            garden_contact = st.text_input("Contact Email")
            garden_features = st.text_input("Features (comma-separated)")
        
        if st.form_submit_button("Add Garden"):
            if garden_name and garden_location and garden_contact:
                st.success("✅ Community garden added successfully!")
                st.rerun()
            else:
                st.warning("Please fill in all required fields")

def render_urban_dashboard(tracker):
    """Render urban dashboard"""
    st.markdown("### 📊 Urban Farming Dashboard")
    
    stats = tracker.get_stats()
    
    # Overall score
    garden_score = min(100, (stats["total_plants"] * 5) + (stats["total_harvest"] * 2))
    
    st.markdown("#### 🏆 Urban Garden Score")
    st.progress(garden_score / 100)
    st.caption(f"{garden_score:.0f}/100 - {'Urban Farmer' if garden_score > 70 else 'Growing' if garden_score > 40 else 'Just Started'}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Plants", stats["total_plants"])
    col2.metric("Space Usage", f"{stats['space_used']}/{stats['space_available']}")
    col3.metric("Total Harvest", f"{stats['total_harvest']:.1f} kg")
    col4.metric("Space Remaining", stats["space_remaining"])
    
    # Plant type distribution
    if tracker.data["plants"]:
        st.markdown("#### 🌿 Plant Type Distribution")
        
        type_counts = {}
        for plant_data in tracker.data["plants"]:
            plant = next((p for p in UrbanPlantDatabase.PLANTS if p["id"] == plant_data["plant_id"]), None)
            if plant:
                type_counts[plant["type"]] = type_counts.get(plant["type"], 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Monthly harvest trend
    st.markdown("#### 📈 Harvest Trend")
    
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    harvest_data = [random.uniform(0, 5) for _ in range(12)]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months,
        y=harvest_data,
        mode='lines+markers',
        fill='tozeroy',
        line=dict(color='#4ade80', width=2),
        name='Harvest (kg)'
    ))
    fig.update_layout(
        height=250,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_title="Harvest (kg)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    
    if stats["total_plants"] < 3:
        st.info("🌱 Add more plants to diversify your urban garden")
    elif stats["space_remaining"] > 0:
        st.info("🌿 You have space for more plants - consider adding herbs or vegetables")
    
    if stats["total_harvest"] < 2:
        st.info("🌾 Start harvesting regularly to enjoy the fruits of your labor")
    
    if len(tracker.data["plants"]) > 0 and all(p["harvest_count"] == 0 for p in tracker.data["plants"]):
        st.info("🌱 Your first harvest is coming soon - be patient and consistent!")

# ============================================================
# INTEGRATION
# ============================================================

def render_urban_hub():
    """Render the complete urban hub"""
    render_urban_farming()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from urban_farming import render_urban_hub

# Add as a new tab
with tab41:
    render_urban_hub()
"""