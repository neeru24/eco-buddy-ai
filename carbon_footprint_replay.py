"""
Carbon Footprint Replay Module (#332).

Provides historical data aggregation, milestone detection, animated replay state management,
and GIF export functionality for carbon emission progress visualization over time.
"""

import io
import datetime
from typing import List, Dict, Any, Tuple
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from database import get_assessments


def aggregate_historical_emissions(user_id: int = 1, period: str = "weekly") -> pd.DataFrame:
    """
    Fetch historical assessment data for a user and aggregate it chronologically by week or month.
    
    Args:
        user_id: ID of the target user.
        period: "weekly" or "monthly" grouping.
        
    Returns:
        pd.DataFrame: Aggregated historical timeline dataframe with columns:
                      ['period', 'date_label', 'footprint', 'eco_score', 'distance', 'electricity', 'flights', 'count']
    """
    raw_data = get_assessments(user_id=user_id)
    
    records = []
    if raw_data:
        for row in raw_data:
            # get_assessments tuple: id, date, created_at, transport, distance, electricity, diet, flights, footprint, eco_score
            rec_id = row[0]
            date_str = row[1] if row[1] else row[2]
            distance = row[4] or 0.0
            electricity = row[5] or 0.0
            flights = row[7] or 0
            footprint = row[8] or 0.0
            eco_score = row[9] or 0
            
            try:
                dt = pd.to_datetime(date_str)
            except Exception:
                dt = pd.Timestamp.now()
                
            records.append({
                "id": rec_id,
                "timestamp": dt,
                "footprint": footprint,
                "eco_score": eco_score,
                "distance": distance,
                "electricity": electricity,
                "flights": flights,
            })
            
    # If no records exist or data is minimal, construct baseline historical data for preview
    if len(records) < 2:
        now = pd.Timestamp.now()
        base_dates = [now - pd.Timedelta(weeks=i) for i in range(8, 0, -1)]
        sample_footprints = [450.0, 420.0, 390.0, 410.0, 340.0, 310.0, 280.0, 250.0]
        sample_scores = [55, 60, 64, 62, 73, 78, 85, 90]
        sample_dist = [120.0, 110.0, 95.0, 105.0, 80.0, 70.0, 60.0, 50.0]
        sample_elec = [320.0, 300.0, 280.0, 290.0, 240.0, 220.0, 200.0, 180.0]
        
        for idx, dt in enumerate(base_dates):
            records.append({
                "id": idx + 1,
                "timestamp": dt,
                "footprint": sample_footprints[idx],
                "eco_score": sample_scores[idx],
                "distance": sample_dist[idx],
                "electricity": sample_elec[idx],
                "flights": 1 if idx in [0, 3] else 0,
            })
            
    df = pd.DataFrame(records)
    df = df.sort_values(by="timestamp").reset_index(drop=True)
    
    if period == "weekly":
        df["period_key"] = df["timestamp"].dt.to_period("W").astype(str)
        df["date_label"] = df["timestamp"].dt.strftime("Week of %b %d, %Y")
    else:
        df["period_key"] = df["timestamp"].dt.to_period("M").astype(str)
        df["date_label"] = df["timestamp"].dt.strftime("%B %Y")
        
    grouped = df.groupby(["period_key", "date_label"]).agg(
        footprint=("footprint", "mean"),
        eco_score=("eco_score", "mean"),
        distance=("distance", "sum"),
        electricity=("electricity", "sum"),
        flights=("flights", "sum"),
        count=("id", "count")
    ).reset_index()
    
    # Sort chronologically by period_key
    grouped = grouped.sort_values(by="period_key").reset_index(drop=True)
    return grouped


def detect_milestones(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Identify key milestones and achievements across historical replay periods.
    
    Args:
        df: Aggregated historical timeline dataframe.
        
    Returns:
        List[Dict[str, Any]]: List of milestones with period_idx, title, description, badge.
    """
    milestones = []
    if df.empty:
        return milestones
        
    min_footprint_idx = df["footprint"].idxmin()
    max_score_idx = df["eco_score"].idxmax()
    
    # Lowest Footprint Milestone
    milestones.append({
        "period_idx": int(min_footprint_idx),
        "title": "🌱 All-Time Low Emissions",
        "description": f"Achieved lowest emission record of {df.loc[min_footprint_idx, 'footprint']:.1f} kg CO2!",
        "badge": "Green Champion",
        "date_label": df.loc[min_footprint_idx, "date_label"],
    })
    
    # Highest Eco Score Milestone
    milestones.append({
        "period_idx": int(max_score_idx),
        "title": "🏆 Peak Eco Score",
        "description": f"Reached highest Eco Score rating of {int(df.loc[max_score_idx, 'eco_score'])}/100!",
        "badge": "Sustainability Elite",
        "date_label": df.loc[max_score_idx, "date_label"],
    })
    
    # Biggest Reduction Milestone between consecutive periods
    if len(df) > 1:
        df["fp_diff"] = df["footprint"].diff()
        biggest_drop_idx = df["fp_diff"].idxmin()
        if not pd.isna(biggest_drop_idx) and df.loc[biggest_drop_idx, "fp_diff"] < 0:
            drop_amount = abs(df.loc[biggest_drop_idx, "fp_diff"])
            pct_drop = (drop_amount / df.loc[biggest_drop_idx - 1, "footprint"]) * 100
            milestones.append({
                "period_idx": int(biggest_drop_idx),
                "title": "⚡ Biggest Emission Cut",
                "description": f"Reduced emissions by {drop_amount:.1f} kg CO2 ({pct_drop:.1f}%) in a single period!",
                "badge": "Carbon Cutter",
                "date_label": df.loc[biggest_drop_idx, "date_label"],
            })
            
    return milestones


def export_replay_gif(df: pd.DataFrame) -> bytes:
    """
    Generate an animated GIF replay visualizing emission changes over historical periods.
    
    Args:
        df: Aggregated historical timeline dataframe.
        
    Returns:
        bytes: Animated GIF binary buffer.
    """
    images: List[Image.Image] = []
    width, height = 600, 400
    
    max_fp = df["footprint"].max() * 1.2 if not df.empty else 500.0
    
    for i, row in df.iterrows():
        img = Image.new("RGB", (width, height), color=(245, 247, 250))
        draw = ImageDraw.Draw(img)
        
        # Header banner
        draw.rectangle([0, 0, width, 60], fill=(46, 125, 50))
        draw.text((20, 18), "EcoBuddy - Carbon Footprint Replay", fill=(255, 255, 255))
        
        # Period & Date
        draw.text((20, 80), f"Period {i+1}/{len(df)}: {row['date_label']}", fill=(33, 33, 33))
        
        # Key Stats
        draw.rectangle([20, 110, 280, 190], fill=(232, 245, 233), outline=(76, 175, 80), width=2)
        draw.text((35, 125), "Carbon Footprint:", fill=(51, 51, 51))
        draw.text((35, 150), f"{row['footprint']:.1f} kg CO2", fill=(46, 125, 50))
        
        draw.rectangle([300, 110, 560, 190], fill=(227, 242, 253), outline=(33, 150, 243), width=2)
        draw.text((315, 125), "Eco Score:", fill=(51, 51, 51))
        draw.text((315, 150), f"{int(row['eco_score'])} / 100", fill=(21, 101, 192))
        
        # Bar Chart Frame
        chart_top = 220
        chart_bottom = 350
        chart_left = 60
        chart_right = 540
        
        draw.line([(chart_left, chart_bottom), (chart_right, chart_bottom)], fill=(189, 189, 189), width=2)
        
        num_bars = len(df)
        bar_step = (chart_right - chart_left) / max(num_bars, 1)
        bar_width = max(10, bar_step * 0.6)
        
        for idx in range(i + 1):
            curr_row = df.iloc[idx]
            x_center = chart_left + (idx + 0.5) * bar_step
            bar_h = (curr_row["footprint"] / max_fp) * (chart_bottom - chart_top)
            
            bar_color = (76, 175, 80) if idx == i else (165, 214, 167)
            draw.rectangle(
                [x_center - bar_width / 2, chart_bottom - bar_h, x_center + bar_width / 2, chart_bottom],
                fill=bar_color
            )
            
        images.append(img)
        
    buffer = io.BytesIO()
    if images:
        images[0].save(
            buffer,
            format="GIF",
            save_all=True,
            append_images=images[1:],
            duration=800,
            loop=0
        )
    return buffer.getvalue()


def render_carbon_footprint_replay(user_id: int = 1) -> None:
    """
    Render the Carbon Footprint Replay interactive visualization component in Streamlit.
    """
    st.title("🎬 Carbon Footprint Replay")
    st.markdown(
        "Watch an animated replay showing how your carbon emissions and sustainability score "
        "have evolved over time across weeks or months."
    )
    
    col_config1, col_config2 = st.columns([2, 1])
    with col_config1:
        period_option = st.selectbox(
            "Timeframe Granularity",
            ["weekly", "monthly"],
            format_func=lambda x: "Weekly Replay" if x == "weekly" else "Monthly Replay"
        )
    
    df_history = aggregate_historical_emissions(user_id=user_id, period=period_option)
    milestones = detect_milestones(df_history)
    
    if df_history.empty:
        st.warning("No historical data available to generate a replay.")
        return
        
    st.subheader("📊 Historical Emission Timeline")
    
    # Replay Controls
    total_frames = len(df_history)
    if "replay_frame" not in st.session_state:
        st.session_state.replay_frame = total_frames - 1
        
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1, 2])
    with col_ctrl1:
        if st.button("⏮️ Start Over"):
            st.session_state.replay_frame = 0
            st.rerun()
    with col_ctrl2:
        if st.button("▶️ Next Step"):
            st.session_state.replay_frame = min(st.session_state.replay_frame + 1, total_frames - 1)
            st.rerun()
            
    with col_ctrl3:
        current_frame = st.slider(
            "Replay Timeline Step",
            min_value=0,
            max_value=total_frames - 1,
            value=st.session_state.replay_frame,
            format="Step %d"
        )
        st.session_state.replay_frame = current_frame
        
    curr_data = df_history.iloc[current_frame]
    
    # Current Frame Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Date", curr_data["date_label"])
    m2.metric("Carbon Footprint", f"{curr_data['footprint']:.1f} kg CO2")
    m3.metric("Eco Score", f"{int(curr_data['eco_score'])} / 100")
    m4.metric("Assessments Count", f"{int(curr_data['count'])}")
    
    # Replay Progress Chart
    visible_df = df_history.iloc[: current_frame + 1]
    st.line_chart(visible_df.set_index("date_label")[["footprint", "eco_score"]])
    
    # Milestone Highlights
    st.subheader("⭐ Milestone Highlights")
    active_milestones = [m for m in milestones if m["period_idx"] <= current_frame]
    if active_milestones:
        for m in active_milestones:
            with st.container():
                st.success(f"{m['title']} ({m['date_label']}) - {m['description']} [Badge: {m['badge']}]")
    else:
        st.info("Keep replaying to unlock milestones along your timeline!")
        
    # Export Replay as GIF
    st.subheader("📥 Export Replay Visualization")
    with st.spinner("Generating your replay GIF..."):
        gif_bytes = export_replay_gif(df_history)
    st.download_button(
        label="🎥 Download Replay as GIF",
        data=gif_bytes,
        file_name="carbon_footprint_replay.gif",
        mime="image/gif"
    )
