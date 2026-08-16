"""Boundary reconciliation.

Each module in this app is correct on its own terms. This page checks what
happens when their answers are added together, and counts each kilogram once.
"""

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from boundary_reconciliation import (
    DEFAULT_CONFIDENCE,
    DEFAULT_FRAME,
    FRAMES,
    MODULE_CLAIMS,
    ReconciliationError,
    activity_label,
    delete_reconciliation,
    get_frame,
    get_reconciliation_insights,
    get_reconciliations,
    list_activities,
    list_frames,
    make_claim,
    reconcile,
    save_reconciliation,
)
from styles.theme import apply_theme

CONFIDENCE_LEVELS = ["measured", "estimated", "modelled"]

PRESET = [
    {"source": "household", "activity": "home.electricity", "kg": 1200.0,
     "frame": "consumption", "kind": "footprint", "confidence": "measured",
     "base_kg": 0.0, "exclusive_group": ""},
    {"source": "digital_footprint", "activity": "home.electricity.devices",
     "kg": 300.0, "frame": "consumption", "kind": "footprint",
     "confidence": "modelled", "base_kg": 0.0, "exclusive_group": ""},
    {"source": "degree_days", "activity": "home.gas.space_heating", "kg": 1800.0,
     "frame": "consumption", "kind": "footprint", "confidence": "measured",
     "base_kg": 0.0, "exclusive_group": ""},
    {"source": "device_lifecycle", "activity": "goods.electronics.embodied",
     "kg": 250.0, "frame": "consumption", "kind": "footprint",
     "confidence": "modelled", "base_kg": 0.0, "exclusive_group": ""},
    {"source": "shopping_assistant", "activity": "goods.electronics", "kg": 400.0,
     "frame": "consumption", "kind": "footprint", "confidence": "estimated",
     "base_kg": 0.0, "exclusive_group": ""},
    {"source": "financed_emissions", "activity": "investments", "kg": 4000.0,
     "frame": "financed", "kind": "footprint", "confidence": "modelled",
     "base_kg": 0.0, "exclusive_group": ""},
    {"source": "grid_scheduler", "activity": "home.electricity.flexible",
     "kg": 120.0, "frame": "consumption", "kind": "saving",
     "confidence": "modelled", "base_kg": 400.0, "exclusive_group": ""},
    {"source": "smart_home", "activity": "home.electricity.flexible", "kg": 100.0,
     "frame": "consumption", "kind": "saving", "confidence": "modelled",
     "base_kg": 400.0, "exclusive_group": ""},
]

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🧾 Boundary Reconciliation</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Every module here is correct on its own terms. Nothing checks what "
    "happens when you add several of them together — and in some combinations "
    "the same kilogram gets counted twice."
)

with st.expander("What overlaps, and what only looks like it does"):
    st.markdown(
        """
**Footprints that overlap.** `digital_footprint` estimates the electricity your
devices use; `household` reads it off the bill. The device electricity is
*inside* the bill. Buy a laptop and its embodied carbon can appear in both
`device_lifecycle` and `shopping_assistant`.

**Savings that overlap.** `grid_scheduler` projects a saving from shifting
flexible load; `smart_home` projects one from automating the same load. Two
savings, one dishwasher.

**And the mistake to avoid.** Two claims on the same activity are *not*
automatically duplicates. Insulating a loft and installing a heat pump both act
on space-heating gas, but they act one after the other — the second saves less
because the first already happened. Deleting one would understate as badly as
adding both overstates. So footprints deduplicate and savings **compose**.

**Frames are never added.** A consumption footprint, a production attribution
and a financed attribution can all contain the same tonne, held by three
different people. They are reported side by side and left that way.

**Where the rules do not resolve, nothing is chosen.** Two measured claims on
the same boundary that disagree produce a conflict, not a quietly selected
winner — that is how this problem gets reproduced one level up.
        """
    )

st.markdown("---")
st.markdown("### 1. The Claims")

if "reconciliation_claims" not in st.session_state:
    st.session_state.reconciliation_claims = [dict(row) for row in PRESET]

claims = st.session_state.reconciliation_claims

add_col, preset_col, clear_col, _ = st.columns([1, 1, 1, 2])
with add_col:
    if st.button("➕ Add claim", use_container_width=True):
        claims.append({
            "source": "new_module", "activity": "home.electricity", "kg": 100.0,
            "frame": DEFAULT_FRAME, "kind": "footprint",
            "confidence": DEFAULT_CONFIDENCE, "base_kg": 0.0, "exclusive_group": "",
        })
with preset_col:
    if st.button("Reset to example", use_container_width=True):
        st.session_state.reconciliation_claims = [dict(row) for row in PRESET]
        st.rerun()
with clear_col:
    if st.button("Clear all", use_container_width=True):
        st.session_state.reconciliation_claims = []
        st.rerun()

for index, claim in enumerate(list(claims)):
    with st.container(border=True):
        first = st.columns([2, 3, 2, 1])
        with first[0]:
            claim["source"] = st.text_input(
                "Module", value=claim["source"], key=f"rc_source_{index}"
            )
        with first[1]:
            options = list_activities()
            if claim["activity"] not in options:
                options = options + [claim["activity"]]
            claim["activity"] = st.selectbox(
                "Activity",
                options,
                index=options.index(claim["activity"]),
                format_func=activity_label,
                key=f"rc_activity_{index}",
            )
        with first[2]:
            claim["kg"] = st.number_input(
                "kg CO₂e",
                min_value=0.0,
                max_value=1000000.0,
                value=float(claim["kg"]),
                step=10.0,
                key=f"rc_kg_{index}",
            )
        with first[3]:
            st.write("")
            if st.button("Remove", key=f"rc_remove_{index}", use_container_width=True):
                claims.pop(index)
                st.rerun()

        second = st.columns([2, 2, 2, 2])
        with second[0]:
            claim["kind"] = st.selectbox(
                "Kind",
                ["footprint", "saving"],
                index=["footprint", "saving"].index(claim["kind"]),
                key=f"rc_kind_{index}",
            )
        with second[1]:
            claim["frame"] = st.selectbox(
                "Frame",
                list_frames(),
                index=list_frames().index(claim["frame"]),
                format_func=lambda name: get_frame(name)["label"],
                key=f"rc_frame_{index}",
            )
        with second[2]:
            claim["confidence"] = st.selectbox(
                "Confidence",
                CONFIDENCE_LEVELS,
                index=CONFIDENCE_LEVELS.index(claim["confidence"]),
                key=f"rc_confidence_{index}",
            )
        with second[3]:
            if claim["kind"] == "saving":
                claim["base_kg"] = st.number_input(
                    "Out of (kg)",
                    min_value=0.0,
                    max_value=1000000.0,
                    value=float(claim["base_kg"] or 0.0),
                    step=10.0,
                    key=f"rc_base_{index}",
                    help="A saving needs the base it came from, or two "
                         "measures on the same activity cannot be composed.",
                )
            else:
                claim["base_kg"] = 0.0
                st.caption("Footprints need no base.")

built = []
problems = []
for claim in claims:
    try:
        built.append(make_claim(
            source=claim["source"] or "unnamed",
            activity=claim["activity"],
            kg=claim["kg"],
            frame=claim["frame"],
            kind=claim["kind"],
            confidence=claim["confidence"],
            base_kg=claim["base_kg"] if claim["kind"] == "saving" else None,
            exclusive_group=claim.get("exclusive_group") or None,
        ))
    except ReconciliationError as error:
        problems.append(f"{claim.get('source', 'a claim')}: {error}")

for problem in problems:
    st.error(problem)

report = reconcile(built)

st.markdown("---")
st.markdown("### 2. What The Sum Would Have Said")

naive_col, over_col, pct_col, conflict_col = st.columns(4)
with naive_col:
    st.metric("Naive sum", f"{report['naive_total_kg']:,.0f} kg")
with over_col:
    st.metric(
        "Overstated by",
        f"{report['overstatement_kg']:,.0f} kg",
        delta=f"−{report['overstatement_kg']:,.0f}",
        delta_color="inverse",
    )
with pct_col:
    st.metric("Share", f"{report['overstatement_pct']:.1f}%")
with conflict_col:
    st.metric("Unresolved conflicts", len(report["conflicts"]))

st.markdown("---")
st.markdown("### 3. Footprints, By Frame")
st.caption(
    "These totals are never added to each other. The same tonne can appear in "
    "more than one of them, held by different people."
)

frames = report["footprints"]["frames"]
if not frames:
    st.caption("No footprint claims.")
else:
    frame_columns = st.columns(len(frames))
    for column, (name, frame) in zip(frame_columns, frames.items()):
        with column:
            st.markdown(f"**{frame['label']}**")
            st.metric("Reconciled", f"{frame['reconciled_total_kg']:,.0f} kg")
            if frame["removed_kg"] > 0:
                st.caption(
                    f"Naive sum {frame['naive_total_kg']:,.0f} kg, of which "
                    f"{frame['removed_kg']:,.0f} kg was already counted "
                    f"somewhere else."
                )
            st.caption(FRAMES[name]["note"])

    rows = []
    for name, frame in frames.items():
        for claim in frame["claims"]:
            rows.append({
                "Frame": frame["label"],
                "Module": claim["source"],
                "Activity": activity_label(claim["activity"]),
                "Confidence": claim["confidence"],
                "Claimed": round(claim["kg"]),
                "Counted": round(claim["retained_kg"]),
                "Removed": round(claim["removed_kg"]),
            })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

audit = report["footprints"]["audit"]
if audit:
    st.markdown("**Audit trail**")
    st.caption(
        "A corrected total nobody can trace back to its adjustments will not "
        "be trusted, and should not be."
    )
    for entry in audit:
        st.markdown(
            f"- **{entry['source']}** − {entry['removed_kg']:,.0f} kg "
            f"(*{entry['rule']}*) — {entry['detail']}"
        )

if report["conflicts"]:
    st.markdown("**Conflicts**")
    for conflict in report["conflicts"]:
        st.error(f"{' vs '.join(conflict['claims'])} — {conflict['reason']}")

if report["unreconcilable"]:
    st.warning(
        f"{len(report['unreconcilable'])} claim(s) did not declare enough "
        f"boundary to be reconciled and are excluded from the totals rather "
        f"than quietly trusted."
    )

st.markdown("---")
st.markdown("### 4. Savings, Composed Rather Than Deleted")

savings = report["savings"]
if not savings["activities"]:
    st.caption("No saving claims.")
else:
    naive_col, composed_col, loss_col = st.columns(3)
    with naive_col:
        st.metric("Added up", f"{savings['naive_total_kg']:,.0f} kg")
    with composed_col:
        st.metric("Composed", f"{savings['composed_total_kg']:,.0f} kg")
    with loss_col:
        st.metric(
            "Interaction",
            f"{savings['interaction_loss_kg']:,.0f} kg",
            help="Not duplication — the second measure acts on what the first "
                 "left behind.",
        )

    for activity in savings["activities"]:
        with st.container(border=True):
            st.markdown(
                f"**{activity['label']}** — "
                f"{activity['composed_total_kg']:,.0f} kg of a "
                f"{activity['base_kg']:,.0f} kg base"
            )
            if activity["interacting"]:
                st.caption(
                    "More than one measure acts here, so each is applied "
                    "against what the previous one left."
                )
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Module": entry["source"],
                            "On its own": round(entry["standalone_kg"]),
                            "After interaction": round(entry["applied_kg"]),
                            "Given back": round(entry["interaction_kg"]),
                        }
                        for entry in activity["applied"]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

    if savings["dropped"]:
        st.markdown("**Dropped as mutually exclusive**")
        for entry in savings["dropped"]:
            st.markdown(f"- {entry['claim']} — {entry['detail']}")

    figure = go.Figure(
        go.Waterfall(
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Added up", "Interaction", "Composed"],
            y=[
                savings["naive_total_kg"],
                -savings["interaction_loss_kg"],
                0,
            ],
            connector={"line": {"width": 1}},
        )
    )
    figure.update_layout(
        title="Projected savings, before and after interaction",
        yaxis_title="kg CO₂e",
        height=340,
    )
    st.plotly_chart(figure, use_container_width=True)

st.markdown("---")
st.markdown("### 5. Who Claims What")
st.caption(
    "Not enforced — a claim carries its own boundary — but recorded so the "
    "overlaps are visible in one place rather than rediscovered."
)
st.dataframe(
    pd.DataFrame(
        [
            {
                "Module": module,
                "Activity": activity_label(entry["activity"]),
                "Frame": FRAMES[entry["frame"]]["label"],
                "Confidence": entry["confidence"],
            }
            for module, entry in MODULE_CLAIMS.items()
        ]
    ),
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")
st.markdown("### 💡 What To Take From This")
for insight in get_reconciliation_insights(report):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 💾 Saved Reconciliations")

name_col, save_col = st.columns([3, 1])
with name_col:
    report_name = st.text_input(
        "Name", value="Full account", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save", use_container_width=True):
        if save_reconciliation(user_id, report_name, report):
            st.success("Saved.")
            st.rerun()
        else:
            st.error("Could not save this reconciliation.")

saved = get_reconciliations(user_id)
if not saved:
    st.caption("Nothing saved yet.")
else:
    for entry in saved:
        with st.container(border=True):
            detail_col, delete_col = st.columns([5, 1])
            with detail_col:
                flag = f" · {entry['conflict_count']} conflict(s)" if entry["conflict_count"] else ""
                st.markdown(f"**{entry['name']}**{flag}")
                st.caption(
                    f"{entry['naive_total_kg']:,.0f} kg claimed, "
                    f"{entry['overstatement_kg']:,.0f} kg of it twice · "
                    f"{entry['created_at']}"
                )
            with delete_col:
                if st.button("Delete", key=f"delete_reconciliation_{entry['id']}"):
                    delete_reconciliation(entry["id"])
                    st.rerun()

    st.download_button(
        "📥 Download as JSON",
        json.dumps(saved, indent=2, default=str),
        file_name="boundary_reconciliations.json",
        mime="application/json",
    )
