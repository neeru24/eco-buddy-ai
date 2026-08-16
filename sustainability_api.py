"""
EcoBuddy AI Sustainability Insights REST API Service.

Provides secure REST API endpoints exposing carbon calculations, historical insights,
sustainability recommendations, reduction goals, API key provisioning, and
OpenAPI/Swagger documentation.

All API routes are organised under the version prefix defined by API_VERSION_PREFIX
(currently ``/api/v1``).  Change the constant here to migrate the entire API to a
new version without touching individual route handlers.
"""

import json
import http.server
import urllib.parse
from typing import Any
from emissions import calculate_footprint, calculate_eco_score
from recommendations import generate_recommendations
from database import get_assessments, get_active_goal
from goals import evaluate_progress
from api_auth import authenticate_request, generate_api_key, init_api_keys_db

# ---------------------------------------------------------------------------
# Version prefix — single source of truth for the API version segment.
# Update this constant (e.g. "/api/v2") when introducing a new major version.
# ---------------------------------------------------------------------------
API_VERSION_PREFIX = "/api/v1"


def _route(path: str) -> str:
    """Build a versioned route by prepending API_VERSION_PREFIX."""
    return f"{API_VERSION_PREFIX}{path}"


# ---------------------------------------------------------------------------
# OpenAPI 3.0.3 specification
# ---------------------------------------------------------------------------
OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "EcoBuddy AI Sustainability Insights API",
        "version": "1.0.0",
        "description": (
            "REST API exposing EcoBuddy AI insights for integration with "
            "third-party applications.  All endpoints are accessible under "
            f"the ``{API_VERSION_PREFIX}`` prefix."
        ),
    },
    "servers": [
        {"url": "http://localhost:8000", "description": "Local API Server"}
    ],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
            },
        }
    },
    "security": [
        {"ApiKeyAuth": []},
        {"BearerAuth": []},
    ],
    "paths": {
        _route("/health"): {
            "get": {
                "summary": "Health Check",
                "description": "Check if API service is online.",
                "responses": {
                    "200": {"description": "API is healthy"}
                },
            }
        },
        _route("/auth/keys"): {
            "post": {
                "summary": "Create API Key",
                "description": "Provision a new API key for third-party application integration.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "app_name": {"type": "string", "example": "My Green App"},
                                    "user_id": {"type": "string", "example": "user_123"},
                                },
                                "required": ["app_name"],
                            }
                        }
                    },
                },
                "responses": {
                    "201": {"description": "API Key created successfully"},
                    "400": {"description": "Invalid input"},
                },
            }
        },
        _route("/insights/calculate"): {
            "post": {
                "summary": "Calculate Sustainability Insights",
                "description": (
                    "Calculate annual carbon emissions, Eco Score, and personalised "
                    "insights from lifestyle inputs."
                ),
                "security": [{"ApiKeyAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "transport": {"type": "string", "example": "Car"},
                                    "distance": {"type": "number", "example": 15.0},
                                    "electricity": {"type": "number", "example": 250.0},
                                    "diet": {"type": "string", "example": "Omnivore"},
                                    "flights": {"type": "integer", "example": 2},
                                },
                                "required": ["transport", "distance", "electricity", "diet", "flights"],
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Calculated insights"},
                    "400": {"description": "Bad request / calculation error"},
                    "401": {"description": "Unauthorized"},
                },
            }
        },
        _route("/insights/assessments"): {
            "get": {
                "summary": "Get Historical Assessments",
                "description": "Retrieve a user's historical footprint assessments.",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "schema": {"type": "integer", "default": 10},
                    }
                ],
                "responses": {
                    "200": {"description": "Historical assessment list"},
                    "401": {"description": "Unauthorized"},
                },
            }
        },
        _route("/insights/recommendations"): {
            "get": {
                "summary": "Get Recommendations",
                "description": "Get prioritised action items to lower carbon footprint.",
                "security": [{"ApiKeyAuth": []}],
                "parameters": [
                    {"name": "transport", "in": "query", "schema": {"type": "string"}},
                    {"name": "electricity", "in": "query", "schema": {"type": "number"}},
                    {"name": "diet", "in": "query", "schema": {"type": "string"}},
                    {"name": "flights", "in": "query", "schema": {"type": "integer"}},
                ],
                "responses": {
                    "200": {"description": "Sustainability recommendations"},
                    "401": {"description": "Unauthorized"},
                },
            }
        },
        _route("/insights/goals"): {
            "get": {
                "summary": "Get Active Reduction Goals",
                "description": "Retrieve status and evaluation of active carbon reduction goals.",
                "security": [{"ApiKeyAuth": []}],
                "responses": {
                    "200": {"description": "Active reduction goal and progress evaluation"},
                    "401": {"description": "Unauthorized"},
                },
            }
        },
    },
}

# ---------------------------------------------------------------------------
# Swagger UI HTML — references the versioned OpenAPI spec endpoint
# ---------------------------------------------------------------------------
SWAGGER_UI_HTML = f"""<!DOCTYPE html>
<html>
<head>
  <title>EcoBuddy AI - Swagger UI</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
  <style>
    html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
    *, *:before, *:after {{ box-sizing: inherit; }}
    body {{ margin: 0; background: #fafafa; }}
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
  <script>
    window.onload = function() {{
      window.ui = SwaggerUIBundle({{
        url: '{API_VERSION_PREFIX}/openapi.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIBundle.SwaggerUIStandalonePreset
        ]
      }});
    }};
  </script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Request dispatcher
# ---------------------------------------------------------------------------

def process_api_request(
    method: str,
    path: str,
    headers: dict,
    body: dict = None,
    query_params: dict = None,
) -> tuple:
    """
    Process an API request and return ``(status_code, payload, content_type)``.

    All protected routes require a valid API key supplied via the
    ``X-API-Key`` header or an ``Authorization: Bearer <key>`` header.
    """
    headers = headers or {}
    query_params = query_params or {}

    # ------------------------------------------------------------------ #
    # Public (unauthenticated) endpoints
    # ------------------------------------------------------------------ #

    # Health check
    if method == "GET" and path == _route("/health"):
        return (
            200,
            {
                "status": "healthy",
                "service": "EcoBuddy AI Sustainability Insights API",
                "version": "1.0.0",
                "api_prefix": API_VERSION_PREFIX,
            },
            "application/json",
        )

    # OpenAPI spec
    if method == "GET" and path == _route("/openapi.json"):
        return 200, OPENAPI_SPEC, "application/json"

    # Swagger UI — also reachable via legacy ``/docs`` for convenience
    if method == "GET" and path in ("/docs", _route("/docs")):
        return 200, SWAGGER_UI_HTML, "text/html"

    # Create API Key (developer / public endpoint — no auth required)
    if method == "POST" and path == _route("/auth/keys"):
        app_name = body.get("app_name") if body else None
        if not app_name:
            return (
                400,
                {"error": "Bad Request", "message": "Missing 'app_name' parameter."},
                "application/json",
            )
        user_id = body.get("user_id", "default_user")
        key_data = generate_api_key(app_name, user_id=user_id)
        return (
            201,
            {
                "success": True,
                "message": "API key generated successfully. Save this key — it will not be shown again.",
                "data": key_data,
            },
            "application/json",
        )

    # ------------------------------------------------------------------ #
    # Protected endpoints — authentication required
    # ------------------------------------------------------------------ #
    is_auth, auth_res = authenticate_request(headers)
    if not is_auth:
        return 401, {"error": "Unauthorized", "message": auth_res}, "application/json"

    user_id = auth_res.get("user_id", "default_user")

    # POST /api/v1/insights/calculate
    if method == "POST" and path == _route("/insights/calculate"):
        if not body:
            return (
                400,
                {"error": "Bad Request", "message": "JSON body is required."},
                "application/json",
            )
        try:
            transport = str(body.get("transport", "Car"))
            distance = float(body.get("distance", 10.0))
            electricity = float(body.get("electricity", 150.0))
            diet = str(body.get("diet", "Omnivore"))
            flights = int(body.get("flights", 0))

            footprint, category_breakdown = calculate_footprint(
                transport, distance, electricity, diet, flights
            )
            eco_score = calculate_eco_score(footprint, category_breakdown)
            insight, recs = generate_recommendations(
                transport, electricity, diet, flights, category_breakdown
            )

            return (
                200,
                {
                    "success": True,
                    "data": {
                        "annual_footprint_kg_co2": round(footprint, 2),
                        "eco_score": round(eco_score, 1),
                        "category_breakdown": category_breakdown,
                        "insight": insight,
                        "recommendations": recs,
                    },
                },
                "application/json",
            )
        except Exception as exc:
            return (
                400,
                {"error": "Calculation Error", "message": str(exc)},
                "application/json",
            )

    # GET /api/v1/insights/assessments
    if method == "GET" and path == _route("/insights/assessments"):
        limit = int(query_params.get("limit", [10])[0]) if "limit" in query_params else 10
        raw_assessments = get_assessments() or []
        assessments = []
        for row in raw_assessments[:limit]:
            if isinstance(row, (list, tuple)) and len(row) >= 9:
                assessments.append(
                    {
                        "id": row[0],
                        "date": row[1],
                        "transport": row[2],
                        "distance": row[3],
                        "electricity": row[4],
                        "diet": row[5],
                        "flights": row[6],
                        "footprint_kg": row[7],
                        "eco_score": row[8],
                    }
                )
        return (
            200,
            {"success": True, "count": len(assessments), "data": assessments},
            "application/json",
        )

    # GET /api/v1/insights/recommendations
    if method == "GET" and path == _route("/insights/recommendations"):
        transport = query_params.get("transport", ["Car"])[0]
        electricity = float(query_params.get("electricity", [200.0])[0])
        diet = query_params.get("diet", ["Omnivore"])[0]
        flights = int(query_params.get("flights", [1])[0])

        footprint, category_breakdown = calculate_footprint(
            transport, 10.0, electricity, diet, flights
        )
        eco_score = calculate_eco_score(footprint, category_breakdown)
        insight, recs = generate_recommendations(
            transport, electricity, diet, flights, category_breakdown
        )

        return (
            200,
            {"success": True, "data": {"insight": insight, "recommendations": recs}},
            "application/json",
        )

    # GET /api/v1/insights/goals
    if method == "GET" and path == _route("/insights/goals"):
        goal = get_active_goal(user_id)
        if not goal:
            return (
                200,
                {
                    "success": True,
                    "data": None,
                    "message": "No active reduction goal found for user.",
                },
                "application/json",
            )
        raw_assessments = get_assessments(user_id=user_id) or []
        eval_data = evaluate_progress(goal, raw_assessments)
        return (
            200,
            {"success": True, "data": {"goal": goal, "evaluation": eval_data}},
            "application/json",
        )

    return (
        404,
        {
            "error": "Not Found",
            "message": f"Endpoint '{path}' with method '{method}' not found.",
        },
        "application/json",
    )


# ---------------------------------------------------------------------------
# Standalone HTTP server handler
# ---------------------------------------------------------------------------

class SustainabilityAPIRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP request handler for the standalone EcoBuddy AI REST API server."""

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # Suppress default access-log noise during testing
        pass

    def do_GET(self) -> None:
        self._handle("GET")

    def do_POST(self) -> None:
        self._handle("POST")

    def _handle(self, method: str) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        headers = {k: v for k, v in self.headers.items()}
        body = None
        if "Content-Length" in self.headers:
            content_length = int(self.headers["Content-Length"])
            if content_length > 0:
                raw_body = self.rfile.read(content_length)
                try:
                    body = json.loads(raw_body.decode("utf-8"))
                except json.JSONDecodeError:
                    body = {}

        status_code, response_data, content_type = process_api_request(
            method, path, headers, body=body, query_params=query_params
        )

        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-API-Key, Authorization")
        self.end_headers()

        if content_type == "application/json" and isinstance(response_data, (dict, list)):
            self.wfile.write(json.dumps(response_data, indent=2).encode("utf-8"))
        elif isinstance(response_data, str):
            self.wfile.write(response_data.encode("utf-8"))
