# ============================================================
# FILE: pet_care.py
# EcoBuddy AI+ Sustainable Pet Care Guide
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# PET FOOD DATABASE
# ============================================================

class PetFoodDatabase:
    """Database of sustainable pet food options"""
    
    FOODS = [
        {
            "name": "Insect-Based Protein",
            "pet_type": "Dog",
            "protein_source": "Insects",
            "sustainability_score": 95,
            "price_range": "$$",
            "description": "Cricket and black soldier fly protein with low environmental impact",
            "carbon_footprint": "Low",
            "water_usage": "Very Low",
            "benefits": ["High protein", "Sustainable", "Hypoallergenic"],
            "emoji": "🐛"
        },
        {
            "name": "Plant-Based Formula",
            "pet_type": "Dog",
            "protein_source": "Plants",
            "sustainability_score": 90,
            "price_range": "$$",
            "description": "Complete nutrition from plant sources with added supplements",
            "carbon_footprint": "Low",
            "water_usage": "Low",
            "benefits": ["Low carbon", "Cruelty-free", "Complete nutrition"],
            "emoji": "🌱"
        },
        {
            "name": "Sustainable Seafood",
            "pet_type": "Cat",
            "protein_source": "Fish",
            "sustainability_score": 80,
            "price_range": "$$$",
            "description": "Certified sustainable wild-caught fish",
            "carbon_footprint": "Medium",
            "water_usage": "Medium",
            "benefits": ["Omega-3 rich", "High quality", "Sustainable"],
            "emoji": "🐟"
        },
        {
            "name": "Lab-Grown Meat",
            "pet_type": "Dog",
            "protein_source": "Cultured",
            "sustainability_score": 85,
            "price_range": "$$$",
            "description": "Cultured meat with significantly lower environmental impact",
            "carbon_footprint": "Low",
            "water_usage": "Low",
            "benefits": ["Carbon-friendly", "No slaughter", "High quality"],
            "emoji": "🧬"
        },
        {
            "name": "Free-Range Poultry",
            "pet_type": "Cat",
            "protein_source": "Poultry",
            "sustainability_score": 70,
            "price_range": "$$",
            "description": "Free-range chicken and turkey from ethical farms",
            "carbon_footprint": "Medium",
            "water_usage": "Medium",
            "benefits": ["Ethical farming", "High quality", "Natural diet"],
            "emoji": "🐓"
        },
        {
            "name": "Insect-Based Formula",
            "pet_type": "Cat",
            "protein_source": "Insects",
            "sustainability_score": 92,
            "price_range": "$$",
            "description": "Cricket and insect protein optimized for cats",
            "carbon_footprint": "Low",
            "water_usage": "Very Low",
            "benefits": ["Sustainable", "High protein", "Eco-friendly"],
            "emoji": "🦗"
        }
    ]
    
    @staticmethod
    def get_foods(pet_type=None):
        """Get foods by pet type"""
        if pet_type:
            return [f for f in PetFoodDatabase.FOODS if f["pet_type"] == pet_type]
        return PetFoodDatabase.FOODS
    
    @staticmethod
    def get_pet_types():
        """Get pet types"""
        return sorted(set(f["pet_type"] for f in PetFoodDatabase.FOODS))

# ============================================================
# PET SUPPLIES DATABASE
# ============================================================

class PetSupplies:
    """Database of sustainable pet supplies"""
    
    SUPPLIES = [
        {
            "name": "Bamboo Poop Bags",
            "category": "Waste",
            "sustainability_score": 95,
            "price_range": "$",
            "description": "Compostable bamboo-based poop bags",
            "emoji": "🟫",
            "saving": "500+ plastic bags/year"
        },
        {
            "name": "Recycled Toy Rope",
            "category": "Toys",
            "sustainability_score": 90,
            "price_range": "$",
            "description": "Toys made from recycled plastic bottles",
            "emoji": "🧸",
            "saving": "50+ bottles per toy"
        },
        {
            "name": "Hemp Collar",
            "category": "Accessories",
            "sustainability_score": 88,
            "price_range": "$$",
            "description": "Durable and biodegradable hemp fiber collar",
            "emoji": "🐾",
            "saving": "Replaces plastic collars"
        },
        {
            "name": "Bamboo Grooming Brush",
            "category": "Grooming",
            "sustainability_score": 92,
            "price_range": "$",
            "description": "Bamboo handle with natural bristles",
            "emoji": "🪥",
            "saving": "Eliminates plastic brushes"
        },
        {
            "name": "Recycled Bedding",
            "category": "Bedding",
            "sustainability_score": 87,
            "price_range": "$$",
            "description": "Pet beds made from recycled materials",
            "emoji": "🛏️",
            "saving": "100+ recycled plastic bottles"
        },
        {
            "name": "Natural Flea Repellent",
            "category": "Health",
            "sustainability_score": 85,
            "price_range": "$$",
            "description": "Chemical-free, plant-based flea prevention",
            "emoji": "🌿",
            "saving": "Reduces chemical exposure"
        }
    ]
    
    @staticmethod
    def get_supplies(category=None):
        """Get supplies by category"""
        if category:
            return [s for s in PetSupplies.SUPPLIES if s["category"] == category]
        return PetSupplies.SUPPLIES
    
    @staticmethod
    def get_categories():
        """Get supply categories"""
        return sorted(set(s["category"] for s in PetSupplies.SUPPLIES))

# ============================================================
# PET FOOTPRINT CALCULATOR
# ============================================================

class PetFootprintCalculator:
    """Calculate pet's carbon footprint"""
    
    @staticmethod
    def calculate_footprint(pet_type, weight_kg, food_type, poop_bags_per_week=14):
        """Calculate pet's annual carbon footprint"""
        
        # Base carbon factors (kg CO2 per year)
        factors = {
            "Dog": 250,
            "Cat": 100
        }
        
        base = factors.get(pet_type, 150)
        
        # Food impact
        food_impact = {
            "Insect-Based Protein": 0.5,
            "Plant-Based Formula": 0.6,
            "Sustainable Seafood": 1.0,
            "Lab-Grown Meat": 0.7,
            "Free-Range Poultry": 1.2,
            "Regular Meat": 1.5,
            "Insect-Based Formula": 0.5
        }
        
        food_multiplier = food_impact.get(food_type, 1.0)
        
        # Size impact
        size_impact = weight_kg / 20  # Average dog 20kg
        
        # Waste impact (poop bags)
        waste_impact = poop_bags_per_week * 52 * 0.01  # Each bag ~0.01kg CO2
        
        total = (base * food_multiplier * size_impact) + waste_impact
        
        return {
            "total_kg": total,
            "food_impact": base * food_multiplier * size_impact,
            "waste_impact": waste_impact,
            "trees_needed": total / 22,
            "equivalent_driving_km": total * 4  # Approximate conversion
        }

# ============================================================
# PET SUSTAINABILITY TIPS
# ============================================================

class PetSustainabilityTips:
    """Tips for sustainable pet care"""
    
    TIPS = {
        "Food": [
            "🌱 Choose plant-based or insect-based pet food",
            "🐟 Look for sustainably sourced fish ingredients",
            "🔄 Buy pet food in bulk to reduce packaging waste",
            "🏠 Consider homemade pet food with organic ingredients"
        ],
        "Waste": [
            "♻️ Use compostable or biodegradable poop bags",
            "🧹 Compost pet waste in designated compost systems",
            "🗑️ Reduce single-use pet products",
            "🔄 Recycle pet product packaging"
        ],
        "Toys": [
            "🧸 Choose toys made from natural or recycled materials",
            "♻️ Repair toys instead of throwing them away",
            "📦 Make DIY toys from household items",
            "🔄 Donate unused toys to shelters"
        ],
        "Grooming": [
            "🌿 Use natural, chemical-free grooming products",
            "🪥 Choose bamboo grooming tools",
            "💧 Bathe pets less frequently to save water",
            "♻️ Recycle grooming product containers"
        ],
        "Health": [
            "🌱 Choose natural flea and tick prevention",
            "🏥 Prevent obesity to reduce health issues",
            "💊 Don't over-medicate unnecessarily",
            "🔄 Recycle pet medicine packaging"
        ]
    }
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category:
            return PetSustainabilityTips.TIPS.get(category, [])
        return PetSustainabilityTips.TIPS
    
    @staticmethod
    def get_categories():
        """Get tip categories"""
        return list(PetSustainabilityTips.TIPS.keys())

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_pet_care():
    """Render the complete pet care guide"""
    st.markdown("<div class='section-header'>🐾 Sustainable Pet Care Guide</div>", unsafe_allow_html=True)
    
    # Introduction
    st.markdown("""
    <div class='subtitle'>
        Make your pet care routine more sustainable - from food to toys to waste management
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🍽️ Pet Food",
        "🛍️ Supplies",
        "👣 Carbon Footprint",
        "💡 Tips",
        "🎯 Action Plan"
    ])
    
    with tab1:
        render_pet_food()
    
    with tab2:
        render_pet_supplies()
    
    with tab3:
        render_pet_footprint()
    
    with tab4:
        render_pet_tips()
    
    with tab5:
        render_pet_action_plan()

def render_pet_food():
    """Render pet food section"""
    st.markdown("### 🍽️ Sustainable Pet Food Options")
    
    # Pet type selector
    pet_type = st.radio("Select Pet Type", ["Dog", "Cat"], horizontal=True)
    
    # Get foods
    foods = PetFoodDatabase.get_foods(pet_type)
    
    st.markdown(f"**Found {len(foods)} sustainable options for {pet_type}s**")
    
    # Display foods
    for food in foods:
        score_color = "#4ade80" if food['sustainability_score'] >= 80 else "#fbbf24" if food['sustainability_score'] >= 70 else "#f87171"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{food['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{food['name']}</h4>
                            <span style='font-size: 13px; color: #6b7280;'>
                                {food['protein_source']} • {food['price_range']}
                            </span>
                        </div>
                        <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                            {food['sustainability_score']}/100
                        </span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{food['description']}</p>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>
                        <span>🌍 Carbon: {food['carbon_footprint']}</span>
                        <span>💧 Water: {food['water_usage']}</span>
                        <span>💚 {' '.join(food['benefits'][:2])}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"✅ Choose {food['name']}", key=f"food_{food['name']}"):
            if "pet_food_choice" not in st.session_state:
                st.session_state.pet_food_choice = []
            if food['name'] not in st.session_state.pet_food_choice:
                st.session_state.pet_food_choice.append(food['name'])
                st.success(f"✅ Added {food['name']} to your pet care plan!")
                st.rerun()

def render_pet_supplies():
    """Render pet supplies section"""
    st.markdown("### 🛍️ Sustainable Pet Supplies")
    
    # Category filter
    categories = ["All"] + PetSupplies.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get supplies
    if selected_category == "All":
        supplies = PetSupplies.get_supplies()
    else:
        supplies = PetSupplies.get_supplies(selected_category)
    
    # Display supplies
    for supply in supplies:
        score_color = "#4ade80" if supply['sustainability_score'] >= 80 else "#fbbf24" if supply['sustainability_score'] >= 70 else "#f87171"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{supply['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h5 style='margin: 0; color: #4ade80;'>{supply['name']}</h5>
                            <span style='font-size: 12px; color: #6b7280;'>{supply['category']} • {supply['price_range']}</span>
                        </div>
                        <span style='background: {score_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827; font-weight: 700;'>
                            {supply['sustainability_score']}/100
                        </span>
                    </div>
                    <p style='font-size: 13px; color: #6b7280; margin: 4px 0;'>{supply['description']}</p>
                    <span style='font-size: 12px; color: #4ade80;'>💚 Saves: {supply['saving']}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"✅ Add {supply['name']}", key=f"supply_{supply['name']}"):
            if "pet_supplies" not in st.session_state:
                st.session_state.pet_supplies = []
            if supply['name'] not in st.session_state.pet_supplies:
                st.session_state.pet_supplies.append(supply['name'])
                st.success(f"✅ Added {supply['name']} to your plan!")
                st.rerun()

def render_pet_footprint():
    """Render pet footprint calculator"""
    st.markdown("### 👣 Calculate Your Pet's Carbon Footprint")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pet_type = st.selectbox("Pet Type", ["Dog", "Cat"])
        weight = st.number_input("Pet Weight (kg)", min_value=1, value=20, step=1)
    
    with col2:
        food_type = st.selectbox(
            "Food Type",
            PetFoodDatabase.get_foods(pet_type) if pet_type else PetFoodDatabase.FOODS,
            format_func=lambda x: x['name'] if isinstance(x, dict) else str(x)
        )
        poop_bags = st.number_input("Poop Bags per Week", min_value=0, value=14, step=1)
    
    if st.button("🐾 Calculate Footprint", type="primary", use_container_width=True):
        food_name = food_type['name'] if isinstance(food_type, dict) else str(food_type)
        
        result = PetFootprintCalculator.calculate_footprint(
            pet_type,
            weight,
            food_name,
            poop_bags
        )
        
        st.markdown("### 📊 Your Pet's Environmental Impact")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Annual CO₂", f"{result['total_kg']:.0f} kg")
        col2.metric("Trees Needed", f"{result['trees_needed']:.1f}")
        col3.metric("Food Impact", f"{result['food_impact']:.0f} kg")
        col4.metric("Waste Impact", f"{result['waste_impact']:.1f} kg")
        
        # Comparison
        st.markdown("#### 🚗 Equivalent Impact")
        st.metric("Equivalent Driving Distance", f"{result['equivalent_driving_km']:.0f} km/year")
        
        # Progress bar
        st.markdown("#### 🌍 Environmental Impact Level")
        impact_percent = min((result['total_kg'] / 500) * 100, 100)
        st.progress(impact_percent / 100)
        
        if impact_percent < 20:
            st.success("🌟 Excellent! Your pet has a very low carbon footprint!")
        elif impact_percent < 40:
            st.info("🌱 Good! Your pet's footprint is below average")
        elif impact_percent < 60:
            st.warning("📊 Average footprint - consider sustainable food choices")
        else:
            st.error("🔴 High footprint - explore sustainable alternatives")
        
        # Recommendations
        st.markdown("#### 💡 Recommendations to Reduce Impact")
        
        tips = []
        if pet_type == "Dog" and weight > 25:
            tips.append("🔄 Consider switching to a lower-impact protein source")
        if poop_bags > 10:
            tips.append("♻️ Switch to compostable poop bags")
        if "Regular Meat" in food_name:
            tips.append("🌱 Try plant-based or insect-based food alternatives")
        
        if tips:
            for tip in tips:
                st.info(tip)
        else:
            st.success("✅ You're already making sustainable choices!")

def render_pet_tips():
    """Render pet sustainability tips"""
    st.markdown("### 💡 Sustainable Pet Care Tips")
    
    # Category filter
    categories = ["All"] + PetSustainabilityTips.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    if selected_category == "All":
        tips = []
        for cat_tips in PetSustainabilityTips.get_tips().values():
            tips.extend(cat_tips)
    else:
        tips = PetSustainabilityTips.get_tips(selected_category)
    
    # Display tips
    cols = st.columns(2)
    for i, tip in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class='card' style='height: 100%;'>
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <div style='font-size: 24px;'>💚</div>
                    <div>
                        <div style='font-size: 14px;'>{tip}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick tips carousel
    st.markdown("---")
    st.markdown("### 🌟 Quick Eco-Pet Actions")
    
    quick_actions = [
        "🐕 Walk your dog instead of driving",
        "🧸 Make DIY toys from old t-shirts",
        "♻️ Recycle pet food cans and packaging",
        "🌿 Grow cat grass instead of buying",
        "💧 Use rainwater for pet water bowls"
    ]
    
    cols = st.columns(3)
    for i, action in enumerate(quick_actions):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background: #1f2937; padding: 12px; border-radius: 10px; text-align: center; margin: 5px 0;'>
                <div style='font-size: 13px;'>{action}</div>
            </div>
            """, unsafe_allow_html=True)

def render_pet_action_plan():
    """Render pet action plan"""
    st.markdown("### 🎯 Your Sustainable Pet Care Plan")
    
    # Get selected items
    foods = st.session_state.get("pet_food_choice", [])
    supplies = st.session_state.get("pet_supplies", [])
    tips = st.session_state.get("pet_tips_tracked", [])
    
    total = len(foods) + len(supplies) + len(tips)
    
    if total > 0:
        st.markdown("#### 📊 Your Progress")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Food Options", len(foods))
        col2.metric("Supplies", len(supplies))
        col3.metric("Tips", len(tips))
        
        # Overall progress
        total_actions = 15  # Approximate total possible
        progress = min((total / total_actions) * 100, 100)
        
        st.markdown("#### Overall Progress")
        st.progress(progress / 100)
        
        # Display checklist
        if foods:
            st.markdown("#### ✅ Sustainable Food Choices")
            for item in foods:
                st.success(f"🍽️ {item}")
        
        if supplies:
            st.markdown("#### ✅ Sustainable Supplies")
            for item in supplies:
                st.success(f"🛍️ {item}")
        
        if tips:
            st.markdown("#### ✅ Tips Implemented")
            for item in tips:
                st.success(f"💡 {item}")
        
        # Achievement level
        achievement_level = "Eco-Pet Champion" if progress >= 80 else "Sustainable Pet Parent" if progress >= 50 else "Pet Eco-Explorer"
        emoji = "🏆" if progress >= 80 else "🌿" if progress >= 50 else "🐾"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='text-align: center;'>
                <div style='font-size: 40px;'>{emoji}</div>
                <h4 style='color: #4ade80;'>{achievement_level}</h4>
                <p style='color: #6b7280;'>Keep adding sustainable pet care actions to level up!</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Reset button
        if st.button("🔄 Reset Pet Plan", use_container_width=True):
            st.session_state.pet_food_choice = []
            st.session_state.pet_supplies = []
            st.session_state.pet_tips_tracked = []
            st.rerun()
    
    else:
        st.info("🐾 Start by adding sustainable food options, supplies, or tips from the other tabs!")

# ============================================================
# INTEGRATION
# ============================================================

def render_pet_hub():
    """Render the complete pet hub"""
    render_pet_care()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from pet_care import render_pet_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19 = st.tabs([
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
    "🐾 Pet Care"  # NEW
])

with tab19:
    render_pet_hub()
"""