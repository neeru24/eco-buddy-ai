"""
Household Per-Capita Footprint Allocation.

EcoBuddy AI treats every user as if they live alone. The app's own inputs prove
the assumption: `pages/Carbon_Footprint.py` asks for *"Monthly Electricity
(kWh)"* — a figure read off a **household** meter — and `emissions.py` charges
the entire thing to one person:

    electricity_emission = electricity * elec_factor * 12
    contributors["Electricity"] = round(electricity_emission, 2)

The same flaw runs through the appliance list (a fridge serves the whole home),
the water module (laundry and dishwashing are shared) and the leaderboard
(which ranks a solo occupant against someone in a shared house).

For anyone not living alone this overstates their footprint by 2-5x, makes the
leaderboard unfair, and invalidates every benchmark comparison — published
national averages are *per capita*, and the app compares an undivided household
total against them.

Why not simply divide everything by household size
--------------------------------------------------
Because that would divide *personal* emissions too. Your own commute and your
own flights are yours alone; dividing them by four understates your footprint
just as badly as not dividing electricity overstates it. Shared and personal
categories have to be classified separately, which is what this module does.
"""

import datetime

# --- Allocation methods -----------------------------------------------------

METHOD_EQUAL = "equal"
METHOD_ADULT_EQUIVALENT = "adult_equivalent"
METHOD_CUSTOM = "custom"

ALLOCATION_METHODS = [METHOD_EQUAL, METHOD_ADULT_EQUIVALENT, METHOD_CUSTOM]

METHOD_LABELS = {
    METHOD_EQUAL: "Equal split (per head)",
    METHOD_ADULT_EQUIVALENT: "Adult-equivalent (age-weighted)",
    METHOD_CUSTOM: "Custom shares",
}

# --- Consumption weighting --------------------------------------------------

# An OECD-style equivalence approach: a toddler does not consume like an adult,
# so an equal per-head split overstates a child's share and understates every
# adult's. Bands are (max_age_inclusive, weight).
AGE_WEIGHT_BANDS = [
    (4, 0.30),
    (12, 0.50),
    (17, 0.75),
    (64, 1.00),
    (200, 0.90),
]

DEFAULT_ADULT_WEIGHT = 1.00

# A dependent adult (non-earning, at home) still consumes close to a full share.
DEPENDENT_WEIGHT_MULTIPLIER = 1.0

# --- Category classification ------------------------------------------------

# How much of each category is genuinely shared across the household.
# Electricity is metered for the whole home, so 100%. Transport is mostly
# personal but a family car does shared duty. Diet and flights are personal.
SHARED_FRACTIONS = {
    "Electricity": 1.00,
    "Transport": 0.25,
    "Diet": 0.00,
    "Flights": 0.00,
    "Water": 0.75,
    "Waste": 0.90,
    "Heating": 1.00,
    "Appliances": 1.00,
}

DEFAULT_SHARED_FRACTION = 0.0

SHARED_CATEGORIES = [
    category for category, fraction in SHARED_FRACTIONS.items() if fraction >= 0.5
]
PERSONAL_CATEGORIES = [
    category for category, fraction in SHARED_FRACTIONS.items() if fraction < 0.5
]

# --- Home types -------------------------------------------------------------

HOME_TYPES = [
    "Apartment",
    "Terraced house",
    "Semi-detached house",
    "Detached house",
    "Shared house",
    "Other",
]

DEFAULT_HOME_TYPE = "Apartment"

# Published per-capita annual emissions, in kg CO2 per person per year. These
# are the only valid comparison for a per-capita figure.
PER_CAPITA_BENCHMARKS = {
    "Global": 4800.0,
    "US": 14900.0,
    "UK": 5200.0,
    "EU": 6800.0,
}

DEFAULT_BENCHMARK_REGION = "Global"


class HouseholdError(ValueError):
    """Raised when a household or an allocation request is invalid."""


# --- Construction -----------------------------------------------------------

def make_member(name, age, member_id=None, is_dependent=False, custom_share=None):
    """
    One household occupant.

    Returns a plain dict so it round-trips through JSON, SQLite and
    st.session_state without any serialisation glue.
    """
    try:
        parsed_age = int(age)
    except (TypeError, ValueError):
        raise HouseholdError(f"age must be a whole number, got {age!r}")
    if parsed_age < 0:
        raise HouseholdError("age cannot be negative")
    if parsed_age > 130:
        raise HouseholdError("age is implausibly high")

    if custom_share is not None:
        try:
            custom_share = float(custom_share)
        except (TypeError, ValueError):
            raise HouseholdError(f"custom_share must be a number, got {custom_share!r}")
        if not 0.0 <= custom_share <= 1.0:
            raise HouseholdError("custom_share must be between 0 and 1")

    return {
        "id": member_id,
        "name": (name or "Unnamed").strip() or "Unnamed",
        "age": parsed_age,
        "is_dependent": bool(is_dependent),
        "custom_share": custom_share,
    }


def make_household(members, home_type=DEFAULT_HOME_TYPE, home_size_sqm=None,
                   household_id=None, user_id=None):
    """Build and validate a household."""
    household = {
        "id": household_id,
        "user_id": user_id,
        "members": list(members or []),
        "home_type": home_type if home_type in HOME_TYPES else DEFAULT_HOME_TYPE,
        "home_size_sqm": _coerce_optional_positive(home_size_sqm, "home_size_sqm"),
    }
    validate_household(household)
    return household


def _coerce_optional_positive(value, field_name):
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise HouseholdError(f"{field_name} must be a number, got {value!r}")
    if number < 0:
        raise HouseholdError(f"{field_name} cannot be negative")
    return number


def solo_household(user_id=None, age=30):
    """
    The implicit household of a user who has not defined one.

    Allocation against this must be the identity, which is what keeps this
    module fully backward compatible for existing users.
    """
    return make_household(
        [make_member("You", age)],
        home_type=DEFAULT_HOME_TYPE,
        user_id=user_id,
    )


def validate_household(household):
    """Raise HouseholdError if the household cannot be used for allocation."""
    members = household.get("members") or []
    if not members:
        raise HouseholdError("a household must have at least one member")
    if len(members) > 30:
        raise HouseholdError("a household of more than 30 people is not supported")

    for member in members:
        if member.get("age") is None:
            raise HouseholdError(f"member '{member.get('name')}' has no age")
        if member["age"] < 0:
            raise HouseholdError("age cannot be negative")

    custom_shares = [
        member["custom_share"] for member in members
        if member.get("custom_share") is not None
    ]
    if custom_shares:
        if len(custom_shares) != len(members):
            raise HouseholdError(
                "custom shares must be set for every member or for none of them"
            )
        total = sum(custom_shares)
        if abs(total - 1.0) > 0.01:
            raise HouseholdError(
                f"custom shares must sum to 1.0, got {total:.3f}"
            )
    return True


# --- Adult equivalence ------------------------------------------------------

def adult_equivalent(member):
    """
    The consumption weight of one member relative to a working-age adult.

    An infant is not a full consumer of household resources, and treating one
    as such is the flaw in a naive per-head split.
    """
    age = member["age"]
    for max_age, weight in AGE_WEIGHT_BANDS:
        if age <= max_age:
            base = weight
            break
    else:
        base = DEFAULT_ADULT_WEIGHT

    if member.get("is_dependent"):
        base *= DEPENDENT_WEIGHT_MULTIPLIER
    return base


def household_adult_equivalents(household):
    """Total adult-equivalent consumption units in the household."""
    return sum(adult_equivalent(member) for member in household["members"])


def household_size(household):
    """Headcount, regardless of age."""
    return len(household["members"])


def member_shares(household, method=METHOD_ADULT_EQUIVALENT):
    """
    Each member's fractional share of the shared resources.

    Shares always sum to 1.0, which is what makes the allocation conservative:
    a household's emissions are redistributed, never created or destroyed.
    """
    validate_household(household)
    members = household["members"]

    if method == METHOD_CUSTOM:
        if any(member.get("custom_share") is None for member in members):
            raise HouseholdError(
                "custom allocation requires a custom_share on every member"
            )
        return {
            _member_key(member, index): member["custom_share"]
            for index, member in enumerate(members)
        }

    if method == METHOD_EQUAL:
        share = 1.0 / len(members)
        return {_member_key(member, index): share for index, member in enumerate(members)}

    if method == METHOD_ADULT_EQUIVALENT:
        total = household_adult_equivalents(household)
        if total <= 0:
            share = 1.0 / len(members)
            return {
                _member_key(member, index): share
                for index, member in enumerate(members)
            }
        return {
            _member_key(member, index): adult_equivalent(member) / total
            for index, member in enumerate(members)
        }

    raise HouseholdError(
        f"unknown allocation method '{method}'. "
        f"Must be one of: {', '.join(ALLOCATION_METHODS)}"
    )


def _member_key(member, index):
    """
    A stable, unique key for a member.

    The positional index is always part of the key. Names are not unique (two
    people in a household can share one), and `id` is None until the household
    has been saved — so keying on either alone silently collapses two members
    into one entry and loses a share.
    """
    member_id = member.get("id")
    suffix = index if member_id is None else f"{member_id}-{index}"
    return f"{member['name']}#{suffix}"


def primary_share(household, method=METHOD_ADULT_EQUIVALENT):
    """
    The share belonging to the first member, who is the app's user.

    The user is always stored first, so this is the fraction of shared
    household emissions that is genuinely theirs.
    """
    shares = member_shares(household, method)
    return next(iter(shares.values()))


# --- Allocation -------------------------------------------------------------

def shared_fraction(category):
    """How much of a category is shared rather than personal."""
    return SHARED_FRACTIONS.get(category, DEFAULT_SHARED_FRACTION)


def allocate_category(value, category, household, method=METHOD_ADULT_EQUIVALENT):
    """
    Split one category's emissions into the user's personal share.

    The shared portion is divided by the user's share of the household; the
    personal portion is left entirely with them. A solo household returns the
    input unchanged.
    """
    try:
        amount = float(value)
    except (TypeError, ValueError):
        raise HouseholdError(f"{category} value must be a number, got {value!r}")

    fraction = shared_fraction(category)
    user_share = primary_share(household, method)

    shared_part = amount * fraction
    personal_part = amount - shared_part
    allocated_shared = shared_part * user_share

    return {
        "category": category,
        "household_total_kg": round(amount, 2),
        "shared_fraction": fraction,
        "shared_kg": round(shared_part, 2),
        "personal_kg": round(personal_part, 2),
        "your_share_of_shared": round(user_share, 4),
        "allocated_kg": round(allocated_shared + personal_part, 2),
    }


def allocate_footprint(contributors, household, method=METHOD_ADULT_EQUIVALENT):
    """
    Split a full contributors dict into the user's personal footprint.

    Returns both the household total and the user's allocated total, plus the
    per-category breakdown so the split is inspectable rather than magic.
    """
    validate_household(household)

    allocations = {}
    household_total = 0.0
    allocated_total = 0.0

    for category, value in (contributors or {}).items():
        try:
            amount = float(value)
        except (TypeError, ValueError):
            continue
        allocation = allocate_category(amount, category, household, method)
        allocations[category] = allocation
        household_total += amount
        allocated_total += allocation["allocated_kg"]

    return {
        "method": method,
        "household_size": household_size(household),
        "adult_equivalents": round(household_adult_equivalents(household), 3),
        "your_share_of_shared": round(primary_share(household, method), 4),
        "allocations": allocations,
        "household_total_kg": round(household_total, 2),
        "allocated_total_kg": round(allocated_total, 2),
        "reduction_kg": round(household_total - allocated_total, 2),
        "reduction_percent": round(
            ((household_total - allocated_total) / household_total * 100.0)
            if household_total > 0 else 0.0, 1
        ),
    }


def per_capita_footprint(contributors, household, method=METHOD_ADULT_EQUIVALENT):
    """
    The household's total emissions divided evenly across its members.

    Distinct from `allocate_footprint()`, which returns *the user's* share
    accounting for personal categories. This is the household average.
    """
    validate_household(household)
    total = household_total_footprint(contributors)
    size = household_size(household)
    return round(total / size, 2) if size else 0.0


def household_total_footprint(contributors):
    """Sum of every category, ignoring unusable values."""
    total = 0.0
    for value in (contributors or {}).values():
        try:
            total += float(value)
        except (TypeError, ValueError):
            continue
    return round(total, 2)


# --- Analysis ---------------------------------------------------------------

def sharing_efficiency(household, contributors, method=METHOD_ADULT_EQUIVALENT):
    """
    How much per-person emission sharing a home avoids.

    Shared living has real economies of scale — one fridge, one boiler, one set
    of lights for several people — and the app currently hides that entirely.
    Compares the allocated footprint against the counterfactual where every
    member lived alone and bore the full shared load themselves.
    """
    validate_household(household)
    allocation = allocate_footprint(contributors, household, method)

    if household_size(household) <= 1:
        return {
            "household_size": 1,
            "allocated_kg": allocation["allocated_total_kg"],
            "if_living_alone_kg": allocation["allocated_total_kg"],
            "avoided_kg": 0.0,
            "avoided_percent": 0.0,
            "is_shared": False,
        }

    # Living alone means bearing 100% of the shared categories.
    alone_total = 0.0
    for category, value in (contributors or {}).items():
        try:
            amount = float(value)
        except (TypeError, ValueError):
            continue
        alone_total += amount

    allocated = allocation["allocated_total_kg"]
    avoided = alone_total - allocated

    return {
        "household_size": household_size(household),
        "allocated_kg": round(allocated, 2),
        "if_living_alone_kg": round(alone_total, 2),
        "avoided_kg": round(avoided, 2),
        "avoided_percent": round(
            (avoided / alone_total * 100.0) if alone_total > 0 else 0.0, 1
        ),
        "is_shared": True,
    }


def compare_to_benchmark(per_capita_kg, region=DEFAULT_BENCHMARK_REGION):
    """
    Compare a per-capita figure against a published per-capita average.

    Only a per-capita number may be compared here. Passing an undivided
    household total against a per-capita benchmark is the specific mistake this
    module exists to fix.
    """
    if region not in PER_CAPITA_BENCHMARKS:
        region = DEFAULT_BENCHMARK_REGION

    benchmark = PER_CAPITA_BENCHMARKS[region]
    try:
        value = float(per_capita_kg)
    except (TypeError, ValueError):
        raise HouseholdError(f"per_capita_kg must be a number, got {per_capita_kg!r}")

    difference = value - benchmark
    return {
        "region": region,
        "per_capita_kg": round(value, 2),
        "benchmark_kg": benchmark,
        "difference_kg": round(difference, 2),
        "percent_of_benchmark": round((value / benchmark * 100.0) if benchmark else 0.0, 1),
        "is_below_benchmark": difference < 0,
        "verdict": (
            f"{abs(difference):,.0f} kg CO2 "
            f"{'below' if difference < 0 else 'above'} the {region} per-capita average"
        ),
    }


def scale_recommendation_thresholds(thresholds, household, method=METHOD_ADULT_EQUIVALENT):
    """
    Scale per-person advice thresholds to a household's size.

    `recommendations.py` fires "your electricity usage is very high" at
    >= 300 kWh. That is perfectly normal for a family home and genuinely high
    for a studio flat, and the threshold currently has no idea which it is
    looking at. Scaling by adult equivalents makes the advice size-aware.
    """
    validate_household(household)
    equivalents = max(1.0, household_adult_equivalents(household))

    scaled = {}
    for name, threshold in (thresholds or {}).items():
        try:
            scaled[name] = round(float(threshold) * equivalents, 2)
        except (TypeError, ValueError):
            continue
    return scaled


def describe_allocation(allocation):
    """
    A transparent, human-readable account of how the split was computed.

    A per-person number nobody can explain is a number nobody will trust, so
    the reasoning is spelled out rather than left implicit.
    """
    size = allocation["household_size"]
    if size <= 1:
        return (
            "You live alone, so your footprint is your household's footprint — "
            "nothing is shared and nothing is reallocated."
        )

    lines = [
        f"Your household has {size} people "
        f"({allocation['adult_equivalents']:.2f} adult-equivalents), and your share "
        f"of shared resources is {allocation['your_share_of_shared'] * 100:.0f}%.",
        "",
    ]
    for category, item in allocation["allocations"].items():
        if item["shared_fraction"] > 0:
            lines.append(
                f"- {category}: {item['household_total_kg']:,.0f} kg is "
                f"{item['shared_fraction'] * 100:.0f}% shared, so you carry "
                f"{item['allocated_kg']:,.0f} kg."
            )
        else:
            lines.append(
                f"- {category}: {item['household_total_kg']:,.0f} kg is entirely "
                "personal, so all of it stays with you."
            )
    lines.append("")
    lines.append(
        f"Household total {allocation['household_total_kg']:,.0f} kg -> "
        f"your footprint {allocation['allocated_total_kg']:,.0f} kg "
        f"({allocation['reduction_percent']:.0f}% lower)."
    )
    return "\n".join(lines)


def household_to_dict(household):
    """JSON-safe representation for export and session state."""
    return {
        "id": household.get("id"),
        "user_id": household.get("user_id"),
        "home_type": household["home_type"],
        "home_size_sqm": household["home_size_sqm"],
        "members": [
            {
                "id": member.get("id"),
                "name": member["name"],
                "age": member["age"],
                "is_dependent": member["is_dependent"],
                "custom_share": member["custom_share"],
            }
            for member in household["members"]
        ],
        "exported_at": datetime.date.today().isoformat(),
    }


def household_from_dict(payload):
    """Rebuild a household from stored data."""
    if not isinstance(payload, dict):
        raise HouseholdError("household payload must be a mapping")
    return make_household(
        [
            make_member(
                member.get("name"),
                member.get("age"),
                member_id=member.get("id"),
                is_dependent=member.get("is_dependent", False),
                custom_share=member.get("custom_share"),
            )
            for member in payload.get("members", [])
        ],
        home_type=payload.get("home_type", DEFAULT_HOME_TYPE),
        home_size_sqm=payload.get("home_size_sqm"),
        household_id=payload.get("id"),
        user_id=payload.get("user_id"),
    )
