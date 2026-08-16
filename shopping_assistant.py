

# ============================================================
# FILE: shopping_assistant.py
# EcoBuddy AI+ Eco-Smart Shopping Assistant
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
    """Database of products with sustainability ratings"""
    
    PRODUCTS = [
        {
            "id": "p1",
            "name": "Organic Cotton T-Shirt",
            "category": "Clothing",
            "brand": "EcoWear",
            "price": 45.00,
            "sustainability_score": 88,
            "carbon_footprint": 15,
            "water_usage": 2000,
            "packaging": "Recycled cardboard",
            "certifications": ["GOTS", "Fair Trade"],
            "emoji": "👕",
            "description": "100% organic cotton, low-impact dyes"
        },
        {
            "id": "p2",
            "name": "Recycled Polyester Jacket",
            "category": "Clothing",
            "brand": "GreenWear",
            "price": 89.00,
            "sustainability_score": 82,
            "carbon_footprint": 20,
            "water_usage": 800,
            "packaging": "Recycled plastic",
            "certifications": ["GRS"],
            "emoji": "🧥",
            "description": "Made from recycled plastic bottles"
        },
        {
            "id": "p3",
            "name": "Bamboo Toothbrush Set",
            "category": "Personal Care",
            "brand": "EcoSmile",
            "price": 12.99,
            "sustainability_score": 92,
            "carbon_footprint": 2,
            "water_usage": 150,
            "packaging": "Compostable",
            "certifications": ["Plastic Free"],
            "emoji": "🪥",
            "description": "Biodegradable bamboo handle"
        },
        {
            "id": "p4",
            "name": "Reusable Water Bottle",
            "category": "Kitchen",
            "brand": "EcoHydrate",
            "price": 24.99,
            "sustainability_score": 90,
            "carbon_footprint": 5,
            "water_usage": 300,
            "packaging": "Recycled cardboard",
            "certifications": ["BPA Free"],
            "emoji": "🍶",
            "description": "Stainless steel, vacuum insulated"
        },
        {
            "id": "p5",
            "name": "LED Light Bulb 10-pack",
            "category": "Home",
            "brand": "EcoLight",
            "price": 29.99,
            "sustainability_score": 85,
            "carbon_footprint": 8,
            "water_usage": 200,
            "packaging": "Recycled paper",
            "certifications": ["Energy Star"],
            "emoji": "💡",
            "description": "75% less energy than traditional bulbs"
        },
        {
            "id": "p6",
            "name": "Plant-Based Laundry Detergent",
            "category": "Cleaning",
            "brand": "EcoClean",
            "price": 15.99,
            "sustainability_score": 88,
            "carbon_footprint": 6,
            "water_usage": 150,
            "packaging": "Recyclable jug",
            "certifications": ["Cruelty Free"],
            "emoji": "🧺",
            "description": "Plant-based, biodegradable formula"
        },
        {
            "id": "p7",
            "name": "Reusable Grocery Bags Set",
            "category": "Home",
            "brand": "EcoCarry",
            "price": 19.99,
            "sustainability_score": 94,
            "carbon_footprint": 3,
            "water_usage": 100,
            "packaging": "Recycled fabric",
            "certifications": ["Plastic Free"],
            "emoji": "🛍️",
            "description": "Cotton canvas, machine washable"
        },
        {
            "id": "p8",
            "name": "Solar Power Bank",
            "category": "Electronics",
            "brand": "EcoCharge",
            "price": 59.99,
            "sustainability_score": 86,
            "carbon_footprint": 12,
            "water_usage": 400,
            "packaging": "Recycled cardboard",
            "certifications": ["Solar Certified"],
            "emoji": "🔋",
            "description": "Charges devices using solar energy"
        },
        {
            "id": "p9",
            "name": "Beeswax Food Wraps Set",
            "category": "Kitchen",
            "brand": "EcoWrap",
            "price": 22.99,
            "sustainability_score": 91,
            "carbon_footprint": 4,
            "water_usage": 120,
            "packaging": "Compostable",
            "certifications": ["Zero Waste"],
            "emoji": "🧻",
            "description": "Reusable alternative to plastic wrap"
        },
        {
            "id": "p10",
            "name": "Sustainable Sneakers",
            "category": "Clothing",
            "brand": "EcoStep",
            "price": 79.99,
            "sustainability_score": 84,
            "carbon_footprint": 18,
            "water_usage": 600,
            "packaging": "Recycled cardboard",
            "certifications": ["B Corp"],
            "emoji": "👟",
            "description": "Made from recycled ocean plastic"
        },
        {
            "id": "p11",
            "name": "Compostable Phone Case",
            "category": "Electronics",
            "brand": "EcoCase",
            "price": 34.99,
            "sustainability_score": 89,
            "carbon_footprint": 3,
            "water_usage": 80,
            "packaging": "Compostable",
            "certifications": ["Plastic Free"],
            "emoji": "📱",
            "description": "Plant-based, fully compostable case"
        },
        {
            "id": "p12",
            "name": "Organic Face Moisturizer",
            "category": "Personal Care",
            "brand": "EcoGlow",
            "price": 28.99,
            "sustainability_score": 87,
            "carbon_footprint": 5,
            "water_usage": 180,
            "packaging": "Glass jar, recyclable",
            "certifications": ["Organic"],
            "emoji": "🧴",
            "description": "100% natural, organic ingredients"
        }
    ]
    
    @staticmethod
    def get_products(category=None, min_score=None):
        """Get products with filters"""
        products = ProductDatabase.PRODUCTS.copy()
        if category and category != "All":
            products = [p for p in products if p["category"] == category]
        if min_score:
            products = [p for p in products if p["sustainability_score"] >= min_score]
        return products
    
    @staticmethod
    def get_categories():
        """Get product categories"""
        return ["All"] + sorted(set(p["category"] for p in ProductDatabase.PRODUCTS))
    
    @staticmethod
    def get_brands():
        """Get all brands"""
        return sorted(set(p["brand"] for p in ProductDatabase.PRODUCTS))

# ============================================================
# SUSTAINABILITY SCORE CALCULATOR
# ============================================================

class SustainabilityScorer:
    """Calculate and compare product sustainability"""
    
    @staticmethod
    def calculate_score(product):
        """Calculate sustainability score for a product"""
        # Base score from database
        base_score = product.get("sustainability_score", 50)
        
        # Adjust for certifications
        cert_bonus = len(product.get("certifications", [])) * 3
        
        # Adjust for packaging
        packaging_scores = {
            "Compostable": 10,
            "Recycled cardboard": 8,
            "Recycled paper": 7,
            "Recyclable jug": 6,
            "Recycled plastic": 5,
            "Recycled fabric": 7,
            "Glass jar, recyclable": 8,
            "Recycled cardboard": 8
        }
        packaging_bonus = packaging_scores.get(product.get("packaging", ""), 0)
        
        # Adjust for carbon footprint
        carbon_penalty = max(0, product.get("carbon_footprint", 20) - 10)
        
        final_score = min(100, base_score + cert_bonus + packaging_bonus - carbon_penalty)
        return max(0, final_score)
    
    @staticmethod
    def compare_products(product1, product2):
        """Compare two products"""
        score1 = SustainabilityScorer.calculate_score(product1)
        score2 = SustainabilityScorer.calculate_score(product2)
        
        return {
            "product1": {
                "name": product1["name"],
                "score": score1,
                "carbon": product1.get("carbon_footprint", 0),
                "water": product1.get("water_usage", 0),
                "price": product1.get("price", 0)
            },
            "product2": {
                "name": product2["name"],
                "score": score2,
                "carbon": product2.get("carbon_footprint", 0),
                "water": product2.get("water_usage", 0),
                "price": product2.get("price", 0)
            },
            "winner": product1["name"] if score1 > score2 else product2["name"] if score2 > score1 else "Tie",
            "recommendation": f"{product1['name']} is more sustainable" if score1 > score2 else f"{product2['name']} is more sustainable" if score2 > score1 else "Both are equally sustainable"
        }

# ============================================================
# BRAND SUSTAINABILITY RATINGS
# ============================================================

class BrandRatings:
    """Sustainability ratings for brands"""
    
    BRANDS = {
        "EcoWear": {"score": 85, "ethics": "Fair Trade", "transparency": "High"},
        "GreenWear": {"score": 82, "ethics": "Recycled Materials", "transparency": "Medium"},
        "EcoSmile": {"score": 90, "ethics": "Plastic Free", "transparency": "High"},
        "EcoHydrate": {"score": 88, "ethics": "BPA Free", "transparency": "High"},
        "EcoLight": {"score": 83, "ethics": "Energy Efficient", "transparency": "Medium"},
        "EcoClean": {"score": 86, "ethics": "Cruelty Free", "transparency": "High"},
        "EcoCarry": {"score": 92, "ethics": "Plastic Free", "transparency": "High"},
        "EcoCharge": {"score": 84, "ethics": "Solar Certified", "transparency": "Medium"},
        "EcoWrap": {"score": 89, "ethics": "Zero Waste", "transparency": "High"},
        "EcoStep": {"score": 82, "ethics": "B Corp", "transparency": "Medium"},
        "EcoCase": {"score": 87, "ethics": "Plastic Free", "transparency": "High"},
        "EcoGlow": {"score": 85, "ethics": "Organic", "transparency": "High"}
    }
    
    @staticmethod
    def get_brand_score(brand):
        """Get sustainability score for a brand"""
        return BrandRatings.BRANDS.get(brand, {"score": 50, "ethics": "Unknown", "transparency": "Low"})
    
    @staticmethod
    def get_top_brands(limit=5):
        """Get top sustainable brands"""
        sorted_brands = sorted(BrandRatings.BRANDS.items(), key=lambda x: x[1]["score"], reverse=True)
        return sorted_brands[:limit]

# ============================================================
# SHOPPING TIPS
# ============================================================

class ShoppingTips:
    """Sustainable shopping tips"""
    
    TIPS = [
        {
            "title": "🌿 Buy Local",
            "description": "Reduce transportation emissions by buying locally produced goods",
            "category": "Buying"
        },
        {
            "title": "♻️ Choose Recycled",
            "description": "Look for products made from recycled materials",
            "category": "Materials"
        },
        {
            "title": "📦 Minimal Packaging",
            "description": "Choose products with minimal or compostable packaging",
            "category": "Packaging"
        },
        {
            "title": "🔋 Energy Efficient",
            "description": "Look for Energy Star certified electronics and appliances",
            "category": "Energy"
        },
        {
            "title": "🧵 Quality Over Quantity",
            "description": "Invest in durable products that last longer",
            "category": "Buying"
        },
        {
            "title": "📱 Check Certifications",
            "description": "Look for GOTS, Fair Trade, B Corp, and other certifications",
            "category": "Certifications"
        },
        {
            "title": "🔄 Buy Second-Hand",
            "description": "Consider pre-owned items to extend product lifecycles",
            "category": "Buying"
        },
        {
            "title": "🌱 Plant-Based Materials",
            "description": "Choose products made from bamboo, hemp, or organic cotton",
            "category": "Materials"
        }
    ]
    
    @staticmethod
    def get_tips(category=None):
        """Get tips by category"""
        if category:
            return [t for t in ShoppingTips.TIPS if t["category"] == category]
        return ShoppingTips.TIPS
    
    @staticmethod
    def get_categories():
        """Get tip categories"""
        return sorted(set(t["category"] for t in ShoppingTips.TIPS))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_shopping_assistant():
    """Render the complete shopping assistant"""
    st.markdown("<div class='section-header'>🛒 Eco-Smart Shopping Assistant</div>", unsafe_allow_html=True)
    
    # Initialize session state
    if "shopping_history" not in st.session_state:
        st.session_state.shopping_history = []
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🛒 Product Scanner",
        "📊 Compare Products",
        "🏷️ Brand Ratings",
        "💡 Shopping Tips"
    ])
    
    with tab1:
        render_product_scanner()
    
    with tab2:
        render_product_comparison()
    
    with tab3:
        render_brand_ratings()
    
    with tab4:
        render_shopping_tips()

def render_product_scanner():
    """Render product scanner"""
    st.markdown("### 🛒 Product Sustainability Scanner")
    
    # Search and filter
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ProductDatabase.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        min_score = st.slider("Minimum Sustainability Score", 0, 100, 70)
    
    with col3:
        search = st.text_input("🔍 Search Product", placeholder="Product name...")
    
    # Get products
    products = ProductDatabase.get_products(selected_category, min_score)
    
    if search:
        products = [p for p in products if search.lower() in p["name"].lower()]
    
    st.caption(f"📦 {len(products)} products found")
    
    # Display products
    for product in products:
        score = SustainabilityScorer.calculate_score(product)
        score_color = "#4ade80" if score >= 80 else "#fbbf24" if score >= 60 else "#f87171"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{product['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{product['name']}</h4>
                            <span style='font-size: 13px; color: #6b7280;'>{product['brand']} • {product['category']}</span>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 14px;'>
                                {score}/100
                            </span>
                            <div style='font-size: 13px; color: #4ade80;'>${product['price']:.2f}</div>
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{product['description']}</p>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px;'>
                        <span>🌍 Carbon: {product['carbon_footprint']} kg</span>
                        <span>💧 Water: {product['water_usage']} L</span>
                        <span>📦 {product['packaging']}</span>
                    </div>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{cert}</span>' for cert in product.get('certifications', [])])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button(f"🔍 Details", key=f"details_{product['id']}"):
                with st.expander("Product Details", expanded=True):
                    st.markdown(f"**Name:** {product['name']}")
                    st.markdown(f"**Brand:** {product['brand']}")
                    st.markdown(f"**Category:** {product['category']}")
                    st.markdown(f"**Price:** ${product['price']:.2f}")
                    st.markdown(f"**Sustainability Score:** {score}/100")
                    st.markdown(f"**Carbon Footprint:** {product['carbon_footprint']} kg CO2")
                    st.markdown(f"**Water Usage:** {product['water_usage']} liters")
                    st.markdown(f"**Packaging:** {product['packaging']}")
                    st.markdown(f"**Certifications:** {', '.join(product.get('certifications', []))}")
        
        with col2:
            if st.button(f"📝 Compare", key=f"compare_{product['id']}"):
                st.session_state.compare_product = product['id']
                st.rerun()

def render_product_comparison():
    """Render product comparison"""
    st.markdown("### 📊 Compare Products")
    
    # Select products to compare
    products = ProductDatabase.get_products()
    product_options = [p["name"] for p in products]
    
    col1, col2 = st.columns(2)
    
    with col1:
        product1_name = st.selectbox("Select First Product", product_options, key="comp1")
    
    with col2:
        product2_name = st.selectbox("Select Second Product", product_options, key="comp2")
    
    if product1_name and product2_name and product1_name != product2_name:
        product1 = next(p for p in products if p["name"] == product1_name)
        product2 = next(p for p in products if p["name"] == product2_name)
        
        # Calculate scores
        score1 = SustainabilityScorer.calculate_score(product1)
        score2 = SustainabilityScorer.calculate_score(product2)
        
        comparison = SustainabilityScorer.compare_products(product1, product2)
        
        st.markdown("#### Comparison Results")
        
        # Display side by side
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='text-align: center;'>
                    <div style='font-size: 40px;'>{product1['emoji']}</div>
                    <h4 style='color: #4ade80;'>{product1['name']}</h4>
                    <div style='font-size: 36px; font-weight: 700; color: {"#4ade80" if score1 > score2 else "#6b7280"};'>
                        {score1}/100
                    </div>
                    <div style='display: flex; justify-content: center; gap: 20px; margin-top: 10px;'>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Carbon</div>
                            <div>{product1['carbon_footprint']} kg</div>
                        </div>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Water</div>
                            <div>{product1['water_usage']} L</div>
                        </div>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Price</div>
                            <div>${product1['price']:.2f}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='text-align: center;'>
                    <div style='font-size: 40px;'>{product2['emoji']}</div>
                    <h4 style='color: #4ade80;'>{product2['name']}</h4>
                    <div style='font-size: 36px; font-weight: 700; color: {"#4ade80" if score2 > score1 else "#6b7280"};'>
                        {score2}/100
                    </div>
                    <div style='display: flex; justify-content: center; gap: 20px; margin-top: 10px;'>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Carbon</div>
                            <div>{product2['carbon_footprint']} kg</div>
                        </div>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Water</div>
                            <div>{product2['water_usage']} L</div>
                        </div>
                        <div>
                            <div style='font-size: 12px; color: #6b7280;'>Price</div>
                            <div>${product2['price']:.2f}</div>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # Winner
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {"#4ade80" if score1 > score2 else "#fbbf24" if score2 > score1 else "#6b7280"};'>
            <div style='text-align: center;'>
                <div style='font-size: 24px; font-weight: 700;'>{comparison['recommendation']}</div>
                <div style='font-size: 14px; color: #6b7280;'>
                    Score difference: {abs(score1 - score2)} points
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Environmental impact visualization
        st.markdown("#### Environmental Impact Comparison")
        
        impact_data = {
            "Product": [product1['name'], product2['name']],
            "Carbon": [product1['carbon_footprint'], product2['carbon_footprint']],
            "Water": [product1['water_usage'], product2['water_usage']]
        }
        
        df_impact = pd.DataFrame(impact_data)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df_impact['Product'],
            y=df_impact['Carbon'],
            name='Carbon (kg)',
            marker_color='#fbbf24'
        ))
        fig.add_trace(go.Bar(
            x=df_impact['Product'],
            y=df_impact['Water'],
            name='Water (L)',
            marker_color='#60a5fa'
        ))
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=20, b=0),
            barmode='group'
        )
        st.plotly_chart(fig, use_container_width=True)

def render_brand_ratings():
    """Render brand ratings"""
    st.markdown("### 🏷️ Brand Sustainability Ratings")
    
    # Top brands
    top_brands = BrandRatings.get_top_brands(5)
    
    st.markdown("#### 🌟 Top Sustainable Brands")
    
    for i, (brand, data) in enumerate(top_brands, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "4️⃣"
        
        score_color = "#4ade80" if data["score"] >= 80 else "#fbbf24" if data["score"] >= 60 else "#f87171"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <span style='font-size: 20px;'>{medal}</span>
                    <span style='font-weight: 700; font-size: 16px;'>{brand}</span>
                    <div style='font-size: 13px; color: #6b7280;'>
                        {data['ethics']} • Transparency: {data['transparency']}
                    </div>
                </div>
                <span style='background: {score_color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700;'>
                    {data['score']}/100
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # All brands
    st.markdown("#### 📋 All Brand Ratings")
    
    all_brands = sorted(BrandRatings.BRANDS.items(), key=lambda x: x[1]["score"], reverse=True)
    
    brand_data = []
    for brand, data in all_brands:
        brand_data.append({
            "Brand": brand,
            "Score": data["score"],
            "Ethics": data["ethics"],
            "Transparency": data["transparency"]
        })
    
    df_brands = pd.DataFrame(brand_data)
    st.dataframe(df_brands, use_container_width=True, hide_index=True)

def render_shopping_tips():
    """Render shopping tips"""
    st.markdown("### 💡 Sustainable Shopping Tips")
    
    # Category filter
    categories = ["All"] + ShoppingTips.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get tips
    if selected_category == "All":
        tips = ShoppingTips.get_tips()
    else:
        tips = ShoppingTips.get_tips(selected_category)
    
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

# ============================================================
# INTEGRATION
# ============================================================

def render_shopping_hub():
    """Render the complete shopping hub"""
    render_shopping_assistant()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from shopping_assistant import render_shopping_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22, tab23, tab24, tab25 = st.tabs([
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
    "👗 Fashion",
    "🏅 Certification",
    "🛒 Shopping"  # NEW
])

with tab25:
    render_shopping_hub()
"""