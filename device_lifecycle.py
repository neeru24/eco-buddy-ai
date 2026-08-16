"""Device lifecycle carbon tracking, repair-vs-replace advice and e-waste routing.

The existing energy audit models what appliances *use*; this module models what
electronics *cost to make*. For a phone or laptop, manufacturing is typically
70-85% of lifetime emissions, so the single most effective action is keeping a
device longer - and that only becomes visible once embodied carbon is amortised
over how long a device is actually kept.

Key ideas:

* ``embodied_kg``    one-off manufacturing + shipping emissions
* ``annualized``     embodied / years owned + annual operating emissions
* ``repair_vs_replace``  compares repairing a device against the embodied cost
  of a replacement, offset by the replacement's efficiency gain

The module is self-contained: its SQLite table is created lazily and no shared
files are modified.
"""

import os
import sqlite3
import logging
import datetime
from typing import Any

logger = logging.getLogger(__name__)

DB_NAME = os.getenv("ECO_BUDDY_DB", "eco_buddy.db")

HOURS_PER_YEAR = 8760
WATTS_TO_KW = 1000.0

# Grid carbon intensity in kg CO2 per kWh, used to convert operating energy.
DEFAULT_GRID_INTENSITY = 0.475

# embodied_kg      : kg CO2e to manufacture and ship one unit
# typical_watts    : average draw while in use
# daily_hours      : typical hours of active use per day
# lifespan_years   : manufacturer/industry expected service life
# recyclable_kg    : mass of recoverable material
# repairability    : 1 (glued shut) to 10 (fully user serviceable)
DEVICE_TYPES = {
    "Smartphone": {
        "icon": "📱",
        "embodied_kg": 70.0,
        "typical_watts": 3.0,
        "daily_hours": 5.0,
        "lifespan_years": 3.0,
        "recyclable_kg": 0.15,
        "repairability": 4,
        "hazardous": True,
    },
    "Tablet": {
        "icon": "📲",
        "embodied_kg": 100.0,
        "typical_watts": 6.0,
        "daily_hours": 3.0,
        "lifespan_years": 4.0,
        "recyclable_kg": 0.4,
        "repairability": 3,
        "hazardous": True,
    },
    "Laptop": {
        "icon": "💻",
        "embodied_kg": 300.0,
        "typical_watts": 45.0,
        "daily_hours": 6.0,
        "lifespan_years": 5.0,
        "recyclable_kg": 1.5,
        "repairability": 6,
        "hazardous": True,
    },
    "Desktop PC": {
        "icon": "🖥️",
        "embodied_kg": 350.0,
        "typical_watts": 120.0,
        "daily_hours": 5.0,
        "lifespan_years": 6.0,
        "recyclable_kg": 7.0,
        "repairability": 9,
        "hazardous": True,
    },
    "Monitor": {
        "icon": "🖵",
        "embodied_kg": 230.0,
        "typical_watts": 30.0,
        "daily_hours": 6.0,
        "lifespan_years": 7.0,
        "recyclable_kg": 3.5,
        "repairability": 5,
        "hazardous": True,
    },
    "Television": {
        "icon": "📺",
        "embodied_kg": 450.0,
        "typical_watts": 90.0,
        "daily_hours": 4.0,
        "lifespan_years": 8.0,
        "recyclable_kg": 9.0,
        "repairability": 4,
        "hazardous": True,
    },
    "Games console": {
        "icon": "🎮",
        "embodied_kg": 180.0,
        "typical_watts": 140.0,
        "daily_hours": 2.0,
        "lifespan_years": 6.0,
        "recyclable_kg": 2.5,
        "repairability": 6,
        "hazardous": True,
    },
    "Smart speaker": {
        "icon": "🔊",
        "embodied_kg": 35.0,
        "typical_watts": 3.0,
        "daily_hours": 24.0,
        "lifespan_years": 5.0,
        "recyclable_kg": 0.6,
        "repairability": 2,
        "hazardous": False,
    },
    "Router": {
        "icon": "📶",
        "embodied_kg": 40.0,
        "typical_watts": 8.0,
        "daily_hours": 24.0,
        "lifespan_years": 6.0,
        "recyclable_kg": 0.5,
        "repairability": 3,
        "hazardous": False,
    },
    "Smartwatch": {
        "icon": "⌚",
        "embodied_kg": 30.0,
        "typical_watts": 0.5,
        "daily_hours": 24.0,
        "lifespan_years": 3.0,
        "recyclable_kg": 0.05,
        "repairability": 2,
        "hazardous": True,
    },
    "Printer": {
        "icon": "🖨️",
        "embodied_kg": 120.0,
        "typical_watts": 20.0,
        "daily_hours": 0.5,
        "lifespan_years": 7.0,
        "recyclable_kg": 4.0,
        "repairability": 5,
        "hazardous": False,
    },
    "E-reader": {
        "icon": "📖",
        "embodied_kg": 45.0,
        "typical_watts": 1.0,
        "daily_hours": 2.0,
        "lifespan_years": 6.0,
        "recyclable_kg": 0.2,
        "repairability": 3,
        "hazardous": True,
    },
}

DEVICE_CONDITIONS = ["Working", "Degraded", "Faulty", "Dead"]

# How much of a device's remaining value each disposal route preserves, and
# how the route is described to the user.
DISPOSAL_ROUTES = {
    "keep": {
        "label": "Keep using it",
        "icon": "♻️",
        "detail": "The greenest device is the one you already own.",
    },
    "repair": {
        "label": "Repair and keep",
        "icon": "🔧",
        "detail": "A repair avoids the entire manufacturing footprint of a replacement.",
    },
    "resell": {
        "label": "Sell or trade in",
        "icon": "💰",
        "detail": "A working device passed on replaces a new purchase for someone else.",
    },
    "donate": {
        "label": "Donate or hand down",
        "icon": "🎁",
        "detail": "Schools, charities and refurbishers keep working hardware in service.",
    },
    "recycle": {
        "label": "Certified e-waste recycler",
        "icon": "🏭",
        "detail": "Recovers metals and keeps hazardous components out of landfill.",
    },
}

# A replacement typically draws less power than the unit it replaces.
DEFAULT_EFFICIENCY_GAIN = 0.25

# Devices older than this multiple of their expected lifespan are "overdue".
OVERDUE_MULTIPLIER = 1.0

TODAY_OVERRIDE = None


def today() -> datetime.date:
    """Return today's date, overridable in tests via ``TODAY_OVERRIDE``."""
    return TODAY_OVERRIDE or datetime.date.today()


def list_device_types() -> list[dict[str, Any]]:
    """Return the device catalogue as a list including the type name."""
    return [dict(info, name=name) for name, info in DEVICE_TYPES.items()]


def get_device_type(name: str) -> dict[str, Any] | None:
    """Return one device type's reference data, or None."""
    info = DEVICE_TYPES.get(name)
    return dict(info, name=name) if info else None


def _clean_year(purchase_year: int) -> int:
    """Clamp a purchase year into a sensible range."""
    current = today().year
    try:
        year = int(purchase_year)
    except (TypeError, ValueError):
        return current
    return max(1990, min(year, current))


def years_owned(purchase_year: int, reference_year: int | None = None) -> float:
    """Return how long a device has been owned, floored at a partial year."""
    reference_year = reference_year or today().year
    owned = reference_year - _clean_year(purchase_year)
    # A device bought this year has still been made, so never divide by zero.
    return max(0.5, float(owned))


def operating_emissions(device_type: str, daily_hours: float | None = None, grid_intensity: float | None = None) -> float:
    """Annual kg CO2 from running a device."""
    info = DEVICE_TYPES.get(device_type)
    if not info:
        raise KeyError(f"Unknown device type: {device_type}")

    hours = info["daily_hours"] if daily_hours is None else float(daily_hours)
    hours = max(0.0, min(hours, 24.0))
    intensity = (
        DEFAULT_GRID_INTENSITY if grid_intensity is None else max(0.0, float(grid_intensity))
    )

    kwh = info["typical_watts"] / WATTS_TO_KW * hours * 365
    return round(kwh * intensity, 2)


def annualized_footprint(device: dict[str, Any], grid_intensity: float | None = None) -> dict[str, Any]:
    """Annualised emissions for one device: amortised embodied plus operating.

    ``device`` needs ``device_type`` and ``purchase_year``; ``daily_hours`` is
    optional and falls back to the catalogue default.
    """
    device_type = device.get("device_type")
    info = DEVICE_TYPES.get(device_type)
    if not info:
        raise KeyError(f"Unknown device type: {device_type}")

    owned = years_owned(device.get("purchase_year"))
    embodied = info["embodied_kg"] * max(1, int(device.get("quantity", 1)))
    operating = operating_emissions(
        device_type, device.get("daily_hours"), grid_intensity
    ) * max(1, int(device.get("quantity", 1)))

    amortised = embodied / owned
    total = amortised + operating

    return {
        "device_type": device_type,
        "name": device.get("name") or device_type,
        "icon": info["icon"],
        "years_owned": round(owned, 1),
        "embodied_kg": round(embodied, 2),
        "amortised_embodied_kg": round(amortised, 2),
        "operating_kg": round(operating, 2),
        "annual_kg": round(total, 2),
        "embodied_share_pct": round(amortised / total * 100, 1) if total > 0 else 0.0,
        "expected_lifespan": info["lifespan_years"],
        "past_lifespan": owned > info["lifespan_years"] * OVERDUE_MULTIPLIER,
    }


def lifetime_footprint(device: dict[str, Any], grid_intensity: float | None = None) -> dict[str, Any]:
    """Total emissions across a device's whole expected life."""
    info = DEVICE_TYPES[device["device_type"]]
    quantity = max(1, int(device.get("quantity", 1)))
    operating = operating_emissions(
        device["device_type"], device.get("daily_hours"), grid_intensity
    ) * quantity
    embodied = info["embodied_kg"] * quantity
    lifetime = embodied + operating * info["lifespan_years"]

    return {
        "embodied_kg": round(embodied, 2),
        "lifetime_operating_kg": round(operating * info["lifespan_years"], 2),
        "lifetime_total_kg": round(lifetime, 2),
        "embodied_share_pct": round(embodied / lifetime * 100, 1) if lifetime else 0.0,
    }


def remaining_life(device: dict[str, Any]) -> dict[str, Any]:
    """How much of a device's expected life is left."""
    info = DEVICE_TYPES[device["device_type"]]
    owned = years_owned(device.get("purchase_year"))
    remaining = max(0.0, info["lifespan_years"] - owned)

    return {
        "years_owned": round(owned, 1),
        "expected_lifespan": info["lifespan_years"],
        "years_remaining": round(remaining, 1),
        "life_used_pct": round(min(100.0, owned / info["lifespan_years"] * 100), 1),
        "past_lifespan": remaining <= 0,
    }


def repair_vs_replace(
    device: dict[str, Any],
    repair_extends_years: float,
    replacement_type: str | None = None,
    efficiency_gain: float = DEFAULT_EFFICIENCY_GAIN,
    grid_intensity: float | None = None,
) -> dict[str, Any]:
    """Compare repairing a device against replacing it.

    Repair carbon is the emissions of continuing to run the old device for
    ``repair_extends_years``. Replacement carbon is the new unit's embodied
    footprint plus its (lower) running emissions over the same period.
    """
    device_type = device.get("device_type")
    if device_type not in DEVICE_TYPES:
        raise KeyError(f"Unknown device type: {device_type}")

    replacement_type = replacement_type or device_type
    if replacement_type not in DEVICE_TYPES:
        raise KeyError(f"Unknown replacement type: {replacement_type}")

    horizon = max(0.5, float(repair_extends_years or 0.5))
    gain = max(0.0, min(float(efficiency_gain), 0.9))

    old_operating = operating_emissions(
        device_type, device.get("daily_hours"), grid_intensity
    )
    new_operating = operating_emissions(
        replacement_type, device.get("daily_hours"), grid_intensity
    ) * (1 - gain)

    repair_kg = old_operating * horizon
    replace_kg = DEVICE_TYPES[replacement_type]["embodied_kg"] + new_operating * horizon
    difference = replace_kg - repair_kg

    operating_saving_per_year = old_operating - new_operating
    break_even_years = (
        DEVICE_TYPES[replacement_type]["embodied_kg"] / operating_saving_per_year
        if operating_saving_per_year > 0
        else None
    )

    verdict = "repair" if difference > 0 else "replace"

    if verdict == "repair":
        message = (
            f"Repairing avoids {difference:,.0f} kg CO₂ over the next "
            f"{horizon:.0f} year(s) - the replacement's manufacturing footprint "
            f"outweighs its efficiency gain."
        )
    else:
        message = (
            f"Replacing saves {abs(difference):,.0f} kg CO₂ over the next "
            f"{horizon:.0f} year(s) because this device is unusually power hungry."
        )

    return {
        "verdict": verdict,
        "repair_kg": round(repair_kg, 2),
        "replace_kg": round(replace_kg, 2),
        "difference_kg": round(difference, 2),
        "horizon_years": round(horizon, 1),
        "efficiency_gain": round(gain, 3),
        "break_even_years": round(break_even_years, 1) if break_even_years else None,
        "repairability": DEVICE_TYPES[device_type]["repairability"],
        "message": message,
    }


def upgrade_break_even(old_type: str, new_type: str, daily_hours: float | None = None, efficiency_gain: float = DEFAULT_EFFICIENCY_GAIN,
                       grid_intensity: float | None = None) -> dict[str, Any]:
    """Years of lower running cost needed to repay a new device's manufacturing debt."""
    if old_type not in DEVICE_TYPES or new_type not in DEVICE_TYPES:
        raise KeyError("Unknown device type")

    gain = max(0.0, min(float(efficiency_gain), 0.9))
    old_operating = operating_emissions(old_type, daily_hours, grid_intensity)
    new_operating = operating_emissions(new_type, daily_hours, grid_intensity) * (1 - gain)
    annual_saving = old_operating - new_operating
    embodied = DEVICE_TYPES[new_type]["embodied_kg"]

    if annual_saving <= 0:
        return {
            "annual_saving_kg": round(annual_saving, 2),
            "embodied_kg": embodied,
            "break_even_years": None,
            "ever_pays_back": False,
            "message": "The new device is not more efficient, so it never repays its manufacturing carbon.",
        }

    years = embodied / annual_saving
    return {
        "annual_saving_kg": round(annual_saving, 2),
        "embodied_kg": embodied,
        "break_even_years": round(years, 1),
        "ever_pays_back": years <= DEVICE_TYPES[new_type]["lifespan_years"],
        "message": (
            f"The new device repays its {embodied:,.0f} kg manufacturing footprint "
            f"after {years:.1f} years of use."
        ),
    }


def disposal_guidance(device: dict[str, Any]) -> dict[str, Any]:
    """Recommend a disposal route based on the device's condition and age."""
    device_type = device.get("device_type")
    info = DEVICE_TYPES.get(device_type)
    if not info:
        raise KeyError(f"Unknown device type: {device_type}")

    condition = device.get("condition", "Working")
    if condition not in DEVICE_CONDITIONS:
        condition = "Working"

    life = remaining_life(device)

    if condition == "Working" and not life["past_lifespan"]:
        route = "keep"
    elif condition == "Working":
        route = "resell"
    elif condition == "Degraded":
        route = "donate" if life["past_lifespan"] else "repair"
    elif condition == "Faulty":
        route = "repair" if info["repairability"] >= 5 else "recycle"
    else:
        route = "recycle"

    return {
        "route": route,
        "label": DISPOSAL_ROUTES[route]["label"],
        "icon": DISPOSAL_ROUTES[route]["icon"],
        "detail": DISPOSAL_ROUTES[route]["detail"],
        "condition": condition,
        "repairability": info["repairability"],
        "recoverable_kg": info["recyclable_kg"],
        "hazardous": info["hazardous"],
        "warning": (
            "Contains a lithium battery - never put this in household waste or "
            "kerbside recycling."
            if info["hazardous"]
            else None
        ),
    }


def portfolio_summary(devices: list[dict[str, Any]], grid_intensity: float | None = None) -> dict[str, Any]:
    """Aggregate every device a user owns."""
    devices = devices or []
    rows = []

    for device in devices:
        if device.get("device_type") not in DEVICE_TYPES:
            continue
        row = annualized_footprint(device, grid_intensity)
        row["id"] = device.get("id")
        row["condition"] = device.get("condition", "Working")
        rows.append(row)

    if not rows:
        return {
            "devices": [],
            "device_count": 0,
            "total_embodied_kg": 0.0,
            "total_annual_kg": 0.0,
            "total_operating_kg": 0.0,
            "average_age_years": 0.0,
            "past_lifespan_count": 0,
            "heaviest": None,
        }

    rows.sort(key=lambda row: row["annual_kg"], reverse=True)

    total_annual = sum(row["annual_kg"] for row in rows)
    for row in rows:
        row["share_pct"] = (
            round(row["annual_kg"] / total_annual * 100, 1) if total_annual > 0 else 0.0
        )

    return {
        "devices": rows,
        "device_count": len(rows),
        "total_embodied_kg": round(sum(row["embodied_kg"] for row in rows), 2),
        "total_annual_kg": round(total_annual, 2),
        "total_operating_kg": round(sum(row["operating_kg"] for row in rows), 2),
        "average_age_years": round(
            sum(row["years_owned"] for row in rows) / len(rows), 1
        ),
        "past_lifespan_count": sum(1 for row in rows if row["past_lifespan"]),
        "heaviest": rows[0]["name"],
    }


def extension_savings(devices: list[dict[str, Any]], extra_years: float, grid_intensity: float | None = None) -> dict[str, Any]:
    """CO2 avoided by keeping every device ``extra_years`` longer.

    Extending ownership does not reduce emissions already released; it spreads
    them over more years, which is what lowers the annualised figure.
    """
    devices = devices or []
    extra_years = max(0.0, float(extra_years or 0.0))

    current = 0.0
    extended = 0.0

    for device in devices:
        if device.get("device_type") not in DEVICE_TYPES:
            continue
        now = annualized_footprint(device, grid_intensity)
        stretched_embodied = now["embodied_kg"] / (now["years_owned"] + extra_years)
        current += now["annual_kg"]
        extended += stretched_embodied + now["operating_kg"]

    saved = current - extended
    return {
        "extra_years": round(extra_years, 1),
        "current_annual_kg": round(current, 2),
        "extended_annual_kg": round(extended, 2),
        "saved_annual_kg": round(saved, 2),
        "saved_pct": round(saved / current * 100, 1) if current > 0 else 0.0,
    }


def get_lifecycle_tips(summary: dict[str, Any], limit: int = 5) -> list[str]:
    """Return tips ranked by what this particular portfolio looks like."""
    if not summary.get("devices"):
        return ["Register your electronics to see their manufacturing footprint."]

    tips = []

    if summary["past_lifespan_count"]:
        tips.append(
            f"{summary['past_lifespan_count']} of your devices are past their expected "
            f"lifespan and still working - every extra year keeps lowering their annual cost."
        )

    heaviest = summary["devices"][0]
    if heaviest["embodied_share_pct"] >= 50:
        tips.append(
            f"{heaviest['embodied_share_pct']:.0f}% of your {heaviest['name']}'s annual "
            f"footprint is manufacturing, not electricity - keeping it longer beats "
            f"any efficiency setting."
        )
    else:
        tips.append(
            f"Your {heaviest['name']} is dominated by running energy - check its power "
            f"settings and standby draw."
        )

    if summary["average_age_years"] < 2:
        tips.append(
            "Your devices are young. Aim to reach the end of their expected lifespan "
            "before replacing anything."
        )
    else:
        tips.append(
            f"Your devices average {summary['average_age_years']} years old - "
            f"a battery or screen repair usually beats a replacement on carbon."
        )

    tips.append(
        "Buy refurbished where you can: it avoids the manufacturing footprint entirely."
    )
    tips.append(
        "Never bin electronics. Certified recyclers recover metals and handle batteries safely."
    )

    return tips[: max(0, int(limit))]


def _get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_NAME)


def init_device_lifecycle_db() -> bool:
    """Create the device table if it does not exist yet."""
    conn = None
    try:
        conn = _get_conn()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                purchase_year INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                daily_hours REAL,
                condition TEXT NOT NULL DEFAULT 'Working',
                status TEXT NOT NULL DEFAULT 'active',
                retired_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("Device lifecycle init error: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def register_device(user_id: int, name: str, device_type: str, purchase_year: int, quantity: int = 1,
                    daily_hours: float | None = None, condition: str = "Working") -> int | None:
    """Register a device. Returns the new row id, or None if invalid."""
    if device_type not in DEVICE_TYPES:
        logger.warning("Refusing to register unknown device type: %s", device_type)
        return None

    init_device_lifecycle_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            """
            INSERT INTO user_devices (
                user_id, name, device_type, purchase_year, quantity,
                daily_hours, condition
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                (name or device_type).strip() or device_type,
                device_type,
                _clean_year(purchase_year),
                max(1, int(quantity or 1)),
                None if daily_hours is None else max(0.0, min(float(daily_hours), 24.0)),
                condition if condition in DEVICE_CONDITIONS else "Working",
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except (sqlite3.Error, ValueError, TypeError) as exc:
        logger.error("Unable to register device: %s", exc)
        return None
    finally:
        if conn:
            conn.close()


def get_devices(user_id: int, include_retired: bool = False) -> list[dict[str, Any]]:
    """Return a user's devices, newest first."""
    init_device_lifecycle_db()
    conn = None
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        query = """
            SELECT id, name, device_type, purchase_year, quantity, daily_hours,
                   condition, status, retired_at, created_at
            FROM user_devices
            WHERE user_id = ?
        """
        if not include_retired:
            query += " AND status = 'active'"
        query += " ORDER BY purchase_year DESC, id DESC"

        rows = conn.execute(query, (user_id,)).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.error("Unable to load devices: %s", exc)
        return []
    finally:
        if conn:
            conn.close()


def update_device(device_id: int, condition: str | None = None, daily_hours: float | None = None, quantity: int | None = None) -> bool:
    """Update a registered device's condition, usage hours or quantity."""
    init_device_lifecycle_db()
    updates = []
    params = []

    if condition in DEVICE_CONDITIONS:
        updates.append("condition = ?")
        params.append(condition)
    if daily_hours is not None:
        updates.append("daily_hours = ?")
        params.append(max(0.0, min(float(daily_hours), 24.0)))
    if quantity is not None:
        updates.append("quantity = ?")
        params.append(max(1, int(quantity)))

    if not updates:
        return False

    conn = None
    try:
        conn = _get_conn()
        params.append(device_id)
        cursor = conn.execute(
            f"UPDATE user_devices SET {', '.join(updates)} WHERE id = ?", params
        )
        conn.commit()
        return cursor.rowcount > 0
    except (sqlite3.Error, ValueError, TypeError) as exc:
        logger.error("Unable to update device: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def retire_device(device_id: int) -> bool:
    """Mark a device retired without losing its history."""
    init_device_lifecycle_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute(
            """
            UPDATE user_devices
            SET status = 'retired', retired_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'active'
            """,
            (device_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to retire device: %s", exc)
        return False
    finally:
        if conn:
            conn.close()


def delete_device(device_id: int) -> bool:
    """Permanently delete a registered device."""
    init_device_lifecycle_db()
    conn = None
    try:
        conn = _get_conn()
        cursor = conn.execute("DELETE FROM user_devices WHERE id = ?", (device_id,))
        conn.commit()
        return cursor.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("Unable to delete device: %s", exc)
        return False
    finally:
        if conn:
            conn.close()
