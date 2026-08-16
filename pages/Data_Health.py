import json

import pandas as pd
import streamlit as st

from data_quality import (
    SEVERITY_CRITICAL,
    SEVERITY_INFO,
    SEVERITY_ORDER,
    SEVERITY_WARNING,
    audit_assessments,
    filter_clean_records,
    summarize_report,
    to_dict,
)
from database import get_assessments
from styles.theme import apply_theme

user_id = st.session_state.get('user_id')
if not user_id:
    st.warning('Please log in from the main application page.')
    st.stop()
apply_theme()

SEVERITY_STYLE = {
    SEVERITY_CRITICAL: ("🚨", "#e5484d"),
    SEVERITY_WARNING: ("⚠️", "#f5a524"),
    SEVERITY_INFO: ("ℹ️", "#4c8dff"),
}

GRADE_COLORS = {
    "A": "#0cb93d",
    "B": "#4caf50",
    "C": "#f5a524",
    "D": "#f97316",
    "F": "#e5484d",
}

st.markdown("<div class='section-header'>🩺 Data Health</div>", unsafe_allow_html=True)
st.markdown(
    "Your charts, trends, forecast and eco score are only as trustworthy as the "
    "data behind them. This page audits your stored assessments for anomalies "
    "and tells you how much confidence they deserve."
)
st.markdown("---")

assessments = get_assessments(user_id)

if not assessments:
    st.info("No assessments recorded yet — run one from the Carbon Footprint page.")
    st.stop()

run_drift_check = st.checkbox(
    "Also re-derive each footprint from its own inputs (slower)",
    value=False,
    help="Recomputes every stored assessment to find rows whose footprint no "
         "longer matches the inputs it was calculated from.",
)

with st.spinner("Auditing your assessment history..."):
    report = audit_assessments(assessments, include_drift=run_drift_check)

# --- Headline ---------------------------------------------------------------

grade_color = GRADE_COLORS.get(report["grade"], "#888888")

st.markdown(
    f"<div style='padding:1rem 1.25rem;border-radius:10px;"
    f"border-left:6px solid {grade_color};background:rgba(128,128,128,0.08);"
    f"margin-bottom:1rem;'>"
    f"<span style='font-size:2rem;font-weight:700;color:{grade_color};'>"
    f"{report['grade']}</span>"
    f"<span style='margin-left:0.75rem;'>{summarize_report(report)}</span></div>",
    unsafe_allow_html=True,
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Confidence", f"{report['confidence_score']:.0f}/100")
col2.metric("Assessments", report["record_count"])
col3.metric("Issues found", report["issue_count"])
col4.metric("Records flagged", len(report["flagged_record_ids"]))

st.progress(report["confidence_score"] / 100.0)

# --- Issues -----------------------------------------------------------------

if not report["issues"]:
    st.success(
        "No data quality issues found. Every chart and trend built from this "
        "history can be taken at face value."
    )
else:
    st.markdown("### 🔍 What was found")

    for severity in SEVERITY_ORDER:
        issues = report["by_severity"].get(severity, [])
        if not issues:
            continue

        icon, color = SEVERITY_STYLE[severity]
        st.markdown(
            f"<div style='margin-top:1rem;font-weight:600;color:{color};'>"
            f"{icon} {severity.title()} ({len(issues)})</div>",
            unsafe_allow_html=True,
        )

        for issue in issues:
            with st.expander(issue["message"]):
                st.markdown(f"**What to do:** {issue['suggested_action']}")
                if issue["record_ids"]:
                    st.caption(
                        "Affected assessment ID(s): "
                        + ", ".join(str(record_id) for record_id in issue["record_ids"])
                    )
                st.caption(f"Issue code: `{issue['code']}`")

# --- Impact on analytics ----------------------------------------------------

st.markdown("---")
st.markdown("### 📉 Effect on your analytics")

clean_records = filter_clean_records(assessments, report)
excluded_count = len(assessments) - len(clean_records)

if excluded_count:
    st.warning(
        f"**{excluded_count} record(s)** are unreliable enough that trends and "
        "forecasts are better computed without them."
    )

    footprints = [row[7] for row in assessments if row[7] is not None]
    clean_footprints = [row[7] for row in clean_records if row[7] is not None]

    if footprints and clean_footprints:
        st.dataframe(
            pd.DataFrame([
                {
                    "Metric": "Average footprint (kg CO₂)",
                    "All records": round(sum(footprints) / len(footprints), 1),
                    "Excluding flagged": round(
                        sum(clean_footprints) / len(clean_footprints), 1
                    ),
                },
                {
                    "Metric": "Highest footprint (kg CO₂)",
                    "All records": round(max(footprints), 1),
                    "Excluding flagged": round(max(clean_footprints), 1),
                },
                {
                    "Metric": "Records counted",
                    "All records": len(footprints),
                    "Excluding flagged": len(clean_footprints),
                },
            ]),
            use_container_width=True,
            hide_index=True,
        )
else:
    st.success(
        "Nothing is severe enough to exclude — every record is safe to feed to "
        "your trends and forecast."
    )

st.caption(
    "Outliers are flagged but deliberately kept: a genuinely high-emission month "
    "is exactly what this app exists to surface, so only records that cannot be "
    "analysed at all are excluded."
)

# --- Flagged records --------------------------------------------------------

if report["flagged_record_ids"]:
    with st.expander("🗂️ Flagged assessments"):
        flagged = set(report["flagged_record_ids"])
        st.dataframe(
            pd.DataFrame([
                {
                    "ID": row[0],
                    "Date": row[1],
                    "Transport": row[2],
                    "Diet": row[5],
                    "Footprint (kg)": row[7],
                    "Eco score": row[8],
                }
                for row in assessments if row[0] in flagged
            ]),
            use_container_width=True,
            hide_index=True,
        )

# --- Export -----------------------------------------------------------------

st.markdown("---")
st.download_button(
    "⬇️ Download quality report (JSON)",
    data=json.dumps(to_dict(report), indent=2),
    file_name="eco_buddy_data_quality_report.json",
    mime="application/json",
    use_container_width=True,
)
