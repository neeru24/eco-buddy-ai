"""
Tests for the Sustainability Insights REST API (issue #404 — API Version Prefix).

All endpoint paths must be served under the version prefix defined by
``API_VERSION_PREFIX`` in ``sustainability_api``.  The tests import that
constant directly so they stay in sync if the prefix is ever updated.
"""

import pytest
from api_auth import (
    generate_api_key,
    validate_api_key,
    revoke_api_key,
    list_api_keys,
    authenticate_request,
    init_api_keys_db,
)
from sustainability_api import (
    process_api_request,
    OPENAPI_SPEC,
    SWAGGER_UI_HTML,
    API_VERSION_PREFIX,
)


def setup_module(module):
    """Ensure API-keys DB table is initialised before any test runs."""
    init_api_keys_db()


# ---------------------------------------------------------------------------
# API version prefix
# ---------------------------------------------------------------------------

def test_api_version_prefix_constant():
    """API_VERSION_PREFIX must be the string '/api/v1'."""
    assert API_VERSION_PREFIX == "/api/v1"


def test_all_openapi_paths_start_with_prefix():
    """Every path in the OpenAPI spec must begin with API_VERSION_PREFIX."""
    for path in OPENAPI_SPEC["paths"]:
        assert path.startswith(API_VERSION_PREFIX), (
            f"OpenAPI path '{path}' does not start with '{API_VERSION_PREFIX}'"
        )


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def test_generate_and_validate_api_key():
    key_info = generate_api_key("Test Service App", user_id="test_user_1")
    assert key_info["app_name"] == "Test Service App"
    assert key_info["api_key"].startswith("eco_live_")
    assert key_info["key_prefix"].startswith("eco_live_")

    # Validate raw key
    validated = validate_api_key(key_info["api_key"])
    assert validated is not None
    assert validated["app_name"] == "Test Service App"
    assert validated["user_id"] == "test_user_1"

    # Revoke key
    revoked = revoke_api_key(key_info["id"])
    assert revoked is True

    # Validate after revocation
    assert validate_api_key(key_info["api_key"]) is None


def test_authenticate_request_headers():
    key_info = generate_api_key("Auth Header Test", user_id="test_user_2")
    raw_key = key_info["api_key"]

    # X-API-Key header
    is_auth, res = authenticate_request({"X-API-Key": raw_key})
    assert is_auth is True
    assert res["app_name"] == "Auth Header Test"

    # Bearer authorisation header
    is_auth_b, res_b = authenticate_request({"Authorization": f"Bearer {raw_key}"})
    assert is_auth_b is True
    assert res_b["app_name"] == "Auth Header Test"

    # Invalid header
    is_auth_inv, res_inv = authenticate_request({"X-API-Key": "invalid_key_value"})
    assert is_auth_inv is False
    assert "Invalid" in res_inv

    # Missing header
    is_auth_m, res_m = authenticate_request({})
    assert is_auth_m is False
    assert "Missing" in res_m


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

def test_api_health_endpoint():
    code, data, content_type = process_api_request("GET", f"{API_VERSION_PREFIX}/health", {})
    assert code == 200
    assert data["status"] == "healthy"
    assert data["api_prefix"] == API_VERSION_PREFIX
    assert content_type == "application/json"


def test_api_openapi_spec():
    code, data, content_type = process_api_request("GET", f"{API_VERSION_PREFIX}/openapi.json", {})
    assert code == 200
    assert data["openapi"] == "3.0.3"
    assert f"{API_VERSION_PREFIX}/insights/calculate" in data["paths"]
    assert content_type == "application/json"


def test_api_swagger_ui_docs_versioned():
    code, data, content_type = process_api_request("GET", f"{API_VERSION_PREFIX}/docs", {})
    assert code == 200
    assert "SwaggerUIBundle" in data
    assert content_type == "text/html"


def test_api_swagger_ui_docs_legacy():
    """Legacy /docs route must still work for backward compatibility."""
    code, data, content_type = process_api_request("GET", "/docs", {})
    assert code == 200
    assert "SwaggerUIBundle" in data
    assert content_type == "text/html"


# ---------------------------------------------------------------------------
# Auth/keys endpoint
# ---------------------------------------------------------------------------

def test_api_create_key_endpoint():
    code, data, _ = process_api_request(
        "POST",
        f"{API_VERSION_PREFIX}/auth/keys",
        {},
        body={"app_name": "API Provision App"},
    )
    assert code == 201
    assert data["success"] is True
    assert "api_key" in data["data"]


def test_api_create_key_missing_app_name():
    code, data, _ = process_api_request(
        "POST", f"{API_VERSION_PREFIX}/auth/keys", {}, body={}
    )
    assert code == 400
    assert "app_name" in data["message"]


# ---------------------------------------------------------------------------
# Protected endpoints
# ---------------------------------------------------------------------------

def test_api_calculate_insights_unauthorized():
    code, data, _ = process_api_request(
        "POST", f"{API_VERSION_PREFIX}/insights/calculate", {}, body={}
    )
    assert code == 401
    assert data["error"] == "Unauthorized"


def test_api_calculate_insights_success():
    key_info = generate_api_key("Calc Test App")
    headers = {"X-API-Key": key_info["api_key"]}
    body = {
        "transport": "Car",
        "distance": 20.0,
        "electricity": 300.0,
        "diet": "Non-Vegetarian",
        "flights": 3,
    }
    code, data, _ = process_api_request(
        "POST", f"{API_VERSION_PREFIX}/insights/calculate", headers, body=body
    )
    assert code == 200
    assert data["success"] is True
    assert "annual_footprint_kg_co2" in data["data"]
    assert "eco_score" in data["data"]
    assert "recommendations" in data["data"]


def test_api_unknown_endpoint_returns_404():
    """Requests to non-existent versioned routes must return 404."""
    key_info = generate_api_key("404 Test App")
    headers = {"X-API-Key": key_info["api_key"]}
    code, data, _ = process_api_request("GET", f"{API_VERSION_PREFIX}/nonexistent", headers)
    assert code == 404
    assert data["error"] == "Not Found"
