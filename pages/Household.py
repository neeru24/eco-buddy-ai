import streamlit as st
import pandas as pd
import plotly.express as px

from household import (
    ALLOCATION_METHODS,
    MAX_WEIGHT,
    MEMBER_ROLES,
    MIN_WEIGHT,
    PERSONAL_CATEGORIES,
    REGIONAL_PER_CAPITA_KG,
    SHARED_CATEGORIES,
    add_member,
    compute_household_footprint,
    create_household,
    delete_household,
    get_households_for_user,
    household_insights,
    join_household,
    per_capita_vs_national,
    rank_members,
    remove_member,
    update_household,
    update_member,
    validate_member_weights,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()

apply_theme()

st.markdown(
    "<div class='section-header'>🏠 Household Carbon Sharing</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "Sharing a home means sharing emissions. Split electricity, water and waste "
    "fairly so everyone sees their real per-person footprint."
)

households = get_households_for_user(user_id)

if not households:
    st.markdown("---")
    st.info("You are not part of a household yet. Create one, or join with a code.")

    create_tab, join_tab = st.tabs(["Create a household", "Join with a code"])

    with create_tab:
        with st.form("create_household_form"):
            new_name = st.text_input("Household name", value="My household")
            new_region = st.selectbox("Region", list(REGIONAL_PER_CAPITA_KG.keys()))
            your_name = st.text_input("Your display name", value="Me")
            if st.form_submit_button("Create household", use_container_width=True):
                household_id = create_household(new_name, user_id, region=new_region)
                if household_id:
                    add_member(household_id, your_name, user_id=user_id)
                    st.success("Household created.")
                    st.rerun()
                else:
                    st.error("Could not create the household. Please try again.")

    with join_tab:
        with st.form("join_household_form"):
            code = st.text_input("Join code", placeholder="e.g. K7QM2X")
            display_name = st.text_input("Your display name", value="Me")
            if st.form_submit_button("Join household", use_container_width=True):
                joined, message = join_household(code, user_id, display_name)
                if joined:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    st.stop()

household_labels = {f"{h['name']} ({h['join_code']})": h for h in households}
selected_label = st.selectbox("Household", list(household_labels))
household = household_labels[selected_label]
members = household["members"]

st.markdown("---")
top_left, top_right = st.columns([2, 1])
with top_left:
    st.markdown(f"### {household['name']}")
    st.caption(f"Members: {len(members)} · Region: {household['region']}")
with top_right:
    st.metric("Join code", household["join_code"])
    st.caption("Share this code with the people you live with.")

st.markdown("### 👥 Members")

valid, message = validate_member_weights(members)
if not valid:
    st.warning(message)

for member in members:
    name_col, weight_col, role_col, action_col = st.columns([2, 2, 2, 1])
    name_col.markdown(f"**{member['name']}**")
    new_weight = weight_col.slider(
        "Occupancy weight",
        min_value=MIN_WEIGHT,
        max_value=3.0,
        value=float(min(member["weight"], 3.0)),
        step=0.1,
        key=f"weight_{member['id']}",
        label_visibility="collapsed",
        help=f"How much of the home this person uses. 1.0 is a full-time resident (max {MAX_WEIGHT}).",
    )
    new_role = role_col.selectbox(
        "Role",
        MEMBER_ROLES,
        index=MEMBER_ROLES.index(member["role"]) if member["role"] in MEMBER_ROLES else 0,
        key=f"role_{member['id']}",
        label_visibility="collapsed",
    )
    if new_weight != member["weight"] or new_role != member["role"]:
        update_member(member["id"], weight=new_weight, role=new_role)
        st.rerun()
    if action_col.button("🗑️", key=f"remove_{member['id']}", help="Remove member"):
        remove_member(member["id"])
        st.rerun()

with st.form("add_member_form", clear_on_submit=True):
    add_name, add_weight, add_role = st.columns([2, 2, 2])
    member_name = add_name.text_input("Name", placeholder="Flatmate")
    member_weight = add_weight.number_input(
        "Occupancy weight", min_value=MIN_WEIGHT, max_value=MAX_WEIGHT, value=1.0, step=0.1
    )
    member_role = add_role.selectbox("Role", MEMBER_ROLES)
    if st.form_submit_button("➕ Add member", use_container_width=True):
        if add_member(household["id"], member_name, member_weight, member_role):
            st.rerun()
        else:
            st.error("Could not add that member - names must be unique and non-empty.")

st.markdown("---")
st.markdown("### ⚖️ How should shared emissions be split?")

method_keys = list(ALLOCATION_METHODS)
method = st.radio(
    "Allocation method",
    method_keys,
    index=method_keys.index(household["allocation_method"]),
    format_func=lambda key: ALLOCATION_METHODS[key],
    horizontal=True,
)
if method != household["allocation_method"]:
    update_household(household["id"], method=method)

st.markdown("### 🏘️ Shared Household Emissions (kg CO₂ per year)")
shared_inputs = {}
shared_columns = st.columns(len(SHARED_CATEGORIES))
for index, (key, info) in enumerate(SHARED_CATEGORIES.items()):
    shared_inputs[key] = shared_columns[index].number_input(
        f"{info['icon']} {info['label']}",
        min_value=0.0,
        max_value=100000.0,
        value=800.0 if key == "electricity" else 200.0,
        step=50.0,
        key=f"shared_{key}",
    )

usage_readings = {}
if method == "usage":
    st.markdown("#### Measured usage per member")
    st.caption(
        "Enter any per-member reading (sub-meter kWh, days at home, ...). "
        "Members left at zero share the remainder equally."
    )
    usage_columns = st.columns(max(1, len(members)))
    for index, member in enumerate(members):
        usage_readings[member["name"]] = usage_columns[index % len(usage_columns)].number_input(
            member["name"], min_value=0.0, value=0.0, step=1.0, key=f"usage_{member['id']}"
        )

st.markdown("### 🙋 Personal Emissions (kg CO₂ per year)")
personal_by_member = {}
for member in members:
    with st.expander(f"{member['name']}'s personal categories"):
        personal_columns = st.columns(len(PERSONAL_CATEGORIES))
        personal = {}
        for index, (key, info) in enumerate(PERSONAL_CATEGORIES.items()):
            personal[key] = personal_columns[index].number_input(
                f"{info['icon']} {info['label']}",
                min_value=0.0,
                max_value=100000.0,
                value=0.0,
                step=50.0,
                key=f"personal_{member['id']}_{key}",
            )
        personal_by_member[member["name"]] = personal

breakdown = compute_household_footprint(
    members, shared_inputs, personal_by_member, method, usage_readings
)

st.markdown("---")
st.markdown("### 📊 Household Breakdown")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Household total", f"{breakdown['household_total_kg']:,.0f} kg")
m2.metric("Shared", f"{breakdown['shared_total_kg']:,.0f} kg")
m3.metric("Personal", f"{breakdown['personal_total_kg']:,.0f} kg")
m4.metric("Per person", f"{breakdown['per_capita_kg']:,.0f} kg")

if breakdown["members"]:
    stacked = pd.DataFrame(
        [
            {"Member": row["name"], "Type": "Shared", "kg CO₂": row["shared_kg"]}
            for row in breakdown["members"]
        ]
        + [
            {"Member": row["name"], "Type": "Personal", "kg CO₂": row["personal_kg"]}
            for row in breakdown["members"]
        ]
    )
    fig = px.bar(
        stacked,
        x="Member",
        y="kg CO₂",
        color="Type",
        barmode="stack",
        color_discrete_map={"Shared": "#4ade80", "Personal": "#38bdf8"},
    )
    fig.add_hline(
        y=breakdown["per_capita_kg"],
        line_dash="dash",
        line_color="#f97316",
        annotation_text="household average",
    )
    fig.update_layout(height=380, margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Position": row["position"],
                    "Member": row["name"],
                    "Total kg CO₂": row["total_kg"],
                    "vs average": f"{row['gap_kg']:+.0f} kg ({row['gap_pct']:+.0f}%)",
                }
                for row in rank_members(breakdown)
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

for insight in household_insights(breakdown):
    st.markdown(f"- {insight}")

st.markdown("---")
st.markdown("### 🌍 Per-Capita Context")

region = st.selectbox(
    "Compare against",
    list(REGIONAL_PER_CAPITA_KG.keys()),
    index=list(REGIONAL_PER_CAPITA_KG.keys()).index(household["region"]),
)
if region != household["region"]:
    update_household(household["id"], region=region)

context = per_capita_vs_national(breakdown["per_capita_kg"], region)
if context["below_average"]:
    st.success(
        f"Each person here emits {abs(context['difference_kg']):,.0f} kg "
        f"({abs(context['difference_pct'])}%) less than the {context['region']} average "
        f"of {context['baseline_kg']:,.0f} kg."
    )
else:
    st.warning(
        f"Each person here emits {context['difference_kg']:,.0f} kg "
        f"({context['difference_pct']}%) more than the {context['region']} average "
        f"of {context['baseline_kg']:,.0f} kg."
    )

if household["owner_user_id"] == user_id:
    st.markdown("---")
    with st.expander("⚠️ Danger zone"):
        st.caption("Deleting a household removes all of its members for everyone.")
        if st.button("Delete this household", key="delete_household"):
            delete_household(household["id"])
            st.rerun()
