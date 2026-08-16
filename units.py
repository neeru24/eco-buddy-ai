"""
Unit System & Localization Layer.

EcoBuddy AI is metric-only and bakes its units directly into UI label strings:
`"Average Shower Duration (minutes/day)"` in the water page, kWh and km in the
carbon page, and a bare `utility_rate` in the energy audit with no currency
symbol at all. A user who thinks in miles, gallons or pounds cannot use the app
without mental arithmetic, and the solar ROI payback figure is a number with no
currency attached to it.

This module centralises three things that were previously scattered or absent:

    conversion   between units of the same physical dimension
    formatting   consistent precision, thousands separators and symbols
    preference   which units and currency a given user wants to see

Storage stays canonical metric. Conversion happens only at the display
boundary — `to_preferred()` on the way out, `from_preferred()` on the way back
in — so no calculation module has to change and no stored value is rewritten.
"""

from typing import Any

# --- Dimensions -------------------------------------------------------------

DIM_DISTANCE = "distance"
DIM_MASS = "mass"
DIM_VOLUME = "volume"
DIM_ENERGY = "energy"
DIM_TEMPERATURE = "temperature"
DIM_AREA = "area"

DIMENSIONS = [
    DIM_DISTANCE,
    DIM_MASS,
    DIM_VOLUME,
    DIM_ENERGY,
    DIM_TEMPERATURE,
    DIM_AREA,
]


class UnitError(ValueError):
    """Raised for unknown units, unknown currencies or dimension mismatches."""


# --- Unit registry ----------------------------------------------------------

def _unit(key: str, symbol: str, name: str, plural: str, dimension: str,
          factor: float, precision: int = 1) -> dict[str, Any]:
    """
    One unit definition.

    `factor` is how many base units one of this unit represents. The base unit
    of each dimension has factor 1.0: metre, kilogram, litre, kilowatt-hour,
    square metre.
    """
    return {
        "key": key,
        "symbol": symbol,
        "name": name,
        "plural": plural,
        "dimension": dimension,
        "factor": float(factor),
        "precision": precision,
    }


UNITS = {
    # Distance — base: metre
    "m": _unit("m", "m", "metre", "metres", DIM_DISTANCE, 1.0, 0),
    "km": _unit("km", "km", "kilometre", "kilometres", DIM_DISTANCE, 1000.0, 1),
    "mi": _unit("mi", "mi", "mile", "miles", DIM_DISTANCE, 1609.344, 1),
    "ft": _unit("ft", "ft", "foot", "feet", DIM_DISTANCE, 0.3048, 0),

    # Mass — base: kilogram
    "kg": _unit("kg", "kg", "kilogram", "kilograms", DIM_MASS, 1.0, 1),
    "g": _unit("g", "g", "gram", "grams", DIM_MASS, 0.001, 0),
    "t": _unit("t", "t", "tonne", "tonnes", DIM_MASS, 1000.0, 2),
    "lb": _unit("lb", "lb", "pound", "pounds", DIM_MASS, 0.45359237, 1),
    "short_ton": _unit("short_ton", "tons", "US ton", "US tons", DIM_MASS, 907.18474, 2),

    # Volume — base: litre
    "L": _unit("L", "L", "litre", "litres", DIM_VOLUME, 1.0, 1),
    "mL": _unit("mL", "mL", "millilitre", "millilitres", DIM_VOLUME, 0.001, 0),
    "m3": _unit("m3", "m³", "cubic metre", "cubic metres", DIM_VOLUME, 1000.0, 2),
    "gal_us": _unit("gal_us", "gal", "US gallon", "US gallons", DIM_VOLUME, 3.785411784, 1),
    "gal_uk": _unit("gal_uk", "gal", "imperial gallon", "imperial gallons",
                    DIM_VOLUME, 4.54609, 1),

    # Energy — base: kilowatt-hour
    "kWh": _unit("kWh", "kWh", "kilowatt-hour", "kilowatt-hours", DIM_ENERGY, 1.0, 1),
    "Wh": _unit("Wh", "Wh", "watt-hour", "watt-hours", DIM_ENERGY, 0.001, 0),
    "MWh": _unit("MWh", "MWh", "megawatt-hour", "megawatt-hours", DIM_ENERGY, 1000.0, 2),
    "therm": _unit("therm", "thm", "therm", "therms", DIM_ENERGY, 29.3001, 2),
    "MJ": _unit("MJ", "MJ", "megajoule", "megajoules", DIM_ENERGY, 0.2777778, 2),

    # Temperature — base: Celsius. Affine, never scaled by `factor`.
    "C": _unit("C", "°C", "degree Celsius", "degrees Celsius", DIM_TEMPERATURE, 1.0, 1),
    "F": _unit("F", "°F", "degree Fahrenheit", "degrees Fahrenheit",
               DIM_TEMPERATURE, 1.0, 1),
    "K": _unit("K", "K", "kelvin", "kelvin", DIM_TEMPERATURE, 1.0, 1),

    # Area — base: square metre
    "m2": _unit("m2", "m²", "square metre", "square metres", DIM_AREA, 1.0, 1),
    "ft2": _unit("ft2", "ft²", "square foot", "square feet", DIM_AREA, 0.09290304, 0),
}

# The canonical unit of each dimension: everything else is defined relative to it.
BASE_UNITS = {
    DIM_DISTANCE: "m",
    DIM_MASS: "kg",
    DIM_VOLUME: "L",
    DIM_ENERGY: "kWh",
    DIM_TEMPERATURE: "C",
    DIM_AREA: "m2",
}

# The unit the app actually stores each kind of value in. Distance is stored in
# kilometres rather than the dimension's base metre, which is why this mapping
# exists separately from BASE_UNITS.
STORAGE_UNITS = {
    DIM_DISTANCE: "km",
    DIM_MASS: "kg",
    DIM_VOLUME: "L",
    DIM_ENERGY: "kWh",
    DIM_TEMPERATURE: "C",
    DIM_AREA: "m2",
}


def get_unit(key: str) -> dict[str, Any]:
    """Look up a unit definition by key."""
    if key not in UNITS:
        raise UnitError(
            f"unknown unit '{key}'. Known units: {', '.join(sorted(UNITS))}"
        )
    return UNITS[key]


def list_units(dimension: str | None = None) -> list[str]:
    """Unit keys, optionally restricted to one dimension."""
    return sorted(
        key for key, unit in UNITS.items()
        if dimension is None or unit["dimension"] == dimension
    )


def same_dimension(unit_a: str, unit_b: str) -> bool:
    """True when two units measure the same physical quantity."""
    return get_unit(unit_a)["dimension"] == get_unit(unit_b)["dimension"]


# --- Unit systems -----------------------------------------------------------

METRIC = "metric"
IMPERIAL = "imperial"
UNIT_SYSTEMS = [METRIC, IMPERIAL]

SYSTEM_UNITS = {
    METRIC: {
        DIM_DISTANCE: "km",
        DIM_MASS: "kg",
        DIM_VOLUME: "L",
        DIM_ENERGY: "kWh",
        DIM_TEMPERATURE: "C",
        DIM_AREA: "m2",
    },
    IMPERIAL: {
        DIM_DISTANCE: "mi",
        DIM_MASS: "lb",
        DIM_VOLUME: "gal_us",
        DIM_ENERGY: "kWh",  # kWh is universal on electricity bills
        DIM_TEMPERATURE: "F",
        DIM_AREA: "ft2",
    },
}

SYSTEM_LABELS = {
    METRIC: "Metric (km, kg, L, °C)",
    IMPERIAL: "Imperial (mi, lb, gal, °F)",
}


# --- Currencies -------------------------------------------------------------

def _currency(code: str, symbol: str, name: str, symbol_first: bool = True,
              decimals: int = 2) -> dict[str, Any]:
    return {
        "code": code,
        "symbol": symbol,
        "name": name,
        "symbol_first": symbol_first,
        "decimals": decimals,
    }


CURRENCIES = {
    "USD": _currency("USD", "$", "US Dollar"),
    "EUR": _currency("EUR", "€", "Euro", symbol_first=False),
    "GBP": _currency("GBP", "£", "British Pound"),
    "INR": _currency("INR", "₹", "Indian Rupee"),
    "CAD": _currency("CAD", "C$", "Canadian Dollar"),
    "AUD": _currency("AUD", "A$", "Australian Dollar"),
    "JPY": _currency("JPY", "¥", "Japanese Yen", decimals=0),
    "BRL": _currency("BRL", "R$", "Brazilian Real"),
    "ZAR": _currency("ZAR", "R", "South African Rand"),
    "NGN": _currency("NGN", "₦", "Nigerian Naira"),
}

DEFAULT_CURRENCY = "USD"


def get_currency(code: str) -> dict[str, Any]:
    """Look up a currency definition by ISO code."""
    if code not in CURRENCIES:
        raise UnitError(
            f"unknown currency '{code}'. Known currencies: {', '.join(sorted(CURRENCIES))}"
        )
    return CURRENCIES[code]


def list_currencies() -> list[str]:
    """Every supported currency code, alphabetically."""
    return sorted(CURRENCIES)


# --- Preferences ------------------------------------------------------------

def make_preference(system: str = METRIC, currency: str = DEFAULT_CURRENCY) -> dict[str, Any]:
    """
    A user's display preference: a unit system plus a currency.

    Falls back to metric + USD on unrecognised input rather than raising, so a
    corrupted stored preference degrades to the default instead of breaking
    every page that reads it.
    """
    if system not in UNIT_SYSTEMS:
        system = METRIC
    if currency not in CURRENCIES:
        currency = DEFAULT_CURRENCY
    return {"system": system, "currency": currency}


DEFAULT_PREFERENCE = make_preference()


def preferred_unit(dimension: str, preference: dict[str, Any] | None = None) -> str:
    """The unit this preference wants for a given dimension."""
    preference = preference or DEFAULT_PREFERENCE
    if dimension not in DIMENSIONS:
        raise UnitError(f"unknown dimension '{dimension}'")
    return SYSTEM_UNITS[preference["system"]][dimension]


# --- Conversion -------------------------------------------------------------

def convert(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert between two units of the same dimension.

    Temperature is rejected here on purpose: it is affine rather than
    multiplicative, so running it through a ratio of factors would silently
    produce wrong numbers. Use `convert_temperature()` instead.
    """
    source = get_unit(from_unit)
    target = get_unit(to_unit)

    if source["dimension"] != target["dimension"]:
        raise UnitError(
            f"cannot convert {from_unit} ({source['dimension']}) to "
            f"{to_unit} ({target['dimension']}) — different dimensions"
        )
    if source["dimension"] == DIM_TEMPERATURE:
        raise UnitError(
            "temperature conversion is affine, not multiplicative; "
            "use convert_temperature()"
        )

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise UnitError(f"value must be a number, got {value!r}")

    if from_unit == to_unit:
        return number
    return number * source["factor"] / target["factor"]


def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    """Convert between Celsius, Fahrenheit and Kelvin."""
    for unit in (from_unit, to_unit):
        if get_unit(unit)["dimension"] != DIM_TEMPERATURE:
            raise UnitError(f"{unit} is not a temperature unit")

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise UnitError(f"value must be a number, got {value!r}")

    if from_unit == to_unit:
        return number

    # Normalise to Celsius, then out again.
    if from_unit == "F":
        celsius = (number - 32.0) * 5.0 / 9.0
    elif from_unit == "K":
        celsius = number - 273.15
    else:
        celsius = number

    if to_unit == "F":
        return celsius * 9.0 / 5.0 + 32.0
    if to_unit == "K":
        return celsius + 273.15
    return celsius


def to_preferred(value: float, storage_unit: str, preference: dict[str, Any] | None = None) -> tuple[float, str]:
    """
    Convert a stored (metric) value into the user's display unit.

    Returns `(converted_value, display_unit_key)` so a caller can format the
    result without having to look the unit up a second time.
    """
    preference = preference or DEFAULT_PREFERENCE
    dimension = get_unit(storage_unit)["dimension"]
    target = preferred_unit(dimension, preference)

    if dimension == DIM_TEMPERATURE:
        return convert_temperature(value, storage_unit, target), target
    return convert(value, storage_unit, target), target


def from_preferred(value: float, storage_unit: str, preference: dict[str, Any] | None = None) -> float:
    """
    Convert a value the user typed in their own units back to storage units.

    The inverse of `to_preferred()`. Form input must go through this before it
    reaches the database, or the stored data stops being canonical metric.
    """
    preference = preference or DEFAULT_PREFERENCE
    dimension = get_unit(storage_unit)["dimension"]
    source = preferred_unit(dimension, preference)

    if dimension == DIM_TEMPERATURE:
        return convert_temperature(value, source, storage_unit)
    return convert(value, source, storage_unit)


# --- Auto-scaling -----------------------------------------------------------

# Ordered smallest to largest, each entry carrying how many of itself make one
# of the next step up.
SCALE_LADDERS = {
    DIM_MASS: [("g", 1000.0), ("kg", 1000.0), ("t", None)],
    DIM_ENERGY: [("Wh", 1000.0), ("kWh", 1000.0), ("MWh", None)],
    DIM_DISTANCE: [("m", 1000.0), ("km", None)],
    DIM_VOLUME: [("mL", 1000.0), ("L", 1000.0), ("m3", None)],
}


def auto_scale(value: float, unit: str) -> tuple[float, str]:
    """
    Pick the most readable magnitude for a value.

    A footprint of 12,400 kg reads far better as "12.4 t", and 0.004 kWh reads
    better as "4 Wh". Returns `(scaled_value, unit_key)`.

    Units outside a defined ladder (temperature, area, imperial units) are
    returned untouched rather than guessed at.
    """
    definition = get_unit(unit)
    ladder = SCALE_LADDERS.get(definition["dimension"])
    if not ladder:
        return float(value), unit

    keys = [step[0] for step in ladder]
    if unit not in keys:
        return float(value), unit

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise UnitError(f"value must be a number, got {value!r}")

    if number == 0:
        return 0.0, unit

    index = keys.index(unit)
    magnitude = abs(number)

    # Step up while the value is comfortably above the next threshold.
    while index < len(ladder) - 1 and ladder[index][1] and magnitude >= ladder[index][1]:
        number /= ladder[index][1]
        magnitude = abs(number)
        index += 1

    # Step down while the value is inconveniently small.
    while index > 0 and magnitude < 1.0:
        number *= ladder[index - 1][1]
        magnitude = abs(number)
        index -= 1

    return number, keys[index]


# --- Formatting -------------------------------------------------------------

def format_number(value: float, precision: int = 1) -> str:
    """A number with thousands separators and fixed precision."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise UnitError(f"value must be a number, got {value!r}")
    return f"{number:,.{max(0, int(precision))}f}"


def format_quantity(value: float, unit: str, preference: dict[str, Any] | None = None,
                    precision: int | None = None, scale: bool = False,
                    convert_to_preference: bool = True) -> str:
    """
    Format a stored value for display: converted, scaled, and labelled.

    `convert_to_preference=False` formats the value in the unit given without
    converting, which is what a caller that has already converted needs.
    """
    preference = preference or DEFAULT_PREFERENCE

    if convert_to_preference:
        display_value, display_unit = to_preferred(value, unit, preference)
    else:
        display_value, display_unit = float(value), unit

    if scale:
        display_value, display_unit = auto_scale(display_value, display_unit)

    definition = get_unit(display_unit)
    if precision is None:
        precision = definition["precision"]

    return f"{format_number(display_value, precision)} {definition['symbol']}"


def format_co2(value_kg: float, preference: dict[str, Any] | None = None, scale: bool = True) -> str:
    """
    The app-wide canonical footprint formatter.

    Everything currently does its own thing — some `f"{x:.0f}"`, some
    `f"{x:.2f}"`, some bare `round()` — so 5234.7891 renders raw in places.
    """
    preference = preference or DEFAULT_PREFERENCE
    display_value, display_unit = to_preferred(value_kg, "kg", preference)
    if scale:
        display_value, display_unit = auto_scale(display_value, display_unit)

    definition = get_unit(display_unit)
    precision = 0 if abs(display_value) >= 100 else definition["precision"]
    return f"{format_number(display_value, precision)} {definition['symbol']} CO₂"


def format_currency(value: float, preference: dict[str, Any] | None = None, show_code: bool = False) -> str:
    """Format a monetary amount with the right symbol, placement and precision."""
    preference = preference or DEFAULT_PREFERENCE
    currency = get_currency(preference["currency"])

    try:
        number = float(value)
    except (TypeError, ValueError):
        raise UnitError(f"value must be a number, got {value!r}")

    negative = number < 0
    body = format_number(abs(number), currency["decimals"])

    if currency["symbol_first"]:
        text = f"{currency['symbol']}{body}"
    else:
        text = f"{body} {currency['symbol']}"

    if negative:
        text = f"-{text}"
    if show_code:
        text = f"{text} {currency['code']}"
    return text


def label_with_unit(base_label: str, dimension: str, preference: dict[str, Any] | None = None,
                    per: str | None = None) -> str:
    """
    Build a form label carrying the user's unit, e.g. "Daily Distance (mi)".

    This is what lets pages stop hardcoding units into their label strings,
    which is the reason adding a unit today means editing eight files.
    """
    preference = preference or DEFAULT_PREFERENCE
    unit = preferred_unit(dimension, preference)
    symbol = get_unit(unit)["symbol"]
    if per:
        return f"{base_label} ({symbol}/{per})"
    return f"{base_label} ({symbol})"


def unit_symbol(dimension: str, preference: dict[str, Any] | None = None) -> str:
    """Just the symbol a preference wants for a dimension."""
    return get_unit(preferred_unit(dimension, preference))["symbol"]


def describe_preference(preference: dict[str, Any] | None = None) -> str:
    """Human-readable summary for a settings panel."""
    preference = preference or DEFAULT_PREFERENCE
    currency = get_currency(preference["currency"])
    return f"{SYSTEM_LABELS[preference['system']]} · {currency['name']} ({currency['symbol']})"


def preference_to_dict(preference: dict[str, Any]) -> dict[str, Any]:
    """JSON-safe representation for storage and session state."""
    return {"system": preference["system"], "currency": preference["currency"]}


def preference_from_dict(payload: dict[str, Any]) -> dict[str, Any]:
    """Rebuild a preference from stored data, defaulting on anything invalid."""
    if not isinstance(payload, dict):
        return make_preference()
    return make_preference(
        payload.get("system", METRIC),
        payload.get("currency", DEFAULT_CURRENCY),
    )


# --- Convenience wrappers for the app's actual quantities -------------------

def format_distance(value_km: float, preference: dict[str, Any] | None = None,
                    precision: int | None = None) -> str:
    """Format a stored distance (km)."""
    return format_quantity(value_km, "km", preference, precision=precision)


def format_volume(value_litres: float, preference: dict[str, Any] | None = None,
                  precision: int | None = None) -> str:
    """Format a stored water volume (litres)."""
    return format_quantity(value_litres, "L", preference, precision=precision)


def format_energy(value_kwh: float, preference: dict[str, Any] | None = None,
                  precision: int | None = None, scale: bool = False) -> str:
    """Format a stored energy amount (kWh)."""
    return format_quantity(value_kwh, "kWh", preference, precision=precision, scale=scale)


def format_area(value_sqm: float, preference: dict[str, Any] | None = None,
                precision: int | None = None) -> str:
    """Format a stored area (m²)."""
    return format_quantity(value_sqm, "m2", preference, precision=precision)
