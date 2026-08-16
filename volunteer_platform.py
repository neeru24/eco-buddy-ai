# ============================================================
# FILE: volunteer_platform.py
# EcoBuddy AI+ Volunteer & Community Action Platform
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math
import hashlib

# ============================================================
# VOLUNTEER OPPORTUNITIES DATABASE
# ============================================================

class VolunteerOpportunities:
    """Database of volunteer and community action opportunities"""
    
    OPPORTUNITIES = [
        {
            "id": "v1",
            "title": "Community Garden Build",
            "organization": "Green Thumb Initiative",
            "category": "Environment",
            "location": "Local Community Center",
            "date": datetime.now() + timedelta(days=5),
            "duration": "4 hours",
            "description": "Help build a sustainable community garden with raised beds and composting systems.",
            "skills_needed": ["Gardening", "Manual Labor", "Teamwork"],
            "impact": "Create green space, grow food, build community",
            "spots_available": 12,
            "total_spots": 20,
            "emoji": "🌱",
            "recurring": False,
            "age_restriction": "All ages welcome"
        },
        {
            "id": "v2",
            "title": "Beach Cleanup Drive",
            "organization": "Ocean Guardians",
            "category": "Environment",
            "location": "Coastal Beach Park",
            "date": datetime.now() + timedelta(days=7),
            "duration": "3 hours",
            "description": "Join us in removing plastic waste from our beaches and protecting marine life.",
            "skills_needed": ["None", "Enthusiasm"],
            "impact": "Clean oceans, save marine life, community engagement",
            "spots_available": 25,
            "total_spots": 30,
            "emoji": "🌊",
            "recurring": True,
            "age_restriction": "Under 16 with adult"
        },
        {
            "id": "v3",
            "title": "Tree Planting Event",
            "organization": "Forest Alliance",
            "category": "Environment",
            "location": "City Forest Park",
            "date": datetime.now() + timedelta(days=10),
            "duration": "5 hours",
            "description": "Plant native trees to restore urban forest and improve air quality.",
            "skills_needed": ["None", "Physical stamina"],
            "impact": "500+ trees planted, improved air quality, habitat creation",
            "spots_available": 8,
            "total_spots": 15,
            "emoji": "🌳",
            "recurring": False,
            "age_restriction": "All ages welcome"
        },
        {
            "id": "v4",
            "title": "Sustainable Food Workshop",
            "organization": "Food for Future",
            "category": "Education",
            "location": "Community Hall",
            "date": datetime.now() + timedelta(days=12),
            "duration": "2 hours",
            "description": "Learn about sustainable food practices, meal planning, and reducing food waste.",
            "skills_needed": ["Interest in sustainability"],
            "impact": "Educate community, reduce food waste, promote sustainability",
            "spots_available": 20,
            "total_spots": 25,
            "emoji": "🥗",
            "recurring": False,
            "age_restriction": "All ages welcome"
        },
        {
            "id": "v5",
            "title": "Solar Panel Installation Help",
            "organization": "Solar for All",
            "category": "Energy",
            "location": "Various Homes",
            "date": datetime.now() + timedelta(days=14),
            "duration": "6 hours",
            "description": "Assist with installing solar panels for low-income families in the community.",
            "skills_needed": ["Construction", "Electrical knowledge"],
            "impact": "Clean energy access, reduced bills, community support",
            "spots_available": 5,
            "total_spots": 10,
            "emoji": "☀️",
            "recurring": False,
            "age_restriction": "18+ only"
        },
        {
            "id": "v6",
            "title": "Community Composting Program",
            "organization": "Zero Waste Initiative",
            "category": "Waste",
            "location": "Community Garden",
            "date": datetime.now() + timedelta(days=3),
            "duration": "3 hours",
            "description": "Help set up and manage community composting system for organic waste.",
            "skills_needed": ["Organizational skills", "Interest in composting"],
            "impact": "Reduce waste, create fertilizer, educate community",
            "spots_available": 10,
            "total_spots": 15,
            "emoji": "♻️",
            "recurring": True,
            "age_restriction": "All ages welcome"
        },
        {
            "id": "v7",
            "title": "Environmental Education Mentor",
            "organization": "Eco-Schools Program",
            "category": "Education",
            "location": "Local Schools",
            "date": datetime.now() + timedelta(days=8),
            "duration": "2 hours",
            "description": "Mentor students on environmental topics and sustainability projects.",
            "skills_needed": ["Communication", "Teaching skills", "Patience"],
            "impact": "Educate youth, inspire environmental action",
            "spots_available": 6,
            "total_spots": 10,
            "emoji": "📚",
            "recurring": True,
            "age_restriction": "18+ only"
        },
        {
            "id": "v8",
            "title": "Park Restoration Project",
            "organization": "Parks & Recreation",
            "category": "Environment",
            "location": "Central Park",
            "date": datetime.now() + timedelta(days=21),
            "duration": "4 hours",
            "description": "Restore local park through planting, cleaning, and trail maintenance.",
            "skills_needed": ["None", "Teamwork"],
            "impact": "Beautiful park, improved community space",
            "spots_available": 15,
            "total_spots": 20,
            "emoji": "🌺",
            "recurring": False,
            "age_restriction": "All ages welcome"
        }
    ]
    
    @staticmethod
    def get_opportunities(category=None, date_filter="All"):
        """Get opportunities with filters"""
        opportunities = VolunteerOpportunities.OPPORTUNITIES.copy()
        
        if category and category != "All":
            opportunities = [o for o in opportunities if o["category"] == category]
        
        if date_filter == "Upcoming":
            opportunities = [o for o in opportunities if o["date"] >= datetime.now()]
        elif date_filter == "Soon (7 days)":
            cutoff = datetime.now() + timedelta(days=7)
            opportunities = [o for o in opportunities if datetime.now() <= o["date"] <= cutoff]
        
        return sorted(opportunities, key=lambda x: x["date"])
    
    @staticmethod
    def get_categories():
        """Get opportunity categories"""
        return ["All"] + sorted(set(o["category"] for o in VolunteerOpportunities.OPPORTUNITIES))
    
    @staticmethod
    def get_category_stats():
        """Get category statistics"""
        stats = {}
        for opp in VolunteerOpportunities.OPPORTUNITIES:
            category = opp["category"]
            if category not in stats:
                stats[category] = 0
            stats[category] += 1
        return stats
    
    @staticmethod
    def get_organization_stats():
        """Get organization statistics"""
        stats = {}
        for opp in VolunteerOpportunities.OPPORTUNITIES:
            org = opp["organization"]
            if org not in stats:
                stats[org] = 0
            stats[org] += 1
        return stats

# ============================================================
# USER VOLUNTEER TRACKER
# ============================================================

class VolunteerTracker:
    """Track user volunteer activities"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.activities = self._load_activities()
    
    def _load_activities(self):
        """Load activities from session"""
        if "volunteer_activities" not in st.session_state:
            st.session_state.volunteer_activities = {}
        return st.session_state.volunteer_activities.get(self.user_id, [])
    
    def save(self):
        """Save activities"""
        st.session_state.volunteer_activities[self.user_id] = self.activities
    
    def register(self, opportunity_id):
        """Register for a volunteer opportunity"""
        # Check if already registered
        if any(a["opportunity_id"] == opportunity_id for a in self.activities):
            return False, "Already registered for this opportunity"
        
        # Find opportunity
        opp = next((o for o in VolunteerOpportunities.OPPORTUNITIES if o["id"] == opportunity_id), None)
        if not opp:
            return False, "Opportunity not found"
        
        # Check availability
        if opp["spots_available"] <= 0:
            return False, "No spots available"
        
        # Register
        activity = {
            "opportunity_id": opportunity_id,
            "title": opp["title"],
            "organization": opp["organization"],
            "date": opp["date"].isoformat(),
            "registered_at": datetime.now().isoformat(),
            "status": "registered",
            "hours_completed": 0
        }
        
        self.activities.append(activity)
        self.save()
        
        # Update spots available
        for o in VolunteerOpportunities.OPPORTUNITIES:
            if o["id"] == opportunity_id:
                o["spots_available"] -= 1
                break
        
        return True, "Successfully registered!"
    
    def cancel_registration(self, opportunity_id):
        """Cancel volunteer registration"""
        for i, activity in enumerate(self.activities):
            if activity["opportunity_id"] == opportunity_id:
                # Update spots available
                for o in VolunteerOpportunities.OPPORTUNITIES:
                    if o["id"] == opportunity_id:
                        o["spots_available"] += 1
                        break
                
                del self.activities[i]
                self.save()
                return True, "Registration cancelled"
        
        return False, "Registration not found"
    
    def complete_activity(self, opportunity_id, hours):
        """Complete a volunteer activity"""
        for activity in self.activities:
            if activity["opportunity_id"] == opportunity_id:
                activity["status"] = "completed"
                activity["hours_completed"] = hours
                self.save()
                return True
        return False
    
    def get_stats(self):
        """Get volunteer statistics"""
        if not self.activities:
            return {
                "total_activities": 0,
                "completed": 0,
                "registered": 0,
                "total_hours": 0,
                "impact_score": 0
            }
        
        total = len(self.activities)
        completed = sum(1 for a in self.activities if a["status"] == "completed")
        registered = sum(1 for a in self.activities if a["status"] == "registered")
        total_hours = sum(a.get("hours_completed", 0) for a in self.activities if a["status"] == "completed")
        
        return {
            "total_activities": total,
            "completed": completed,
            "registered": registered,
            "total_hours": total_hours,
            "impact_score": completed * 10 + total_hours
        }

# ============================================================
# COMMUNITY IMPACT CALCULATOR
# ============================================================

class CommunityImpactCalculator:
    """Calculate community impact of volunteer activities"""
    
    @staticmethod
    def calculate_impact(activities):
        """Calculate community impact from activities"""
        if not activities:
            return {
                "trees_planted": 0,
                "co2_saved": 0,
                "waste_reduced": 0,
                "people_educated": 0,
                "community_score": 0
            }
        
        # Impact per activity type (simplified)
        impact_factors = {
            "Community Garden Build": {"trees": 5, "co2": 100, "waste": 50, "people": 20},
            "Beach Cleanup Drive": {"trees": 0, "co2": 50, "waste": 200, "people": 10},
            "Tree Planting Event": {"trees": 50, "co2": 500, "waste": 0, "people": 15},
            "Sustainable Food Workshop": {"trees": 0, "co2": 30, "waste": 30, "people": 40},
            "Solar Panel Installation Help": {"trees": 0, "co2": 200, "waste": 0, "people": 10},
            "Community Composting Program": {"trees": 0, "co2": 80, "waste": 150, "people": 25},
            "Environmental Education Mentor": {"trees": 0, "co2": 20, "waste": 10, "people": 50},
            "Park Restoration Project": {"trees": 20, "co2": 150, "waste": 40, "people": 30}
        }
        
        totals = {"trees": 0, "co2": 0, "waste": 0, "people": 0}
        
        for activity in activities:
            title = activity.get("title", "")
            if title in impact_factors:
                factor = impact_factors[title]
                totals["trees"] += factor["trees"]
                totals["co2"] += factor["co2"]
                totals["waste"] += factor["waste"]
                totals["people"] += factor["people"]
        
        # Community score
        community_score = (totals["trees"] * 2) + (totals["co2"] / 10) + (totals["waste"] / 5) + (totals["people"] / 2)
        
        return {
            "trees_planted": totals["trees"],
            "co2_saved": totals["co2"],
            "waste_reduced": totals["waste"],
            "people_educated": totals["people"],
            "community_score": int(community_score)
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_volunteer_platform():
    """Render the complete volunteer platform"""
    st.markdown("<div class='section-header'>🤝 Volunteer & Community Action Platform</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize tracker
    if "volunteer_tracker" not in st.session_state:
        st.session_state.volunteer_tracker = VolunteerTracker(user_id)
    
    tracker = st.session_state.volunteer_tracker
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📋 Opportunities",
        "📊 My Impact",
        "🏆 Community Impact"
    ])
    
    with tab1:
        render_opportunities(tracker)
    
    with tab2:
        render_my_impact(tracker)
    
    with tab3:
        render_community_impact(tracker)

def render_opportunities(tracker):
    """Render volunteer opportunities"""
    st.markdown("### 📋 Volunteer Opportunities")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        categories = VolunteerOpportunities.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        date_filters = ["All", "Upcoming", "Soon (7 days)"]
        selected_date = st.selectbox("Date Filter", date_filters)
    
    # Get opportunities
    opportunities = VolunteerOpportunities.get_opportunities(selected_category, selected_date)
    
    # Display count
    st.caption(f"📋 {len(opportunities)} opportunities found")
    
    # Display opportunities
    for opp in opportunities:
        days_until = (opp["date"] - datetime.now()).days
        date_str = opp["date"].strftime("%B %d, %Y")
        
        availability_color = "#4ade80" if opp["spots_available"] > 10 else "#fbbf24" if opp["spots_available"] > 5 else "#f87171"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{opp['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{opp['title']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>🏢 {opp['organization']}</span>
                                <span>📂 {opp['category']}</span>
                                <span>📍 {opp['location']}</span>
                                <span>📅 {date_str} ({days_until} days)</span>
                                <span>⏱️ {opp['duration']}</span>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <div style='font-size: 20px; font-weight: 700; color: {availability_color};'>
                                {opp['spots_available']}/{opp['total_spots']}
                            </div>
                            <div style='font-size: 12px; color: #6b7280;'>Spots Available</div>
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{opp['description']}</p>
                    <div style='display: flex; gap: 10px; flex-wrap: wrap; font-size: 13px;'>
                        <span>🛠️ Skills: {', '.join(opp['skills_needed'])}</span>
                        <span>🌍 Impact: {opp['impact']}</span>
                        <span>👤 {opp['age_restriction']}</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 3])
        
        with col1:
            # Check if already registered
            is_registered = any(a["opportunity_id"] == opp["id"] for a in tracker.activities)
            
            if is_registered:
                if st.button(f"✅ Registered", key=f"registered_{opp['id']}", disabled=True):
                    pass
            else:
                if opp["spots_available"] > 0:
                    if st.button(f"🤝 Register", key=f"register_{opp['id']}", type="primary"):
                        success, message = tracker.register(opp["id"])
                        if success:
                            st.success(message)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.button(f"🔴 Full", key=f"full_{opp['id']}", disabled=True)
        
        with col2:
            if is_registered:
                if st.button(f"❌ Cancel", key=f"cancel_{opp['id']}"):
                    success, message = tracker.cancel_registration(opp["id"])
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        # Expand for details
        if st.button(f"📖 Details", key=f"details_{opp['id']}"):
            with st.expander("Full Details", expanded=True):
                st.markdown(f"**Organization:** {opp['organization']}")
                st.markdown(f"**Location:** {opp['location']}")
                st.markdown(f"**Date:** {opp['date'].strftime('%B %d, %Y at %I:%M %p')}")
                st.markdown(f"**Duration:** {opp['duration']}")
                st.markdown(f"**Age Restriction:** {opp['age_restriction']}")
                st.markdown(f"**Recurring:** {'Yes' if opp['recurring'] else 'No'}")
                st.markdown(f"**Impact:** {opp['impact']}")
                st.markdown(f"**Skills Needed:** {', '.join(opp['skills_needed'])}")
                
                if st.button("🗑️ Close Details"):
                    st.rerun()
        
        st.markdown("---")

def render_my_impact(tracker):
    """Render user's volunteer impact"""
    st.markdown("### 📊 My Volunteer Impact")
    
    stats = tracker.get_stats()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Activities", stats["total_activities"])
    col2.metric("Completed", stats["completed"])
    col3.metric("Registered", stats["registered"])
    col4.metric("Total Hours", f"{stats['total_hours']:.0f}h")
    
    # Impact score
    st.markdown("#### 💪 Impact Score")
    st.progress(min(stats["impact_score"] / 200, 1.0))
    st.caption(f"Score: {stats['impact_score']} points")
    
    # My activities
    st.markdown("### 📋 My Activities")
    
    if tracker.activities:
        for activity in tracker.activities:
            date = datetime.fromisoformat(activity["date"]).strftime("%B %d, %Y")
            status_emoji = "✅" if activity["status"] == "completed" else "📋" if activity["status"] == "registered" else "⏰"
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{status_emoji} {activity['title']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>
                            {activity['organization']} • {date} • Status: {activity['status']}
                            {f' • Hours: {activity["hours_completed"]:.0f}h' if activity["status"] == "completed" else ''}
                        </div>
                    </div>
                    <div>
                        {f'<span style="background: #4ade80; padding: 2px 12px; border-radius: 12px; font-size: 12px; color: #111827;">✅ Done</span>' if activity["status"] == "completed" else 
                         f'<span style="background: #fbbf24; padding: 2px 12px; border-radius: 12px; font-size: 12px; color: #111827;">📋 Pending</span>'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if activity["status"] == "registered":
                col1, col2 = st.columns([1, 3])
                with col1:
                    hours = st.number_input(
                        f"Hours completed for {activity['title']}",
                        min_value=0.5,
                        max_value=24.0,
                        value=2.0,
                        step=0.5,
                        key=f"hours_{activity['opportunity_id']}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button(f"✅ Complete", key=f"complete_{activity['opportunity_id']}"):
                        tracker.complete_activity(activity['opportunity_id'], hours)
                        st.success("✅ Activity completed!")
                        st.rerun()
    else:
        st.info("🤝 No volunteer activities yet. Browse opportunities and register!")

def render_community_impact(tracker):
    """Render community impact"""
    st.markdown("### 🏆 Community Impact")
    
    # Calculate total community impact
    all_activities = []
    for user_id, activities in st.session_state.get("volunteer_activities", {}).items():
        all_activities.extend(activities)
    
    impact = CommunityImpactCalculator.calculate_impact(all_activities)
    
    # Display impact metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌳 Trees Planted", f"{impact['trees_planted']:,}")
    col2.metric("🌍 CO₂ Saved", f"{impact['co2_saved']:,} kg")
    col3.metric("♻️ Waste Reduced", f"{impact['waste_reduced']:,} kg")
    col4.metric("👨‍🎓 People Educated", f"{impact['people_educated']:,}")
    
    # Community score
    st.markdown("#### 🌟 Community Impact Score")
    st.progress(min(impact['community_score'] / 500, 1.0))
    st.caption(f"Score: {impact['community_score']} points")
    
    # Impact visualization
    st.markdown("### 📊 Impact Breakdown")
    
    impact_data = {
        "Category": ["Trees Planted", "CO₂ Saved", "Waste Reduced", "People Educated"],
        "Value": [impact['trees_planted'], impact['co2_saved'], impact['waste_reduced'], impact['people_educated']],
        "Unit": ["trees", "kg", "kg", "people"]
    }
    
    df_impact = pd.DataFrame(impact_data)
    
    fig = go.Figure(data=[go.Bar(
        x=df_impact['Category'],
        y=df_impact['Value'],
        marker_color=['#4ade80', '#fbbf24', '#f87171', '#60a5fa'],
        text=df_impact['Value'],
        textposition='auto'
    )])
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_title="Impact Value"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Top volunteers
    st.markdown("### 🏅 Top Volunteers")
    
    # Calculate volunteer stats
    volunteer_stats = {}
    for user_id, activities in st.session_state.get("volunteer_activities", {}).items():
        completed = sum(1 for a in activities if a.get("status") == "completed")
        hours = sum(a.get("hours_completed", 0) for a in activities if a.get("status") == "completed")
        volunteer_stats[user_id] = {"completed": completed, "hours": hours}
    
    if volunteer_stats:
        # Sort by completed activities
        top_volunteers = sorted(volunteer_stats.items(), key=lambda x: x[1]["completed"], reverse=True)[:5]
        
        for i, (user_id, stats) in enumerate(top_volunteers, 1):
            emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i-1] if i <= 5 else "👤"
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-size: 20px;'>{emoji}</span>
                        <span style='font-weight: 600;'>Volunteer #{user_id}</span>
                    </div>
                    <div>
                        <span style='background: #1f2937; padding: 2px 12px; border-radius: 12px; font-size: 12px;'>
                            {stats['completed']} activities • {stats['hours']:.0f} hours
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("🏅 No volunteers yet. Be the first to make a difference!")

# ============================================================
# INTEGRATION
# ============================================================

def render_volunteer_hub():
    """Render the complete volunteer hub"""
    render_volunteer_platform()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from volunteer_platform import render_volunteer_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17, tab18, tab19, tab20, tab21, tab22 = st.tabs([
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
    "🤝 Volunteer"  # NEW
])

with tab22:
    render_volunteer_hub()
"""