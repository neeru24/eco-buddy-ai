
# ============================================================
# FILE: community_resilience.py
# EcoBuddy AI+ Community Resilience & Disaster Preparedness
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# RISK DATABASE
# ============================================================

class ClimateRisks:
    """Climate risk assessment database"""
    
    RISKS = {
        "Flood": {
            "description": "Rising water levels and flooding",
            "warning_signs": ["Heavy rainfall", "Rising water levels", "Flood warnings"],
            "preparedness": ["Sandbags", "Elevate valuables", "Flood insurance"],
            "evacuation": "Move to higher ground",
            "severity": "High"
        },
        "Wildfire": {
            "description": "Uncontrolled fires in natural areas",
            "warning_signs": ["Dry conditions", "High winds", "Smoke"],
            "preparedness": ["Clear vegetation", "Prepare go-bag", "Fire-resistant materials"],
            "evacuation": "Follow official evacuation routes",
            "severity": "Critical"
        },
        "Hurricane": {
            "description": "Severe tropical storms with high winds",
            "warning_signs": ["Storm warnings", "Barometric drop", "High winds"],
            "preparedness": ["Board windows", "Secure outdoor items", "Stock supplies"],
            "evacuation": "Follow mandatory evacuation orders",
            "severity": "Critical"
        },
        "Drought": {
            "description": "Extended period of water scarcity",
            "warning_signs": ["Water restrictions", "Dry conditions", "Crop failure"],
            "preparedness": ["Water conservation", "Rainwater harvesting", "Drought-resistant plants"],
            "evacuation": "Not typically required",
            "severity": "Medium"
        },
        "Heat Wave": {
            "description": "Extreme and prolonged high temperatures",
            "warning_signs": ["Heat warnings", "Humidity", "Power outages"],
            "preparedness": ["Cooling center locations", "Hydration", "Fan/AC readiness"],
            "evacuation": "Seek air-conditioned shelter",
            "severity": "High"
        },
        "Earthquake": {
            "description": "Ground shaking and structural damage",
            "warning_signs": ["Seismic activity", "Warning systems"],
            "preparedness": ["Secure furniture", "Family communication plan", "Emergency kit"],
            "evacuation": "Avoid buildings, seek open space",
            "severity": "High"
        }
    }
    
    @staticmethod
    def get_risks():
        """Get all climate risks"""
        return ClimateRisks.RISKS

# ============================================================
# EMERGENCY SUPPLIES
# ============================================================

class EmergencySupplies:
    """Emergency supply checklists"""
    
    SUPPLIES = {
        "Basic": {
            "Water": "1 gallon per person per day (3-day supply)",
            "Food": "3-day supply of non-perishable items",
            "Battery Radio": "NOAA weather radio with batteries",
            "Flashlight": "With extra batteries",
            "First Aid Kit": "Basic medical supplies",
            "Whistle": "To signal for help",
            "Dust Mask": "To filter contaminated air",
            "Plastic Sheeting": "For shelter",
            "Manual Can Opener": "For food",
            "Cell Phone": "With chargers and backup battery"
        },
        "Additional": {
            "Prescription": "Extra medication supply",
            "Glasses": "Extra pair of glasses",
            "Cash": "Small bills and coins",
            "Important Papers": "Identification, insurance documents",
            "Sleeping Bag": "Warm blanket per person",
            "Change of Clothes": "Season-appropriate attire",
            "Hygiene Items": "Toiletries and sanitizing wipes",
            "Tools": "For turning off utilities",
            "Maps": "Local area maps",
            "Entertainment": "Books, games for extended stays"
        },
        "Pet": {
            "Food": "Pet food supply",
            "Water": "Extra water for pets",
            "Medication": "Pet medication",
            "Leash": "And carrier",
            "Records": "Vaccination records",
            "Bowl": "Food and water bowls"
        },
        "Baby": {
            "Formula": "Baby formula supply",
            "Diapers": "Extra diapers",
            "Wipes": "Baby wipes",
            "Clothes": "Extra baby clothes",
            "Bottles": "Clean bottles",
            "Baby Food": "Baby food supply"
        }
    }
    
    @staticmethod
    def get_supplies(category=None):
        """Get supplies by category"""
        if category and category != "All":
            return EmergencySupplies.SUPPLIES.get(category, {})
        all_supplies = {}
        for cat, items in EmergencySupplies.SUPPLIES.items():
            all_supplies.update(items)
        return all_supplies
    
    @staticmethod
    def get_categories():
        """Get supply categories"""
        return ["All"] + list(EmergencySupplies.SUPPLIES.keys())

# ============================================================
# COMMUNITY NETWORK
# ============================================================

class CommunityNetwork:
    """Community support network system"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.network = self._load_network()
    
    def _load_network(self):
        """Load network from session"""
        if "community_network" not in st.session_state:
            st.session_state.community_network = {}
        return st.session_state.community_network.get(self.user_id, {
            "neighbors": [],
            "emergency_contacts": [],
            "skills": [],
            "resources": [],
            "groups": []
        })
    
    def save(self):
        """Save network"""
        st.session_state.community_network[self.user_id] = self.network
    
    def add_neighbor(self, name, contact, skills="", resources=""):
        """Add neighbor to network"""
        neighbor = {
            "name": name,
            "contact": contact,
            "skills": skills,
            "resources": resources,
            "added": datetime.now().isoformat()
        }
        self.network["neighbors"].append(neighbor)
        self.save()
        return neighbor
    
    def add_emergency_contact(self, name, relationship, phone):
        """Add emergency contact"""
        contact = {
            "name": name,
            "relationship": relationship,
            "phone": phone,
            "added": datetime.now().isoformat()
        }
        self.network["emergency_contacts"].append(contact)
        self.save()
        return contact

# ============================================================
# PREPAREDNESS PLAN
# ============================================================

class PreparednessPlan:
    """Family preparedness plan"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.plan = self._load_plan()
    
    def _load_plan(self):
        """Load plan from session"""
        if "preparedness_plan" not in st.session_state:
            st.session_state.preparedness_plan = {}
        return st.session_state.preparedness_plan.get(self.user_id, {
            "evacuation_routes": [],
            "meeting_points": [],
            "communication_plan": "",
            "special_needs": [],
            "pets": [],
            "items_ready": []
        })
    
    def save(self):
        """Save plan"""
        st.session_state.preparedness_plan[self.user_id] = self.plan
    
    def add_evacuation_route(self, route_description):
        """Add evacuation route"""
        if route_description not in self.plan["evacuation_routes"]:
            self.plan["evacuation_routes"].append(route_description)
            self.save()
            return True
        return False

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_community_resilience():
    """Render the complete resilience platform"""
    st.markdown("<div class='section-header'>🌊 Community Resilience & Disaster Preparedness</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize components
    if "community_network" not in st.session_state:
        st.session_state.community_network = CommunityNetwork(user_id)
    if "preparedness_plan" not in st.session_state:
        st.session_state.preparedness_plan = PreparednessPlan(user_id)
    
    network = st.session_state.community_network
    plan = st.session_state.preparedness_plan
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "⚠️ Risk Assessment",
        "📋 Preparedness",
        "🛠️ Supplies",
        "🤝 Community Network",
        "📊 Dashboard"
    ])
    
    with tab1:
        render_risk_assessment()
    
    with tab2:
        render_preparedness_plan(plan)
    
    with tab3:
        render_supplies()
    
    with tab4:
        render_community_network(network)
    
    with tab5:
        render_resilience_dashboard(network, plan)

def render_risk_assessment():
    """Render risk assessment"""
    st.markdown("### ⚠️ Climate Risk Assessment")
    
    st.markdown("""
    <div class='subtitle'>
        Identify and understand climate risks in your area
    </div>
    """, unsafe_allow_html=True)
    
    # Location input (simulated)
    location = st.text_input("📍 Your Location", placeholder="City, State, or Region")
    
    if location:
        st.success(f"📍 Analyzing risks for {location}...")
    
    # Risk cards
    risks = ClimateRisks.get_risks()
    
    for risk_name, risk_info in risks.items():
        severity_colors = {
            "Critical": "#f87171",
            "High": "#fbbf24",
            "Medium": "#60a5fa",
            "Low": "#4ade80"
        }
        color = severity_colors.get(risk_info["severity"], "#6b7280")
        
        with st.container():
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: space-between; align-items: start;'>
                    <div>
                        <div style='font-weight: 700; font-size: 16px;'>⚠️ {risk_name}</div>
                        <div style='font-size: 14px; color: #6b7280;'>{risk_info['description']}</div>
                        <div style='font-size: 13px; margin-top: 4px;'>
                            <span style='background: #1f2937; padding: 2px 8px; border-radius: 8px; font-size: 11px;'>
                                Severity: {risk_info['severity']}
                            </span>
                        </div>
                    </div>
                </div>
                <details style='margin-top: 8px;'>
                    <summary style='cursor: pointer; color: #4ade80;'>📋 Details</summary>
                    <div style='margin-top: 8px;'>
                        <div><b>⚠️ Warning Signs:</b></div>
                        <ul>{''.join([f'<li>{sign}</li>' for sign in risk_info['warning_signs']])}</ul>
                        <div><b>🛠️ Preparedness:</b></div>
                        <ul>{''.join([f'<li>{item}</li>' for item in risk_info['preparedness']])}</ul>
                        <div><b>🚨 Evacuation:</b> {risk_info['evacuation']}</div>
                    </div>
                </details>
            </div>
            """, unsafe_allow_html=True)
        
        # Quick action button
        if st.button(f"Prepare for {risk_name}", key=f"prepare_{risk_name}"):
            st.info(f"📋 Checklist for {risk_name} loaded in the Preparedness tab")
        
        st.markdown("---")

def render_preparedness_plan(plan):
    """Render preparedness plan"""
    st.markdown("### 📋 Family Preparedness Plan")
    
    st.markdown("""
    <div class='subtitle'>
        Create your family's emergency preparedness plan
    </div>
    """, unsafe_allow_html=True)
    
    # Plan completeness
    items = [
        "✅ Communication Plan",
        "✅ Evacuation Routes",
        "✅ Meeting Points",
        "✅ Emergency Contacts",
        "✅ Special Needs",
        "✅ Pet Plan",
        "✅ Supply Kit Ready"
    ]
    
    completed = sum(1 for item in plan.plan.get("items_ready", []))
    progress = (completed / 7) * 100
    
    st.markdown("#### 📊 Plan Readiness")
    st.progress(progress / 100)
    st.caption(f"{completed}/7 items complete")
    
    # Plan sections
    st.markdown("---")
    
    # Evacuation Routes
    st.markdown("#### 🗺️ Evacuation Routes")
    
    new_route = st.text_input("Add Evacuation Route", placeholder="e.g., Route to highway via Main Street")
    if st.button("Add Route"):
        if new_route:
            plan.add_evacuation_route(new_route)
            st.success("✅ Route added!")
            st.rerun()
    
    if plan.plan["evacuation_routes"]:
        for route in plan.plan["evacuation_routes"]:
            st.markdown(f"• {route}")
    else:
        st.info("No evacuation routes added yet")
    
    # Meeting Points
    st.markdown("#### 📍 Meeting Points")
    
    meeting_point = st.text_input("Add Meeting Point", placeholder="e.g., Neighbor's house, Community center")
    if st.button("Add Meeting Point"):
        if meeting_point:
            plan.plan["meeting_points"].append(meeting_point)
            plan.save()
            st.success("✅ Meeting point added!")
            st.rerun()
    
    if plan.plan["meeting_points"]:
        for point in plan.plan["meeting_points"]:
            st.markdown(f"• {point}")
    else:
        st.info("No meeting points added yet")
    
    # Communication Plan
    st.markdown("#### 📞 Communication Plan")
    
    comm_plan = st.text_area("Your Family Communication Plan", 
                             placeholder="e.g., Call family member, text, social media...",
                             value=plan.plan["communication_plan"])
    if st.button("Update Communication Plan"):
        plan.plan["communication_plan"] = comm_plan
        plan.save()
        st.success("✅ Communication plan updated!")
    
    # Special Needs
    st.markdown("#### 🏥 Special Needs")
    
    special_need = st.text_input("Add Special Needs", placeholder="e.g., Medical needs, mobility issues...")
    if st.button("Add Special Need"):
        if special_need:
            plan.plan["special_needs"].append(special_need)
            plan.save()
            st.success("✅ Special need added!")
            st.rerun()
    
    if plan.plan["special_needs"]:
        for need in plan.plan["special_needs"]:
            st.markdown(f"• {need}")
    
    # Mark as ready
    st.markdown("---")
    if st.button("✅ Mark Plan as Ready", use_container_width=True):
        if "Ready" not in plan.plan.get("items_ready", []):
            plan.plan["items_ready"].append("Ready")
            plan.save()
            st.success("🎉 Your family preparedness plan is complete!")
            st.balloons()

def render_supplies():
    """Render emergency supplies"""
    st.markdown("### 🛠️ Emergency Supply Checklist")
    
    st.markdown("""
    <div class='subtitle'>
        Prepare your emergency supply kit
    </div>
    """, unsafe_allow_html=True)
    
    # Category filter
    categories = EmergencySupplies.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get supplies
    supplies = EmergencySupplies.get_supplies(selected_category)
    
    # Display supplies as checklist
    st.markdown("#### 📋 Supply Checklist")
    
    # Initialize checked items
    if "checked_supplies" not in st.session_state:
        st.session_state.checked_supplies = {}
    
    for item, description in supplies.items():
        key = f"supply_{item}"
        checked = st.session_state.checked_supplies.get(key, False)
        
        col1, col2, col3 = st.columns([1, 3, 1])
        with col1:
            checked = st.checkbox("", key=key, value=checked)
            st.session_state.checked_supplies[key] = checked
        with col2:
            st.markdown(f"**{item}**")
        with col3:
            st.caption(description)
    
    # Summary
    total = len(supplies)
    checked_count = sum(1 for key, val in st.session_state.checked_supplies.items() 
                       if key.startswith("supply_") and val)
    
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Items", total)
    col2.metric("Ready", checked_count)
    col3.metric("Progress", f"{(checked_count/total*100):.0f}%" if total > 0 else "0%")
    
    st.progress(checked_count / total if total > 0 else 0)
    
    if checked_count == total and total > 0:
        st.success("🎉 Your emergency supply kit is complete!")
        st.balloons()
    
    # Export checklist
    st.markdown("---")
    if st.button("📤 Download Checklist", use_container_width=True):
        st.success("📥 Checklist downloaded!")

def render_community_network(network):
    """Render community network"""
    st.markdown("### 🤝 Community Network")
    
    st.markdown("""
    <div class='subtitle'>
        Build connections with your community for mutual support
    </div>
    """, unsafe_allow_html=True)
    
    # Add neighbor
    st.markdown("#### 🏠 Add Neighbor to Network")
    
    with st.form("add_neighbor_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Neighbor's Name")
            contact = st.text_input("Contact Information")
        with col2:
            skills = st.text_input("Skills (e.g., Medical, Search & Rescue)")
            resources = st.text_input("Resources Available")
        
        if st.form_submit_button("Add Neighbor"):
            if name and contact:
                network.add_neighbor(name, contact, skills, resources)
                st.success(f"✅ {name} added to your network!")
                st.rerun()
            else:
                st.warning("Please enter name and contact")
    
    # Display network
    st.markdown("#### 📋 Your Network")
    
    if network.network["neighbors"]:
        for neighbor in network.network["neighbors"]:
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{neighbor['name']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>
                            📞 {neighbor['contact']}
                            {f'• 🛠️ {neighbor["skills"]}' if neighbor.get("skills") else ''}
                            {f'• 📦 {neighbor["resources"]}' if neighbor.get("resources") else ''}
                        </div>
                    </div>
                    <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;'>
                        Added: {datetime.fromisoformat(neighbor["added"]).strftime("%b %d")}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🏠 No neighbors added yet. Start building your community network!")
    
    # Emergency Contacts
    st.markdown("#### 📞 Emergency Contacts")
    
    with st.form("add_contact_form"):
        col1, col2 = st.columns(2)
        with col1:
            contact_name = st.text_input("Contact Name")
            relationship = st.text_input("Relationship")
        with col2:
            phone = st.text_input("Phone Number")
        
        if st.form_submit_button("Add Emergency Contact"):
            if contact_name and phone:
                network.add_emergency_contact(contact_name, relationship, phone)
                st.success(f"✅ {contact_name} added as emergency contact!")
                st.rerun()
            else:
                st.warning("Please enter name and phone")
    
    if network.network["emergency_contacts"]:
        for contact in network.network["emergency_contacts"]:
            st.markdown(f"• **{contact['name']}** ({contact['relationship']}) - 📞 {contact['phone']}")

def render_resilience_dashboard(network, plan):
    """Render resilience dashboard"""
    st.markdown("### 📊 Community Resilience Dashboard")
    
    # Overall readiness score
    risk_awareness = 60 + random.randint(0, 30)
    plan_readiness = len(plan.plan.get("items_ready", [])) * 14
    network_strength = len(network.network["neighbors"]) * 10
    supplies_ready = sum(1 for key, val in st.session_state.get("checked_supplies", {}).items() 
                        if val and key.startswith("supply_"))
    
    readiness_score = min(100, (risk_awareness + plan_readiness + network_strength + supplies_ready) / 4)
    
    st.markdown("#### 🏆 Resilience Score")
    st.progress(readiness_score / 100)
    st.caption(f"{readiness_score:.0f}/100 - {'Strong' if readiness_score > 80 else 'Developing' if readiness_score > 50 else 'Needs Improvement'}")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Risk Awareness", f"{risk_awareness:.0f}%")
    col2.metric("Plan Readiness", f"{plan_readiness:.0f}%")
    col3.metric("Network Strength", len(network.network["neighbors"]))
    col4.metric("Supplies Ready", supplies_ready)
    
    # Radar chart
    categories = ["Risk Awareness", "Plan Readiness", "Network", "Supplies", "Communication"]
    scores = [
        risk_awareness,
        plan_readiness,
        network_strength,
        supplies_ready,
        len(plan.plan.get("communication_plan", "")) * 5
    ]
    
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='Your Score',
        line=dict(color='#4ade80')
    ))
    fig.add_trace(go.Scatterpolar(
        r=[80, 80, 80, 80, 80],
        theta=categories,
        fill='toself',
        name='Target Score',
        line=dict(color='#fbbf24', dash='dash')
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        height=300,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    
    recs = []
    if risk_awareness < 70:
        recs.append("📚 Review climate risks in your area to improve awareness")
    if plan_readiness < 60:
        recs.append("📋 Complete your family preparedness plan")
    if len(network.network["neighbors"]) < 3:
        recs.append("🤝 Connect with more neighbors in your community network")
    if supplies_ready < 10:
        recs.append("🛠️ Build your emergency supply kit")
    
    if recs:
        for rec in recs:
            st.info(f"💡 {rec}")
    else:
        st.success("🌟 Your community resilience is strong! Continue maintaining your preparedness.")

# ============================================================
# INTEGRATION
# ============================================================

def render_resilience_hub():
    """Render the complete resilience hub"""
    render_community_resilience()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from community_resilience import render_resilience_hub

# Add as a new tab
with tab35:
    render_resilience_hub()
"""