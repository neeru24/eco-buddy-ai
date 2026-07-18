import streamlit as st
import pandas as pd
from database import (
    get_squad_for_user,
    get_squad_members,
    create_squad,
    join_squad_by_code,
    leave_squad,
    get_or_create_user,
    get_username
)
import gamification as gf
from styles.theme import apply_theme

# Apply theme
apply_theme()

st.markdown("<div class='section-header'>👥 Squad Management</div>", unsafe_allow_html=True)

# Initialize active user in session state
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = 1

# Sidebar User Simulator
st.sidebar.markdown("### 👥 User Simulation")
sim_username = st.sidebar.selectbox(
    "Act as user:",
    ["Alice", "Bob", "Charlie", "Dave", "Eve", "The Professor", "Custom..."],
    key="squads_sim_user"
)

if sim_username == "Custom...":
    custom_name = st.sidebar.text_input("Enter custom username:", "NewUser", key="squads_custom_user")
    if custom_name:
        st.session_state.active_user_id = get_or_create_user(custom_name)
else:
    st.session_state.active_user_id = get_or_create_user(sim_username)

user_id = st.session_state.active_user_id
st.sidebar.info(f"Simulating as: **{get_username(user_id)}** (ID: {user_id})")

# Fetch current user squad
my_squad = get_squad_for_user(user_id)

if my_squad:
    st.success(f"You are a member of **{my_squad['name']}**!")
    
    tab1, tab2 = st.tabs(["🛡️ My Squad Details", "👋 Leave Squad"])
    
    with tab1:
        st.markdown(f"### {my_squad['name']}")
        st.write(my_squad['description'] or "No description provided.")
        
        st.info(f"🔑 **Invite Code:** `{my_squad['invite_code']}` (Share this code to invite friends!)")
        
        st.markdown("#### 👥 Squad Roster")
        members = get_squad_members(my_squad['id'])
        if members:
            # Format roster table
            member_list = []
            for m in members:
                role = "👑 Owner/Founder" if m['user_id'] == my_squad['owner_user_id'] else "Member"
                member_list.append({
                    "User ID": m['user_id'],
                    "Username": m['username'],
                    "Joined At": m['joined_at'],
                    "Role": role
                })
            df_members = pd.DataFrame(member_list)
            st.dataframe(df_members, use_container_width=True, hide_index=True)
            
    with tab2:
        st.markdown("### Leave current squad")
        st.warning("Are you sure you want to leave this squad? If you are the owner, ownership will be transferred to the oldest member. If no other members exist, the squad will be deleted.")
        if st.button("Confirm & Leave Squad"):
            if leave_squad(user_id):
                st.success("Successfully left the squad.")
                st.rerun()
            else:
                st.error("Failed to leave the squad.")

else:
    st.info("You are not currently in a squad. You can either join an existing one or create your own squad to get started!")
    
    tab1, tab2 = st.tabs(["🔑 Join a Squad", "🆕 Create a Squad"])
    
    with tab1:
        st.markdown("### Join via Invite Code")
        invite_code = st.text_input("Enter invite code:", placeholder="e.g. SQ-A1B2C3").strip()
        if st.button("Join Squad"):
            if not invite_code:
                st.error("Please enter a valid invite code.")
            else:
                success, msg = join_squad_by_code(user_id, invite_code)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab2:
        st.markdown("### Form a New Squad")
        squad_name = st.text_input("Squad Name:", placeholder="e.g. Carbon Busters").strip()
        squad_desc = st.text_area("Squad Description:", placeholder="Describe your squad goal...").strip()
        
        if st.button("Create Squad"):
            if not squad_name:
                st.error("Please enter a squad name.")
            else:
                code = create_squad(squad_name, squad_desc, user_id)
                if code:
                    st.success(f"Squad successfully created! Your invite code is `{code}`")
                    # Unlock squad founder badge
                    gf.unlock_badge(user_id, 'b5')
                    st.rerun()
                else:
                    st.error("Failed to create squad. Make sure you are not already in a squad.")
