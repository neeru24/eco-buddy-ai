# ============================================================
# FILE: home_guide.py
# EcoBuddy AI+ Eco-Home & Sustainable Living Guide
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# SUSTAINABLE HOME TIPS
# ============================================================

class SustainableHomeTips:
    """Tips for making your home more sustainable"""
    
    TIPS = {
        "Energy": [
            {
                "title": "Switch to LED Bulbs",
                "description": "LED bulbs use 75% less energy and last 25 times longer",
                "saving": "$100/year per 10 bulbs",
                "difficulty": "Easy",
                "cost": "$2-5 per bulb",
                "emoji": "💡"
            },
            {
                "title": "Install a Smart Thermostat",
                "description": "Automatically adjusts temperature for optimal efficiency",
                "saving": "$180/year",
                "difficulty": "Medium",
                "cost": "$100-250",
                "emoji": "🌡️"
            },
            {
                "title": "Unplug Phantom Loads",
                "description": "Devices on standby consume up to 10% of home electricity",
                "saving": "$100/year",
                "difficulty": "Easy",
                "cost": "Free",
                "emoji": "🔌"
            },
            {
                "title": "Install Solar Panels",
                "description": "Generate clean energy and reduce electricity bills",
                "saving": "$1,000/year",
                "difficulty": "Hard",
                "cost": "$10,000-20,000",
                "emoji": "☀️"
            },
            {
                "title": "Use Energy-Efficient Appliances",
                "description": "Energy Star rated appliances use 10-50% less energy",
                "saving": "$200-500/year",
                "difficulty": "Medium",
                "cost": "$500-2,000",
                "emoji": "⚡"
            }
        ],
        "Water": [
            {
                "title": "Fix Leaky Faucets",
                "description": "A dripping faucet can waste 20 liters per day",
                "saving": "7,300 liters/year",
                "difficulty": "Easy",
                "cost": "$10-50",
                "emoji": "💧"
            },
            {
                "title": "Install Low-Flow Showerheads",
                "description": "Reduce water usage by 40% without sacrificing pressure",
                "saving": "15,000 liters/year",
                "difficulty": "Easy",
                "cost": "$15-40",
                "emoji": "🚿"
            },
            {
                "title": "Collect Rainwater",
                "description": "Use rain barrels for garden and outdoor needs",
                "saving": "5,000 liters/year",
                "difficulty": "Easy",
                "cost": "$50-150",
                "emoji": "🌧️"
            },
            {
                "title": "Install a Greywater System",
                "description": "Reuse water from sinks and showers for irrigation",
                "saving": "30,000 liters/year",
                "difficulty": "Hard",
                "cost": "$500-2,000",
                "emoji": "♻️"
            }
        ],
        "Waste": [
            {
                "title": "Start Composting",
                "description": "Turn food scraps into nutrient-rich soil",
                "saving": "200kg waste/year",
                "difficulty": "Easy",
                "cost": "$20-100",
                "emoji": "🌱"
            },
            {
                "title": "Use Reusable Bags",
                "description": "Eliminate single-use plastic bags",
                "saving": "500 plastic bags/year",
                "difficulty": "Easy",
                "cost": "$5-15",
                "emoji": "🛍️"
            },
            {
                "title": "Buy in Bulk",
                "description": "Reduce packaging waste and save money",
                "saving": "50% less packaging",
                "difficulty": "Easy",
                "cost": "Varies",
                "emoji": "📦"
            },
            {
                "title": "Repair Instead of Replace",
                "description": "Extend the life of items and reduce waste",
                "saving": "50kg waste/year",
                "difficulty": "Medium",
                "cost": "Varies",
                "emoji": "🔧"
            }
        ],
        "Chemicals": [
            {
                "title": "Use Natural Cleaners",
                "description": "Vinegar, baking soda, and lemon are effective alternatives",
                "saving": "$50/year on cleaners",
                "difficulty": "Easy",
                "cost": "$5-20",
                "emoji": "🧹"
            },
            {
                "title": "Avoid Pesticides",
                "description": "Use natural pest control methods",
                "saving": "Reduced chemical exposure",
                "difficulty": "Medium",
                "cost": "$10-50",
                "emoji": "🐞"
            },
            {
                "title": "Choose Non-Toxic Paints",
                "description": "Low-VOC paints are better for health and environment",
                "saving": "Reduced indoor air pollution",
                "difficulty": "Easy",
                "cost": "$30-60/gallon",
                "emoji": "🎨"
            }
        ],
        "Indoor Air": [
            {
                "title": "Add Indoor Plants",
                "description": "Plants naturally purify indoor air",
                "saving": "25% less indoor pollutants",
                "difficulty": "Easy",
                "cost": "$10-50",
                "emoji": "🌿"
            },
            {
                "title": "Use an Air Purifier",
                "description": "Remove pollutants and allergens from indoor air",
                "saving": "Improved air quality",
                "difficulty": "Easy",
                "cost": "$100-500",
                "emoji": "🌀"
            },
            {
                "title": "Open Windows Daily",
                "description": "Fresh air circulation reduces indoor pollutants",
                "saving": "Free",
                "difficulty": "Easy",
                "cost": "Free",
                "emoji": "🪟"
            }
        ]
    }
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category:
            return SustainableHomeTips.TIPS.get(category, [])
        return SustainableHomeTips.TIPS
    
    @staticmethod
    def get_categories():
        """Get all categories"""
        return list(SustainableHomeTips.TIPS.keys())
    
    @staticmethod
    def get_random_tip():
        """Get a random tip"""
        all_tips = []
        for tips in SustainableHomeTips.TIPS.values():
            all_tips.extend(tips)
        return random.choice(all_tips)

# ============================================================
# HOME ENERGY AUDIT
# ============================================================

class HomeEnergyAudit:
    """Simple home energy audit tool"""
    
    @staticmethod
    def calculate_savings(actions):
        """Calculate potential savings from energy actions"""
        savings = {
            "LED Bulbs": 100,
            "Smart Thermostat": 180,
            "Unplug Phantom Loads": 100,
            "Solar Panels": 1000,
            "Energy-Efficient Appliances": 350,
            "Fix Leaky Faucets": 50,
            "Low-Flow Showerheads": 75,
            "Rainwater Collection": 40,
            "Composting": 30,
            "Natural Cleaners": 50
        }
        
        total = 0
        actions_taken = []
        for action in actions:
            if action in savings:
                total += savings[action]
                actions_taken.append(action)
        
        return {
            "total_savings": total,
            "actions": actions_taken,
            "count": len(actions_taken)
        }
    
    @staticmethod
    def calculate_carbon_savings(energy_savings):
        """Calculate carbon savings from energy savings"""
        # Approximate: $100 savings = 500kg CO2 reduction
        co2_saved = (energy_savings / 100) * 500
        return co2_saved

# ============================================================
# SUSTAINABLE PRODUCT RECOMMENDATIONS
# ============================================================

class SustainableProducts:
    """Sustainable product recommendations"""
    
    PRODUCTS = [
        {
            "name": "Bamboo Toothbrush",
            "category": "Personal Care",
            "price": "$3-5",
            "eco_score": 85,
            "description": "Biodegradable bamboo handle, recyclable bristles",
            "saving": "4 plastic toothbrushes/year",
            "emoji": "🪥"
        },
        {
            "name": "Reusable Water Bottle",
            "category": "Kitchen",
            "price": "$15-30",
            "eco_score": 92,
            "description": "Stainless steel or glass, eliminates single-use plastic",
            "saving": "500 plastic bottles/year",
            "emoji": "🍶"
        },
        {
            "name": "Beeswax Wraps",
            "category": "Kitchen",
            "price": "$15-25",
            "eco_score": 88,
            "description": "Reusable alternative to plastic wrap",
            "saving": "300m plastic wrap/year",
            "emoji": "🧻"
        },
        {
            "name": "Reusable Coffee Cup",
            "category": "Kitchen",
            "price": "$10-20",
            "eco_score": 87,
            "description": "Eliminate disposable coffee cups",
            "saving": "200 cups/year",
            "emoji": "☕"
        },
        {
            "name": "Eco-Friendly Laundry Detergent",
            "category": "Cleaning",
            "price": "$10-20",
            "eco_score": 82,
            "description": "Plant-based, biodegradable ingredients",
            "saving": "10kg plastic/year",
            "emoji": "🧺"
        },
        {
            "name": "Reusable Shopping Bags",
            "category": "Lifestyle",
            "price": "$5-15",
            "eco_score": 90,
            "description": "Eliminate single-use plastic bags",
            "saving": "500 bags/year",
            "emoji": "🛍️"
        },
        {
            "name": "Solar Charger",
            "category": "Electronics",
            "price": "$30-60",
            "eco_score": 93,
            "description": "Charge devices with renewable energy",
            "saving": "50kg CO2/year",
            "emoji": "🔋"
        },
        {
            "name": "Compost Bin",
            "category": "Kitchen",
            "price": "$20-50",
            "eco_score": 91,
            "description": "Turn food waste into nutrient-rich compost",
            "saving": "200kg waste/year",
            "emoji": "🗑️"
        }
    ]
    
    @staticmethod
    def get_products(category=None):
        """Get products by category"""
        if category:
            return [p for p in SustainableProducts.PRODUCTS if p["category"] == category]
        return SustainableProducts.PRODUCTS
    
    @staticmethod
    def get_categories():
        """Get product categories"""
        return sorted(set(p["category"] for p in SustainableProducts.PRODUCTS))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_home_guide():
    """Render the complete home guide"""
    st.markdown("<div class='section-header'>🏠 Eco-Home & Sustainable Living Guide</div>", unsafe_allow_html=True)
    
    # Random tip
    tip = SustainableHomeTips.get_random_tip()
    st.info(f"💡 **Did you know?** {tip['title']} - {tip['description']}")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏠 Home Tips",
        "🔌 Energy Audit",
        "🛒 Sustainable Products",
        "📊 Progress Tracker"
    ])
    
    with tab1:
        render_home_tips()
    
    with tab2:
        render_energy_audit()
    
    with tab3:
        render_products()
    
    with tab4:
        render_home_progress()

def render_home_tips():
    """Render home tips"""
    st.markdown("### 🏠 Sustainable Home Tips")
    
    # Category selector
    categories = SustainableHomeTips.get_categories()
    selected_category = st.selectbox("Select Category", ["All"] + categories)
    
    # Get tips
    if selected_category == "All":
        tips = []
        for cat_tips in SustainableHomeTips.get_tips().values():
            tips.extend(cat_tips)
    else:
        tips = SustainableHomeTips.get_tips(selected_category)
    
    # Display tips
    for tip in tips:
        difficulty_colors = {
            "Easy": "#4ade80",
            "Medium": "#fbbf24",
            "Hard": "#f87171"
        }
        color = difficulty_colors.get(tip["difficulty"], "#6b7280")
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {color};'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 32px;'>{tip['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h5 style='margin: 0; color: #4ade80;'>{tip['title']}</h5>
                            <div style='font-size: 13px; color: #6b7280;'>{tip['description']}</div>
                        </div>
                        <span style='background: {color}; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827; font-weight: 700;'>
                            {tip['difficulty']}
                        </span>
                    </div>
                    <div style='display: flex; gap: 20px; margin-top: 6px; font-size: 13px;'>
                        <span>💰 {tip['cost']}</span>
                        <span>💚 Saves: {tip['saving']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action button
        if st.button(f"✅ Add to My Plan - {tip['title']}", key=f"add_{tip['title']}"):
            if "home_actions" not in st.session_state:
                st.session_state.home_actions = []
            if tip['title'] not in st.session_state.home_actions:
                st.session_state.home_actions.append(tip['title'])
                st.success(f"✅ Added {tip['title']} to your action plan!")
                st.rerun()

def render_energy_audit():
    """Render energy audit"""
    st.markdown("### 🔌 Home Energy Audit")
    
    st.markdown("""
    <div class='subtitle'>
        Select actions you've taken or plan to take to see your potential savings
    </div>
    """, unsafe_allow_html=True)
    
    # Energy actions checklist
    energy_actions = [
        "LED Bulbs",
        "Smart Thermostat",
        "Unplug Phantom Loads",
        "Solar Panels",
        "Energy-Efficient Appliances"
    ]
    
    water_actions = [
        "Fix Leaky Faucets",
        "Low-Flow Showerheads",
        "Rainwater Collection"
    ]
    
    waste_actions = [
        "Composting",
        "Natural Cleaners"
    ]
    
    st.markdown("#### ⚡ Energy Actions")
    selected_energy = []
    for action in energy_actions:
        if st.checkbox(action, key=f"energy_{action}"):
            selected_energy.append(action)
    
    st.markdown("#### 💧 Water Actions")
    selected_water = []
    for action in water_actions:
        if st.checkbox(action, key=f"water_{action}"):
            selected_water.append(action)
    
    st.markdown("#### ♻️ Waste Actions")
    selected_waste = []
    for action in waste_actions:
        if st.checkbox(action, key=f"waste_{action}"):
            selected_waste.append(action)
    
    all_actions = selected_energy + selected_water + selected_waste
    
    if all_actions and st.button("📊 Calculate My Impact", type="primary", use_container_width=True):
        # Calculate savings
        energy_savings = HomeEnergyAudit.calculate_savings(all_actions)
        co2_savings = HomeEnergyAudit.calculate_carbon_savings(energy_savings["total_savings"])
        
        st.markdown("### 📊 Your Impact")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Actions Selected", energy_savings["count"])
        col2.metric("Annual Savings", f"${energy_savings['total_savings']:.0f}")
        col3.metric("CO₂ Reduced", f"{co2_savings:.0f} kg/year")
        col4.metric("Trees Equivalent", f"{co2_savings/22:.1f}")
        
        # Progress bar
        st.markdown("#### Progress")
        st.progress(min(energy_savings["count"] / 10, 1.0))
        
        # Breakdown chart
        if energy_savings["actions"]:
            savings_data = {
                "Energy": sum(HomeEnergyAudit.calculate_savings(selected_energy)["total_savings"]),
                "Water": sum(HomeEnergyAudit.calculate_savings(selected_water)["total_savings"]),
                "Waste": sum(HomeEnergyAudit.calculate_savings(selected_waste)["total_savings"])
            }
            
            fig = go.Figure(data=[go.Bar(
                x=list(savings_data.keys()),
                y=list(savings_data.values()),
                marker_color=['#fbbf24', '#60a5fa', '#4ade80']
            )])
            fig.update_layout(
                title="Savings by Category ($/year)",
                height=250,
                margin=dict(l=0, r=0, t=40, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.markdown("### 💡 Recommendations")
        
        if energy_savings["count"] < 3:
            st.info("🌱 Start with easy actions like switching to LED bulbs and fixing leaky faucets")
        elif energy_savings["count"] < 6:
            st.info("🌿 Great progress! Consider installing a smart thermostat or low-flow showerheads")
        else:
            st.success("🌟 Excellent! You're on your way to an eco-home. Consider solar panels for maximum impact")

def render_products():
    """Render sustainable products"""
    st.markdown("### 🛒 Sustainable Product Recommendations")
    
    # Category filter
    categories = ["All"] + SustainableProducts.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get products
    if selected_category == "All":
        products = SustainableProducts.get_products()
    else:
        products = SustainableProducts.get_products(selected_category)
    
    # Display products in grid
    cols = st.columns(2)
    for i, product in enumerate(products):
        with cols[i % 2]:
            eco_score = product['eco_score']
            color = "#4ade80" if eco_score >= 80 else "#fbbf24" if eco_score >= 70 else "#f87171"
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; align-items: start; gap: 12px;'>
                    <div style='font-size: 32px;'>{product['emoji']}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h5 style='margin: 0; color: #4ade80;'>{product['name']}</h5>
                                <span style='font-size: 12px; color: #6b7280;'>{product['category']}</span>
                            </div>
                            <span style='background: {color}; padding: 2px 8px; border-radius: 12px; font-size: 11px; color: #111827; font-weight: 700;'>
                                {eco_score}/100
                            </span>
                        </div>
                        <p style='font-size: 13px; color: #6b7280; margin: 4px 0;'>{product['description']}</p>
                        <div style='display: flex; gap: 15px; font-size: 12px;'>
                            <span>💰 {product['price']}</span>
                            <span>💚 {product['saving']}</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_home_progress():
    """Render home progress tracker"""
    st.markdown("### 📊 Your Eco-Home Progress")
    
    # Get actions from session
    actions = st.session_state.get("home_actions", [])
    
    if actions:
        # Stats
        energy_actions = ["LED Bulbs", "Smart Thermostat", "Unplug Phantom Loads", "Solar Panels", "Energy-Efficient Appliances"]
        water_actions = ["Fix Leaky Faucets", "Low-Flow Showerheads", "Rainwater Collection"]
        waste_actions = ["Composting", "Natural Cleaners"]
        
        energy_count = sum(1 for a in actions if a in energy_actions)
        water_count = sum(1 for a in actions if a in water_actions)
        waste_count = sum(1 for a in actions if a in waste_actions)
        
        total = len(actions)
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Actions", total)
        col2.metric("⚡ Energy", f"{energy_count}/5")
        col3.metric("💧 Water", f"{water_count}/3")
        col4.metric("♻️ Waste", f"{waste_count}/2")
        
        # Progress by category
        st.markdown("#### Progress by Category")
        
        progress_data = {
            "Energy": energy_count / 5,
            "Water": water_count / 3,
            "Waste": waste_count / 2
        }
        
        fig = go.Figure(data=[go.Bar(
            x=list(progress_data.keys()),
            y=list(progress_data.values()),
            marker_color=['#fbbf24', '#60a5fa', '#4ade80'],
            text=[f"{v*100:.0f}%" for v in progress_data.values()],
            textposition='auto'
        )])
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis=dict(range=[0, 1])
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Checklist
        st.markdown("#### ✅ Your Action Checklist")
        
        for action in actions:
            st.success(f"✅ {action}")
        
        # Next steps
        st.markdown("#### 🎯 Next Steps")
        
        all_tips = []
        for cat_tips in SustainableHomeTips.get_tips().values():
            all_tips.extend(cat_tips)
        
        completed_titles = actions
        next_steps = [t for t in all_tips if t["title"] not in completed_titles][:3]
        
        for step in next_steps:
            st.markdown(f"• {step['emoji']} **{step['title']}** - {step['description']}")
        
        # Reset button
        if st.button("🔄 Reset Progress", use_container_width=True):
            st.session_state.home_actions = []
            st.rerun()
    else:
        st.info("🌱 Start your eco-home journey by adding actions from the 'Home Tips' tab!")
        
        # Show quick start
        st.markdown("### 🌟 Quick Start Actions")
        quick_actions = [
            "Switch to LED Bulbs",
            "Fix Leaky Faucets",
            "Start Composting"
        ]
        
        for action in quick_actions:
            if st.button(f"➕ Add {action}", key=f"quick_{action}"):
                if "home_actions" not in st.session_state:
                    st.session_state.home_actions = []
                if action not in st.session_state.home_actions:
                    st.session_state.home_actions.append(action)
                    st.success(f"✅ Added {action}!")
                    st.rerun()

# ============================================================
# INTEGRATION
# ============================================================

def render_home_hub():
    """Render the complete home hub"""
    render_home_guide()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from home_guide import render_home_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18 = st.tabs([
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
    "🏠 Eco-Home"  # NEW
])

with tab18:
    render_home_hub()
"""