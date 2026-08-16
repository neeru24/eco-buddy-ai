
# ============================================================
# FILE: eco_art.py
# EcoBuddy AI+ Eco-Art & Creative Sustainability
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# ART GALLERY DATABASE
# ============================================================

class ArtGallery:
    """Eco-art gallery database"""
    
    ARTWORKS = [
        {
            "id": "a1",
            "title": "🌊 Ocean's Cry",
            "artist": "EcoArtist1",
            "category": "Painting",
            "medium": "Recycled Plastic",
            "description": "A powerful representation of ocean pollution using recycled materials",
            "eco_message": "Our oceans are choking on plastic. Reduce, reuse, recycle.",
            "date": datetime.now() - timedelta(days=5),
            "likes": 45,
            "views": 230,
            "featured": True,
            "emoji": "🌊"
        },
        {
            "id": "a2",
            "title": "🌳 Forest Guardian",
            "artist": "GreenBrush",
            "category": "Digital Art",
            "medium": "Digital",
            "description": "A digital painting celebrating the beauty of old-growth forests",
            "eco_message": "Protect our forests - they are the lungs of our planet.",
            "date": datetime.now() - timedelta(days=10),
            "likes": 32,
            "views": 180,
            "featured": False,
            "emoji": "🌳"
        },
        {
            "id": "a3",
            "title": "♻️ Recycled Dreams",
            "artist": "UpcycleQueen",
            "category": "Sculpture",
            "medium": "Found Objects",
            "description": "Sculpture created entirely from found and recycled materials",
            "eco_message": "One person's trash is another's treasure. See the potential in everything.",
            "date": datetime.now() - timedelta(days=15),
            "likes": 28,
            "views": 150,
            "featured": False,
            "emoji": "♻️"
        },
        {
            "id": "a4",
            "title": "💧 Water's Whisper",
            "artist": "NatureLover",
            "category": "Photography",
            "medium": "Digital Photography",
            "description": "A stunning photo capturing the beauty of a pristine lake",
            "eco_message": "Fresh water is precious. Cherish and protect it.",
            "date": datetime.now() - timedelta(days=20),
            "likes": 38,
            "views": 210,
            "featured": True,
            "emoji": "💧"
        },
        {
            "id": "a5",
            "title": "🌿 Green Future",
            "artist": "EcoDreamer",
            "category": "Digital Art",
            "medium": "Digital",
            "description": "A vision of a sustainable future city",
            "eco_message": "Imagine a world where sustainability is the norm.",
            "date": datetime.now() - timedelta(days=25),
            "likes": 22,
            "views": 120,
            "featured": False,
            "emoji": "🌿"
        }
    ]
    
    @staticmethod
    def get_artworks(category=None, featured_only=False):
        """Get artworks with filters"""
        artworks = ArtGallery.ARTWORKS.copy()
        if category and category != "All":
            artworks = [a for a in artworks if a["category"] == category]
        if featured_only:
            artworks = [a for a in artworks if a["featured"]]
        return sorted(artworks, key=lambda x: x["likes"], reverse=True)
    
    @staticmethod
    def get_categories():
        """Get artwork categories"""
        return ["All"] + sorted(set(a["category"] for a in ArtGallery.ARTWORKS))
    
    @staticmethod
    def add_artwork(title, artist, category, medium, description, eco_message):
        """Add new artwork"""
        artwork = {
            "id": f"a{len(ArtGallery.ARTWORKS) + 1}",
            "title": title,
            "artist": artist,
            "category": category,
            "medium": medium,
            "description": description,
            "eco_message": eco_message,
            "date": datetime.now(),
            "likes": 0,
            "views": 0,
            "featured": False,
            "emoji": random.choice(["🎨", "🖼️", "✨", "🌟", "🌈"])
        }
        ArtGallery.ARTWORKS.append(artwork)
        return artwork
    
    @staticmethod
    def like_artwork(artwork_id):
        """Like an artwork"""
        for artwork in ArtGallery.ARTWORKS:
            if artwork["id"] == artwork_id:
                artwork["likes"] += 1
                return True
        return False

# ============================================================
# CREATIVE CHALLENGES
# ============================================================

class CreativeChallenges:
    """Creative sustainability challenges"""
    
    CHALLENGES = [
        {
            "id": "c1",
            "title": "🌱 Recycle Art Challenge",
            "description": "Create art using only recycled materials",
            "category": "Upcycling",
            "duration": "14 days",
            "prize": "Eco Art Supply Kit",
            "participants": 45,
            "featured": True,
            "emoji": "♻️"
        },
        {
            "id": "c2",
            "title": "🌍 Climate Action Poster",
            "description": "Design a poster about climate action",
            "category": "Design",
            "duration": "10 days",
            "prize": "Digital Art Tablet",
            "participants": 38,
            "featured": True,
            "emoji": "🎨"
        },
        {
            "id": "c3",
            "title": "📸 Nature Photography",
            "description": "Capture the beauty of nature in your area",
            "category": "Photography",
            "duration": "21 days",
            "prize": "Photography Workshop",
            "participants": 52,
            "featured": False,
            "emoji": "📸"
        },
        {
            "id": "c4",
            "title": "🌿 Sustainable Garden Art",
            "description": "Create garden art from natural materials",
            "category": "Garden",
            "duration": "14 days",
            "prize": "Garden Tool Set",
            "participants": 29,
            "featured": False,
            "emoji": "🌿"
        }
    ]
    
    @staticmethod
    def get_challenges(category=None):
        """Get challenges with filters"""
        challenges = CreativeChallenges.CHALLENGES.copy()
        if category and category != "All":
            challenges = [c for c in challenges if c["category"] == category]
        return challenges
    
    @staticmethod
    def get_categories():
        """Get challenge categories"""
        return ["All"] + sorted(set(c["category"] for c in CreativeChallenges.CHALLENGES))

# ============================================================
# ARTIST NETWORK
# ============================================================

class ArtistNetwork:
    """Connect eco-artists"""
    
    ARTISTS = [
        {
            "name": "EcoArtist1",
            "location": "New York, USA",
            "medium": ["Recycled Materials", "Acrylic"],
            "focus": "Ocean Conservation",
            "experience": "5 years",
            "portfolio": ["Ocean's Cry", "Wave of Change"],
            "available": True,
            "bio": "Creating art to raise awareness about ocean pollution"
        },
        {
            "name": "GreenBrush",
            "location": "London, UK",
            "medium": ["Digital Art", "Illustration"],
            "focus": "Forest Protection",
            "experience": "7 years",
            "portfolio": ["Forest Guardian", "Tree of Life"],
            "available": True,
            "bio": "Digital artist passionate about forest conservation"
        },
        {
            "name": "UpcycleQueen",
            "location": "Tokyo, Japan",
            "medium": ["Sculpture", "Mixed Media"],
            "focus": "Waste Reduction",
            "experience": "6 years",
            "portfolio": ["Recycled Dreams", "Plastic Paradise"],
            "available": False,
            "bio": "Creating beauty from discarded materials"
        }
    ]
    
    @staticmethod
    def get_artists():
        """Get all artists"""
        return ArtistNetwork.ARTISTS
    
    @staticmethod
    def get_available_artists():
        """Get available artists"""
        return [a for a in ArtistNetwork.ARTISTS if a["available"]]

# ============================================================
# UPCYCLING PROJECTS
# ============================================================

class UpcyclingProjects:
    """Creative upcycling projects"""
    
    PROJECTS = [
        {
            "id": "u1",
            "title": "🌿 Plastic Bottle Planter",
            "description": "Transform plastic bottles into beautiful planters",
            "materials": ["Plastic bottles", "Paint", "Soil", "Plants"],
            "difficulty": "Easy",
            "time": "30 minutes",
            "eco_impact": "Reduces plastic waste, creates green space",
            "likes": 28,
            "emoji": "🌱",
            "instructions": [
                "Clean and dry plastic bottles",
                "Cut bottles in half",
                "Paint and decorate",
                "Add soil and plants"
            ]
        },
        {
            "id": "u2",
            "title": "♻️ Fabric Scrap Rug",
            "description": "Create a colorful rug from fabric scraps",
            "materials": ["Fabric scraps", "Scissors", "Needle", "Thread"],
            "difficulty": "Medium",
            "time": "3 hours",
            "eco_impact": "Diverts textile waste from landfill",
            "likes": 18,
            "emoji": "🧶",
            "instructions": [
                "Cut fabric into strips",
                "Braid or weave strips together",
                "Sew into rug shape"
            ]
        },
        {
            "id": "u3",
            "title": "📦 Cardboard Sculpture",
            "description": "Create sculptures from recycled cardboard",
            "materials": ["Cardboard", "Glue", "Paint"],
            "difficulty": "Medium",
            "time": "2 hours",
            "eco_impact": "Reduces cardboard waste",
            "likes": 15,
            "emoji": "📦",
            "instructions": [
                "Sketch your design",
                "Cut and shape cardboard",
                "Assemble with glue",
                "Paint and decorate"
            ]
        }
    ]
    
    @staticmethod
    def get_projects():
        """Get upcycling projects"""
        return UpcyclingProjects.PROJECTS

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_eco_art():
    """Render the complete eco-art platform"""
    st.markdown("<div class='section-header'>🎨 Eco-Art & Creative Sustainability</div>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🖼️ Art Gallery",
        "🎯 Creative Challenges",
        "👥 Artist Network",
        "♻️ Upcycling Projects",
        "📊 Dashboard"
    ])
    
    with tab1:
        render_art_gallery()
    
    with tab2:
        render_creative_challenges()
    
    with tab3:
        render_artist_network()
    
    with tab4:
        render_upcycling_projects()
    
    with tab5:
        render_art_dashboard()

def render_art_gallery():
    """Render art gallery"""
    st.markdown("### 🖼️ Eco-Art Gallery")
    
    st.markdown("""
    <div class='subtitle'>
        Inspiring art for environmental awareness and action
    </div>
    """, unsafe_allow_html=True)
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        categories = ArtGallery.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        search = st.text_input("🔍 Search Art", placeholder="Search by title or artist...")
    
    # Get artworks
    artworks = ArtGallery.get_artworks(selected_category)
    
    if search:
        artworks = [a for a in artworks if search.lower() in a["title"].lower() or search.lower() in a["artist"].lower()]
    
    st.caption(f"🖼️ {len(artworks)} artworks found")
    
    # Display artworks
    for artwork in artworks:
        days_ago = (datetime.now() - artwork["date"]).days
        time_str = f"{days_ago} days ago" if days_ago > 0 else "Today"
        
        featured_badge = "🌟 Featured" if artwork["featured"] else ""
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 48px;'>{artwork['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{artwork['title']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>👤 {artwork['artist']}</span>
                                <span>📂 {artwork['category']}</span>
                                <span>🎨 {artwork['medium']}</span>
                                <span>📅 {time_str}</span>
                            </div>
                        </div>
                        <div>
                            {f'<span style="background: #fbbf24; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;">{featured_badge}</span>' if featured_badge else ''}
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{artwork['description']}</p>
                    <div style='background: #1f2937; padding: 8px 12px; border-radius: 8px; margin: 6px 0;'>
                        <div style='color: #fbbf24; font-style: italic;'>" {artwork['eco_message']} "</div>
                    </div>
                    <div style='display: flex; gap: 20px; font-size: 13px;'>
                        <span>❤️ {artwork['likes']} likes</span>
                        <span>👁️ {artwork['views']} views</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(f"❤️ Like", key=f"like_{artwork['id']}"):
                ArtGallery.like_artwork(artwork["id"])
                st.success("❤️ Liked!")
                st.rerun()
        
        with col2:
            if st.button(f"💬 Comment", key=f"comment_{artwork['id']}"):
                st.success("💬 Comment feature coming soon!")
        
        st.markdown("---")
    
    # Submit artwork
    st.markdown("#### 🎨 Submit Your Artwork")
    
    with st.form("submit_art_form"):
        col1, col2 = st.columns(2)
        with col1:
            art_title = st.text_input("Artwork Title")
            art_category = st.selectbox("Category", ArtGallery.get_categories()[1:])
            art_medium = st.text_input("Medium/Materials")
        with col2:
            art_artist = st.text_input("Artist Name")
            art_description = st.text_area("Description")
            art_eco_message = st.text_area("Eco Message")
        
        if st.form_submit_button("📤 Submit Artwork"):
            if art_title and art_artist and art_description:
                ArtGallery.add_artwork(art_title, art_artist, art_category, art_medium, art_description, art_eco_message)
                st.success("✅ Artwork submitted successfully! It will be reviewed shortly.")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please fill in all required fields")

def render_creative_challenges():
    """Render creative challenges"""
    st.markdown("### 🎯 Creative Sustainability Challenges")
    
    # Category filter
    categories = CreativeChallenges.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    challenges = CreativeChallenges.get_challenges(selected_category)
    
    for challenge in challenges:
        featured_badge = "🌟 Featured" if challenge["featured"] else ""
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {"#4ade80" if challenge["featured"] else "#6b7280"};'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='font-weight: 700; font-size: 16px;'>{challenge['title']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>{challenge['category']} • {challenge['duration']}</div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{challenge['description']}</p>
                    <div style='display: flex; gap: 15px; font-size: 12px;'>
                        <span>🏷️ Prize: {challenge['prize']}</span>
                        <span>👥 {challenge['participants']} participants</span>
                    </div>
                </div>
                <div style='text-align: right;'>
                    {f'<span style="background: #fbbf24; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;">{featured_badge}</span>' if featured_badge else ''}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"🎯 Join Challenge", key=f"join_{challenge['id']}"):
            st.success(f"✅ Joined {challenge['title']} challenge!")
        
        st.markdown("---")

def render_artist_network():
    """Render artist network"""
    st.markdown("### 👥 Eco-Artist Network")
    
    st.markdown("""
    <div class='subtitle'>
        Connect with artists passionate about sustainability
    </div>
    """, unsafe_allow_html=True)
    
    artists = ArtistNetwork.get_artists()
    
    for artist in artists:
        availability_color = "#4ade80" if artist["available"] else "#6b7280"
        availability_text = "Available" if artist["available"] else "Busy"
        
        st.markdown(f"""
        <div class='card'>
            <div style='display: flex; justify-content: space-between; align-items: start;'>
                <div>
                    <div style='font-weight: 700; font-size: 16px;'>{artist['name']}</div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        📍 {artist['location']} • ⏱️ {artist['experience']}
                    </div>
                    <div style='font-size: 13px; color: #6b7280;'>
                        🎯 Focus: {artist['focus']}
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{artist['bio']}</p>
                    <div style='display: flex; gap: 6px; flex-wrap: wrap;'>
                        {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 11px;">{medium}</span>' for medium in artist['medium']])}
                    </div>
                    <div style='font-size: 12px; color: #4ade80;'>
                        🖼️ Portfolio: {', '.join(artist['portfolio'])}
                    </div>
                </div>
                <div>
                    <span style='background: {availability_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827;'>
                        {availability_text}
                    </span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if artist["available"]:
            if st.button(f"🤝 Connect with {artist['name']}", key=f"connect_{artist['name']}"):
                st.success(f"✅ Connection request sent to {artist['name']}!")
        
        st.markdown("---")
    
    # Join network
    st.markdown("#### 🌟 Join the Artist Network")
    
    with st.form("artist_form"):
        col1, col2 = st.columns(2)
        with col1:
            artist_name = st.text_input("Full Name")
            artist_location = st.text_input("Location")
            artist_focus = st.text_input("Art Focus")
        with col2:
            artist_experience = st.text_input("Years of Experience")
            artist_bio = st.text_area("Bio")
        
        st.markdown("**Mediums:**")
        mediums = st.multiselect("Select Your Mediums", ["Acrylic", "Watercolor", "Digital Art", "Sculpture", "Photography", "Mixed Media", "Recycled Materials"])
        
        if st.form_submit_button("Join Network"):
            st.success("✅ Welcome to the Eco-Artist Network!")
            st.balloons()

def render_upcycling_projects():
    """Render upcycling projects"""
    st.markdown("### ♻️ Upcycling Projects")
    
    st.markdown("""
    <div class='subtitle'>
        Transform waste materials into beautiful creations
    </div>
    """, unsafe_allow_html=True)
    
    projects = UpcyclingProjects.get_projects()
    
    for project in projects:
        difficulty_colors = {
            "Easy": "#4ade80",
            "Medium": "#fbbf24",
            "Hard": "#f87171"
        }
        color = difficulty_colors.get(project["difficulty"], "#6b7280")
        
        st.markdown(f"""
        <div class='card' style='border-left: 4px solid {color};'>
            <div style='display: flex; align-items: start; gap: 12px;'>
                <div style='font-size: 32px;'>{project['emoji']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <div style='font-weight: 700;'>{project['title']}</div>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {project['difficulty']} • {project['time']} • ❤️ {project['likes']}
                            </div>
                        </div>
                        <span style='background: {color}; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;'>
                            {project['difficulty']}
                        </span>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{project['description']}</p>
                    <div style='font-size: 13px; color: #4ade80;'>
                        🌍 {project['eco_impact']}
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"📖 View Instructions", key=f"view_{project['id']}"):
            with st.expander("Instructions", expanded=True):
                st.markdown("**Materials:**")
                for material in project['materials']:
                    st.markdown(f"• {material}")
                st.markdown("**Steps:**")
                for i, step in enumerate(project['instructions'], 1):
                    st.markdown(f"{i}. {step}")
        
        st.markdown("---")

def render_art_dashboard():
    """Render art dashboard"""
    st.markdown("### 📊 Eco-Art Dashboard")
    
    artworks = ArtGallery.get_artworks()
    challenges = CreativeChallenges.get_challenges()
    artists = ArtistNetwork.get_artists()
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🖼️ Artworks", len(artworks))
    col2.metric("🎯 Challenges", len(challenges))
    col3.metric("👥 Artists", len(artists))
    col4.metric("❤️ Total Likes", sum(a["likes"] for a in artworks))
    
    # Category distribution
    st.markdown("#### 📊 Category Distribution")
    
    cat_counts = {}
    for artwork in artworks:
        cat_counts[artwork["category"]] = cat_counts.get(artwork["category"], 0) + 1
    
    fig = go.Figure(data=[go.Pie(
        labels=list(cat_counts.keys()),
        values=list(cat_counts.values()),
        hole=0.3,
        marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171'])
    )])
    fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)
    
    # Top artists
    st.markdown("#### 🏆 Top Artists")
    
    artist_likes = {}
    for artwork in artworks:
        artist_likes[artwork["artist"]] = artist_likes.get(artwork["artist"], 0) + artwork["likes"]
    
    top_artists = sorted(artist_likes.items(), key=lambda x: x[1], reverse=True)[:5]
    
    for artist, likes in top_artists:
        st.markdown(f"• {artist}: {likes} likes")
    
    # Activity feed
    st.markdown("#### 📅 Recent Activity")
    
    activities = [
        "🖼️ New artwork: 'Green Future' by EcoDreamer",
        "❤️ 'Ocean's Cry' reached 45 likes",
        "🎯 New challenge: Recycle Art Challenge",
        "👥 ArtistNetwork: UpcycleQueen joined",
        "♻️ New upcycling project: Plastic Bottle Planter"
    ]
    
    for activity in activities:
        st.info(activity)

# ============================================================
# INTEGRATION
# ============================================================

def render_art_hub():
    """Render the complete art hub"""
    render_eco_art()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from eco_art import render_art_hub

# Add as a new tab
with tab39:
    render_art_hub()
"""