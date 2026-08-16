import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Food Impact Explorer",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================================
# DATA
# Relative illustrative values for UI/demo purposes
# ============================================================

FOOD_DATA = {
    "🥩 Beef": {
        "category": "Meat",
        "carbon": 60.0,
        "water": 15000,
        "land": 27.0,
        "impact": "Very High",
        "level": 4,
        "alternative": "🫘 Lentils",
        "description": "Beef generally has a high environmental footprint."
    },
    "🐑 Lamb": {
        "category": "Meat",
        "carbon": 24.0,
        "water": 10000,
        "land": 21.0,
        "impact": "Very High",
        "level": 4,
        "alternative": "🫘 Beans",
        "description": "Lamb production can have a significant environmental impact."
    },
    "🍗 Chicken": {
        "category": "Meat",
        "carbon": 7.0,
        "water": 4300,
        "land": 8.0,
        "impact": "Medium",
        "level": 2,
        "alternative": "🫘 Lentils",
        "description": "Chicken generally has a lower footprint than beef and lamb."
    },
    "🐟 Fish": {
        "category": "Seafood",
        "carbon": 6.0,
        "water": 3000,
        "land": 5.0,
        "impact": "Medium",
        "level": 2,
        "alternative": "🌱 Tofu",
        "description": "Fish impacts vary significantly by species and fishing method."
    },
    "🥚 Eggs": {
        "category": "Animal Products",
        "carbon": 4.5,
        "water": 3300,
        "land": 5.5,
        "impact": "Low–Medium",
        "level": 2,
        "alternative": "🫘 Beans",
        "description": "Eggs generally have a lower footprint than many meats."
    },
    "🥛 Dairy": {
        "category": "Animal Products",
        "carbon": 3.2,
        "water": 6000,
        "land": 4.0,
        "impact": "Medium",
        "level": 2,
        "alternative": "🌱 Plant-based alternative",
        "description": "Dairy impacts depend on production systems and product type."
    },
    "🍚 Rice": {
        "category": "Grains",
        "carbon": 2.7,
        "water": 2500,
        "land": 2.5,
        "impact": "Low–Medium",
        "level": 2,
        "alternative": "🌾 Other grains",
        "description": "Rice can have a higher footprint than some other grains."
    },
    "🫘 Lentils": {
        "category": "Plant Protein",
        "carbon": 0.9,
        "water": 1250,
        "land": 0.9,
        "impact": "Very Low",
        "level": 1,
        "alternative": "🥗 Vegetables",
        "description": "Lentils are generally a lower-impact source of protein."
    },
    "🌱 Tofu": {
        "category": "Plant Protein",
        "carbon": 2.0,
        "water": 2000,
        "land": 3.5,
        "impact": "Low",
        "level": 1,
        "alternative": "🫘 Lentils",
        "description": "Tofu is generally a lower-impact protein option."
    },
    "🥦 Vegetables": {
        "category": "Vegetables",
        "carbon": 0.5,
        "water": 300,
        "land": 0.4,
        "impact": "Very Low",
        "level": 1,
        "alternative": "🥦 Seasonal vegetables",
        "description": "Many vegetables have relatively low environmental impacts."
    }
}


st.markdown("""
<style>

.block-container {
    max-width: 1200px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

/* Hero */
.hero {
    padding: 2.5rem;
    border-radius: 24px;
    margin-bottom: 2rem;
    background: linear-gradient(
        135deg,
        rgba(34, 197, 94, 0.18),
        rgba(16, 185, 129, 0.08)
    );
    border: 1px solid rgba(34, 197, 94, 0.25);
}

.hero-title {
    font-size: 3rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

.hero-text {
    font-size: 1.1rem;
    opacity: 0.8;
    max-width: 750px;
}

/* Cards */
.impact-card {
    padding: 1.4rem;
    border-radius: 18px;
    border: 1px solid rgba(128,128,128,0.18);
    background: rgba(128,128,128,0.05);
    min-height: 150px;
}

.metric-icon {
    font-size: 2rem;
}

.metric-title {
    font-size: 0.95rem;
    opacity: 0.7;
}

.metric-value {
    font-size: 1.7rem;
    font-weight: 750;
}

/* Impact badge */
.impact-badge {
    display: inline-block;
    padding: 0.45rem 0.9rem;
    border-radius: 999px;
    font-weight: 700;
    margin-top: 0.5rem;
}

/* Comparison */
.compare-card {
    padding: 1.5rem;
    border-radius: 20px;
    border: 1px solid rgba(128,128,128,0.18);
}

/* Section */
.section-title {
    font-size: 1.8rem;
    font-weight: 750;
    margin-top: 2rem;
    margin-bottom: 0.4rem;
}

.section-subtitle {
    opacity: 0.7;
    margin-bottom: 1.2rem;
}

/* Tip */
.tip-card {
    padding: 1.2rem;
    border-radius: 16px;
    border: 1px solid rgba(128,128,128,0.18);
    background: rgba(128,128,128,0.04);
}

</style>
""", unsafe_allow_html=True)

# ============================================================
# HERO
# ============================================================

st.markdown("""
<div class="hero">

<div class="hero-title">
🍽️ Food Impact Explorer
</div>

<div class="hero-text">
Discover how different food choices can influence carbon emissions,
water use and land use. Explore foods, compare alternatives and build
a lower-impact meal.
</div>

</div>
""", unsafe_allow_html=True)

# ============================================================
# FOOD SELECTOR
# ============================================================

st.markdown(
    '<div class="section-title">🔎 Explore a Food</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Choose a food to explore its environmental impact.'
    '</div>',
    unsafe_allow_html=True
)

selected_food = st.selectbox(
    "Select a food",
    list(FOOD_DATA.keys())
)

food = FOOD_DATA[selected_food]

# ============================================================
# MAIN FOOD SUMMARY
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="impact-card">
        <div class="metric-icon">🌍</div>
        <div class="metric-title">Carbon footprint</div>
        <div class="metric-value">%.1f kg</div>
        <small>CO₂e / kg food</small>
    </div>
    """ % food["carbon"], unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="impact-card">
        <div class="metric-icon">💧</div>
        <div class="metric-title">Water use</div>
        <div class="metric-value">%,d L</div>
        <small>Approx. water use / kg</small>
    </div>
    """ % food["water"], unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="impact-card">
        <div class="metric-icon">🌱</div>
        <div class="metric-title">Land use</div>
        <div class="metric-value">%.1f m²</div>
        <small>Land use indicator</small>
    </div>
    """ % food["land"], unsafe_allow_html=True)

with col4:

    badge_class = (
        "impact-high"
        if food["level"] >= 4
        else "impact-medium"
        if food["level"] == 2
        else "impact-low"
    )

    st.markdown(f"""
    <div class="impact-card">
        <div class="metric-icon">🌎</div>
        <div class="metric-title">Overall impact</div>
        <div class="metric-value">{food["impact"]}</div>
        <div class="impact-badge {badge_class}">
            Level {food["level"]}/4
        </div>
    </div>
    """, unsafe_allow_html=True)

st.info(food["description"])

# ============================================================
# IMPACT CHART
# ============================================================

st.markdown(
    '<div class="section-title">📊 Environmental Impact Profile</div>',
    unsafe_allow_html=True
)

chart_data = pd.DataFrame({
    "Impact": [
        "Carbon",
        "Water",
        "Land"
    ],
    "Relative Impact": [
        food["carbon"],
        food["water"] / 250,
        food["land"]
    ]
})

fig = px.bar(
    chart_data,
    x="Relative Impact",
    y="Impact",
    orientation="h",
    text="Relative Impact"
)

fig.update_layout(
    height=330,
    margin=dict(l=10, r=10, t=20, b=20),
    showlegend=False,
    xaxis_title="Relative impact",
    yaxis_title=""
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# ============================================================
# COMPARE FOODS
# ============================================================

st.markdown(
    '<div class="section-title">⚖️ Compare Food Choices</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'See how two food choices differ across environmental indicators.'
    '</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)

with c1:
    food_a_name = st.selectbox(
        "Food A",
        list(FOOD_DATA.keys()),
        index=list(FOOD_DATA.keys()).index(selected_food)
    )

with c2:
    food_b_name = st.selectbox(
        "Food B",
        list(FOOD_DATA.keys()),
        index=7
    )

food_a = FOOD_DATA[food_a_name]
food_b = FOOD_DATA[food_b_name]

comparison_df = pd.DataFrame({
    "Food": [food_a_name, food_b_name],
    "Carbon": [food_a["carbon"], food_b["carbon"]],
    "Water": [
        food_a["water"] / 1000,
        food_b["water"] / 1000
    ],
    "Land": [food_a["land"], food_b["land"]]
})

fig_compare = px.bar(
    comparison_df,
    x="Food",
    y=["Carbon", "Water", "Land"],
    barmode="group",
    title="Relative Environmental Comparison"
)

fig_compare.update_layout(
    height=400,
    margin=dict(l=10, r=10, t=60, b=20)
)

st.plotly_chart(
    fig_compare,
    use_container_width=True
)

# ============================================================
# LOWER IMPACT ALTERNATIVE
# ============================================================

st.markdown(
    '<div class="section-title">🌱 Try a Lower-Impact Alternative</div>',
    unsafe_allow_html=True
)

alternative = food["alternative"]

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown(f"""
    <div class="compare-card">
        <h3>{selected_food}</h3>
        <p>Current choice</p>
        <strong>{food["impact"]} impact</strong>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.success(
        f"💡 Consider trying **{alternative}** as an alternative. "
        "Plant-based foods are often lower-impact choices, although "
        "the actual impact depends on production and sourcing."
    )

# ============================================================
# MEAL BUILDER
# ============================================================

st.markdown(
    '<div class="section-title">🍽️ Build Your Meal</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-subtitle">'
    'Create a simple meal and see its combined relative impact.'
    '</div>',
    unsafe_allow_html=True
)

meal_col1, meal_col2, meal_col3 = st.columns(3)

with meal_col1:
    protein = st.selectbox(
        "🥩 Protein",
        [
            "🥩 Beef",
            "🍗 Chicken",
            "🐟 Fish",
            "🥚 Eggs",
            "🫘 Lentils",
            "🌱 Tofu"
        ]
    )

with meal_col2:
    grain = st.selectbox(
        "🍚 Grain",
        [
            "🍚 Rice",
            "🌾 Other grains"
        ]
    )

with meal_col3:
    vegetable = st.selectbox(
        "🥦 Vegetable",
        [
            "🥦 Vegetables"
        ]
    )

# Handle grain without data entry error
grain_key = "🍚 Rice"

protein_data = FOOD_DATA[protein]
grain_data = FOOD_DATA[grain_key]
vegetable_data = FOOD_DATA[vegetable]

meal_carbon = (
    protein_data["carbon"]
    + grain_data["carbon"]
    + vegetable_data["carbon"]
)

meal_water = (
    protein_data["water"]
    + grain_data["water"]
    + vegetable_data["water"]
)

meal_land = (
    protein_data["land"]
    + grain_data["land"]
    + vegetable_data["land"]
)

meal_score = (
    protein_data["level"]
    + grain_data["level"]
    + vegetable_data["level"]
)

if meal_score >= 9:
    meal_impact = "🔴 High"
elif meal_score >= 6:
    meal_impact = "🟠 Medium"
else:
    meal_impact = "🟢 Low"

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric(
        "🌍 Carbon",
        f"{meal_carbon:.1f} kg CO₂e"
    )

with m2:
    st.metric(
        "💧 Water",
        f"{meal_water:,.0f} L"
    )

with m3:
    st.metric(
        "🌱 Land",
        f"{meal_land:.1f} m²"
    )

with m4:
    st.metric(
        "🌎 Meal Impact",
        meal_impact
    )

# ============================================================
# SMART SUGGESTION
# ============================================================

if protein == "🥩 Beef":

    st.warning(
        "🌱 **Try switching the protein:** "
        "Replacing beef with lentils or tofu can generally lower "
        "the environmental impact of the meal."
    )

elif protein in ["🍗 Chicken", "🐟 Fish", "🥚 Eggs"]:

    st.info(
        "💡 **Small improvement:** "
        "Consider adding more plant-based ingredients to your meal."
    )

else:

    st.success(
        "🌱 **Great choice!** "
        "Your selected protein is generally a lower-impact option."
    )

# ============================================================
# FOOD CATEGORY EXPLORER
# ============================================================

st.markdown(
    '<div class="section-title">📚 Explore Food Categories</div>',
    unsafe_allow_html=True
)

category = st.radio(
    "Choose a category",
    [
        "All",
        "Meat",
        "Seafood",
        "Animal Products",
        "Plant Protein",
        "Grains",
        "Vegetables"
    ],
    horizontal=True
)

if category == "All":
    filtered_foods = FOOD_DATA.items()
else:
    filtered_foods = [
        (name, data)
        for name, data in FOOD_DATA.items()
        if data["category"] == category
    ]

for name, data in filtered_foods:

    with st.expander(f"{name} — {data['impact']} impact"):

        e1, e2, e3 = st.columns(3)

        with e1:
            st.write(f"🌍 Carbon: **{data['carbon']:.1f} kg CO₂e**")

        with e2:
            st.write(f"💧 Water: **{data['water']:,} L**")

        with e3:
            st.write(f"🌱 Land: **{data['land']:.1f} m²**")

# ============================================================
# TIPS
# ============================================================

st.markdown(
    '<div class="section-title">💡 Simple Ways to Reduce Food Impact</div>',
    unsafe_allow_html=True
)

tips = [
    ("🌱", "Include more plant-based proteins such as lentils, beans and tofu."),
    ("🥕", "Choose a variety of seasonal foods where practical."),
    ("♻️", "Reduce food waste by planning meals and storing food properly."),
    ("🍽️", "Choose portions that match what you are likely to eat."),
    ("🌎", "Consider the production method and sourcing of foods when possible.")
]

tip_cols = st.columns(2)

for i, (icon, text) in enumerate(tips):

    with tip_cols[i % 2]:

        st.markdown(f"""
        <div class="tip-card">
            <strong>{icon} {text}</strong>
        </div>
        """, unsafe_allow_html=True)

        st.write("")

# ============================================================
# DISCLAIMER
# ============================================================

st.caption(
    "ℹ️ Environmental impact values shown here are illustrative "
    "relative indicators for exploration and should not be treated "
    "as precise lifecycle-assessment results. Actual impacts vary "
    "by production method, location, season, transport and sourcing."
)