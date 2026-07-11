# EcoBuddy AI

EcoBuddy AI is a polished Streamlit-based web application that helps users track, analyze, and reduce their personal carbon footprint using lifestyle inputs.

It converts daily habits into:
- Carbon emissions
- Eco scores
- Visual insights
- Personalized recommendations
  
# Features
- Friendly lifestyle input form for transport, electricity, diet, and flights
- Annual carbon footprint calculation with contributor breakdown
- Eco score and badge system for instant impact feedback
- Animated and modern dashboard layout with insights and recommendations
- Interactive Plotly charts for emission sources and trend tracking
- PDF report export for sharing and record keeping
- Local assessment history to monitor progress over time

---

# Installation

1. Clone or download the repository

```bash
cd eco-buddy-ai
```

2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Set up Environment Variables (for live API integration)

Copy the `.env.example` template to create your own `.env` file:
```bash
cp .env.example .env
```
Open `.env` and replace `your_api_key_here` with your actual Carbon API key (e.g., from Climatiq). If no key is provided, the app will gracefully fall back to using static, offline emission factors.

## Run the app

```bash
streamlit run app.py
```

Then open the local Streamlit link shown in your terminal.

---

# Project Structure


```bash
eco-buddy-ai/
│── app.py                  # Main Streamlit app
│── database.py             # SQLite database logic
│── emissions.py            # Footprint calculation
│── recommendations.py      # Eco suggestions engine
│── requirements.txt        # Dependencies
│── eco_buddy.db            # Local DB (auto-created)
│
├── test_db.py
├── test_emissions.py
└── test_recommendations.py
```

---

- `app.py` — Main Streamlit application and UI
- `database.py` — Database initialization and assessment persistence
- `emissions.py` — Carbon footprint calculation logic
- `recommendations.py` — Eco recommendation generation
- `requirements.txt` — Python project dependencies
- `test_db.py`, `test_emissions.py`, `test_recommendations.py` — Unit tests

---

# How It Works
1. User enters lifestyle data
2. System calculates carbon emissions
3. Eco score is generated
4. AI insights + recommendations are created
5. Results are visualized in charts
6. Data is saved for history tracking
7. PDF report can be downloaded

---

# Key Modules

database.py → Stores user data (SQLite)

emissions.py → Calculates carbon footprint

recommendations.py → Generates eco suggestions

app.py → Streamlit UI + dashboard

---

# Project Goal
Help users understand their carbon footprint and encourage sustainable lifestyle changes through simple insights and tracking.

---

# Output
- Carbon footprint (kg CO₂/year)
- Eco score (0–100)
- Emission breakdown chart
- Trend tracking
- Personalized recommendations

---

# Testing

```bash
python test_db.py
python test_emissions.py
python test_recommendations.py
```

---

# Tech Stack
- Python
- Streamlit
- Pandas
- Matplotlib
- SQLite
- ReportLab

#### EcoBuddy AI helps turn everyday lifestyle choices into actionable environmental insights, promoting a more sustainable future.
### Enjoy your eco journey!

<div align="center">
  
## ❤️ Made with Passion by [neeru24](https://github.com/neeru24)

⭐ If you found this project helpful, consider giving it a star. ⭐

</div>
