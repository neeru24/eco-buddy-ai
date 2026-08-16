import streamlit as st
import pandas as pd
from carbon_marketplace import PROJECTS
from carbon_credit_ledger import (
    CREDIT_STANDARDS,
    issue_credit,
    retire_credit,
    get_portfolio,
    get_portfolio_summary,
    verify_ledger,
    lookup_credit,
    get_ledger_height,
)
from styles.theme import apply_theme

user_id = st.session_state.get("user_id")
if not user_id:
    st.warning("Please log in from the main application page.")
    st.stop()
apply_theme()

st.markdown("<div class='section-header'>🔗 Blockchain-Verified Carbon Credit Portfolio</div>", unsafe_allow_html=True)
st.markdown(
    "Own carbon credits backed by a tamper-evident hash-chain ledger. Every "
    "issue and retirement is recorded immutably and can be publicly verified."
)

st.caption("⚠️ Educational simulation of a distributed ledger — not financial advice.")

summary = get_portfolio_summary(user_id)
ledger_valid, blocks, _ = verify_ledger()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Active Credits", f"{summary['total_active']} t")
c2.metric("Retired Credits", f"{summary['total_retired']} t")
c3.metric("Portfolio Value", f"${summary['total_value_usd']}")
c4.metric("Ledger Blocks", blocks or get_ledger_height())

if ledger_valid:
    st.success("✅ Ledger verified — hash chain is intact and tamper-free." if blocks else "ℹ️ Ledger is empty — create your first credit below.")
else:
    st.error("❌ Ledger integrity check failed! The hash chain is broken.")

st.markdown("---")
st.markdown("### 🛒 Buy Carbon Credits")

with st.form("buy_credits"):
    b1, b2 = st.columns(2)
    project_options = {p["name"]: p for p in PROJECTS}
    project_name = b1.selectbox("Project", list(project_options.keys()))
    standard = b2.selectbox("Crediting Standard", CREDIT_STANDARDS)
    c_b1, c_b2, c_b3 = st.columns(3)
    vintage = c_b1.number_input("Vintage year", min_value=2015, max_value=2026, value=2026, step=1)
    tonnes = c_b2.number_input("Tonnes", min_value=1.0, max_value=1000.0, value=10.0, step=1.0)
    c_b3.caption(f"Cost: **${project_options[project_name]['cost_per_tonne']}/t**")

    if st.form_submit_button("🛒 Purchase & Issue Credit", type="primary"):
        project = project_options[project_name]
        cost = project["cost_per_tonne"]
        credit = issue_credit(
            user_id, project, vintage, tonnes, cost, standard=standard
        )
        if credit:
            st.balloons()
            st.success(
                f"Issued **{tonnes} tCO₂e** from *{project['name']}* — "
                f"serial **{credit['serial_number']}** recorded on the ledger."
            )
            st.rerun()
        else:
            st.error("Could not issue credit.")

st.markdown("---")
st.markdown("### 📂 Your Credits")

portfolio = get_portfolio(user_id)
if portfolio:
    rows = []
    for cr in portfolio:
        rows.append({
            "Serial": cr["serial_number"],
            "Project": cr["project_name"],
            "Standard": cr["standard"],
            "Vintage": cr["vintage"],
            "Tonnes": cr["tonnes"],
            "Status": "✅ Retired" if cr["status"] == "retired" else "🟢 Active",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    active_credits = [c for c in portfolio if c["status"] == "active"]
    if active_credits:
        st.markdown("#### 🗑️ Retire a Credit")
        options = {
            f"{c['serial_number']} — {c['tonnes']} t ({c['project_name']})": c["id"]
            for c in active_credits
        }
        sel = st.selectbox("Select active credit to retire", list(options.keys()))
        reason = st.text_input(
            "Retirement reason (optional)",
            placeholder="e.g., Offset my annual flight emissions",
        )
        if st.button("🏁 Retire Credit", type="primary"):
            success, msg = retire_credit(user_id, options[sel], reason.strip())
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.warning(msg)
else:
    st.info("No credits yet — purchase your first above.")

st.markdown("---")
st.markdown("### 🔍 Verify a Credit Serial")

serial_input = st.text_input(
    "Enter a serial number (e.g., from a certificate)",
    placeholder="CR-2026-XXXX...",
)
if serial_input.strip():
    credit_record = lookup_credit(serial_input.strip())
    if credit_record:
        st.markdown("**Credit record:**")
        info = {
            "Project": credit_record["project_name"],
            "Standard": credit_record["standard"],
            "Vintage": credit_record["vintage"],
            "Tonnes": f"{credit_record['tonnes']} tCO₂e",
            "Status": "✅ Retired" if credit_record["status"] == "retired" else "🟢 Active",
            "Issued Hash": credit_record["issued_hash"][:24] + "...",
        }
        if credit_record.get("retired_hash"):
            info["Retired Hash"] = credit_record["retired_hash"][:24] + "..."
        st.json(info)

        if credit_record.get("events"):
            st.markdown("**Ledger events:**")
            for ev in credit_record["events"]:
                st.markdown(
                    f"- `{ev['timestamp'][:19]}` — **{ev['data'].get('event')}** "
                    f"({ev['data'].get('serial', '')[:20]}...) hash `{ev['hash']}`"
                )
    else:
        st.warning("No credit found with that serial number.")

st.markdown("---")
st.markdown("### 🔎 Ledger Verification")
st.markdown(
    "The ledger uses a SHA-256 hash chain: each block contains the previous "
    "block's hash, so altering any past record invalidates the entire chain. "
    "Use the serial verification above to confirm a credit's full lifecycle."
)