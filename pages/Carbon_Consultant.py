import streamlit as st
from carbon_consultant import (
    QUICK_QUESTIONS, build_user_context, ask_consultant,
    save_message, get_conversation, clear_conversation,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>💬 AI Carbon Consultant</div>", unsafe_allow_html=True)
st.markdown(
    "Your personal conversational sustainability advisor. Ask anything about "
    "reducing your carbon footprint and get advice grounded in your own "
    "assessment history."
)

if "consultant_chat" not in st.session_state:
    st.session_state.consultant_chat = []

user_context = build_user_context(user_id)
with st.expander("🧠 My Sustainability Context (used by the AI)"):
    st.write(user_context)

st.markdown("---")
st.markdown("### ❓ Quick Questions")
quick = st.radio(
    "Or pick a question to get started:",
    QUICK_QUESTIONS,
    index=None,
    label_visibility="collapsed",
)

st.markdown("---")
st.markdown("### 💭 Ask the Consultant")

chat_input = st.text_input(
    "Your question",
    placeholder="e.g., How can I reduce my footprint by 30%?",
    key="consultant_input",
    label_visibility="collapsed",
)
chat_col, clear_col = st.columns([3, 1])
with chat_col:
    send_btn = st.button("💬 Send", type="primary", use_container_width=True)
with clear_col:
    if st.button("🧹 New Chat", use_container_width=True):
        clear_conversation(user_id)
        st.session_state.consultant_chat = []
        st.rerun()

if send_btn or quick:
    question = chat_input.strip() if chat_input.strip() else quick
    if question:
        with st.spinner("Consulting your carbon advisor..."):
            answer = ask_consultant(question, user_context)
        if answer:
            save_message(user_id, "user", question)
            save_message(user_id, "assistant", answer)
            st.session_state.consultant_chat.append(("user", question))
            st.session_state.consultant_chat.append(("assistant", answer))
        else:
            st.error(
                "No AI provider is available right now. Set a GEMINI_API_KEY or "
                "GROQ_API_KEY environment variable to enable the carbon consultant."
            )

st.markdown("---")
st.markdown("### 📜 Conversation")

history = get_conversation(user_id)
if history:
    for msg in history:
        if msg["role"] == "user":
            st.markdown(f"**🧑 You:** {msg['message']}")
        else:
            st.markdown("**🤖 Carbon Consultant:**")
            st.markdown(msg["message"])
        st.markdown("---")
elif not st.session_state.consultant_chat:
    st.info("Ask a question above to start your conversation with the carbon consultant.")
