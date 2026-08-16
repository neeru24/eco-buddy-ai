# ============================================================
# FILE: travel_planner.py
# EcoBuddy AI+ Sustainable Travel & Tourism Planner
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math
from typing import Any

# ============================================================
# DESTINATION DATABASE
# ============================================================

class EcoDestinations:
    """Database of eco-friendly travel destinations"""
    
    DESTINATIONS = [
        {
            "name": "Costa Rica",
            "country": "Costa Rica",
            "region": "Central America",
            "eco_score": 95,
            "description": "World leader in eco-tourism with extensive rainforests and wildlife",
            "activities": ["Rainforest hiking", "Wildlife watching", "Beach conservation", "Volcano tours"],
            "best_season": "December-April",
            "carbon_offset_cost": 45,
            "sustainable_accommodations": 120,
            "image": "🌴",
            "co2_saved": 350
        },
        {
            "name": "Iceland",
            "country": "Iceland",
            "region": "Europe",
            "eco_score": 92,
            "description": "Geothermal energy leader with stunning natural landscapes",
            "activities": ["Geothermal baths", "Glacier hiking", "Northern lights", "Waterfall tours"],
            "best_season": "June-August",
            "carbon_offset_cost": 55,
            "sustainable_accommodations": 80,
            "image": "❄️",
            "co2_saved": 280
        },
        {
            "name": "New Zealand",
            "country": "New Zealand",
            "region": "Oceania",
            "eco_score": 90,
            "description": "Pristine nature with strong conservation efforts",
            "activities": ["Hiking", "Kiwi wildlife", "Maori culture", "Glacier tours"],
            "best_season": "November-March",
            "carbon_offset_cost": 60,
            "sustainable_accommodations": 95,
            "image": "🏔️",
            "co2_saved": 300
        },
        {
            "name": "Bhutan",
            "country": "Bhutan",
            "region": "Asia",
            "eco_score": 93,
            "description": "Carbon-negative country with stunning Himalayan views",
            "activities": ["Monastery visits", "Himalayan trekking", "Buddhist culture", "Nature walks"],
            "best_season": "March-May",
            "carbon_offset_cost": 40,
            "sustainable_accommodations": 60,
            "image": "🏯",
            "co2_saved": 420
        },
        {
            "name": "Slovenia",
            "country": "Slovenia",
            "region": "Europe",
            "eco_score": 88,
            "description": "Green capital of Europe with sustainable tourism",
            "activities": ["Lake Bled", "Cave exploration", "Wine tasting", "Mountain biking"],
            "best_season": "May-September",
            "carbon_offset_cost": 35,
            "sustainable_accommodations": 150,
            "image": "🏞️",
            "co2_saved": 200
        },
        {
            "name": "Maldives",
            "country": "Maldives",
            "region": "Asia",
            "eco_score": 85,
            "description": "Luxury eco-resorts with coral reef conservation",
            "activities": ["Snorkeling", "Coral planting", "Island hopping", "Sea turtle watching"],
            "best_season": "November-April",
            "carbon_offset_cost": 70,
            "sustainable_accommodations": 45,
            "image": "🏝️",
            "co2_saved": 250
        },
        {
            "name": "Kenya",
            "country": "Kenya",
            "region": "Africa",
            "eco_score": 87,
            "description": "Wildlife conservation and community-based tourism",
            "activities": ["Safari", "Maasai culture", "Wildlife photography", "Conservation work"],
            "best_season": "July-October",
            "carbon_offset_cost": 50,
            "sustainable_accommodations": 70,
            "image": "🦁",
            "co2_saved": 380
        },
        {
            "name": "Portugal",
            "country": "Portugal",
            "region": "Europe",
            "eco_score": 86,
            "description": "Sustainable vineyards and coastal conservation",
            "activities": ["Wine tours", "Surfing", "Hiking", "Cultural heritage"],
            "best_season": "May-October",
            "carbon_offset_cost": 30,
            "sustainable_accommodations": 200,
            "image": "🍷",
            "co2_saved": 180
        }
    ]
    
    @staticmethod
    def get_destinations(filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Get destinations with optional filters"""
        destinations = EcoDestinations.DESTINATIONS.copy()
        
        if filters:
            if filters.get("region"):
                destinations = [d for d in destinations if d["region"] == filters["region"]]
            if filters.get("min_eco_score"):
                destinations = [d for d in destinations if d["eco_score"] >= filters["min_eco_score"]]
            if filters.get("max_cost"):
                destinations = [d for d in destinations if d["carbon_offset_cost"] <= filters["max_cost"]]
        
        return destinations
    
    @staticmethod
    def get_regions() -> list[str]:
        """Get unique regions"""
        return sorted(set(d["region"] for d in EcoDestinations.DESTINATIONS))

# ============================================================
# TRIP CARBON CALCULATOR
# ============================================================

class TripCarbonCalculator:
    """Calculate carbon footprint for trips"""
    
    @staticmethod
    def calculate_trip_carbon(destination: str, transport_mode: str, duration_days: int, travelers: int) -> dict[str, Any]:
        """Calculate carbon footprint for a trip"""
        
        # Base carbon factors (kg CO2 per km)
        carbon_factors = {
            "Car": 0.12,
            "Train": 0.03,
            "Bus": 0.04,
            "Flight": 0.15,
            "Boat": 0.06
        }
        
        # Distance from major hubs (simplified)
        distances = {
            "Costa Rica": 8000,
            "Iceland": 5000,
            "New Zealand": 18000,
            "Bhutan": 7000,
            "Slovenia": 6000,
            "Maldives": 8000,
            "Kenya": 7000,
            "Portugal": 6000
        }
        
        # Get distance
        distance = distances.get(destination, 10000)
        
        # Calculate emissions
        factor = carbon_factors.get(transport_mode, 0.12)
        base_emissions = distance * factor * travelers
        
        # Daily activities emissions
        daily_emissions = travelers * 10 * duration_days  # 10kg per traveler per day
        
        # Accommodation emissions
        accommodation_emissions = travelers * 15 * duration_days  # 15kg per traveler per day
        
        # Total emissions
        total_emissions = base_emissions + daily_emissions + accommodation_emissions
        
        # Calculate offset cost
        offset_cost = total_emissions * 0.02  # $2 per 100kg
        
        return {
            "total_emissions_kg": total_emissions,
            "transport_emissions": base_emissions,
            "daily_activities": daily_emissions,
            "accommodation": accommodation_emissions,
            "offset_cost_usd": offset_cost,
            "trees_needed": total_emissions / 22,
            "reduction_percent": 0
        }

# ============================================================
# SUSTAINABLE PACKING CHECKLIST
# ============================================================

class SustainablePacking:
    """Sustainable packing checklist"""
    
    ITEMS = [
        {"name": "Reusable Water Bottle", "category": "Reusable", "saving": 50},
        {"name": "Shopping Tote Bag", "category": "Reusable", "saving": 30},
        {"name": "Bamboo Utensils", "category": "Reusable", "saving": 20},
        {"name": "Solid Shampoo Bar", "category": "Personal Care", "saving": 15},
        {"name": "Reusable Coffee Cup", "category": "Reusable", "saving": 25},
        {"name": "Eco-Friendly Sunscreen", "category": "Personal Care", "saving": 10},
        {"name": "Rechargeable Batteries", "category": "Electronics", "saving": 15},
        {"name": "Cloth Napkins", "category": "Reusable", "saving": 10},
        {"name": "Travel Clothesline", "category": "Laundry", "saving": 5},
        {"name": "Eco-Friendly Bug Spray", "category": "Personal Care", "saving": 10},
        {"name": "Snack Containers", "category": "Reusable", "saving": 15},
        {"name": "Solar Charger", "category": "Electronics", "saving": 20}
    ]
    
    @staticmethod
    def get_checklist() -> list[dict[str, Any]]:
        """Get sustainable packing checklist"""
        return SustainablePacking.ITEMS
    
    @staticmethod
    def calculate_savings(selected_items: list[str]) -> int:
        """Calculate plastic saved from selected items"""
        total_saving = sum(item["saving"] for item in SustainablePacking.ITEMS if item["name"] in selected_items)
        return total_saving

# ============================================================
# ECO-TRAVEL TIPS
# ============================================================

class EcoTravelTips:
    """Eco-friendly travel tips"""
    
    TIPS = [
        {
            "category": "Transportation",
            "tip": "Choose direct flights when possible",
            "saving": "30% less emissions"
        },
        {
            "category": "Transportation",
            "tip": "Take trains instead of short flights",
            "saving": "50% less emissions"
        },
        {
            "category": "Accommodation",
            "tip": "Stay at eco-certified hotels",
            "saving": "40% energy reduction"
        },
        {
            "category": "Accommodation",
            "tip": "Reuse towels and linens",
            "saving": "500L water per stay"
        },
        {
            "category": "Activities",
            "tip": "Choose local guides and tours",
            "saving": "Supports local economy"
        },
        {
            "category": "Activities",
            "tip": "Avoid activities that exploit animals",
            "saving": "Protects wildlife"
        },
        {
            "category": "Food",
            "tip": "Eat local and seasonal food",
            "saving": "Food miles reduced"
        },
        {
            "category": "Food",
            "tip": "Avoid food waste",
            "saving": "20% less food waste"
        },
        {
            "category": "Waste",
            "tip": "Carry a reusable water bottle",
            "saving": "200 plastic bottles/year"
        },
        {
            "category": "Waste",
            "tip": "Say no to plastic straws",
            "saving": "100 straws/year"
        }
    ]
    
    @staticmethod
    def get_tips(category: str | None = None) -> list[dict[str, Any]]:
        """Get travel tips by category"""
        if category:
            return [t for t in EcoTravelTips.TIPS if t["category"] == category]
        return EcoTravelTips.TIPS

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_travel_planner() -> None:
    """Render the complete travel planner"""
    st.markdown("<div class='section-header'>🌍 Eco-Travel & Sustainable Tourism</div>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌴 Destinations",
        "✈️ Trip Planner",
        "🧳 Packing Guide",
        "💡 Travel Tips"
    ])
    
    with tab1:
        render_destinations()
    
    with tab2:
        render_trip_planner()
    
    with tab3:
        render_packing_guide()
    
    with tab4:
        render_travel_tips()

def render_destinations() -> None:
    """Render eco-destinations"""
    st.markdown("### 🌴 Eco-Friendly Destinations")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        region_filter = st.selectbox(
            "Region",
            ["All"] + EcoDestinations.get_regions()
        )
    
    with col2:
        min_score = st.slider(
            "Minimum Eco Score",
            0, 100, 80
        )
    
    with col3:
        max_cost = st.slider(
            "Max Offset Cost ($)",
            0, 100, 70
        )
    
    # Get filtered destinations
    filters = {}
    if region_filter != "All":
        filters["region"] = region_filter
    filters["min_eco_score"] = min_score
    filters["max_cost"] = max_cost
    
    destinations = EcoDestinations.get_destinations(filters)
    
    # Display destinations
    for dest in destinations:
        with st.container():
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='display: flex; align-items: start; gap: 15px;'>
                    <div style='font-size: 48px;'>{dest['image']}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h4 style='margin: 0; color: #4ade80;'>{dest['name']}</h4>
                                <span style='font-size: 13px; color: #6b7280;'>{dest['country']} • {dest['region']}</span>
                            </div>
                            <div style='text-align: right;'>
                                <span style='background: #4ade80; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                                    {dest['eco_score']}/100
                                </span>
                            </div>
                        </div>
                        <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{dest['description']}</p>
                        <div style='display: flex; gap: 10px; flex-wrap: wrap;'>
                            {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px;">{act}</span>' for act in dest['activities'][:3]])}
                        </div>
                        <div style='display: flex; gap: 20px; margin-top: 8px; font-size: 13px; color: #6b7280;'>
                            <span>🌿 Best: {dest['best_season']}</span>
                            <span>💰 Offset: ${dest['carbon_offset_cost']}</span>
                            <span>🏨 Sustainable: {dest['sustainable_accommodations']}+</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Book button
            if st.button(f"Plan Trip to {dest['name']}", key=f"plan_{dest['name']}"):
                st.session_state.trip_destination = dest['name']
                st.rerun()

def render_trip_planner() -> None:
    """Render trip planner"""
    st.markdown("### ✈️ Plan Your Sustainable Trip")
    
    # Trip details
    col1, col2 = st.columns(2)
    
    with col1:
        destination = st.selectbox(
            "Destination",
            [d["name"] for d in EcoDestinations.DESTINATIONS]
        )
        
        transport_mode = st.selectbox(
            "Main Transport Mode",
            ["Flight", "Train", "Car", "Bus", "Boat"]
        )
        
        travelers = st.number_input(
            "Number of Travelers",
            min_value=1,
            value=2,
            step=1
        )
    
    with col2:
        duration = st.number_input(
            "Duration (days)",
            min_value=1,
            value=7,
            step=1
        )
        
        accommodation_type = st.selectbox(
            "Accommodation Type",
            ["Eco-Resort", "Sustainable Hotel", "Hostel", "Camping", "Homestay"]
        )
        
        include_offset = st.checkbox("Include Carbon Offset", value=True)
    
    # Calculate trip impact
    if st.button("🌿 Calculate Trip Impact", use_container_width=True, type="primary"):
        with st.spinner("Calculating your trip's environmental impact..."):
            # Get destination data
            dest_data = next(d for d in EcoDestinations.DESTINATIONS if d["name"] == destination)
            
            # Calculate carbon
            calculator = TripCarbonCalculator()
            carbon_data = calculator.calculate_trip_carbon(
                destination,
                transport_mode,
                duration,
                travelers
            )
            
            # Display results
            st.markdown("### 📊 Trip Environmental Impact")
            
            # Key metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total CO₂", f"{carbon_data['total_emissions_kg']:.0f} kg")
            col2.metric("Offset Cost", f"${carbon_data['offset_cost_usd']:.2f}")
            col3.metric("Trees Needed", f"{carbon_data['trees_needed']:.1f}")
            col4.metric("Destination Score", f"{dest_data['eco_score']}/100")
            
            # Breakdown chart
            st.markdown("#### Emissions Breakdown")
            
            breakdown_data = {
                "Transport": carbon_data['transport_emissions'],
                "Daily Activities": carbon_data['daily_activities'],
                "Accommodation": carbon_data['accommodation']
            }
            
            fig = go.Figure(data=[go.Pie(
                labels=list(breakdown_data.keys()),
                values=list(breakdown_data.values()),
                hole=0.3,
                marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa'])
            )])
            fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
            
            # Recommendations
            st.markdown("### 💡 Emission Reduction Tips")
            
            tips = []
            if transport_mode in ["Flight", "Car"]:
                tips.append("🚆 Consider taking a train instead of a flight/car for shorter distances")
            if duration > 10:
                tips.append("🏨 Choose eco-certified accommodations for longer stays")
            if travelers > 1:
                tips.append("👥 Traveling with others reduces per-person emissions")
            if dest_data['eco_score'] > 80:
                tips.append(f"🌟 {destination} is an eco-friendly destination! Your visit supports conservation")
            
            for tip in tips:
                st.info(tip)
            
            # Offset option
            if include_offset:
                st.markdown("### 🌍 Offset Your Trip")
                st.success(f"✅ You can offset your trip for ${carbon_data['offset_cost_usd']:.2f}")
                
                if st.button("🌿 Offset This Trip", use_container_width=True):
                    st.balloons()
                    st.success("🎉 Trip offset successfully! You're now carbon neutral for this trip!")

def render_packing_guide() -> None:
    """Render sustainable packing guide"""
    st.markdown("### 🧳 Sustainable Packing Checklist")
    
    # Get checklist
    items = SustainablePacking.get_checklist()
    
    # Categories
    categories = sorted(set(item["category"] for item in items))
    selected_items = []
    
    for category in categories:
        st.markdown(f"#### {category}")
        category_items = [item for item in items if item["category"] == category]
        
        cols = st.columns(2)
        for i, item in enumerate(category_items):
            with cols[i % 2]:
                if st.checkbox(f"{item['name']} (Saves {item['saving']} items)", key=f"pack_{item['name']}"):
                    selected_items.append(item['name'])
    
    # Calculate savings
    if selected_items:
        st.markdown("---")
        st.markdown("### 📊 Your Packing Impact")
        
        savings = SustainablePacking.calculate_savings(selected_items)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Items Packed", len(selected_items))
        col2.metric("Single-Use Items Avoided", f"{savings} pieces")
        col3.metric("Waste Reduction", f"{savings * 2}%")
        
        st.progress(min(savings / 100, 1.0))
        
        if savings > 50:
            st.success("🌟 Excellent! You're a sustainable packing champion!")
        elif savings > 25:
            st.info("🌱 Good start! Every sustainable item counts!")
        else:
            st.warning("📝 Try adding more reusable items to reduce waste")

def render_travel_tips() -> None:
    """Render eco-travel tips"""
    st.markdown("### 💡 Eco-Travel Tips")
    
    # Category filter
    categories = ["All"] + sorted(set(t["category"] for t in EcoTravelTips.TIPS))
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    if selected_category == "All":
        tips = EcoTravelTips.get_tips()
    else:
        tips = EcoTravelTips.get_tips(selected_category)
    
    # Display tips
    for tip in tips:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 24px;'>🌱</div>
                <div>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <span style='font-weight: 700;'>{tip['tip']}</span>
                        <span style='background: #1f2937; padding: 2px 12px; border-radius: 12px; font-size: 12px; color: #4ade80;'>
                            {tip['category']}
                        </span>
                    </div>
                    <div style='color: #6b7280; font-size: 14px; margin-top: 4px;'>
                        💚 {tip['saving']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick tips
    st.markdown("---")
    st.markdown("### 🚀 Quick Eco-Travel Actions")
    
    quick_tips = [
        "📱 Use digital boarding passes",
        "💧 Bring your own water bottle",
        "♻️ Say no to mini toiletries",
        "🌿 Choose eco-tours",
        "🏨 Skip daily room cleaning",
        "🚶 Explore on foot when possible"
    ]
    
    cols = st.columns(3)
    for i, tip in enumerate(quick_tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background: #1f2937; padding: 12px; border-radius: 10px; text-align: center; margin: 5px 0;'>
                <div style='font-size: 20px;'>{tip.split()[0]}</div>
                <div style='font-size: 13px;'>{tip}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_travel_hub() -> None:
    """Render the complete travel hub"""
    render_travel_planner()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from travel_planner import render_travel_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14 = st.tabs([
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
    "🌍 Eco-Travel"  # NEW
])

with tab14:
    render_travel_hub()
"""