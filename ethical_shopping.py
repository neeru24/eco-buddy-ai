
# ============================================================
# FILE: ethical_shopping.py
# EcoBuddy AI+ Ethical Shopping & Conscious Consumer Guide
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# PRODUCT DATABASE
# ============================================================

class ProductDatabase:
    """Database of products with ethical scores"""
    
    PRODUCTS = [
        {
            "id": "p1",
            "name": "Organic Cotton T-Shirt",
            "category": "Clothing",
            "brand": "EcoWear",
            "price": 45.00,
            "ethical_score": 88,
            "sustainability_factors": ["Organic materials", "Fair Trade", "Low water usage"],
            "certifications": ["GOTS", "Fair Trade"],
            "carbon_footprint": 5,
            "water_usage": 800,
            "emoji": "👕"
        },
        {
            "id": "p2",
            "name": "Recycled Plastic Backpack",
            "category": "Accessories",
            "brand": "GreenGear",
            "price": 65.00,
            "ethical_score": 85,
            "sustainability_factors": ["Recycled materials", "Ethical manufacturing"],
            "certifications": ["GRS"],
            "carbon_footprint": 3,
            "water_usage": 200,
            "emoji": "🎒"
        },
        {
            "id": "p3",
            "name": "Bamboo Cutlery Set",
            "category": "Kitchen",
            "brand": "EcoLife",
            "price": 24.99,
            "ethical_score": 92,
            "sustainability_factors": ["Biodegradable", "Sustainable sourcing"],
            "certifications": ["FSC"],
            "carbon_footprint": 1,
            "water_usage": 50,
            "emoji": "🍴"
        },
        {
            "id": "p4",
            "name": "Glass Water Bottle",
            "category": "Kitchen",
            "brand": "PureGlass",
            "price": 29.99,
            "ethical_score": 90,
            "sustainability_factors": ["Reusable", "Plastic-free"],
            "certifications": ["BPA-free"],
            "carbon_footprint": 2,
            "water_usage": 100,
            "emoji": "🍶"
        },
        {
            "id": "p5",
            "name": "Plant-Based Sneakers",
            "category": "Clothing",
            "brand": "EcoStep",
            "price": 79.99,
            "ethical_score": 87,
            "sustainability_factors": ["Plant-based materials", "Carbon neutral"],
            "certifications": ["B Corp"],
            "carbon_footprint": 4,
            "water_usage": 600,
            "emoji": "👟"
        },
        {
            "id": "p6",
            "name": "Solar Phone Charger",
            "category": "Electronics",
            "brand": "EcoCharge",
            "price": 59.99,
            "ethical_score": 86,
            "sustainability_factors": ["Solar powered", "Low energy"],
            "certifications": ["Energy Star"],
            "carbon_footprint": 2,
            "water_usage": 150,
            "emoji": "🔋"
        }
    ]
    
    @staticmethod
    def get_products(category=None, min_score=None):
        """Get products with filters"""
        products = ProductDatabase.PRODUCTS.copy()
        if category and category != "All":
            products = [p for p in products if p["category"] == category]
        if min_score:
            products = [p for p in products if p["ethical_score"] >= min_score]
        return products
    
    @staticmethod
    def get_categories():
        """Get product categories"""
        return ["All"] + sorted(set(p["category"] for p in ProductDatabase.PRODUCTS))

# ============================================================
# BRAND DATABASE
# ============================================================

class BrandDatabase:
    """Database of brand ethical ratings"""
    
    BRANDS = [
        {
            "name": "EcoWear",
            "industry": "Clothing",
            "ethical_score": 90,
            "transparency_score": 88,
            "environmental_score": 92,
            "social_score": 85,
            "certifications": ["GOTS", "Fair Trade", "B Corp"],
            "sustainability_commitment": "Carbon neutral by 2025",
            "emoji": "🌿"
        },
        {
            "name": "GreenGear",
            "industry": "Accessories",
            "ethical_score": 85,
            "transparency_score": 82,
            "environmental_score": 88,
            "social_score": 80,
            "certifications": ["GRS", "ISO 14001"],
            "sustainability_commitment": "100% recycled materials by 2026",
            "emoji": "♻️"
        },
        {
            "name": "EcoLife",
            "industry": "Home Goods",
            "ethical_score": 92,
            "transparency_score": 90,
            "environmental_score": 94,
            "social_score": 88,
            "certifications": ["FSC", "Plastic Free"],
            "sustainability_commitment": "Zero waste manufacturing",
            "emoji": "🌱"
        },
        {
            "name": "PureGlass",
            "industry": "Home Goods",
            "ethical_score": 88,
            "transparency_score": 85,
            "environmental_score": 90,
            "social_score": 84,
            "certifications": ["BPA-free", "Recyclable"],
            "sustainability_commitment": "Using 100% recycled glass",
            "emoji": "💚"
        },
        {
            "name": "EcoStep",
            "industry": "Clothing",
            "ethical_score": 87,
            "transparency_score": 84,
            "environmental_score": 89,
            "social_score": 83,
            "certifications": ["B Corp", "Carbon Neutral"],
            "sustainability_commitment": "Carbon positive by 2025",
            "emoji": "👟"
        }
    ]
    
    @staticmethod
    def get_brands(industry=None):
        """Get brands with filters"""
        brands = BrandDatabase.BRANDS.copy()
        if industry and industry != "All":
            brands = [b for b in brands if b["industry"] == industry]
        return brands
    
    @staticmethod
    def get_industries():
        """Get brand industries"""
        return ["All"] + sorted(set(b["industry"] for b in BrandDatabase.BRANDS))

# ============================================================
# SHOPPING TRACKER
# ============================================================

class ShoppingTracker:
    """Track sustainable shopping habits"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load shopping data from session"""
        if "shopping_data" not in st.session_state:
            st.session_state.shopping_data = {}
        return st.session_state.shopping_data.get(self.user_id, {
            "purchases": [],
            "sustainable_purchases": 0,
            "total_spent": 0,
            "sustainable_spent": 0,
            "wishlist": [],
            "savings": 0
        })
    
    def save(self):
        """Save shopping data"""
        st.session_state.shopping_data[self.user_id] = self.data
    
    def add_purchase(self, product_name, product_id, price, is_sustainable):
        """Add a purchase record"""
        purchase = {
            "product": product_name,
            "product_id": product_id,
            "price": price,
            "is_sustainable": is_sustainable,
            "date": datetime.now().isoformat()
        }
        self.data["purchases"].append(purchase)
        self.data["total_spent"] += price
        
        if is_sustainable:
            self.data["sustainable_purchases"] += 1
            self.data["sustainable_spent"] += price
        
        self.save()
        return purchase
    
    def add_wishlist(self, product_id):
        """Add product to wishlist"""
        if product_id not in self.data["wishlist"]:
            self.data["wishlist"].append(product_id)
            self.save()
            return True
        return False
    
    def remove_wishlist(self, product_id):
        """Remove product from wishlist"""
        if product_id in self.data["wishlist"]:
            self.data["wishlist"].remove(product_id)
            self.save()
            return True
        return False
    
    def get_stats(self):
        """Get shopping statistics"""
        total = len(self.data["purchases"])
        sustainable = self.data["sustainable_purchases"]
        
        return {
            "total_purchases": total,
            "sustainable_purchases": sustainable,
            "sustainable_percentage": (sustainable / total * 100) if total > 0 else 0,
            "total_spent": self.data["total_spent"],
            "sustainable_spent": self.data["sustainable_spent"],
            "sustainable_spent_percentage": (self.data["sustainable_spent"] / self.data["total_spent"] * 100) if self.data["total_spent"] > 0 else 0,
            "wishlist_count": len(self.data["wishlist"])
        }

# ============================================================
# SHOPPING IMPACT CALCULATOR
# ============================================================

class ShoppingImpactCalculator:
    """Calculate environmental impact of shopping choices"""
    
    @staticmethod
    def calculate_impact(purchases):
        """Calculate environmental impact"""
        total_carbon = 0
        total_water = 0
        sustainable_count = 0
        
        for purchase in purchases:
            # Find product
            product = next((p for p in ProductDatabase.PRODUCTS if p["id"] == purchase["product_id"]), None)
            if product:
                if purchase["is_sustainable"]:
                    carbon_saving = product["carbon_footprint"] * 0.7
                    water_saving = product["water_usage"] * 0.5
                    total_carbon += carbon_saving
                    total_water += water_saving
                    sustainable_count += 1
                else:
                    total_carbon += product["carbon_footprint"]
                    total_water += product["water_usage"]
        
        return {
            "total_carbon_saved": total_carbon,
            "total_water_saved": total_water,
            "trees_equivalent": total_carbon / 22,
            "sustainable_purchases": sustainable_count
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_ethical_shopping():
    """Render the complete ethical shopping guide"""
    st.markdown("<div class='section-header'>🛍️ Ethical Shopping & Conscious Consumer Guide</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize shopping tracker
    if "shopping_tracker" not in st.session_state:
        st.session_state.shopping_tracker = ShoppingTracker(user_id)
    
    tracker = st.session_state.shopping_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🛍️ Product Scanner",
        "🏷️ Brand Ratings",
        "💚 Wishlist",
        "📊 Shopping Impact",
        "📈 Dashboard"
    ])
    
    with tab1:
        render_product_scanner(tracker)
    
    with tab2:
        render_brand_ratings()
    
    with tab3:
        render_wishlist(tracker)
    
    with tab4:
        render_shopping_impact(tracker)
    
    with tab5:
        render_consumer_dashboard(tracker)

def render_product_scanner(tracker):
    """Render product scanner"""
    st.markdown("### 🛍️ Ethical Product Scanner")
    
    st.markdown("""
    <div class='subtitle'>
        Discover products that align with your values
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        categories = ProductDatabase.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        min_score = st.slider("Minimum Ethical Score", 0, 100, 70)
    
    # Get products
    products = ProductDatabase.get_products(selected_category, min_score)
    
    # Search
    search = st.text_input("🔍 Search Products", placeholder="Search by name or brand...")
    if search:
        products = [p for p in products if search.lower() in p["name"].lower() or search.lower() in p["brand"].lower()]
    
    st.caption(f"📦 {len(products)} products found")
    
    # Display products
    for product in products:
        score_color = "#4ade80" if product["ethical_score"] >= 80 else "#fbbf24" if product["ethical_score"] >= 60 else "#f87171"
        in_wishlist = product["id"] in tracker.data["wishlist"]
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{product['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{product['name']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>🏷️ {product['brand']}</span>
                                <span>📂 {product['category']}</span>
                                <span>💰 ${product['price']:.2f}</span>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                                {product['ethical_score']}/100
                            </span>
                        </div>
                    </div>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin: 6px 0;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{factor}</span>' for factor in product['sustainability_factors'][:3]])}
                    </div>
                    <div style='display: flex; gap: 15px; font-size: 13px;'>
                        <span>🌍 Carbon: {product['carbon_footprint']} kg</span>
                        <span>💧 Water: {product['water_usage']} L</span>
                        <span>📜 {', '.join(product['certifications'])}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            if st.button(f"🔍 Details", key=f"details_{product['id']}"):
                with st.expander("Product Details", expanded=True):
                    st.markdown(f"**Product:** {product['name']}")
                    st.markdown(f"**Brand:** {product['brand']}")
                    st.markdown(f"**Category:** {product['category']}")
                    st.markdown(f"**Price:** ${product['price']:.2f}")
                    st.markdown(f"**Ethical Score:** {product['ethical_score']}/100")
                    st.markdown(f"**Carbon Footprint:** {product['carbon_footprint']} kg CO2")
                    st.markdown(f"**Water Usage:** {product['water_usage']} liters")
                    st.markdown(f"**Certifications:** {', '.join(product['certifications'])}")
                    st.markdown(f"**Sustainability Factors:** {', '.join(product['sustainability_factors'])}")
        
        with col2:
            if in_wishlist:
                if st.button(f"💚 Saved", key=f"wishlist_{product['id']}"):
                    tracker.remove_wishlist(product["id"])
                    st.rerun()
            else:
                if st.button(f"💚 Save", key=f"wishlist_{product['id']}"):
                    tracker.add_wishlist(product["id"])
                    st.success("✅ Added to wishlist!")
                    st.rerun()
        
        with col3:
            if st.button(f"🛒 Buy Sustainably", key=f"buy_{product['id']}"):
                tracker.add_purchase(product["name"], product["id"], product["price"], True)
                st.success("✅ Sustainable purchase recorded!")
                st.rerun()
        
        st.markdown("---")

def render_brand_ratings():
    """Render brand ratings"""
    st.markdown("### 🏷️ Brand Ratings")
    
    st.markdown("""
    <div class='subtitle'>
        Know the companies behind your products
    </div>
    """, unsafe_allow_html=True)
    
    # Industry filter
    industries = BrandDatabase.get_industries()
    selected_industry = st.selectbox("Filter by Industry", industries)
    
    # Get brands
    brands = BrandDatabase.get_brands(selected_industry)
    
    for brand in brands:
        avg_score = (brand["environmental_score"] + brand["social_score"]) / 2
        score_color = "#4ade80" if avg_score >= 80 else "#fbbf24" if avg_score >= 60 else "#f87171"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <span style='font-size: 24px;'>{brand['emoji']}</span>
                        <div>
                            <div style='font-weight: 700; font-size: 16px;'>{brand['name']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>{brand['industry']}</div>
                        </div>
                    </div>
                    <div style='display: flex; gap: 15px; margin: 6px 0; font-size: 13px;'>
                        <span>🌿 Environmental: {brand['environmental_score']}/100</span>
                        <span>🤝 Social: {brand['social_score']}/100</span>
                        <span>🔍 Transparency: {brand['transparency_score']}/100</span>
                    </div>
                    <div style='font-size: 13px; color: #4ade80;'>
                        💚 {brand['sustainability_commitment']}
                    </div>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{cert}</span>' for cert in brand['certifications'][:3]])}
                    </div>
                </div>
                <div style='text-align: right;'>
                    <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                        {avg_score:.0f}/100
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")

def render_wishlist(tracker):
    """Render wishlist"""
    st.markdown("### 💚 My Wishlist")
    
    stats = tracker.get_stats()
    st.caption(f"📋 {stats['wishlist_count']} items in your wishlist")
    
    if tracker.data["wishlist"]:
        for product_id in tracker.data["wishlist"]:
            product = next((p for p in ProductDatabase.PRODUCTS if p["id"] == product_id), None)
            if product:
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 600;'>{product['emoji']} {product['name']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {product['brand']} • ${product['price']:.2f} • {product['category']}
                            </div>
                            <div style='font-size: 12px; color: #4ade80;'>
                                Ethical Score: {product['ethical_score']}/100
                            </div>
                        </div>
                        <div style='display: flex; gap: 10px;'>
                            <button onclick="st.session_state.remove_wishlist('{product['id']}')" style='background: none; border: none; color: #f87171; cursor: pointer;'>
                                ❌ Remove
                            </button>
                            <button onclick="st.session_state.buy_{product['id']} = True" style='background: #4ade80; border: none; padding: 4px 12px; border-radius: 8px; cursor: pointer;'>
                                🛒 Buy
                            </button>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🛒 Buy {product['name']}", key=f"wish_buy_{product['id']}"):
                    tracker.add_purchase(product["name"], product["id"], product["price"], True)
                    tracker.remove_wishlist(product["id"])
                    st.success("✅ Purchased and removed from wishlist!")
                    st.rerun()
                
                if st.button(f"❌ Remove {product['name']}", key=f"wish_remove_{product['id']}"):
                    tracker.remove_wishlist(product["id"])
                    st.rerun()
                
                st.markdown("---")
    else:
        st.info("💚 Your wishlist is empty. Browse products and save your favorites!")

def render_shopping_impact(tracker):
    """Render shopping impact"""
    st.markdown("### 📊 Shopping Impact Calculator")
    
    purchases = tracker.data["purchases"]
    
    if purchases:
        impact = ShoppingImpactCalculator.calculate_impact(purchases)
        stats = tracker.get_stats()
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("CO₂ Saved", f"{impact['total_carbon_saved']:.1f} kg")
        col2.metric("Water Saved", f"{impact['total_water_saved']:.1f} L")
        col3.metric("Trees Equivalent", f"{impact['trees_equivalent']:.1f}")
        col4.metric("Sustainable Purchases", impact['sustainable_purchases'])
        
        # Progress
        st.markdown("#### 🌱 Sustainable Spending Progress")
        st.progress(stats['sustainable_percentage'] / 100)
        st.caption(f"{stats['sustainable_percentage']:.1f}% of purchases are sustainable")
        
        # Comparison chart
        st.markdown("#### 📊 Spending Breakdown")
        
        spending_data = {
            "Category": ["Sustainable", "Traditional"],
            "Amount": [stats['sustainable_spent'], stats['total_spent'] - stats['sustainable_spent']]
        }
        
        fig = go.Figure(data=[go.Pie(
            labels=spending_data["Category"],
            values=spending_data["Amount"],
            hole=0.3,
            marker=dict(colors=['#4ade80', '#6b7280'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.markdown("#### 💡 Recommendations")
        
        if stats['sustainable_percentage'] < 50:
            st.info("🌱 Try to increase sustainable purchases by 20% this month")
        elif stats['sustainable_percentage'] < 80:
            st.info("🌿 Good progress! Consider switching to sustainable alternatives")
        else:
            st.success("🌟 Excellent! You're a conscious consumer leader!")
        
    else:
        st.info("📊 Start tracking your purchases to see your shopping impact")

def render_consumer_dashboard(tracker):
    """Render consumer dashboard"""
    st.markdown("### 📈 Consumer Dashboard")
    
    stats = tracker.get_stats()
    
    # Overall score
    consumer_score = stats['sustainable_percentage']
    
    st.markdown("#### 🏆 Conscious Consumer Score")
    st.progress(consumer_score / 100)
    st.caption(f"{consumer_score:.0f}/100 - {'Conscious Consumer' if consumer_score > 70 else 'Developing' if consumer_score > 40 else 'Building Awareness'}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Purchases", stats['total_purchases'])
    col2.metric("Sustainable", stats['sustainable_purchases'])
    col3.metric("Sustain. %", f"{stats['sustainable_percentage']:.0f}%")
    col4.metric("Wishlist", stats['wishlist_count'])
    
    # Recent purchases
    st.markdown("#### 📋 Recent Purchases")
    
    if tracker.data["purchases"]:
        recent = tracker.data["purchases"][-5:]
        for purchase in recent[::-1]:
            date = datetime.fromisoformat(purchase["date"]).strftime("%b %d, %Y")
            sustainability = "🌿 Sustainable" if purchase["is_sustainable"] else "🔄 Traditional"
            st.markdown(f"• {date}: {purchase['product']} - ${purchase['price']:.2f} ({sustainability})")
    else:
        st.info("No purchases recorded yet")
    
    # Goals
    st.markdown("#### 🎯 Sustainable Shopping Goals")
    
    goals = [
        {"goal": "Increase sustainable purchases by 10%", "progress": min(100, stats['sustainable_percentage'] + 10)},
        {"goal": "Reduce carbon footprint by 20%", "progress": min(100, stats['sustainable_percentage'] * 0.8)},
        {"goal": "Support 5 ethical brands", "progress": min(100, len(set(p['brand'] for p in ProductDatabase.PRODUCTS if p['ethical_score'] > 80)))}
    ]
    
    for goal in goals:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{goal['goal']}</div>
                </div>
                <span style='font-weight: 700; color: #4ade80;'>{min(100, int(goal['progress']))}%</span>
            </div>
            <div style='margin-top: 4px;'>
                <div class='progress-bar' style='height: 4px;'>
                    <div class='progress-fill' style='width: {min(100, goal['progress'])}%;'></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_consumer_hub():
    """Render the complete consumer hub"""
    render_ethical_shopping()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from ethical_shopping import render_consumer_hub

# Add as a new tab
with tab40:
    render_consumer_hub()
"""