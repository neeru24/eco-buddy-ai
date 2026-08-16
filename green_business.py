
# ============================================================
# FILE: green_business.py
# EcoBuddy AI+ Green Business Accelerator
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# BUSINESS PLANNING
# ============================================================

class BusinessPlan:
    """Green business planning tools"""
    
    BUSINESS_MODELS = {
        "Product": "Selling sustainable products",
        "Service": "Providing eco-services",
        "Platform": "Connecting sustainable providers",
        "B2B": "Sustainable business solutions",
        "Social Enterprise": "Mission-driven business"
    }
    
    SUSTAINABILITY_FOCUS = {
        "Carbon Reduction": "Products/services that reduce emissions",
        "Waste Management": "Solutions for waste reduction",
        "Clean Energy": "Renewable energy solutions",
        "Water Conservation": "Water efficiency and conservation",
        "Biodiversity": "Products/services protecting ecosystems",
        "Sustainable Agriculture": "Eco-friendly farming solutions",
        "Circular Economy": "Products/services enabling circularity"
    }
    
    @staticmethod
    def get_business_models():
        """Get business models"""
        return BusinessPlan.BUSINESS_MODELS
    
    @staticmethod
    def get_sustainability_focus():
        """Get sustainability focus areas"""
        return BusinessPlan.SUSTAINABILITY_FOCUS

# ============================================================
# IMPACT CALCULATOR
# ============================================================

class ImpactCalculator:
    """Calculate business environmental impact"""
    
    @staticmethod
    def calculate_impact(business_type, products_sold, customers, employees):
        """Calculate environmental impact"""
        
        # Impact factors per business type
        impact_factors = {
            "Product": 1.0,
            "Service": 0.5,
            "Platform": 0.8,
            "B2B": 1.2,
            "Social Enterprise": 1.5
        }
        
        factor = impact_factors.get(business_type, 1.0)
        
        # Carbon impact estimation
        carbon_impact = products_sold * 0.1 * factor  # kg CO2 per product
        if employees > 0:
            carbon_impact += employees * 50  # kg CO2 per employee
        
        # Impact reduction (sustainability efforts)
        impact_reduction = 30 + random.randint(0, 40)  # percentage
        
        # Number of customers reached
        customer_reach = customers * 100
        
        return {
            "carbon_impact": carbon_impact * (1 - impact_reduction/100),
            "impact_reduction": impact_reduction,
            "customer_reach": customer_reach,
            "jobs_created": employees,
            "trees_equivalent": carbon_impact / 22
        }

# ============================================================
# FUNDING DATABASE
# ============================================================

class FundingDatabase:
    """Green funding opportunities"""
    
    FUNDING = [
        {
            "name": "Green Innovation Fund",
            "type": "Grant",
            "amount": "$50,000 - $500,000",
            "focus": "Clean Energy",
            "deadline": datetime.now() + timedelta(days=45),
            "description": "Supporting innovative clean energy solutions",
            "application": "https://example.com/green-innovation"
        },
        {
            "name": "Impact Investor Network",
            "type": "Investment",
            "amount": "$100,000 - $5,000,000",
            "focus": "All",
            "deadline": datetime.now() + timedelta(days=60),
            "description": "Venture capital for sustainable startups",
            "application": "https://example.com/impact-invest"
        },
        {
            "name": "Sustainability Accelerator",
            "type": "Program",
            "amount": "$25,000 + Mentorship",
            "focus": "Early Stage",
            "deadline": datetime.now() + timedelta(days=30),
            "description": "Accelerator program for green startups",
            "application": "https://example.com/sustainability-accel"
        },
        {
            "name": "Circular Economy Grant",
            "type": "Grant",
            "amount": "$20,000 - $100,000",
            "focus": "Waste Management",
            "deadline": datetime.now() + timedelta(days=90),
            "description": "Funding for circular economy innovations",
            "application": "https://example.com/circular-economy"
        },
        {
            "name": "Climate Tech Fund",
            "type": "Investment",
            "amount": "$250,000 - $10,000,000",
            "focus": "Climate Tech",
            "deadline": datetime.now() + timedelta(days=120),
            "description": "Series A funding for climate solutions",
            "application": "https://example.com/climate-tech"
        },
        {
            "name": "Women in Green Tech",
            "type": "Grant",
            "amount": "$10,000 - $50,000",
            "focus": "Green Tech",
            "deadline": datetime.now() + timedelta(days=15),
            "description": "Supporting women entrepreneurs in green tech",
            "application": "https://example.com/women-green"
        }
    ]
    
    @staticmethod
    def get_funding(funding_type=None, focus=None):
        """Get funding opportunities with filters"""
        funding = FundingDatabase.FUNDING.copy()
        if funding_type and funding_type != "All":
            funding = [f for f in funding if f["type"] == funding_type]
        if focus and focus != "All":
            funding = [f for f in funding if focus in f["focus"]]
        return funding
    
    @staticmethod
    def get_types():
        """Get funding types"""
        return ["All"] + sorted(set(f["type"] for f in FundingDatabase.FUNDING))
    
    @staticmethod
    def get_focus_areas():
        """Get focus areas"""
        focuses = set()
        for f in FundingDatabase.FUNDING:
            for area in f["focus"].split(", "):
                focuses.add(area)
        return ["All"] + sorted(list(focuses))

# ============================================================
# MENTORSHIP NETWORK
# ============================================================

class MentorshipNetwork:
    """Mentorship network for green entrepreneurs"""
    
    MENTORS = [
        {
            "name": "Dr. Sarah Green",
            "expertise": ["Clean Energy", "Business Strategy"],
            "experience": "15 years",
            "industry": "Energy",
            "available": True,
            "bio": "Renewable energy expert with experience scaling clean tech startups"
        },
        {
            "name": "Michael Eco",
            "expertise": ["Waste Management", "Circular Economy"],
            "experience": "12 years",
            "industry": "Waste",
            "available": True,
            "bio": "Circular economy specialist with experience in waste reduction"
        },
        {
            "name": "Dr. Lisa Sustainable",
            "expertise": ["Sustainable Agriculture", "Impact Investing"],
            "experience": "18 years",
            "industry": "Agriculture",
            "available": False,
            "bio": "Expert in sustainable agriculture and impact investment"
        },
        {
            "name": "David GreenTech",
            "expertise": ["Green Tech", "Product Development"],
            "experience": "10 years",
            "industry": "Technology",
            "available": True,
            "bio": "Green technology product developer and innovation strategist"
        }
    ]
    
    @staticmethod
    def get_mentors():
        """Get all mentors"""
        return MentorshipNetwork.MENTORS
    
    @staticmethod
    def get_expertise_areas():
        """Get all expertise areas"""
        areas = set()
        for mentor in MentorshipNetwork.MENTORS:
            for expertise in mentor["expertise"]:
                areas.add(expertise)
        return sorted(list(areas))

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_green_business():
    """Render the complete green business accelerator"""
    st.markdown("<div class='section-header'>🚀 Green Business Accelerator</div>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📋 Business Planning",
        "📊 Impact Calculator",
        "💰 Funding Resources",
        "🤝 Mentorship",
        "📈 Dashboard"
    ])
    
    with tab1:
        render_business_planning()
    
    with tab2:
        render_impact_calculator()
    
    with tab3:
        render_funding_resources()
    
    with tab4:
        render_mentorship()
    
    with tab5:
        render_business_dashboard()

def render_business_planning():
    """Render business planning"""
    st.markdown("### 📋 Green Business Planning")
    
    st.markdown("""
    <div class='subtitle'>
        Plan your sustainable venture with our guided tools
    </div>
    """, unsafe_allow_html=True)
    
    # Business basics
    with st.form("business_plan_form"):
        st.markdown("#### 💼 Business Basics")
        
        col1, col2 = st.columns(2)
        with col1:
            business_name = st.text_input("Business Name")
            business_model = st.selectbox("Business Model", list(BusinessPlan.get_business_models().keys()))
        
        with col2:
            sustainability_focus = st.selectbox("Sustainability Focus", list(BusinessPlan.get_sustainability_focus().keys()))
            stage = st.selectbox("Business Stage", ["Idea", "Pre-Seed", "Seed", "Series A", "Growth"])
        
        st.markdown("#### 🎯 Mission & Vision")
        mission = st.text_area("Mission Statement", placeholder="Your sustainability mission...")
        vision = st.text_area("Vision Statement", placeholder="Your long-term vision...")
        
        st.markdown("#### 📊 Business Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            target_revenue = st.number_input("Target Revenue ($)", min_value=0, value=100000, step=10000)
        with col2:
            target_customers = st.number_input("Target Customers", min_value=0, value=1000, step=100)
        with col3:
            target_employees = st.number_input("Target Employees", min_value=0, value=5, step=1)
        
        if st.form_submit_button("Save Business Plan"):
            st.success("✅ Business plan saved successfully!")
            st.balloons()
    
    # Business model canvas
    st.markdown("#### 🗺️ Business Model Canvas")
    
    canvas_elements = {
        "Value Proposition": "What problem do you solve?",
        "Customer Segments": "Who are your customers?",
        "Channels": "How do you reach customers?",
        "Customer Relationships": "How do you interact with customers?",
        "Revenue Streams": "How do you make money?",
        "Key Resources": "What resources do you need?",
        "Key Activities": "What do you do?",
        "Key Partners": "Who helps you?",
        "Cost Structure": "What are your costs?"
    }
    
    for element, placeholder in canvas_elements.items():
        st.text_area(element, placeholder=placeholder, key=f"canvas_{element}")

def render_impact_calculator():
    """Render impact calculator"""
    st.markdown("### 📊 Environmental Impact Calculator")
    
    st.markdown("""
    <div class='subtitle'>
        Measure and project your business's environmental impact
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        business_type = st.selectbox("Business Type", ["Product", "Service", "Platform", "B2B", "Social Enterprise"])
        products_sold = st.number_input("Monthly Products/Services Sold", min_value=0, value=1000, step=100)
    
    with col2:
        customers = st.number_input("Monthly Customers", min_value=0, value=500, step=50)
        employees = st.number_input("Number of Employees", min_value=0, value=10, step=1)
    
    if st.button("🌿 Calculate Impact", type="primary", use_container_width=True):
        impact = ImpactCalculator.calculate_impact(business_type, products_sold, customers, employees)
        
        st.markdown("#### 📊 Your Environmental Impact")
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Carbon Impact", f"{impact['carbon_impact']:.0f} kg CO2")
        col2.metric("Impact Reduction", f"{impact['impact_reduction']:.0f}%")
        col3.metric("Customer Reach", f"{impact['customer_reach']:,.0f}")
        col4.metric("Jobs Created", impact['jobs_created'])
        
        # Trees equivalent
        st.metric("🌳 Trees Equivalent", f"{impact['trees_equivalent']:.0f} trees")
        
        # Impact visualization
        impact_data = {
            "Category": ["Carbon Impact", "Impact Reduction", "Customer Reach"],
            "Value": [impact['carbon_impact'], impact['impact_reduction'], impact['customer_reach']/1000]
        }
        
        fig = go.Figure(data=[go.Bar(
            x=impact_data["Category"],
            y=impact_data["Value"],
            marker_color=['#f87171', '#4ade80', '#60a5fa']
        )])
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title="Impact Value"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Recommendations
        st.markdown("#### 💡 Impact Recommendations")
        
        recs = []
        if impact['carbon_impact'] > 1000:
            recs.append("🌱 Consider switching to renewable energy sources")
        if impact['impact_reduction'] < 50:
            recs.append("♻️ Implement more sustainability practices in your operations")
        if employees > 0:
            recs.append("👥 Implement employee sustainability training")
        
        for rec in recs:
            st.info(rec)

def render_funding_resources():
    """Render funding resources"""
    st.markdown("### 💰 Green Funding Resources")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        funding_types = FundingDatabase.get_types()
        selected_type = st.selectbox("Funding Type", funding_types)
    
    with col2:
        focus_areas = FundingDatabase.get_focus_areas()
        selected_focus = st.selectbox("Focus Area", focus_areas)
    
    # Get funding
    funding = FundingDatabase.get_funding(selected_type, selected_focus)
    
    st.caption(f"💰 {len(funding)} opportunities found")
    
    # Display funding
    for fund in funding:
        days_left = (fund["deadline"] - datetime.now()).days
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='font-weight: 700; font-size: 16px;'>{fund['name']}</div>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px; color: #6b7280;'>
                        <span>🏷️ {fund['type']}</span>
                        <span>💰 {fund['amount']}</span>
                        <span>🎯 {fund['focus']}</span>
                        <span>⏰ {days_left} days left</span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{fund['description']}</p>
                </div>
                <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;'>
                    📅 {fund['deadline'].strftime("%b %d")}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(f"Apply Now", key=f"apply_{fund['name']}"):
                st.success(f"✅ Application link: {fund['application']}")
        
        st.markdown("---")

def render_mentorship():
    """Render mentorship"""
    st.markdown("### 🤝 Mentorship Network")
    
    # Expertise filter
    expertise_areas = MentorshipNetwork.get_expertise_areas()
    selected_expertise = st.multiselect("Filter by Expertise", expertise_areas)
    
    # Get mentors
    mentors = MentorshipNetwork.get_mentors()
    
    if selected_expertise:
        mentors = [m for m in mentors if any(e in selected_expertise for e in m["expertise"])]
    
    # Display mentors
    for mentor in mentors:
        status_color = "#4ade80" if mentor["available"] else "#6b7280"
        status_text = "Available" if mentor["available"] else "Busy"
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {status_color};'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='font-weight: 700; font-size: 16px;'>{mentor['name']}</div>
                    <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 13px; color: #6b7280;'>
                        <span>💼 {mentor['industry']}</span>
                        <span>⏱️ {mentor['experience']}</span>
                        <span>🛠️ {', '.join(mentor['expertise'])}</span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{mentor['bio']}</p>
                </div>
                <div>
                    <span style='background: {status_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;'>
                        {status_text}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if mentor["available"]:
            if st.button(f"📩 Connect with {mentor['name']}", key=f"connect_{mentor['name']}"):
                st.success(f"✅ Request sent to {mentor['name']}!")
        
        st.markdown("---")
    
    # Become a mentor
    st.markdown("#### 🌟 Become a Mentor")
    
    with st.form("mentor_form"):
        col1, col2 = st.columns(2)
        with col1:
            mentor_name = st.text_input("Full Name")
            mentor_industry = st.text_input("Industry")
        with col2:
            mentor_experience = st.text_input("Experience (years)")
            mentor_expertise = st.text_input("Expertise Areas (comma-separated)")
        
        mentor_bio = st.text_area("Bio / Background", height=100)
        
        if st.form_submit_button("Submit Mentor Application"):
            st.success("✅ Thank you for applying to be a mentor!")
            st.info("We'll review your application and get back to you shortly.")

def render_business_dashboard():
    """Render business dashboard"""
    st.markdown("### 📈 Green Business Dashboard")
    
    # Progress metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Business Plan", "75% Complete")
    col2.metric("Impact Score", "82/100")
    col3.metric("Funding Found", "3 Opportunities")
    col4.metric("Mentors", "2 Connected")
    
    # Progress bar
    st.markdown("#### 📊 Business Readiness")
    readiness_score = 65 + random.randint(0, 25)
    st.progress(readiness_score / 100)
    st.caption(f"Readiness Score: {readiness_score}%")
    
    # Quick links
    st.markdown("#### 🚀 Quick Actions")
    
    actions = [
        "📋 Complete Business Plan",
        "📊 Calculate Impact",
        "💰 Apply for Funding",
        "🤝 Connect with Mentor"
    ]
    
    for action in actions:
        if st.button(action, use_container_width=True):
            st.success(f"✅ {action} started!")
    
    # Resources
    st.markdown("#### 📚 Green Business Resources")
    
    resources = [
        {"title": "Sustainable Business Guide", "type": "Guide"},
        {"title": "Impact Reporting Templates", "type": "Template"},
        {"title": "Green Marketing Strategy", "type": "Guide"},
        {"title": "Sustainability Certification", "type": "Resource"}
    ]
    
    for resource in resources:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{resource['title']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>{resource['type']}</div>
                </div>
                <span style='background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;'>
                    Download
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_business_hub():
    """Render the complete business hub"""
    render_green_business()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from green_business import render_business_hub

# Add as a new tab
with tab36:
    render_business_hub()
"""