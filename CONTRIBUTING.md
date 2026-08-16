# 🤝 Contributing to EcoBuddy AI

First off, thank you for considering contributing to **EcoBuddy AI**! 🌱

We welcome contributions of all kinds, including bug fixes, new features, documentation improvements, performance enhancements, and testing. Every contribution helps make EcoBuddy AI better for everyone.

---

# Table of Contents

* Ways to Contribute
* Getting Started
* Development Setup
* Branch Naming
* Commit Messages
* Pull Request Guidelines
* Coding Standards
* Adding a Calculator Plugin
* Reporting Bugs
* Suggesting Features
* Testing
* Community Guidelines

---

# Ways to Contribute

You can contribute by:

* 🐛 Fixing bugs
* ✨ Adding new features
* 📚 Improving documentation
* 🧪 Writing or improving tests
* ⚡ Optimizing performance
* 🎨 Improving the user interface
* 🔒 Enhancing security
* 📝 Improving code readability

---

# Getting Started

## 1. Fork the Repository

Fork the project to your GitHub account.

## 2. Clone Your Fork

```bash
git clone https://github.com/<your-username>/eco-buddy-ai.git
cd eco-buddy-ai
```

## 3. Create a Virtual Environment

### Windows

```bash
python -m venv venv
venv\Scripts\activate
```

### macOS/Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

## 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the Application

```bash
streamlit run app.py
```

---

# Development Setup

Before making changes:

* Ensure all dependencies are installed.
* Create a new branch for your work.
* Test your changes before submitting a pull request.

---

# Branch Naming

Use descriptive branch names such as:

```
feature/add-pdf-export
feature/improve-dashboard
bugfix/database-error
docs/update-readme
test/add-emission-tests
refactor/recommendation-engine
```

---

# Commit Messages

Write concise and meaningful commit messages.

Examples:

```
feat: add eco score calculation
fix: resolve SQLite connection issue
docs: update installation guide
test: add recommendation unit tests
refactor: simplify emission calculations
```

---

# Pull Request Guidelines

Before submitting a pull request:

* Ensure your branch is up to date with the main branch.
* Keep pull requests focused on a single change.
* Update documentation if necessary.
* Include tests for new functionality.
* Ensure existing tests continue to pass.

Your pull request should include:

* A clear description of the changes
* Screenshots (if UI changes were made)
* Related issue number (if applicable)

Example:

```
Closes #12
```

---

# Coding Standards

Please follow these guidelines:

* Follow PEP 8 style guidelines for Python.
* Use meaningful variable and function names.
* Keep functions small and focused.
* Add comments where necessary.
* Remove unused imports and code.
* Write readable and maintainable code.

---

# Caching Strategy

EcoBuddy AI uses a centralized caching layer for predictable and maintainable cache behavior.

## Architecture

- **`cache_config.py`** — TTL policies and cache categories (single source of truth)
- **`cache.py`** — Reusable `@cached()` decorator wrapping `st.cache_data`
- **`invalidation.py`** — Dependency-aware cache invalidation registry
- **`cache_metrics.py`** — Cache performance metrics (hits, misses, invalidations)

## Using the Cache Decorator

```python
from cache import cached
from cache_config import TTL_DB_READ, CACHE_CATEGORY_DB_READS

@cached(category=CACHE_CATEGORY_DB_READS, ttl=TTL_DB_READ)
def get_data(user_id):
    # ... database query ...
    return data
```

## Cache Categories

| Category | Default TTL | Use Case |
|----------|-------------|----------|
| `db_reads` | 60s | Database read queries |
| `api` | 24h | External API results (Climatiq) |
| `computed` | 5min | Computed analytics (summaries, forecasts) |
| `static` | None | Static/constant data |
| `session` | None | Session-scoped data (OCR, exports) |

## Cache Invalidation

Write operations use centralized invalidation helpers from `invalidation.py`:

```python
from invalidation import invalidate_on_assessment_save

def save_assessment(...):
    # ... database write ...
    invalidate_on_assessment_save()  # Clears dependent caches
```

**Never call `.clear()` directly on cached functions.** Always use the invalidation helpers.

## Adding a New Cached Function

1. Choose the appropriate category from `cache_config.py`
2. Use the `@cached()` decorator with the category and TTL
3. If this function's cache needs invalidation, add a helper to `invalidation.py`
4. Call the invalidation helper from all write operations that affect this data

## Cache Metrics

Enable metrics display in the Streamlit sidebar:

```python
from cache_metrics import render_metrics_sidebar
render_metrics_sidebar()
```

---

# Adding a Calculator Plugin

EcoBuddy AI uses a plugin-based architecture for sustainability calculators. You can add a new calculator without modifying the application's core logic.

## Plugin Architecture Overview

```
plugins/
├── __init__.py          # Auto-discovery registry + lookup API
├── base.py              # CalculatorPlugin ABC + InputField/CalcResult dataclasses
├── carbon_footprint.py  # Carbon footprint calculator (wraps emissions.py)
├── energy_audit.py      # Home energy audit (wraps energy_audit.py)
├── water_footprint.py   # Water footprint (wraps water.py)
└── route_emissions.py   # Trip/route emissions (wraps marketplace.py)
```

### How Discovery Works

1. `plugins/__init__.py` uses `pkgutil.iter_modules()` to scan all `.py` files in the `plugins/` directory.
2. Each module is imported with `importlib.import_module()`.
3. All classes that subclass `CalculatorPlugin` are instantiated and registered by their `name` property.
4. Duplicate names are logged as warnings and rejected (first registration wins).
5. Failed module imports or class instantiations are logged but do not crash the application.

### API

```python
from plugins import discover_plugins, get_all_plugins, get_plugin, get_plugins_by_category

discover_plugins()                         # Trigger discovery (called lazily)
plugins = get_all_plugins()                # dict[str, CalculatorPlugin]
plugin = get_plugin("carbon_footprint")    # Single lookup
water_plugins = get_plugins_by_category("Water")  # Category filter
```

## How to Add a New Plugin

### 1. Create a new file in `plugins/`

```python
from plugins.base import CalculatorPlugin, InputField, CalcResult


class MyNewPlugin(CalculatorPlugin):

    @property
    def name(self) -> str:
        return "my_new_calculator"  # Unique identifier, used for lookup

    @property
    def description(self) -> str:
        return "Description of what this calculator does."

    @property
    def category(self) -> str:
        return "MyCategory"  # Grouping: "Emissions", "Energy", "Water", "Transport"

    def get_input_fields(self) -> list[InputField]:
        return [
            InputField(
                name="my_input",
                label="My Input",
                type="number",        # "number", "select", or "text"
                default=0,
                min_val=0,
                max_val=100,
            ),
        ]

    def calculate(self, inputs: dict) -> CalcResult:
        my_input = inputs.get("my_input", 0)
        result_value = my_input * 2

        return CalcResult(
            total=result_value,
            unit="kg CO2",
            contributors={"My Category": result_value},
            metadata={},
        )

    def get_recommendations(self, result: CalcResult) -> list[str]:
        return [f"Your result is {result.total} {result.unit}."]
```

### 2. That's it!

No registration step is needed. The plugin is **automatically discovered** when the application starts.

### 3. Add tests

```python
from plugins import get_plugin

def test_my_plugin_calculate():
    plugin = get_plugin("my_new_calculator")
    assert plugin is not None
    result = plugin.calculate({"my_input": 5})
    assert result.total == 10
```

## Key Classes

### `InputField`

A frozen dataclass defining a user-facing input.

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Unique field identifier (used as dict key in `inputs`) |
| `label` | `str` | Display label for the UI |
| `type` | `str` | One of `"number"`, `"select"`, `"text"` |
| `default` | `Any` | Default value |
| `options` | `tuple` | Allowed values (for `"select"` type) |
| `min_val` | `float \| None` | Minimum allowed value |
| `max_val` | `float \| None` | Maximum allowed value |
| `help_text` | `str` | Optional tooltip/help text |

Validation rules enforced in `__post_init__`:
- `name` and `label` must be non-empty.
- `type` must be one of the valid types.
- `min_val` must be <= `max_val` if both are provided.

### `CalcResult`

A frozen dataclass returned by `calculate()`.

| Field | Type | Description |
|-------|------|-------------|
| `total` | `float` | The primary result value |
| `unit` | `str` | Unit of the result (e.g., `"kg CO2/year"`) |
| `contributors` | `dict` | Breakdown by category |
| `metadata` | `dict` | Arbitrary extra data (eco scores, warnings, comparisons) |

### `CalculatorPlugin` (ABC)

The abstract base class. Required properties/methods:

| Member | Required | Description |
|--------|----------|-------------|
| `name` | Yes | Unique string identifier |
| `description` | Yes | Human-readable description |
| `category` | Yes | Grouping category |
| `get_input_fields()` | Yes | Returns list of `InputField` |
| `calculate(inputs)` | Yes | Core logic, returns `CalcResult` |
| `get_recommendations(result)` | No | Returns list of recommendation strings (defaults to `[]`) |

## Best Practices

- Keep plugin logic decoupled from the UI layer.
- Store original inputs in `CalcResult.metadata` if needed by `get_recommendations()`.
- Validate inputs in `calculate()` and raise `ValueError` for invalid data.
- Use `metadata` for plugin-specific extra data (not `contributors`).
- Use frozen dataclasses to prevent accidental mutation.
- Write tests for calculate, recommendations, and edge cases.

---

# Reporting Bugs

When reporting a bug, please include:

* Operating system
* Python version
* Steps to reproduce
* Expected behavior
* Actual behavior
* Error messages or logs
* Screenshots (if applicable)

---

# Suggesting Features

Feature requests should include:

* A clear description of the proposed feature
* The problem it solves
* Possible implementation ideas
* Any alternatives considered

---

# Testing

Run all tests before opening a pull request:

```bash
pytest
```

A couple of legacy tests are plain scripts and are run directly:

```bash
python test_db.py
python test_recommendations.py
```

`test_emissions.py` uses `unittest` and can be run with either `pytest` or directly:

```bash
pytest test_emissions.py
# or
python test_emissions.py
```

If you add new functionality, include corresponding tests whenever possible.

---

# Community Guidelines

Please be respectful and constructive when interacting with other contributors.

By participating in this project, you agree to abide by the project's **Code of Conduct**.

---

# Questions?

If you have questions or need assistance, feel free to open a GitHub Issue or start a discussion.

Thank you for contributing to **EcoBuddy AI** and helping build a more sustainable future! 🌱
