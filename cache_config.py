"""
Centralized cache configuration for EcoBuddy AI.

Defines TTL policies, cache categories, and size limits as a single source of truth.
All cached functions should reference these constants rather than hardcoding values.
"""

# Cache TTL constants (in seconds)
TTL_EXTERNAL_API = 86400       # 24 hours - external API results (Climatiq, etc.)
TTL_LLM_RESPONSE = 3600        # 1 hour - LLM API responses (Gemini/Groq)
TTL_COMPUTED_ANALYTICS = 300   # 5 minutes - computed analytics (ARIMA, summaries)
TTL_DB_READ = 60               # 1 minute - database read queries
TTL_STATIC_DATA = None         #z No expiry - static/constant data
TTL_SESSION = None             # Session-scoped - per-session data (OCR, exports)
TTL_OCR = None                 # Session-scoped - OCR results (file-hash keyed)

# Cache categories for invalidation grouping
CACHE_CATEGORY_DB_READS = "db_reads"
CACHE_CATEGORY_API = "api"
CACHE_CATEGORY_COMPUTED = "computed"
CACHE_CATEGORY_STATIC = "static"
CACHE_CATEGORY_SESSION = "session"

# Default max cache entries (None = unlimited)
DEFAULT_MAX_ENTRIES = None

# Cache configuration registry
# Maps category -> {ttl, max_entries, description}
CACHE_CATEGORIES = {
    CACHE_CATEGORY_DB_READS: {
        "ttl": TTL_DB_READ,
        "stale_ttl": 30,
        "max_entries": DEFAULT_MAX_ENTRIES,
        "description": "Database read queries - short TTL with event-driven invalidation",
    },
    CACHE_CATEGORY_API: {
        "ttl": TTL_EXTERNAL_API,
        "stale_ttl": 3600,
        "max_entries": 100,
        "description": "External API results - long TTL, expensive to fetch",
    },
    CACHE_CATEGORY_COMPUTED: {
        "ttl": TTL_COMPUTED_ANALYTICS,
        "stale_ttl": 300,
        "max_entries": 50,
        "description": "Computed analytics - medium TTL, CPU-bound",
    },
    CACHE_CATEGORY_STATIC: {
        "ttl": TTL_STATIC_DATA,
        "stale_ttl": 0,
        "max_entries": 20,
        "description": "Static/constant data - no expiry needed",
    },
    CACHE_CATEGORY_SESSION: {
        "ttl": TTL_SESSION,
        "stale_ttl": 0,
        "max_entries": DEFAULT_MAX_ENTRIES,
        "description": "Session-scoped data - per-user, per-session",
    },
}
