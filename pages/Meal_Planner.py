import streamlit as st
import pandas as pd
import plotly.express as px

from meal_planner import (
    DAYS_OF_WEEK,
    DIET_DAILY_BASELINE_KG,
    MEAL_SLOTS,
    TIER_ICONS,
    apply_swaps,
    build_meal,
    compare_to_baseline,
    delete_meal_plan,
    deserialize_plan,
    empty_week,
    generate_shopping_list,
    get_meal_plans,
    get_plan_history,
    heaviest_meals,
    list_ingredients,
    plan_insights,
    plan_week,
    save_meal_plan,
    score_plan,
    suggest_swaps,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🍽️ Eco Meal Planner</div>", unsafe_allow_html=True
)
st.markdown(
    "Plan your week, see the carbon and water cost of every meal, and swap the "
    "heaviest ingredients before you shop."
)

if "meal_plan_week" not in st.session_state:
    st.session_state.meal_plan_week = empty_week()

week = st.session_state.meal_plan_week

st.markdown("---")
st.markdown("### ➕ Add a Meal")

with st.form("add_meal_form", clear_on_submit=True):
    form_top = st.columns([2, 1, 1])
    meal_name = form_top[0].text_input("Meal name", placeholder="e.g. Lentil curry")
    meal_day = form_top[1].selectbox("Day", DAYS_OF_WEEK)
    meal_slot = form_top[2].selectbox("Slot", MEAL_SLOTS, index=2)

    st.caption("Pick up to five ingredients and their portion size in grams.")
    ingredient_names = [item["name"] for item in list_ingredients()]

    chosen = []
    for row in range(5):
        pick_col, gram_col = st.columns([2, 1])
        ingredient = pick_col.selectbox(
            f"Ingredient {row + 1}",
            ["— none —"] + ingredient_names,
            key=f"meal_ingredient_{row}",
        )
        grams = gram_col.number_input(
            f"Grams {row + 1}",
            min_value=0.0,
            max_value=2000.0,
            value=150.0 if row == 0 else 0.0,
            step=25.0,
            key=f"meal_grams_{row}",
        )
        if ingredient != "— none —" and grams > 0:
            chosen.append((ingredient, grams))

    if st.form_submit_button("Add meal to plan", use_container_width=True):
        if not chosen:
            st.warning("Choose at least one ingredient with a portion size.")
        else:
            week[meal_day].append(build_meal(meal_name, chosen, meal_slot))
            st.session_state.meal_plan_week = week
            st.success(f"Added **{meal_name or 'Untitled meal'}** to {meal_day}.")

st.markdown("---")
st.markdown("### 🗓️ Your Week")

weekly = plan_week(week)

if weekly["meal_count"] == 0:
    st.info("No meals planned yet. Add one above to see your week's footprint.")
else:
    scored = score_plan(weekly)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Weekly CO₂", f"{weekly['total_co2_kg']:,.1f} kg")
    m2.metric("Virtual water", f"{weekly['total_water_l']:,.0f} L")
    m3.metric("Daily average", f"{weekly['avg_daily_co2_kg']:,.2f} kg")
    m4.metric("Plan score", f"{scored['score']} ({scored['grade']})")
    st.caption(scored["label"])

    diet_type = st.selectbox(
        "Compare against a typical week for a…",
        list(DIET_DAILY_BASELINE_KG.keys()),
        index=list(DIET_DAILY_BASELINE_KG.keys()).index("Omnivore"),
    )
    comparison = compare_to_baseline(weekly, diet_type)
    if comparison["better_than_baseline"]:
        st.success(
            f"Your plan is {abs(comparison['difference_kg']):.1f} kg CO₂ "
            f"({abs(comparison['difference_pct'])}%) below a typical "
            f"{comparison['diet_type'].lower()} week."
        )
    else:
        st.warning(
            f"Your plan is {comparison['difference_kg']:.1f} kg CO₂ "
            f"({comparison['difference_pct']}%) above a typical "
            f"{comparison['diet_type'].lower()} week."
        )

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.markdown("#### Carbon by day")
        day_df = pd.DataFrame(
            [
                {"Day": info["day"], "kg CO₂": info["co2_kg"]}
                for info in weekly["daily"].values()
            ]
        )
        bar = px.bar(day_df, x="Day", y="kg CO₂", color="kg CO₂",
                     color_continuous_scale="Greens")
        bar.update_layout(
            height=340, coloraxis_showscale=False,
            margin=dict(l=10, r=10, t=30, b=10),
        )
        st.plotly_chart(bar, use_container_width=True)

    with chart_right:
        st.markdown("#### Carbon by category")
        cat_df = pd.DataFrame(
            [
                {"Category": category, "kg CO₂": value}
                for category, value in weekly["by_category"].items()
                if value > 0
            ]
        )
        if cat_df.empty:
            st.caption("No ingredients recorded yet.")
        else:
            pie = px.pie(
                cat_df, names="Category", values="kg CO₂", hole=0.45,
                color_discrete_sequence=px.colors.sequential.Greens_r,
            )
            pie.update_layout(height=340, margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(pie, use_container_width=True)

    for insight in plan_insights(weekly):
        st.markdown(f"- {insight}")

    st.markdown("---")
    st.markdown("### 🔁 Swap Suggestions")
    st.caption("Your heaviest meals, and the single biggest swap available in each.")

    for meal in heaviest_meals(week, limit=3):
        swaps = suggest_swaps(meal, max_suggestions=3)
        header = (
            f"{TIER_ICONS.get(meal['tier'], '🟢')} {meal['day']} · "
            f"{meal['name']} — {meal['co2_kg']:.2f} kg CO₂"
        )
        with st.expander(header):
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Ingredient": item["ingredient"],
                            "Grams": item["grams"],
                            "kg CO₂": item["co2_kg"],
                            "Water (L)": item["water_l"],
                            "Share %": item["co2_share_pct"],
                        }
                        for item in meal["contributions"]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

            if not swaps:
                st.caption("This meal already uses the lowest-impact option in every category.")
                continue

            swapped = apply_swaps(meal, swaps)
            for swap in swaps:
                st.markdown(
                    f"- **{swap['from']} → {swap['to']}** saves "
                    f"{swap['co2_saved_kg']:.2f} kg CO₂ and "
                    f"{swap['water_saved_l']:,.0f} L of water"
                )
            st.success(
                f"Applying all three: {meal['co2_kg']:.2f} kg → "
                f"{swapped['co2_kg']:.2f} kg CO₂"
            )

    st.markdown("---")
    st.markdown("### 🛒 Shopping List")
    shopping = generate_shopping_list(weekly)
    list_columns = st.columns(min(3, max(1, len(shopping))))
    for index, (category, items) in enumerate(shopping.items()):
        with list_columns[index % len(list_columns)]:
            st.markdown(f"**{category}**")
            for item in items:
                st.markdown(
                    f"{TIER_ICONS.get(item['tier'], '🟢')} {item['ingredient']} — "
                    f"{item['grams']:,.0f} g"
                )

    st.markdown("---")
    save_col, clear_col = st.columns(2)
    with save_col:
        plan_name = st.text_input("Plan name", value="My week", key="meal_plan_name")
        if st.button("💾 Save Plan", use_container_width=True):
            if save_meal_plan(user_id, plan_name, week):
                st.success("Meal plan saved.")
            else:
                st.error("Could not save this plan. Please try again.")
    with clear_col:
        st.markdown("&nbsp;", unsafe_allow_html=True)
        if st.button("🧹 Clear Week", use_container_width=True):
            st.session_state.meal_plan_week = empty_week()
            st.rerun()

st.markdown("---")
st.markdown("### 📚 Saved Plans")

saved_plans = get_meal_plans(user_id)
if not saved_plans:
    st.caption("No saved plans yet. Build a week above and save it to compare later.")
else:
    history = get_plan_history(user_id)
    if history["entries"] >= 2:
        trend_df = pd.DataFrame(history["series"])
        line = px.line(
            trend_df, x="date", y="total_co2_kg", markers=True,
            labels={"date": "Saved on", "total_co2_kg": "kg CO₂ per week"},
        )
        line.update_traces(line_color="#4ade80")
        line.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(line, use_container_width=True)
        st.caption(f"Best plan score so far: **{history['best_score']}/100**")

    for plan in saved_plans:
        with st.expander(
            f"{plan['plan_name']} — {plan['total_co2_kg']:,.1f} kg CO₂ "
            f"(score {plan['score']}, grade {plan['grade']}) · {plan['created_at']}"
        ):
            restored = deserialize_plan(plan["plan"])
            rows = [
                {
                    "Day": day,
                    "Meal": meal["name"],
                    "Slot": meal["slot"],
                    "kg CO₂": meal["co2_kg"],
                    "Water (L)": meal["water_l"],
                }
                for day in DAYS_OF_WEEK
                for meal in restored[day]
            ]
            if rows:
                st.dataframe(
                    pd.DataFrame(rows), use_container_width=True, hide_index=True
                )

            action_left, action_right = st.columns(2)
            if action_left.button("📥 Load Into Planner", key=f"load_plan_{plan['id']}"):
                st.session_state.meal_plan_week = restored
                st.rerun()
            if action_right.button("🗑️ Delete", key=f"delete_plan_{plan['id']}"):
                delete_meal_plan(plan["id"])
                st.rerun()
