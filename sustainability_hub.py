# ============================================================
# NEW FEATURE: Carbon Offset Marketplace Simulator
# File: marketplace_enhanced.py
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
from typing import Any

class CarbonOffsetMarketplace:
    """Enhanced carbon offset marketplace with real-time pricing simulation"""
    
    def __init__(self) -> None:
        self.projects = [
            {
                "id": 1,
                "name": "Amazon Rainforest Conservation",
                "category": "Forestry",
                "region": "South America",
                "cost_per_tonne": 12.50,
                "available_capacity": 15000,
                "description": "Protects endangered rainforest from deforestation",
                "image": "🌳",
                "co2_removed": 45000,
                "rating": 4.8,
                "certification": "VCS Verified"
            },
            {
                "id": 2,
                "name": "Solar Energy Initiative",
                "category": "Renewable Energy",
                "region": "Africa",
                "cost_per_tonne": 8.75,
                "available_capacity": 25000,
                "description": "Provides solar panels to rural communities",
                "image": "☀️",
                "co2_removed": 38000,
                "rating": 4.5,
                "certification": "Gold Standard"
            },
            {
                "id": 3,
                "name": "Wind Farm Expansion",
                "category": "Renewable Energy",
                "region": "Europe",
                "cost_per_tonne": 10.20,
                "available_capacity": 20000,
                "description": "Expands offshore wind energy capacity",
                "image": "💨",
                "co2_removed": 52000,
                "rating": 4.7,
                "certification": "VERRA"
            },
            {
                "id": 4,
                "name": "Mangrove Restoration",
                "category": "Blue Carbon",
                "region": "Southeast Asia",
                "cost_per_tonne": 15.00,
                "available_capacity": 8000,
                "description": "Restores critical coastal mangrove ecosystems",
                "image": "🌊",
                "co2_removed": 28000,
                "rating": 4.9,
                "certification": "Plan Vivo"
            },
            {
                "id": 5,
                "name": "Methane Capture",
                "category": "Waste Management",
                "region": "North America",
                "cost_per_tonne": 6.30,
                "available_capacity": 12000,
                "description": "Captures methane from landfills for energy",
                "image": "♻️",
                "co2_removed": 35000,
                "rating": 4.3,
                "certification": "CARB"
            }
        ]
        
    def get_project_by_id(self, project_id: int) -> dict[str, Any] | None:
        """Retrieve project by ID"""
        for project in self.projects:
            if project["id"] == project_id:
                return project
        return None
    
    def calculate_offset_cost(self, tonnes: float, cost_per_tonne: float, quantity_discount: bool = False) -> float:
        """Calculate cost with potential quantity discounts"""
        base_cost = tonnes * cost_per_tonne
        
        if quantity_discount and tonnes >= 100:
            discount = 0.10  # 10% discount for bulk purchases
            return base_cost * (1 - discount)
        elif quantity_discount and tonnes >= 50:
            discount = 0.05  # 5% discount for medium purchases
            return base_cost * (1 - discount)
        
        return base_cost
    
    def get_market_insights(self) -> list[str]:
        """Generate market insights based on current data"""
        insights = []
        
        # Find best value project
        best_value = min(self.projects, key=lambda x: x["cost_per_tonne"])
        insights.append(f"💡 Best value: **{best_value['name']}** at ${best_value['cost_per_tonne']:.2f}/tonne")
        
        # Find highest impact project
        highest_impact = max(self.projects, key=lambda x: x["co2_removed"])
        insights.append(f"🌍 Highest impact: **{highest_impact['name']}** removing {highest_impact['co2_removed']:,} tonnes CO₂")
        
        # Find highest rated project
        highest_rated = max(self.projects, key=lambda x: x["rating"])
        insights.append(f"⭐ Highest rated: **{highest_rated['name']}** ({highest_rated['rating']}/5.0)")
        
        return insights
    
    def get_category_summary(self) -> dict[str, Any]:
        """Get summary statistics by category"""
        categories = {}
        for project in self.projects:
            cat = project["category"]
            if cat not in categories:
                categories[cat] = {
                    "count": 0,
                    "total_capacity": 0,
                    "avg_cost": 0,
                    "total_co2": 0
                }
            categories[cat]["count"] += 1
            categories[cat]["total_capacity"] += project["available_capacity"]
            categories[cat]["total_co2"] += project["co2_removed"]
            
        for cat in categories:
            categories[cat]["avg_cost"] = sum(
                p["cost_per_tonne"] for p in self.projects if p["category"] == cat
            ) / categories[cat]["count"]
            
        return categories

# ============================================================
# NEW FEATURE: Eco-Goals Dashboard
# File: eco_goals.py
# ============================================================

class EcoGoalsManager:
    """Manage and track personalized eco-goals"""
    
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        self.goals = self._load_goals()
    
    def _load_goals(self) -> list[dict[str, Any]]:
        """Load user goals from session state"""
        if "eco_goals" not in st.session_state:
            st.session_state.eco_goals = {}
        return st.session_state.eco_goals.get(self.user_id, [])
    
    def save_goals(self) -> None:
        """Save goals to session state"""
        st.session_state.eco_goals[self.user_id] = self.goals
    
    def create_goal(self, title: str, target: float, category: str, deadline: str) -> dict[str, Any]:
        """Create a new eco-goal"""
        goal = {
            "id": len(self.goals) + 1,
            "title": title,
            "target": target,
            "current_progress": 0,
            "category": category,
            "deadline": deadline,
            "created_at": datetime.now().isoformat(),
            "status": "active",  # active, completed, expired
            "progress_updates": []
        }
        self.goals.append(goal)
        self.save_goals()
        return goal
    
    def update_progress(self, goal_id: int, progress_value: float, note: str = "") -> bool:
        """Update progress for a specific goal"""
        for goal in self.goals:
            if goal["id"] == goal_id:
                goal["current_progress"] = min(progress_value, goal["target"])
                goal["progress_updates"].append({
                    "timestamp": datetime.now().isoformat(),
                    "value": progress_value,
                    "note": note
                })
                if goal["current_progress"] >= goal["target"]:
                    goal["status"] = "completed"
                self.save_goals()
                return True
        return False
    
    def get_goal_stats(self) -> dict[str, Any]:
        """Get statistics about user goals"""
        if not self.goals:
            return {
                "total": 0,
                "completed": 0,
                "active": 0,
                "completion_rate": 0
            }
        
        total = len(self.goals)
        completed = sum(1 for g in self.goals if g["status"] == "completed")
        active = sum(1 for g in self.goals if g["status"] == "active")
        
        return {
            "total": total,
            "completed": completed,
            "active": active,
            "completion_rate": (completed / total * 100) if total > 0 else 0
        }
    
    def generate_suggestion(self) -> tuple[str, str, int, str]:
        """Generate a random eco-goal suggestion"""
        suggestions = [
            ("Reduce monthly electricity usage by 20%", "Energy", 30, "Reduce your electricity consumption through efficiency measures"),
            ("Walk or bike for trips under 3km", "Transportation", 30, "Choose active transportation for short trips"),
            ("Go meat-free for one day per week", "Diet", 52, "Reduce your dietary carbon footprint"),
            ("Take public transport twice a week", "Transportation", 104, "Reduce vehicle emissions by using public transit"),
            ("Reduce shower time by 2 minutes", "Water", 30, "Conserve water and reduce heating energy"),
            ("Plant a tree in your community", "Biodiversity", 1, "Contribute to carbon sequestration"),
            ("Unplug devices when not in use", "Energy", 30, "Reduce phantom power consumption"),
            ("Buy locally sourced food once per week", "Diet", 52, "Reduce food transportation emissions")
        ]
        return random.choice(suggestions)

# ============================================================
# NEW FEATURE: Impact Visualizer
# File: impact_visualizer.py
# ============================================================

class ImpactVisualizer:
    """Visualize environmental impact with engaging graphics"""
    
    @staticmethod
    def calculate_equivalent_impact(footprint_kg: float) -> dict[str, Any]:
        """Calculate equivalencies for carbon footprint"""
        equivalents = {
            "trees_absorbed": footprint_kg / 20,  # Trees absorb ~20kg CO2/year
            "car_km_driven": footprint_kg * 0.12,  # ~0.12kg CO2 per km
            "smartphones_charged": footprint_kg * 146,  # ~0.00685kg per charge
            "lightbulb_hours": footprint_kg * 100,  # LED bulb ~0.01kg per hour
            "meals_produced": footprint_kg / 2.5,  # Average meal ~2.5kg CO2
            "plastic_bottles": footprint_kg * 50  # ~0.02kg CO2 per bottle
        }
        return equivalents
    
    @staticmethod
    def get_water_equivalent(kg_co2: float) -> float:
        """Calculate water footprint equivalent"""
        # Each kg CO2 roughly equals 3-5 liters of water
        return kg_co2 * 4
    
    @staticmethod
    def get_forest_equivalent(kg_co2: float) -> float:
        """Calculate forest area equivalent (sq meters)"""
        # Each kg CO2 requires ~0.5 sq meters of forest
        return kg_co2 * 0.5
    
    @staticmethod
    def render_impact_cards(equivalents: dict[str, Any]) -> None:
        """Render impact equivalency cards"""
        cols = st.columns(3)
        cards = [
            ("🌳 Trees", f"{equivalents['trees_absorbed']:.0f}", "Trees that absorb your annual CO₂"),
            ("🚗 Car Travel", f"{equivalents['car_km_driven']:.0f} km", "Equivalent car emissions"),
            ("💡 Light Bulbs", f"{equivalents['lightbulb_hours']:.0f} hours", "LED bulbs powered"),
            ("🍽️ Meals", f"{equivalents['meals_produced']:.0f}", "Meals produced"),
            ("📱 Phone Charges", f"{equivalents['smartphones_charged']:.0f}", "Smartphone charges"),
            ("💧 Water", f"{ImpactVisualizer.get_water_equivalent(equivalents['trees_absorbed']):.0f} L", "Water footprint")
        ]
        
        for i, (icon, value, label) in enumerate(cards):
            with cols[i % 3]:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='font-size: 28px;'>{icon}</div>
                    <div style='font-size: 24px; font-weight: 700; color: #4ade80;'>{value}</div>
                    <div style='font-size: 12px; color: #6b7280;'>{label}</div>
                </div>
                """, unsafe_allow_html=True)

    @staticmethod
    def render_eco_clock(eco_score: float) -> None:
        """Render an eco-clock visualization"""
        import math
        
        # Calculate angle from score
        angle = (eco_score / 100) * 180  # 0-100 maps to 0-180 degrees
        
        # Determine color based on score
        if eco_score >= 75:
            color = "#4ade80"
            label = "Excellent"
        elif eco_score >= 50:
            color = "#fbbf24"
            label = "Good"
        else:
            color = "#f87171"
            label = "Needs Work"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px;'>
            <div style='position: relative; width: 200px; height: 120px; margin: 0 auto;'>
                <div style='position: absolute; width: 200px; height: 100px; background: #1f2937; border-radius: 100px 100px 0 0; overflow: hidden;'>
                    <div style='position: absolute; width: 100%; height: 100%; transform: rotate({angle}deg); transform-origin: bottom center; background: linear-gradient(90deg, #4ade80, #fbbf24, #f87171);'></div>
                </div>
                <div style='position: absolute; width: 180px; height: 90px; background: #111827; border-radius: 90px 90px 0 0; top: 5px; left: 10px;'></div>
                <div style='position: absolute; width: 60px; height: 60px; background: #4ade80; border-radius: 50%; top: 45px; left: 70px; display: flex; align-items: center; justify-content: center;'>
                    <span style='color: #111827; font-weight: 800; font-size: 18px;'>{eco_score}</span>
                </div>
            </div>
            <div style='margin-top: 10px; font-size: 18px; font-weight: 700; color: {color};'>{label}</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# NEW FEATURE: Green Investment Calculator
# File: green_investment.py
# ============================================================

class GreenInvestmentCalculator:
    """Calculate potential savings and returns from green investments"""
    
    @staticmethod
    def calculate_solar_roi(roof_area: float, panel_efficiency: float, sun_hours: float, cost_per_watt: float = 3.50) -> dict[str, float]:
        """
        Calculate ROI for solar panel investment
        Returns: dict with financial metrics
        """
        # Calculate system size (kW)
        system_size = (roof_area * panel_efficiency / 100) * 0.85  # 85% efficiency factor
        
        # Annual generation (kWh)
        annual_generation = system_size * sun_hours * 365 * 0.9  # 90% performance factor
        
        # Installation cost
        installation_cost = system_size * 1000 * cost_per_watt
        
        # Annual savings (assuming $0.15/kWh)
        annual_savings = annual_generation * 0.15
        
        # Simple payback period
        if annual_savings > 0:
            payback_years = installation_cost / annual_savings
        else:
            payback_years = float('inf')
        
        # 25-year net savings
        total_savings_25yr = annual_savings * 25
        net_savings_25yr = total_savings_25yr - installation_cost
        
        # Carbon offset (kg CO2/year)
        carbon_offset = annual_generation * 0.4  # 0.4 kg CO2 per kWh
        
        return {
            "system_size_kw": system_size,
            "annual_generation_kwh": annual_generation,
            "installation_cost": installation_cost,
            "annual_savings": annual_savings,
            "payback_years": payback_years,
            "net_savings_25yr": net_savings_25yr,
            "carbon_offset_kg": carbon_offset,
            "trees_equivalent": carbon_offset / 20  # Trees absorb ~20kg CO2/year
        }
    
    @staticmethod
    def calculate_ev_savings(annual_miles: float, current_mpg: float = 25, electricity_cost: float = 0.15) -> dict[str, float]:
        """
        Calculate savings from switching to electric vehicle
        """
        # Current fuel costs (assuming $3.50/gallon)
        fuel_cost = (annual_miles / current_mpg) * 3.50
        
        # EV electricity costs (assuming 3 miles/kWh)
        ev_electricity_cost = (annual_miles / 3) * electricity_cost
        
        # Maintenance savings (EVs have ~50% lower maintenance)
        maintenance_savings = 300  # Estimated annual savings
        
        # Total annual savings
        annual_savings = fuel_cost - ev_electricity_cost + maintenance_savings
        
        # Carbon reduction (assuming 0.4 kg CO2/mile for gas, 0 for EV)
        carbon_reduction = annual_miles * 0.4
        
        return {
            "annual_savings": annual_savings,
            "fuel_cost": fuel_cost,
            "ev_cost": ev_electricity_cost,
            "maintenance_savings": maintenance_savings,
            "carbon_reduction_kg": carbon_reduction,
            "trees_equivalent": carbon_reduction / 20
        }
    
    @staticmethod
    def render_calculator() -> None:
        """Render the green investment calculator interface"""
        st.markdown("### 💰 Green Investment Calculator")
        
        calc_type = st.selectbox(
            "Select Calculation Type",
            ["Solar Panel ROI", "EV Savings Calculator"]
        )
        
        if calc_type == "Solar Panel ROI":
            col1, col2 = st.columns(2)
            
            with col1:
                roof_area = st.number_input("Available Roof Area (m²)", min_value=1, value=30)
                panel_efficiency = st.slider("Panel Efficiency (%)", 10, 30, 20, 5)
                
            with col2:
                sun_hours = st.number_input("Peak Sun Hours/Day", min_value=1.0, max_value=8.0, value=4.5, step=0.5)
                cost_per_watt = st.number_input("Cost per Watt ($)", min_value=1.0, max_value=6.0, value=3.50, step=0.25)
            
            if st.button("Calculate Solar ROI"):
                results = GreenInvestmentCalculator.calculate_solar_roi(
                    roof_area, panel_efficiency, sun_hours, cost_per_watt
                )
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("System Size", f"{results['system_size_kw']:.1f} kW")
                col2.metric("Annual Generation", f"{results['annual_generation_kwh']:,.0f} kWh")
                col3.metric("Installation Cost", f"${results['installation_cost']:,.2f}")
                col4.metric("Payback Period", f"{results['payback_years']:.1f} years")
                
                col1, col2 = st.columns(2)
                col1.metric("25-Year Net Savings", f"${results['net_savings_25yr']:,.2f}")
                col2.metric("Carbon Offset", f"{results['carbon_offset_kg']:,.0f} kg/year")
                
                st.info(f"🌳 Equivalent to planting **{results['trees_equivalent']:.0f}** trees per year!")
        
        else:  # EV Savings Calculator
            col1, col2 = st.columns(2)
            
            with col1:
                annual_miles = st.number_input("Annual Miles Driven", min_value=1000, value=12000, step=1000)
                current_mpg = st.number_input("Current Vehicle MPG", min_value=5, value=25, step=1)
                
            with col2:
                electricity_cost = st.number_input("Electricity Cost ($/kWh)", min_value=0.05, max_value=0.50, value=0.15, step=0.01)
            
            if st.button("Calculate EV Savings"):
                results = GreenInvestmentCalculator.calculate_ev_savings(
                    annual_miles, current_mpg, electricity_cost
                )
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Annual Savings", f"${results['annual_savings']:,.2f}")
                col2.metric("Fuel Cost Savings", f"${results['fuel_cost'] - results['ev_cost']:,.2f}")
                col3.metric("Carbon Reduction", f"{results['carbon_reduction_kg']:,.0f} kg/year")
                
                st.info(f"🌳 Equivalent to planting **{results['trees_equivalent']:.0f}** trees per year!")

# ============================================================
# NEW FEATURE: Sustainability Quiz
# File: sustainability_quiz.py
# ============================================================

class SustainabilityQuiz:
    """Interactive quiz to test environmental knowledge"""
    
    QUESTIONS = [
        {
            "question": "What is the average carbon footprint per person globally?",
            "options": ["2,000 kg CO₂/year", "4,800 kg CO₂/year", "10,000 kg CO₂/year", "1,000 kg CO₂/year"],
            "correct": 1,
            "explanation": "The global average is approximately 4,800 kg CO₂ per person per year, though this varies significantly by country."
        },
        {
            "question": "Which transportation mode has the lowest carbon footprint per passenger km?",
            "options": ["Car", "Plane", "Train", "Bus"],
            "correct": 2,
            "explanation": "Trains are generally the most efficient mode of transport, producing significantly less CO₂ per passenger kilometer than cars or planes."
        },
        {
            "question": "What is the most effective way to reduce individual carbon footprint?",
            "options": ["Recycling", "Eating less meat", "Flying less", "All of the above"],
            "correct": 3,
            "explanation": "A combination of behavioral changes is most effective. Reducing air travel, adopting plant-based diets, and recycling all contribute to lower emissions."
        },
        {
            "question": "How much CO₂ does a single tree absorb in a year?",
            "options": ["5 kg", "22 kg", "50 kg", "100 kg"],
            "correct": 1,
            "explanation": "A mature tree can absorb approximately 22 kg of CO₂ per year, depending on the species and conditions."
        },
        {
            "question": "What percentage of global greenhouse gas emissions comes from food production?",
            "options": ["10%", "15%", "25%", "40%"],
            "correct": 2,
            "explanation": "Food production accounts for approximately 25% of global greenhouse gas emissions, with meat and dairy production being significant contributors."
        },
        {
            "question": "Which renewable energy source produces the most electricity globally?",
            "options": ["Solar", "Wind", "Hydro", "Geothermal"],
            "correct": 2,
            "explanation": "Hydropower is the largest source of renewable electricity globally, followed by wind and solar."
        },
        {
            "question": "What is 'Blue Carbon'?",
            "options": ["Carbon stored in the ocean", "Carbon from blue industries", "Carbon offsets purchased online", "Carbon from water pollution"],
            "correct": 0,
            "explanation": "Blue carbon refers to carbon captured and stored by marine ecosystems like mangroves, seagrasses, and tidal marshes."
        }
    ]
    
    @staticmethod
    def run_quiz() -> None:
        """Run the sustainability quiz"""
        st.markdown("### 📝 Sustainability Quiz")
        st.markdown("Test your environmental knowledge!")
        
        if "quiz_score" not in st.session_state:
            st.session_state.quiz_score = 0
            st.session_state.quiz_answers = []
            st.session_state.quiz_completed = False
        
        if not st.session_state.quiz_completed:
            score = 0
            answers = []
            
            for i, q in enumerate(SustainabilityQuiz.QUESTIONS):
                st.markdown(f"**Q{i+1}: {q['question']}**")
                options = q['options']
                answer = st.radio(
                    f"Select your answer for Q{i+1}",
                    options,
                    key=f"quiz_q_{i}",
                    label_visibility="collapsed"
                )
                
                if st.button(f"Check Answer {i+1}", key=f"check_{i}"):
                    correct_index = q['correct']
                    is_correct = options.index(answer) == correct_index
                    if is_correct:
                        st.success("✅ Correct! " + q['explanation'])
                    else:
                        st.error("❌ Incorrect. " + q['explanation'])
                st.markdown("---")
            
            if st.button("Submit Quiz", type="primary"):
                score = 0
                for i, q in enumerate(SustainabilityQuiz.QUESTIONS):
                    if f"quiz_q_{i}" in st.session_state:
                        answer = st.session_state[f"quiz_q_{i}"]
                        if answer == q['options'][q['correct']]:
                            score += 1
                
                st.session_state.quiz_score = score
                st.session_state.quiz_answers = answers
                st.session_state.quiz_completed = True
                st.rerun()
        else:
            score = st.session_state.quiz_score
            total = len(SustainabilityQuiz.QUESTIONS)
            percentage = (score / total) * 100
            
            st.markdown("### 🎯 Quiz Results")
            
            if percentage >= 80:
                st.success(f"🌟 Excellent! You scored {score}/{total} ({percentage:.0f}%) - You're an Eco Champion!")
            elif percentage >= 60:
                st.info(f"🌱 Good job! You scored {score}/{total} ({percentage:.0f}%) - You're Eco Conscious!")
            else:
                st.warning(f"📚 You scored {score}/{total} ({percentage:.0f}%) - Keep learning about sustainability!")
            
            if st.button("Retake Quiz"):
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_"):
                        del st.session_state[key]
                st.rerun()

# ============================================================
# INTEGRATION: Add to main app
# ============================================================

def render_sustainability_hub() -> None:
    """Render the complete sustainability hub"""
    st.markdown("<div class='section-header'>🌿 Sustainability Hub</div>", unsafe_allow_html=True)
    
    hub_tabs = st.tabs([
        "🎯 Eco Goals",
        "📊 Impact Visualizer",
        "💰 Green Investments",
        "📝 Quiz"
    ])
    
    with hub_tabs[0]:
        render_eco_goals()
    
    with hub_tabs[1]:
        render_impact_visualizer()
    
    with hub_tabs[2]:
        GreenInvestmentCalculator.render_calculator()
    
    with hub_tabs[3]:
        SustainabilityQuiz.run_quiz()

def render_eco_goals() -> None:
    """Render the eco-goals interface"""
    st.markdown("### 🎯 Your Eco Goals")
    
    goals_manager = EcoGoalsManager(st.session_state.get('user_id', 1))
    stats = goals_manager.get_goal_stats()
    
    # Display statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Goals", stats['total'])
    col2.metric("Completed", stats['completed'])
    col3.metric("Active", stats['active'])
    col4.metric("Completion Rate", f"{stats['completion_rate']:.0f}%")
    
    st.progress(stats['completion_rate'] / 100)
    
    # Create new goal
    with st.expander("➕ Create New Goal"):
        with st.form("new_goal_form"):
            title = st.text_input("Goal Title", placeholder="e.g., Reduce electricity usage by 20%")
            category = st.selectbox("Category", ["Energy", "Transportation", "Diet", "Water", "Biodiversity", "Waste"])
            target = st.number_input("Target Value", min_value=1, value=30)
            deadline = st.date_input("Deadline", min_value=datetime.now().date())
            
            if st.form_submit_button("Create Goal"):
                goals_manager.create_goal(title, target, category, deadline.isoformat())
                st.success("✅ Goal created successfully!")
                st.rerun()
    
    # Display existing goals
    goals = goals_manager.goals
    if goals:
        for goal in goals:
            with st.container():
                status_emoji = "✅" if goal['status'] == 'completed' else "📋" if goal['status'] == 'active' else "⏰"
                progress_pct = (goal['current_progress'] / goal['target']) * 100 if goal['target'] > 0 else 0
                
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-size: 20px;'>{status_emoji}</span>
                            <span style='font-weight: 700; font-size: 16px;'>{goal['title']}</span>
                        </div>
                        <span style='font-size: 14px; color: #6b7280;'>{goal['category']} • Deadline: {goal['deadline'][:10]}</span>
                    </div>
                    <div style='margin-top: 10px;'>
                        <div style='display: flex; justify-content: space-between; font-size: 14px;'>
                            <span>Progress</span>
                            <span>{goal['current_progress']:.0f}/{goal['target']}</span>
                        </div>
                        <div class='progress-bar' style='height: 8px;'>
                            <div class='progress-fill' style='width: {min(progress_pct, 100)}%;'></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_progress = st.number_input(
                        f"Update Progress for {goal['id']}",
                        min_value=0.0,
                        max_value=float(goal['target']),
                        value=float(goal['current_progress']),
                        step=1.0,
                        key=f"progress_{goal['id']}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    if st.button("Update", key=f"update_{goal['id']}"):
                        goals_manager.update_progress(goal['id'], new_progress)
                        st.rerun()
    else:
        st.info("No goals set yet. Create your first eco-goal above!")
    
    # Get suggestion
    if st.button("💡 Get Goal Suggestion"):
        suggestion = goals_manager.generate_suggestion()
        st.info(f"🎯 Suggested Goal: **{suggestion[0]}** ({suggestion[1]})")

def render_impact_visualizer() -> None:
    """Render the impact visualizer interface"""
    st.markdown("### 🌍 Visualize Your Impact")
    
    # Get user's latest footprint
    history = get_assessments(st.session_state.get('user_id', 1))
    if history:
        latest_footprint = history[0][7]
        
        equivalents = ImpactVisualizer.calculate_equivalent_impact(latest_footprint)
        ImpactVisualizer.render_impact_cards(equivalents)
        
        # Render eco clock
        eco_score = history[0][8]
        ImpactVisualizer.render_eco_clock(eco_score)
        
        # Additional visualizations
        st.markdown("---")
        st.markdown("### 📊 Impact Breakdown")
        
        # Create a simple donut chart of impact categories
        fig = go.Figure(data=[go.Pie(
            labels=['Transportation', 'Electricity', 'Diet', 'Flights'],
            values=[30, 25, 20, 25],
            hole=0.4,
            marker=dict(colors=['#4ade80', '#60a5fa', '#fbbf24', '#f87171'])
        )])
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=0, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Complete an assessment to visualize your environmental impact!")

# ============================================================
# ADD TO MAIN APP - Place this in the main navigation
# ============================================================

def add_sustainability_hub() -> None:
    """Add Sustainability Hub to main app navigation"""
    # Add this as a new tab in the main app
    pass

# ============================================================
# SAMPLE INTEGRATION CODE
# ============================================================

# To integrate into the main app, add the following code where you want the hub to appear:

"""
# Add this after the existing tabs or as a new section:

# Sustainability Hub
with st.expander("🌿 Sustainability Hub", expanded=False):
    render_sustainability_hub()

# Or add as a new tab:
# tab7, tab8 = st.tabs(["...", "🌿 Sustainability Hub"])
# with tab8:
#     render_sustainability_hub()
"""

# ============================================================
# COMPATIBILITY WITH EXISTING CODE
# ============================================================

# This code is designed to work with the existing EcoBuddy codebase.
# It uses the same session state management, database functions,
# and styling conventions as the original application.

# To use the new features, simply import and call the functions
# from your main app file.

print("✅ EcoBuddy Sustainability Hub loaded successfully!")
print("🌱 New features available: Eco Goals, Impact Visualizer, Green Investments, Quiz")