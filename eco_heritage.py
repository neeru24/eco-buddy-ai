
# ============================================================
# FILE: eco_heritage.py
# EcoBuddy AI+ Eco-Heritage & Cultural Sustainability
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# KNOWLEDGE DATABASE
# ============================================================

class HeritageKnowledge:
    """Database of traditional ecological knowledge"""
    
    WISDOM = [
        {
            "id": "k1",
            "title": "🌿 Three Sisters Farming",
            "culture": "Native American",
            "region": "North America",
            "category": "Agriculture",
            "description": "Companion planting of corn, beans, and squash - each plant supports the others",
            "wisdom": "The corn provides a natural trellis for beans, beans fix nitrogen, and squash shades the soil",
            "modern_application": "Sustainable polyculture farming, soil health improvement",
            "emoji": "🌽",
            "contributor": "Elder Knowledge Keeper"
        },
        {
            "id": "k2",
            "title": "🌊 Rainforest Stewardship",
            "culture": "Amazonian",
            "region": "South America",
            "category": "Forestry",
            "description": "Sustainable forest management practices of Amazonian peoples",
            "wisdom": "Harvest only what's needed, plant two for every one taken, use all parts of the plant",
            "modern_application": "Sustainable forestry, conservation biology",
            "emoji": "🌳",
            "contributor": "Community Elder"
        },
        {
            "id": "k3",
            "title": "💧 Water Wisdom",
            "culture": "Various",
            "region": "Global",
            "category": "Water",
            "description": "Traditional water conservation and management techniques",
            "wisdom": "Rainwater harvesting, qanat systems, rainwater gardens, natural filtration",
            "modern_application": "Water conservation, sustainable urban drainage",
            "emoji": "💧",
            "contributor": "Cultural Preservation Society"
        },
        {
            "id": "k4",
            "title": "🌾 Permaculture Principles",
            "culture": "Indigenous",
            "region": "Global",
            "category": "Agriculture",
            "description": "Traditional farming practices that mimic natural ecosystems",
            "wisdom": "Work with nature not against it, diverse polycultures, soil building",
            "modern_application": "Permaculture design, regenerative agriculture",
            "emoji": "🌾",
            "contributor": "Sustainable Farming Network"
        },
        {
            "id": "k5",
            "title": "🔥 Cultural Burning",
            "culture": "Aboriginal Australian",
            "region": "Australia",
            "category": "Forestry",
            "description": "Controlled burning practices for ecosystem management",
            "wisdom": "Small, frequent burns reduce fuel load and promote biodiversity",
            "modern_application": "Wildfire prevention, ecological management",
            "emoji": "🔥",
            "contributor": "Indigenous Fire Practitioners"
        },
        {
            "id": "k6",
            "title": "🏡 Earth Architecture",
            "culture": "Various",
            "region": "Global",
            "category": "Building",
            "description": "Traditional sustainable building materials and techniques",
            "wisdom": "Adobe, rammed earth, straw bale, cob construction with local materials",
            "modern_application": "Sustainable architecture, low-carbon building",
            "emoji": "🏗️",
            "contributor": "Traditional Builders Guild"
        }
    ]
    
    STORIES = [
        {
            "id": "s1",
            "title": "The Giving Tree",
            "culture": "Various",
            "content": "A tree gives shelter, food, and medicine. In return, we must care for it. This is the circle of life.",
            "wisdom": "Reciprocity with nature is essential for survival",
            "contributor": "Elder Storyteller",
            "date": datetime.now() - timedelta(days=10),
            "emoji": "🌳"
        },
        {
            "id": "s2",
            "title": "Water is Life",
            "culture": "Various",
            "content": "Our ancestors taught us that water is sacred. We must protect it for seven generations to come.",
            "wisdom": "Water conservation is a sacred duty",
            "contributor": "Water Protector",
            "date": datetime.now() - timedelta(days=20),
            "emoji": "💧"
        },
        {
            "id": "s3",
            "title": "The Web of Life",
            "culture": "Various",
            "content": "Everything is connected. When we harm one part of nature, we harm ourselves.",
            "wisdom": "Interconnectedness of all living things",
            "contributor": "Wisdom Keeper",
            "date": datetime.now() - timedelta(days=15),
            "emoji": "🕸️"
        }
    ]
    
    @staticmethod
    def get_wisdom(category=None, region=None):
        """Get wisdom with filters"""
        wisdom = HeritageKnowledge.WISDOM.copy()
        if category and category != "All":
            wisdom = [w for w in wisdom if w["category"] == category]
        if region and region != "All":
            wisdom = [w for w in wisdom if w["region"] == region]
        return wisdom
    
    @staticmethod
    def get_stories():
        """Get cultural stories"""
        return HeritageKnowledge.STORIES
    
    @staticmethod
    def get_categories():
        """Get wisdom categories"""
        return ["All"] + sorted(set(w["category"] for w in HeritageKnowledge.WISDOM))
    
    @staticmethod
    def get_regions():
        """Get regions"""
        return ["All"] + sorted(set(w["region"] for w in HeritageKnowledge.WISDOM))

# ============================================================
# HERITAGE TRACKER
# ============================================================

class HeritageTracker:
    """Track user engagement with heritage content"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load heritage data from session"""
        if "heritage_data" not in st.session_state:
            st.session_state.heritage_data = {}
        return st.session_state.heritage_data.get(self.user_id, {
            "saved_wisdom": [],
            "contributed": [],
            "stories_read": [],
            "points": 0
        })
    
    def save(self):
        """Save heritage data"""
        st.session_state.heritage_data[self.user_id] = self.data
    
    def save_wisdom(self, wisdom_id):
        """Save wisdom to personal collection"""
        if wisdom_id not in self.data["saved_wisdom"]:
            self.data["saved_wisdom"].append(wisdom_id)
            self.data["points"] += 5
            self.save()
            return True
        return False
    
    def contribute(self, contribution_type):
        """Track user contribution"""
        self.data["contributed"].append({
            "type": contribution_type,
            "date": datetime.now().isoformat()
        })
        self.data["points"] += 15
        self.save()
        return True

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_heritage():
    """Render the complete heritage platform"""
    st.markdown("<div class='section-header'>🌍 Eco-Heritage & Cultural Sustainability</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize tracker
    if "heritage_tracker" not in st.session_state:
        st.session_state.heritage_tracker = HeritageTracker(user_id)
    
    tracker = st.session_state.heritage_tracker
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📜 Traditional Wisdom",
        "📖 Cultural Stories",
        "🗺️ Heritage Map",
        "🌿 Community Knowledge"
    ])
    
    with tab1:
        render_traditional_wisdom(tracker)
    
    with tab2:
        render_cultural_stories(tracker)
    
    with tab3:
        render_heritage_map()
    
    with tab4:
        render_community_knowledge(tracker)

def render_traditional_wisdom(tracker):
    """Render traditional wisdom"""
    st.markdown("### 📜 Traditional Ecological Knowledge")
    
    st.markdown("""
    <div class='subtitle'>
        Timeless wisdom from indigenous and traditional cultures for sustainable living
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        categories = HeritageKnowledge.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        regions = HeritageKnowledge.get_regions()
        selected_region = st.selectbox("Region", regions)
    
    # Get wisdom
    wisdom = HeritageKnowledge.get_wisdom(selected_category, selected_region)
    
    # Search
    search = st.text_input("🔍 Search Wisdom", placeholder="Search by title or description...")
    if search:
        wisdom = [w for w in wisdom if search.lower() in w["title"].lower() or search.lower() in w["description"].lower()]
    
    st.caption(f"📜 {len(wisdom)} pieces of wisdom found")
    
    # Display wisdom
    for entry in wisdom:
        is_saved = entry["id"] in tracker.data["saved_wisdom"]
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{entry['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{entry['title']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>🏷️ {entry['culture']}</span>
                                <span>📍 {entry['region']}</span>
                                <span>📂 {entry['category']}</span>
                                <span>👤 {entry['contributor']}</span>
                            </div>
                        </div>
                        <div>
                            {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;">✅ Saved</span>' if is_saved else ''}
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{entry['description']}</p>
                    <div style='background: #1f2937; padding: 12px; border-radius: 8px; margin: 8px 0;'>
                        <div style='color: #fbbf24; font-style: italic;'>" {entry['wisdom']} "</div>
                    </div>
                    <div style='font-size: 13px; color: #4ade80;'>
                        💡 Modern Application: {entry['modern_application']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if not is_saved:
                if st.button(f"💾 Save", key=f"save_{entry['id']}"):
                    tracker.save_wisdom(entry["id"])
                    st.success("✅ Wisdom saved! +5 points")
                    st.rerun()
            else:
                st.button("✅ Saved", key=f"saved_{entry['id']}", disabled=True)
        
        with col2:
            if st.button(f"📤 Share Wisdom", key=f"share_{entry['id']}"):
                st.success("📤 Shared with the community!")
        
        st.markdown("---")

def render_cultural_stories(tracker):
    """Render cultural stories"""
    st.markdown("### 📖 Cultural Stories & Wisdom")
    
    stories = HeritageKnowledge.get_stories()
    
    for story in stories:
        date_str = story["date"].strftime("%B %d, %Y")
        read = story["id"] in tracker.data.get("stories_read", [])
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{story['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700;'>{story['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {story['culture']} • 📅 {date_str}
                            </div>
                        </div>
                        {f'<span style="background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;">✅ Read</span>' if read else ''}
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{story['content']}</p>
                    <div style='font-size: 13px; color: #fbbf24;'>
                        💡 Wisdom: {story['wisdom']}
                    </div>
                    <div style='font-size: 12px; color: #6b7280;'>
                        👤 {story['contributor']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if not read:
            if st.button(f"📖 Read Story", key=f"read_{story['id']}"):
                if story["id"] not in tracker.data["stories_read"]:
                    tracker.data["stories_read"].append(story["id"])
                    tracker.data["points"] += 3
                    tracker.save()
                    st.success("📖 Story read! +3 points")
                    st.rerun()
        
        st.markdown("---")
    
    # Share a story
    st.markdown("#### 📝 Share Your Story")
    
    with st.form("story_form"):
        story_title = st.text_input("Story Title")
        story_culture = st.text_input("Culture/Tradition")
        story_content = st.text_area("Share your story or wisdom", height=100)
        
        if st.form_submit_button("📤 Share Story"):
            if story_title and story_content:
                st.success("✅ Thank you for sharing your story! It will help preserve cultural wisdom.")
                tracker.contribute("story")
                st.rerun()
            else:
                st.warning("Please fill in all fields")

def render_heritage_map():
    """Render heritage map"""
    st.markdown("### 🗺️ Heritage Map")
    
    st.markdown("""
    <div class='subtitle'>
        Explore cultural heritage sites and traditional territories
    </div>
    """, unsafe_allow_html=True)
    
    # Simulated map data
    heritage_sites = [
        {"name": "Amazon Rainforest", "region": "South America", "type": "Sacred Site"},
        {"name": "Mesoamerican Gardens", "region": "Central America", "type": "Cultural Site"},
        {"name": "Indigenous Territories", "region": "North America", "type": "Traditional Land"},
        {"name": "Australian Dreamtime Sites", "region": "Australia", "type": "Sacred Site"},
        {"name": "African Rainforest", "region": "Africa", "type": "Cultural Site"},
        {"name": "Himalayan Forests", "region": "Asia", "type": "Traditional Land"},
        {"name": "Nordic Traditional Sites", "region": "Europe", "type": "Cultural Site"},
        {"name": "Pacific Islands", "region": "Oceania", "type": "Sacred Site"}
    ]
    
    # Create a simple map visualization
    site_data = {
        "Type": ["Sacred Site", "Cultural Site", "Traditional Land"],
        "Count": [
            sum(1 for s in heritage_sites if s["type"] == "Sacred Site"),
            sum(1 for s in heritage_sites if s["type"] == "Cultural Site"),
            sum(1 for s in heritage_sites if s["type"] == "Traditional Land")
        ]
    }
    
    fig = go.Figure(data=[go.Pie(
        labels=site_data["Type"],
        values=site_data["Count"],
        hole=0.3,
        marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa'])
    )])
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Display sites
    st.markdown("#### 📍 Heritage Sites")
    
    for site in heritage_sites:
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <div style='font-weight: 600;'>{site['name']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>{site['region']}</div>
                </div>
                <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px;'>
                    {site['type']}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add heritage site form
    st.markdown("---")
    st.markdown("#### ➕ Add Heritage Site")
    
    with st.form("heritage_site_form"):
        col1, col2 = st.columns(2)
        with col1:
            site_name = st.text_input("Site Name")
            site_region = st.text_input("Region")
        with col2:
            site_type = st.selectbox("Type", ["Sacred Site", "Cultural Site", "Traditional Land"])
        
        if st.form_submit_button("📍 Add Site"):
            if site_name:
                st.success("✅ Heritage site added to the map!")
                st.rerun()
            else:
                st.warning("Please enter a site name")

def render_community_knowledge(tracker):
    """Render community knowledge section"""
    st.markdown("### 🌿 Community Knowledge")
    
    st.markdown("""
    <div class='subtitle'>
        Share and discover traditional knowledge from the community
    </div>
    """, unsafe_allow_html=True)
    
    # Contributions stats
    stats = tracker.data.get("contributed", [])
    points = tracker.data.get("points", 0)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Points", points)
    col2.metric("Contributions", len(stats))
    col3.metric("Wisdom Saved", len(tracker.data.get("saved_wisdom", [])))
    
    # Contribution types
    if stats:
        st.markdown("#### 📊 Your Contributions")
        contrib_types = [c["type"] for c in stats]
        df_contrib = pd.DataFrame({"Type": contrib_types})
        contrib_counts = df_contrib["Type"].value_counts()
        
        fig = go.Figure(data=[go.Bar(
            x=list(contrib_counts.index),
            y=list(contrib_counts.values),
            marker_color='#4ade80'
        )])
        fig.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title="Count"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Contribute section
    st.markdown("#### 📝 Contribute Knowledge")
    
    st.markdown("""
    <div class='card-highlight'>
        <div style='display: flex; align-items: center; gap: 12px;'>
            <div style='font-size: 32px;'>🌿</div>
            <div>
                <div style='font-weight: 700;'>Share Your Traditional Knowledge</div>
                <div style='font-size: 14px; color: #6b7280;'>
                    Every contribution helps preserve cultural wisdom for future generations
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("contribute_form"):
        contribution_type = st.selectbox("Contribution Type", ["Wisdom", "Story", "Practice", "Heritage Site"])
        title = st.text_input("Title")
        description = st.text_area("Description", height=100)
        
        if st.form_submit_button("🌿 Contribute"):
            if title and description:
                tracker.contribute(contribution_type.lower())
                st.success("✅ Thank you for contributing! +15 points")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please fill in all fields")

# ============================================================
# INTEGRATION
# ============================================================

def render_heritage_hub():
    """Render the complete heritage hub"""
    render_eco_heritage()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_heritage import render_heritage_hub

# Add as a new tab
with tab33:
    render_heritage_hub()
"""