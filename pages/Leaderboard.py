import streamlit as st
import pandas as pd
import datetime
from database import (
    get_squad_leaderboard,
    get_active_monthly_challenges,
    get_or_create_user,
    get_username
)
import gamification as gf
from styles.theme import apply_theme

# Apply theme
apply_theme()

st.markdown("<div class='section-header'>🏆 Community Leaderboard</div>", unsafe_allow_html=True)

# Initialize active user in session state
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = 1

# Sidebar User Simulator
st.sidebar.markdown("### 👥 User Simulation")
sim_username = st.sidebar.selectbox(
    "Act as user:",
    ["Alice", "Bob", "Charlie", "Dave", "Eve", "The Professor", "Custom..."],
    key="leaderboard_sim_user"
)

if sim_username == "Custom...":
    custom_name = st.sidebar.text_input("Enter custom username:", "NewUser", key="leaderboard_custom_user")
    if custom_name:
        st.session_state.active_user_id = get_or_create_user(custom_name)
else:
    st.session_state.active_user_id = get_or_create_user(sim_username)

st.sidebar.info(f"Simulating as: **{get_username(st.session_state.active_user_id)}** (ID: {st.session_state.active_user_id})")

# Tabs for Leaderboard
tab1, tab2, tab3 = st.tabs(["🏆 Squad Rankings", "🗓️ Monthly Challenges", "⚙️ Cycle Evaluator"])

with tab1:
    st.markdown("### 🥇 Global Squad Standings")
    st.write("Squads compete collectively based on the aggregated XP of all their members.")

    leaderboard_data = get_squad_leaderboard()
    if not leaderboard_data:
        st.info("No squads registered yet. Go to the Squads page to create one!")
    else:
        df = pd.DataFrame(leaderboard_data)
        # Add rank column starting at 1
        df.insert(0, 'Rank', range(1, len(df) + 1))
        # Rename columns for display
        df.columns = ['Rank', 'Squad ID', 'Squad Name', 'Description', 'Total XP']
        
        # Display with emojis for top 3
        def format_rank(r):
            if r == 1:
                return "🥇 1st"
            elif r == 2:
                return "🥈 2nd"
            elif r == 3:
                return "🥉 3rd"
            return f"{r}th"
            
        df['Rank'] = df['Rank'].apply(format_rank)
        
        st.dataframe(
            df[['Rank', 'Squad Name', 'Description', 'Total XP']],
            use_container_width=True,
            hide_index=True
        )

with tab2:
    st.markdown("### 📅 Active Monthly Challenges")
    st.write("Aggregated target XP goals for squads to achieve during the month. Reach the target to unlock rewards!")

    challenges = get_active_monthly_challenges()
    if not challenges:
        st.success("All challenges for this cycle have been completed! 🎉")
    else:
        leaderboard_data = get_squad_leaderboard()
        for ch in challenges:
            with st.container():
                st.markdown(f"#### 🎯 {ch['title']}")
                st.write(ch['description'])
                st.caption(f"🗓️ Start: {ch['start_date']} | End: {ch['end_date']} | Goal: **{ch['target_xp']} XP**")
                
                # Show progress for each squad
                if leaderboard_data:
                    st.write("**Squad Progress:**")
                    for squad in leaderboard_data:
                        progress = min(1.0, float(squad['total_xp']) / float(ch['target_xp']))
                        percent = int(progress * 100)
                        
                        # Custom color based on status
                        if percent >= 100:
                            st.write(f"✅ **{squad['name']}**: {squad['total_xp']} / {ch['target_xp']} XP (Goal Met!)")
                            st.progress(1.0)
                        else:
                            st.write(f"⏳ **{squad['name']}**: {squad['total_xp']} / {ch['target_xp']} XP ({percent}%)")
                            st.progress(progress)
                else:
                    st.info("No squads available to track progress.")
                st.markdown("---")

with tab3:
    st.markdown("### ⚙️ Challenge Cycle Evaluator")
    st.write("Simulate the end of the monthly challenge cycle to distribute badges and rewards to qualifying squads.")
    
    st.warning("Running the evaluator will process all active challenges, reward qualifying squads/users, and close the challenges.")
    
    if st.button("🚀 End Challenge Cycle & Distribute Rewards"):
        results = gf.evaluate_monthly_challenges()
        if not results:
            st.info("No active challenges were found to evaluate.")
        else:
            st.success("Successfully completed evaluation cycle!")
            for res in results:
                st.write(f"- Challenge **{res['challenge_id']}** evaluated.")
                if res['winning_squads']:
                    st.write(f"  🏆 Winners: {', '.join(res['winning_squads'])}")
                else:
                    st.write("  ❌ No squads met the XP target for this challenge.")
            st.balloons()
            st.rerun()
