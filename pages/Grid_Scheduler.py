import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from grid_scheduler import (
    DEFAULT_DAYS_PER_YEAR,
    DEFAULT_GRID_PROFILE,
    DEFAULT_TARIFF,
    GRID_PROFILES,
    HOUR_LABELS,
    HOURS_IN_DAY,
    SHIFTABLE_LOADS,
    SHIFT_WORTH_IT_SCORE,
    TARIFFS,
    annual_savings,
    blend_curve,
    build_schedule,
    delete_schedule,
    get_intensity_curve,
    get_schedules,
    get_scheduling_tips,
    get_tariff,
    list_grid_profiles,
    list_shiftable_loads,
    save_schedule,
    shift_potential,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>⏰ Grid Carbon Intensity Scheduler</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "The rest of the app measures how much electricity you use. This page is "
    "about **when** you use it — the same kilowatt-hour can emit three times "
    "as much at 7pm as it does at 2pm, and moving a wash costs you nothing."
)

st.markdown("---")
st.markdown("### ⚡ Your Grid")

profile_col, tariff_col, days_col = st.columns(3)
grid_profile = profile_col.selectbox(
    "Grid mix",
    list(GRID_PROFILES.keys()),
    index=list(GRID_PROFILES.keys()).index(DEFAULT_GRID_PROFILE),
    help="Pick the mix that best describes your region's generation.",
)
tariff_name = tariff_col.selectbox(
    "Electricity tariff",
    list(TARIFFS.keys()),
    index=list(TARIFFS.keys()).index(DEFAULT_TARIFF),
)
days_per_year = days_col.number_input(
    "Run days per year",
    min_value=0,
    max_value=365,
    value=DEFAULT_DAYS_PER_YEAR,
    step=1,
    help="How many days a year this routine actually happens.",
)

base_curve = get_intensity_curve(grid_profile)
tariff = get_tariff(tariff_name)

solar_share = st.slider(
    "Share of a midday load your own rooftop solar can cover",
    min_value=0.0,
    max_value=1.0,
    value=0.0,
    step=0.05,
    help=(
        "If you generate your own power, the middle of the day is far cleaner "
        "for you than the grid average suggests."
    ),
)

curve = blend_curve(base_curve, solar_share) if solar_share > 0 else [float(v) for v in base_curve]

with st.expander("📏 Use my own hourly intensity figures"):
    st.caption(
        "Built-in curves are used unless you override them. Many grid operators "
        "publish real gCO₂/kWh figures by hour — paste them in here."
    )
    use_custom = st.checkbox("Override with my operator's data")
    custom_curve = []
    hour_columns = st.columns(6)
    for hour in range(HOURS_IN_DAY):
        custom_curve.append(
            hour_columns[hour % 6].number_input(
                HOUR_LABELS[hour],
                min_value=0.0,
                max_value=2000.0,
                value=float(curve[hour]),
                step=5.0,
                key=f"intensity_{hour}",
            )
        )
    if use_custom:
        curve = custom_curve

potential = shift_potential(curve)
profile_summary = {item["name"]: item for item in list_grid_profiles()}

if potential < SHIFT_WORTH_IT_SCORE:
    st.info(
        f"**Shift potential: {potential:.0f}/100.** This grid is close to flat "
        "across the day, so moving loads around saves very little. Your effort "
        "is better spent using less rather than re-timing it."
    )
else:
    st.success(
        f"**Shift potential: {potential:.0f}/100.** There is real day-to-night "
        "variation here — timing alone is worth chasing."
    )

st.markdown("---")
st.markdown("### 🔌 What Do You Run?")

flexible_loads = [item["name"] for item in list_shiftable_loads(shiftable_only=True)]
selected_loads = st.multiselect(
    "Flexible appliances",
    flexible_loads,
    default=["Dishwasher", "Washing machine", "Tumble dryer"],
    help="Only loads whose timing you can genuinely choose.",
)

constraints = {}
if selected_loads:
    st.caption(
        "Set the hours each appliance is allowed to run. Leaving both bounds "
        "the same means no restriction at all."
    )
    for load_name in selected_loads:
        details = SHIFTABLE_LOADS[load_name]
        with st.expander(
            f"{load_name} — {details['kwh']} kWh over {details['duration_hours']}h"
        ):
            st.caption(details["note"])
            earliest_col, latest_col, energy_col = st.columns(3)
            earliest = earliest_col.selectbox(
                "Not before", HOUR_LABELS, index=0, key=f"early_{load_name}"
            )
            latest = latest_col.selectbox(
                "Finished by", HOUR_LABELS, index=0, key=f"late_{load_name}"
            )
            energy = energy_col.number_input(
                "Energy per run (kWh)",
                min_value=0.0,
                max_value=200.0,
                value=float(details["kwh"]),
                step=0.1,
                key=f"kwh_{load_name}",
            )
            constraints[load_name] = {
                "earliest_hour": HOUR_LABELS.index(earliest),
                "latest_hour": HOUR_LABELS.index(latest),
                "kwh": energy,
            }

if not selected_loads:
    st.warning("Pick at least one appliance to build a schedule.")
    st.stop()

schedule = build_schedule(
    selected_loads, curve, tariff, constraints, days_per_year=days_per_year
)
annual = annual_savings(schedule, days_per_year=days_per_year)
marks = schedule["peak_and_trough"]

st.markdown("---")
st.markdown("### 📉 The Day, Hour by Hour")

figure = go.Figure()
figure.add_trace(
    go.Scatter(
        x=HOUR_LABELS,
        y=curve,
        mode="lines",
        name="Carbon intensity",
        line=dict(color="#78a945", width=3),
        fill="tozeroy",
        fillcolor="rgba(120, 169, 69, 0.18)",
    )
)

for item in schedule["loads"]:
    start = item["start_hour"]
    end = (start + item["duration_hours"]) % HOURS_IN_DAY
    if end <= start:
        end = HOURS_IN_DAY - 1
    figure.add_vrect(
        x0=HOUR_LABELS[start],
        x1=HOUR_LABELS[end],
        fillcolor="rgba(47, 94, 50, 0.22)",
        line_width=0,
        annotation_text=item["load"],
        annotation_position="top left",
    )

figure.add_hline(
    y=marks["average_intensity"],
    line_dash="dot",
    line_color="#888",
    annotation_text="Daily average",
)
figure.update_layout(
    height=430,
    margin=dict(l=10, r=10, t=30, b=10),
    xaxis_title="Hour of day",
    yaxis_title="gCO₂ per kWh",
    showlegend=False,
)
st.plotly_chart(figure, use_container_width=True)

st.caption(
    f"Greenest hour **{HOUR_LABELS[marks['greenest_hour']]}** at "
    f"{marks['greenest_intensity']:.0f} gCO₂/kWh · dirtiest hour "
    f"**{HOUR_LABELS[marks['dirtiest_hour']]}** at {marks['dirtiest_intensity']:.0f} "
    f"— a {marks['spread_pct']:.0f}% spread for the identical kilowatt-hour."
)

st.markdown("---")
st.markdown("### 🗓️ Your Schedule")

rows = []
for item in schedule["loads"]:
    rows.append(
        {
            "Appliance": item["load"],
            "Run at": item["window_label"],
            "Energy": f"{item['kwh']:.2f} kWh",
            "CO₂ there": f"{item['co2_kg']:.3f} kg",
            "At worst hour": f"{item['worst_co2_kg']:.3f} kg",
            "Saved per run": f"{item['saving_vs_average_kg']:.3f} kg",
            "Cost": f"{item['cost']:.2f}",
        }
    )
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

metric_columns = st.columns(4)
metric_columns[0].metric("Daily CO₂ at best timing", f"{schedule['total_co2_kg']:.2f} kg")
metric_columns[1].metric(
    "Saved vs average timing",
    f"{schedule['daily_saving_vs_average_kg']:.2f} kg/day",
)
metric_columns[2].metric("Saved per year", f"{annual['co2_saved_kg']:.1f} kg")
metric_columns[3].metric(
    "Saved vs worst timing", f"{annual['co2_saved_vs_worst_kg']:.1f} kg/yr"
)

if annual["cost_penalty"] > 0:
    st.warning(
        f"On the **{tariff_name}** tariff the greenest hours are not the cheapest "
        f"ones. Following this plan costs about **{annual['cost_penalty']:.2f}** more "
        "per year than pure cost-chasing would. The cheapest start hour for each "
        "load is available in the schedule data if the bill matters more to you."
    )

st.markdown("---")
st.markdown("### 💡 What To Do About It")
for tip in get_scheduling_tips(schedule, curve):
    st.markdown(f"- {tip}")

st.markdown("---")
st.markdown("### 💾 Save This Schedule")

name_col, save_col = st.columns([3, 1])
schedule_name = name_col.text_input("Schedule name", value="Weekday routine")
if save_col.button("Save schedule", use_container_width=True):
    if save_schedule(user_id, schedule_name, schedule, grid_profile, tariff_name):
        st.success("Schedule saved.")
    else:
        st.error("Could not save that schedule.")

saved_schedules = get_schedules(user_id)
if saved_schedules:
    st.markdown("#### Saved schedules")
    for record in saved_schedules:
        detail_col, delete_col = st.columns([5, 1])
        detail_col.markdown(
            f"**{record['schedule_name']}** — {record['grid_profile']} · "
            f"{record['total_kwh']:.1f} kWh/day · "
            f"{record['daily_saving_kg']:.2f} kg saved daily · "
            f"{record['annual_saving_kg']:.0f} kg a year"
        )
        if delete_col.button("Delete", key=f"delete_schedule_{record['id']}"):
            delete_schedule(record["id"])
            st.rerun()
else:
    st.caption("No saved schedules yet.")

st.markdown("---")
st.markdown("### 📚 How the Grids Compare")
comparison = pd.DataFrame(
    [
        {
            "Grid mix": item["name"],
            "Average": f"{item['average_intensity']:.0f} gCO₂/kWh",
            "Cleanest hour": f"{item['min_intensity']:.0f}",
            "Dirtiest hour": f"{item['max_intensity']:.0f}",
            "Shift potential": f"{item['shift_potential']:.0f}/100",
        }
        for item in list_grid_profiles()
    ]
)
st.dataframe(comparison, use_container_width=True, hide_index=True)
st.caption(
    "A flat grid rewards using less. A variable one also rewards using it later. "
    "Curves are representative daily shapes, not forecasts — override them above "
    "if your operator publishes real figures."
)
