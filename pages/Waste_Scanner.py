import streamlit as st
import time
from database import get_or_create_user, get_username
import gamification as gf
from waste_classifier import classify_waste_image
from styles.theme import apply_theme

# Apply theme
apply_theme()

st.markdown("<div class='section-header'>📸 AI Vision Waste Scanner</div>", unsafe_allow_html=True)
st.write("Take a picture of your waste item, and our AI Assistant will analyze it to provide correct sorting and disposal instructions.")

# Initialize active user in session state
if "active_user_id" not in st.session_state:
    st.session_state.active_user_id = 1

# Sidebar User Simulator
st.sidebar.markdown("### 👥 User Simulation")
sim_username = st.sidebar.selectbox(
    "Act as user:",
    ["Alice", "Bob", "Charlie", "Dave", "Eve", "The Professor", "Custom..."],
    key="scanner_sim_user"
)

if sim_username == "Custom...":
    custom_name = st.sidebar.text_input("Enter custom username:", "NewUser", key="scanner_custom_user")
    if custom_name:
        st.session_state.active_user_id = get_or_create_user(custom_name)
else:
    st.session_state.active_user_id = get_or_create_user(sim_username)

user_id = st.session_state.active_user_id
st.sidebar.info(f"Simulating as: **{get_username(user_id)}** (ID: {user_id})")

# Automatically enroll in the waste scanning challenge (c6) if not already enrolled
enrolled = gf.get_user_challenges(user_id)
c6_status = None
c6_progress = 0.0

for c in enrolled:
    if c['challenge_id'] == 'c6':
        c6_status = c['status']
        c6_progress = c['progress_value']
        break

if c6_status is None:
    gf.enroll_challenge(user_id, 'c6')
    c6_status = 'enrolled'
    c6_progress = 0.0

# Gamification Info Panel
total_xp = gf.get_total_xp(user_id)
level = gf.calculate_level(total_xp)

st.markdown("### 📊 Your Progress")
col1, col2, col3 = st.columns(3)
col1.metric("Current Level", f"Lvl {level}")
col2.metric("Total XP", f"{total_xp} XP")

challenge_def = gf.CHALLENGES['c6']
if c6_status == 'completed':
    col3.metric("Scanner Challenge", "🎉 Completed!")
    st.success("You have fully completed the **Scan and sort 3 waste items** challenge! Keep scanning to maintain your eco-habits.")
else:
    col3.metric("Scanner Progress", f"{int(c6_progress)} / {int(challenge_def['target'])}")
    st.info(f"🎯 **Active Challenge**: {challenge_def['title']} to earn **{challenge_def['xp']} XP**!")

st.markdown("---")

# Camera Input
st.write("📷 **Align waste item in camera frame:**")
captured_file = st.camera_input("Capture Waste Photo", label_visibility="collapsed")

if captured_file is not None:
    # Read image bytes
    image_bytes = captured_file.getvalue()
    
    with st.spinner("🧠 The Professor is analyzing the intercepted payload..."):
        # Let's add a slight artificial delay for a premium feel
        time.sleep(1.0)
        result = classify_waste_image(image_bytes)
        
    if result:
        st.markdown("### 🔍 Classification Results")
        
        category = result.get("category", "Landfill")
        item_type = result.get("type", "Unknown item")
        confidence = result.get("confidence", 0.8)
        instructions = result.get("instructions", "Sort in the general bin.")
        
        # Color schemes for waste categories
        # Recyclable = Blue, Compost = Green, Landfill = Grey
        if category == "Recyclable":
            color_hex = "#1E88E5"
            bg_hex = "#E3F2FD"
            emoji = "♻️"
        elif category == "Compost":
            color_hex = "#43A047"
            bg_hex = "#E8F5E9"
            emoji = "🍏"
        else:
            color_hex = "#757575"
            bg_hex = "#F5F5F5"
            emoji = "🗑️"
            
        # Display output card
        st.markdown(
            f"""
            <div style="background-color: {bg_hex}; border-left: 5px solid {color_hex}; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                <h3 style="color: {color_hex}; margin: 0 0 10px 0;">{emoji} {category}</h3>
                <p style="margin: 0 0 8px 0; font-size: 16px;"><b>Object Identified:</b> {item_type}</p>
                <p style="margin: 0 0 12px 0; font-size: 14px;"><b>Confidence Score:</b> {int(confidence * 100)}%</p>
                <div style="background-color: white; padding: 15px; border-radius: 4px; border: 1px dashed {color_hex};">
                    <p style="margin: 0; font-size: 15px; color: #333;">📋 <b>Instructions:</b> {instructions}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Update challenge progress and show rewards
        if c6_status == 'enrolled':
            # Perform update
            gf.update_challenge_progress(user_id, 'c6', progress_increment=1.0)
            
            # Check if it was completed
            is_complete = gf.validate_challenge_progress(user_id, 'c6')
            
            # Show update info
            if is_complete:
                st.balloons()
                st.success(f"🏆 **Challenge Completed!** You have scanned 3 waste items and earned **{challenge_def['xp']} XP**!")
                
                # Check for badge eligibility
                unlocked_before = [b['badge_id'] for b in gf.get_unlocked_badges(user_id)]
                gf.check_badge_eligibility(user_id)
                unlocked_after = [b['badge_id'] for b in gf.get_unlocked_badges(user_id)]
                
                new_badges = set(unlocked_after) - set(unlocked_before)
                for badge_id in new_badges:
                    badge = gf.BADGES.get(badge_id)
                    st.success(f"🎖️ **New Badge Unlocked**: **{badge['name']}** (+{badge['xp']} XP) — {badge['desc']}!")
            else:
                st.info(f"⭐ **Progress Updated**: You are now at **{int(c6_progress + 1)} / {int(challenge_def['target'])}** scans completed for this challenge!")
                
            # Rerun to update progress metric card after a small display window
            time.sleep(2.0)
            st.rerun()
    else:
        st.error("Failed to analyze image. Please try again with a clearer picture.")
