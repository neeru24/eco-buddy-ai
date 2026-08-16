import streamlit as st
from config import HOURS_PER_DAY, WATTS_TO_KW, DAYS_PER_YEAR, MONTHS_PER_YEAR
from cache import cached
from cache_config import TTL_COMPUTED_ANALYTICS, CACHE_CATEGORY_COMPUTED
from typing import Any


def calculate_appliance_energy(power_rating_watts: float, hours_used_per_day: float,
                               standby_draw_watts: float, quantity: int) -> tuple[float, float, float]:
    standby_hours = max(0, HOURS_PER_DAY - hours_used_per_day)
    active_energy_kwh = (power_rating_watts * hours_used_per_day * quantity) / WATTS_TO_KW
    standby_energy_kwh = (standby_draw_watts * standby_hours * quantity) / WATTS_TO_KW
    total_daily_kwh = active_energy_kwh + standby_energy_kwh
    return total_daily_kwh, active_energy_kwh, standby_energy_kwh


def calculate_appliance_cost(daily_kwh: float, rate_per_kwh: float) -> tuple[float, float, float]:
    daily_cost = daily_kwh * rate_per_kwh
    return daily_cost, daily_cost * MONTHS_PER_YEAR, daily_cost * DAYS_PER_YEAR


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_home_energy_summary(appliances: list[dict[str, Any]]) -> tuple[float, float, float]:
    total_daily_kwh = sum(calculate_appliance_energy(a['power_rating_watts'], a['hours_used_per_day'], a['standby_draw_watts'], a['quantity'])[0] for a in appliances)
    return total_daily_kwh, total_daily_kwh * MONTHS_PER_YEAR, total_daily_kwh * DAYS_PER_YEAR


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def generate_hourly_energy_profile(appliances: list[dict[str, Any]]) -> list[float]:
    profile = [0.0] * HOURS_PER_DAY
    for app in appliances:
        pwr = app['power_rating_watts'] * app['quantity']
        hrs = app['hours_used_per_day']
        stdby = app['standby_draw_watts'] * app['quantity']
        
        for i in range(HOURS_PER_DAY):
            profile[i] += stdby / WATTS_TO_KW
            
        if hrs > 0:
            full_hours = int(hrs)
            fraction = hrs - full_hours
            start_hr = max(0, 18 - int(hrs / 2))
            
            for i in range(full_hours):
                hr = (start_hr + i) % HOURS_PER_DAY
                profile[hr] += pwr / WATTS_TO_KW
            
            if fraction > 0 and full_hours < HOURS_PER_DAY:
                hr = (start_hr + full_hours) % HOURS_PER_DAY
                profile[hr] += (pwr * fraction) / WATTS_TO_KW
    return profile


def calculate_solar_system_size(roof_space_m2: float, panel_efficiency_pct: float) -> float:
    return roof_space_m2 * (panel_efficiency_pct / 100.0)


def calculate_annual_solar_generation(system_size_kw: float, peak_sun_hours: float,
                                      performance_ratio: float = 0.75) -> float:
    return system_size_kw * peak_sun_hours * DAYS_PER_YEAR * performance_ratio


def calculate_solar_installation_cost(system_size_kw: float, cost_per_kw: float) -> float:
    return system_size_kw * cost_per_kw


def calculate_solar_payback_period(installation_cost: float, annual_savings: float) -> float:
    if annual_savings <= 0: return float('inf')
    return installation_cost / annual_savings


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def calculate_long_term_solar_savings(annual_generation_kwh: float, utility_rate: float,
                                      years: int, rate_increase_pct: float,
                                      maintenance_cost: float) -> float:
    total_savings = 0
    current_rate = utility_rate
    for _ in range(years):
        yearly_savings = (annual_generation_kwh * current_rate) - maintenance_cost
        total_savings += yearly_savings
        current_rate *= (1 + rate_increase_pct / 100.0)
    return total_savings


def calculate_solar_carbon_offset(annual_generation_kwh: float,
                                  grid_carbon_intensity_kg_kwh: float = 0.4) -> float:
    return annual_generation_kwh * grid_carbon_intensity_kg_kwh


ROOM_TYPES = {
    'Living Room': {
        'icon': '🛋️',
        'typical_appliances': ['TV', 'Lighting', 'AC/Fan', 'Sound System', 'Router'],
        'base_wattage': 800,
        'daily_hours': 6,
    },
    'Kitchen': {
        'icon': '🍳',
        'typical_appliances': ['Refrigerator', 'Oven/Microwave', 'Lighting', 'Exhaust Fan', 'Dishwasher'],
        'base_wattage': 1200,
        'daily_hours': 4,
    },
    'Bedroom': {
        'icon': '🛏️',
        'typical_appliances': ['Lighting', 'AC/Fan', 'Chargers', 'Lamp'],
        'base_wattage': 500,
        'daily_hours': 8,
    },
    'Bathroom': {
        'icon': '🚿',
        'typical_appliances': ['Water Heater', 'Lighting', 'Exhaust Fan', 'Hair Dryer'],
        'base_wattage': 1500,
        'daily_hours': 2,
    },
    'Home Office': {
        'icon': '💻',
        'typical_appliances': ['Computer', 'Monitor', 'Lighting', 'Printer', 'AC/Fan'],
        'base_wattage': 600,
        'daily_hours': 8,
    },
    'Hall/Dining': {
        'icon': '🚪',
        'typical_appliances': ['Lighting', 'Fan', 'TV', 'AC'],
        'base_wattage': 700,
        'daily_hours': 5,
    },
    'Utility Room': {
        'icon': '🔧',
        'typical_appliances': ['Washing Machine', 'Dryer', 'Water Heater', 'Lighting'],
        'base_wattage': 2000,
        'daily_hours': 2,
    },
}


@cached(category=CACHE_CATEGORY_COMPUTED, ttl=TTL_COMPUTED_ANALYTICS)
def estimate_room_energy(room_type: str, area_sqft: float, num_devices: int = 1) -> dict[str, Any]:
    room = ROOM_TYPES.get(room_type, ROOM_TYPES['Living Room'])
    base_wattage = room['base_wattage'] * num_devices
    area_factor = area_sqft / 200.0
    daily_kwh = (base_wattage * room['daily_hours'] * area_factor) / 1000.0
    monthly_kwh = daily_kwh * 30
    yearly_kwh = daily_kwh * 365
    return {
        'daily_kwh': round(daily_kwh, 2),
        'monthly_kwh': round(monthly_kwh, 2),
        'yearly_kwh': round(yearly_kwh, 2),
        'appliances': room['typical_appliances'],
        'icon': room['icon'],
    }


def generate_room_recommendations(room_type: str, daily_kwh: float) -> tuple[list[tuple[str, str, str, int, int]], float, int]:
    recommendations = []
    room = ROOM_TYPES.get(room_type, ROOM_TYPES['Living Room'])

    common_recs = [
        ('💡', 'Switch to LED lighting', 'Reduce lighting energy by up to 80%', 5, 15),
    ]

    room_specific = {
        'Living Room': [
            ('📺', 'Use smart power strips for entertainment', 'Eliminate standby power drain', 3, 10),
            ('🌡️', 'Set AC thermostat to 24°C', 'Save 6-8% on cooling per degree', 4, 12),
        ],
        'Kitchen': [
            ('🧊', 'Keep refrigerator coils clean', 'Improve efficiency by up to 30%', 2, 8),
            ('🍳', 'Use microwave/convection instead of oven', 'Uses 50% less energy for small meals', 5, 10),
        ],
        'Bedroom': [
            ('🌡️', 'Use fan instead of AC when possible', 'Uses 90% less energy than AC', 5, 20),
            ('🔌', 'Unplug chargers when not in use', 'Eliminate phantom load', 2, 5),
        ],
        'Bathroom': [
            ('🚿', 'Install low-flow shower head', 'Reduce water heating energy', 5, 15),
            ('💧', 'Use cold water for washing', 'Eliminates water heating cost', 3, 10),
        ],
        'Home Office': [
            ('💻', 'Enable power saving on devices', 'Reduce energy by 30%', 3, 8),
            ('📱', 'Use laptop instead of desktop', 'Uses 80% less energy', 5, 12),
        ],
        'Hall/Dining': [
            ('💡', 'Install motion sensor lighting', 'Eliminate unnecessary usage', 3, 8),
            ('🌡️', 'Zone cooling to occupied rooms', 'Reduce AC load', 4, 15),
        ],
        'Utility Room': [
            ('👕', 'Air dry clothes instead of dryer', 'Eliminate dryer energy entirely', 8, 25),
            ('🧺', 'Run full loads only', 'Reduce frequency by 30%', 3, 8),
        ],
    }

    recommendations.extend(common_recs)
    recommendations.extend(room_specific.get(room_type, []))

    savings_pct = sum(r[3] for r in recommendations)
    potential_savings_kwh = daily_kwh * (savings_pct / 100.0)

    return recommendations, round(potential_savings_kwh, 2), savings_pct


def estimate_home_blueprint(rooms: list[dict[str, Any]]) -> dict[str, Any]:
    total_daily_kwh = 0
    room_details = []

    for room in rooms:
        est = estimate_room_energy(room['type'], room['area_sqft'], room.get('devices', 1))
        recs, savings, pct = generate_room_recommendations(room['type'], est['daily_kwh'])
        total_daily_kwh += est['daily_kwh']
        room_details.append({
            'name': room.get('name', room['type']),
            'type': room['type'],
            'area_sqft': room['area_sqft'],
            'icon': est['icon'],
            'usage': est,
            'recommendations': recs,
            'potential_savings_kwh': savings,
            'savings_pct': pct,
        })

    total_monthly = total_daily_kwh * 30
    total_yearly = total_daily_kwh * 365
    total_savings_daily = sum(r['potential_savings_kwh'] for r in room_details)

    return {
        'rooms': room_details,
        'total_daily_kwh': round(total_daily_kwh, 2),
        'total_monthly_kwh': round(total_monthly, 2),
        'total_yearly_kwh': round(total_yearly, 2),
        'total_savings_daily_kwh': round(total_savings_daily, 2),
        'total_savings_yearly_kwh': round(total_savings_daily * 365, 2),
    }
