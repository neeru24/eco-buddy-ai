# ============================================================
# FILE: wellness_center.py
# EcoBuddy AI+ Eco-Wellness & Mindful Living
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# MEDITATION & MINDFULNESS
# ============================================================

class MindfulnessLibrary:
    """Library of eco-themed meditations and mindfulness exercises"""
    
    MEDITATIONS = [
        {
            "id": "m1",
            "title": "Forest Bathing Meditation",
            "description": "Connect with nature through guided visualization",
            "duration": "10 minutes",
            "category": "Nature",
            "difficulty": "Beginner",
            "benefits": ["Stress reduction", "Nature connection", "Mental clarity"],
            "steps": [
                "Find a comfortable position",
                "Close your eyes and take three deep breaths",
                "Visualize yourself in a peaceful forest",
                "Feel the earth beneath your feet",
                "Listen to the birds and rustling leaves",
                "Breathe in the fresh forest air",
                "Gradually return to the present moment"
            ],
            "emoji": "🌳",
            "color": "#4ade80"
        },
        {
            "id": "m2",
            "title": "Ocean Breathing",
            "description": "Rhythmic breathing to calm the mind",
            "duration": "5 minutes",
            "category": "Breathwork",
            "difficulty": "Beginner",
            "benefits": ["Stress reduction", "Focus improvement", "Relaxation"],
            "steps": [
                "Sit comfortably with a straight spine",
                "Inhale for 4 counts",
                "Hold for 4 counts",
                "Exhale for 4 counts",
                "Hold for 4 counts",
                "Repeat for 5 minutes"
            ],
            "emoji": "🌊",
            "color": "#60a5fa"
        },
        {
            "id": "m3",
            "title": "Gratitude Nature Walk",
            "description": "Mindful walking in nature",
            "duration": "15 minutes",
            "category": "Movement",
            "difficulty": "Beginner",
            "benefits": ["Gratitude practice", "Mindfulness", "Physical activity"],
            "steps": [
                "Find a natural setting",
                "Walk slowly and notice your surroundings",
                "Express gratitude for the trees, flowers, and sky",
                "Feel the ground beneath your feet",
                "Notice the sounds of nature",
                "Thank the earth for its gifts"
            ],
            "emoji": "🚶",
            "color": "#fbbf24"
        },
        {
            "id": "m4",
            "title": "Earth Connection Meditation",
            "description": "Feel your connection to the earth",
            "duration": "8 minutes",
            "category": "Nature",
            "difficulty": "Intermediate",
            "benefits": ["Grounding", "Connection", "Peace"],
            "steps": [
                "Sit or lie on the ground",
                "Feel the earth beneath you",
                "Breathe in the earth's energy",
                "Imagine roots growing from your body into the earth",
                "Feel supported and connected",
                "Send loving energy back to the earth"
            ],
            "emoji": "🌍",
            "color": "#34d399"
        },
        {
            "id": "m5",
            "title": "Eco-Anxiety Relief",
            "description": "Managing anxiety about environmental issues",
            "duration": "12 minutes",
            "category": "Mental Health",
            "difficulty": "Intermediate",
            "benefits": ["Anxiety reduction", "Hope restoration", "Empowerment"],
            "steps": [
                "Acknowledge your feelings about the environment",
                "Take a deep breath",
                "Focus on what you can control",
                "Visualize positive environmental change",
                "Find hope in collective action",
                "End with a commitment to take one positive action"
            ],
            "emoji": "🧘",
            "color": "#a78bfa"
        }
    ]
    
    @staticmethod
    def get_meditations(category=None):
        """Get meditations by category"""
        meditations = MindfulnessLibrary.MEDITATIONS.copy()
        if category:
            meditations = [m for m in meditations if m["category"] == category]
        return meditations
    
    @staticmethod
    def get_categories():
        """Get meditation categories"""
        return sorted(set(m["category"] for m in MindfulnessLibrary.MEDITATIONS))

# ============================================================
# NATURE JOURNAL
# ============================================================

class NatureJournal:
    """Track nature observations and gratitude"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.entries = self._load_entries()
    
    def _load_entries(self):
        """Load journal entries from session"""
        if "nature_journal" not in st.session_state:
            st.session_state.nature_journal = {}
        return st.session_state.nature_journal.get(self.user_id, [])
    
    def save(self):
        """Save journal entries"""
        st.session_state.nature_journal[self.user_id] = self.entries
    
    def add_entry(self, observation, gratitude, mood, location=None):
        """Add a journal entry"""
        entry = {
            "id": len(self.entries) + 1,
            "date": datetime.now().isoformat(),
            "observation": observation,
            "gratitude": gratitude,
            "mood": mood,
            "location": location,
            "timestamp": datetime.now().isoformat()
        }
        self.entries.insert(0, entry)  # Newest first
        self.save()
        return entry
    
    def get_stats(self):
        """Get journal statistics"""
        if not self.entries:
            return {
                "total": 0,
                "week_count": 0,
                "mood_trend": [],
                "common_observations": []
            }
        
        df = pd.DataFrame(self.entries)
        df['date'] = pd.to_datetime(df['date']).dt.date
        
        # Week count
        week_ago = datetime.now().date() - timedelta(days=7)
        week_count = len(df[df['date'] >= week_ago])
        
        # Mood trend
        mood_trend = df['mood'].tolist()
        
        # Common observations (simple text analysis)
        observations = ' '.join(df['observation'].tolist())
        words = observations.lower().split()
        common_words = [w for w in words if len(w) > 3]
        
        return {
            "total": len(self.entries),
            "week_count": week_count,
            "mood_trend": mood_trend,
            "common_observations": list(set(common_words[:5]))
        }

# ============================================================
# ECO-GRATITUDE PRACTICE
# ============================================================

class EcoGratitude:
    """Daily eco-gratitude practice"""
    
    PROMPTS = [
        "What natural beauty did you notice today?",
        "What aspect of nature are you grateful for?",
        "How did you connect with the environment today?",
        "What environmental action made you feel proud?",
        "What sustainable choice did you make today?",
        "What wildlife did you observe today?",
        "What natural sound brought you peace?",
        "What sustainable habit are you developing?"
    ]
    
    @staticmethod
    def get_daily_prompt():
        """Get today's gratitude prompt"""
        day = datetime.now().day
        return EcoGratitude.PROMPTS[day % len(EcoGratitude.PROMPTS)]
    
    @staticmethod
    def get_random_prompt():
        """Get a random gratitude prompt"""
        return random.choice(EcoGratitude.PROMPTS)

# ============================================================
# NATURE CONNECTION QUIZ
# ============================================================

class NatureConnectionQuiz:
    """Quiz to assess nature connection"""
    
    QUESTIONS = [
        {
            "question": "How often do you spend time in nature?",
            "options": ["Daily", "Weekly", "Monthly", "Rarely"],
            "scores": [4, 3, 2, 1]
        },
        {
            "question": "How connected do you feel to the natural world?",
            "options": ["Deeply connected", "Somewhat connected", "Slightly connected", "Disconnected"],
            "scores": [4, 3, 2, 1]
        },
        {
            "question": "How often do you notice wildlife around you?",
            "options": ["Frequently", "Sometimes", "Rarely", "Never"],
            "scores": [4, 3, 2, 1]
        },
        {
            "question": "How important is nature to your well-being?",
            "options": ["Essential", "Very important", "Somewhat important", "Not important"],
            "scores": [4, 3, 2, 1]
        },
        {
            "question": "How often do you practice mindfulness in nature?",
            "options": ["Daily", "Weekly", "Occasionally", "Never"],
            "scores": [4, 3, 2, 1]
        }
    ]
    
    @staticmethod
    def get_quiz():
        """Get the nature connection quiz"""
        return NatureConnectionQuiz.QUESTIONS
    
    @staticmethod
    def calculate_score(answers):
        """Calculate nature connection score"""
        total = sum(answers)
        max_score = len(NatureConnectionQuiz.QUESTIONS) * 4
        
        percentage = (total / max_score) * 100
        
        if percentage >= 80:
            return "🌿 Deep Nature Connection", percentage
        elif percentage >= 60:
            return "🌱 Growing Connection", percentage
        elif percentage >= 40:
            return "🌳 Developing Connection", percentage
        else:
            return "🌱 Nature Connection Opportunity", percentage

# ============================================================
# ECO-AFFIRMATIONS
# ============================================================

class EcoAffirmations:
    """Positive affirmations for eco-conscious living"""
    
    AFFIRMATIONS = [
        "🌍 I am part of nature, and nature is part of me",
        "💚 My choices today create a better tomorrow",
        "🌱 I have the power to make a positive impact",
        "🌿 Each small action I take matters",
        "☀️ I am grateful for the earth's abundant gifts",
        "💧 I respect and conserve natural resources",
        "🌳 I am connected to all living beings",
        "🌺 I choose kindness for the planet",
        "🌟 I am a steward of the earth",
        "🌍 Together, we can create a sustainable future",
        "💚 My eco-friendly habits are making a difference",
        "🌱 I am learning and growing in sustainability",
        "🌿 Every day, I make choices that honor nature",
        "☀️ I am grateful for clean air, water, and land",
        "💧 I use resources wisely and with gratitude",
        "🌳 I find peace and inspiration in nature",
        "🌺 I am part of the solution",
        "🌟 My actions ripple outward to create change"
    ]
    
    @staticmethod
    def get_affirmation():
        """Get a random affirmation"""
        return random.choice(EcoAffirmations.AFFIRMATIONS)
    
    @staticmethod
    def get_daily_affirmation():
        """Get affirmation of the day"""
        day = datetime.now().day
        return EcoAffirmations.AFFIRMATIONS[day % len(EcoAffirmations.AFFIRMATIONS)]

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_wellness_center():
    """Render the complete wellness center"""
    st.markdown("<div class='section-header'>🧘 Eco-Wellness & Mindful Living</div>", unsafe_allow_html=True)
    
    # Daily affirmation
    st.info(f"💚 **Daily Affirmation:** {EcoAffirmations.get_daily_affirmation()}")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🧘 Meditations",
        "📓 Nature Journal",
        "🙏 Gratitude Practice",
        "🌿 Connection Quiz"
    ])
    
    with tab1:
        render_meditations()
    
    with tab2:
        render_nature_journal()
    
    with tab3:
        render_gratitude_practice()
    
    with tab4:
        render_nature_quiz()

def render_meditations():
    """Render meditations"""
    st.markdown("### 🧘 Guided Meditations")
    
    # Category filter
    categories = ["All"] + MindfulnessLibrary.get_categories()
    selected_category = st.selectbox("Filter by Category", categories)
    
    # Get meditations
    if selected_category == "All":
        meditations = MindfulnessLibrary.get_meditations()
    else:
        meditations = MindfulnessLibrary.get_meditations(selected_category)
    
    # Display meditations
    for meditation in meditations:
        with st.container():
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='display: flex; align-items: start; gap: 15px;'>
                    <div style='font-size: 40px;'>{meditation['emoji']}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h4 style='margin: 0; color: #4ade80;'>{meditation['title']}</h4>
                                <span style='font-size: 13px; color: #6b7280;'>
                                    {meditation['category']} • {meditation['difficulty']} • {meditation['duration']}
                                </span>
                            </div>
                            <span style='background: {meditation['color']}20; padding: 4px 12px; border-radius: 20px; color: {meditation['color']}; font-weight: 700; font-size: 12px;'>
                                ⏱️ {meditation['duration']}
                            </span>
                        </div>
                        <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{meditation['description']}</p>
                        <div style='display: flex; gap: 6px; flex-wrap: wrap;'>
                            {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px;">{benefit}</span>' for benefit in meditation['benefits'][:3]])}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show steps button
            if st.button(f"🧘 Start {meditation['title']}", key=f"med_{meditation['id']}"):
                st.session_state.selected_meditation = meditation['id']
                st.rerun()
    
    # Show selected meditation details
    if st.session_state.get("selected_meditation"):
        meditation = next((m for m in MindfulnessLibrary.MEDITATIONS if m["id"] == st.session_state.selected_meditation), None)
        if meditation:
            with st.expander(f"🧘 {meditation['title']} - Guided Practice", expanded=True):
                st.markdown(f"**Description:** {meditation['description']}")
                st.markdown(f"**Duration:** {meditation['duration']}")
                
                st.markdown("**Practice Steps:**")
                for i, step in enumerate(meditation['steps'], 1):
                    st.markdown(f"{i}. {step}")
                
                # Timer
                col1, col2 = st.columns([1, 2])
                with col1:
                    if st.button("⏱️ Start Timer"):
                        st.session_state.timer_active = True
                
                if st.session_state.get("timer_active", False):
                    st.markdown("**Timer:** [10:00 remaining]")
                    with col2:
                        if st.button("⏹️ Stop Timer"):
                            st.session_state.timer_active = False
                            st.rerun()
                
                if st.button("🔄 Close Practice"):
                    st.session_state.selected_meditation = None
                    st.rerun()

def render_nature_journal():
    """Render nature journal"""
    st.markdown("### 📓 Nature Journal")
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize journal
    if "nature_journal_obj" not in st.session_state:
        st.session_state.nature_journal_obj = NatureJournal(user_id)
    
    journal = st.session_state.nature_journal_obj
    
    # Add entry
    with st.expander("✍️ New Journal Entry", expanded=False):
        with st.form("journal_form"):
            observation = st.text_area("🌿 What did you observe in nature today?", height=100)
            gratitude = st.text_area("🙏 What are you grateful for in nature today?", height=100)
            mood = st.slider("😊 How are you feeling today?", 1, 5, 3)
            location = st.text_input("📍 Where did you experience nature?")
            
            if st.form_submit_button("💾 Save Journal Entry"):
                if observation and gratitude:
                    journal.add_entry(observation, gratitude, mood, location)
                    st.success("✅ Journal entry saved!")
                    st.rerun()
                else:
                    st.warning("Please fill in both observation and gratitude fields")
    
    # Display statistics
    stats = journal.get_stats()
    
    if stats['total'] > 0:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Entries", stats['total'])
        col2.metric("This Week", stats['week_count'])
        col3.metric("Mood Trend", f"{sum(stats['mood_trend'])/len(stats['mood_trend']):.1f}/5" if stats['mood_trend'] else "N/A")
        
        # Display recent entries
        st.markdown("### 📋 Recent Entries")
        
        for entry in journal.entries[:5]:
            date = datetime.fromisoformat(entry['date']).strftime("%b %d, %Y")
            mood_emoji = ["😊", "🙂", "😐", "😕", "😟"][entry['mood'] - 1] if 1 <= entry['mood'] <= 5 else "😊"
            
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 600;'>{date}</span>
                    <span>{mood_emoji} {entry['mood']}/5</span>
                </div>
                <div style='color: #6b7280; font-size: 14px; margin-top: 6px;'>
                    <div><b>🌿 Observed:</b> {entry['observation']}</div>
                    <div><b>🙏 Grateful:</b> {entry['gratitude']}</div>
                    {f'<div><b>📍 Location:</b> {entry["location"]}</div>' if entry.get('location') else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📓 Start your nature journal by adding your first entry above!")

def render_gratitude_practice():
    """Render gratitude practice"""
    st.markdown("### 🙏 Daily Eco-Gratitude Practice")
    
    # Daily prompt
    prompt = EcoGratitude.get_daily_prompt()
    
    st.markdown(f"""
    <div class='card-highlight'>
        <div style='text-align: center;'>
            <div style='font-size: 32px;'>🌿</div>
            <h4 style='color: #4ade80;'>Today's Gratitude Prompt</h4>
            <p style='font-size: 18px;'>{prompt}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Gratitude entry
    with st.form("gratitude_form"):
        gratitude_text = st.text_area("✍️ Write your gratitude here", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            mood_after = st.select_slider("How do you feel now?", options=["😟", "😕", "😐", "🙂", "😊"])
        with col2:
            action_taken = st.text_input("What action will you take to honor nature?")
        
        if st.form_submit_button("💾 Save Gratitude"):
            if gratitude_text:
                # Save to journal as well
                journal = st.session_state.get("nature_journal_obj")
                if journal:
                    journal.add_entry(
                        f"Gratitude: {gratitude_text[:50]}...",
                        gratitude_text,
                        ["😟", "😕", "😐", "🙂", "😊"].index(mood_after) + 1
                    )
                st.success("✅ Your gratitude has been saved!")
                st.balloons()
                st.rerun()
            else:
                st.warning("Please write your gratitude before saving")
    
    # Gratitude prompts generator
    st.markdown("### 🎲 More Gratitude Prompts")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🌿 New Prompt", use_container_width=True):
            st.session_state.gratitude_prompt = EcoGratitude.get_random_prompt()
            st.rerun()
    
    if "gratitude_prompt" in st.session_state:
        st.info(f"💡 {st.session_state.gratitude_prompt}")

def render_nature_quiz():
    """Render nature connection quiz"""
    st.markdown("### 🌿 Nature Connection Quiz")
    st.markdown("Discover your connection to the natural world")
    
    questions = NatureConnectionQuiz.get_quiz()
    
    if "nature_quiz_submitted" not in st.session_state:
        st.session_state.nature_quiz_submitted = False
    
    if not st.session_state.nature_quiz_submitted:
        answers = []
        
        for i, q in enumerate(questions):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            answer = st.radio(
                "Select your answer",
                q['options'],
                key=f"nature_quiz_{i}",
                label_visibility="collapsed"
            )
            answers.append(q['options'].index(answer))
        
        if st.button("🌿 See My Nature Connection Score", type="primary", use_container_width=True):
            score = sum(q['scores'][a] for q, a in zip(questions, answers))
            label, percentage = NatureConnectionQuiz.calculate_score(answers)
            
            st.session_state.nature_quiz_score = score
            st.session_state.nature_quiz_percentage = percentage
            st.session_state.nature_quiz_label = label
            st.session_state.nature_quiz_submitted = True
            st.rerun()
    
    else:
        # Show results
        label = st.session_state.get("nature_quiz_label", "")
        percentage = st.session_state.get("nature_quiz_percentage", 0)
        
        st.markdown("### 🌿 Your Nature Connection Score")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overall Score", f"{percentage:.0f}%")
        
        with col2:
            st.metric("Connection Level", label)
        
        # Progress bar
        st.progress(percentage / 100)
        
        # Recommendations
        st.markdown("### 💡 Recommendations")
        
        if percentage >= 80:
            st.success("🌟 Excellent nature connection! Continue deepening your relationship with the natural world through daily practice.")
            st.markdown("**Next Steps:**")
            st.markdown("• Share your connection with others")
            st.markdown("• Lead nature walks in your community")
            st.markdown("• Start a nature journaling group")
        elif percentage >= 60:
            st.info("🌱 Good nature connection! Here are ways to deepen it:")
            st.markdown("• Spend at least 15 minutes in nature daily")
            st.markdown("• Practice mindfulness in nature")
            st.markdown("• Learn about local wildlife and plants")
        elif percentage >= 40:
            st.warning("🌳 Developing nature connection. Try these:")
            st.markdown("• Start with 5 minutes of nature time daily")
            st.markdown("• Bring nature indoors with plants")
            st.markdown("• Notice the sky, trees, and birds around you")
        else:
            st.info("🌱 Opportunity to strengthen your nature connection:")
            st.markdown("• Begin with simple observation")
            st.markdown("• Take a mindful walk in a park")
            st.markdown("• Practice gratitude for nature")
        
        if st.button("🔄 Retake Quiz", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key.startswith("nature_quiz"):
                    del st.session_state[key]
            st.rerun()
    
    # Nature connection tips
    st.markdown("---")
    st.markdown("### 🌿 Tips for Deepening Nature Connection")
    
    tips = [
        "🌅 Watch the sunrise or sunset daily",
        "🌳 Touch a tree and feel its energy",
        "🐦 Listen to birdsong",
        "🌺 Notice the flowers and plants around you",
        "💧 Observe the movement of water",
        "🌿 Practice deep breathing outdoors",
        "📸 Take photos of natural beauty",
        "🧘 Meditate in a natural setting"
    ]
    
    cols = st.columns(3)
    for i, tip in enumerate(tips):
        with cols[i % 3]:
            st.markdown(f"""
            <div style='background: #1f2937; padding: 12px; border-radius: 10px; text-align: center; margin: 5px 0; height: 80px; display: flex; align-items: center; justify-content: center;'>
                <div style='font-size: 13px;'>{tip}</div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_wellness_hub():
    """Render the complete wellness hub"""
    render_wellness_center()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from wellness_center import render_wellness_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16, tab17 = st.tabs([
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
    "🧘 Eco-Wellness"  # NEW
])

with tab17:
    render_wellness_hub()
"""