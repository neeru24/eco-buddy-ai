"""Uncertainty propagation and confidence intervals for footprint estimates.

Every number this app reports is a point estimate. The assessment says 4.2
tonnes, `goals.py` builds a reduction pathway against it, and the trend chart
plots it next to last year's figure as though both were measured. None of them
were. A carbon footprint is an estimate built from remembered activity data
multiplied by emission factors that are themselves ranges, and the app has
never said so.

That silence causes real errors of interpretation:

*   A user compares 4.2 t to last year's 4.4 t, sees a 5% cut and celebrates
    a difference that sits comfortably inside the noise.
*   A reduction pathway inherits a baseline that could be 30% wrong, and no
    one downstream knows it.
*   Nobody can tell which input is worth measuring properly. Reading the gas
    meter might halve the spread; recounting coffees will not move it.

This module answers those three questions and nothing else.

The model
---------
A footprint is a sum of components, each of which is an activity amount times
an emission factor::

    component = amount x factor
    total     = sum(components)

Both terms are uncertain. Activity data is uncertain because of how it was
obtained - a metered reading is tight, a number recalled at the end of the
year is not. Emission factors are uncertain because of how they were derived -
a directly measured factor is tight, a proxy borrowed from a similar activity
is not.

Both are strictly positive and multiplicative in their error, so both are
modelled as lognormal and described by a geometric standard deviation (GSD).
A GSD of 1.25 means roughly "within 25% up or down, one sigma". Two lognormal
GSDs combine in quadrature on the log scale, which is the only place the
arithmetic gets interesting::

    combined = exp(sqrt(ln(a)^2 + ln(b)^2))

Totals are then propagated by Monte Carlo rather than analytically, because a
sum of lognormals has no closed form and because sampling gets the sensitivity
analysis almost for free.

Determinism
-----------
Every entry point takes a seed and defaults to a fixed one. The same inputs
always produce the same interval - a statistics feature whose numbers flicker
between page loads is worse than no feature at all, and it would be untestable
besides.

The module is self-contained: only the standard library is used, its SQLite
table is created lazily, and no shared files are modified.
"""

import os
import json
import math
import random
import sqlite3
import logging
import statistics
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

# Monte Carlo settings. Ten thousand draws puts the Monte Carlo error on a P5
# or P95 estimate well below the width of the interval being reported, which
# is the only precision that matters here. More draws would be spurious
# accuracy on top of factors that are themselves rounded.
DEFAULT_ITERATIONS = 10000
MIN_ITERATIONS = 200
MAX_ITERATIONS = 200000
DEFAULT_SEED = 20260804

# The reported interval. P5-P95 is a 90% interval, which is the convention in
# GHG inventory uncertainty reporting.
LOWER_PERCENTILE = 5
UPPER_PERCENTILE = 95

# How the activity amount was obtained, and the geometric standard deviation
# that implies. These are judgement calls about human data entry, not physical
# measurements, and they are deliberately on the generous side - a footprint
# tool that claims tight activity data is flattering itself.
ACTIVITY_QUALITY = {
    "metered": {
        "label": "Metered reading",
        "gsd": 1.05,
        "description": "Read off a meter or an odometer. Wrong only by transcription.",
    },
    "billed": {
        "label": "From a bill or statement",
        "gsd": 1.12,
        "description": "Taken from a bill. Accurate, but may cover an estimated period.",
    },
    "logged": {
        "label": "Logged at the time",
        "gsd": 1.20,
        "description": "Recorded as it happened, in an app or a notebook.",
    },
    "estimated": {
        "label": "Estimated from a typical week",
        "gsd": 1.35,
        "description": "Scaled up from a representative period. Misses seasonality.",
    },
    "recalled": {
        "label": "Recalled from memory",
        "gsd": 1.55,
        "description": "Answered from memory at the end of the year.",
    },
    "assumed": {
        "label": "Assumed household average",
        "gsd": 1.90,
        "description": "Not supplied at all. A population average standing in.",
    },
}

DEFAULT_ACTIVITY_QUALITY = "estimated"

# How the emission factor was derived. This mirrors the pedigree-matrix idea
# used in life-cycle inventory work: the further a factor is from a direct
# measurement of the exact thing being estimated, the wider its distribution.
#
# `emission_factors.py` already records provenance and distinguishes static
# from API-derived factor sets. `factor_tier_for_kind()` below maps that
# registry vocabulary onto these tiers so the provenance work already in the
# repo finally has a quantitative consequence.
FACTOR_TIER = {
    "measured": {
        "label": "Directly measured",
        "gsd": 1.06,
        "description": "Measured for this exact activity, in this region, this year.",
    },
    "verified": {
        "label": "Verified national statistic",
        "gsd": 1.14,
        "description": "Published and independently verified. Right country, recent.",
    },
    "published": {
        "label": "Published average",
        "gsd": 1.25,
        "description": "A reputable published average, possibly a few years old.",
    },
    "proxy": {
        "label": "Proxy from a similar activity",
        "gsd": 1.50,
        "description": "Borrowed from a related activity or a neighbouring region.",
    },
    "assumed": {
        "label": "Rough assumption",
        "gsd": 2.00,
        "description": "An order-of-magnitude placeholder. Treat with suspicion.",
    },
}

DEFAULT_FACTOR_TIER = "published"

# Mapping from the `emission_factors.py` registry vocabulary onto factor tiers.
# A static built-in constant is a published average; a live API response for
# the user's own region is better than that but not measured for them.
FACTOR_KIND_TIERS = {
    "static": "published",
    "dynamic": "verified",
}

# Above this relative half-width the estimate is too vague to act on, and the
# module says so rather than printing a confident-looking interval.
WIDE_INTERVAL_THRESHOLD = 0.35

# A sensitivity contribution below this is not worth showing anyone.
NEGLIGIBLE_CONTRIBUTION = 0.01

# Probability thresholds for the year-on-year verdict.
STRONG_EVIDENCE = 0.95
MODERATE_EVIDENCE = 0.80


class UncertaintyError(ValueError):
    """Raised when a component or a set of components cannot be modelled."""


# --- Quality vocabulary -----------------------------------------------------


def list_activity_qualities() -> list[dict[str, Any]]:
    """Return the activity data quality levels, tightest first."""
    levels = [
        {"key": key, **details} for key, details in ACTIVITY_QUALITY.items()
    ]
    return sorted(levels, key=lambda item: item["gsd"])


def list_factor_tiers() -> list[dict[str, Any]]:
    """Return the emission factor quality tiers, tightest first."""
    tiers = [{"key": key, **details} for key, details in FACTOR_TIER.items()]
    return sorted(tiers, key=lambda item: item["gsd"])


def activity_gsd(quality: str) -> float:
    """Geometric standard deviation implied by how activity data was obtained."""
    entry = ACTIVITY_QUALITY.get(quality) or ACTIVITY_QUALITY[DEFAULT_ACTIVITY_QUALITY]
    return entry["gsd"]


def factor_gsd(tier: str) -> float:
    """Geometric standard deviation implied by an emission factor's pedigree."""
    entry = FACTOR_TIER.get(tier) or FACTOR_TIER[DEFAULT_FACTOR_TIER]
    return entry["gsd"]


def factor_tier_for_kind(kind: str) -> str:
    """Map an `emission_factors.py` factor-set kind onto a quality tier."""
    return FACTOR_KIND_TIERS.get(kind, DEFAULT_FACTOR_TIER)


# --- Lognormal arithmetic ---------------------------------------------------


def combine_gsd(*gsds: float) -> float:
    """Combine independent geometric standard deviations.

    Multiplicative errors add in quadrature on the log scale, so combining
    two lognormals means combining their log-sigmas, not their GSDs directly.
    A GSD of 1.0 (no uncertainty at all) contributes nothing, which falls out
    of the arithmetic without a special case.
    """
    total = 0.0
    for gsd in gsds:
        try:
            value = float(gsd)
        except (TypeError, ValueError):
            continue
        if value <= 1.0:
            continue
        total += math.log(value) ** 2
    return math.exp(math.sqrt(total))


def gsd_to_relative_spread(gsd: float) -> float:
    """Approximate one-sigma relative spread of a lognormal, as a fraction.

    Reported as the symmetric-ish figure a user expects to see next to a
    number ("plus or minus 22%"). The underlying distribution is not
    symmetric, which is exactly why the percentiles rather than this figure
    drive the reported interval.
    """
    try:
        value = float(gsd)
    except (TypeError, ValueError):
        return 0.0
    if value <= 1.0:
        return 0.0
    sigma = math.log(value)
    return math.sqrt(math.exp(sigma ** 2) - 1.0)


def lognormal_sigma(gsd: float) -> float:
    """Log-scale sigma for a given geometric standard deviation."""
    try:
        value = float(gsd)
    except (TypeError, ValueError):
        return 0.0
    return math.log(value) if value > 1.0 else 0.0


def percentile(sorted_values: list[float], pct: float) -> float:
    """Linear-interpolated percentile of an already-sorted list."""
    if not sorted_values:
        return 0.0
    if len(sorted_values) == 1:
        return float(sorted_values[0])

    rank = (len(sorted_values) - 1) * (max(0.0, min(100.0, float(pct))) / 100.0)
    lower_index = int(math.floor(rank))
    upper_index = int(math.ceil(rank))
    if lower_index == upper_index:
        return float(sorted_values[lower_index])

    weight = rank - lower_index
    lower = float(sorted_values[lower_index])
    upper = float(sorted_values[upper_index])
    return lower + (upper - lower) * weight


# --- Components -------------------------------------------------------------


def build_component(
    name: str,
    amount: float,
    factor: float,
    activity_quality: str = DEFAULT_ACTIVITY_QUALITY,
    factor_tier: str = DEFAULT_FACTOR_TIER,
    unit: str = "",
    category: str = "",
) -> dict[str, Any]:
    """Describe one contribution to a footprint and its uncertainty.

    ``amount`` is activity data in whatever unit the factor expects, and
    ``factor`` converts it to kgCO2e. Negative amounts are rejected outright:
    a component of a footprint is a quantity of something, and a negative one
    is a data error rather than a sequestration credit, which belongs in its
    own accounting line.
    """
    try:
        amount_value = float(amount)
        factor_value = float(factor)
    except (TypeError, ValueError):
        raise UncertaintyError(f"Component '{name}' has a non-numeric amount or factor")

    if amount_value < 0 or factor_value < 0:
        raise UncertaintyError(f"Component '{name}' cannot have a negative amount or factor")
    if math.isnan(amount_value) or math.isnan(factor_value):
        raise UncertaintyError(f"Component '{name}' has a NaN amount or factor")
    if math.isinf(amount_value) or math.isinf(factor_value):
        raise UncertaintyError(f"Component '{name}' has an infinite amount or factor")

    quality = activity_quality if activity_quality in ACTIVITY_QUALITY else DEFAULT_ACTIVITY_QUALITY
    tier = factor_tier if factor_tier in FACTOR_TIER else DEFAULT_FACTOR_TIER
    combined = combine_gsd(activity_gsd(quality), factor_gsd(tier))

    return {
        "name": str(name),
        "category": str(category or ""),
        "unit": str(unit or ""),
        "amount": amount_value,
        "factor": factor_value,
        "emissions": amount_value * factor_value,
        "activity_quality": quality,
        "factor_tier": tier,
        "activity_gsd": activity_gsd(quality),
        "factor_gsd": factor_gsd(tier),
        "combined_gsd": combined,
        "relative_spread": gsd_to_relative_spread(combined),
    }


def point_estimate(components: list[dict[str, Any]]) -> float:
    """Sum of the component point estimates - what the app reports today."""
    return sum(float(component.get("emissions", 0.0)) for component in components or [])


def _validate_components(components: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a usable component list or raise."""
    if not components:
        raise UncertaintyError("At least one component is required")
    cleaned = [component for component in components if component]
    if not cleaned:
        raise UncertaintyError("At least one component is required")
    return cleaned


# --- Monte Carlo propagation ------------------------------------------------


def _clean_iterations(iterations: int) -> int:
    """Clamp an iteration count into a range that is fast and meaningful."""
    try:
        count = int(iterations)
    except (TypeError, ValueError):
        count = DEFAULT_ITERATIONS
    return max(MIN_ITERATIONS, min(MAX_ITERATIONS, count))


def _sample_matrix(
    components: list[dict[str, Any]],
    iterations: int,
    seed: int | None,
) -> list[list[float]]:
    """Draw ``iterations`` lognormal samples for every component.

    Returned as one list of draws per component so the sensitivity analysis
    can reuse exactly the same draws. Sharing the sample matrix means the
    variance reduction attributed to a component is not contaminated by
    Monte Carlo noise from re-sampling, which matters because those
    reductions are often only a few percentage points apart.

    Each component gets its own seeded generator, so adding a component never
    perturbs the draws of the ones before it.
    """
    matrix = []
    for index, component in enumerate(components):
        emissions = float(component.get("emissions", 0.0))
        sigma = lognormal_sigma(component.get("combined_gsd", 1.0))

        if emissions <= 0.0 or sigma <= 0.0:
            matrix.append([emissions] * iterations)
            continue

        rng = random.Random(seed + index * 7919)
        # Shift the log-mean so the *median* of the draws lands on the point
        # estimate. Without this the mean of a lognormal sits above its
        # median and the whole distribution drifts upward, which would make
        # the tool systematically pessimistic for no defensible reason.
        mu = math.log(emissions)
        matrix.append([math.exp(rng.gauss(mu, sigma)) for _ in range(iterations)])
    return matrix


def _column_sums(matrix: list[list[float]], count: int) -> list[float]:
    """Total each Monte Carlo draw across every component."""
    if not matrix:
        return []
    return [sum(component[draw] for component in matrix) for draw in range(count)]


def _summarise(totals: list[float], point: float) -> dict[str, Any]:
    """Turn a list of sampled totals into the reported summary."""
    ordered = sorted(totals)
    mean = statistics.fmean(ordered)
    median = statistics.median(ordered)
    lower = percentile(ordered, LOWER_PERCENTILE)
    upper = percentile(ordered, UPPER_PERCENTILE)
    half_width = (upper - lower) / 2.0
    relative = (half_width / median) if median > 0 else 0.0

    return {
        "point_estimate": point,
        "mean": mean,
        "median": median,
        "lower": lower,
        "upper": upper,
        "interval_width": upper - lower,
        "relative_half_width": relative,
        "standard_deviation": statistics.pstdev(ordered) if len(ordered) > 1 else 0.0,
        "variance": statistics.pvariance(ordered) if len(ordered) > 1 else 0.0,
        "confidence_level": UPPER_PERCENTILE - LOWER_PERCENTILE,
        "is_wide": relative > WIDE_INTERVAL_THRESHOLD,
    }


def propagate(
    components: list[dict[str, Any]],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int | None = DEFAULT_SEED,
) -> dict[str, Any]:
    """Propagate component uncertainty into an interval around the total.

    Returns the point estimate the app shows today alongside the median, the
    P5-P95 interval and the relative half-width - the "plus or minus 28%"
    figure that is the whole reason the module exists.
    """
    cleaned = _validate_components(components)
    count = _clean_iterations(iterations)
    matrix = _sample_matrix(cleaned, count, seed)

    totals = _column_sums(matrix, count)
    if not totals:
        raise UncertaintyError("Propagation produced no samples")

    summary = _summarise(totals, point_estimate(cleaned))
    summary["iterations"] = count
    summary["seed"] = seed
    summary["component_count"] = len(cleaned)
    return summary


def analytical_interval(components: list[dict[str, Any]]) -> dict[str, Any]:
    """Cheap closed-form cross-check on the Monte Carlo result.

    Combines component variances assuming independence. It is not what the
    module reports - the assumption is too strong and the lognormal tails are
    wrong - but a large disagreement with `propagate()` is a good signal that
    something is off, and it costs nothing to compute.
    """
    cleaned = _validate_components(components)
    point = point_estimate(cleaned)
    if point <= 0:
        return {"point_estimate": 0.0, "standard_deviation": 0.0, "relative_half_width": 0.0}

    variance = 0.0
    for component in cleaned:
        emissions = float(component.get("emissions", 0.0))
        spread = gsd_to_relative_spread(component.get("combined_gsd", 1.0))
        variance += (emissions * spread) ** 2

    deviation = math.sqrt(variance)
    return {
        "point_estimate": point,
        "standard_deviation": deviation,
        # 1.645 sigma is the 90% interval half-width for a normal, matching
        # the P5-P95 range the Monte Carlo path reports.
        "relative_half_width": (1.645 * deviation / point) if point > 0 else 0.0,
    }


# --- Sensitivity ------------------------------------------------------------


def sensitivity_ranking(
    components: list[dict[str, Any]],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int | None = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    """Rank components by how much of the total variance each one causes.

    For each component the total is recomputed with that component pinned to
    its point estimate, using the same draws for everything else. The drop in
    variance is the share of the spread that component is responsible for.

    This is the output that makes the feature actionable: it is the
    difference between telling a user their footprint is uncertain and telling
    them which single number to go and measure.
    """
    cleaned = _validate_components(components)
    count = _clean_iterations(iterations)
    matrix = _sample_matrix(cleaned, count, seed)
    totals = _column_sums(matrix, count)

    base_variance = statistics.pvariance(totals) if len(totals) > 1 else 0.0
    total_point = point_estimate(cleaned)
    rankings = []

    for index, component in enumerate(cleaned):
        emissions = float(component.get("emissions", 0.0))
        pinned = [
            totals[draw] - matrix[index][draw] + emissions for draw in range(count)
        ]
        pinned_variance = statistics.pvariance(pinned) if len(pinned) > 1 else 0.0
        reduction = base_variance - pinned_variance
        share = (reduction / base_variance) if base_variance > 0 else 0.0

        rankings.append(
            {
                "name": component.get("name", ""),
                "category": component.get("category", ""),
                "emissions": emissions,
                "emissions_share": (emissions / total_point) if total_point > 0 else 0.0,
                "combined_gsd": component.get("combined_gsd", 1.0),
                "activity_quality": component.get("activity_quality", ""),
                "factor_tier": component.get("factor_tier", ""),
                "variance_share": max(0.0, share),
                "residual_relative_half_width": _relative_half_width(pinned),
                "is_negligible": max(0.0, share) < NEGLIGIBLE_CONTRIBUTION,
            }
        )

    return sorted(rankings, key=lambda item: item["variance_share"], reverse=True)


def _relative_half_width(totals: list[float]) -> float:
    """Relative P5-P95 half-width of a list of sampled totals."""
    ordered = sorted(totals)
    median = statistics.median(ordered)
    if median <= 0:
        return 0.0
    lower = percentile(ordered, LOWER_PERCENTILE)
    upper = percentile(ordered, UPPER_PERCENTILE)
    return ((upper - lower) / 2.0) / median


def improvement_plan(
    components: list[dict[str, Any]],
    target_quality: str = "metered",
    iterations: int = DEFAULT_ITERATIONS,
    seed: int | None = DEFAULT_SEED,
) -> dict[str, Any]:
    """What the interval would look like if each input were measured properly.

    Answers the question a user actually has once they have been shown an
    error bar: *what do I go and do about it?* For each component, the
    activity data quality is upgraded to ``target_quality`` and the whole
    propagation re-run, so the reported saving is the real effect on the
    total rather than a per-component figure that would not compose.

    Components already at or above the target are reported with no gain,
    which is the honest answer and stops the page suggesting a user re-read
    a meter they already read.
    """
    cleaned = _validate_components(components)
    target = target_quality if target_quality in ACTIVITY_QUALITY else "metered"
    target_gsd = activity_gsd(target)

    baseline = propagate(cleaned, iterations=iterations, seed=seed)
    baseline_width = baseline["relative_half_width"]

    actions = []
    for index, component in enumerate(cleaned):
        current_gsd = component.get("activity_gsd", 1.0)
        if current_gsd <= target_gsd:
            actions.append(
                {
                    "name": component.get("name", ""),
                    "current_quality": component.get("activity_quality", ""),
                    "target_quality": target,
                    "already_good": True,
                    "improved_relative_half_width": baseline_width,
                    "reduction": 0.0,
                    "reduction_points": 0.0,
                }
            )
            continue

        upgraded = list(cleaned)
        improved = dict(component)
        improved["activity_quality"] = target
        improved["activity_gsd"] = target_gsd
        improved["combined_gsd"] = combine_gsd(target_gsd, improved.get("factor_gsd", 1.0))
        improved["relative_spread"] = gsd_to_relative_spread(improved["combined_gsd"])
        upgraded[index] = improved

        result = propagate(upgraded, iterations=iterations, seed=seed)
        reduction = baseline_width - result["relative_half_width"]

        actions.append(
            {
                "name": component.get("name", ""),
                "current_quality": component.get("activity_quality", ""),
                "target_quality": target,
                "already_good": False,
                "improved_relative_half_width": result["relative_half_width"],
                "reduction": max(0.0, reduction),
                "reduction_points": max(0.0, reduction) * 100.0,
            }
        )

    actions.sort(key=lambda item: item["reduction"], reverse=True)
    return {
        "baseline_relative_half_width": baseline_width,
        "target_quality": target,
        "actions": actions,
        "best_action": actions[0] if actions and not actions[0]["already_good"] else None,
    }


# --- Comparing two footprints -----------------------------------------------


def compare_footprints(
    before_components: list[dict[str, Any]],
    after_components: list[dict[str, Any]],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int | None = DEFAULT_SEED,
) -> dict[str, Any]:
    """Is the change between two footprints real, or is it noise?

    The naive approach - check whether the two intervals overlap - is well
    known to be over-conservative, so the difference is sampled directly and
    the probability that the second total is genuinely lower is reported.

    The two footprints are sampled with different seed offsets because they
    are separate estimates. Correlated errors between them (the same factor
    used in both years) would narrow the difference, so treating them as
    independent is the conservative choice and it is the one made here.
    """
    before = _validate_components(before_components)
    after = _validate_components(after_components)
    count = _clean_iterations(iterations)

    before_matrix = _sample_matrix(before, count, seed)
    after_matrix = _sample_matrix(after, count, seed + 104729)

    before_totals = _column_sums(before_matrix, count)
    after_totals = _column_sums(after_matrix, count)
    differences = [before_totals[draw] - after_totals[draw] for draw in range(count)]

    reductions = sum(1 for value in differences if value > 0)
    probability = reductions / count

    before_point = point_estimate(before)
    after_point = point_estimate(after)
    change = after_point - before_point
    percent_change = (change / before_point * 100.0) if before_point > 0 else 0.0

    ordered = sorted(differences)
    return {
        "before_point": before_point,
        "after_point": after_point,
        "absolute_change": change,
        "percent_change": percent_change,
        "probability_reduced": probability,
        "difference_median": statistics.median(ordered),
        "difference_lower": percentile(ordered, LOWER_PERCENTILE),
        "difference_upper": percentile(ordered, UPPER_PERCENTILE),
        "verdict": _verdict(probability),
        "explanation": _explanation(probability, percent_change),
        "iterations": count,
    }


def _verdict(probability: float) -> str:
    """Classify the strength of evidence for a real reduction."""
    if probability >= STRONG_EVIDENCE:
        return "reduced"
    if probability >= MODERATE_EVIDENCE:
        return "probably_reduced"
    if probability <= 1.0 - STRONG_EVIDENCE:
        return "increased"
    if probability <= 1.0 - MODERATE_EVIDENCE:
        return "probably_increased"
    return "inconclusive"


def _explanation(probability: float, percent_change: float) -> str:
    """A plain sentence for the verdict, because the number alone gets misread."""
    magnitude = abs(percent_change)
    verdict = _verdict(probability)

    if verdict == "reduced":
        return (
            f"Your footprint really did fall by about {magnitude:.0f}%. "
            f"That change is larger than the uncertainty in the estimate."
        )
    if verdict == "probably_reduced":
        return (
            f"Your footprint probably fell by about {magnitude:.0f}%, but the "
            f"change is close enough to the uncertainty that it is not certain."
        )
    if verdict == "increased":
        return (
            f"Your footprint really did rise by about {magnitude:.0f}%. "
            f"That change is larger than the uncertainty in the estimate."
        )
    if verdict == "probably_increased":
        return (
            f"Your footprint probably rose by about {magnitude:.0f}%, but the "
            f"change is close enough to the uncertainty that it is not certain."
        )
    return (
        f"The {magnitude:.0f}% difference is smaller than the uncertainty in "
        f"both estimates. Treat these two footprints as the same."
    )


def detectable_change(
    components: list[dict[str, Any]],
    iterations: int = DEFAULT_ITERATIONS,
    seed: int | None = DEFAULT_SEED,
) -> dict[str, Any]:
    """Smallest reduction that would be distinguishable from noise.

    Useful before the fact rather than after it: a user setting a 3% annual
    target should be told up front that their data cannot resolve 3%.

    Two independent estimates of similar size each contribute their own
    spread, so the detectable difference is the interval half-width scaled by
    root two.
    """
    summary = propagate(components, iterations=iterations, seed=seed)
    relative = summary["relative_half_width"] * math.sqrt(2.0)
    return {
        "relative_half_width": summary["relative_half_width"],
        "min_detectable_relative": relative,
        "min_detectable_percent": relative * 100.0,
        "min_detectable_absolute": relative * summary["median"],
        "median": summary["median"],
    }


# --- Narrative --------------------------------------------------------------


def format_interval(summary: dict[str, Any], unit: str = "kg CO2e", decimals: int = 0) -> str:
    """Render a summary as the string a user should see in place of a total."""
    median = summary.get("median", 0.0)
    lower = summary.get("lower", 0.0)
    upper = summary.get("upper", 0.0)
    relative = summary.get("relative_half_width", 0.0) * 100.0
    return (
        f"{median:,.{decimals}f} {unit} "
        f"({lower:,.{decimals}f}-{upper:,.{decimals}f}, ±{relative:.0f}%)"
    )


def get_uncertainty_notes(summary: dict[str, Any], rankings: list[dict[str, Any]] | None = None) -> list[str]:
    """Short interpretation notes for a propagated result."""
    notes = []
    relative = summary.get("relative_half_width", 0.0)

    if summary.get("is_wide"):
        notes.append(
            f"This estimate is uncertain to about ±{relative * 100:.0f}%. "
            f"It is fine for spotting big differences and no use at all for "
            f"tracking small ones."
        )
    elif relative > 0.15:
        notes.append(
            f"An uncertainty of ±{relative * 100:.0f}% is normal for a "
            f"footprint built from household data. Changes smaller than that "
            f"are not measurable."
        )
    else:
        notes.append(
            f"±{relative * 100:.0f}% is a tight estimate, which means your "
            f"activity data is unusually good."
        )

    mean = summary.get("mean", 0.0)
    median = summary.get("median", 0.0)
    if median > 0 and (mean - median) / median > 0.05:
        notes.append(
            "The average sits above the midpoint because the uncertain inputs "
            "can be badly underestimated more easily than badly overestimated."
        )

    if rankings:
        dominant = rankings[0]
        if dominant["variance_share"] > 0.5:
            notes.append(
                f"{dominant['name']} alone causes "
                f"{dominant['variance_share'] * 100:.0f}% of the uncertainty. "
                f"Improving anything else first is wasted effort."
            )
        negligible = [item for item in rankings if item["is_negligible"]]
        if len(negligible) >= 2:
            notes.append(
                f"{len(negligible)} inputs contribute almost nothing to the "
                f"uncertainty. Their precision does not matter."
            )

    return notes


# --- Persistence ------------------------------------------------------------


def _connect() -> sqlite3.Connection:
    """Open a connection with the uncertainty table guaranteed to exist."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS uncertainty_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            components TEXT NOT NULL,
            point_estimate REAL NOT NULL,
            median REAL NOT NULL,
            lower REAL NOT NULL,
            upper REAL NOT NULL,
            relative_half_width REAL NOT NULL,
            iterations INTEGER NOT NULL,
            seed INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def save_profile(user_id: int, name: str, components: list[dict[str, Any]], summary: dict[str, Any]) -> int | None:
    """Persist a set of components and the interval they produced."""
    if not user_id:
        return None

    conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO uncertainty_profiles (
                user_id, name, components, point_estimate, median,
                lower, upper, relative_half_width, iterations, seed, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                int(user_id),
                str(name or "Untitled"),
                json.dumps(components),
                float(summary.get("point_estimate", 0.0)),
                float(summary.get("median", 0.0)),
                float(summary.get("lower", 0.0)),
                float(summary.get("upper", 0.0)),
                float(summary.get("relative_half_width", 0.0)),
                int(summary.get("iterations", DEFAULT_ITERATIONS)),
                int(summary.get("seed", DEFAULT_SEED)),
                datetime.datetime.now().isoformat(timespec="seconds"),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error:
        logger.exception("Failed to save uncertainty profile")
        return None
    finally:
        conn.close()


def get_profiles(user_id: int, limit: int = 25) -> list[dict[str, Any]]:
    """Return saved profiles for a user, newest first."""
    if not user_id:
        return []

    conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, name, components, point_estimate, median, lower, upper,
                   relative_half_width, iterations, seed, created_at
            FROM uncertainty_profiles
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(user_id), int(limit)),
        ).fetchall()
    except sqlite3.Error:
        logger.exception("Failed to read uncertainty profiles")
        return []
    finally:
        conn.close()

    profiles = []
    for row in rows:
        try:
            components = json.loads(row[2])
        except (TypeError, ValueError):
            components = []
        profiles.append(
            {
                "id": row[0],
                "name": row[1],
                "components": components,
                "point_estimate": row[3],
                "median": row[4],
                "lower": row[5],
                "upper": row[6],
                "relative_half_width": row[7],
                "iterations": row[8],
                "seed": row[9],
                "created_at": row[10],
            }
        )
    return profiles


def delete_profile(user_id: int, profile_id: int) -> bool:
    """Delete one saved profile. Scoped by user so ids cannot be guessed."""
    if not user_id or not profile_id:
        return False

    conn = _connect()
    try:
        cursor = conn.execute(
            "DELETE FROM uncertainty_profiles WHERE id = ? AND user_id = ?",
            (int(profile_id), int(user_id)),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error:
        logger.exception("Failed to delete uncertainty profile")
        return False
    finally:
        conn.close()
