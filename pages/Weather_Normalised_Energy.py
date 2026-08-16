import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from degree_days import (
    DEFAULT_BASE_TEMPERATURE,
    DEFAULT_CLIMATE_ZONE,
    MIN_READINGS,
    MONTHS,
    US_BASE_TEMPERATURE,
    DegreeDayError,
    annual_degree_days,
    attribute_change,
    compare_to_typical,
    delete_baseline,
    estimate_retrofit,
    fit_energy_model,
    get_baselines,
    get_energy_tips,
    heating_season_months,
    list_climate_zones,
    monthly_degree_day_series,
    predict_consumption,
    save_baseline,
    split_consumption,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🌡️ Weather-Normalised Energy</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Most of your energy bill is the weather. That makes month-to-month and "
    "year-to-year comparisons close to meaningless — insulate in October, hit "
    "a cold November, and your bill goes **up**. This page takes the "
    "temperature out so you can see what you actually did."
)

# Grid electricity factor used only to translate kWh into carbon on this page.
DEFAULT_EMISSION_FACTOR = 0.21

st.markdown("---")
st.markdown("### 📍 Your Climate")

zones = list_climate_zones()
zone_names = [zone["name"] for zone in zones]

zone_col, base_col, unit_col = st.columns(3)
with zone_col:
    zone = st.selectbox(
        "Climate zone",
        zone_names,
        index=zone_names.index(DEFAULT_CLIMATE_ZONE)
        if DEFAULT_CLIMATE_ZONE in zone_names
        else 0,
    )
with base_col:
    convention = st.radio(
        "Base temperature convention",
        ["UK / EU (15.5°C)", "US (18.3°C)", "Custom"],
        horizontal=False,
    )
with unit_col:
    if convention == "Custom":
        base_temperature = st.number_input(
            "Base temperature (°C)",
            min_value=5.0,
            max_value=30.0,
            value=DEFAULT_BASE_TEMPERATURE,
            step=0.5,
        )
    else:
        base_temperature = (
            DEFAULT_BASE_TEMPERATURE
            if convention.startswith("UK")
            else US_BASE_TEMPERATURE
        )
        st.metric("Base temperature", f"{base_temperature}°C")

selected = next(item for item in zones if item["name"] == zone)
st.caption(selected["description"])

annual = annual_degree_days(zone, base_temperature)
series = monthly_degree_day_series(zone, base_temperature)

hdd_col, cdd_col, season_col = st.columns(3)
hdd_col.metric("Annual heating degree days", f"{annual['hdd']:,.0f}")
cdd_col.metric("Annual cooling degree days", f"{annual['cdd']:,.0f}")
season = heating_season_months(zone, base_temperature)
season_col.metric("Heating season", f"{len(season)} months" if season else "None")

degree_day_figure = go.Figure()
degree_day_figure.add_trace(
    go.Bar(
        name="Heating degree days",
        x=MONTHS,
        y=[month["hdd"] for month in series],
        marker_color="rgba(70, 130, 180, 0.8)",
    )
)
degree_day_figure.add_trace(
    go.Bar(
        name="Cooling degree days",
        x=MONTHS,
        y=[month["cdd"] for month in series],
        marker_color="rgba(214, 137, 16, 0.8)",
    )
)
degree_day_figure.update_layout(
    barmode="group",
    height=320,
    yaxis_title="Degree days",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(degree_day_figure, use_container_width=True)

with st.expander("Why a warm month still shows heating demand"):
    st.markdown(
        "Degree days are counted per day, not per month. A month averaging "
        "16°C still contains cold nights when the heating comes on, so "
        "calculating from the monthly average alone would report zero and the "
        "boiler would disagree. This page uses **Hitchin's formula**, the "
        "standard correction that recovers daily behaviour from a monthly "
        "mean. It matters most in spring and autumn — exactly where the "
        "interesting variation lives."
    )

st.markdown("---")
st.markdown("### 🔢 Your Meter Readings")
st.caption(
    f"Enter monthly kWh from your bills. At least {MIN_READINGS} months are "
    f"needed, and a full year gives a dependable answer. The degree days are "
    f"filled in from your climate zone — overwrite them if you have real "
    f"local figures."
)

default_readings = pd.DataFrame(
    [
        {
            "Month": MONTHS[index],
            "kWh": round(180.0 + 0.55 * series[index]["hdd"], 0),
            "Heating degree days": round(series[index]["hdd"], 0),
        }
        for index in range(12)
    ]
)

edited = st.data_editor(
    default_readings,
    num_rows="dynamic",
    use_container_width=True,
    key="degree_day_readings",
    column_config={
        "kWh": st.column_config.NumberColumn(min_value=0.0, format="%.0f"),
        "Heating degree days": st.column_config.NumberColumn(
            min_value=0.0, format="%.0f"
        ),
    },
)

readings = [
    {
        "label": str(row.get("Month", "")),
        "kwh": row.get("kWh", 0.0),
        "hdd": row.get("Heating degree days", 0.0),
    }
    for _, row in edited.iterrows()
]

try:
    fit = fit_energy_model(readings)
except DegreeDayError as error:
    st.error(str(error))
    st.stop()

st.markdown("---")
st.markdown("### 🏠 What Your Home Is Actually Doing")

if fit["warning"]:
    if fit["is_reliable"]:
        st.info(fit["warning"])
    else:
        st.warning(fit["warning"])

baseload_col, sensitivity_col, fit_col = st.columns(3)
baseload_col.metric("Baseload", f"{fit['baseload']:,.0f} kWh/month")
sensitivity_col.metric("Envelope", f"{fit['sensitivity']:.2f} kWh per degree day")
fit_col.metric(
    "Model fit (R²)",
    f"{fit['r_squared']:.2f}",
    delta="reliable" if fit["is_reliable"] else "not reliable",
    delta_color="normal" if fit["is_reliable"] else "inverse",
)

split = split_consumption(fit, annual["hdd"])

split_figure = go.Figure()
split_figure.add_trace(
    go.Bar(
        name="Baseload (appliances, hot water, standby)",
        x=["Annual energy"],
        y=[split["baseload_total"]],
        marker_color="rgba(46, 139, 87, 0.8)",
    )
)
split_figure.add_trace(
    go.Bar(
        name="Weather-driven (heating)",
        x=["Annual energy"],
        y=[split["weather_total"]],
        marker_color="rgba(70, 130, 180, 0.8)",
    )
)
split_figure.update_layout(
    barmode="stack",
    height=300,
    yaxis_title="kWh per year",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(split_figure, use_container_width=True)

diagnosis = {
    "envelope": (
        "**Your building fabric is the problem.** Most of your energy goes on "
        "heating, which means insulation, draught-proofing and glazing are "
        "where your money should go. Replacing appliances would barely move it."
    ),
    "baseload": (
        "**Your appliances are the problem.** Most of your energy is consumed "
        "regardless of the weather, so insulation would barely touch it. Look "
        "at always-on loads, hot water and standby."
    ),
    "balanced": (
        "**Your energy is split fairly evenly** between heating and baseload, "
        "so both fabric measures and appliance changes are worth doing."
    ),
}
st.markdown(diagnosis[split["dominant"]])

for tip in get_energy_tips(fit, split):
    st.info(tip)

# The fitted line against the actual readings. If the points scatter widely
# around it, the R squared above is telling the truth and the user can see why.
scatter_figure = go.Figure()
scatter_figure.add_trace(
    go.Scatter(
        name="Your readings",
        x=[reading["hdd"] for reading in readings],
        y=[reading["kwh"] for reading in readings],
        mode="markers",
        marker=dict(size=10, color="rgba(46, 139, 87, 0.85)"),
    )
)
line_hdd = sorted(reading["hdd"] for reading in readings)
scatter_figure.add_trace(
    go.Scatter(
        name="Fitted model",
        x=line_hdd,
        y=[predict_consumption(fit, hdd) for hdd in line_hdd],
        mode="lines",
        line=dict(color="rgba(70, 130, 180, 0.9)", dash="dash"),
    )
)
scatter_figure.update_layout(
    height=340,
    xaxis_title="Heating degree days in the period",
    yaxis_title="kWh consumed",
    margin=dict(l=10, r=10, t=30, b=10),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(scatter_figure, use_container_width=True)

with st.expander("How does this compare to other homes?"):
    floor_area = st.number_input(
        "Floor area (m²)", min_value=0, max_value=1000, value=90, step=5
    )
    if floor_area > 0:
        context = compare_to_typical(fit, annual["hdd"], floor_area_m2=floor_area)
        band_labels = {
            "excellent": "Excellent — comparable to a modern, well-insulated home.",
            "good": "Good — better than most of the housing stock.",
            "typical": "Typical — room for improvement in the fabric.",
            "poor": "Poor — the sort of figure a solid-wall, uninsulated home gives.",
        }
        st.metric(
            "Annual energy per m²", f"{context['annual_kwh_per_m2']:,.0f} kWh/m²"
        )
        st.markdown(band_labels[context["band"]])

st.markdown("---")
st.markdown("### 📆 Year-on-Year, With the Weather Removed")
st.caption(
    "The question every energy comparison is really asking: did I improve, or "
    "was it just a milder winter?"
)

before_col, after_col = st.columns(2)
with before_col:
    st.markdown("**Last year**")
    before_kwh = st.number_input("kWh used", min_value=0.0, value=5000.0, step=100.0, key="before_kwh")
    before_hdd = st.number_input(
        "Heating degree days", min_value=0.0, value=2000.0, step=50.0, key="before_hdd"
    )
with after_col:
    st.markdown("**This year**")
    after_kwh = st.number_input("kWh used", min_value=0.0, value=5200.0, step=100.0, key="after_kwh")
    after_hdd = st.number_input(
        "Heating degree days", min_value=0.0, value=2600.0, step=50.0, key="after_hdd"
    )

attribution = attribute_change(
    before_kwh, before_hdd, after_kwh, after_hdd, fit, DEFAULT_EMISSION_FACTOR
)

raw_col, weather_col, behaviour_col = st.columns(3)
raw_col.metric(
    "Raw change", f"{attribution['total_change']:+,.0f} kWh",
    delta=f"{attribution['total_change_percent']:+.1f}%",
    delta_color="inverse",
)
weather_col.metric("Down to the weather", f"{attribution['weather_change']:+,.0f} kWh")
behaviour_col.metric(
    "Down to you",
    f"{attribution['behaviour_change']:+,.0f} kWh",
    delta=f"{attribution['behaviour_change_co2']:+,.0f} kg CO2e",
    delta_color="inverse",
)

if attribution["verdict"] in ("genuine_improvement", "hidden_improvement"):
    st.success(attribution["explanation"])
elif attribution["verdict"] == "mild_weather_flattered":
    st.warning(attribution["explanation"])
else:
    st.error(attribution["explanation"])

st.markdown("---")
st.markdown("### 🔨 Did the Retrofit Work?")
st.caption(
    "A fabric measure shows up as a fall in kWh per degree day. Save a "
    "baseline before the work, fit again afterwards, and the difference is a "
    "measurement rather than a brochure claim."
)

name_col, save_col = st.columns([3, 1])
with name_col:
    baseline_name = st.text_input(
        "Baseline name", value="Before retrofit", label_visibility="collapsed"
    )
with save_col:
    if st.button("Save this fit as a baseline", use_container_width=True):
        if save_baseline(user_id, baseline_name, fit, zone, base_temperature):
            st.success("Saved.")
        else:
            st.error("Could not save that baseline.")

baselines = get_baselines(user_id)
if not baselines:
    st.caption("No saved baselines yet. Save one to compare against later.")
else:
    labels = {
        f"{item['name']} ({item['sensitivity']:.2f} kWh/HDD, R²={item['r_squared']:.2f})": item
        for item in baselines
    }
    chosen = st.selectbox("Compare current fit against", list(labels.keys()))
    baseline = labels[chosen]

    retrofit = estimate_retrofit(
        baseline, fit, annual["hdd"], DEFAULT_EMISSION_FACTOR
    )

    change_col, saving_col, carbon_col = st.columns(3)
    change_col.metric(
        "Envelope change",
        f"{retrofit['sensitivity_change']:+.2f} kWh/HDD",
        delta=f"{retrofit['sensitivity_change_percent']:+.0f}%",
        delta_color="inverse",
    )
    saving_col.metric("Annual saving", f"{retrofit['annual_kwh_saving']:+,.0f} kWh")
    carbon_col.metric("Carbon saving", f"{retrofit['annual_co2_saving']:+,.0f} kg CO2e")

    if retrofit["improved"]:
        st.success(
            f"Measured, not promised: your home now uses "
            f"{abs(retrofit['sensitivity_change']):.2f} kWh less for every "
            f"heating degree day, worth about "
            f"{abs(retrofit['annual_kwh_saving']):,.0f} kWh a year."
        )
    else:
        st.warning(
            "The fitted sensitivity has not improved. Either the work has not "
            "had an effect that shows in the meter, or the readings since do "
            "not yet cover enough cold weather to tell."
        )

    if abs(retrofit["baseload_change_kwh"]) > 100:
        st.info(
            f"Your baseload also changed by "
            f"{retrofit['baseload_change_kwh']:+,.0f} kWh a year. That is not "
            f"the retrofit — it is appliances, occupancy or hot water, and it "
            f"is reported separately so it cannot flatter the fabric result."
        )

    if retrofit["note"]:
        st.warning(retrofit["note"])

    for item in baselines:
        detail_col, delete_col = st.columns([5, 1])
        with detail_col:
            st.markdown(
                f"**{item['name']}** — baseload {item['baseload']:,.0f} kWh/month, "
                f"{item['sensitivity']:.2f} kWh/HDD, R²={item['r_squared']:.2f} "
                f"{'✅' if item['is_reliable'] else '⚠️'} · {item['created_at']}"
            )
        with delete_col:
            if st.button("Delete", key=f"delete_baseline_{item['id']}"):
                delete_baseline(user_id, item["id"])
                st.rerun()

st.markdown("---")
st.caption(
    "Method: consumption is regressed against heating degree days as "
    "kWh = baseload + sensitivity × HDD, the standard approach in CIBSE TM41 "
    "and ASHRAE Guideline 14. Degree days are recovered from monthly mean "
    "temperatures using Hitchin's formula. Two parameters fitted to twelve "
    "points is a small model, which is why the R² is reported prominently and "
    "a poor fit is called out rather than quietly reported as fact."
)
