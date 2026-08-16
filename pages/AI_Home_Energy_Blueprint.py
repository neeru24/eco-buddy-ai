import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import energy_audit as ea
from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🏠 AI Home Energy Blueprint</div>", unsafe_allow_html=True)

st.markdown(
    "Describe your home layout or upload a floor plan. "
    "Get room-by-room energy estimates, personalized recommendations, and savings projections."
)

input_mode = st.radio("Choose input method", ["Describe Your Home", "Upload Floor Plan"], horizontal=True)

rooms = []

from session_state_utils import ensure_session_state

ensure_session_state({"blueprint_rooms": []})

if input_mode == "Describe Your Home":
    st.markdown("### 🏡 Add Rooms")

    room_types = list(ea.ROOM_TYPES.keys())

    with st.form("add_room_form", clear_on_submit=True):
        row = st.columns(4)
        room_name = row[0].text_input("Room Name", placeholder="e.g. Master Bedroom")
        room_type = row[1].selectbox("Room Type", room_types)
        area = row[2].number_input("Area (sq ft)", min_value=20, max_value=2000, value=200, step=10)
        devices = row[3].number_input("Device Multiplier", min_value=1, max_value=10, value=1, step=1)

        if st.form_submit_button("➕ Add Room"):
            st.session_state.blueprint_rooms.append({
                'name': room_name or room_type,
                'type': room_type,
                'area_sqft': area,
                'devices': devices,
            })
            st.rerun()

    if st.session_state.blueprint_rooms:
        st.markdown("#### Rooms in your home")
        room_df = pd.DataFrame(st.session_state.blueprint_rooms)
        room_df.columns = ['Name', 'Type', 'Area (sq ft)', 'Devices']
        st.dataframe(room_df, use_container_width=True)

        if st.button("🗑️ Clear All Rooms"):
            st.session_state.blueprint_rooms = []
            st.rerun()

        rooms = st.session_state.blueprint_rooms

else:
    st.markdown("### 📄 Upload Floor Plan")
    uploaded_file = st.file_uploader(
        "Upload a floor plan image (JPG/PNG)", type=['jpg', 'jpeg', 'png']
    )
    if uploaded_file:
        st.image(uploaded_file, caption="Uploaded Floor Plan", use_container_width=True)
        st.info("Floor plan analysis coming soon. For now, please use 'Describe Your Home' to add rooms manually.")

        with st.form("manual_from_floorplan"):
            with st.expander("➕ Add Room", expanded=True):
                row2 = st.columns(4)
                fp_name = row2[0].text_input("Room Name", key="fp_name")
                fp_type = row2[1].selectbox("Room Type", room_types, key="fp_type")
                fp_area = row2[2].number_input("Area (sq ft)", min_value=20, max_value=2000, value=200, step=10, key="fp_area")
                fp_devices = row2[3].number_input("Device Multiplier", min_value=1, max_value=10, value=1, step=1, key="fp_devices")
                if st.form_submit_button("➕ Add Room from Floor Plan"):
                    st.session_state.blueprint_rooms.append({
                        'name': fp_name or fp_type,
                        'type': fp_type,
                        'area_sqft': fp_area,
                        'devices': fp_devices,
                    })
                    st.rerun()

        if 'blueprint_rooms' in st.session_state and st.session_state.blueprint_rooms:
            rooms = st.session_state.blueprint_rooms

st.markdown("---")

if not rooms:
    st.info("👆 Add at least one room to generate your energy blueprint.")
    st.stop()

if st.button("🚀 Generate Energy Blueprint", type="primary"):
    with st.spinner("Analyzing your home layout..."):
        blueprint = ea.estimate_home_blueprint(rooms)

    st.balloons()
    st.markdown("## 📋 Home Energy Blueprint")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Daily Usage", f"{blueprint['total_daily_kwh']} kWh")
    col2.metric("Total Monthly Usage", f"{blueprint['total_monthly_kwh']} kWh")
    col3.metric("Total Yearly Usage", f"{blueprint['total_yearly_kwh']} kWh")

    st.markdown("---")

    for rd in blueprint['rooms']:
        with st.expander(f"{rd['icon']} **{rd['name']}** ({rd['type']}, {rd['area_sqft']} sq ft)", expanded=True):
            u = rd['usage']
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric("Daily", f"{u['daily_kwh']} kWh")
            rc2.metric("Monthly", f"{u['monthly_kwh']} kWh")
            rc3.metric("Yearly", f"{u['yearly_kwh']} kWh")

            st.markdown(f"**Typical appliances:** {', '.join(u['appliances'])}")

            if rd['recommendations']:
                st.markdown("**Recommendations:**")
                for icon, title, desc, savings_pct, _ in rd['recommendations']:
                    st.markdown(f"- {icon} **{title}** — {desc} _(~{savings_pct}% savings)_")

                st.markdown(f"**Potential daily savings:** {rd['potential_savings_kwh']} kWh  "
                            f"({rd['savings_pct']}% reduction)")

    st.markdown("---")
    st.markdown("### 📊 Energy Distribution by Room")

    fig_pie = px.pie(
        names=[rd['name'] for rd in blueprint['rooms']],
        values=[rd['usage']['daily_kwh'] for rd in blueprint['rooms']],
        title="Daily Energy Consumption by Room",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig_pie.update_traces(textposition='inside', textinfo='label+percent')
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_pie, use_container_width=True)

    room_names = [rd['name'] for rd in blueprint['rooms']]
    current_usage = [rd['usage']['daily_kwh'] for rd in blueprint['rooms']]
    potential_usage = [max(0, rd['usage']['daily_kwh'] - rd['potential_savings_kwh'])
                       for rd in blueprint['rooms']]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name='Current Usage', x=room_names, y=current_usage,
        marker_color='#ef4444', marker_line_color='#ef4444'
    ))
    fig_bar.add_trace(go.Bar(
        name='With Improvements', x=room_names, y=potential_usage,
        marker_color='#4ade80', marker_line_color='#4ade80'
    ))
    fig_bar.update_layout(
        title="Current vs Potential Usage (kWh/day)",
        barmode='group', template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title="kWh/day",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 💰 Savings Summary")
    s1, s2, s3 = st.columns(3)
    s1.metric("Daily Savings Potential", f"{blueprint['total_savings_daily_kwh']} kWh")
    s2.metric("Yearly Savings Potential", f"{blueprint['total_savings_yearly_kwh']} kWh")
    s3.metric("Yearly Cost Savings", f"${blueprint['total_savings_yearly_kwh'] * 0.15:,.2f}")

    savings_data = {
        'Room': [rd['name'] for rd in blueprint['rooms']],
        'Type': [rd['type'] for rd in blueprint['rooms']],
        'Area (sq ft)': [rd['area_sqft'] for rd in blueprint['rooms']],
        'Daily kWh': [rd['usage']['daily_kwh'] for rd in blueprint['rooms']],
        'Monthly kWh': [rd['usage']['monthly_kwh'] for rd in blueprint['rooms']],
        'Yearly kWh': [rd['usage']['yearly_kwh'] for rd in blueprint['rooms']],
        'Potential Savings (kWh/day)': [rd['potential_savings_kwh'] for rd in blueprint['rooms']],
    }
    df_export = pd.DataFrame(savings_data)

    st.download_button(
        "📥 Download Blueprint Report (CSV)",
        df_export.to_csv(index=False),
        "home_energy_blueprint.csv",
        "text/csv",
    )

    st.session_state.blueprint_rooms = []
