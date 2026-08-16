import datetime

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from device_lifecycle import (
    DEVICE_CONDITIONS,
    DEVICE_TYPES,
    DEFAULT_EFFICIENCY_GAIN,
    annualized_footprint,
    delete_device,
    disposal_guidance,
    extension_savings,
    get_devices,
    get_lifecycle_tips,
    lifetime_footprint,
    list_device_types,
    portfolio_summary,
    register_device,
    remaining_life,
    repair_vs_replace,
    retire_device,
    update_device,
    upgrade_break_even,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🔌 Device Lifecycle & E-Waste</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Most of a phone or laptop's carbon is emitted before you unbox it. Register "
    "your electronics to see that manufacturing footprint amortised over how long "
    "you actually keep them."
)

device_type_names = list(DEVICE_TYPES.keys())
current_year = datetime.date.today().year

st.markdown("---")
st.markdown("### ➕ Register a Device")

with st.form("register_device_form", clear_on_submit=True):
    row_one = st.columns([2, 2, 1])
    device_name = row_one[0].text_input("Name", placeholder="e.g. Work laptop")
    device_type = row_one[1].selectbox("Type", device_type_names)
    quantity = row_one[2].number_input("Quantity", min_value=1, max_value=20, value=1)

    row_two = st.columns([1, 1, 1])
    purchase_year = row_two[0].number_input(
        "Purchase year", min_value=1990, max_value=current_year, value=current_year - 2
    )
    daily_hours = row_two[1].number_input(
        "Hours used per day",
        min_value=0.0,
        max_value=24.0,
        value=float(DEVICE_TYPES[device_type_names[0]]["daily_hours"]),
        step=0.5,
        help="Leave at the default if you are not sure.",
    )
    condition = row_two[2].selectbox("Condition", DEVICE_CONDITIONS)

    if st.form_submit_button("Register device", use_container_width=True):
        if register_device(
            user_id, device_name, device_type, purchase_year, quantity, daily_hours, condition
        ):
            st.success(f"Registered **{device_name or device_type}**.")
            st.rerun()
        else:
            st.error("Could not register that device. Please check the details.")

devices = get_devices(user_id)
summary = portfolio_summary(devices)

st.markdown("---")
st.markdown("### 📦 Your Device Portfolio")

if not devices:
    st.info("No devices registered yet. Add one above to see its lifecycle footprint.")
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Devices", summary["device_count"])
    m2.metric("Embodied carbon owned", f"{summary['total_embodied_kg']:,.0f} kg")
    m3.metric("Annualised footprint", f"{summary['total_annual_kg']:,.0f} kg/yr")
    m4.metric("Average age", f"{summary['average_age_years']:,.1f} yrs")

    if summary["past_lifespan_count"]:
        st.success(
            f"🎉 {summary['past_lifespan_count']} device(s) are past their expected "
            f"lifespan and still going — that is the single best thing on this page."
        )

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.markdown("#### Manufacturing vs running, per device")
        split_df = pd.DataFrame(
            [
                {"Device": row["name"], "Source": "Manufacturing (amortised)",
                 "kg CO₂/yr": row["amortised_embodied_kg"]}
                for row in summary["devices"]
            ]
            + [
                {"Device": row["name"], "Source": "Running energy",
                 "kg CO₂/yr": row["operating_kg"]}
                for row in summary["devices"]
            ]
        )
        bar = px.bar(
            split_df,
            x="Device",
            y="kg CO₂/yr",
            color="Source",
            barmode="stack",
            color_discrete_map={
                "Manufacturing (amortised)": "#f97316",
                "Running energy": "#4ade80",
            },
        )
        bar.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(bar, use_container_width=True)

    with chart_right:
        st.markdown("#### Keeping devices longer")
        extra_years = st.slider("Extra years of ownership", 1, 5, 2)
        extension = extension_savings(devices, extra_years)
        st.metric(
            f"Annualised footprint after {extra_years} more year(s)",
            f"{extension['extended_annual_kg']:,.0f} kg/yr",
            delta=f"-{extension['saved_annual_kg']:,.0f} kg ({extension['saved_pct']}%)",
            delta_color="inverse",
        )
        curve = go.Figure()
        curve.add_trace(
            go.Scatter(
                x=list(range(0, 6)),
                y=[
                    extension_savings(devices, year)["extended_annual_kg"]
                    for year in range(0, 6)
                ],
                mode="lines+markers",
                line=dict(color="#4ade80"),
                name="Annualised footprint",
            )
        )
        curve.update_layout(
            height=300,
            xaxis_title="Extra years kept",
            yaxis_title="kg CO₂ per year",
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(curve, use_container_width=True)

    st.markdown("#### Device details")
    for device in devices:
        footprint = annualized_footprint(device)
        life = remaining_life(device)
        guidance = disposal_guidance(device)
        lifetime = lifetime_footprint(device)

        header = (
            f"{footprint['icon']} {footprint['name']} — "
            f"{footprint['annual_kg']:,.0f} kg CO₂/yr · {life['years_owned']} yrs old"
        )
        with st.expander(header):
            detail_one, detail_two, detail_three = st.columns(3)
            detail_one.metric("Manufacturing", f"{footprint['embodied_kg']:,.0f} kg")
            detail_two.metric(
                "Amortised", f"{footprint['amortised_embodied_kg']:,.0f} kg/yr"
            )
            detail_three.metric("Running", f"{footprint['operating_kg']:,.0f} kg/yr")

            st.progress(
                min(1.0, life["life_used_pct"] / 100),
                text=(
                    f"{life['life_used_pct']}% of its expected "
                    f"{life['expected_lifespan']}-year life used"
                ),
            )
            st.caption(
                f"Over a full life this device is responsible for about "
                f"{lifetime['lifetime_total_kg']:,.0f} kg CO₂, "
                f"{lifetime['embodied_share_pct']}% of it from manufacturing."
            )

            st.markdown(
                f"**Disposal advice:** {guidance['icon']} {guidance['label']} — "
                f"{guidance['detail']}"
            )
            st.caption(
                f"Repairability {guidance['repairability']}/10 · "
                f"{guidance['recoverable_kg']} kg of recoverable material"
            )
            if guidance["warning"]:
                st.warning(guidance["warning"])

            control_one, control_two, control_three = st.columns(3)
            new_condition = control_one.selectbox(
                "Condition",
                DEVICE_CONDITIONS,
                index=DEVICE_CONDITIONS.index(device["condition"]),
                key=f"condition_{device['id']}",
            )
            if new_condition != device["condition"]:
                update_device(device["id"], condition=new_condition)
                st.rerun()
            if control_two.button("📤 Retire", key=f"retire_{device['id']}"):
                retire_device(device["id"])
                st.rerun()
            if control_three.button("🗑️ Delete", key=f"delete_device_{device['id']}"):
                delete_device(device["id"])
                st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Lifecycle Tips")
    for tip in get_lifecycle_tips(summary):
        st.markdown(f"- {tip}")

st.markdown("---")
st.markdown("### 🔧 Repair or Replace?")
st.caption(
    "Compare keeping a device running against the manufacturing cost of a new one."
)

calc_left, calc_right = st.columns(2)
with calc_left:
    compare_type = st.selectbox("Device you own", device_type_names, key="repair_old")
    compare_hours = st.number_input(
        "Hours used per day",
        min_value=0.0,
        max_value=24.0,
        value=float(DEVICE_TYPES[compare_type]["daily_hours"]),
        step=0.5,
        key="repair_hours",
    )
    extends = st.slider("Years a repair would add", 1, 8, 3)

with calc_right:
    replacement = st.selectbox("Replacement you are considering", device_type_names,
                               index=device_type_names.index(compare_type), key="repair_new")
    gain = st.slider(
        "Replacement efficiency gain",
        0.0,
        0.9,
        DEFAULT_EFFICIENCY_GAIN,
        0.05,
        help="How much less power the new device draws.",
    )

comparison = repair_vs_replace(
    {"device_type": compare_type, "daily_hours": compare_hours},
    extends,
    replacement,
    gain,
)

verdict_left, verdict_right = st.columns(2)
verdict_left.metric("Repair & keep", f"{comparison['repair_kg']:,.0f} kg CO₂")
verdict_right.metric("Buy a replacement", f"{comparison['replace_kg']:,.0f} kg CO₂")

if comparison["verdict"] == "repair":
    st.success(f"🔧 **Repair wins.** {comparison['message']}")
else:
    st.warning(f"🆕 **Replacing wins here.** {comparison['message']}")

payback = upgrade_break_even(compare_type, replacement, compare_hours, gain)
if payback["break_even_years"] is None:
    st.caption(payback["message"])
elif payback["ever_pays_back"]:
    st.caption(
        f"{payback['message']} That is within the replacement's "
        f"{DEVICE_TYPES[replacement]['lifespan_years']:.0f}-year expected life."
    )
else:
    st.caption(
        f"{payback['message']} That is longer than its expected life of "
        f"{DEVICE_TYPES[replacement]['lifespan_years']:.0f} years, so it never pays back."
    )

st.markdown("---")
st.markdown("### 📚 Device Reference")
st.dataframe(
    pd.DataFrame(
        [
            {
                "Device": f"{info['icon']} {info['name']}",
                "Manufacturing (kg CO₂)": info["embodied_kg"],
                "Typical watts": info["typical_watts"],
                "Expected life (yrs)": info["lifespan_years"],
                "Repairability": f"{info['repairability']}/10",
            }
            for info in sorted(list_device_types(), key=lambda i: -i["embodied_kg"])
        ]
    ),
    use_container_width=True,
    hide_index=True,
)
