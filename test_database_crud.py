import pytest
import os
import sqlite3
import database as db

# Use a test database
TEST_DB = "test_eco_buddy.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    original_db_name = db.DB_NAME
    db.DB_NAME = TEST_DB
    # Setup
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db.init_db()
    db.init_energy_db()
    db.init_marketplace_db()
    yield
    # Teardown
    db.DB_NAME = original_db_name
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_add_and_get_appliance():
    # Test adding an appliance
    success = db.add_appliance(1, "Test AC", "AC", 2, 1500, 5, 10)
    assert success is True

    # Test getting appliances
    appliances = db.get_appliances(1)
    assert len(appliances) == 1
    assert appliances[0]['name'] == "Test AC"
    assert appliances[0]['category'] == "AC"
    assert appliances[0]['quantity'] == 2
    assert appliances[0]['power_rating_watts'] == 1500
    assert appliances[0]['hours_used_per_day'] == 5
    assert appliances[0]['standby_draw_watts'] == 10

def test_delete_appliance():
    db.add_appliance(1, "Test Heater", "Heat Pump", 1, 2000, 4, 0)
    appliances = db.get_appliances(1)
    app_id = appliances[0]['id']
    
    success = db.delete_appliance(app_id)
    assert success is True
    
    appliances_after = db.get_appliances(1)
    assert len(appliances_after) == 0

def test_save_and_get_solar_config():
    success = db.save_solar_config(1, 50.0, 5.0, 0.12, 22.0, 2000.0, 150.0, 2.5)
    assert success is True
    
    config = db.get_solar_config(1)
    assert config is not None
    assert config['roof_space_m2'] == 50.0
    assert config['peak_sun_hours'] == 5.0
    assert config['utility_rate_per_kwh'] == 0.12
    assert config['panel_efficiency'] == 22.0
    assert config['installation_cost_per_kw'] == 2000.0
    assert config['maintenance_cost_per_year'] == 150.0
    assert config['annual_rate_increase'] == 2.5

def test_init_marketplace_db():
    assert db.init_marketplace_db() is True

def test_save_and_get_journey_profile():
    db.init_marketplace_db()
    success = db.save_journey_profile(1, "Commute", 15.0, "Car", 1, 5, True)
    assert success is True
    
    profiles = db.get_journey_profiles(1)
    assert len(profiles) == 1
    assert profiles[0]['name'] == "Commute"
    assert profiles[0]['distance_km'] == 15.0

def test_delete_journey_profile():
    db.init_marketplace_db()
    db.save_journey_profile(1, "Trip", 100.0, "Bus", 1, 1, False)
    profiles = db.get_journey_profiles(1)
    
    success = db.delete_journey_profile(profiles[0]['id'])
    assert success is True
    
    profiles_after = db.get_journey_profiles(1)
    assert len(profiles_after) == 0

def test_save_and_get_offset_transactions():
    db.init_marketplace_db()
    success = db.save_offset_transaction(1, "proj_1", "Test Project", 2.5, 10.0, 25.0)
    assert success is True
    
    transactions = db.get_offset_transactions(1)
    assert len(transactions) == 1
    assert transactions[0]['project_name'] == "Test Project"
    assert transactions[0]['offset_tonnes'] == 2.5
    assert transactions[0]['total_cost'] == 25.0

def test_delete_offset_transaction():
    db.init_marketplace_db()
    db.save_offset_transaction(1, "proj_2", "Test Project 2", 1.0, 15.0, 15.0)
    transactions = db.get_offset_transactions(1)
    
    success = db.delete_offset_transaction(transactions[0]['id'])
    assert success is True
    
    transactions_after = db.get_offset_transactions(1)
    assert len(transactions_after) == 0

def test_get_total_offsets_and_spend():
    db.init_marketplace_db()
    db.save_offset_transaction(1, "proj_1", "Project 1", 2.0, 10.0, 20.0)
    db.save_offset_transaction(1, "proj_2", "Project 2", 3.0, 15.0, 45.0)
    
    total_offsets = db.get_total_offsets(1)
    total_spend = db.get_total_spend(1)
    
    assert total_offsets == 5.0
    assert total_spend == 65.0

def test_user_crud():
    # Create user
    success = db.create_user("testuser", "test@example.com", "password123", False)
    assert success is True
    
    # Try creating duplicate
    success2 = db.create_user("testuser", "test2@example.com", "pass", False)
    assert success2 is False
    
    # Verify user
    user = db.verify_user("testuser", "password123")
    assert user is not None
    assert user["username"] == "testuser"
    
    # Verify invalid password
    bad_user = db.verify_user("testuser", "wrongpass")
    assert bad_user is None
    
    # Get user by username
    user_data = db.get_user_by_username("testuser")
    assert user_data is not None
    assert user_data["email"] == "test@example.com"
    
    # Update preference
    assert db.update_user_leaderboard_preference(user["id"], True) is True
    
def test_carbon_budget_crud():
    db.create_user("budgetuser", "budget@example.com", "pass", False)
    user = db.get_user_by_username("budgetuser")
    user_id = user["id"]
    
    # Create budget
    success = db.save_carbon_budget(user_id, "monthly", 500.0)
    assert success is True
    
    # Get budget
    budget = db.get_carbon_budget(user_id)
    assert budget is not None
    assert budget[0] == "monthly"
    assert budget[1] == 500.0
    
    # Update budget
    update_success = db.update_carbon_budget(user_id, "yearly", 6000.0)
    assert update_success is True
    
    budget_after = db.get_carbon_budget(user_id)
    assert budget_after[0] == "yearly"
    assert budget_after[1] == 6000.0

