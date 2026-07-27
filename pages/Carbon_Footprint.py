import streamlit as st
import pandas as pd
import time
from database import *
from emissions import *
from recommendations import *
from ocr_utils import *
import os
import tempfile
import uuid
import plotly.graph_objects as go
import plotly.express as px
from report import generate_pdf
import gamification as gf
from marketplace import *
import energy_audit as ea
from notifications import success, error, warning, info

from styles.theme import apply_theme
apply_theme()


from cache import cached
from cache_config import TTL_LLM_RESPONSE

@cached(ttl=TTL_LLM_RESPONSE)
def compute_arima_forecast(ts_data):
    import warnings
    from statsmodels.tsa.arima.model import ARIMA
    import numpy as np

    warnings.filterwarnings('ignore')
    arr = np.array(ts_data)
    model = ARIMA(arr, order=(1, 1, 0))
    fitted_model = model.fit()

    forecast_steps = 5
    forecast = fitted_model.get_forecast(steps=forecast_steps)
    forecast_mean = forecast.predicted_mean
    conf_int = forecast.conf_int(alpha=0.05)

    forecast_line = [float(arr[-1])] + [float(v) for v in forecast_mean]
    conf_lower = [float(arr[-1])] + [float(v) for v in conf_int[:, 0]]
    conf_upper = [float(arr[-1])] + [float(v) for v in conf_int[:, 1]]

    return forecast_line, conf_lower, conf_upper

user_id = st.session_state.get('user_id')
if not user_id:
    warning('Please log in from the main application page.')
    st.stop()

tab_assess, tab_forecast = st.tabs(['📝 Assessment', '📈 Forecasting'])

with tab_assess:
    st.markdown("<div class='section-header'>📝 Your Lifestyle Profile</div>", unsafe_allow_html=True)
    st.markdown("### Region Setting")
    region = st.selectbox("Select Your Region for API Emissions Factor", ["Global", "US", "UK", "EU"])

    # -------------------------
    # QUICK LOG (AI)
    # -------------------------
    st.markdown("### 🤖 AI Quick Log")
    col_ai_input, col_ai_btn = st.columns([4, 1], vertical_alignment="bottom")
    with col_ai_input:
        quick_log_text = st.text_area("Let AI auto-fill your profile! Describe your day naturally.", placeholder="e.g., 'I drove 15 miles in my SUV and had a beef steak'", key="quick_log_input", height=68)
    with col_ai_btn:
        parse_btn = st.button("✨ Parse with AI", use_container_width=True)
    
    if parse_btn:
        if quick_log_text.strip():
            with st.spinner("Analyzing text..."):
                parsed_data = parse_quick_log(quick_log_text)
                if parsed_data:
                    st.session_state.temp_parsed = parsed_data
                else:
                    error("Could not parse the text. Please try again.")
        else:
            warning("Please enter some text first.")

    if "temp_parsed" in st.session_state:
        tp = st.session_state.temp_parsed
        info(f"**We found:** {tp.get('distance', 10.0)} km by {tp.get('transport', 'Car')}, and {tp.get('diet', 'Vegetarian')} diet. Is this correct?")
        c_yes, c_no = st.columns(2)
        with c_yes:
            if st.button("✅ Yes, use this", key="confirm_yes"):
                st.session_state.transport = tp.get('transport', 'Car')
                st.session_state.distance = float(tp.get('distance', 10.0))
                st.session_state.diet = tp.get('diet', 'Vegetarian')
                del st.session_state.temp_parsed
                st.rerun()
        with c_no:
            if st.button("❌ No, cancel", key="confirm_no"):
                del st.session_state.temp_parsed
                st.rerun()

    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>🚗</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Transportation</span></div>", unsafe_allow_html=True)
        transport = st.selectbox("Primary Transport", ["Car", "Public Transport", "Bike", "Walking"])
        distance = st.number_input("Daily Distance (km)", min_value=0.0, value=10.0, step=1.0)

    with col2:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>⚡</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Energy & Diet</span></div>", unsafe_allow_html=True)
        uploaded_bill = st.file_uploader("Upload Utility Bill (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded_bill is not None:
            if st.button("Extract Energy Usage"):
                with st.spinner("Extracting data from bill..."):
                    extracted_text = extract_text_from_file(uploaded_bill)
                    parsed_val = parse_energy_consumption(extracted_text)
                    if parsed_val is not None:
                        st.session_state.extracted_kwh = float(parsed_val)
                        success(f"Extracted {parsed_val} kWh from bill!")
                    else:
                        warning("Could not extract energy consumption. Please enter manually.")

        electricity = st.number_input("Monthly Electricity (kWh)", min_value=0.0, value=float(st.session_state.get('extracted_kwh', 0.0)), step=10.0)
        diet = st.selectbox("Diet Type", ["Vegetarian", "Non-Vegetarian"])

    with col3:
        st.markdown("<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 16px;'><span style='font-size: 24px;'>✈️</span><span style='font-size: 18px; font-weight: 700; color: #000;'>Travel</span></div>", unsafe_allow_html=True)
        flights = st.number_input("Annual Flights", min_value=0, value=0, step=1)
        info("💡 How many long-distance flights per year?")

    col_btn1, col_btn2, col_btn3 = st.columns([1, 1.5, 1])
    with col_btn1:
        reset_btn = st.button("🔄 Reset Assessment", use_container_width=True)
        if reset_btn:
            st.session_state.pop("extracted_kwh", None)
            st.session_state.pop("analysis", None)
            success("✅ Assessment form has been reset.")
            st.rerun()

    with col_btn2:
        st.caption("✔ All input fields are validated before analysis.")
        analyze_btn = st.button("🌿 Analyze My Impact", use_container_width=True)

    if analyze_btn:
        with st.spinner("🌍 Analyzing your carbon footprint..."):
            total, contributors = calculate_footprint(transport, distance, electricity, diet, flights, region)
        eco_score = calculate_eco_score(total, contributors)
        insight, recommendations = generate_recommendations(transport, electricity, diet, flights, contributors)
        save_assessment(user_id, transport, distance, electricity, diet, flights, total, eco_score)
        gf.check_badge_eligibility(user_id)
        st.session_state.analysis = {
            "transport": transport, "distance": distance, "electricity": electricity,
            "diet": diet, "flights": flights, "total": total, "eco_score": eco_score,
            "contributors": contributors, "insight": insight, "recommendations": recommendations,
        }

    if "analysis" in st.session_state:
        data = st.session_state.analysis
        success("✅ Analysis completed!")
        st.markdown("---")
        st.markdown("### 👤 Your Inputs")
        c1, c2 = st.columns(2)
        with c1:
            st.write(f"**🚗 Transport:** {data['transport']}")
            st.write(f"**📍 Daily Distance:** {data['distance']} km")
            st.write(f"**⚡ Electricity:** {data['electricity']} kWh")
        with c2:
            st.write(f"**🥗 Diet:** {data['diet']}")
            st.write(f"**✈️ Annual Flights:** {data['flights']}")
        st.markdown("---")
        st.markdown("<div class='section-header'>📊 Your Carbon Footprint Analysis</div>", unsafe_allow_html=True)
    
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌍 Total Footprint", f"{data['total']:.2f} kg CO₂")
        with col2:
            st.metric("🌱 Eco Score", f"{data['eco_score']}/100")
        
        st.markdown("### 💡 AI Insight")
        info(data["insight"])
        st.markdown("### 🌱 Recommendations")
        for rec in data["recommendations"]:
            success(rec)
    else:
        st.markdown("""
        <style>
        @keyframes bounce {
            0%,100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        .empty-card{
            background: linear-gradient(135deg,#132238,#0f172a);
            border:1px solid rgba(74,222,128,0.25);
            border-radius:20px;
            padding:45px 35px;
            text-align:center;
            box-shadow:0 12px 30px rgba(0,0,0,.25);
            margin-top:20px;
        }

        .empty-title{
            font-size:32px;
            font-weight:800;
            color:#4ade80;
            margin-bottom:12px;
        }

        .empty-subtitle{
            color:#cbd5e1;
            font-size:17px;
            line-height:1.8;
            max-width:650px;
            margin:auto;
        }

        .empty-checklist{
            margin-top:28px;
            text-align:left;
            display:inline-block;
            color:#e2e8f0;
            font-size:16px;
            line-height:2;
        }

        .empty-icon{
            font-size:72px;
            animation:bounce 2s infinite;
            margin-bottom:20px;
        }

        .tip-box{
            margin-top:28px;
            background:rgba(74,222,128,.08);
            border-left:5px solid #4ade80;
            padding:18px;
            border-radius:12px;
            color:#d1fae5;
            font-size:15px;
        }
        </style>

        <div class="empty-card">

            <div class="empty-icon">🌱</div>

            <div class="empty-title">
                Welcome to Your Eco Journey
            </div>

            <div class="empty-subtitle">
                Complete your lifestyle profile above and click
                <b>"Analyze My Impact"</b> to generate your first carbon footprint report.
            </div>

            <div class="empty-checklist">
                ✅ Personalized Eco Score<br>
                ✅ Carbon Footprint Dashboard<br>
                ✅ AI Insights & Recommendations<br>
                ✅ Emission Charts & Trends<br>
                ✅ Downloadable PDF Report
            </div>

            <div class="tip-box">
                💡 <b>Tip:</b> Even small lifestyle changes can make a meaningful impact over time.
                Start with your first assessment and track your progress.
            </div>

        </div>
        """, unsafe_allow_html=True)


    st.markdown("---")

    st.markdown("## 🌱 What You'll Unlock")

    col1, col2, col3 = st.columns(3)

    with col1:
        success("📊 Carbon Footprint Dashboard")
        st.caption("Track your yearly emissions.")

    with col2:
        success("🤖 AI Insights")
        st.caption("Get AI-powered analysis.")

    with col3:
        success("💡 Smart Recommendations")
        st.caption("Receive personalized eco tips.")


    st.markdown("---")

    st.markdown("## 🚀 How It Works")

    info("1️⃣ Fill in your lifestyle details")
    info("2️⃣ Click **Analyze My Impact**")
    info("3️⃣ Review your carbon footprint")
    info("4️⃣ Get personalized AI recommendations")
    info("5️⃣ Download your PDF report")

    st.markdown("---")
    st.markdown("## ✨ Why Use EcoBuddy AI?")

    feature1, feature2 = st.columns(2)

    with feature1:
        success("📈 Track your carbon footprint over time")
        success("🤖 AI-powered personalized insights")
        success("📄 Export reports as PDF")

    with feature2:
        success("🌍 Build sustainable habits")
        success("📊 Interactive charts and trends")
        success("🏆 Improve your Eco Score")


    st.markdown("---")

    st.markdown("## 💡 Eco Tips")

    tip_col1, tip_col2 = st.columns(2)

    with tip_col1:
        success("🚶 Walk or cycle for short trips")
        success("💧 Save water whenever possible")
        success("♻️ Recycle household waste")

    with tip_col2:
        success("⚡ Turn off unused appliances")
        success("🚌 Use public transport")
        success("🌱 Plant more trees")

    
        st.markdown("---")

    st.markdown(
        """
        ### 🌍 Every small action matters

        Your sustainability journey starts with a single assessment.
        Complete your profile today and discover simple ways to reduce
        your carbon footprint and make a positive environmental impact.
        """
    )

    st.markdown("---")

    st.markdown("## 🚀 Ready to Begin?")

    success(
        "Complete the lifestyle form above and click **Analyze My Impact** "
        "to generate your first carbon footprint assessment."
    )

with tab_forecast:
    st.markdown("<div class='section-header'>📈 Carbon Emissions Forecasting</div>", unsafe_allow_html=True)
    st.write("Based on your historical logs, here is a projection of your future carbon footprint.")
    
    assessments = get_assessments(user_id)
    if len(assessments) < 5:
        info("We need at least 5 logs to generate a reliable forecast. Keep logging your footprint!")
    else:
        try:
            import pandas as pd
            import plotly.graph_objects as go
            from statsmodels.tsa.arima.model import ARIMA
            import warnings
            warnings.filterwarnings('ignore')
            
            df = pd.DataFrame(assessments, columns=['id', 'date', 'transport', 'distance', 'electricity', 'diet', 'flights', 'footprint', 'eco_score'])
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            ts_data = df['footprint'].values
            
            forecast_line, conf_lower, conf_upper = compute_arima_forecast(tuple(ts_data))
            
            hist_x = list(range(1, len(ts_data) + 1))
            future_x = list(range(len(ts_data), len(ts_data) + len(forecast_line)))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=hist_x, y=list(ts_data), mode='lines+markers', name='Historical Data',
                line=dict(color='#4ade80', width=3)
            ))
            
            fig.add_trace(go.Scatter(
                x=future_x, y=forecast_line, mode='lines+markers', name='Forecast',
                line=dict(color='#f43f5e', width=3, dash='dot')
            ))
            
            fig.add_trace(go.Scatter(
                x=future_x + future_x[::-1],
                y=list(conf_upper) + list(conf_lower)[::-1],
                fill='toself',
                fillcolor='rgba(244, 63, 94, 0.2)',
                line=dict(color='rgba(255,255,255,0)'),
                name='95% Confidence Interval',
                showlegend=True
            ))
            
            fig.update_layout(
                title='Carbon Footprint Forecast',
                xaxis_title='Assessment #',
                yaxis_title='CO₂ Emissions (kg)',
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            if forecast_line[-1] > ts_data[-1]:
                warning("Your footprint is projected to increase. Try adopting more eco-friendly habits!")
            else:
                success("Great job! Your footprint is on a downward trend. Keep it up!")
        except Exception as e:
            error(f"Error generating forecast: {e}")
