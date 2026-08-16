# ============================================================
# FILE: fashion_guide.py
# EcoBuddy AI+ Sustainable Fashion & Wardrobe Guide
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# FABRIC DATABASE
# ============================================================

class FabricDatabase:
    """Database of fabric sustainability ratings"""
    
    FABRICS = [
        {
            "name": "Organic Cotton",
            "category": "Natural",
            "sustainability_score": 85,
            "water_usage": "Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "High",
            "price_range": "$$",
            "description": "Cotton grown without harmful pesticides or synthetic fertilizers",
            "benefits": ["Chemical-free", "Biodegradable", "Comfortable"],
            "drawbacks": ["Requires more land", "Higher cost"],
            "emoji": "🌿",
            "care_tips": "Wash in cold water, air dry"
        },
        {
            "name": "Recycled Polyester",
            "category": "Synthetic",
            "sustainability_score": 75,
            "water_usage": "Low",
            "carbon_footprint": "Medium",
            "biodegradable": False,
            "durability": "High",
            "price_range": "$",
            "description": "Polyester made from recycled plastic bottles",
            "benefits": ["Reduces plastic waste", "Durable", "Affordable"],
            "drawbacks": ["Releases microplastics", "Not biodegradable"],
            "emoji": "♻️",
            "care_tips": "Wash in cold water, use a microplastic filter bag"
        },
        {
            "name": "Linen",
            "category": "Natural",
            "sustainability_score": 88,
            "water_usage": "Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "Very High",
            "price_range": "$$$",
            "description": "Made from flax plant, requires minimal water and pesticides",
            "benefits": ["Biodegradable", "Breathable", "Durable"],
            "drawbacks": ["Expensive", "Wrinkles easily"],
            "emoji": "🧵",
            "care_tips": "Iron while damp, line dry"
        },
        {
            "name": "Hemp",
            "category": "Natural",
            "sustainability_score": 90,
            "water_usage": "Very Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "Very High",
            "price_range": "$$",
            "description": "Highly sustainable crop requiring minimal water and no pesticides",
            "benefits": ["Low water usage", "Pest-resistant", "CO2-absorbing"],
            "drawbacks": ["Stiff initially", "Limited availability"],
            "emoji": "🌱",
            "care_tips": "Machine wash gentle, line dry"
        },
        {
            "name": "Tencel/Lyocell",
            "category": "Semi-synthetic",
            "sustainability_score": 82,
            "water_usage": "Low",
            "carbon_footprint": "Medium",
            "biodegradable": True,
            "durability": "Medium",
            "price_range": "$$",
            "description": "Made from wood pulp in a closed-loop process",
            "benefits": ["Biodegradable", "Soft", "Breathable"],
            "drawbacks": ["Energy-intensive production"],
            "emoji": "🌳",
            "care_tips": "Machine wash gentle, air dry"
        },
        {
            "name": "Wool (Sustainable)",
            "category": "Animal",
            "sustainability_score": 70,
            "water_usage": "Medium",
            "carbon_footprint": "Medium",
            "biodegradable": True,
            "durability": "High",
            "price_range": "$$$",
            "description": "Ethically sourced wool from responsible farms",
            "benefits": ["Biodegradable", "Warm", "Durable"],
            "drawbacks": ["Methane emissions", "Land usage"],
            "emoji": "🐑",
            "care_tips": "Dry clean or hand wash cold"
        },
        {
            "name": "Recycled Cotton",
            "category": "Natural",
            "sustainability_score": 78,
            "water_usage": "Very Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "Medium",
            "price_range": "$",
            "description": "Cotton made from recycled textile waste",
            "benefits": ["Reduces waste", "Saves water", "Affordable"],
            "drawbacks": ["May pill", "Shorter fibers"],
            "emoji": "🔄",
            "care_tips": "Wash cold, line dry"
        },
        {
            "name": "Bamboo Linen",
            "category": "Natural",
            "sustainability_score": 80,
            "water_usage": "Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "High",
            "price_range": "$$",
            "description": "Made from bamboo, grows rapidly without pesticides",
            "benefits": ["Fast-growing", "Biodegradable", "Soft"],
            "drawbacks": ["Processing can be chemical-heavy"],
            "emoji": "🎋",
            "care_tips": "Machine wash cold, tumble dry low"
        },
        {
            "name": "Piñatex",
            "category": "Innovative",
            "sustainability_score": 85,
            "water_usage": "Very Low",
            "carbon_footprint": "Low",
            "biodegradable": True,
            "durability": "Medium",
            "price_range": "$$$",
            "description": "Leather alternative made from pineapple leaf fibers",
            "benefits": ["Waste utilization", "Cruelty-free", "Unique"],
            "drawbacks": ["Expensive", "Limited production"],
            "emoji": "🍍",
            "care_tips": "Wipe clean with damp cloth"
        }
    ]
    
    @staticmethod
    def get_fabrics(category=None):
        """Get fabrics with filters"""
        fabrics = FabricDatabase.FABRICS.copy()
        if category and category != "All":
            fabrics = [f for f in fabrics if f["category"] == category]
        return sorted(fabrics, key=lambda x: x["sustainability_score"], reverse=True)
    
    @staticmethod
    def get_categories():
        """Get fabric categories"""
        return ["All"] + sorted(set(f["category"] for f in FabricDatabase.FABRICS))

# ============================================================
# WARDROBE TRACKER
# ============================================================

class WardrobeTracker:
    """Track user's wardrobe items"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.items = self._load_items()
    
    def _load_items(self):
        """Load items from session"""
        if "wardrobe_items" not in st.session_state:
            st.session_state.wardrobe_items = {}
        return st.session_state.wardrobe_items.get(self.user_id, [])
    
    def save(self):
        """Save items"""
        st.session_state.wardrobe_items[self.user_id] = self.items
    
    def add_item(self, name, fabric, category, brand, price, purchase_date, is_sustainable=True):
        """Add a wardrobe item"""
        item = {
            "id": len(self.items) + 1,
            "name": name,
            "fabric": fabric,
            "category": category,
            "brand": brand,
            "price": price,
            "purchase_date": purchase_date,
            "is_sustainable": is_sustainable,
            "times_worn": 0,
            "created_at": datetime.now().isoformat()
        }
        self.items.append(item)
        self.save()
        return item
    
    def remove_item(self, item_id):
        """Remove an item from wardrobe"""
        for i, item in enumerate(self.items):
            if item["id"] == item_id:
                del self.items[i]
                self.save()
                return True
        return False
    
    def update_wears(self, item_id):
        """Update times worn for an item"""
        for item in self.items:
            if item["id"] == item_id:
                item["times_worn"] += 1
                self.save()
                return True
        return False
    
    def get_stats(self):
        """Get wardrobe statistics"""
        if not self.items:
            return {
                "total": 0,
                "sustainable": 0,
                "categories": {},
                "total_spent": 0,
                "avg_price": 0,
                "sustainable_percentage": 0
            }
        
        df = pd.DataFrame(self.items)
        
        total = len(df)
        sustainable = len(df[df["is_sustainable"] == True]) if "is_sustainable" in df.columns else 0
        total_spent = df["price"].sum() if "price" in df.columns else 0
        avg_price = total_spent / total if total > 0 else 0
        
        category_counts = df["category"].value_counts().to_dict() if "category" in df.columns else {}
        
        return {
            "total": total,
            "sustainable": sustainable,
            "categories": category_counts,
            "total_spent": total_spent,
            "avg_price": avg_price,
            "sustainable_percentage": (sustainable / total * 100) if total > 0 else 0
        }

# ============================================================
# FASHION IMPACT CALCULATOR
# ============================================================

class FashionImpactCalculator:
    """Calculate fashion environmental impact"""
    
    @staticmethod
    def calculate_impact(num_items, fabric_types, washes_per_year=30):
        """Calculate fashion environmental impact"""
        
        # Carbon factors (kg CO2 per item)
        carbon_factors = {
            "Organic Cotton": 15,
            "Recycled Polyester": 20,
            "Linen": 12,
            "Hemp": 10,
            "Tencel/Lyocell": 18,
            "Wool (Sustainable)": 25,
            "Recycled Cotton": 14,
            "Bamboo Linen": 16,
            "Piñatex": 30
        }
        
        # Water factors (liters per item)
        water_factors = {
            "Organic Cotton": 2000,
            "Recycled Polyester": 500,
            "Linen": 1500,
            "Hemp": 1000,
            "Tencel/Lyocell": 1800,
            "Wool (Sustainable)": 3000,
            "Recycled Cotton": 500,
            "Bamboo Linen": 1200,
            "Piñatex": 400
        }
        
        total_carbon = 0
        total_water = 0
        
        for fabric in fabric_types:
            carbon = carbon_factors.get(fabric, 20)
            water = water_factors.get(fabric, 2000)
            total_carbon += carbon * num_items
            total_water += water * num_items
        
        # Washing impact (adds 20% more carbon)
        washing_impact = total_carbon * 0.2
        
        return {
            "total_carbon_kg": total_carbon + washing_impact,
            "total_water_liters": total_water,
            "washing_impact": washing_impact,
            "trees_equivalent": (total_carbon + washing_impact) / 22,
            "average_per_item": {
                "carbon": (total_carbon + washing_impact) / num_items if num_items > 0 else 0,
                "water": total_water / num_items if num_items > 0 else 0
            }
        }

# ============================================================
# FASHION TIPS
# ============================================================

class FashionTips:
    """Sustainable fashion tips"""
    
    TIPS = [
        {
            "title": "🚫 Avoid Fast Fashion",
            "description": "Choose quality over quantity and buy less",
            "category": "Buying"
        },
        {
            "title": "🔄 Buy Second-Hand",
            "description": "Thrift stores and vintage shops are eco-friendly",
            "category": "Buying"
        },
        {
            "title": "🧵 Repair Instead of Replace",
            "description": "Learn basic mending skills to extend clothing life",
            "category": "Care"
        },
        {
            "title": "🌿 Choose Natural Fibers",
            "description": "Organic cotton, linen, and hemp are better for the planet",
            "category": "Materials"
        },
        {
            "title": "♻️ Recycle Old Clothes",
            "description": "Donate or recycle textiles, don't trash them",
            "category": "Disposal"
        },
        {
            "title": "🧺 Wash Less Often",
            "description": "Wash clothes only when needed to save water and energy",
            "category": "Care"
        },
        {
            "title": "💧 Wash in Cold Water",
            "description": "Cold water saves energy and preserves fabric",
            "category": "Care"
        },
        {
            "title": "☀️ Air Dry",
            "description": "Line drying saves energy and extends fabric life",
            "category": "Care"
        },
        {
            "title": "🌍 Support Ethical Brands",
            "description": "Research brands that prioritize sustainability",
            "category": "Buying"
        },
        {
            "title": "📦 Buy Quality Basics",
            "description": "Invest in timeless, versatile pieces",
            "category": "Buying"
        }
    ]
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category:
            return [t for t in FashionTips.TIPS if t["category"] == category]
        return FashionTips.TIPS
    
    @staticmethod
    def get_categories():
        """Get tip categories"""
        return sorted(set(t["category"] for t in FashionTips.TIPS))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_fashion_guide():
    """Render the complete fashion guide"""
    st.markdown("<div class='section-header'>👗 Sustainable Fashion & Wardrobe Guide</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize wardrobe tracker
    if "wardrobe_tracker" not in st.session_state:
        st.session_state.wardrobe_tracker = WardrobeTracker(user_id)
    
    tracker = st.session_state.wardrobe_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👗 Fabric Guide",
        "👚 My Wardrobe",
        "📊 Impact Calculator",
        "💡 Fashion Tips"
    ])
    
    with tab1:
        render_fabric_guide()
    
    with tab2:
        render_wardrobe(tracker)
    
    with tab3:
        render_impact_calculator(tracker)
    
    with tab4:
        render_fashion_tips()

def render_fabric_guide():
    """Render fabric guide"""
    st.markdown("### 👗 Sustainable Fabric Guide")
    
    # Category filter
    categories = FabricDatabase.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get fabrics
    fabrics = FabricDatabase.get_fabrics(selected_category)
    
    # Display fabrics
    for fabric in fabrics:
        score_color = "#4ade80" if fabric['sustainability_score'] >= 80 else "#fbbf24" if fabric['sustainability_score'] >= 70 else "#f87171"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{fabric['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{fabric['name']}</h4>
                            <span style='font-size: 13px; color: #6b7280;'>{fabric['category']} • {fabric['price_range']}</span>
                        </div>
                        <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                            {fabric['sustainability_score']}/100
                        </span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{fabric['description']}</p>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>
                        <span>💧 Water: {fabric['water_usage']}</span>
                        <span>🌍 Carbon: {fabric['carbon_footprint']}</span>
                        <span>♻️ Biodegradable: {'Yes' if fabric['biodegradable'] else 'No'}</span>
                        <span>💪 Durability: {fabric['durability']}</span>
                    </div>
                    <div style='display: flex; gap: 10px; margin-top: 4px; font-size: 13px;'>
                        <span>✅ Benefits: {', '.join(fabric['benefits'][:2])}</span>
                    </div>
                    <div style='font-size: 12px; color: #4ade80; margin-top: 4px;'>
                        💡 {fabric['care_tips']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📝 Learn More - {fabric['name']}", key=f"learn_{fabric['name']}"):
            with st.expander("Fabric Details", expanded=True):
                st.markdown(f"**Name:** {fabric['name']}")
                st.markdown(f"**Category:** {fabric['category']}")
                st.markdown(f"**Sustainability Score:** {fabric['sustainability_score']}/100")
                st.markdown(f"**Water Usage:** {fabric['water_usage']}")
                st.markdown(f"**Carbon Footprint:** {fabric['carbon_footprint']}")
                st.markdown(f"**Biodegradable:** {'Yes' if fabric['biodegradable'] else 'No'}")
                st.markdown(f"**Durability:** {fabric['durability']}")
                st.markdown(f"**Price Range:** {fabric['price_range']}")
                st.markdown(f"**Benefits:** {', '.join(fabric['benefits'])}")
                st.markdown(f"**Drawbacks:** {', '.join(fabric['drawbacks'])}")
                st.markdown(f"**Care Tips:** {fabric['care_tips']}")
        
        st.markdown("---")

def render_wardrobe(tracker):
    """Render wardrobe tracker"""
    st.markdown("### 👚 My Sustainable Wardrobe")
    
    # Add item form
    with st.expander("➕ Add Clothing Item", expanded=False):
        with st.form("wardrobe_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Item Name", placeholder="e.g., Organic Cotton T-Shirt")
                fabric = st.selectbox("Fabric Type", [f["name"] for f in FabricDatabase.FABRICS])
                category = st.selectbox("Category", ["Tops", "Bottoms", "Dresses", "Outerwear", "Accessories", "Footwear"])
            
            with col2:
                brand = st.text_input("Brand")
                price = st.number_input("Price ($)", min_value=0.0, value=50.0, step=5.0)
                purchase_date = st.date_input("Purchase Date", datetime.now())
                is_sustainable = st.checkbox("This is a sustainable item", value=True)
            
            if st.form_submit_button("Add to Wardrobe"):
                if name:
                    tracker.add_item(
                        name, fabric, category, brand, price,
                        purchase_date.isoformat(), is_sustainable
                    )
                    st.success("✅ Item added to wardrobe!")
                    st.rerun()
                else:
                    st.warning("Please enter an item name")
    
    # Wardrobe statistics
    stats = tracker.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Items", stats["total"])
    col2.metric("Sustainable", stats["sustainable"])
    col3.metric("Sustain. %", f"{stats['sustainable_percentage']:.0f}%")
    col4.metric("Total Spent", f"${stats['total_spent']:.2f}")
    
    # Category breakdown
    if stats['categories']:
        st.markdown("#### 📊 Wardrobe Categories")
        
        fig = go.Figure(data=[go.Pie(
            labels=list(stats['categories'].keys()),
            values=list(stats['categories'].values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Display items
    st.markdown("#### 📋 My Items")
    
    if tracker.items:
        for item in tracker.items:
            sustainable_icon = "✅" if item.get("is_sustainable", False) else "❌"
            purchase_date = datetime.fromisoformat(item["purchase_date"]).strftime("%b %d, %Y") if item.get("purchase_date") else "Unknown"
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{item['name']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>
                            {item['fabric']} • {item['category']} • {item['brand']}
                            • Purchased: {purchase_date}
                            • Worn: {item.get('times_worn', 0)} times
                            {f' • 💰 ${item["price"]:.2f}' if item.get('price') else ''}
                        </div>
                    </div>
                    <div style='display: flex; gap: 10px; align-items: center;'>
                        <span style='font-size: 20px;'>{sustainable_icon}</span>
                        <button onclick="st.session_state.wear_{item['id']} = True" style='background: #4ade80; border: none; padding: 4px 8px; border-radius: 8px; cursor: pointer;'>
                            👕 Wear
                        </button>
                        <button onclick="st.session_state.remove_{item['id']} = True" style='background: #f87171; border: none; padding: 4px 8px; border-radius: 8px; cursor: pointer; color: white;'>
                            ❌
                        </button>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button(f"👕 Worn", key=f"wear_{item['id']}", use_container_width=True):
                tracker.update_wears(item['id'])
                st.rerun()
            
            if st.button(f"🗑️ Remove", key=f"remove_{item['id']}", use_container_width=True):
                tracker.remove_item(item['id'])
                st.rerun()
    else:
        st.info("👚 Your wardrobe is empty. Add your first sustainable item!")

def render_impact_calculator(tracker):
    """Render fashion impact calculator"""
    st.markdown("### 📊 Fashion Impact Calculator")
    
    st.markdown("""
    <div class='subtitle'>
        Calculate the environmental impact of your clothing choices
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_items = st.number_input("Number of clothing items", min_value=1, value=10, step=1)
        washes_per_year = st.number_input("Washes per year per item", min_value=0, value=30, step=5)
    
    with col2:
        fabric_types = st.multiselect(
            "Fabric Types in your wardrobe",
            [f["name"] for f in FabricDatabase.FABRICS],
            default=["Organic Cotton", "Recycled Polyester"]
        )
    
    if st.button("🌍 Calculate Impact", type="primary", use_container_width=True):
        if fabric_types:
            impact = FashionImpactCalculator.calculate_impact(
                num_items,
                fabric_types,
                washes_per_year
            )
            
            st.markdown("### 📊 Your Fashion Impact")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("CO₂ Emissions", f"{impact['total_carbon_kg']:.0f} kg")
            col2.metric("Water Usage", f"{impact['total_water_liters']:,.0f} L")
            col3.metric("Trees Needed", f"{impact['trees_equivalent']:.1f}")
            col4.metric("Washing Impact", f"{impact['washing_impact']:.0f} kg")
            
            # Per item average
            st.markdown("#### Per Item Average")
            col1, col2 = st.columns(2)
            col1.metric("Avg CO₂ per Item", f"{impact['average_per_item']['carbon']:.1f} kg")
            col2.metric("Avg Water per Item", f"{impact['average_per_item']['water']:,.0f} L")
            
            # Impact level
            if impact['total_carbon_kg'] < 100:
                st.success("🌟 Low impact! Your fashion choices are sustainable!")
            elif impact['total_carbon_kg'] < 200:
                st.info("🌱 Medium impact. Consider reducing items or choosing better fabrics")
            else:
                st.warning("⚠️ High impact. Try sustainable alternatives and buy less")
            
            # Recommendations
            st.markdown("#### 💡 Recommendations")
            
            if "Recycled Polyester" in fabric_types:
                st.markdown("• ♻️ Consider reducing recycled polyester - it still releases microplastics")
            if "Wool" in fabric_types:
                st.markdown("• 🐑 Look for sustainable wool certifications")
            if washes_per_year > 30:
                st.markdown("• 🧺 Wash less often to save water and energy")
            
        else:
            st.warning("Please select at least one fabric type")

def render_fashion_tips():
    """Render fashion tips"""
    st.markdown("### 💡 Sustainable Fashion Tips")
    
    # Category filter
    categories = ["All"] + FashionTips.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    if selected_category == "All":
        tips = FashionTips.get_tips()
    else:
        tips = FashionTips.get_tips(selected_category)
    
    # Display tips
    cols = st.columns(2)
    for i, tip in enumerate(tips):
        with cols[i % 2]:
            st.markdown(f"""
            <div class='card' style='height: 100%;'>
                <div style='display: flex; align-items: start; gap: 10px;'>
                    <div style='font-size: 24px;'>{tip['title'].split()[0]}</div>
                    <div>
                        <div style='font-weight: 600; font-size: 15px;'>{tip['title']}</div>
                        <div style='color: #6b7280; font-size: 14px;'>{tip['description']}</div>
                        <div style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px; display: inline-block; margin-top: 6px; color: #4ade80;'>
                            {tip['category']}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick action plan
    st.markdown("---")
    st.markdown("### 🎯 Your Sustainable Fashion Action Plan")
    
    actions = [
        "🌿 Buy one sustainable item this month",
        "👕 Wear each item at least 30 times before replacing",
        "🧺 Reduce washing frequency by 20%",
        "♻️ Donate or recycle 3 items you no longer wear",
        "🧵 Learn a simple mending technique"
    ]
    
    for action in actions:
        if st.button(action, use_container_width=True, key=f"action_{action}"):
            if "fashion_actions" not in st.session_state:
                st.session_state.fashion_actions = []
            if action not in st.session_state.fashion_actions:
                st.session_state.fashion_actions.append(action)
                st.success(f"✅ Added to your action plan: {action}")
                st.rerun()
    
    # Show action plan
    if "fashion_actions" in st.session_state and st.session_state.fashion_actions:
        st.markdown("#### 📋 My Action Plan")
        for action in st.session_state.fashion_actions:
            st.success(f"✅ {action}")
        
        if st.button("🔄 Reset Action Plan", use_container_width=True):
            st.session_state.fashion_actions = []
            st.rerun()

# ============================================================
# INTEGRATION
# ============================================================

def render_fashion_hub():
    """Render the complete fashion hub"""
    render_fashion_guide()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from fashion_guide import render_fashion_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22, tab23 = st.tabs([
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
    "📰 Eco-News",
    "🤝 Volunteer",
    "👗 Fashion"  # NEW
])

with tab23:
    render_fashion_hub()
"""