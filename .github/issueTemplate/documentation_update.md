---
name: 📚 Documentation Improvement
about: Suggest improvements to the documentation
title: "[Docs]: "
labels: documentation
assignees: ""
---

# 📚 Documentation Improvement

Thank you for helping improve our documentation! Great documentation makes the project more accessible for everyone.

---

## 📝 Description

Describe the documentation issue or improvement.

---

## 📄 Current Documentation

Specify the file(s) or section(s) that need improvement.

Example:
- README.md
- CONTRIBUTING.md
- docs/setup.md

---

## ✍️ Suggested Improvement

Describe how the documentation could be improved.

---

## 🎯 Why is this improvement needed?

Explain how this change would benefit users or contributors.

Examples:
- Easier onboarding
- More accurate information
- Better examples
- Missing instructions

---

## 📸 Screenshots (Optional)

If applicable, include screenshots that highlight the documentation issue.

---

## 📎 Additional Context

Add any additional information or references.

---

---

# 🏗️ Project Architecture

Eco Buddy AI follows a modular architecture where each component is responsible for a specific part of the application. This separation of responsibilities improves maintainability, readability, scalability, and makes it easier for contributors to understand the overall workflow before making changes.

The application starts from the Streamlit interface (`app.py`), where user interactions are collected and processed. Based on the user's inputs, different modules are called for calculations, recommendations, database operations, PDF generation, and gamification features.
```text
                         ┌────────────────────┐
                         │       User         │
                         └─────────┬──────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │     Streamlit Interface  │
                    │         app.py           │
                    └─────────┬────────────────┘
                              │
      ┌──────────────┬─────────┼──────────┬──────────────┐
      ▼              ▼         ▼          ▼              ▼
 database.py   emissions.py recommendations.py llm_parser.py gamification.py
      │              │         │          │              │
      ▼              ▼         ▼          ▼              ▼
 SQLite DB   Carbon Calculation  AI Suggestions  OCR Parsing  XP & Levels
                              │
                              ▼
                      PDF Report Generator
```

## 📦 Module Responsibilities

### app.py
Acts as the central controller of the application. It handles the Streamlit user interface, collects user inputs, coordinates communication between different modules, displays charts, generates reports, and presents recommendations.

### database.py
Responsible for all database operations including saving assessments, retrieving historical records, updating user information, and maintaining persistent application data.

### emissions.py
Calculates the carbon footprint based on transportation, electricity usage, flights, dietary habits, and other environmental factors. It also generates the overall Eco Score.

### recommendations.py
Produces personalized sustainability recommendations using the calculated environmental impact. Suggestions are tailored according to the user's lifestyle and assessment results.

### llm_parser.py
Processes uploaded utility bills and extracts useful information for automatic electricity consumption estimation.

### gamification.py
Manages experience points (XP), achievement badges, streaks, user levels, and overall engagement features that encourage sustainable habits.

### PDF Report Generator
Creates downloadable assessment reports summarizing carbon emissions, Eco Score, insights, and recommendations in an organized PDF format.


## 🔄 Module Interaction Flow

The modules communicate with one another through the main application (`app.py`).

1. The user submits lifestyle information through the Streamlit interface.
2. The interface validates the provided data.
3. Carbon emissions are calculated using `emissions.py`.
4. Eco Score is generated from the calculated emissions.
5. Personalized recommendations are created using `recommendations.py`.
6. Assessment information is stored in the database through `database.py`.
7. Historical records are retrieved whenever users open the Assessment History section.
8. PDF reports are generated on demand using ReportLab.
9. Gamification statistics are updated based on completed assessments.
10. Results are displayed back to the user through interactive charts and visual dashboards.

## 📊 Application Data Flow

The following sequence describes how information travels through the application.

User Input

↓

Input Validation

↓

Carbon Footprint Calculation

↓

Eco Score Calculation

↓

Recommendation Generation

↓

Database Storage

↓

Dashboard Visualization

↓

Historical Assessment Tracking

↓

PDF Report Generation


## ✨ Benefits of the Current Architecture

- Modular codebase with clearly separated responsibilities.
- Easy to maintain and extend.
- Better readability for new contributors.
- Simplifies debugging and testing.
- Supports independent development of different modules.
- Encourages code reuse across multiple features.
- Makes future feature integration significantly easier.
- Reduces code duplication throughout the project.
- Provides a scalable structure for long-term development.