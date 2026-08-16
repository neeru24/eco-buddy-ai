

# ============================================================
# FILE: eco_parenting.py
# EcoBuddy AI+ Eco-Parenting & Family Green Living Guide
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# AGE-BASED GUIDES
# ============================================================

class AgeBasedGuides:
    """Age-specific sustainability guides for children"""
    
    GUIDES = {
        "infant": {
            "title": "👶 Infant (0-2 years)",
            "description": "Starting your baby's sustainability journey",
            "tips": [
                "Use cloth diapers - saves 5,000+ diapers from landfill",
                "Choose organic baby clothing",
                "Make your own baby food",
                "Use glass bottles instead of plastic",
                "Choose wooden or natural toys"
            ],
            "eco_score_target": 60,
            "activities": [
                "Nature walks with baby",
                "Sensory play with natural materials",
                "Sing songs about nature"
            ]
        },
        "toddler": {
            "title": "🧒 Toddler (2-5 years)",
            "description": "Building eco-awareness in early childhood",
            "tips": [
                "Teach recycling through play",
                "Plant seeds and watch them grow",
                "Make art from recycled materials",
                "Read books about nature",
                "Practice water conservation"
            ],
            "eco_score_target": 70,
            "activities": [
                "Garden planting",
                "Recycling sorting game",
                "Nature treasure hunt"
            ]
        },
        "child": {
            "title": "👦 Child (6-12 years)",
            "description": "Developing sustainability values and habits",
            "tips": [
                "Involve in household eco-decisions",
                "Start a compost project",
                "Take on energy-saving challenges",
                "Support a cause or project",
                "Learn about biodiversity"
            ],
            "eco_score_target": 80,
            "activities": [
                "Community cleanup",
                "Build a bug hotel",
                "Start a recycling program"
            ]
        },
        "teen": {
            "title": "🧑 Teen (13-18 years)",
            "description": "Empowering young environmental leaders",
            "tips": [
                "Encourage environmental advocacy",
                "Support climate activism",
                "Learn about sustainable careers",
                "Practice conscious consumerism",
                "Lead community projects"
            ],
            "eco_score_target": 85,
            "activities": [
                "Organize a climate event",
                "Start an eco-club",
                "Volunteer for environmental causes"
            ]
        }
    }
    
    @staticmethod
    def get_guide(age_group):
        """Get guide for specific age group"""
        return AgeBasedGuides.GUIDES.get(age_group)

# ============================================================
# FAMILY ACTIVITIES
# ============================================================

class FamilyActivities:
    """Eco-friendly family activities database"""
    
    ACTIVITIES = [
        {
            "id": "a1",
            "title": "🌱 Family Garden Project",
            "description": "Start a family vegetable garden",
            "age_group": "All ages",
            "duration": "Ongoing",
            "materials": ["Seeds", "Soil", "Garden tools", "Water"],
            "benefits": ["Food security", "Nature connection", "Healthy eating"],
            "difficulty": "Medium",
            "emoji": "🌱"
        },
        {
            "id": "a2",
            "title": "♻️ Recycled Art Day",
            "description": "Create art from recycled materials",
            "age_group": "Toddler+",
            "duration": "2 hours",
            "materials": ["Recycled materials", "Glue", "Paint", "Imagination"],
            "benefits": ["Creativity", "Waste awareness", "Quality time"],
            "difficulty": "Easy",
            "emoji": "🎨"
        },
        {
            "id": "a3",
            "title": "🌳 Nature Scavenger Hunt",
            "description": "Explore nature while finding specific items",
            "age_group": "Child+",
            "duration": "1-2 hours",
            "materials": ["List of items", "Paper bag", "Magnifying glass"],
            "benefits": ["Observation", "Nature appreciation", "Exercise"],
            "difficulty": "Easy",
            "emoji": "🔍"
        },
        {
            "id": "a4",
            "title": "💧 Water Conservation Challenge",
            "description": "Family competition to save water",
            "age_group": "Toddler+",
            "duration": "1 week",
            "materials": ["Water meter", "Chart", "Prizes"],
            "benefits": ["Water awareness", "Teamwork", "Conservation habits"],
            "difficulty": "Easy",
            "emoji": "💧"
        },
        {
            "id": "a5",
            "title": "🌍 Community Cleanup",
            "description": "Clean up a local park or beach",
            "age_group": "Child+",
            "duration": "2-3 hours",
            "materials": ["Gloves", "Bags", "Recycling containers"],
            "benefits": ["Community service", "Environmental impact", "Teamwork"],
            "difficulty": "Medium",
            "emoji": "🧹"
        },
        {
            "id": "a6",
            "title": "🌿 DIY Compost Bin",
            "description": "Build and maintain a family compost bin",
            "age_group": "Child+",
            "duration": "Ongoing",
            "materials": ["Container", "Soil", "Food scraps", "Leaves"],
            "benefits": ["Waste reduction", "Soil health", "Learning"],
            "difficulty": "Hard",
            "emoji": "♻️"
        }
    ]
    
    @staticmethod
    def get_activities(age_group=None):
        """Get activities by age group"""
        if age_group and age_group != "All":
            return [a for a in FamilyActivities.ACTIVITIES if age_group in a["age_group"] or a["age_group"] == "All ages"]
        return FamilyActivities.ACTIVITIES

# ============================================================
# FAMILY TRACKER
# ============================================================

class FamilyTracker:
    """Track family sustainability progress"""
    
    def __init__(self, family_id):
        self.family_id = family_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load family data from session"""
        if "family_data" not in st.session_state:
            st.session_state.family_data = {}
        return st.session_state.family_data.get(self.family_id, {
            "members": [],
            "completed_activities": [],
            "goals": [],
            "points": 0,
            "streak": 0,
            "start_date": datetime.now().isoformat()
        })
    
    def save(self):
        """Save family data"""
        st.session_state.family_data[self.family_id] = self.data
    
    def add_member(self, name, age_group):
        """Add family member"""
        member = {
            "name": name,
            "age_group": age_group,
            "join_date": datetime.now().isoformat()
        }
        self.data["members"].append(member)
        self.save()
        return member
    
    def complete_activity(self, activity_id):
        """Mark activity as completed"""
        if activity_id not in self.data["completed_activities"]:
            self.data["completed_activities"].append(activity_id)
            self.data["points"] += 20
            self.save()
            return True
        return False
    
    def get_stats(self):
        """Get family statistics"""
        return {
            "members": len(self.data["members"]),
            "activities": len(self.data["completed_activities"]),
            "points": self.data["points"],
            "streak": self.data["streak"],
            "start_date": self.data["start_date"]
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_parenting():
    """Render the complete eco-parenting platform"""
    st.markdown("<div class='section-header'>👨‍👩‍👦 Eco-Parenting & Family Green Living</div>", unsafe_allow_html=True)
    
    family_id = st.session_state.get("user_id", 1)
    
    # Initialize family tracker
    if "family_tracker" not in st.session_state:
        st.session_state.family_tracker = FamilyTracker(family_id)
    
    tracker = st.session_state.family_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👶 Age-Based Guides",
        "🎯 Family Activities",
        "📊 Family Tracker",
        "💡 Parent Resources"
    ])
    
    with tab1:
        render_age_guides(tracker)
    
    with tab2:
        render_family_activities(tracker)
    
    with tab3:
        render_family_tracker(tracker)
    
    with tab4:
        render_parent_resources(tracker)

def render_age_guides(tracker):
    """Render age-based guides"""
    st.markdown("### 👶 Age-Based Sustainability Guides")
    
    # Age group selector
    age_groups = list(AgeBasedGuides.GUIDES.keys())
    selected_age = st.selectbox("Select Age Group", age_groups)
    
    guide = AgeBasedGuides.get_guide(selected_age)
    
    if guide:
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='text-align: center;'>
                <div style='font-size: 48px;'>{guide['title'].split()[0]}</div>
                <h2 style='color: #4ade80;'>{guide['title']}</h2>
                <p style='color: #6b7280;'>{guide['description']}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Tips
        st.markdown("#### 💡 Sustainability Tips")
        for tip in guide["tips"]:
            st.info(f"✅ {tip}")
        
        # Activities
        st.markdown("#### 🎯 Suggested Activities")
        for activity in guide["activities"]:
            st.markdown(f"• {activity}")
        
        # Eco Score Target
        st.markdown("#### 🎯 Eco Score Target")
        st.progress(guide["eco_score_target"] / 100)
        st.caption(f"Target: {guide['eco_score_target']}/100")
        
        # Add family member button
        if st.button("👨‍👩‍👧 Add Family Member", key=f"add_{selected_age}"):
            tracker.add_member(f"Child ({selected_age})", selected_age)
            st.success("✅ Family member added!")
            st.rerun()

def render_family_activities(tracker):
    """Render family activities"""
    st.markdown("### 🎯 Family Eco-Activities")
    
    # Age filter
    age_filters = ["All", "Toddler+", "Child+", "All ages"]
    selected_filter = st.selectbox("Filter by Age Group", age_filters)
    
    # Get activities
    activities = FamilyActivities.get_activities(selected_filter)
    
    # Display activities
    for activity in activities:
        is_completed = activity["id"] in tracker.data["completed_activities"]
        
        difficulty_colors = {
            "Easy": "#4ade80",
            "Medium": "#fbbf24",
            "Hard": "#f87171"
        }
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {difficulty_colors.get(activity["difficulty"], "#6b7280")};'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{activity['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700;'>{activity['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {activity['age_group']} • {activity['duration']} • {activity['difficulty']}
                            </div>
                        </div>
                        <div>
                            {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;">✅ Done</span>' if is_completed else 
                             f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px;">🎯 Try</span>'}
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 4px 0;'>{activity['description']}</p>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap; margin-top: 4px;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{mat}</span>' for mat in activity['materials'][:3]])}
                    </div>
                    <div style='font-size: 13px; color: #4ade80;'>
                        💚 Benefits: {', '.join(activity['benefits'])}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not is_completed:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"✅ Complete", key=f"complete_{activity['id']}"):
                    tracker.complete_activity(activity["id"])
                    st.success("🎉 Activity completed! +20 family points!")
                    st.balloons()
                    st.rerun()
        
        st.markdown("---")

def render_family_tracker(tracker):
    """Render family tracker"""
    st.markdown("### 📊 Family Progress")
    
    stats = tracker.get_stats()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Family Members", stats["members"])
    col2.metric("Activities", stats["activities"])
    col3.metric("Family Points", stats["points"])
    col4.metric("Streak", f"{stats['streak']} days")
    
    # Family members
    st.markdown("#### 👨‍👩‍👧 Family Members")
    
    if tracker.data["members"]:
        for member in tracker.data["members"]:
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{member['name']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>
                            {member['age_group']} • Joined: {datetime.fromisoformat(member["join_date"]).strftime("%b %d, %Y")}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("👶 Add family members from the Age-Based Guides section")
    
    # Progress chart
    if tracker.data["completed_activities"]:
        st.markdown("#### 📈 Activity Progress")
        
        # Get activity categories
        activities = FamilyActivities.get_activities()
        completed = tracker.data["completed_activities"]
        
        categories = {}
        for activity in activities:
            if activity["id"] in completed:
                cat = "Completed"
            else:
                cat = "Pending"
            categories[cat] = categories.get(cat, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(categories.keys()),
            values=list(categories.values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#6b7280'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Goals
    st.markdown("#### 🎯 Family Goals")
    
    with st.form("family_goal_form"):
        col1, col2 = st.columns(2)
        with col1:
            goal_desc = st.text_input("Family Goal", placeholder="e.g., Reduce waste by 20%")
        with col2:
            goal_deadline = st.date_input("Deadline", datetime.now() + timedelta(days=30))
        
        if st.form_submit_button("Set Goal"):
            if goal_desc:
                st.success("✅ Family goal set!")
                st.rerun()
            else:
                st.warning("Please enter a goal description")

def render_parent_resources(tracker):
    """Render parent resources"""
    st.markdown("### 💡 Parent Resources")
    
    resources = {
        "Sustainable Products": [
            "🌿 Eco-friendly diapers - Bamboo and cloth options",
            "🧸 Natural toys - Wooden, organic, non-toxic",
            "👕 Organic clothing - Chemical-free children's clothing",
            "🍎 BPA-free bottles and sippy cups"
        ],
        "Eco-Parenting Tips": [
            "💡 Start small - One change at a time",
            "🌱 Lead by example - Children learn by watching",
            "🗣️ Talk about nature - Build appreciation",
            "📚 Read eco-books - Children's books about environment"
        ],
        "Community Support": [
            "👨‍👩‍👧 Family eco-groups - Join local groups",
            "🌍 Online communities - Connect with eco-parents",
            "📅 Family events - Attend eco-events",
            "🤝 Share experiences - Learn from other families"
        ]
    }
    
    # Resource selector
    resource_type = st.selectbox("Select Resource Type", list(resources.keys()))
    
    for resource in resources[resource_type]:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: center; gap: 10px;'>
                <div style='font-size: 20px;'>{resource.split()[0]}</div>
                <div style='font-size: 14px;'>{resource}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick tips carousel
    st.markdown("---")
    st.markdown("#### 🌟 Quick Eco-Parenting Tips")
    
    tips = [
        "🚶 Walk instead of drive for short trips",
        "♻️ Make recycling a family game",
        "🌱 Start a small herb garden together",
        "📚 Read books about nature and animals",
        "💧 Teach kids to conserve water",
        "🌳 Spend time outdoors every day"
    ]
    
    for tip in tips:
        st.info(f"💡 {tip}")
    
    # Share experience
    st.markdown("---")
    st.markdown("#### 📝 Share Your Eco-Parenting Experience")
    
    with st.form("parent_story_form"):
        story = st.text_area("Share your family's sustainability journey", height=100)
        
        if st.form_submit_button("📤 Share Story"):
            if story:
                st.success("✅ Thank you for sharing your story!")
                tracker.data["points"] += 10
                tracker.save()
                st.rerun()
            else:
                st.warning("Please share your experience")

# ============================================================
# INTEGRATION
# ============================================================

def render_parenting_hub():
    """Render the complete parenting hub"""
    render_eco_parenting()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_parenting import render_parenting_hub

# Add as a new tab

"""