import pytest
import os
import json
import zipfile
import io
import database as db
import data_io as io_mod

# Use a test database
TEST_DB = "test_eco_buddy_io.db"

@pytest.fixture(autouse=True)
def setup_teardown():
    original_db_name = db.DB_NAME
    # Setup
    db.DB_NAME = TEST_DB
    io_mod.DB_NAME = TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    db.init_db()
    db.init_energy_db()
    db.init_gamification_db()
    db.init_marketplace_db()
    yield
    # Teardown
    db.DB_NAME = original_db_name
    io_mod.DB_NAME = original_db_name
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def test_export_import_json_roundtrip():
    # Populate some data
    db.save_assessment(1, "Car", 20.0, 150.0, "Vegan", 1, 10.5, 85)
    db.add_appliance(1, "Test AC", "AC", 1, 1500, 5, 10)
    db.save_offset_transaction(1, "proj_1", "Test Project", 2.5, 10.0, 25.0)
    
    # Export data
    json_data = io_mod.export_data_json()
    data = json.loads(json_data)
    
    assert "assessments" in data
    assert "appliances" in data
    assert "offset_transactions" in data
    
    assert len(data["assessments"]) == 1
    assert len(data["appliances"]) == 1
    assert len(data["offset_transactions"]) == 1
    
    # Modify data to test import 'replace' strategy
    db.save_assessment(1, "Bus", 10.0, 100.0, "Meat", 0, 5.5, 60)
    
    # Import data using 'replace'
    success, msg = io_mod.import_data_json(json_data, strategy="replace")
    assert success is True
    
    # Verify replaced data
    assessments = db.get_assessments(1)
    assert len(assessments) == 1
    assert assessments[0][2] == "Car" # Index 2 is transport
    
def test_import_json_merge_strategy():
    # Populate some data
    db.save_assessment(1, "Car", 20.0, 150.0, "Vegan", 1, 10.5, 85)
    db.add_appliance(1, "Test AC", "AC", 1, 1500, 5, 10)
    
    # Export data
    json_data = io_mod.export_data_json()
    
    # Add another record before merge
    db.save_assessment(1, "Bike", 5.0, 50.0, "Vegan", 0, 1.0, 95)
    
    # Import data using 'merge'
    success, msg = io_mod.import_data_json(json_data, strategy="merge")
    assert success is True
    
    # Verify merged data
    assessments = db.get_assessments(1)
    # The original was merged (but it should be skipped if timestamp matches, or ignored if it's already there)
    # Actually, merge won't delete the new "Bike" record.
    assert len(assessments) == 2 
    
def test_export_data_csv_zip():
    db.save_assessment(1, "Train", 50.0, 200.0, "Vegetarian", 2, 12.0, 70)
    db.add_appliance(1, "Test Fridge", "Fridge", 1, 300, 24, 0)
    
    zip_bytes = io_mod.export_data_csv_zip()
    assert zip_bytes is not None
    
    # Verify ZIP contents
    with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as zip_ref:
        files = zip_ref.namelist()
        assert "assessments.csv" in files
        assert "appliances.csv" in files
        
        with zip_ref.open("assessments.csv") as f:
            content = f.read().decode("utf-8")
            assert "Train" in content
            
def test_import_invalid_json():
    success, msg = io_mod.import_data_json("not valid json", strategy="merge")
    assert success is False
    assert "Invalid JSON file format" in msg
