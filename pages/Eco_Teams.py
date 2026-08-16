import streamlit as st
import pandas as pd
from eco_teams import (
    TEAM_CHALLENGE_TYPES,
    create_team,
    join_team,
    leave_team,
    get_user_teams,
    get_team_info,
    get_team_members,
    get_team_footprint,
    create_team_challenge,
    get_team_challenges,
    update_challenge_progress,
    get_team_leaderboard,
    get_within_team_contributions,
    get_team_badges,
    transfer_ownership,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🤝 Community Eco-Teams</div>", unsafe_allow_html=True)
st.markdown(
    "Form teams with friends, family, or coworkers to tackle emissions together. "
    "Share invite codes, launch group challenges, and climb the leaderboards."
)

my_teams = get_user_teams(user_id)

# --- CREATE / JOIN TEAM ---
if not my_teams:
    st.info("You're not on a team yet. Create one or join with an invite code.")
    tab1, tab2 = st.tabs(["🆕 Create Team", "🔗 Join Team"])
    with tab1:
        with st.form("create_team"):
            name = st.text_input("Team Name", placeholder="e.g., Green Guardians")
            desc = st.text_area("Description (optional)", placeholder="Family sustainability squad")
            if st.form_submit_button("Create Team", type="primary"):
                if name.strip():
                    team = create_team(user_id, name.strip(), desc.strip())
                    if team:
                        st.success(f"Team '{team['name']}' created! Invite code: **{team['invite_code']}**")
                        st.rerun()
                    else:
                        st.error("Could not create team.")
                else:
                    st.warning("Team name is required.")
    with tab2:
        with st.form("join_team"):
            code = st.text_input("Invite Code", placeholder="ABC123XY").upper()
            if st.form_submit_button("Join Team", type="primary"):
                if code.strip():
                    ok, msg = join_team(user_id, code.strip())
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
                else:
                    st.warning("Enter an invite code.")
    st.stop()

# --- TEAM TABS ---
team_tabs = []
for team in my_teams:
    team_tabs.append(f"{team['name']} ({'👑' if team['role'] == 'owner' else '👤'})")

selected_idx = st.tabs(team_tabs).index(st.session_state.get("selected_team_tab", 0))
if selected_idx != st.session_state.get("selected_team_tab", 0):
    st.session_state.selected_team_tab = selected_idx
    st.rerun()

team = my_teams[selected_idx]
team_id = team["id"]
info = get_team_info(team_id)
members = get_team_members(team_id)
footprint = get_team_footprint(team_id)

st.markdown(f"### {info['name']} {'👑' if team['role'] == 'owner' else ''}")
if info["description"]:
    st.caption(info["description"])
st.code(f"Invite Code: {info['invite_code']}", language=None)
st.caption(f"Created: {info['created_at'][:10]} | Members: {len(members)}")

# --- TEAM FOOTPRINT ---
st.markdown("---")
st.markdown("#### 📊 Team Footprint")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total CO₂e", f"{footprint['total_footprint_kg']} kg")
c2.metric("Per Capita", f"{footprint['per_capita_kg']} kg")
c3.metric("Transport", f"{footprint['transport_kg']} kg")
c4.metric("Energy", f"{footprint['energy_kg']} kg")
c1.metric("Waste", f"{footprint['waste_kg']} kg")
c2.metric("Water", f"{footprint['water_liters']} L")

# --- MEMBERS ---
st.markdown("#### 👥 Members")
member_data = []
for m in members:
    fp = footprint["contributions"].get(m["user_id"], {"footprint_kg": 0, "waste_kg": 0})
    member_data.append({
        "Role": "👑 Owner" if m["role"] == "owner" else "👤 Member",
        "User ID": m["user_id"],
        "Footprint (kg)": fp["footprint_kg"],
        "Waste CO₂e (kg/wk)": fp["waste_kg"],
        "Joined": m["joined_at"][:10],
    })
st.dataframe(pd.DataFrame(member_data), use_container_width=True, hide_index=True)

# Owner actions
if team["role"] == "owner":
    st.markdown("**Owner Actions:**")
    oc1, oc2 = st.columns(2)
    with oc1:
        new_owner = st.selectbox("Transfer ownership to:", [m["user_id"] for m in members if m["user_id"] != user_id],
                                  format_func=lambda uid: f"User {uid}")
        if st.button("Transfer Ownership"):
            ok, msg = transfer_ownership(team_id, user_id, new_owner)
            (st.success if ok else st.error)(msg)
            if ok: st.rerun()
    with oc2:
        if st.button("⚠️ Delete Team", type="secondary"):
            st.warning("Team deletion not implemented — contact admin.")

# --- CHALLENGES ---
st.markdown("---")
st.markdown("#### 🎯 Team Challenges")

active_challenges = get_team_challenges(team_id, status="active")
completed_challenges = get_team_challenges(team_id, status="completed")

if active_challenges:
    for ch in active_challenges:
        info = TEAM_CHALLENGE_TYPES.get(ch["challenge_type"], {})
        label = info.get("title", ch["challenge_type"])
        unit = info.get("unit", "")
        icon = info.get("icon", "🎯")
        progress = min(ch["current_value"] / ch["target_value"], 1.0) if ch["target_value"] > 0 else 0

        st.markdown(f"**{icon} {label}** — {ch['current_value']:.1f}/{ch['target_value']:.1f} {unit}")
        st.progress(progress)
        st.caption(f"Reward: {ch['reward_xp']} XP each | Ends: {ch['ends_at'][:10]}")

        # Contribute
        c1, c2 = st.columns([3, 1])
        val = c1.number_input("Your contribution", min_value=0.0, step=0.1, key=f"contrib_{ch['id']}")
        if c2.button("Add", key=f"add_{ch['id']}"):
            ok = update_challenge_progress(team_id, ch["id"], user_id, val)
            if ok:
                st.success("Contribution recorded!")
                st.rerun()
            else:
                st.error("Could not record contribution.")

if completed_challenges:
    with st.expander("✅ Completed Challenges"):
        for ch in completed_challenges:
            info = TEAM_CHALLENGE_TYPES.get(ch["challenge_type"], {})
            label = info.get("title", ch["challenge_type"])
            st.write(f"✅ {label} — finished {ch['completed_at'][:10]}, {ch['reward_xp']} XP awarded")

# Create new challenge
if team["role"] == "owner":
    with st.expander("➕ Launch New Challenge"):
        with st.form("new_challenge"):
            ct = st.selectbox("Type", list(TEAM_CHALLENGE_TYPES.keys()),
                              format_func=lambda k: f"{TEAM_CHALLENGE_TYPES[k]['icon']} {TEAM_CHALLENGE_TYPES[k]['title']} ({TEAM_CHALLENGE_TYPES[k]['unit']})")
            target = st.number_input("Target value", min_value=1.0, value=100.0, step=10.0)
            days = st.slider("Duration (days)", 1, 30, 7)
            xp = st.number_input("XP reward per member", min_value=10, value=100, step=10)
            if st.form_submit_button("Launch Challenge"):
                ch = create_team_challenge(team_id, ct, target, days, xp)
                if ch:
                    st.success("Challenge launched!")
                    st.rerun()
                else:
                    st.error("Could not create challenge.")

# --- BADGES ---
st.markdown("---")
st.markdown("#### 🏅 Team Badges")
badges = get_team_badges(team_id)
if badges:
    cols = st.columns(min(len(badges), 4))
    for i, b in enumerate(badges):
        with cols[i % len(cols)]:
            st.markdown(f"**{b['name']}**")
            st.caption(b["description"])
            st.caption(f"Earned: {b['earned_at'][:10]}")
else:
    st.info("No team badges yet — complete a challenge to earn your first!")

# --- LEADERBOARDS ---
st.markdown("---")
lb_tab1, lb_tab2 = st.tabs(["🏆 Global Team Leaderboard", "📈 Within-Team Contributions"])

with lb_tab1:
    board = get_team_leaderboard()
    if board:
        st.dataframe(pd.DataFrame([{
            "Rank": i + 1,
            "Team": row["name"],
            "Members": row["members"],
            "Per Capita (kg)": row["per_capita_kg"],
            "Total (kg)": row["total_footprint_kg"],
        } for i, row in enumerate(board)]), use_container_width=True, hide_index=True)
    else:
        st.info("No teams on the leaderboard yet.")

with lb_tab2:
    contribs = get_within_team_contributions(team_id)
    if contribs:
        st.dataframe(pd.DataFrame([{
            "Rank": i + 1,
            "User ID": c["user_id"],
            "Role": c["role"],
            "Footprint (kg)": c["footprint_kg"],
            "Waste CO₂e (kg)": c["waste_kg"],
            "Total (kg)": c["total_contribution_kg"],
        } for i, c in enumerate(contribs)]), use_container_width=True, hide_index=True)
    else:
        st.info("No contribution data yet.")

# --- LEAVE TEAM ---
if team["role"] == "member":
    st.markdown("---")
    if st.button("🚪 Leave Team", type="secondary"):
        ok, msg = leave_team(user_id, team_id)
        (st.success if ok else st.error)(msg)
        if ok: st.rerun()