import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from voice_assistant import (
    PRIVACY_NOTICE,
    VOICE_PROMPTS,
    parse_voice_command,
    build_confirmation_summary,
    save_voice_log,
    record_voice_log_history,
    get_voice_log_history,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🎙️ Voice-Activated Eco Assistant</div>", unsafe_allow_html=True)
st.markdown(
    "Log your daily eco-activities hands-free. Say something like "
    "*\"I drove 10 km to work today\"* or *\"I recycled a plastic bottle\"* — "
    "we'll parse it, let you confirm, and save it to your footprint."
)

st.caption(f"🔒 {PRIVACY_NOTICE}")

st.markdown("---")

# ---------------------------------------------------------------------------
# Mic capture (browser Web Speech API) — writes transcript to session_state
# ---------------------------------------------------------------------------
mic_html = """
<div id="voice" style="text-align:center; font-family:sans-serif;">
  <button id="micBtn" onclick="startListening()"
    style="padding:16px 28px;font-size:18px;border-radius:40px;border:none;
           background:#2e7d32;color:white;cursor:pointer;">
    🎙️ Start Listening
  </button>
  <p id="status" style="margin-top:10px;color:#555;"></p>
  <div id="transcriptBox" style="margin:12px auto;max-width:520px;min-height:48px;
       border:1px dashed #999;border-radius:8px;padding:10px;color:#333;background:#fafafa;"></div>
  <button id="useBtn" onclick="useTranscript()" disabled
    style="padding:10px 20px;font-size:15px;border-radius:20px;border:none;
           background:#1565c0;color:white;cursor:pointer;">
    Use this text ⏎
  </button>
</div>
<script>
  let finalText = "";
  let recognition = null;
  function startListening() {
    const w = window.SpeechRecognition || window.webkitSpeechRecognition;
    const status = document.getElementById("status");
    if (!w) {
      status.innerHTML = "❌ This browser does not support speech recognition. Use the text box below instead.";
      document.getElementById("useBtn").disabled = true;
      return;
    }
    recognition = new w();
    recognition.lang = "en-US";
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onstart = () => status.innerHTML = "🎙️ Listening… speak now";
    recognition.onresult = (e) => {
      let interim = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const t = e.results[i][0].transcript;
        if (e.results[i].isFinal) finalText += t; else interim += t;
      }
      document.getElementById("transcriptBox").innerText = finalText + interim;
      document.getElementById("useBtn").disabled = finalText.trim() === "";
    };
    recognition.onerror = (e) => {
      status.innerHTML = "⚠️ Microphone error: " + (e.error || "unknown") + ". Try the text box below.";
    };
    recognition.onend = () => {
      status.innerHTML = finalText ? "✅ Done. Click 'Use this text'." : "No speech detected.";
    };
    recognition.start();
  }
  function useTranscript() {
    parent.postMessage({ transcript: finalText.trim() }, "*");
    document.getElementById("status").innerHTML = "📨 Sent to Eco Buddy — confirming below…";
  }
</script>
"""

if "voice_transcript" not in st.session_state:
    st.session_state.voice_transcript = ""

components.html(mic_html, height=260)

st.markdown("#### ✍️ Or type / edit your activity")
st.session_state.voice_transcript = st.text_area(
    "Describe your eco-activity",
    value=st.session_state.voice_transcript,
    height=90,
    placeholder='e.g. "I drove 10 km to work" or "I recycled a plastic bottle"',
    key="voice_text_area",
)

# Example prompts
st.markdown("**Example voice prompts:**")
cols = st.columns(2)
for i, prompt in enumerate(VOICE_PROMPTS):
    (cols[0] if i % 2 == 0 else cols[1]).caption(f"💬 \"{prompt}\"")

if st.button("🧠 Parse My Activity", type="primary", use_container_width=True):
    text = st.session_state.voice_transcript.strip()
    if not text:
        st.warning("Say or type something first.")
    else:
        st.session_state.parsed_command = parse_voice_command(text)
        st.session_state.parsed_raw = text
        st.rerun()

# ---------------------------------------------------------------------------
# Confirmation flow
# ---------------------------------------------------------------------------
if "parsed_command" in st.session_state:
    parsed = st.session_state.parsed_command
    st.markdown("---")
    st.markdown("<div class='section-header'>✅ Confirm Before Saving</div>", unsafe_allow_html=True)

    if parsed.get("action_type") == "unknown":
        st.warning("I couldn't understand that. Try rephrasing, e.g. *\"I took a 5 minute shower\"* or *\"I biked 8 km\"*.")
    else:
        st.markdown(f"**Detected:** {build_confirmation_summary(parsed)}")
        st.caption(f"Parsed with the {'AI assistant' if parsed.get('source') == 'llm' else 'built-in keyword parser'}.")

        c1, c2 = st.columns(2)
        if c1.button("💾 Confirm & Save", type="primary", use_container_width=True):
            ok, msg = save_voice_log(user_id, parsed)
            if ok:
                record_voice_log_history(user_id, st.session_state.parsed_raw, parsed, True)
                st.success(msg)
                st.balloons()
                st.session_state.pop("parsed_command", None)
                st.session_state.voice_transcript = ""
                st.rerun()
            else:
                st.error(msg)
        if c2.button("↩️ Cancel", use_container_width=True):
            st.session_state.pop("parsed_command", None)
            st.rerun()

st.markdown("---")
st.markdown("### 🕘 Voice Log History")
history = get_voice_log_history(user_id)
if history:
    st.dataframe(
        pd.DataFrame([{
            "Time": row["created_at"],
            "Heard": row["raw_text"][:60],
            "Action": row["action_type"],
            "Saved": "✅" if row["confirmed"] else "—",
        } for row in history]),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No voice logs yet — say or type your first activity above.")