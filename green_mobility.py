
# ============================================================
# FILE: green_mobility.py
# EcoBuddy AI+ Green Mobility & Sustainable Transportation
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random
import math
import json

# ============================================================
# TRANSPORTATION DATA
# ============================================================

class TransportationData:
    """Transportation modes and emission factors"""
    
    MODES = {
        "Walking": {
            "emission_factor": 0,
            "co2_per_km": 0,
            "cost_per_km": 0,
            "speed": 5,
            "health_benefit": 10,
            "emoji": "🚶"
        },
        "Cycling": {
            "emission_factor": 0,
            "co2_per_km": 0,
            "cost_per_km": 0.01,
            "speed": 15,
            "health_benefit": 8,
            "emoji": "🚲"
        },
        "Public Transit": {
            "emission_factor": 0.04,
            "co2_per_km": 0.04,
            "cost_per_km": 0.15,
            "speed": 25,
            "health_benefit": 2,
            "emoji": "🚌"
        },
        "Electric Car": {
            "emission_factor": 0.05,
            "co2_per_km": 0.05,
            "cost_per_km": 0.08,
            "speed": 45,
            "health_benefit": 0,
            "emoji": "⚡"
        },
        "Hybrid Car": {
            "emission_factor": 0.12,
            "co2_per_km": 0.12,
            "cost_per_km": 0.12,
            "speed": 45,
            "health_benefit": 0,
            "emoji": "🔋"
        },
        "Gas Car": {
            "emission_factor": 0.21,
            "co2_per_km": 0.21,
            "cost_per_km": 0.15,
            "speed": 50,
            "health_benefit": 0,
            "emoji": "🚗"
        },
        "Carpool": {
            "emission_factor": 0.07,
            "co2_per_km": 0.07,
            "cost_per_km": 0.10,
            "speed": 45,
            "health_benefit": 1,
            "emoji": "👥"
        },
        "Electric Scooter": {
            "emission_factor": 0.02,
            "co2_per_km": 0.02,
            "cost_per_km": 0.05,
            "speed": 20,
            "health_benefit": 2,
            "emoji": "🛴"
        },
        "Train": {
            "emission_factor": 0.03,
            "co2_per_km": 0.03,
            "cost_per_km": 0.20,
            "speed": 80,
            "health_benefit": 1,
            "emoji": "🚆"
        },
        "Ferry": {
            "emission_factor": 0.15,
            "co2_per_km": 0.15,
            "cost_per_km": 0.25,
            "speed": 30,
            "health_benefit": 0,
            "emoji": "⛴️"
        }
    }
    
    @staticmethod
    def get_modes():
        """Get all transportation modes"""
        return TransportationData.MODES
    
    @staticmethod
    def get_mode(mode_name):
        """Get specific mode data"""
        return TransportationData.MODES.get(mode_name)

# ============================================================
# TRIP PLANNER
# ============================================================

class TripPlanner:
    """Plan and compare sustainable trips"""
    
    @staticmethod
    def plan_trip(distance_km, modes=None):
        """Plan a trip with multiple modes"""
        if modes is None:
            modes = list(TransportationData.MODES.keys())
        
        results = []
        for mode in modes:
            data = TransportationData.get_mode(mode)
            if data:
                time_hours = distance_km / data["speed"] if data["speed"] > 0 else 0
                co2 = distance_km * data["co2_per_km"]
                cost = distance_km * data["cost_per_km"]
                
                # Calculate environmental score (0-100)
                env_score = 100 - (co2 / 20 * 100) if co2 > 0 else 100
                env_score = max(0, min(100, env_score))
                
                results.append({
                    "mode": mode,
                    "emoji": data["emoji"],
                    "time": time_hours,
                    "time_minutes": time_hours * 60,
                    "co2": co2,
                    "cost": cost,
                    "env_score": env_score,
                    "health_benefit": data["health_benefit"]
                })
        
        # Sort by environmental score
        return sorted(results, key=lambda x: x["env_score"], reverse=True)
    
    @staticmethod
    def calculate_savings(current_mode, proposed_mode, distance_km):
        """Calculate savings between modes"""
        current = TransportationData.get_mode(current_mode)
        proposed = TransportationData.get_mode(proposed_mode)
        
        if not current or not proposed:
            return None
        
        current_co2 = distance_km * current["co2_per_km"]
        proposed_co2 = distance_km * proposed["co2_per_km"]
        
        co2_saved = current_co2 - proposed_co2
        money_saved = (distance_km * current["cost_per_km"]) - (distance_km * proposed["cost_per_km"])
        
        return {
            "co2_saved_kg": co2_saved,
            "money_saved": money_saved,
            "trees_equivalent": co2_saved / 22,
            "percentage_reduction": ((co2_saved / current_co2) * 100) if current_co2 > 0 else 0
        }

# ============================================================
# MOBILITY TRACKER
# ============================================================

class MobilityTracker:
    """Track user mobility habits"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.data = self._load_data()
    
    def _load_data(self):
        """Load mobility data from session"""
        if "mobility_data" not in st.session_state:
            st.session_state.mobility_data = {}
        return st.session_state.mobility_data.get(self.user_id, {
            "trips": [],
            "total_distance": 0,
            "total_co2": 0,
            "weekly_trips": {},
            "preferred_mode": None,
            "streak_days": 0
        })
    
    def save(self):
        """Save mobility data"""
        st.session_state.mobility_data[self.user_id] = self.data
    
    def add_trip(self, mode, distance_km, date=None):
        """Add a trip record"""
        if date is None:
            date = datetime.now()
        
        data = TransportationData.get_mode(mode)
        if not data:
            return False
        
        co2 = distance_km * data["co2_per_km"]
        
        trip = {
            "mode": mode,
            "distance": distance_km,
            "co2": co2,
            "date": date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.data["trips"].append(trip)
        self.data["total_distance"] += distance_km
        self.data["total_co2"] += co2
        
        # Update weekly stats
        week = date.strftime("%Y-W%W")
        if week not in self.data["weekly_trips"]:
            self.data["weekly_trips"][week] = {"trips": 0, "distance": 0, "co2": 0}
        self.data["weekly_trips"][week]["trips"] += 1
        self.data["weekly_trips"][week]["distance"] += distance_km
        self.data["weekly_trips"][week]["co2"] += co2
        
        self.save()
        return True
    
    def get_stats(self):
        """Get mobility statistics"""
        return {
            "total_trips": len(self.data["trips"]),
            "total_distance": self.data["total_distance"],
            "total_co2": self.data["total_co2"],
            "weekly_stats": self.data["weekly_trips"],
            "streak_days": self.data["streak_days"]
        }
    
    def get_carbon_savings(self):
        """Calculate carbon savings from sustainable choices"""
        total_emissions = self.data["total_co2"]
        
        # Calculate savings by comparing to car
        car_emissions = 0
        for trip in self.data["trips"]:
            mode = trip["mode"]
            data = TransportationData.get_mode(mode)
            if data:
                car_co2 = trip["distance"] * 0.21  # Gas car factor
                car_emissions += car_co2
        
        saved = max(0, car_emissions - total_emissions)
        
        return {
            "total_saved_kg": saved,
            "trees_equivalent": saved / 22,
            "percentage_reduction": ((saved / car_emissions) * 100) if car_emissions > 0 else 0
        }

# ============================================================
# EV CALCULATOR
# ============================================================

class EVCalculator:
    """Electric vs Gas vehicle comparison"""
    
    @staticmethod
    def compare_vehicles(daily_km, gas_mpg=25, ev_efficiency=4, gas_price=3.50, electricity_price=0.15):
        """Compare EV and gas vehicle costs and emissions"""
        
        # Annual calculations
        annual_km = daily_km * 365
        
        # Gas vehicle
        gas_gallons = annual_km / (gas_mpg * 1.609)  # Convert km to miles
        gas_cost = gas_gallons * gas_price
        gas_co2 = annual_km * 0.21  # kg CO2 per km
        
        # EV
        ev_kwh = annual_km / ev_efficiency
        ev_cost = ev_kwh * electricity_price
        ev_co2 = annual_km * 0.05  # kg CO2 per km
        
        # Savings
        co2_saved = gas_co2 - ev_co2
        money_saved = gas_cost - ev_cost
        
        return {
            "gas": {
                "annual_cost": gas_cost,
                "annual_co2": gas_co2,
                "monthly_cost": gas_cost / 12,
                "monthly_co2": gas_co2 / 12
            },
            "ev": {
                "annual_cost": ev_cost,
                "annual_co2": ev_co2,
                "monthly_cost": ev_cost / 12,
                "monthly_co2": ev_co2 / 12
            },
            "savings": {
                "money": money_saved,
                "co2": co2_saved,
                "money_5_years": money_saved * 5,
                "co2_5_years": co2_saved * 5,
                "trees_equivalent": co2_saved / 22
            }
        }

# ============================================================
# CAR SHARING NETWORK
# ============================================================

class CarSharingNetwork:
    """Community car sharing platform"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.network = self._load_network()
    
    def _load_network(self):
        """Load car sharing network from session"""
        if "car_sharing" not in st.session_state:
            st.session_state.car_sharing = {
                "vehicles": [],
                "bookings": [],
                "members": {}
            }
        return st.session_state.car_sharing
    
    def save(self):
        """Save car sharing network"""
        st.session_state.car_sharing = self.network
    
    def add_vehicle(self, owner, model, type, capacity, location, price_per_day):
        """Add a vehicle to sharing network"""
        vehicle = {
            "id": len(self.network["vehicles"]) + 1,
            "owner": owner,
            "model": model,
            "type": type,
            "capacity": capacity,
            "location": location,
            "price_per_day": price_per_day,
            "available": True,
            "added": datetime.now().isoformat(),
            "total_bookings": 0
        }
        self.network["vehicles"].append(vehicle)
        self.save()
        return vehicle
    
    def book_vehicle(self, vehicle_id, renter, start_date, end_date):
        """Book a vehicle"""
        vehicle = next((v for v in self.network["vehicles"] if v["id"] == vehicle_id), None)
        if not vehicle or not vehicle["available"]:
            return False, "Vehicle not available"
        
        booking = {
            "id": len(self.network["bookings"]) + 1,
            "vehicle_id": vehicle_id,
            "renter": renter,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "booked_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.network["bookings"].append(booking)
        vehicle["available"] = False
        vehicle["total_bookings"] += 1
        
        # Add to member bookings
        if renter not in self.network["members"]:
            self.network["members"][renter] = {"bookings": []}
        self.network["members"][renter]["bookings"].append(booking["id"])
        
        self.save()
        return True, "Vehicle booked successfully!"
    
    def return_vehicle(self, vehicle_id):
        """Return a vehicle"""
        vehicle = next((v for v in self.network["vehicles"] if v["id"] == vehicle_id), None)
        if vehicle:
            vehicle["available"] = True
            # Close active booking
            booking = next((b for b in self.network["bookings"] if b["vehicle_id"] == vehicle_id and b["status"] == "active"), None)
            if booking:
                booking["status"] = "completed"
            self.save()
            return True
        return False
    
    def get_stats(self):
        """Get car sharing statistics"""
        return {
            "total_vehicles": len(self.network["vehicles"]),
            "available_vehicles": sum(1 for v in self.network["vehicles"] if v["available"]),
            "total_bookings": len(self.network["bookings"]),
            "active_bookings": sum(1 for b in self.network["bookings"] if b["status"] == "active")
        }

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_green_mobility():
    """Render the complete green mobility hub"""
    st.markdown("<div class='section-header'>🚗 Green Mobility & Sustainable Transportation</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize components
    if "mobility_tracker" not in st.session_state:
        st.session_state.mobility_tracker = MobilityTracker(user_id)
    if "car_sharing" not in st.session_state:
        st.session_state.car_sharing = CarSharingNetwork(user_id)
    
    tracker = st.session_state.mobility_tracker
    car_sharing = st.session_state.car_sharing
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Trip Planner",
        "📊 Mobility Tracker",
        "⚡ EV Calculator",
        "🚗 Car Sharing",
        "📈 Dashboard"
    ])
    
    with tab1:
        render_trip_planner()
    
    with tab2:
        render_mobility_tracker(tracker)
    
    with tab3:
        render_ev_calculator()
    
    with tab4:
        render_car_sharing(car_sharing)
    
    with tab5:
        render_mobility_dashboard(tracker)

def render_trip_planner():
    """Render trip planner"""
    st.markdown("### 🗺️ Sustainable Trip Planner")
    
    st.markdown("""
    <div class='subtitle'>
        Plan your trip and compare sustainable transportation options
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        distance = st.number_input("Trip Distance (km)", min_value=0.5, value=10.0, step=0.5)
    
    with col2:
        selected_modes = st.multiselect(
            "Select Modes to Compare",
            list(TransportationData.MODES.keys()),
            default=["Walking", "Cycling", "Public Transit", "Electric Car", "Gas Car"]
        )
    
    if st.button("🌿 Plan Trip", type="primary", use_container_width=True):
        if selected_modes:
            results = TripPlanner.plan_trip(distance, selected_modes)
            
            st.markdown("#### 📊 Trip Options")
            
            # Create comparison table
            df = pd.DataFrame(results)
            df_display = df[["emoji", "mode", "time_minutes", "co2", "cost", "env_score"]]
            df_display.columns = ["", "Mode", "Time (min)", "CO₂ (kg)", "Cost ($)", "Eco Score"]
            df_display["Eco Score"] = df_display["Eco Score"].apply(lambda x: f"{x:.0f}%")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            # Best option highlight
            best = results[0]
            st.markdown(f"""
            <div class='card-highlight'>
                <div style='display: flex; align-items: center; gap: 15px;'>
                    <div style='font-size: 40px;'>🏆</div>
                    <div>
                        <div style='font-weight: 700; font-size: 18px;'>Best Option: {best['emoji']} {best['mode']}</div>
                        <div style='color: #6b7280;'>
                            🕐 {best['time_minutes']:.0f} min • 🌍 {best['co2']:.2f} kg CO₂ • 💰 ${best['cost']:.2f}
                        </div>
                        <div style='color: #4ade80;'>Eco Score: {best['env_score']:.0f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Visual comparison
            st.markdown("#### 📊 Emissions Comparison")
            
            fig = go.Figure()
            for result in results:
                fig.add_trace(go.Bar(
                    x=[result["mode"]],
                    y=[result["co2"]],
                    name=result["mode"],
                    marker_color='#4ade80' if result["mode"] == best["mode"] else '#6b7280'
                ))
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=20, b=0),
                yaxis_title="CO₂ Emissions (kg)"
            )
            st.plotly_chart(fig, use_container_width=True)

def render_mobility_tracker(tracker):
    """Render mobility tracker"""
    st.markdown("### 📊 Track Your Mobility")
    
    # Add trip form
    with st.expander("➕ Add Trip Record", expanded=False):
        with st.form("add_trip_form"):
            col1, col2 = st.columns(2)
            with col1:
                mode = st.selectbox("Transportation Mode", list(TransportationData.MODES.keys()))
                distance = st.number_input("Distance (km)", min_value=0.1, value=5.0, step=0.5)
            with col2:
                date = st.date_input("Date", datetime.now())
            
            if st.form_submit_button("Add Trip"):
                if tracker.add_trip(mode, distance, datetime.combine(date, datetime.min.time())):
                    st.success("✅ Trip recorded successfully!")
                    st.rerun()
                else:
                    st.error("Failed to record trip")
    
    # Statistics
    stats = tracker.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Trips", stats["total_trips"])
    col2.metric("Total Distance", f"{stats['total_distance']:.1f} km")
    col3.metric("Total CO₂", f"{stats['total_co2']:.1f} kg")
    col4.metric("Weekly Trips", len([k for k in stats["weekly_stats"].keys() if k.startswith(datetime.now().strftime("%Y-W%W"))]))
    
    # Carbon savings
    savings = tracker.get_carbon_savings()
    
    st.markdown("#### 🌍 Carbon Savings")
    col1, col2 = st.columns(2)
    col1.metric("CO₂ Saved", f"{savings['total_saved_kg']:.1f} kg")
    col2.metric("Trees Equivalent", f"{savings['trees_equivalent']:.1f}")
    
    st.progress(min(savings['percentage_reduction'] / 100, 1.0))
    
    # Weekly trend
    st.markdown("#### 📈 Weekly Trend")
    
    weeks = sorted(stats["weekly_stats"].keys())[-6:]
    weekly_data = []
    for week in weeks:
        weekly_data.append({
            "Week": week,
            "Distance": stats["weekly_stats"][week]["distance"],
            "CO₂": stats["weekly_stats"][week]["co2"]
        })
    
    if weekly_data:
        df_weekly = pd.DataFrame(weekly_data)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_weekly["Week"],
            y=df_weekly["Distance"],
            mode='lines+markers',
            name='Distance (km)',
            line=dict(color='#4ade80', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=df_weekly["Week"],
            y=df_weekly["CO₂"],
            mode='lines+markers',
            name='CO₂ (kg)',
            line=dict(color='#f87171', width=2)
        ))
        fig.update_layout(
            height=250,
            margin=dict(l=0, r=0, t=20, b=0),
            yaxis_title="Value"
        )
        st.plotly_chart(fig, use_container_width=True)

def render_ev_calculator():
    """Render EV calculator"""
    st.markdown("### ⚡ Electric Vehicle Calculator")
    
    st.markdown("""
    <div class='subtitle'>
        Compare the costs and emissions of Electric vs Gas vehicles
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        daily_km = st.number_input("Daily Distance (km)", min_value=10, value=50, step=10)
        gas_mpg = st.number_input("Gas Vehicle MPG", min_value=10, value=25, step=1)
        gas_price = st.number_input("Gas Price ($/gallon)", min_value=2.0, value=3.50, step=0.25)
    
    with col2:
        ev_efficiency = st.number_input("EV Efficiency (km/kWh)", min_value=2.0, value=4.0, step=0.5)
        electricity_price = st.number_input("Electricity Price ($/kWh)", min_value=0.05, value=0.15, step=0.01)
    
    if st.button("📊 Compare Vehicles", type="primary", use_container_width=True):
        results = EVCalculator.compare_vehicles(daily_km, gas_mpg, ev_efficiency, gas_price, electricity_price)
        
        st.markdown("#### 📊 Comparison Results")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Annual Cost - Gas", f"${results['gas']['annual_cost']:.2f}")
        col2.metric("Annual Cost - EV", f"${results['ev']['annual_cost']:.2f}")
        col3.metric("Annual Savings", f"${results['savings']['money']:.2f}")
        
        # Emissions comparison
        col1, col2, col3 = st.columns(3)
        col1.metric("Annual CO₂ - Gas", f"{results['gas']['annual_co2']:.0f} kg")
        col2.metric("Annual CO₂ - EV", f"{results['ev']['annual_co2']:.0f} kg")
        col3.metric("CO₂ Saved", f"{results['savings']['co2']:.0f} kg")
        
        # 5 year savings
        st.markdown("#### 📈 5-Year Projection")
        
        col1, col2 = st.columns(2)
        col1.metric("5-Year Money Saved", f"${results['savings']['money_5_years']:.2f}")
        col2.metric("5-Year CO₂ Saved", f"{results['savings']['co2_5_years']:.0f} kg")
        
        st.progress(min(results['savings']['co2'] / 5000, 1.0))
        st.caption(f"🌳 Equivalent to planting {results['savings']['trees_equivalent']:.1f} trees per year")

def render_car_sharing(car_sharing):
    """Render car sharing network"""
    st.markdown("### 🚗 Community Car Sharing Network")
    
    stats = car_sharing.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Vehicles", stats["total_vehicles"])
    col2.metric("Available", stats["available_vehicles"])
    col3.metric("Total Bookings", stats["total_bookings"])
    col4.metric("Active Bookings", stats["active_bookings"])
    
    st.markdown("---")
    
    # List vehicles
    st.markdown("#### 🚗 Available Vehicles")
    
    available_vehicles = [v for v in car_sharing.network["vehicles"] if v["available"]]
    
    if available_vehicles:
        for vehicle in available_vehicles:
            st.markdown(f"""
            <div class='card'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <div>
                        <div style='font-weight: 600;'>🚗 {vehicle['model']}</div>
                        <div style='font-size: 13px; color: #6b7280;'>
                            {vehicle['type']} • Capacity: {vehicle['capacity']} • Location: {vehicle['location']}
                        </div>
                        <div style='font-size: 12px; color: #4ade80;'>👤 Owner: {vehicle['owner']}</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-weight: 700; color: #4ade80;'>${vehicle['price_per_day']}/day</div>
                        <span style='background: #4ade80; padding: 2px 10px; border-radius: 12px; font-size: 11px; color: #111827;'>
                            Available
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(f"📅 Book", key=f"book_{vehicle['id']}"):
                    st.session_state.booking_vehicle = vehicle['id']
                    st.rerun()
            
            if st.session_state.get("booking_vehicle") == vehicle["id"]:
                with st.expander("Book Vehicle", expanded=True):
                    start_date = st.date_input("Start Date", datetime.now(), key=f"start_{vehicle['id']}")
                    end_date = st.date_input("End Date", datetime.now() + timedelta(days=1), key=f"end_{vehicle['id']}")
                    
                    if st.button("Confirm Booking", key=f"confirm_{vehicle['id']}"):
                        success, message = car_sharing.book_vehicle(
                            vehicle["id"],
                            st.session_state.get("username", "User"),
                            start_date,
                            end_date
                        )
                        if success:
                            st.success(message)
                            st.session_state.booking_vehicle = None
                            st.rerun()
                        else:
                            st.error(message)
    else:
        st.info("🚗 No vehicles currently available for sharing")
    
    # Add vehicle form
    st.markdown("---")
    st.markdown("#### ➕ Share Your Vehicle")
    
    with st.form("add_vehicle_form"):
        col1, col2 = st.columns(2)
        with col1:
            model = st.text_input("Vehicle Model")
            vehicle_type = st.selectbox("Vehicle Type", ["Sedan", "SUV", "Truck", "Van", "Electric", "Hybrid"])
        with col2:
            capacity = st.number_input("Passenger Capacity", min_value=1, value=4)
            location = st.text_input("Location")
            price_per_day = st.number_input("Price per Day ($)", min_value=10, value=50, step=5)
        
        if st.form_submit_button("Share Vehicle"):
            if model and location:
                car_sharing.add_vehicle(
                    st.session_state.get("username", "User"),
                    model, vehicle_type, capacity, location, price_per_day
                )
                st.success("✅ Vehicle added to sharing network!")
                st.rerun()
            else:
                st.warning("Please fill in all fields")

def render_mobility_dashboard(tracker):
    """Render mobility dashboard"""
    st.markdown("### 📈 Sustainable Mobility Dashboard")
    
    stats = tracker.get_stats()
    savings = tracker.get_carbon_savings()
    
    # Overall score
    transport_score = min(100, (savings['percentage_reduction'] * 1.5) + 20)
    
    st.markdown("#### 🏆 Mobility Sustainability Score")
    st.progress(transport_score / 100)
    st.caption(f"{transport_score:.0f}/100 - { 'Excellent' if transport_score > 80 else 'Good' if transport_score > 60 else 'Developing' }")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Distance", f"{stats['total_distance']:.1f} km")
    col2.metric("Total CO₂", f"{stats['total_co2']:.1f} kg")
    col3.metric("CO₂ Saved", f"{savings['total_saved_kg']:.1f} kg")
    col4.metric("Trees Equivalent", f"{savings['trees_equivalent']:.1f}")
    
    # Mode distribution
    st.markdown("#### 📊 Mode Distribution")
    
    mode_counts = {}
    for trip in tracker.data["trips"]:
        mode = trip["mode"]
        mode_counts[mode] = mode_counts.get(mode, 0) + 1
    
    if mode_counts:
        fig = go.Figure(data=[go.Pie(
            labels=list(mode_counts.keys()),
            values=list(mode_counts.values()),
            hole=0.3,
            marker=dict(colors=['#4ade80', '#fbbf24', '#60a5fa', '#a78bfa', '#f87171'])
        )])
        fig.update_layout(height=250, margin=dict(l=0, r=0, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No trips recorded yet")
    
    # Recommendations
    st.markdown("#### 💡 Recommendations")
    
    if stats["total_trips"] > 0:
        # Find most used mode
        if mode_counts:
            most_used = max(mode_counts.items(), key=lambda x: x[1])
            if most_used[0] in ["Gas Car", "Hybrid Car"]:
                st.info("🚲 Consider switching to public transit or cycling for short trips")
            elif most_used[0] in ["Walking", "Cycling"]:
                st.success("🌟 Great job using active transportation!")
            elif most_used[0] in ["Public Transit"]:
                st.success("🌿 Good choice using public transportation!")
    else:
        st.info("📊 Start tracking your trips to get personalized recommendations")

# ============================================================
# INTEGRATION
# ============================================================

def render_mobility_hub():
    """Render the complete mobility hub"""
    render_green_mobility()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from green_mobility import render_mobility_hub

# Add as a new tab
with tab38:
    render_mobility_hub()
"""