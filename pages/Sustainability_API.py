import streamlit as st
import json
import streamlit.components.v1 as components
from styles.theme import apply_theme
from api_auth import generate_api_key, list_api_keys, revoke_api_key
from sustainability_api import OPENAPI_SPEC, SWAGGER_UI_HTML, process_api_request

apply_theme()

st.title("🔌 Sustainability Insights API")
st.subheader("Third-Party Application Integration & API Portal")

st.markdown("""
Expose EcoBuddy AI insights to external mobile apps, smart home dashboards, IoT devices, or enterprise reporting platforms via secure REST API endpoints.
""")

tabs = st.tabs(["🔑 API Key Management", "📚 API Documentation & OpenAPI", "🧪 Interactive API Tester"])

# TAB 1: API Key Management
with tabs[0]:
    st.markdown("### Provision New API Key")
    with st.form("create_api_key_form"):
        app_name = st.text_input("Application Name", placeholder="e.g. My Eco Smart Home App")
        user_id = st.text_input("Developer / User ID", value="default_user")
        submit = st.form_submit_button("Generate API Key", use_container_width=True)

    if submit:
        if not app_name.strip():
            st.error("Please enter a valid Application Name.")
        else:
            key_data = generate_api_key(app_name, user_id=user_id)
            st.success("API Key generated successfully! Save your raw secret key now. It will NOT be shown again.")
            st.code(key_data["api_key"], language="text")
            st.info(f"Prefix: {key_data['key_prefix']} | Role: {key_data['role']} | Rate Limit: {key_data['rate_limit']} req/min")

    st.markdown("---")
    st.markdown("### Existing API Keys")
    keys = list_api_keys()
    if not keys:
        st.info("No API keys provisioned yet. Use the form above to generate your first API key.")
    else:
        for k in keys:
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
            with col1:
                st.write(f"**{k['app_name']}** (`{k['key_prefix']}`)")
            with col2:
                st.write(f"Role: {k['role']}")
            with col3:
                status_str = "🟢 Active" if k['is_active'] else "🔴 Revoked"
                st.write(status_str)
            with col4:
                if k['is_active']:
                    if st.button("Revoke Key", key=f"revoke_{k['id']}"):
                        revoke_api_key(k['id'])
                        st.success("Key revoked.")
                        st.rerun()

# TAB 2: Documentation & OpenAPI
with tabs[1]:
    st.markdown("### Swagger / OpenAPI 3.0 Documentation")
    st.markdown("Explore endpoints, schemas, authentication headers, and payload structures.")
    
    components.html(SWAGGER_UI_HTML, height=600, scrolling=True)

    st.markdown("### Integration Code Examples")
    st.markdown("#### Python Request Example")
    st.code("""import requests

url = "http://localhost:8000/api/v1/insights/calculate"
headers = {
    "X-API-Key": "eco_live_YOUR_API_KEY_HERE",
    "Content-Type": "application/json"
}
payload = {
    "transport": "Car",
    "distance": 15.0,
    "electricity": 250.0,
    "diet": "Omnivore",
    "flights": 2
}

response = requests.post(url, headers=headers, json=payload)
print(response.json())
""", language="python")

    st.markdown("#### cURL Example")
    st.code("""curl -X POST "http://localhost:8000/api/v1/insights/calculate" \\
     -H "X-API-Key: eco_live_YOUR_API_KEY_HERE" \\
     -H "Content-Type: application/json" \\
     -d '{"transport": "Car", "distance": 15.0, "electricity": 250.0, "diet": "Omnivore", "flights": 2}'
""", language="bash")

# TAB 3: Interactive API Tester
with tabs[2]:
    st.markdown("### Live API Endpoint Console")
    api_key_input = st.text_input("Enter API Key for Testing", placeholder="eco_live_...")
    endpoint_choice = st.selectbox(
        "Select Endpoint",
        [
            "POST /api/v1/insights/calculate",
            "GET /api/v1/insights/assessments",
            "GET /api/v1/insights/recommendations",
            "GET /api/v1/insights/goals",
            "GET /api/v1/health"
        ]
    )

    if endpoint_choice == "POST /api/v1/insights/calculate":
        col_a, col_b = st.columns(2)
        with col_a:
            t = st.selectbox("Transport", ["Car", "Public Transport", "Bike", "Walking"])
            dist = st.number_input("Daily Distance (km)", value=15.0)
            elec = st.number_input("Monthly Electricity (kWh)", value=250.0)
        with col_b:
            d = st.selectbox("Diet", ["Non-Vegetarian", "Omnivore", "Vegetarian", "Vegan"])
            fl = st.number_input("Annual Flights", value=2)

        if st.button("Execute Request", use_container_width=True):
            headers = {"X-API-Key": api_key_input} if api_key_input else {}
            body = {
                "transport": t,
                "distance": dist,
                "electricity": elec,
                "diet": d,
                "flights": fl
            }
            code, res, _ = process_api_request("POST", "/api/v1/insights/calculate", headers, body=body)
            st.markdown(f"**HTTP Status:** `{code}`")
            st.json(res)

    elif endpoint_choice == "GET /api/v1/insights/assessments":
        if st.button("Execute Request", use_container_width=True):
            headers = {"X-API-Key": api_key_input} if api_key_input else {}
            code, res, _ = process_api_request("GET", "/api/v1/insights/assessments", headers)
            st.markdown(f"**HTTP Status:** `{code}`")
            st.json(res)

    elif endpoint_choice == "GET /api/v1/insights/recommendations":
        if st.button("Execute Request", use_container_width=True):
            headers = {"X-API-Key": api_key_input} if api_key_input else {}
            code, res, _ = process_api_request("GET", "/api/v1/insights/recommendations", headers)
            st.markdown(f"**HTTP Status:** `{code}`")
            st.json(res)

    elif endpoint_choice == "GET /api/v1/insights/goals":
        if st.button("Execute Request", use_container_width=True):
            headers = {"X-API-Key": api_key_input} if api_key_input else {}
            code, res, _ = process_api_request("GET", "/api/v1/insights/goals", headers)
            st.markdown(f"**HTTP Status:** `{code}`")
            st.json(res)

    elif endpoint_choice == "GET /api/v1/health":
        if st.button("Execute Request", use_container_width=True):
            code, res, _ = process_api_request("GET", "/api/v1/health", {})
            st.markdown(f"**HTTP Status:** `{code}`")
            st.json(res)
