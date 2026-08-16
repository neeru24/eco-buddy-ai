# ============================================================
# FILE: learning_center.py
# EcoBuddy AI+ Eco-Education & Learning Center
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import math

# ============================================================
# COURSE DATABASE
# ============================================================

class CourseDatabase:
    """Database of sustainability courses"""
    
    COURSES = [
        {
            "id": "c1",
            "title": "Introduction to Sustainability",
            "category": "Basics",
            "level": "Beginner",
            "duration": "2 hours",
            "modules": 5,
            "description": "Learn the fundamentals of sustainability and environmental science",
            "topics": ["What is Sustainability", "The 3 Pillars", "Environmental Impact", "Sustainable Development Goals"],
            "certificate": True,
            "rating": 4.8,
            "students": 12500,
            "emoji": "🌍",
            "color": "#4ade80"
        },
        {
            "id": "c2",
            "title": "Climate Change 101",
            "category": "Climate",
            "level": "Beginner",
            "duration": "3 hours",
            "modules": 6,
            "description": "Understanding climate change causes, effects, and solutions",
            "topics": ["Greenhouse Effect", "Carbon Cycle", "Global Warming", "Climate Action"],
            "certificate": True,
            "rating": 4.9,
            "students": 18000,
            "emoji": "🌡️",
            "color": "#f87171"
        },
        {
            "id": "c3",
            "title": "Zero Waste Living",
            "category": "Lifestyle",
            "level": "Beginner",
            "duration": "1.5 hours",
            "modules": 4,
            "description": "Practical guide to reducing waste in your daily life",
            "topics": ["Waste Management", "Recycling", "Composting", "Zero Waste Habits"],
            "certificate": False,
            "rating": 4.7,
            "students": 8500,
            "emoji": "♻️",
            "color": "#60a5fa"
        },
        {
            "id": "c4",
            "title": "Renewable Energy Fundamentals",
            "category": "Energy",
            "level": "Intermediate",
            "duration": "4 hours",
            "modules": 8,
            "description": "Deep dive into solar, wind, hydro, and other renewable energy sources",
            "topics": ["Solar Power", "Wind Energy", "Hydro Power", "Geothermal", "Bioenergy"],
            "certificate": True,
            "rating": 4.6,
            "students": 9200,
            "emoji": "☀️",
            "color": "#fbbf24"
        },
        {
            "id": "c5",
            "title": "Sustainable Food Systems",
            "category": "Food",
            "level": "Intermediate",
            "duration": "3 hours",
            "modules": 6,
            "description": "Understanding sustainable agriculture and food production",
            "topics": ["Organic Farming", "Food Miles", "Plant-based Diet", "Food Waste"],
            "certificate": False,
            "rating": 4.5,
            "students": 6700,
            "emoji": "🥗",
            "color": "#a78bfa"
        },
        {
            "id": "c6",
            "title": "Green Business Practices",
            "category": "Business",
            "level": "Advanced",
            "duration": "5 hours",
            "modules": 10,
            "description": "Implementing sustainability in business operations",
            "topics": ["ESG", "Green Marketing", "Sustainable Supply Chain", "Carbon Accounting"],
            "certificate": True,
            "rating": 4.8,
            "students": 5400,
            "emoji": "💼",
            "color": "#34d399"
        },
        {
            "id": "c7",
            "title": "Water Conservation",
            "category": "Water",
            "level": "Beginner",
            "duration": "2 hours",
            "modules": 4,
            "description": "Learn techniques to conserve water at home and in your community",
            "topics": ["Water Cycle", "Water Scarcity", "Efficient Usage", "Rainwater Harvesting"],
            "certificate": False,
            "rating": 4.4,
            "students": 7200,
            "emoji": "💧",
            "color": "#60a5fa"
        },
        {
            "id": "c8",
            "title": "Biodiversity & Conservation",
            "category": "Biodiversity",
            "level": "Intermediate",
            "duration": "3.5 hours",
            "modules": 7,
            "description": "Understanding ecosystems, species conservation, and biodiversity",
            "topics": ["Ecosystems", "Species at Risk", "Habitat Restoration", "Conservation Strategies"],
            "certificate": True,
            "rating": 4.7,
            "students": 4800,
            "emoji": "🐝",
            "color": "#34d399"
        }
    ]
    
    @staticmethod
    def get_courses(filters=None):
        """Get courses with filters"""
        courses = CourseDatabase.COURSES.copy()
        
        if filters:
            if filters.get("category"):
                courses = [c for c in courses if c["category"] == filters["category"]]
            if filters.get("level"):
                courses = [c for c in courses if c["level"] == filters["level"]]
            if filters.get("certificate_only"):
                courses = [c for c in courses if c["certificate"] == True]
        
        return courses
    
    @staticmethod
    def get_categories():
        """Get course categories"""
        return sorted(set(c["category"] for c in CourseDatabase.COURSES))
    
    @staticmethod
    def get_levels():
        """Get difficulty levels"""
        return ["Beginner", "Intermediate", "Advanced"]

# ============================================================
# ECO-QUIZZES
# ============================================================

class EcoQuizzes:
    """Interactive eco-quizzes for learning"""
    
    QUIZZES = {
        "sustainability_basics": {
            "title": "Sustainability Basics Quiz",
            "description": "Test your knowledge about sustainability fundamentals",
            "category": "Basics",
            "difficulty": "Easy",
            "questions": [
                {
                    "question": "What are the three pillars of sustainability?",
                    "options": ["Environmental, Social, Economic", "Green, Clean, Renewable", "Air, Water, Land", "Reduce, Reuse, Recycle"],
                    "correct": 0,
                    "explanation": "The three pillars are Environmental, Social, and Economic sustainability."
                },
                {
                    "question": "What is the greenhouse effect?",
                    "options": ["Trapping of heat by greenhouse gases", "Growing plants in greenhouses", "Global warming reversal", "Cooling of the atmosphere"],
                    "correct": 0,
                    "explanation": "Greenhouse gases trap heat in the atmosphere, causing the greenhouse effect."
                },
                {
                    "question": "What is the current atmospheric CO₂ level?",
                    "options": ["280 ppm", "350 ppm", "420 ppm", "500 ppm"],
                    "correct": 2,
                    "explanation": "Current CO₂ levels are around 420 ppm, up from 280 ppm pre-industrial."
                }
            ]
        },
        "climate_change": {
            "title": "Climate Change Quiz",
            "description": "Test your knowledge about climate change",
            "category": "Climate",
            "difficulty": "Medium",
            "questions": [
                {
                    "question": "What is the main cause of global warming?",
                    "options": ["Solar activity", "Volcanic eruptions", "Human activities", "Natural cycles"],
                    "correct": 2,
                    "explanation": "Human activities, particularly burning fossil fuels, are the main cause."
                },
                {
                    "question": "What is the Paris Agreement target temperature rise limit?",
                    "options": ["1.5°C", "2.0°C", "2.5°C", "3.0°C"],
                    "correct": 0,
                    "explanation": "The target is to limit warming to 1.5°C above pre-industrial levels."
                }
            ]
        },
        "renewable_energy": {
            "title": "Renewable Energy Quiz",
            "description": "Test your knowledge about renewable energy",
            "category": "Energy",
            "difficulty": "Medium",
            "questions": [
                {
                    "question": "Which renewable energy source produces the most electricity globally?",
                    "options": ["Solar", "Wind", "Hydro", "Geothermal"],
                    "correct": 2,
                    "explanation": "Hydroelectric power is the largest source of renewable electricity."
                },
                {
                    "question": "What is the most efficient solar panel type?",
                    "options": ["Monocrystalline", "Polycrystalline", "Thin-film", "Perovskite"],
                    "correct": 0,
                    "explanation": "Monocrystalline panels are the most efficient, up to 22%."
                }
            ]
        }
    }
    
    @staticmethod
    def get_quizzes(category=None):
        """Get quizzes by category"""
        quizzes = EcoQuizzes.QUIZZES.copy()
        if category:
            quizzes = {k: v for k, v in quizzes.items() if v["category"] == category}
        return quizzes
    
    @staticmethod
    def get_quiz(quiz_id):
        """Get a specific quiz"""
        return EcoQuizzes.QUIZZES.get(quiz_id)

# ============================================================
# LEARNING PATHS
# ============================================================

class LearningPaths:
    """Curated learning paths for users"""
    
    PATHS = {
        "sustainability_basics": {
            "title": "Sustainability Basics",
            "description": "Start your sustainability journey",
            "courses": ["c1", "c2"],
            "difficulty": "Beginner",
            "duration": "5 hours"
        },
        "climate_action": {
            "title": "Climate Action",
            "description": "Learn about climate change and solutions",
            "courses": ["c2", "c4", "c6"],
            "difficulty": "Intermediate",
            "duration": "12 hours"
        },
        "sustainable_lifestyle": {
            "title": "Sustainable Lifestyle",
            "description": "Practical sustainable living skills",
            "courses": ["c3", "c5", "c7"],
            "difficulty": "Beginner",
            "duration": "6.5 hours"
        },
        "green_professional": {
            "title": "Green Professional",
            "description": "Sustainability for career professionals",
            "courses": ["c6", "c4", "c8"],
            "difficulty": "Advanced",
            "duration": "15 hours"
        }
    }
    
    @staticmethod
    def get_paths():
        """Get all learning paths"""
        return LearningPaths.PATHS
    
    @staticmethod
    def get_path(path_id):
        """Get a specific learning path"""
        return LearningPaths.PATHS.get(path_id)

# ============================================================
# ECO-FACT OF THE DAY
# ============================================================

class EcoFactsLibrary:
    """Library of eco-facts for daily learning"""
    
    FACTS = [
        "🌍 One tree can absorb up to 22kg of CO2 per year",
        "💡 LED bulbs use 75% less energy than incandescent bulbs",
        "🚗 Taking public transport can reduce your carbon footprint by 30%",
        "🥩 Producing 1kg of beef generates 27kg of CO2",
        "♻️ Recycling one aluminum can saves enough energy to power a TV for 3 hours",
        "🌊 8 million tons of plastic enter the ocean every year",
        "🌱 Planting trees is the most cost-effective way to fight climate change",
        "💧 Turning off the tap while brushing saves up to 8 gallons of water per day",
        "☀️ Solar energy is the most abundant energy source on Earth",
        "🚲 Cycling instead of driving saves 150g of CO2 per kilometer",
        "🌿 A plant-based diet can reduce carbon footprint by 50%",
        "♻️ The average person generates 4.4 pounds of waste per day",
        "🌊 Coral reefs support 25% of all marine life",
        "🌳 Forests cover 31% of the Earth's land area",
        "💡 Energy efficiency is the cheapest form of energy",
        "🚶 Walking 10,000 steps daily reduces CO2 by 3kg per year",
        "🌿 Composting reduces methane emissions from landfills",
        "☀️ Solar power is now cheaper than coal in most countries",
        "🌍 The ozone layer is recovering thanks to international action",
        "💧 Water conservation can save up to 30% of household water usage"
    ]
    
    @staticmethod
    def get_daily_fact():
        """Get fact of the day"""
        day = datetime.now().day
        return EcoFactsLibrary.FACTS[day % len(EcoFactsLibrary.FACTS)]
    
    @staticmethod
    def get_random_fact():
        """Get random fact"""
        return random.choice(EcoFactsLibrary.FACTS)

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_learning_center():
    """Render the complete learning center"""
    st.markdown("<div class='section-header'>📚 Eco-Education & Learning Center</div>", unsafe_allow_html=True)
    
    # Daily fact
    st.info(f"💡 **Daily Eco-Fact:** {EcoFactsLibrary.get_daily_fact()}")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📖 Courses",
        "🎯 Learning Paths",
        "📝 Quizzes",
        "📚 Resources"
    ])
    
    with tab1:
        render_courses()
    
    with tab2:
        render_learning_paths()
    
    with tab3:
        render_quizzes()
    
    with tab4:
        render_resources()

def render_courses():
    """Render courses"""
    st.markdown("### 📖 Sustainability Courses")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        category_filter = st.selectbox(
            "Category",
            ["All"] + CourseDatabase.get_categories()
        )
    
    with col2:
        level_filter = st.selectbox(
            "Level",
            ["All"] + CourseDatabase.get_levels()
        )
    
    with col3:
        certificate_only = st.checkbox("Certificate Included")
    
    # Get filtered courses
    filters = {}
    if category_filter != "All":
        filters["category"] = category_filter
    if level_filter != "All":
        filters["level"] = level_filter
    if certificate_only:
        filters["certificate_only"] = True
    
    courses = CourseDatabase.get_courses(filters)
    
    # Display courses
    for course in courses:
        with st.container():
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='display: flex; align-items: start; gap: 15px;'>
                    <div style='font-size: 40px;'>{course['emoji']}</div>
                    <div style='flex: 1;'>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div>
                                <h4 style='margin: 0; color: #4ade80;'>{course['title']}</h4>
                                <span style='font-size: 13px; color: #6b7280;'>
                                    {course['category']} • {course['level']} • {course['duration']}
                                </span>
                            </div>
                            <div style='text-align: right;'>
                                <span style='background: {course['color']}20; padding: 4px 12px; border-radius: 20px; color: {course['color']}; font-weight: 700; font-size: 13px;'>
                                    ⭐ {course['rating']}
                                </span>
                                {f'<span style="background: #4ade80; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 12px; margin-left: 8px;">📜 Certificate</span>' if course['certificate'] else ''}
                            </div>
                        </div>
                        <p style='color: #6b7280; font-size: 14px; margin: 8px 0;'>{course['description']}</p>
                        <div style='display: flex; gap: 6px; flex-wrap: wrap;'>
                            {' '.join([f'<span style="background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px;">{topic}</span>' for topic in course['topics'][:3]])}
                        </div>
                        <div style='display: flex; gap: 20px; margin-top: 8px; font-size: 13px; color: #6b7280;'>
                            <span>📚 {course['modules']} modules</span>
                            <span>👨‍🎓 {course['students']:,} students</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button(f"📖 View Course", key=f"view_{course['id']}"):
                    st.session_state.selected_course = course['id']
                    st.rerun()
            
            with col2:
                if st.button(f"📚 Save", key=f"save_{course['id']}"):
                    if "saved_courses" not in st.session_state:
                        st.session_state.saved_courses = []
                    if course['id'] not in st.session_state.saved_courses:
                        st.session_state.saved_courses.append(course['id'])
                        st.success(f"✅ Saved {course['title']} to your library!")
                        st.rerun()
    
    # Show selected course details
    if st.session_state.get("selected_course"):
        course = next((c for c in CourseDatabase.COURSES if c["id"] == st.session_state.selected_course), None)
        if course:
            with st.expander(f"📖 {course['title']} - Course Details", expanded=True):
                st.markdown(f"**Description:** {course['description']}")
                st.markdown(f"**Duration:** {course['duration']}")
                st.markdown(f"**Level:** {course['level']}")
                st.markdown(f"**Modules:** {course['modules']}")
                
                st.markdown("**Topics Covered:**")
                for topic in course['topics']:
                    st.markdown(f"• {topic}")
                
                if course['certificate']:
                    st.success("🎓 This course offers a certificate upon completion!")
                
                if st.button("🔄 Close Course Details"):
                    st.session_state.selected_course = None
                    st.rerun()

def render_learning_paths():
    """Render learning paths"""
    st.markdown("### 🎯 Learning Paths")
    
    st.markdown("""
    <div class='subtitle'>
        Curated learning journeys to build your sustainability knowledge step by step
    </div>
    """, unsafe_allow_html=True)
    
    paths = LearningPaths.get_paths()
    
    for path_id, path in paths.items():
        with st.container():
            difficulty_colors = {
                "Beginner": "#4ade80",
                "Intermediate": "#fbbf24",
                "Advanced": "#f87171"
            }
            color = difficulty_colors.get(path["difficulty"], "#6b7280")
            
            st.markdown(f"""
            <div class='card' style='border-left: 4px solid {color};'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <h4 style='margin: 0; color: #4ade80;'>{path['title']}</h4>
                        <p style='color: #6b7280; font-size: 14px; margin: 4px 0;'>{path['description']}</p>
                        <div style='display: flex; gap: 15px; font-size: 13px; color: #6b7280;'>
                            <span>📚 {len(path['courses'])} courses</span>
                            <span>⏱️ {path['duration']}</span>
                            <span style='color: {color};'>🎯 {path['difficulty']}</span>
                        </div>
                    </div>
                    <div>
                        {f'<span style="background: {color}; padding: 4px 12px; border-radius: 20px; color: #111827; font-weight: 700; font-size: 12px;">In Progress</span>' if path_id in st.session_state.get("learning_paths", []) else ''}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"🚀 Start Path", key=f"path_{path_id}"):
                    if "learning_paths" not in st.session_state:
                        st.session_state.learning_paths = []
                    if path_id not in st.session_state.learning_paths:
                        st.session_state.learning_paths.append(path_id)
                        st.success(f"✅ Started {path['title']}!")
                        st.rerun()
    
    # Progress tracking
    if "learning_paths" in st.session_state and st.session_state.learning_paths:
        st.markdown("---")
        st.markdown("### 📊 Your Learning Progress")
        
        total_paths = len(LearningPaths.get_paths())
        started_paths = len(st.session_state.learning_paths)
        
        col1, col2 = st.columns(2)
        col1.metric("Paths Started", f"{started_paths}/{total_paths}")
        col2.metric("Progress", f"{(started_paths/total_paths*100):.0f}%")
        
        st.progress(started_paths / total_paths)

def render_quizzes():
    """Render eco-quizzes"""
    st.markdown("### 📝 Eco-Quizzes")
    
    # Quiz selection
    quizzes = EcoQuizzes.get_quizzes()
    quiz_options = list(quizzes.keys())
    
    if quiz_options:
        col1, col2 = st.columns([2, 1])
        with col1:
            selected_quiz = st.selectbox(
                "Select Quiz",
                quiz_options,
                format_func=lambda x: quizzes[x]["title"]
            )
        
        with col2:
            if st.button("🔄 Reset Quiz Progress"):
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_"):
                        del st.session_state[key]
                st.rerun()
        
        # Display quiz
        if selected_quiz:
            quiz = quizzes[selected_quiz]
            
            st.markdown(f"""
            <div class='card-highlight'>
                <h4>{quiz['title']}</h4>
                <p style='color: #6b7280;'>{quiz['description']}</p>
                <div style='display: flex; gap: 15px; font-size: 13px; color: #6b7280;'>
                    <span>📂 {quiz['category']}</span>
                    <span>🎯 {quiz['difficulty']}</span>
                    <span>📝 {len(quiz['questions'])} questions</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Quiz logic
            quiz_key = f"quiz_{selected_quiz}_score"
            quiz_answers_key = f"quiz_{selected_quiz}_answers"
            quiz_submitted_key = f"quiz_{selected_quiz}_submitted"
            
            if not st.session_state.get(quiz_submitted_key, False):
                score = 0
                answers = []
                
                for i, q in enumerate(quiz['questions']):
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    answer = st.radio(
                        "Select your answer",
                        q['options'],
                        key=f"quiz_{selected_quiz}_{i}",
                        label_visibility="collapsed"
                    )
                    answers.append(answer)
                
                if st.button("📝 Submit Quiz", type="primary", use_container_width=True):
                    # Calculate score
                    for i, q in enumerate(quiz['questions']):
                        if i < len(answers):
                            if answers[i] == q['options'][q['correct']]:
                                score += 1
                    
                    st.session_state[quiz_key] = score
                    st.session_state[quiz_answers_key] = answers
                    st.session_state[quiz_submitted_key] = True
                    st.rerun()
            else:
                # Show results
                score = st.session_state.get(quiz_key, 0)
                total = len(quiz['questions'])
                percentage = (score / total) * 100
                
                st.markdown("### 🎯 Quiz Results")
                
                if percentage >= 80:
                    st.success(f"🌟 Excellent! You scored {score}/{total} ({percentage:.0f}%)")
                elif percentage >= 60:
                    st.info(f"🌱 Good job! You scored {score}/{total} ({percentage:.0f}%)")
                else:
                    st.warning(f"📚 Keep learning! You scored {score}/{total} ({percentage:.0f}%)")
                
                # Show explanations
                st.markdown("### 📖 Review Your Answers")
                answers = st.session_state.get(quiz_answers_key, [])
                for i, q in enumerate(quiz['questions']):
                    if i < len(answers):
                        user_answer = answers[i]
                        correct_answer = q['options'][q['correct']]
                        is_correct = user_answer == correct_answer
                        
                        st.markdown(f"""
                        <div class='card' style='border-left: 4px solid {'#4ade80' if is_correct else '#f87171'};'>
                            <div>
                                <span style='font-weight: 700;'>{'✅' if is_correct else '❌'} Q{i+1}: {q['question']}</span>
                                <div style='font-size: 14px; color: {'#4ade80' if is_correct else '#f87171'};'>
                                    Your answer: {user_answer}
                                </div>
                                <div style='font-size: 14px; color: #4ade80;'>
                                    Correct answer: {correct_answer}
                                </div>
                                <div style='font-size: 13px; color: #6b7280; margin-top: 4px;'>
                                    💡 {q['explanation']}
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                if st.button("🔄 Retake Quiz", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        if key.startswith(f"quiz_{selected_quiz}"):
                            del st.session_state[key]
                    st.rerun()

def render_resources():
    """Render additional resources"""
    st.markdown("### 📚 Learning Resources")
    
    resources = {
        "Articles": [
            {"title": "10 Easy Ways to Reduce Your Carbon Footprint", "source": "EcoBuddy", "category": "Lifestyle"},
            {"title": "Understanding Carbon Offsetting", "source": "ClimateAction", "category": "Climate"},
            {"title": "Guide to Sustainable Fashion", "source": "GreenLiving", "category": "Lifestyle"},
            {"title": "Renewable Energy 101", "source": "CleanEnergy", "category": "Energy"},
            {"title": "Food Waste Reduction Strategies", "source": "Sustainability", "category": "Food"}
        ],
        "Videos": [
            {"title": "The Story of Stuff", "source": "YouTube", "category": "Basics"},
            {"title": "Our Planet Series", "source": "Netflix", "category": "Biodiversity"},
            {"title": "Before the Flood", "source": "National Geographic", "category": "Climate"},
            {"title": "Kiss the Ground", "source": "Netflix", "category": "Food"},
            {"title": "The True Cost of Fast Fashion", "source": "YouTube", "category": "Lifestyle"}
        ],
        "Books": [
            {"title": "The Uninhabitable Earth", "author": "David Wallace-Wells", "category": "Climate"},
            {"title": "Drawdown", "author": "Paul Hawken", "category": "Solutions"},
            {"title": "Silent Spring", "author": "Rachel Carson", "category": "Biodiversity"},
            {"title": "The Sixth Extinction", "author": "Elizabeth Kolbert", "category": "Biodiversity"},
            {"title": "Sustainable Living", "author": "Emily Smith", "category": "Lifestyle"}
        ],
        "Podcasts": [
            {"title": "Climate Now", "source": "Spotify", "category": "Climate"},
            {"title": "Sustainable Living Podcast", "source": "Apple Podcasts", "category": "Lifestyle"},
            {"title": "The Green Living Hour", "source": "Spotify", "category": "Lifestyle"},
            {"title": "Energy Transition", "source": "Google Podcasts", "category": "Energy"},
            {"title": "Zero Waste Community", "source": "Apple Podcasts", "category": "Waste"}
        ]
    }
    
    # Resource type selector
    resource_types = list(resources.keys())
    selected_type = st.radio("Select Resource Type", resource_types, horizontal=True)
    
    # Display resources
    for resource in resources[selected_type]:
        with st.container():
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <span style='font-weight: 600;'>{resource['title']}</span>
                        <div style='font-size: 13px; color: #6b7280;'>
                            {resource.get('source', '')}{resource.get('author', '')}
                        </div>
                    </div>
                    <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #4ade80;'>
                        {resource['category']}
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# INTEGRATION
# ============================================================

def render_learning_hub():
    """Render the complete learning hub"""
    render_learning_center()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from learning_center import render_learning_hub

# Add as a new tab
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15, tab16 = st.tabs([
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
    "📚 Learning Center"  # NEW
])

with tab11:
    render_learning_hub()
"""