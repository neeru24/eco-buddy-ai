"""
Carbon Calculation Replay Module (#443).

Enables comparison of calculation revisions, side-by-side input difference viewing,
chronological replay timeline navigation, and emission change highlight breakdown.
"""

from typing import List, Dict, Any, Tuple
import pandas as pd
import streamlit as st
from database import get_assessments


def compare_revisions(rev_a: Dict[str, Any], rev_b: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare two calculation revisions and generate delta metrics for all input fields.
    
    Args:
        rev_a: Baseline revision dict.
        rev_b: Comparison target revision dict.
        
    Returns:
        Dict[str, Any]: Comparison result with deltas and change flags.
    """
    fp_a = rev_a.get("footprint", 0.0)
    fp_b = rev_b.get("footprint", 0.0)
    
    score_a = rev_a.get("eco_score", 0)
    score_b = rev_b.get("eco_score", 0)
    
    dist_a = rev_a.get("distance", 0.0)
    dist_b = rev_b.get("distance", 0.0)
    
    elec_a = rev_a.get("electricity", 0.0)
    elec_b = rev_b.get("electricity", 0.0)
    
    flt_a = rev_a.get("flights", 0)
    flt_b = rev_b.get("flights", 0)
    
    return {
        "footprint_delta": round(fp_b - fp_a, 2),
        "eco_score_delta": score_b - score_a,
        "distance_delta": round(dist_b - dist_a, 2),
        "electricity_delta": round(elec_b - elec_a, 2),
        "flights_delta": flt_b - flt_a,
        "transport_changed": rev_a.get("transport") != rev_b.get("transport"),
        "diet_changed": rev_a.get("diet") != rev_b.get("diet"),
        "rev_a": rev_a,
        "rev_b": rev_b,
    }


def get_change_highlights(rev_a: Dict[str, Any], rev_b: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate human-readable change highlight breakdown explaining what caused emission shifts.
    """
    highlights = []
    diff = compare_revisions(rev_a, rev_b)
    
    # Transport shift
    if diff["transport_changed"]:
        highlights.append({
            "field": "Transport",
            "type": "Mode Shift",
            "impact": f"Changed transport mode from '{rev_a.get('transport')}' to '{rev_b.get('transport')}'."
        })
    if diff["distance_delta"] != 0:
        sign = "+" if diff["distance_delta"] > 0 else ""
        highlights.append({
            "field": "Distance",
            "type": "Travel Volume",
            "impact": f"Commute distance changed by {sign}{diff['distance_delta']} km."
        })
        
    # Electricity shift
    if diff["electricity_delta"] != 0:
        sign = "+" if diff["electricity_delta"] > 0 else ""
        highlights.append({
            "field": "Electricity",
            "type": "Energy Usage",
            "impact": f"Electricity consumption changed by {sign}{diff['electricity_delta']} kWh."
        })
        
    # Diet shift
    if diff["diet_changed"]:
        highlights.append({
            "field": "Diet",
            "type": "Dietary Choice",
            "impact": f"Diet type updated from '{rev_a.get('diet')}' to '{rev_b.get('diet')}'."
        })
        
    # Flights shift
    if diff["flights_delta"] != 0:
        sign = "+" if diff["flights_delta"] > 0 else ""
        highlights.append({
            "field": "Flights",
            "type": "Air Travel",
            "impact": f"Annual flights changed by {sign}{diff['flights_delta']} flight(s)."
        })
        
    if not highlights:
        highlights.append({
            "field": "Inputs",
            "type": "No Change",
            "impact": "Calculation inputs are identical between these two revisions."
        })
        
    return highlights


def build_replay_timeline(user_id: int = 1) -> List[Dict[str, Any]]:
    """
    Construct a chronological timeline of user calculation revisions.
    """
    raw_data = get_assessments(user_id=user_id)
    timeline = []
    
    if raw_data:
        for idx, row in enumerate(reversed(raw_data)):
            # row: id, date, created_at, transport, distance, electricity, diet, flights, footprint, eco_score
            timeline.append({
                "revision_num": idx + 1,
                "assessment_id": row[0],
                "date": row[1] or row[2] or f"Revision #{idx+1}",
                "transport": row[3] or "Car",
                "distance": float(row[4] or 0.0),
                "electricity": float(row[5] or 0.0),
                "diet": row[6] or "Average",
                "flights": int(row[7] or 0),
                "footprint": float(row[8] or 0.0),
                "eco_score": int(row[9] or 0),
            })
            
    # Sample baseline timeline if history is empty
    if len(timeline) < 2:
        sample_revisions = [
            {"revision_num": 1, "assessment_id": 101, "date": "2026-01-10", "transport": "Gasoline Car", "distance": 120.0, "electricity": 350.0, "diet": "Meat-Heavy", "flights": 2, "footprint": 480.0, "eco_score": 52},
            {"revision_num": 2, "assessment_id": 102, "date": "2026-02-15", "transport": "Hybrid Car", "distance": 90.0, "electricity": 280.0, "diet": "Flexitarian", "flights": 1, "footprint": 340.0, "eco_score": 70},
            {"revision_num": 3, "assessment_id": 103, "date": "2026-03-20", "transport": "Electric Vehicle", "distance": 60.0, "electricity": 220.0, "diet": "Vegetarian", "flights": 0, "footprint": 210.0, "eco_score": 88},
        ]
        return sample_revisions
        
    return timeline


def render_calculation_replay(user_id: int = 1) -> None:
    """
    Render Streamlit UI for Carbon Calculation Replay.
    """
    st.title("🧮 Carbon Calculation Replay")
    st.markdown(
        "Replay past calculations and compare revisions side-by-side to understand "
        "exactly how input adjustments (transport, energy, diet, travel) impacted your carbon footprint."
    )
    
    timeline = build_replay_timeline(user_id=user_id)
    if not timeline:
        st.warning("No calculation revisions available to replay.")
        return
        
    st.subheader("⏱️ Replay Timeline Scrubbing")
    step_idx = st.slider(
        "Select Revision Step",
        min_value=1,
        max_value=len(timeline),
        value=len(timeline),
        format="Rev #%d"
    )
    current_rev = timeline[step_idx - 1]
    
    st.info(
        f"**Viewing Revision #{current_rev['revision_num']}** (Assessment ID #{current_rev['assessment_id']} | Date: {current_rev['date']})"
    )
    
    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Transport Mode", current_rev["transport"])
    m2.metric("Distance (km)", f"{current_rev['distance']:.1f}")
    m3.metric("Total Footprint", f"{current_rev['footprint']:.1f} kg CO2")
    m4.metric("Eco Score", f"{current_rev['eco_score']} / 100")
    
    st.divider()
    
    # Revision Comparison Mode
    st.subheader("⚖️ Compare Calculation Revisions")
    col_a, col_b = st.columns(2)
    
    rev_labels = [f"Rev #{r['revision_num']} ({r['date']} - {r['footprint']:.1f} kg)" for r in timeline]
    with col_a:
        idx_a = st.selectbox("Baseline Revision (A)", range(len(timeline)), format_func=lambda i: rev_labels[i], index=0)
    with col_b:
        idx_b = st.selectbox("Comparison Revision (B)", range(len(timeline)), format_func=lambda i: rev_labels[i], index=len(timeline)-1)
        
    rev_a = timeline[idx_a]
    rev_b = timeline[idx_b]
    
    diff_res = compare_revisions(rev_a, rev_b)
    highlights = get_change_highlights(rev_a, rev_b)
    
    # Summary deltas
    c1, c2, c3 = st.columns(3)
    fp_delta = diff_res["footprint_delta"]
    score_delta = diff_res["eco_score_delta"]
    c1.metric("Footprint Change", f"{diff_res['rev_b']['footprint']:.1f} kg", delta=f"{fp_delta:+.1f} kg", delta_color="inverse")
    c2.metric("Eco Score Change", f"{diff_res['rev_b']['eco_score']} pts", delta=f"{score_delta:+d} pts")
    c3.metric("Revisions Span", f"Rev #{rev_a['revision_num']} ➔ Rev #{rev_b['revision_num']}")
    
    # Input Difference Viewer Table
    st.subheader("🔍 Input Difference Viewer")
    diff_data = [
        {"Input Parameter": "Transport Mode", "Baseline (Rev A)": rev_a["transport"], "Target (Rev B)": rev_b["transport"], "Difference": "Changed" if diff_res["transport_changed"] else "Identical"},
        {"Input Parameter": "Distance (km)", "Baseline (Rev A)": f"{rev_a['distance']:.1f}", "Target (Rev B)": f"{rev_b['distance']:.1f}", "Difference": f"{diff_res['distance_delta']:+.1f} km"},
        {"Input Parameter": "Electricity (kWh)", "Baseline (Rev A)": f"{rev_a['electricity']:.1f}", "Target (Rev B)": f"{rev_b['electricity']:.1f}", "Difference": f"{diff_res['electricity_delta']:+.1f} kWh"},
        {"Input Parameter": "Diet Type", "Baseline (Rev A)": rev_a["diet"], "Target (Rev B)": rev_b["diet"], "Difference": "Changed" if diff_res["diet_changed"] else "Identical"},
        {"Input Parameter": "Flights", "Baseline (Rev A)": str(rev_a["flights"]), "Target (Rev B)": str(rev_b["flights"]), "Difference": f"{diff_res['flights_delta']:+d} flight(s)"},
        {"Input Parameter": "Total Footprint", "Baseline (Rev A)": f"{rev_a['footprint']:.1f} kg", "Target (Rev B)": f"{rev_b['footprint']:.1f} kg", "Difference": f"{diff_res['footprint_delta']:+.1f} kg CO2"},
    ]
    st.dataframe(pd.DataFrame(diff_data), use_container_width=True)
    
    # Change Highlights
    st.subheader("💡 Emission Change Highlights")
    for h in highlights:
        st.success(f"**[{h['field']} - {h['type']}]** {h['impact']}")
