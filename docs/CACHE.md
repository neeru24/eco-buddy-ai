# Cache Lifecycle and Stampede Protection

EcoBuddy AI's `cached()` decorator supports fresh TTLs, stale fallback, and
per-key refresh coordination without requiring the Streamlit frontend.

## Lifecycle

For one cache key:

1. **Fresh:** return the cached value while its age is below `ttl`.
2. **Stale:** once fresh TTL expires but the value remains inside `stale_ttl`,
   one caller refreshes while concurrent callers immediately receive stale
   data.
3. **Expired or missing:** one caller computes and concurrent callers wait.
4. **Refresh success:** store the new value and wake waiting callers.
5. **Refresh failure:** return stale data when available; otherwise propagate
   the exception.
6. **Cleanup:** refresh state is released after success or failure.

Locks are per key. Requests for different keys compute concurrently.

## Usage

```python
from cache import cached

@cached(
    ttl=300,
    stale_ttl=900,
    namespace="emission-factors",
)
def load_emission_factors(region):
    ...
```

Existing decorators remain valid:

```python
@cached(category="db_reads", ttl=60)
def load_user_assessments(user_id):
    ...
```

The wrapped function still exposes:

```python
load_user_assessments.clear()
load_user_assessments.cache_info()
```

## Category defaults

`cache_config.py` can provide both `ttl` and `stale_ttl`.

Current defaults include:

- database reads: 60 seconds fresh + 30 seconds stale;
- external APIs: 24 hours fresh + 1 hour stale;
- computed analytics: 5 minutes fresh + 5 minutes stale;
- static/session values: no stale extension.

Callers can override either value.

## Metrics

`cache_metrics.py` records:

- `fresh_hits`;
- `stale_hits`;
- `misses`;
- `refreshes`;
- `refresh_failures`;
- `prevented_duplicate_computations`;
- `invalidations`.

```python
from cache_metrics import get_cache_stats

stats = get_cache_stats("load_emission_factors")
```

The legacy `hits` field remains available as fresh plus stale hits.

## Failure behavior

A refresh exception is returned to the caller when there is no usable stale
entry. The same exception is not swallowed.

When stale data is still allowed, it is returned as a resilience fallback and
`refresh_failures` is incremented.

Refresh locks are always released so future calls can retry.

## Tests

```powershell
python -m pytest test_cache_stampede.py -v
```

The suite uses an injectable fake clock and multithreaded tests. It does not
open Streamlit or sleep for TTL expiration.
