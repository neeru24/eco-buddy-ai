import streamlit as st
import pandas as pd
from ai_waste_sorter import (
    WASTE_CATEGORIES,
    DISPOSAL_RULES,
    classify_waste_image,
    save_classification,
    get_classification_history,
    update_classification_feedback,
    get_classification_accuracy,
    add_classified_item_to_waste_assessment,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🗑️ AI Waste Sorter & Recycling Guide</div>", unsafe_allow_html=True)
st.markdown(
    "Upload a photo of any waste item and get instant classification, "
    "location-aware disposal guidance, and a recycling tip."
)

# Region selector for disposal rules
regions = list(DISPOSAL_RULES.keys())
region = st.selectbox("🌍 Your region (for disposal rules)", regions, index=0)

st.markdown("---")

# File uploader
uploaded = st.file_uploader(
    "📤 Upload a photo of the item",
    type=["png", "jpg", "jpeg", "webp"],
    help="Best results with a clear, well-lit photo of a single item.",
)

if uploaded:
    with st.spinner("🔍 Analyzing with AI vision..."):
        # Convert to bytes for hashing and classification
        file_bytes = uploaded.getvalue()
        import io
        img_stream = io.BytesIO(file_bytes)

        classification = classify_waste_image(img_stream, region)

    # Display result
    cat = classification["category"]
    color = WASTE_CATEGORIES[cat]["color"]
    label = classification["label"]
    conf = classification["confidence"]

    st.markdown(f"""
    <div style="background:{color}15; border:2px solid {color}; border-radius:12px; padding:16px; margin:8px 0;">
        <h3 style="margin:0; color:{color};">{label}</h3>
        <p style="margin:4px 0 0 0;">
            <strong>Confidence:</strong> {conf:.0%} &nbsp;|&nbsp;
            <strong>Subcategory:</strong> {classification.get('subcategory') or '—'} &nbsp;|&nbsp;
            <strong>Region:</strong> {classification['region']}
        </p>
        <p style="margin:8px 0 0 0; font-size:0.95rem;"><em>{classification['explanation']}</em></p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### ♻️ How to dispose")
        st.info(classification["disposal_guidance"])
    with col2:
        st.markdown("### 💡 Did you know?")
        st.success(classification["fact"])
        st.caption(f"💡 Tip: {classification['tip']}")

    # Confidence warning
    if conf < 0.6:
        st.warning("⚠️ Low confidence — please double-check the category below.")

    # Feedback + Save
    st.markdown("### ✅ Confirm & Save")
    c1, c2, c3 = st.columns(3)
    feedback = c1.selectbox(
        "Was this classification correct?",
        ["👍 Yes", "👎 No — wrong category", "🤷 Not sure"],
        index=0,
    )
    correct_cat = None
    if feedback == "👎 No — wrong category":
        correct_cat = c2.selectbox("Correct category:", list(WASTE_CATEGORIES.keys()), format_func=lambda k: WASTE_CATEGORIES[k]["label"])
    if c3.button("💾 Save Classification", type="primary", use_container_width=True):
        img_hash = __import__("hashlib").sha256(file_bytes).hexdigest()[:16]
        ok = save_classification(user_id, img_hash, classification,
                                  feedback if feedback != "👍 Yes" else None,
                                  correct_cat)
        if ok:
            st.success("Classification saved to your history!")
            if feedback == "👍 Yes":
                # Auto-add to waste assessment
                added = add_classified_item_to_waste_assessment(user_id, classification)
                if added:
                    st.toast("📊 Added to your weekly waste footprint!", icon="✅")
            st.rerun()
        else:
            st.error("Could not save.")

st.markdown("---")

# Accuracy & History
st.markdown("### 📈 Your Sorting Accuracy")
acc = get_classification_accuracy(user_id)
if acc["accuracy"] is not None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Items with feedback", acc["total_feedback"])
    c2.metric("Correct", acc["correct"])
    c3.metric("Accuracy", f"{acc['accuracy']}%")
else:
    st.info("Start saving classifications and marking corrections to see your accuracy.")

st.markdown("---")
st.markdown("### 🕘 Classification History")
history = get_classification_history(user_id)
if history:
    for row in history:
        cat = row["category"]
        color = WASTE_CATEGORIES[cat]["color"]
        label = WASTE_CATEGORIES[cat]["label"]
        with st.expander(f"{label} — {row['created_at'][:16]} ({row['confidence']:.0%})"):
            st.write(f"**Subcategory:** {row['subcategory'] or '—'}")
            st.write(f"**Region:** {row['region']}")
            if row["user_feedback"]:
                st.write(f"**Your feedback:** {row['user_feedback']}")
            if row["correct_category"]:
                st.write(f"**Corrected to:** {WASTE_CATEGORIES[row['correct_category']]['label']}")
            # Allow updating feedback if not set
            if not row["user_feedback"]:
                fb = st.selectbox("Mark accuracy:", ["👍 Correct", "👎 Wrong", "🤷 Unsure"], key=f"fb_{row['id']}")
                corr = None
                if fb == "👎 Wrong":
                    corr = st.selectbox("Correct category:", list(WASTE_CATEGORIES.keys()),
                                        format_func=lambda k: WASTE_CATEGORIES[k]["label"], key=f"corr_{row['id']}")
                if st.button("Save feedback", key=f"savefb_{row['id']}"):
                    if update_classification_feedback(row["id"], user_id, fb, corr):
                        st.success("Feedback saved!")
                        st.rerun()
else:
    st.info("No classifications yet — upload your first item above.")

st.markdown("---")
st.caption("💡 Tip: For best results, photograph one item at a time on a plain background in good light.")