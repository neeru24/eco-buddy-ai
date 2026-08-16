# ============================================================
# FILE: garden_assistant.py
# EcoBuddy AI+ Eco-Garden & Urban Farming Assistant
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

class PlantDatabase:
    """Database of plants for urban gardening"""
    
    PLANTS = [
        {
            "name": "Tomato",
            "category": "Vegetable",
            "difficulty": "Easy",
            "growing_season": "Spring-Summer",
            "harvest_time": "60-80 days",
            "water_need": "Medium",
            "sunlight": "Full Sun",
            "companion_plants": ["Basil", "Marigold"],
            "co2_absorbed": 5.5,
            "space_required": "2-3 sq ft",
            "health_benefits": "Rich in Vitamin C and antioxidants",
            "emoji": "🍅",
            "tips": "Support with stakes or cages for better growth"
        },
        {
            "name": "Lettuce",
            "category": "Vegetable",
            "difficulty": "Easy",
            "growing_season": "Spring-Fall",
            "harvest_time": "40-60 days",
            "water_need": "High",
            "sunlight": "Partial Shade",
            "companion_plants": ["Carrots", "Radishes"],
            "co2_absorbed": 3.2,
            "space_required": "1-2 sq ft",
            "health_benefits": "Low calorie, high in Vitamin A",
            "emoji": "🥬",
            "tips": "Plant in succession for continuous harvest"
        },
        {
            "name": "Basil",
            "category": "Herb",
            "difficulty": "Easy",
            "growing_season": "Spring-Summer",
            "harvest_time": "40-60 days",
            "water_need": "Medium",
            "sunlight": "Full Sun",
            "companion_plants": ["Tomato", "Pepper"],
            "co2_absorbed": 2.8,
            "space_required": "1 sq ft",
            "health_benefits": "Anti-inflammatory properties",
            "emoji": "🌿",
            "tips": "Pinch flowers to encourage leaf growth"
        },
        {
            "name": "Pepper",
            "category": "Vegetable",
            "difficulty": "Medium",
            "growing_season": "Spring-Summer",
            "harvest_time": "70-90 days",
            "water_need": "Medium",
            "sunlight": "Full Sun",
            "companion_plants": ["Basil", "Onions"],
            "co2_absorbed": 4.8,
            "space_required": "2-3 sq ft",
            "health_benefits": "High in Vitamin C and antioxidants",
            "emoji": "🌶️",
            "tips": "Start seeds indoors 8-10 weeks before last frost"
        },
        {
            "name": "Mint",
            "category": "Herb",
            "difficulty": "Easy",
            "growing_season": "Spring-Fall",
            "harvest_time": "30-40 days",
            "water_need": "High",
            "sunlight": "Partial Shade",
            "companion_plants": ["Cabbage", "Tomato"],
            "co2_absorbed": 2.5,
            "space_required": "1-2 sq ft",
            "health_benefits": "Aids digestion, rich in antioxidants",
            "emoji": "🍃",
            "tips": "Grow in containers to prevent spreading"
        },
        {
            "name": "Carrot",
            "category": "Vegetable",
            "difficulty": "Easy",
            "growing_season": "Spring-Fall",
            "harvest_time": "70-80 days",
            "water_need": "Medium",
            "sunlight": "Full Sun",
            "companion_plants": ["Onions", "Lettuce"],
            "co2_absorbed": 3.5,
            "space_required": "2-3 sq ft",
            "health_benefits": "Rich in beta-carotene and fiber",
            "emoji": "🥕",
            "tips": "Plant in loose, sandy soil for straight roots"
        },
        {
            "name": "Strawberry",
            "category": "Fruit",
            "difficulty": "Medium",
            "growing_season": "Spring-Summer",
            "harvest_time": "90-110 days",
            "water_need": "High",
            "sunlight": "Full Sun",
            "companion_plants": ["Borage", "Lettuce"],
            "co2_absorbed": 4.2,
            "space_required": "2-3 sq ft",
            "health_benefits": "Rich in Vitamin C and manganese",
            "emoji": "🍓",
            "tips": "Use mulch to retain moisture and suppress weeds"
        },
        {
            "name": "Lavender",
            "category": "Herb",
            "difficulty": "Easy",
            "growing_season": "Spring-Summer",
            "harvest_time": "90-120 days",
            "water_need": "Low",
            "sunlight": "Full Sun",
            "companion_plants": ["Rosemary", "Sage"],
            "co2_absorbed": 3.0,
            "space_required": "2-3 sq ft",
            "health_benefits": "Stress relief and sleep aid",
            "emoji": "🌸",
            "tips": "Plant in well-drained soil"
        },
        {
            "name": "Rosemary",
            "category": "Herb",
            "difficulty": "Easy",
            "growing_season": "Spring-Fall",
            "harvest_time": "80-100 days",
            "water_need": "Low",
            "sunlight": "Full Sun",
            "companion_plants": ["Lavender", "Thyme"],
            "co2_absorbed": 3.2,
            "space_required": "2-3 sq ft",
            "health_benefits": "Improves memory and concentration",
            "emoji": "🌿",
            "tips": "Prune regularly to encourage bushiness"
        },
        {
            "name": "Kale",
            "category": "Vegetable",
            "difficulty": "Easy",
            "growing_season": "Fall-Spring",
            "harvest_time": "50-70 days",
            "water_need": "Medium",
            "sunlight": "Full Sun to Partial Shade",
            "companion_plants": ["Beets", "Celery"],
            "co2_absorbed": 4.0,
            "space_required": "2-3 sq ft",
            "health_benefits": "Superfood rich in vitamins A, C, K",
            "emoji": "🥬",
            "tips": "Harvest outer leaves for continuous production"
        }
    ]
    
    @staticmethod
    def get_plants(filters=None):
        """Get plants with filters"""
        plants = PlantDatabase.PLANTS.copy()
        
        if filters:
            if filters.get("category"):
                plants = [p for p in plants if p["category"] == filters["category"]]
            if filters.get("difficulty"):
                plants = [p for p in plants if p["difficulty"] == filters["difficulty"]]
            if filters.get("sunlight"):
                plants = [p for p in plants if p["sunlight"] == filters["sunlight"]]
        
        return plants
    
    @staticmethod
    def get_categories():
        """Get plant categories"""
        return sorted(set(p["category"] for p in PlantDatabase.PLANTS))
    
    @staticmethod
    def get_difficulties():
        """Get difficulty levels"""
        return ["Easy", "Medium", "Hard"]

# ============================================================
# GARDEN PLANNER
# ============================================================

class GardenPlanner:
    """Plan and manage garden layout"""
    
    @staticmethod
    def calculate_space_required(plants_list):
        """Calculate total space needed for plants"""
        total_space = 0
        for plant_name in plants_list:
            plant = next((p for p in PlantDatabase.PLANTS if p["name"] == plant_name), None)
            if plant:
                space = float(plant["space_required"].split()[0])
                total_space += space
        return total_space
    
    @staticmethod
    def calculate_environmental_impact(plants_list):
        """Calculate environmental impact of garden"""
        total_co2 = 0
        total_water = 0
        
        for plant_name in plants_list:
            plant = next((p for p in PlantDatabase.PLANTS if p["name"] == plant_name), None)
            if plant:
                total_co2 += plant["co2_absorbed"]
                if plant["water_need"] == "Low":
                    total_water += 10  # liters per week
                elif plant["water_need"] == "Medium":
                    total_water += 20
                else:
                    total_water += 30
        
        return {
            "co2_absorbed": total_co2,
            "water_needed": total_water,
            "trees_equivalent": total_co2 / 22,
            "food_produced": len(plants_list) * 2  # kg per plant
        }

# ============================================================
# COMPOST CALCULATOR
# ============================================================

class CompostCalculator:
    """Calculate compost requirements and benefits"""
    
    @staticmethod
    def calculate_compost_need(garden_area, soil_type):
        """Calculate compost needed for garden"""
        # Compost application rates (kg per sq ft)
        rates = {
            "Sandy": 2.5,
            "Loamy": 1.5,
            "Clay": 3.0
        }
        
        rate = rates.get(soil_type, 2.0)
        compost_needed = garden_area * rate
        
        # Environmental benefits
        co2_saved = compost_needed * 0.5  # kg CO2 saved per kg compost
        water_saved = compost_needed * 2  # liters saved
        
        return {
            "compost_needed_kg": compost_needed,
            "co2_saved_kg": co2_saved,
            "water_saved_liters": water_saved,
            "soil_improvement": "Good" if soil_type != "Clay" else "Excellent"
        }

# ============================================================
# GARDEN TIPS & GUIDES
# ============================================================

class GardenTips:
    """Garden tips and guides"""
    
    TIPS = [
        {
            "title": "🌱 Start Seeds Indoors",
            "description": "Start seeds 6-8 weeks before planting season",
            "category": "Seeding"
        },
        {
            "title": "💧 Water Deeply",
            "description": "Water deeply and less frequently for stronger roots",
            "category": "Watering"
        },
        {
            "title": "🌿 Companion Planting",
            "description": "Plant companion plants together for natural pest control",
            "category": "Planting"
        },
        {
            "title": "🧑‍🌾 Rotate Crops",
            "description": "Rotate crops each season to prevent soil depletion",
            "category": "Planning"
        },
        {
            "title": "♻️ Start Composting",
            "description": "Start a compost bin for organic garden waste",
            "category": "Waste"
        },
        {
            "title": "🐝 Attract Pollinators",
            "description": "Plant flowers to attract bees and butterflies",
            "category": "Biodiversity"
        },
        {
            "title": "🌾 Use Mulch",
            "description": "Apply mulch to retain moisture and suppress weeds",
            "category": "Care"
        },
        {
            "title": "💡 Grow Vertical",
            "description": "Use vertical space to maximize garden area",
            "category": "Space"
        }
    ]
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category:
            return [t for t in GardenTips.TIPS if t["category"] == category]
        return GardenTips.TIPS
    
    @staticmethod
    def get_categories():
        """Get tip categories"""
        return sorted(set(t["category"] for t in GardenTips.TIPS))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_garden_assistant():
    """Render the complete garden assistant"""
    st.markdown("<div class='section-header'>🌱 Eco-Garden & Urban Farming</div>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 Plant Guide",
        "📐 Garden Planner",
        "🧑‍🌾 Composting",
        "💡 Garden Tips"
    ])
    
    with tab1:
        render_plant_guide()
    
    with tab2:
        render_garden_planner()
    
    with tab3:
        render_composting_tool()
    
    with tab4:
        render_garden_tips()

def render_plant_guide():
    """Render plant guide"""
    st.markdown("### 🌿 Plant Guide")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All"] + PlantDatabase.get_categories()
        )
    
    with col2:
        difficulty_filter = st.selectbox(
            "Difficulty",
            ["All"] + PlantDatabase.get_difficulties()
        )
    
    with col3:
        search = st.text_input("🔍 Search Plant", placeholder="Type plant name...")
    
    # Get filtered plants
    filters = {}
    if category_filter != "All":
        filters["category"] = category_filter
    if difficulty_filter != "All":
        filters["difficulty"] = difficulty_filter
    
    plants = PlantDatabase.get_plants(filters)
    
    # Search filter
    if search:
        plants = [p for p in plants if search.lower() in p["name"].lower()]
    
    # Display plants
    if plants:
        for plant in plants:
            with st.expander(f"{plant['emoji']} {plant['name']} - {plant['category']}"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**Difficulty:** {plant['difficulty']}")
                    st.markdown(f"**Growing Season:** {plant['growing_season']}")
                    st.markdown(f"**Harvest Time:** {plant['harvest_time']}")
                    st.markdown(f"**Water Need:** {plant['water_need']}")
                    st.markdown(f"**Sunlight:** {plant['sunlight']}")
                    st.markdown(f"**Space Required:** {plant['space_required']}")
                    st.markdown(f"**Companion Plants:** {', '.join(plant['companion_plants'])}")
                    st.markdown(f"**Health Benefits:** {plant['health_benefits']}")
                
                with col2:
                    st.metric("CO₂ Absorbed", f"{plant['co2_absorbed']} kg/year")
                    st.metric("Trees Equivalent", f"{plant['co2_absorbed']/22:.1f}")
                    
                    st.markdown("**💡 Tip:**")
                    st.info(plant['tips'])
                
                # Add to garden button
                if st.button(f"Add {plant['name']} to Garden", key=f"add_{plant['name']}"):
                    if "garden_plants" not in st.session_state:
                        st.session_state.garden_plants = []
                    if plant['name'] not in st.session_state.garden_plants:
                        st.session_state.garden_plants.append(plant['name'])
                        st.success(f"✅ Added {plant['name']} to your garden!")
                        st.rerun()
    else:
        st.info("No plants found matching your filters")

def render_garden_planner():
    """Render garden planner"""
    st.markdown("### 📐 Plan Your Garden")
    
    # Initialize garden
    if "garden_plants" not in st.session_state:
        st.session_state.garden_plants = []
    
    # Garden size
    col1, col2 = st.columns(2)
    
    with col1:
        garden_area = st.number_input(
            "Garden Area (sq ft)",
            min_value=1,
            value=50,
            step=5
        )
    
    with col2:
        soil_type = st.selectbox(
            "Soil Type",
            ["Loamy", "Sandy", "Clay"]
        )
    
    # Current garden
    st.markdown("### 🌱 Your Garden")
    
    if st.session_state.garden_plants:
        # Show current plants
        col1, col2, col3, col4 = st.columns(4)
        total_plants = len(st.session_state.garden_plants)
        
        # Calculate space needed
        space_needed = GardenPlanner.calculate_space_required(st.session_state.garden_plants)
        
        col1.metric("Total Plants", total_plants)
        col2.metric("Space Used", f"{space_needed:.1f} sq ft")
        col3.metric("Space Available", f"{garden_area - space_needed:.1f} sq ft")
        col4.metric("Utilization", f"{(space_needed/garden_area*100):.1f}%")
        
        # Progress bar for space
        st.progress(min(space_needed / garden_area, 1.0))
        
        # Display plants in a grid
        st.markdown("#### Your Plants")
        cols = st.columns(4)
        for i, plant_name in enumerate(st.session_state.garden_plants):
            plant = next((p for p in PlantDatabase.PLANTS if p["name"] == plant_name), None)
            if plant:
                with cols[i % 4]:
                    st.markdown(f"""
                    <div style='text-align: center; padding: 10px; background: #1f2937; border-radius: 10px;'>
                        <div style='font-size: 32px;'>{plant['emoji']}</div>
                        <div style='font-size: 13px; font-weight: 600;'>{plant['name']}</div>
                        <div style='font-size: 11px; color: #6b7280;'>{plant['category']}</div>
                        <button onclick="st.session_state.garden_plants.remove('{plant['name']}')" style='background: none; border: none; color: #f87171; cursor: pointer;'>❌</button>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Calculate impact
        impact = GardenPlanner.calculate_environmental_impact(st.session_state.garden_plants)
        
        st.markdown("### 🌍 Environmental Impact")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CO₂ Absorbed", f"{impact['co2_absorbed']:.1f} kg/year")
        col2.metric("Water Needed", f"{impact['water_needed']:.0f} L/week")
        col3.metric("Trees Equivalent", f"{impact['trees_equivalent']:.1f}")
        col4.metric("Food Produced", f"{impact['food_produced']:.0f} kg/year")
        
        # Reset garden
        if st.button("🌱 Reset Garden", use_container_width=True):
            st.session_state.garden_plants = []
            st.rerun()
    
    else:
        st.info("🌱 Your garden is empty! Browse the Plant Guide to add plants.")
        
        # Quick add suggestions
        st.markdown("### 💡 Quick Start Suggestions")
        quick_plants = ["Tomato", "Lettuce", "Basil", "Mint"]
        
        cols = st.columns(4)
        for i, plant_name in enumerate(quick_plants):
            plant = next((p for p in PlantDatabase.PLANTS if p["name"] == plant_name), None)
            if plant:
                with cols[i]:
                    if st.button(f"{plant['emoji']} {plant['name']}", key=f"quick_{plant['name']}"):
                        if "garden_plants" not in st.session_state:
                            st.session_state.garden_plants = []
                        if plant['name'] not in st.session_state.garden_plants:
                            st.session_state.garden_plants.append(plant['name'])
                            st.success(f"✅ Added {plant['name']}!")
                            st.rerun()

def render_composting_tool():
    """Render composting tool"""
    st.markdown("### 🧑‍🌾 Composting Calculator")
    
    col1, col2 = st.columns(2)
    
    with col1:
        garden_area = st.number_input(
            "Garden Area (sq ft)",
            min_value=1,
            value=50,
            step=5,
            key="compost_area"
        )
    
    with col2:
        soil_type = st.selectbox(
            "Soil Type",
            ["Loamy", "Sandy", "Clay"],
            key="compost_soil"
        )
    
    if st.button("Calculate Compost Need", use_container_width=True):
        result = CompostCalculator.calculate_compost_need(garden_area, soil_type)
        
        st.markdown("### 📊 Compost Requirements")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Compost Needed", f"{result['compost_needed_kg']:.1f} kg")
        col2.metric("CO₂ Saved", f"{result['co2_saved_kg']:.1f} kg")
        col3.metric("Water Saved", f"{result['water_saved_liters']:.0f} L")
        col4.metric("Soil Improvement", result['soil_improvement'])
        
        st.info("💡 Start composting kitchen scraps and garden waste to create nutrient-rich soil!")
    
    # Composting guide
    st.markdown("---")
    st.markdown("### 🌱 Composting Guide")
    
    with st.expander("📋 What to Compost"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("✅ **Greens (Nitrogen-Rich)**")
            st.markdown("• Fruit and vegetable scraps")
            st.markdown("• Coffee grounds and filters")
            st.markdown("• Tea bags")
            st.markdown("• Grass clippings")
            st.markdown("• Food scraps (no meat or dairy)")
        
        with col2:
            st.markdown("✅ **Browns (Carbon-Rich)**")
            st.markdown("• Dry leaves")
            st.markdown("• Straw and hay")
            st.markdown("• Wood chips")
            st.markdown("• Paper and cardboard")
            st.markdown("• Sawdust")
    
    with st.expander("💡 Composting Tips"):
        tips = [
            "Maintain a 3:1 ratio of browns to greens",
            "Keep compost moist but not wet",
            "Turn compost every 2-3 weeks",
            "Add compost to garden beds 2-3 times per year",
            "Use compost tea as natural fertilizer"
        ]
        for tip in tips:
            st.markdown(f"• {tip}")

def render_garden_tips():
    """Render garden tips"""
    st.markdown("### 💡 Garden Tips & Guides")
    
    # Category filter
    categories = ["All"] + GardenTips.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    if selected_category == "All":
        tips = GardenTips.get_tips()
    else:
        tips = GardenTips.get_tips(selected_category)
    
    # Display tips in cards
    cols = st.columns(2)
    for i, tip in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class='card' style='height: 100%;'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='font-size: 28px;'>{tip['title'].split()[0]}</div>
                    <div>
                        <div style='font-weight: 700; font-size: 16px;'>{tip['title']}</div>
                        <div style='color: #6b7280; font-size: 14px;'>{tip['description']}</div>
                        <div style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px; display: inline-block; margin-top: 6px; color: #4ade80;'>
                            {tip['category']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick tips
    st.markdown("---")
    st.markdown("### 🚀 Quick Garden Actions")
    
    quick_actions = [
        "🌱 Start seeds indoors this week",
        "💧 Set up a drip irrigation system",
        "🧑‍🌾 Add compost to your garden beds",
        "🐝 Plant pollinator-friendly flowers",
        "🌿 Start a vertical garden for herbs"
    ]
    
    for action in quick_actions:
        if st.button(action, use_container_width=True, key=f"action_{action}"):
            st.success(f"✅ Action added to your garden plan! {action}")

# ============================================================
# INTEGRATION
# ============================================================

def render_garden_hub():
    """Render the complete garden hub"""
    render_garden_assistant()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from garden_assistant import render_garden_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15 = st.tabs([
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
    "🌱 Eco-Garden"  # NEW
])

with tab10:
    render_garden_hub()
"""