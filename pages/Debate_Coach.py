import streamlit as st
import pandas as pd
from debate_coach import (
    DEBATE_TOPICS, generate_counterargument, score_argument,
    save_debate, get_debate_history,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🗣️ AI Sustainability Debate Coach</div>", unsafe_allow_html=True)
st.markdown(
    "Sharpen your environmental thinking by debating with an AI that provides "
    "fact-based counterarguments, scores your reasoning, and points you to "
    "quality learning resources."
)

if "debate_session" not in st.session_state:
    st.session_state.debate_session = {}

st.markdown("---")
st.markdown("### 🎯 Choose a Debate Topic")

topic_keys = list(DEBATE_TOPICS.keys())
topic_labels = {k: f"{v['icon']} {v['title']}" for k, v in DEBATE_TOPICS.items()}
selected_label = st.selectbox("Select a topic", [topic_labels[k] for k in topic_keys])
topic_key = topic_keys[topic_labels.index(selected_label)]
topic = DEBATE_TOPICS[topic_key]

with st.expander("📖 Topic Context"):
    st.write(topic["context"])
    st.markdown("**Suggested learning resources:**")
    for res in topic["learning_resources"]:
        st.markdown(f"- {res}")

st.markdown("---")
st.markdown("### ✍️ State Your Position")

position = st.selectbox(
    "Your position",
    ["For", "Against", "Neutral / Mixed"],
    key="debate_position",
)
argument = st.text_area(
    "Your argument",
    placeholder="Present your reasoning, evidence, and examples...",
    height=140,
    key="debate_argument",
)

col1, col2 = st.columns(2)
with col1:
    counter_btn = st.button("💬 Get Counterargument", type="primary", use_container_width=True)
with col2:
    score_btn = st.button("📊 Score My Argument", use_container_width=True)

if counter_btn:
    if not argument.strip():
        st.warning("Please write your argument first.")
    else:
        with st.spinner("Crafting a balanced counterargument..."):
            result = generate_counterargument(topic_key, position, argument)
        if result:
            st.session_state.debate_session["counterargument"] = result
            st.session_state.debate_session["topic_key"] = topic_key
            st.session_state.debate_session["position"] = position
            st.session_state.debate_session["argument"] = argument
        else:
            st.error(
                "No AI provider is available right now. Set a GEMINI_API_KEY or "
                "GROQ_API_KEY environment variable to enable AI-powered debates."
            )

if "counterargument" in st.session_state.debate_session:
    result = st.session_state.debate_session["counterargument"]
    st.markdown("---")
    st.markdown("### 🤖 AI Counterargument")
    st.markdown(result["counterargument"])

    st.markdown("#### ✅ Strong Points in Your Argument")
    if isinstance(result["strong_points"], list):
        for point in result["strong_points"]:
            st.markdown(f"- {point}")
    else:
        st.markdown(result["strong_points"])

    st.markdown("#### 🛡️ How to Rebut")
    st.markdown(result["rebuttal_advice"])

    if st.button("💾 Save This Debate"):
        saved = save_debate(
            user_id,
            topic_key,
            st.session_state.debate_session["position"],
            st.session_state.debate_session["argument"],
            result["counterargument"],
            None,
        )
        if saved:
            st.success("Debate saved to your history!")
        else:
            st.error("Could not save debate.")

if score_btn:
    if not argument.strip():
        st.warning("Please write your argument first.")
    else:
        with st.spinner("Evaluating your argument..."):
            score_result = score_argument(argument, topic_key)
        if score_result:
            st.markdown("---")
            st.markdown("### 📊 Argument Score")
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("Overall Score", f"{score_result['score']}/100")
            sc2.metric("Clarity", score_result["clarity"] or "N/A")
            sc3.metric("Evidence", score_result["evidence"] or "N/A")

            st.progress(score_result["score"] / 100)
            st.markdown(f"**Feedback:** {score_result['feedback']}")
            st.markdown("**Logic assessment:** " + (score_result["logic"] or "N/A"))

            if score_result.get("suggestions"):
                st.markdown("**Suggestions to improve:**")
                for s in score_result["suggestions"]:
                    st.markdown(f"- {s}")

            if st.button("💾 Save This Debate (with score)"):
                saved = save_debate(
                    user_id, topic_key, position, argument, None, score_result["score"]
                )
                if saved:
                    st.success("Debate saved to your history!")
                else:
                    st.error("Could not save debate.")

st.markdown("---")
st.markdown("### 📜 Your Debate History")

history = get_debate_history(user_id)
if history:
    rows = []
    for h in history:
        rows.append({
            "Date": h["created_at"][:10] if h["created_at"] else "",
            "Topic": DEBATE_TOPICS.get(h["topic_key"], {}).get("title", h["topic_key"]),
            "Position": h["user_position"],
            "Score": h["score"] if h["score"] is not None else "—",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("No debates saved yet. Complete a debate above to build your history.")
