

# ============================================================
# FILE: event_calendar.py
# EcoBuddy AI+ Eco-Event Calendar & Action Planner
# ============================================================

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import json
import calendar as cal

# ============================================================
# EVENT DATABASE
# ============================================================

class EventDatabase:
    """Database of sustainability events"""
    
    EVENTS = [
        {
            "id": "e1",
            "title": "🌿 Community Cleanup Drive",
            "description": "Join us for a community park cleanup. All supplies provided.",
            "category": "Cleanup",
            "event_type": "In-Person",
            "start_date": datetime.now() + timedelta(days=5),
            "end_date": datetime.now() + timedelta(days=5, hours=3),
            "location": "Central Park",
            "max_participants": 30,
            "registered": 12,
            "is_public": True,
            "organizer": "Green Community",
            "image": "🌳"
        },
        {
            "id": "e2",
            "title": "♻️ Zero Waste Workshop",
            "description": "Learn practical tips to reduce waste in your daily life.",
            "category": "Workshop",
            "event_type": "Virtual",
            "start_date": datetime.now() + timedelta(days=2),
            "end_date": datetime.now() + timedelta(days=2, hours=2),
            "location": "Online",
            "max_participants": 100,
            "registered": 45,
            "is_public": True,
            "organizer": "Eco Foundation",
            "image": "♻️"
        },
        {
            "id": "e3",
            "title": "🌱 Urban Gardening Workshop",
            "description": "Learn how to start your own urban garden.",
            "category": "Workshop",
            "event_type": "Hybrid",
            "start_date": datetime.now() + timedelta(days=7),
            "end_date": datetime.now() + timedelta(days=7, hours=4),
            "location": "Community Garden",
            "max_participants": 25,
            "registered": 8,
            "is_public": True,
            "organizer": "Garden Initiative",
            "image": "🌱"
        },
        {
            "id": "e4",
            "title": "☀️ Solar Energy Webinar",
            "description": "Understanding solar energy and how to get it for your home.",
            "category": "Webinar",
            "event_type": "Virtual",
            "start_date": datetime.now() + timedelta(days=10),
            "end_date": datetime.now() + timedelta(days=10, hours=1.5),
            "location": "Online",
            "max_participants": 200,
            "registered": 78,
            "is_public": True,
            "organizer": "Solar Alliance",
            "image": "☀️"
        },
        {
            "id": "e5",
            "title": "🤝 Eco Volunteer Day",
            "description": "Volunteer at local environmental organizations.",
            "category": "Volunteer",
            "event_type": "In-Person",
            "start_date": datetime.now() + timedelta(days=14),
            "end_date": datetime.now() + timedelta(days=14, hours=5),
            "location": "Various Locations",
            "max_participants": 50,
            "registered": 20,
            "is_public": True,
            "organizer": "Volunteer Network",
            "image": "🤝"
        },
        {
            "id": "e6",
            "title": "🌍 Climate Action Meetup",
            "description": "Connect with climate advocates in your community.",
            "category": "Social",
            "event_type": "Hybrid",
            "start_date": datetime.now() + timedelta(days=12),
            "end_date": datetime.now() + timedelta(days=12, hours=3),
            "location": "Community Center",
            "max_participants": 40,
            "registered": 15,
            "is_public": True,
            "organizer": "Climate Action Group",
            "image": "🌍"
        }
    ]
    
    @staticmethod
    def get_events(category=None, event_type=None):
        """Get events with filters"""
        events = EventDatabase.EVENTS.copy()
        if category and category != "All":
            events = [e for e in events if e["category"] == category]
        if event_type and event_type != "All":
            events = [e for e in events if e["event_type"] == event_type]
        return sorted(events, key=lambda x: x["start_date"])
    
    @staticmethod
    def get_categories():
        """Get event categories"""
        return ["All"] + sorted(set(e["category"] for e in EventDatabase.EVENTS))
    
    @staticmethod
    def get_event_by_id(event_id):
        """Get event by ID"""
        for event in EventDatabase.EVENTS:
            if event["id"] == event_id:
                return event
        return None
    
    @staticmethod
    def get_upcoming_events(days=30):
        """Get upcoming events"""
        cutoff = datetime.now() + timedelta(days=days)
        return [e for e in EventDatabase.EVENTS if e["start_date"] <= cutoff and e["start_date"] >= datetime.now()]

# ============================================================
# ACTION PLAN MANAGER
# ============================================================

class ActionPlanManager:
    """Manage user action plans"""
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.plans = self._load_plans()
    
    def _load_plans(self):
        """Load plans from session"""
        if "action_plans" not in st.session_state:
            st.session_state.action_plans = {}
        return st.session_state.action_plans.get(self.user_id, [])
    
    def save(self):
        """Save plans"""
        st.session_state.action_plans[self.user_id] = self.plans
    
    def create_plan(self, title, goal, deadline):
        """Create a new action plan"""
        plan = {
            "id": len(self.plans) + 1,
            "title": title,
            "goal": goal,
            "deadline": deadline.isoformat(),
            "actions": [],
            "status": "Active",
            "progress": 0,
            "created_at": datetime.now().isoformat()
        }
        self.plans.append(plan)
        self.save()
        return plan
    
    def add_action(self, plan_id, action_text):
        """Add an action to a plan"""
        for plan in self.plans:
            if plan["id"] == plan_id:
                action = {
                    "id": len(plan["actions"]) + 1,
                    "text": action_text,
                    "completed": False
                }
                plan["actions"].append(action)
                self._update_progress(plan)
                self.save()
                return True
        return False
    
    def complete_action(self, plan_id, action_id):
        """Mark an action as completed"""
        for plan in self.plans:
            if plan["id"] == plan_id:
                for action in plan["actions"]:
                    if action["id"] == action_id:
                        action["completed"] = True
                        self._update_progress(plan)
                        self.save()
                        return True
        return False
    
    def _update_progress(self, plan):
        """Update plan progress"""
        if plan["actions"]:
            completed = sum(1 for a in plan["actions"] if a["completed"])
            plan["progress"] = (completed / len(plan["actions"])) * 100
            if plan["progress"] == 100:
                plan["status"] = "Completed"
        else:
            plan["progress"] = 0

# ============================================================
# RENDER FUNCTIONS
# ============================================================

def render_event_calendar():
    """Render the complete event calendar"""
    st.markdown("<div class='section-header'>📅 Eco-Event Calendar & Action Planner</div>", unsafe_allow_html=True)
    
    user_id = st.session_state.get("user_id", 1)
    
    # Initialize action manager
    if "action_manager" not in st.session_state:
        st.session_state.action_manager = ActionPlanManager(user_id)
    
    manager = st.session_state.action_manager
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📅 Events",
        "📝 Action Plans",
        "📊 Calendar View",
        "➕ Create Event"
    ])
    
    with tab1:
        render_events()
    
    with tab2:
        render_action_plans(manager)
    
    with tab3:
        render_calendar_view()
    
    with tab4:
        render_create_event()

def render_events():
    """Render events section"""
    st.markdown("### 📅 Upcoming Events")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        categories = EventDatabase.get_categories()
        selected_category = st.selectbox("Category", categories)
    
    with col2:
        event_types = ["All"] + sorted(set(e["event_type"] for e in EventDatabase.EVENTS))
        selected_type = st.selectbox("Event Type", event_types)
    
    # Get events
    events = EventDatabase.get_events(selected_category, selected_type)
    
    # Search
    search = st.text_input("🔍 Search Events", placeholder="Search by title or location...")
    if search:
        events = [e for e in events if search.lower() in e["title"].lower() or search.lower() in e["location"].lower()]
    
    # Display events
    for event in events:
        days_until = (event["start_date"] - datetime.now()).days
        
        availability_color = "#4ade80" if event["registered"] < event["max_participants"] * 0.7 else "#fbbf24" if event["registered"] < event["max_participants"] * 0.9 else "#f87171"
        
        st.markdown(f"""
        <div class='card-highlight'>
            <div style='display: flex; align-items: start; gap: 15px;'>
                <div style='font-size: 40px;'>{event['image']}</div>
                <div style='flex: 1;'>
                    <div style='display: flex; justify-content: space-between; align-items: start;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{event['title']}</h4>
                            <div style='display: flex; gap: 15px; flex-wrap: wrap; font-size: 12px; color: #6b7280;'>
                                <span>📂 {event['category']}</span>
                                <span>📍 {event['event_type']}</span>
                                <span>🏷️ {event['organizer']}</span>
                                <span>📅 {event['start_date'].strftime('%B %d, %Y')}</span>
                                <span>⏰ {event['start_date'].strftime('%I:%M %p')}</span>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {availability_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827; font-weight: 700;'>
                                {event['registered']}/{event['max_participants']}
                            </span>
                            <div style='font-size: 11px; color: #6b7280;'>Registered</div>
                        </div>
                    </div>
                    <p style='color: #6b7280; font-size: 14px; margin: 6px 0;'>{event['description']}</p>
                    <div style='display: flex; gap: 10px; font-size: 13px;'>
                        <span>📍 {event['location']}</span>
                        <span>⏱️ {days_until} days until event</span>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        with col1:
            if event["registered"] < event["max_participants"]:
                if st.button(f"📝 Register", key=f"register_{event['id']}"):
                    st.success(f"✅ Registered for {event['title']}!")
                    event["registered"] += 1
                    st.rerun()
            else:
                st.button("🔴 Full", key=f"full_{event['id']}", disabled=True)
        
        with col2:
            if st.button("📅 Add to Calendar", key=f"add_{event['id']}"):
                st.success("✅ Added to your calendar!")
        
        st.markdown("---")

def render_action_plans(manager):
    """Render action plans section"""
    st.markdown("### 📝 Action Plans")
    
    # Create new plan
    with st.expander("➕ Create New Action Plan", expanded=False):
        with st.form("action_plan_form"):
            plan_title = st.text_input("Plan Title", placeholder="e.g., Reduce Carbon Footprint")
            plan_goal = st.text_area("Goal Description", placeholder="What do you want to achieve?")
            plan_deadline = st.date_input("Deadline", datetime.now() + timedelta(days=30))
            
            if st.form_submit_button("Create Plan"):
                if plan_title and plan_goal:
                    manager.create_plan(plan_title, plan_goal, plan_deadline)
                    st.success("✅ Action plan created!")
                    st.rerun()
                else:
                    st.warning("Please fill in all fields")
    
    # Display plans
    if manager.plans:
        for plan in manager.plans:
            with st.container():
                status_color = "#4ade80" if plan["status"] == "Completed" else "#fbbf24"
                
                st.markdown(f"""
                <div class='card' style='border-left: 4px solid {status_color};'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <h4 style='margin: 0; color: #4ade80;'>{plan['title']}</h4>
                            <div style='font-size: 13px; color: #6b7280;'>{plan['goal']}</div>
                            <div style='display: flex; gap: 15px; font-size: 12px; color: #6b7280; margin-top: 4px;'>
                                <span>📅 Deadline: {datetime.fromisoformat(plan['deadline']).strftime('%B %d, %Y')}</span>
                                <span>📊 Progress: {plan['progress']:.0f}%</span>
                                <span>📝 {len(plan['actions'])} actions</span>
                            </div>
                        </div>
                        <div style='text-align: right;'>
                            <span style='background: {status_color}; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #111827; font-weight: 700;'>
                                {plan['status']}
                            </span>
                        </div>
                    </div>
                    <div style='margin-top: 8px;'>
                        <div class='progress-bar' style='height: 6px;'>
                            <div class='progress-fill' style='width: {plan['progress']}%;'></div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Actions
                if st.button(f"📋 Manage Actions", key=f"actions_{plan['id']}"):
                    st.session_state.selected_plan = plan["id"]
                    st.rerun()
                
                if st.session_state.get("selected_plan") == plan["id"]:
                    with st.expander("Manage Actions", expanded=True):
                        # Add action
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            new_action = st.text_input("Add action step", key=f"new_action_{plan['id']}")
                        with col2:
                            if st.button("Add", key=f"add_action_{plan['id']}"):
                                if new_action:
                                    manager.add_action(plan["id"], new_action)
                                    st.rerun()
                        
                        # Display actions
                        for action in plan["actions"]:
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                status = "✅" if action["completed"] else "⬜"
                                st.markdown(f"{status} {action['text']}")
                            with col2:
                                if not action["completed"]:
                                    if st.button("Complete", key=f"complete_{plan['id']}_{action['id']}"):
                                        manager.complete_action(plan["id"], action["id"])
                                        st.rerun()
    else:
        st.info("📝 No action plans yet. Create your first plan above!")

def render_calendar_view():
    """Render calendar view"""
    st.markdown("### 📊 Calendar Overview")
    
    # Get upcoming events
    events = EventDatabase.get_upcoming_events(30)
    
    # Create calendar data
    calendar_data = []
    for event in events:
        calendar_data.append({
            "date": event["start_date"].date(),
            "title": event["title"],
            "type": event["category"],
            "event_type": event["event_type"]
        })
    
    if calendar_data:
        df = pd.DataFrame(calendar_data)
        df["date"] = pd.to_datetime(df["date"])
        
        # Count events by date
        event_counts = df.groupby("date").size().reset_index(name="count")
        
        # Create heatmap
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=event_counts["date"],
            y=event_counts["count"],
            marker_color="#4ade80",
            text=event_counts["count"],
            textposition="auto"
        ))
        fig.update_layout(
            title="Events by Date",
            height=300,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis_title="Date",
            yaxis_title="Number of Events"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Upcoming events list
        st.markdown("#### 📅 Upcoming Events (Next 7 Days)")
        
        upcoming = [e for e in events if (e["start_date"] - datetime.now()).days <= 7]
        
        if upcoming:
            for event in upcoming[:5]:
                days = (event["start_date"] - datetime.now()).days
                st.markdown(f"""
                <div class='card'>
                    <div style='display: flex; justify-content: space-between; align-items: center;'>
                        <div>
                            <span style='font-weight: 600;'>{event['image']} {event['title']}</span>
                            <div style='font-size: 13px; color: #6b7280;'>
                                {event['start_date'].strftime('%B %d, %Y • %I:%M %p')}
                            </div>
                        </div>
                        <span style='background: #1f2937; padding: 2px 10px; border-radius: 12px; font-size: 12px; color: #4ade80;'>
                            {days} days away
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No upcoming events in the next 7 days")
        
        # Monthly calendar
        st.markdown("#### 📅 Monthly Calendar")
        
        today = datetime.now()
        year = today.year
        month = today.month
        
        # Create calendar grid
        cal_month = cal.monthcalendar(year, month)
        
        col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
        
        # Headers
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days):
            with locals()[f"col{i+1}"]:
                st.markdown(f"<div style='text-align: center; font-weight: 700; color: #4ade80;'>{day}</div>", unsafe_allow_html=True)
        
        # Calendar days
        for week in cal_month:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day != 0:
                        # Check if there's an event on this day
                        date_obj = datetime(year, month, day)
                        has_event = any(e["start_date"].date() == date_obj.date() for e in events)
                        
                        if has_event:
                            st.markdown(f"<div style='text-align: center; background: #4ade80; border-radius: 50%; color: #111827; font-weight: 700; padding: 4px;'>{day}</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='text-align: center; color: #6b7280;'>{day}</div>", unsafe_allow_html=True)
    else:
        st.info("📅 No events scheduled for the next 30 days")

def render_create_event():
    """Render create event form"""
    st.markdown("### ➕ Create Community Event")
    
    st.markdown("""
    <div class='subtitle'>
        Share your sustainability event with the community
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("create_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Event Title", placeholder="e.g., Community Cleanup")
            category = st.selectbox("Category", ["Cleanup", "Workshop", "Webinar", "Volunteer", "Social", "Other"])
            event_type = st.selectbox("Event Type", ["Virtual", "In-Person", "Hybrid"])
            location = st.text_input("Location", placeholder="Address or Online link")
        
        with col2:
            start_date = st.date_input("Start Date", datetime.now() + timedelta(days=7))
            start_time = st.time_input("Start Time", datetime.now().replace(hour=10, minute=0))
            end_time = st.time_input("End Time", datetime.now().replace(hour=12, minute=0))
            max_participants = st.number_input("Maximum Participants", min_value=1, value=20)
        
        description = st.text_area("Event Description", placeholder="Describe your event...")
        is_public = st.checkbox("Make this event public", value=True)
        
        if st.form_submit_button("Create Event", use_container_width=True):
            if title and description and location:
                # Create event (in production, save to database)
                st.success("✅ Event created successfully! It will be reviewed and published shortly.")
                st.balloons()
                st.info("📢 Your event is now visible to the community.")
            else:
                st.warning("Please fill in all required fields")

# ============================================================
# INTEGRATION
# ============================================================

def render_event_hub():
    """Render the complete event hub"""
    render_event_calendar()

# ============================================================
# SAMPLE USAGE
# ============================================================

"""
# Add to app.py:

# Import
from event_calendar import render_event_hub

# Add as a new tab
with tab28:
    render_event_hub()
"""