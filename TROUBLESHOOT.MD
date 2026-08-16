# 🛠️ TROUBLESHOOT.md

# EcoBuddy AI Troubleshooting Guide

This document provides solutions to common issues you may encounter while installing, running, or using EcoBuddy AI.

---

# Table of Contents

- Installation Issues
- Virtual Environment Problems
- Dependency Errors
- Streamlit Issues
- Database Issues
- Environment Variable Issues
- PDF Generation Problems
- Plotly Visualization Issues
- Testing Issues
- Common Error Messages
- Getting Help

---

# Installation Issues

## Python Version Not Supported

### Problem

```
Python version not supported
```

### Solution

EcoBuddy AI requires **Python 3.10 or later**.

Check your version:

```bash
python --version
```

or

```bash
python3 --version
```

If necessary, install the latest version from:

https://www.python.org/downloads/

---

# Virtual Environment Problems

## Unable to Activate Virtual Environment

### Windows

If activation is blocked:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate:

```bash
venv\Scripts\activate
```

### macOS/Linux

```bash
source venv/bin/activate
```

If the virtual environment does not exist:

```bash
python -m venv venv
```

---

# Dependency Errors

## ModuleNotFoundError

Example:

```
ModuleNotFoundError: No module named 'streamlit'
```

### Solution

Install project dependencies:

```bash
pip install -r requirements.txt
```

If the problem persists:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Package Installation Failed

Try upgrading pip first:

```bash
python -m pip install --upgrade pip
```

Then reinstall dependencies.

---

# Streamlit Issues

## Streamlit Command Not Found

### Problem

```
streamlit: command not found
```

### Solution

Install Streamlit:

```bash
pip install streamlit
```

Or run using Python:

```bash
python -m streamlit run app.py
```

---

## Application Does Not Open

Run:

```bash
streamlit run app.py
```

Then manually open:

```
http://localhost:8501
```

If another application is already using port 8501:

```bash
streamlit run app.py --server.port 8502
```

---

# Database Issues

## SQLite Database Not Created

If the database file is missing:

- Ensure the application has write permissions.
- Run the application once to initialize the database.
- Verify that the project directory is writable.

---

## Database Locked

Close any applications currently using the SQLite database.

If necessary, stop all running Streamlit instances and restart the application.

---

# Environment Variable Issues

## API Key Not Detected

### Problem

Live carbon data is unavailable.

### Solution

Create a `.env` file:

```bash
cp .env.example .env
```

Add your API key:

```
CARBON_API_KEY=your_actual_api_key
```

Restart the application after updating the file.

---

## No API Key Available

No action is required.

EcoBuddy AI automatically switches to built-in offline emission factors.

---

# PDF Generation Problems

## PDF Cannot Be Generated

Ensure ReportLab is installed:

```bash
pip install reportlab
```

Verify that the output directory has write permissions.

---

# Plotly Visualization Issues

## Charts Not Displaying

Install Plotly:

```bash
pip install plotly
```

Refresh the Streamlit page.

If the issue continues:

```bash
pip install --upgrade plotly
```

---

# Testing Issues

## Tests Fail

Ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

Run tests individually:

```bash
python test_db.py
python test_emissions.py
python test_recommendations.py
```

Read the error output carefully to identify the failing module.

---

# Common Error Messages

## FileNotFoundError

### Cause

A required file is missing.

### Solution

Verify that all project files exist and that you are running commands from the project root.

---

## PermissionError

### Cause

The application cannot read or write files.

### Solution

Run the application with appropriate permissions or move the project to a writable directory.

---

## ImportError

### Cause

Missing or incompatible Python package.

### Solution

Reinstall dependencies:

```bash
pip install -r requirements.txt
```

---

## Address Already in Use

### Cause

Another Streamlit instance is already running.

### Solution

Stop the existing process or run the application on another port:

```bash
streamlit run app.py --server.port 8502
```

---

## Browser Displays Blank Page

Try:

- Refreshing the browser.
- Clearing browser cache.
- Restarting Streamlit.
- Checking the terminal for runtime errors.

---

# Performance Tips

- Close unused browser tabs running Streamlit.
- Avoid running multiple instances simultaneously.
- Use a virtual environment to prevent dependency conflicts.
- Keep project dependencies up to date.

---

# Getting Help

If you continue experiencing issues:

1. Verify you are using Python 3.10 or later.
2. Ensure all dependencies are installed.
3. Check the terminal for detailed error messages.
4. Search existing GitHub Issues.
5. Open a new issue with:
   - Operating system
   - Python version
   - Error message
   - Steps to reproduce
   - Screenshots (if applicable)

---

# Useful Commands

Check Python version:

```bash
python --version
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

Run tests:

```bash
python test_db.py
python test_emissions.py
python test_recommendations.py
```

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

---

## Still Need Help?

If none of the solutions above resolve your issue, please open a GitHub Issue with complete error logs and reproduction steps. This helps maintainers diagnose and resolve problems more efficiently.

Happy coding and thank you for contributing to EcoBuddy AI! 🌱