"""
Emission Factor Provenance & Versioning Registry.

Every footprint EcoBuddy AI stores is currently unreproducible: `emissions.py`
uses live Climatiq factors when an API key is present and hardcoded constants
when it is not, but `save_assessment()` records only the final number. Two
assessments computed under different factors end up on the same trend line, so
a user can appear to halve their footprint purely because an API key was added.

This module fixes that by making factor sets first-class, immutable and
versioned. A footprint is only meaningful alongside the factor set that
produced it, so every calculation can now be stamped with a version id and
recomputed under any other version.

Design rules
------------
1.  Factor sets are immutable. Updating a factor means registering a new
    version, never mutating an existing one, so historical results never
    change retroactively.
2.  `static-v1` reproduces today's hardcoded constants exactly. Existing rows
    with no recorded version are treated as `static-v1`, so nothing breaks.
3.  Dynamic (API-derived) sets are fingerprinted by their numbers, so two
    identical API responses resolve to the same version id.
"""

import datetime
import hashlib
import json
from typing import Any

from config import (
    DIET_EMISSION_FACTORS,
    TRANSPORT_EMISSION_FACTORS,
    VALID_REGIONS,
)

# --- Factor kinds -----------------------------------------------------------

KIND_STATIC = "static"
KIND_DYNAMIC = "dynamic"

# The default version every historical assessment is assumed to have used.
DEFAULT_VERSION = "static-v1"

# Sanity bounds. A factor outside these ranges is a bad API response or a typo,
# not a real emission factor, and must never enter the registry.
FACTOR_BOUNDS = {
    "transport": (0.0, 2.0),        # kg CO2 per passenger-km
    "electricity": (0.0, 2.0),      # kg CO2 per kWh
    "diet": (0.0, 10000.0),         # kg CO2 per year
    "flight": (0.0, 5000.0),        # kg CO2 per flight
}


class FactorValidationError(ValueError):
    """Raised when a factor set is malformed or physically implausible."""


class UnknownFactorSetError(KeyError):
    """Raised when a requested factor set version is not registered."""


# --- Sources ----------------------------------------------------------------

def make_source(name: str, publisher: str, year: int, region: str = "Global",
                url: str = "", licence: str = "",
                uncertainty_percent: float = 0.0) -> dict[str, Any]:
    """
    Describe where a factor set's numbers came from.

    Provenance is the whole point of this module: a number the app displays
    should be able to cite its publisher and publication year, so a reviewer
    can tell whether it is current.
    """
    return {
        "name": name,
        "publisher": publisher,
        "year": int(year),
        "region": region,
        "url": url,
        "licence": licence,
        "uncertainty_percent": float(uncertainty_percent),
    }


SOURCE_LEGACY = make_source(
    name="EcoBuddy built-in offline factors",
    publisher="EcoBuddy AI project",
    year=2024,
    region="Global",
    url="",
    licence="MIT (project code)",
    uncertainty_percent=25.0,
)

SOURCE_IPCC_STYLE = make_source(
    name="Global average grid and transport factors",
    publisher="EcoBuddy AI project (documented global averages)",
    year=2026,
    region="Global",
    url="",
    licence="MIT (project code)",
    uncertainty_percent=15.0,
)

SOURCE_CLIMATIQ = make_source(
    name="Climatiq live estimate API",
    publisher="Climatiq",
    year=2026,
    region="Varies",
    url="https://api.climatiq.io/data/v1/estimate",
    licence="Per Climatiq terms of use",
    uncertainty_percent=10.0,
)


# --- Factor sets ------------------------------------------------------------

def make_factor_set(version: str, kind: str, effective_date: str, source: dict[str, Any],
                    transport: dict[str, Any], electricity: float, diet: dict[str, Any],
                    flight: float, region: str = "Global", notes: str = "") -> dict[str, Any]:
    """
    Build a factor set record.

    Returns a plain dict so the set round-trips through JSON and SQLite without
    any serialisation glue. Callers must treat the result as read-only —
    `register_factor_set()` deep-copies on the way in and `get_factor_set()`
    deep-copies on the way out, so accidental mutation cannot leak back into
    the registry.
    """
    factor_set = {
        "version": version,
        "kind": kind,
        "effective_date": str(effective_date),
        "region": region,
        "source": dict(source),
        "notes": notes,
        "factors": {
            "transport": dict(transport),
            "electricity": float(electricity),
            "diet": dict(diet),
            "flight": float(flight),
        },
    }
    factor_set["fingerprint"] = factor_set_fingerprint(factor_set)
    return factor_set


def factor_set_fingerprint(factor_set: dict[str, Any]) -> str:
    """
    Deterministic hash of a factor set's numbers only.

    Two sets holding identical factors produce the same fingerprint regardless
    of version label or notes, which is what lets repeated API responses
    resolve to one version instead of accumulating duplicates.
    """
    factors = factor_set["factors"]
    payload = {
        "transport": {key: round(float(value), 6)
                      for key, value in sorted(factors["transport"].items())},
        "electricity": round(float(factors["electricity"]), 6),
        "diet": {key: round(float(value), 6)
                 for key, value in sorted(factors["diet"].items())},
        "flight": round(float(factors["flight"]), 6),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:12]


def validate_factor_set(factor_set: dict[str, Any]) -> bool:
    """
    Reject malformed or physically implausible factor sets.

    Without this a single bad API response — a null, a negative, a value in the
    wrong unit — would silently poison every subsequent calculation.
    """
    for field in ("version", "kind", "effective_date", "source", "factors"):
        if field not in factor_set:
            raise FactorValidationError(f"factor set is missing required field '{field}'")

    if factor_set["kind"] not in (KIND_STATIC, KIND_DYNAMIC):
        raise FactorValidationError(
            f"unknown factor set kind '{factor_set['kind']}'"
        )

    factors = factor_set["factors"]
    for field in ("transport", "electricity", "diet", "flight"):
        if field not in factors:
            raise FactorValidationError(f"factor set is missing factors.{field}")

    if not factors["transport"]:
        raise FactorValidationError("factor set defines no transport modes")
    if not factors["diet"]:
        raise FactorValidationError("factor set defines no diet types")

    _check_bounds(factors["electricity"], "electricity", "electricity")
    _check_bounds(factors["flight"], "flight", "flight")
    for mode, value in factors["transport"].items():
        _check_bounds(value, "transport", f"transport.{mode}")
    for diet_type, value in factors["diet"].items():
        _check_bounds(value, "diet", f"diet.{diet_type}")

    return True


def _check_bounds(value: Any, bound_key: str, label: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise FactorValidationError(f"{label} must be a number, got {value!r}")

    low, high = FACTOR_BOUNDS[bound_key]
    if not (low <= number <= high):
        raise FactorValidationError(
            f"{label} = {number} is outside the plausible range {low}–{high}"
        )
    return number


# --- The registry -----------------------------------------------------------

_REGISTRY = {}


def register_factor_set(factor_set: dict[str, Any], overwrite: bool = False) -> str:
    """
    Add a factor set to the registry after validating it.

    Refuses to overwrite an existing version unless explicitly told to, because
    silently redefining a version is exactly the retroactive-history problem
    this module exists to prevent.
    """
    validate_factor_set(factor_set)
    version = factor_set["version"]
    if version in _REGISTRY and not overwrite:
        raise FactorValidationError(
            f"factor set '{version}' is already registered; "
            "register a new version instead of redefining an existing one"
        )
    _REGISTRY[version] = json.loads(json.dumps(factor_set))
    return version


def get_factor_set(version: str) -> dict[str, Any]:
    """Return a deep copy of a registered factor set."""
    if version not in _REGISTRY:
        raise UnknownFactorSetError(
            f"unknown emission factor version '{version}'. "
            f"Known versions: {', '.join(sorted(_REGISTRY))}"
        )
    return json.loads(json.dumps(_REGISTRY[version]))


def has_factor_set(version: str) -> bool:
    """True if the version is registered."""
    return version in _REGISTRY


def list_factor_versions(kind: str | None = None) -> list[str]:
    """Registered versions, optionally filtered by kind, sorted by date."""
    versions = [
        version for version, factor_set in _REGISTRY.items()
        if kind is None or factor_set["kind"] == kind
    ]
    return sorted(versions, key=lambda v: (_REGISTRY[v]["effective_date"], v))


def get_latest_factor_set(kind: str = KIND_STATIC) -> dict[str, Any]:
    """The most recently effective registered set of the given kind."""
    versions = list_factor_versions(kind=kind)
    if not versions:
        raise UnknownFactorSetError(f"no factor sets registered for kind '{kind}'")
    return get_factor_set(versions[-1])


def find_by_fingerprint(fingerprint: str) -> str | None:
    """Return the version whose numbers hash to this fingerprint, or None."""
    for version, factor_set in _REGISTRY.items():
        if factor_set.get("fingerprint") == fingerprint:
            return version
    return None


# --- Built-in sets ----------------------------------------------------------

# static-v1 mirrors the constants currently hardcoded in config.py and
# emissions.py. It exists so every pre-existing assessment has a real, citable
# version rather than an unknown one, and so this change stays byte-compatible.
register_factor_set(make_factor_set(
    version="static-v1",
    kind=KIND_STATIC,
    effective_date="2024-01-01",
    source=SOURCE_LEGACY,
    transport=dict(TRANSPORT_EMISSION_FACTORS),
    electricity=0.82,
    diet=dict(DIET_EMISSION_FACTORS),
    flight=250.0,
    region="Global",
    notes=(
        "Reproduces the original built-in offline factors exactly. "
        "Assessments saved before factor versioning are assumed to use this set."
    ),
))

# static-v2 is a documented refresh: grid intensity has fallen materially as
# renewables have grown, and the original 0.82 kg/kWh global average is now
# too high. Registering it as a new version means past results keep their old
# factors instead of being silently rewritten.
register_factor_set(make_factor_set(
    version="static-v2",
    kind=KIND_STATIC,
    effective_date="2026-01-01",
    source=SOURCE_IPCC_STYLE,
    transport={
        "Car": 0.19,
        "Bike": 0.0,
        "Public Transport": 0.07,
        "Walking": 0.0,
    },
    electricity=0.48,
    diet={
        "Vegetarian": 950.0,
        "Non-Vegetarian": 1750.0,
    },
    flight=235.0,
    region="Global",
    notes=(
        "Refreshed global averages. Grid intensity lowered to reflect the "
        "growing renewable share; road transport lowered to reflect fleet "
        "electrification."
    ),
))


def _build_candidate_set(api_payload: dict[str, Any], region: str,
                         effective_date: str | None = None,
                         base_version: str = DEFAULT_VERSION) -> dict[str, Any]:
    """
    Assemble a factor set from an API payload.

    The API only supplies electricity and flight factors, so transport and diet
    are inherited from a static base set — and that inheritance is recorded in
    the notes so a reader can tell which numbers were live and which were
    fallbacks.
    """
    base = get_factor_set(base_version)
    candidate = make_factor_set(
        version="pending",
        kind=KIND_DYNAMIC,
        effective_date=effective_date or datetime.date.today().isoformat(),
        source=SOURCE_CLIMATIQ,
        transport=base["factors"]["transport"],
        electricity=api_payload.get("electricity", base["factors"]["electricity"]),
        diet=base["factors"]["diet"],
        flight=api_payload.get("flight", base["factors"]["flight"]),
        region=region,
        notes=(
            f"Electricity and flight factors from the live API; transport and "
            f"diet inherited from {base_version}."
        ),
    )
    validate_factor_set(candidate)
    return candidate


def register_dynamic_factor_set(api_payload: dict[str, Any], region: str = "Global",
                                effective_date: str | None = None,
                                base_version: str = DEFAULT_VERSION) -> str:
    """
    Wrap a live API response into a validated, fingerprinted factor set.

    Returns the version id. An API response whose numbers match a set already
    in the registry resolves to that version rather than creating a duplicate.
    """
    candidate = _build_candidate_set(api_payload, region, effective_date, base_version)

    existing = find_by_fingerprint(candidate["fingerprint"])
    if existing:
        return existing

    version = f"dynamic-{region.lower()}-{candidate['fingerprint']}"
    candidate["version"] = version
    register_factor_set(candidate)
    return version


def resolve_factor_set(region: str = "Global",
                       api_factors: dict[str, Any] | None = None) -> str:
    """
    Identify the factor set a calculation is actually using.

    Resolution is by fingerprint, not by recency. That distinction matters: the
    offline fallback in emissions.py still uses the original 0.82 kg/kWh and
    250 kg/flight constants, so it must resolve to static-v1 even though
    static-v2 is newer. Returning "the latest set" here would stamp results
    with factors that did not produce them, which is precisely the mislabelling
    this module exists to prevent.

    Adopting a newer static set is therefore a deliberate change to the
    fallback constants in config.py / emissions.py, not a silent side effect of
    registering one.
    """
    if region not in VALID_REGIONS:
        region = "Global"

    if not api_factors:
        return DEFAULT_VERSION

    try:
        candidate = _build_candidate_set(api_factors, region)
    except FactorValidationError:
        # A bad API response must never take down a calculation, and must never
        # be recorded as though it were trustworthy.
        return DEFAULT_VERSION

    existing = find_by_fingerprint(candidate["fingerprint"])
    if existing:
        return existing

    if api_factors.get("is_dynamic"):
        version = f"dynamic-{region.lower()}-{candidate['fingerprint']}"
        candidate["version"] = version
        register_factor_set(candidate)
        return version

    return DEFAULT_VERSION


# --- Comparison and recalculation -------------------------------------------

def diff_factor_sets(version_a: str, version_b: str) -> dict[str, Any]:
    """
    Per-factor absolute and percentage delta between two versions.

    This is what answers "did my footprint actually fall, or did the factors
    change underneath me?".
    """
    set_a = get_factor_set(version_a)
    set_b = get_factor_set(version_b)

    differences = {}

    for key in ("electricity", "flight"):
        differences[key] = _delta(
            set_a["factors"][key], set_b["factors"][key]
        )

    for group in ("transport", "diet"):
        group_a = set_a["factors"][group]
        group_b = set_b["factors"][group]
        for name in sorted(set(group_a) | set(group_b)):
            differences[f"{group}.{name}"] = _delta(
                group_a.get(name), group_b.get(name)
            )

    changed = {key: value for key, value in differences.items() if value["changed"]}
    return {
        "from_version": version_a,
        "to_version": version_b,
        "differences": differences,
        "changed": changed,
        "changed_count": len(changed),
        "identical": len(changed) == 0,
    }


def _delta(before: float | None, after: float | None) -> dict[str, Any]:
    if before is None or after is None:
        return {
            "before": before,
            "after": after,
            "absolute_change": None,
            "percent_change": None,
            "changed": before != after,
        }
    before = float(before)
    after = float(after)
    absolute = after - before
    percent = (absolute / before * 100.0) if before != 0 else None
    return {
        "before": before,
        "after": after,
        "absolute_change": round(absolute, 6),
        "percent_change": round(percent, 4) if percent is not None else None,
        "changed": abs(absolute) > 1e-9,
    }


def recalculate_with_factor_set(inputs: dict[str, Any], version: str) -> dict[str, Any]:
    """
    Recompute a footprint under an arbitrary registered factor set.

    `inputs` mirrors the arguments `calculate_footprint()` takes:
    transport, distance (km/day), electricity (kWh/month), diet, flights (per year).

    Deliberately kept independent of `emissions.py` so a historical result can
    be reproduced without dragging in the live API path.
    """
    factor_set = get_factor_set(version)
    factors = factor_set["factors"]

    transport = inputs.get("transport")
    diet = inputs.get("diet")

    if transport not in factors["transport"]:
        raise FactorValidationError(
            f"factor set '{version}' has no factor for transport mode '{transport}'"
        )
    if diet not in factors["diet"]:
        raise FactorValidationError(
            f"factor set '{version}' has no factor for diet '{diet}'"
        )

    distance = max(0.0, float(inputs.get("distance", 0) or 0))
    electricity = max(0.0, float(inputs.get("electricity", 0) or 0))
    flights = max(0, int(inputs.get("flights", 0) or 0))

    contributors = {
        "Transport": round(factors["transport"][transport] * distance * 365, 2),
        "Electricity": round(electricity * factors["electricity"] * 12, 2),
        "Diet": round(float(factors["diet"][diet]), 2),
        "Flights": round(flights * factors["flight"], 2),
    }
    total = round(sum(contributors.values()), 2)

    return {
        "version": version,
        "fingerprint": factor_set["fingerprint"],
        "total_kg": total,
        "contributors": contributors,
    }


def compare_assessment_across_versions(inputs: dict[str, Any],
                                       versions: list[str]) -> dict[str, Any]:
    """
    Recompute one set of inputs under several factor versions.

    Holding the inputs constant isolates the effect of the factors themselves,
    which is the only honest way to tell a real behaviour change from a
    factor-set change.
    """
    results = [recalculate_with_factor_set(inputs, version) for version in versions]
    totals = [result["total_kg"] for result in results]

    return {
        "inputs": dict(inputs),
        "results": results,
        "min_kg": min(totals) if totals else 0.0,
        "max_kg": max(totals) if totals else 0.0,
        "spread_kg": round(max(totals) - min(totals), 2) if totals else 0.0,
        "spread_percent": (
            round((max(totals) - min(totals)) / min(totals) * 100.0, 2)
            if totals and min(totals) > 0 else 0.0
        ),
    }


def explain_footprint_change(inputs_before: dict[str, Any], inputs_after: dict[str, Any],
                             version_before: str, version_after: str) -> dict[str, Any]:
    """
    Split a footprint change into the part caused by behaviour and the part
    caused by the factor set changing underneath the user.

    The behaviour component holds the factors fixed at the newer version and
    varies only the inputs; the factor component holds the older inputs fixed
    and varies only the version. Together they reconstruct the total change.
    """
    actual_before = recalculate_with_factor_set(inputs_before, version_before)["total_kg"]
    actual_after = recalculate_with_factor_set(inputs_after, version_after)["total_kg"]

    behaviour_before = recalculate_with_factor_set(inputs_before, version_after)["total_kg"]
    factor_effect = behaviour_before - actual_before
    behaviour_effect = actual_after - behaviour_before

    total_change = actual_after - actual_before
    return {
        "total_change_kg": round(total_change, 2),
        "behaviour_change_kg": round(behaviour_effect, 2),
        "factor_change_kg": round(factor_effect, 2),
        "comparable": version_before == version_after,
        "before_kg": actual_before,
        "after_kg": actual_after,
    }


# --- Provenance presentation ------------------------------------------------

def describe_provenance(version: str) -> str:
    """Human-readable citation for the UI, the audit log and the PDF report."""
    factor_set = get_factor_set(version)
    source = factor_set["source"]
    return (
        f"{source['name']} — {source['publisher']}, {source['year']} "
        f"(version {factor_set['version']}, effective {factor_set['effective_date']}, "
        f"region {factor_set['region']}, ±{source['uncertainty_percent']:.0f}%)"
    )


def provenance_block(version: str) -> dict[str, Any]:
    """Structured provenance for embedding in the existing audit log dict."""
    factor_set = get_factor_set(version)
    return {
        "factor_version": factor_set["version"],
        "factor_kind": factor_set["kind"],
        "fingerprint": factor_set["fingerprint"],
        "effective_date": factor_set["effective_date"],
        "region": factor_set["region"],
        "notes": factor_set["notes"],
        "source": factor_set["source"],
        "factors": factor_set["factors"],
        "citation": describe_provenance(version),
    }


def normalize_version(version: str | None) -> str:
    """
    Map a stored value onto a usable version id.

    Rows written before factor versioning existed have NULL here, and are
    treated as static-v1 because that is exactly what they were computed with.
    """
    if not version:
        return DEFAULT_VERSION
    if not has_factor_set(version):
        return DEFAULT_VERSION
    return version


def group_assessments_by_version(assessments: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """
    Bucket assessment rows by the factor version they were computed under.

    More than one bucket means the trend line is mixing incomparable numbers,
    which the dashboard should warn about.
    """
    groups = {}
    for row in assessments or []:
        if isinstance(row, dict):
            version = normalize_version(row.get("factor_version"))
        elif isinstance(row, (list, tuple)) and len(row) >= 10:
            version = normalize_version(row[9])
        else:
            version = DEFAULT_VERSION
        groups.setdefault(version, []).append(row)
    return groups


def is_history_comparable(assessments: list[dict[str, Any]]) -> bool:
    """True when every assessment shares one factor version."""
    return len(group_assessments_by_version(assessments)) <= 1
