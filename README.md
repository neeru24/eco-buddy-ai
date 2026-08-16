# 🌱 EcoBuddy AI

**EcoBuddy AI** is a modern **Streamlit-based web application** that helps users understand, track, and reduce their personal carbon footprint through simple lifestyle inputs. By analyzing everyday habits, the application provides meaningful environmental insights, visual analytics, and actionable recommendations to encourage sustainable living.

---
## 📑 Table of Contents

* [✨ Features](#-features)
* [🚀 Getting Started](#-getting-started)

  * [Prerequisites](#prerequisites)
* [📥 Installation](#-installation)
* [🔑 Environment Variables](#-environment-variables)
* [▶️ Running the Application](#️-running-the-application)
* [📂 Project Structure](#-project-structure)
* [⚙️ How It Works](#️-how-it-works)
* [🧩 Core Modules](#-core-modules)
* [📊 Output](#-output)
* [🧪 Testing](#-testing)
* [🛠️ Tech Stack](#️-tech-stack)
* [🎯 Project Goal](#-project-goal)
* [🤝 Contributing](#-contributing)
* [📄 License](#-license)


# ✨ Features

* 🌍 **Carbon Footprint Calculator** – Estimate annual carbon emissions based on transportation, electricity consumption, diet, and air travel.
* 📊 **Interactive Dashboard** – Explore emission breakdowns through dynamic Plotly visualizations.
* 🌿 **Eco Score & Badge System** – Receive an easy-to-understand sustainability score with achievement badges.
* 💡 **Personalized Recommendations** – Get practical suggestions for reducing your environmental impact.
* 📈 **Progress Tracking** – Save assessment history locally to monitor improvements over time.
* 🧘 **AI Eco Persona Generator** – Analyzes your behavior across transport, diet, energy, water, waste, and gamification data to assign a personalized eco persona with strengths, next steps, and a downloadable persona card.
* 📄 **PDF Report Export** – Download detailed carbon footprint reports for future reference or sharing.
* ⚡ **Offline Support** – Automatically falls back to static emission factors if an API key is unavailable.
* 🎨 **Modern User Interface** – Responsive and visually appealing Streamlit dashboard with an intuitive workflow.

---

# 🚀 Getting Started

## Prerequisites

Ensure you have the following installed:

* Python 3.10 or later
* pip (Python package manager)

---

# 📥 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/eco-buddy-ai.git
cd eco-buddy-ai
```

### 2. Create a Virtual Environment (Recommended)

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Variables

EcoBuddy AI supports live carbon emission data through external APIs.

Copy the example environment file:

```bash
cp .env.example .env
```

Open the `.env` file and replace:

```text
your_api_key_here
```

with your actual Carbon API key (for example, from Climatiq).

If no API key is provided, EcoBuddy AI automatically uses built-in offline emission factors so the application remains fully functional.

---

# ▶️ Running the Application

Start the Streamlit application:

```bash
streamlit run app.py
```

After launching, open the local Streamlit URL displayed in your terminal (typically `http://localhost:8501`).

---

# 📂 Project Structure

```text
eco-buddy-ai/
│
├── app.py                     # Main Streamlit application
├── config.py                  # Eco score baseline, sensitivity, and category weights
├── database.py                # SQLite database operations
├── data_io.py                 # Export/import assessment data as JSON or CSV
├── emission_factors.py        # Versioned, sourced emission factor sets and provenance
├── emissions.py               # Carbon emission calculations
├── energy_audit.py            # Home appliance energy, cost, and solar ROI calculations
├── gamification.py            # XP, levels, streaks, challenges, and achievement badges
├── goals.py                   # Reduction goals, pathways, progress status, and category allocation
├── llm_parser.py              # Parses natural-language quick-log entries (Gemini/Groq)
├── marketplace.py             # Trip emissions, transit comparisons, and carbon offsets
├── ocr_utils.py               # OCR text extraction from uploaded bills/receipts
├── recommendations.py         # Personalized recommendation engine
├── report.py                  # PDF report generation
├── requirements.txt           # Project dependencies
├── units.py                   # Unit conversion, currency, and localized formatting
├── water.py                   # Household water footprint calculations
├── eco_buddy.db               # Local SQLite database (auto-generated)
│
├── pages/                      # Streamlit multi-page app sections
│   ├── Carbon_Footprint.py
│   ├── Data_Health.py
│   ├── Data_Portability.py
│   ├── Display_Settings.py
│   ├── Emission_Factors.py
│   ├── Gamification.py
│   ├── Home_Energy_Audit.py
│   ├── Reduction_Goals.py
│   ├── Route_Planning.py
│   └── Water_Footprint.py
│
├── styles/
│   └── theme.py                # Shared custom CSS theme applied across pages
│
├── test_data_io.py
├── test_data_quality.py
├── test_database_crud.py
├── test_db.py
├── test_emission_factors.py
├── test_emissions.py
├── test_energy_audit.py
├── test_gamification.py
├── test_goals.py
├── test_marketplace.py
├── test_recommendations.py
├── test_units.py
└── test_water.py
```

---

# ⚙️ How It Works

1. Users enter their lifestyle information.
2. The application calculates annual carbon emissions.
3. An Eco Score is generated.
4. Personalized sustainability recommendations are provided.
5. Interactive charts visualize emission sources.
6. Assessment history is stored locally.
7. A downloadable PDF report is generated.

---

# 🧩 Core Modules

| Module               | Description                                        |
| -------------------- | -------------------------------------------------- |
| `app.py`             | Main Streamlit interface and dashboard             |
| `config.py`          | Central configuration for eco-score baseline and category weights |
| `database.py`        | Initializes SQLite database and stores assessments |
| `data_io.py`         | Exports/imports assessment data as JSON or CSV     |
| `emission_factors.py` | Immutable versioned emission factor sets with source provenance, cross-version recalculation, and diffing |
| `emissions.py`       | Calculates annual carbon emissions                 |
| `eco_persona.py`     | Analyzes user behavior and assigns a personalized eco persona with strengths, improvement opportunities, and a downloadable persona card |
| `energy_audit.py`    | Calculates appliance energy use, cost, and solar payback/ROI |
| `gamification.py`    | Manages XP, levels, streaks, challenges, and badges |
| `goals.py`           | Reduction goal pathways, on-track status, projections, and per-category reduction allocation |
| `llm_parser.py`      | Parses natural-language quick-log text into structured data |
| `marketplace.py`     | Calculates trip emissions, transit comparisons, and carbon offsets |
| `ocr_utils.py`       | Extracts text from uploaded PDFs/images for auto data entry |
| `recommendations.py` | Generates personalized eco-friendly suggestions    |
| `report.py`          | Generates downloadable PDF footprint reports       |
| `units.py`           | Metric/imperial conversion, currency formatting, and per-user display preferences |
| `water.py`           | Calculates household water footprint from daily habits |
| `styles/theme.py`    | Applies the shared custom CSS theme across pages   |
| `pages/*.py`         | Streamlit multi-page sections (Carbon Footprint, Water Footprint, Home Energy Audit, Route Planning, Gamification, Eco Persona, Data Portability) |

---

# 📊 Output

EcoBuddy AI provides:

* 🌍 Annual Carbon Footprint (kg CO₂/year)
* ⭐ Eco Score (0–100)
* 🏅 Sustainability Badge
* 📈 Interactive Emission Breakdown Charts
* 📉 Historical Progress Tracking
* 💡 Personalized Sustainability Recommendations
* 📄 Downloadable PDF Report

---

# 🧪 Testing

Most tests use **pytest**. Run the full suite with:

```bash
pytest
```

A couple of legacy tests are plain scripts (no assertions) and are run directly:

```bash
python test_db.py
python test_recommendations.py
```

`test_emissions.py` is written with `unittest` and can be run either way:

```bash
pytest test_emissions.py
# or
python test_emissions.py
```

---

# 🛠️ Tech Stack

* Python
* Streamlit
* Pandas
* Plotly
* Matplotlib
* SQLite
* ReportLab

---

# 🎯 Project Goal

EcoBuddy AI aims to empower individuals to make environmentally conscious decisions by transforming everyday lifestyle choices into clear, actionable sustainability insights.

Through carbon tracking, visual analytics, and personalized recommendations, the project encourages users to adopt greener habits and contribute to a more sustainable future.

---

# 🤝 Contributing

Contributions are welcome!

If you'd like to improve EcoBuddy AI:

1. Fork the repository.
2. Create a feature branch.
3. Commit your changes.
4. Open a Pull Request.

Please ensure your code follows the project's style guidelines and includes appropriate tests where applicable.

---

# 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

 feature/input-validation-and-error-handling
#### EcoBuddy AI helps turn everyday lifestyle choices into actionable environmental insights, promoting a more sustainable future.
### Enjoy your eco journey!

<div align="center">
  

<div align="center">
 
## ❤️ Made with Passion by [neeru24](https://github.com/neeru24)

If you found this project useful, please consider giving it a ⭐ on GitHub.

Together, let's build a greener and more sustainable future! 🌱

</div>
