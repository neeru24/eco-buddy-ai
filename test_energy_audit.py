import pytest
import energy_audit as ea

def test_calculate_appliance_energy():
    # 1000W, 4 hours active, 5W standby, quantity 1
    # Active: 1000 * 4 = 4000Wh = 4kWh
    # Standby: 20 hours * 5W = 100Wh = 0.1kWh
    # Total: 4.1kWh
    total, active, standby = ea.calculate_appliance_energy(1000.0, 4.0, 5.0, 1)
    assert total == 4.1
    assert active == 4.0
    assert standby == 0.1

def test_calculate_appliance_cost():
    # 5 kWh/day at $0.20/kWh
    daily, monthly, yearly = ea.calculate_appliance_cost(5.0, 0.20)
    assert daily == 1.0
    assert monthly == 12.0
    assert yearly == 365.0

def test_calculate_home_energy_summary():
    appliances = [
        {'power_rating_watts': 1000, 'hours_used_per_day': 4, 'standby_draw_watts': 5, 'quantity': 1},
        {'power_rating_watts': 100, 'hours_used_per_day': 10, 'standby_draw_watts': 1, 'quantity': 5}
    ]
    # App1: 4.1 kWh
    # App2: (100*10*5)/1000 = 5kWh active, (1*14*5)/1000 = 0.07kWh standby -> 5.07 kWh
    # Total: 9.17 kWh
    daily, monthly, yearly = ea.calculate_home_energy_summary(appliances)
    assert pytest.approx(daily) == 9.17
    assert pytest.approx(monthly) == 9.17 * 12
    assert pytest.approx(yearly) == 9.17 * 365

def test_generate_hourly_energy_profile():
    appliances = [
        {'power_rating_watts': 1000, 'hours_used_per_day': 4, 'standby_draw_watts': 0, 'quantity': 1}
    ]
    profile = ea.generate_hourly_energy_profile(appliances)
    assert len(profile) == 24
    assert sum(profile) == 4.0

def test_calculate_solar_system_size():
    # 30m2 at 20% efficiency -> 30 * 0.2 = 6kW
    size = ea.calculate_solar_system_size(30.0, 20.0)
    assert size == 6.0

def test_calculate_annual_solar_generation():
    # 6kW * 5 hours * 365 * 0.75 = 8212.5 kWh
    gen = ea.calculate_annual_solar_generation(6.0, 5.0, 0.75)
    assert gen == 8212.5

def test_calculate_solar_payback_period():
    payback = ea.calculate_solar_payback_period(10000.0, 2000.0)
    assert payback == 5.0

def test_calculate_solar_carbon_offset():
    offset = ea.calculate_solar_carbon_offset(8000.0, 0.4)
    assert offset == 3200.0
