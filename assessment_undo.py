"""
Assessment Undo & Restore Module (#441).

Provides one-click undo for the user's most recent assessment, restore functionality for undone assessments,
confirmation modal/dialog protection, and comprehensive assessment activity history logging.
"""

import pandas as pd
import streamlit as st
from database import (
    undo_last_assessment,
    restore_last_deleted_assessment,
    get_last_undone_assessment,
    get_assessment_activity_history,
    get_assessments,
)


def render_assessment_undo_ui(user_id: int = 1) -> None:
    """
    Render Undo & Restore Assessment management panel with confirmation dialog and activity history.
    """
    st.subheader("↩️ Undo & Restore Recent Assessment")
    st.markdown(
        "Accidentally saved an assessment or made a mistake in inputs? "
        "Use one-click Undo to remove your latest entry, or Restore to bring back deleted assessments."
    )
    
    assessments = get_assessments(user_id=user_id)
    last_undone = get_last_undone_assessment(user_id=user_id)
    
    c_undo, c_restore = st.columns(2)
    
    with c_undo:
        st.markdown("### ⏪ Undo Most Recent Assessment")
        if assessments:
            latest = assessments[0]
            # latest tuple: id, date, created_at, transport, distance, electricity, diet, flights, footprint, eco_score
            rec_id = latest[0]
            footprint = latest[8] or 0.0
            eco_score = latest[9] or 0
            
            st.info(f"**Latest Assessment #{rec_id}:** {footprint:.1f} kg CO2 (Score: {eco_score})")
            
            # Confirmation Dialog state
            if f"show_undo_confirm_{user_id}" not in st.session_state:
                st.session_state[f"show_undo_confirm_{user_id}"] = False
                
            if not st.session_state[f"show_undo_confirm_{user_id}"]:
                if st.button("🗑️ Undo Last Assessment", key="btn_init_undo"):
                    st.session_state[f"show_undo_confirm_{user_id}"] = True
                    st.rerun()
            else:
                st.warning("⚠️ **Confirmation Required**: Are you sure you want to undo and remove Assessment #{}?".format(rec_id))
                b_yes, b_no = st.columns(2)
                with b_yes:
                    if st.button("✅ Yes, Undo It", key="btn_confirm_undo"):
                        success, msg, _ = undo_last_assessment(user_id=user_id)
                        st.session_state[f"show_undo_confirm_{user_id}"] = False
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)
                        st.rerun()
                with b_no:
                    if st.button("❌ Cancel", key="btn_cancel_undo"):
                        st.session_state[f"show_undo_confirm_{user_id}"] = False
                        st.rerun()
        else:
            st.caption("No active assessments available to undo.")
            
    with c_restore:
        st.markdown("### 🔄 Restore Undone Assessment")
        if last_undone:
            st.info(
                f"**Undone Entry #{last_undone['original_id']}:** {last_undone['footprint']:.1f} kg CO2 "
                f"(Deleted at {last_undone['deleted_at']})"
            )
            if st.button("♻️ Restore Assessment", key="btn_restore_assessment"):
                success, msg, _ = restore_last_deleted_assessment(user_id=user_id)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                st.rerun()
        else:
            st.caption("No undone assessments available for restoration.")
            
    st.divider()
    
    # Activity History
    st.subheader("📜 Assessment Activity History")
    history = get_assessment_activity_history(user_id=user_id)
    if history:
        df_hist = pd.DataFrame(history)
        df_hist = df_hist[["timestamp", "action", "details", "assessment_id"]]
        df_hist.columns = ["Timestamp", "Action", "Details", "Assessment ID"]
        st.dataframe(df_hist, use_container_width=True)
    else:
        st.caption("No assessment activity recorded yet.")
