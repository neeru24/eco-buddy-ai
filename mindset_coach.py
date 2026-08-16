# ============================================================
# FILE: mindset_coach.py
# EcoBuddy AI+ Eco-Mindset & Behavioral Change Coach
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json

# ============================================================
# MINDSET ASSESSMENT
# ============================================================

class MindsetAssessment:
    """Psychological assessment for environmental mindset"""
    
    QUESTIONS = [
        {
            "id": "m1",
            "dimension": "Self-Efficacy",
            "question": "I believe my actions can make a difference for the environment.",
            "reverse": False
        },
        {
            "id": "m2",
            "dimension": "Environmental Concern",
            "question": "I am deeply concerned about the state of our planet.",
            "reverse": False
        },
        {
            "id": "m3",
            "dimension": "Action Readiness",
            "question": "I am ready to make significant changes to reduce my environmental impact.",
            "reverse": False
        },
        {
            "id": "m4",
            "dimension": "Cognitive Dissonance",
            "question": "I feel uncomfortable when I act in ways that harm the environment.",
            "reverse": False
        },
        {
            "id": "m5",
            "dimension": "Eco-Anxiety",
            "question": "I often feel anxious about the future of our planet.",
            "reverse": True
        },
        {
            "id": "m6",
            "dimension": "Self-Efficacy",
            "question": "I doubt that individual actions can solve environmental problems.",
            "reverse": True
        },
        {
            "id": "m7",
            "dimension": "Environmental Concern",
            "question": "Environmental issues are not a priority in my daily life.",
            "reverse": True
        },
        {
            "id": "m8",
            "dimension": "Action Readiness",
            "question": "I find it difficult to change my daily habits for the environment.",
            "reverse": True
        }
    ]
    
    @staticmethod
    def conduct_assessment(answers):
        """Calculate mindset scores"""
        dimensions = {}
        
        for q in MindsetAssessment.QUESTIONS:
            dim = q["dimension"]
            if dim not in dimensions:
                dimensions[dim] = {"score": 0, "count": 0}
            
            score = answers.get(q["id"], 3)
            if q["reverse"]:
                score = 6 - score  # Reverse scoring
            
            dimensions[dim]["score"] += score
            dimensions[dim]["count"] += 1
        
        results = {}
        for dim, data in dimensions.items():
            results[dim] = (data["score"] / (data["count"] * 5)) * 100
        
        return results
    
    @staticmethod
    def get_interpretation(score):
        """Interpret mindset score"""
        if score >= 80:
            return "🌟 Strong", "You have a strong environmental mindset. Your beliefs and behaviors are well-aligned."
        elif score >= 60:
            return "🌿 Developing", "You're developing a strong environmental mindset. Continue building awareness."
        elif score >= 40:
            return "📝 Emerging", "You're beginning to develop environmental awareness. Focus on small steps."
        else:
            return "🌱 Starting", "You're at the beginning of your environmental journey. Every step counts!"

# ============================================================
# COGNITIVE REFRAMING
# ============================================================

class CognitiveReframing:
    """Tools for cognitive restructuring"""
    
    PATTERNS = [
        {
            "pattern": "All-or-Nothing",
            "description": "Thinking in absolutes (e.g., 'I'll never be perfectly green')",
            "reframe": "Every small action contributes to the bigger picture. Progress over perfection."
        },
        {
            "pattern": "Catastrophizing",
            "description": "Exaggerating negative consequences (e.g., 'It's too late to change anything')",
            "reframe": "Every positive action creates ripples of change. Hope is a powerful catalyst."
        },
        {
            "pattern": "Personalizing",
            "description": "Blaming yourself for global problems (e.g., 'My small actions don't matter')",
            "reframe": "Collective action starts with individual commitment. Your actions are part of the solution."
        },
        {
            "pattern": "Overgeneralization",
            "description": "Drawing broad conclusions from single events",
            "reframe": "Each moment is a new opportunity to make sustainable choices."
        },
        {
            "pattern": "Should Statements",
            "description": "Creating unrealistic expectations (e.g., 'I should be perfect')",
            "reframe": "I choose to do what I can, and that is enough."
        }
    ]
    
    @staticmethod
    def get_patterns():
        """Get cognitive patterns"""
        return CognitiveReframing.PATTERNS
    
    @staticmethod
    def get_reframe(pattern_name):
        """Get reframe for a pattern"""
        for p in CognitiveReframing.PATTERNS:
            if p["pattern"] == pattern_name:
                return p["reframe"]
        return "Consider alternative perspectives that empower rather than limit."

# ============================================================
# ECO-ANXIETY MANAGEMENT
# ============================================================

class EcoAnxietyManager:
    """Manage eco-anxiety and emotional regulation"""
    
    TECHNIQUES = [
        {
            "name": "Grounding Exercise",
            "description": "Connect with the present moment",
            "steps": [
                "Take a deep breath",
                "Notice 5 things around you",
                "Feel your feet on the ground",
                "Connect with nature in this moment"
            ],
            "emoji": "🧘"
        },
        {
            "name": "Action-Based Coping",
            "description": "Transform anxiety into positive action",
            "steps": [
                "Identify one action you can take today",
                "Focus on what you can control",
                "Connect with like-minded people",
                "Celebrate small wins"
            ],
            "emoji": "💪"
        },
        {
            "name": "Perspective Shift",
            "description": "Reframe your relationship with environmental challenges",
            "steps": [
                "Acknowledge your feelings",
                "Remember that progress is happening",
                "Focus on possibilities not problems",
                "Join a community of change-makers"
            ],
            "emoji": "🌟"
        }
    ]
    
    @staticmethod
    def get_techniques():
        """Get anxiety management techniques"""
        return EcoAnxietyManager.TECHNIQUES
    
    @staticmethod
    def assess_anxiety(answers):
        """Assess eco-anxiety level"""
        # Simplified assessment
        score = sum(answers.values()) / len(answers) if answers else 3
        
        if score >= 4:
            return "High", "Your eco-anxiety is significant. Use coping techniques to manage."
        elif score >= 3:
            return "Moderate", "Some eco-anxiety is normal. Practice regular emotional regulation."
        else:
            return "Low", "You're managing eco-anxiety well. Continue building resilience."

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_mindset_coach():
    """Render the complete mindset coach"""
    st.markdown("<div class='section-header'>🧠 Eco-Mindset & Behavioral Change Coach</div>", unsafe_allow_html=True)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🧠 Mindset Assessment",
        "🔄 Cognitive Reframing",
        "🧘 Eco-Anxiety Management",
        "📓 Reflection Journal",
        "📊 Progress & Insights"
    ])
    
    with tab1:
        render_mindset_assessment()
    
    with tab2:
        render_cognitive_reframing()
    
    with tab3:
        render_anxiety_management()
    
    with tab4:
        render_reflection_journal()
    
    with tab5:
        render_coach_progress()

def render_mindset_assessment():
    """Render mindset assessment"""
    st.markdown("### 🧠 Environmental Mindset Assessment")
    
    st.markdown("""
    <div class='subtitle'>
        Understand your psychological relationship with environmental issues
    </div>
    """, unsafe_allow_html=True)
    
    if "mindset_assessment_done" not in st.session_state:
        st.session_state.mindset_assessment_done = False
    
    if not st.session_state.mindset_assessment_done:
        answers = {}
        
        for q in MindsetAssessment.QUESTIONS:
            st.markdown(f"**{q['question']}**")
            answer = st.radio(
                "Select your response",
                ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"],
                key=f"mindset_{q['id']}",
                index=2,
                horizontal=True
            )
            answers[q['id']] = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"].index(answer) + 1
        
        if st.button("📊 Get Results", type="primary", use_container_width=True):
            results = MindsetAssessment.conduct_assessment(answers)
            st.session_state.mindset_results = results
            st.session_state.mindset_assessment_done = True
            st.rerun()
    
    else:
        # Display results
        results = st.session_state.get("mindset_results", {})
        
        st.markdown("#### 📊 Your Mindset Profile")
        
        # Create radar chart
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=list(results.values()),
            theta=list(results.keys()),
            fill='toself',
            name='Your Score',
            line=dict(color='#4ade80')
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
        
        # Interpretations
        st.markdown("#### 💡 Interpretations")
        
        for dim, score in results.items():
            label, description = MindsetAssessment.get_interpretation(score)
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-weight: 700;'>{dim}</span>
                        <div style='font-size: 13px; color: #6b7280;'>{description}</div>
                    </div>
                    <span style='background: {"#4ade80" if score >= 60 else "#fbbf24" if score >= 40 else "#f87171"}; padding: 4px 12px; border-radius: 20px; font-size: 12px; color: #111827; font-weight: 700;'>
                        {score:.0f}/100
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🔄 Retake Assessment"):
            st.session_state.mindset_assessment_done = False
            st.rerun()

def render_cognitive_reframing():
    """Render cognitive reframing tools"""
    st.markdown("### 🔄 Cognitive Reframing")
    
    st.markdown("""
    <div class='subtitle'>
        Identify and transform limiting thought patterns
    </div>
    """, unsafe_allow_html=True)
    
    patterns = CognitiveReframing.get_patterns()
    
    st.markdown("#### 🧠 Common Thought Patterns")
    
    for pattern in patterns:
        with st.expander(f"🔄 {pattern['pattern']}"):
            st.markdown(f"**Description:** {pattern['description']}")
            st.markdown(f"**Reframe:** {pattern['reframe']}")
            
            # Practice reframing
            st.markdown("#### Practice Reframing")
            user_thought = st.text_area(
                "Write a thought you'd like to reframe",
                placeholder="e.g., I can never be perfectly sustainable...",
                key=f"reframe_{pattern['pattern']}"
            )
            
            if user_thought:
                st.markdown(f"""
                <div class='card-highlight'>
                    <div style='display: flex; align-items: start; gap: 10px;'>
                        <div style='font-size: 24px;'>💡</div>
                        <div>
                            <div style='font-weight: 700; color: #4ade80;'>Reframed Thought:</div>
                            <div style='color: #6b7280; font-size: 14px;'>
                                "{user_thought} → {pattern['reframe']}"
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    # Daily affirmation
    st.markdown("---")
    st.markdown("### 💪 Daily Affirmation")
    
    affirmations = [
        "Every sustainable choice I make creates a ripple of positive change.",
        "I am capable of making a difference for our planet.",
        "Progress, not perfection, is the path to sustainability.",
        "My actions today shape the world of tomorrow.",
        "I choose hope and action over despair and inaction."
    ]
    
    current_affirmation = random.choice(affirmations)
    st.info(f"💚 {current_affirmation}")
    
    if st.button("🔄 New Affirmation"):
        st.rerun()

def render_anxiety_management():
    """Render eco-anxiety management"""
    st.markdown("### 🧘 Eco-Anxiety Management")
    
    st.markdown("""
    <div class='subtitle'>
        Tools to manage emotional responses to environmental concerns
    </div>
    """, unsafe_allow_html=True)
    
    # Quick anxiety check
    st.markdown("#### 📊 How are you feeling today?")
    
    anxiety_level = st.slider("Anxiety Level", 1, 10, 5)
    
    if anxiety_level >= 7:
        st.warning("⚠️ Your anxiety level is high. Try the techniques below.")
    elif anxiety_level >= 4:
        st.info("📝 Moderate anxiety is normal. Practice regulation techniques.")
    else:
        st.success("✅ You're managing well. Continue building resilience.")
    
    st.markdown("---")
    
    # Techniques
    st.markdown("#### 🧘 Coping Techniques")
    
    techniques = EcoAnxietyManager.get_techniques()
    
    for technique in techniques:
        with st.expander(f"{technique['emoji']} {technique['name']}"):
            st.markdown(f"**Description:** {technique['description']}")
            st.markdown("**Steps:**")
            for i, step in enumerate(technique['steps'], 1):
                st.markdown(f"{i}. {step}")
            
            if st.button(f"Practice Now", key=f"practice_{technique['name']}"):
                st.success(f"✅ Practicing {technique['name']}... Take a moment to follow the steps.")
    
    # Grounding exercise
    st.markdown("---")
    st.markdown("#### 🌿 Quick Grounding Exercise")
    
    if st.button("🌍 Start Grounding Exercise", use_container_width=True):
        with st.spinner("Take a moment to ground yourself..."):
            import time
            time.sleep(3)
        
        st.markdown("""
        <div class='card-highlight' style='text-align: center;'>
            <div style='font-size: 48px;'>🌿</div>
            <h4>You are safe in this moment</h4>
            <p style='color: #6b7280; font-size: 14px;'>
                Take a deep breath. Feel your connection to the earth.
                You are part of nature, and nature is resilient.
            </p>
        </div>
        """, unsafe_allow_html=True)

def render_reflection_journal():
    """Render reflection journal"""
    st.markdown("### 📓 Reflection Journal")
    
    st.markdown("""
    <div class='subtitle'>
        Cultivate self-awareness through structured reflection
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize journal
    if "journal_entries" not in st.session_state:
        st.session_state.journal_entries = []
    
    # Journal prompts
    prompts = [
        "What sustainable action did you take today?",
        "How do you feel about your environmental impact?",
        "What challenges did you face in making sustainable choices?",
        "What did you learn about sustainability today?",
        "What positive change are you most proud of?"
    ]
    
    selected_prompt = st.selectbox("Choose a prompt to reflect on", prompts)
    
    # Journal entry
    entry = st.text_area("Write your reflection", height=150, placeholder="Write your thoughts here...")
    
    col1, col2 = st.columns(2)
    with col1:
        mood = st.select_slider("How do you feel?", options=["😟", "😕", "😐", "🙂", "😊"])
    with col2:
        if st.button("💾 Save Entry", use_container_width=True):
            if entry:
                st.session_state.journal_entries.append({
                    "date": datetime.now().isoformat(),
                    "prompt": selected_prompt,
                    "entry": entry,
                    "mood": mood
                })
                st.success("✅ Journal entry saved!")
                st.rerun()
            else:
                st.warning("Please write something before saving")
    
    # Display entries
    if st.session_state.journal_entries:
        st.markdown("#### 📋 Past Entries")
        
        for entry in reversed(st.session_state.journal_entries[-5:]):
            date = datetime.fromisoformat(entry["date"]).strftime("%B %d, %Y")
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>{entry['prompt']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>{entry['entry']}</div>
                        <div style='font-size: 12px; color: #6b7280;'>{date} • Mood: {entry['mood']}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        if len(st.session_state.journal_entries) > 5:
            st.caption(f"Showing 5 of {len(st.session_state.journal_entries)} entries")

def render_coach_progress():
    """Render coach progress"""
    st.markdown("### 📊 Your Coaching Progress")
    
    # Simulated progress data
    progress_data = {
        "Mindset": random.randint(40, 90),
        "Emotional Regulation": random.randint(30, 85),
        "Action Readiness": random.randint(50, 95),
        "Self-Efficacy": random.randint(35, 80),
        "Environmental Concern": random.randint(60, 95)
    }
    
    # Progress chart
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=list(progress_data.keys()),
        y=list(progress_data.values()),
        marker_color=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171'],
        text=[f"{v:.0f}%" for v in progress_data.values()],
        textposition='auto'
    ))
    fig.update_layout(
        height=300,
        margin=dict(l=0, r=0, t=20, b=0),
        yaxis_title="Progress (%)"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Coaching insights
    st.markdown("### 💡 Coaching Insights")
    
    insights = [
        "🧠 Your mindset is developing. Continue practicing cognitive reframing.",
        "🌟 Your environmental concern is high - channel it into positive action.",
        "💪 Your action readiness is strong - you're ready to make changes.",
        "📈 Focus on building self-efficacy through small, consistent actions."
    ]
    
    for insight in insights:
        st.info(insight)
    
    # Goal setting
    st.markdown("### 🎯 Next Steps")
    
    goals = [
        "Practice cognitive reframing daily",
        "Use grounding techniques when anxious",
        "Write in your reflection journal weekly",
        "Connect with others about environmental concerns"
    ]
    
    for goal in goals:
        if st.button(f"✅ Add Goal: {goal}", use_container_width=True):
            st.success(f"✅ Goal added: {goal}")

# ============================================================
# INTEGRATION
# ============================================================

def render_coach_hub():
    """Render the complete coach hub"""
    render_mindset_coach()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from mindset_coach import render_coach_hub

# Add as a new tab
with tab29:
    render_coach_hub()
"""