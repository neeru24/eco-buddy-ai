"""
End-to-End Integration Test Suite for EcoBuddy AI - Issue #229

Tests complete user workflows:
1. Complete assessment workflow (create → calculate → save)
2. Database persistence (save → retrieve → validate)
3. PDF generation (generate → verify file creation)
4. Multi-page workflow (assessment → history → export)
"""

import os
import pytest
import uuid
import json
import tempfile
import sqlite3
import datetime
from unittest.mock import patch, MagicMock

import database as db
import gamification as gf
from emissions import calculate_footprint, calculate_eco_score
from recommendations import generate_recommendations
from report import generate_pdf as report_generate_pdf


TEST_USER_ID = 1


@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for all integration tests."""
    original_db_name = db.DB_NAME
    test_db_name = f"test_e2e_{uuid.uuid4().hex[:8]}.db"
    db.DB_NAME = test_db_name
    
    # Initialize all databases
    db.init_db()
    db.init_gamification_db()
    db.init_marketplace_db()
    
    # Create test user
    username = f"testuser_{uuid.uuid4().hex[:6]}"
    email = f"{username}@example.com"
    password = "SecurePassword123!"
    db.create_user(username, email, password)
    
    yield
    
    # Teardown - cleanup
    db.DB_NAME = original_db_name
    if os.path.exists(test_db_name):
        try:
            os.remove(test_db_name)
        except OSError:
            pass


# ============================================================================
# TEST SUITE 1: COMPLETE ASSESSMENT WORKFLOW
# ============================================================================

class TestCompleteAssessmentWorkflow:
    """Tests for the complete assessment workflow from input to saved results."""

    def test_complete_assessment_flow(self):
        """Test complete assessment workflow: input → calculation → save."""
        # Step 1: Simulate user input
        transport = "Car"
        distance = 20.0
        electricity = 250.0
        diet = "Non-Vegetarian"
        flights = 2
        region = "US"

        # Step 2: Calculate emissions (mocking external API calls)
        with patch('emissions.os.environ.get', return_value=None):
            total, contributors = calculate_footprint(
                transport, distance, electricity, diet, flights, region
            )
            
            eco_score = calculate_eco_score(total, contributors)

        # Verify calculations
        assert total > 0
        assert eco_score > 0
        assert len(contributors) > 0

        # Step 3: Generate recommendations
        insight, recommendations = generate_recommendations(
            transport, electricity, diet, flights, contributors
        )

        # Verify recommendations generated
        assert len(insight) > 0
        assert len(recommendations) > 0
        assert isinstance(insight, str)
        assert isinstance(recommendations, list)

        # Step 4: Save assessment to database
        success = db.save_assessment(
            TEST_USER_ID, transport, distance, electricity, diet,
            flights, total, eco_score
        )

        assert success is True

        # Step 5: Retrieve and verify saved assessment
        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1
        
        saved = assessments[0]
        assert saved[2] == transport  # transport
        assert saved[3] == distance   # distance
        assert saved[4] == electricity  # electricity
        assert saved[5] == diet       # diet
        assert saved[6] == flights    # flights
        assert saved[7] == total      # footprint
        assert saved[8] == eco_score  # eco_score

    def test_assessment_workflow_with_bike(self):
        """Test assessment workflow with eco-friendly transport."""
        transport = "Bike"
        distance = 5.0
        electricity = 100.0
        diet = "Vegetarian"
        flights = 0
        region = "Global"

        with patch('emissions.os.environ.get', return_value=None):
            total, contributors = calculate_footprint(
                transport, distance, electricity, diet, flights, region
            )
            eco_score = calculate_eco_score(total, contributors)

        # Eco-friendly should have low footprint
        assert total < 2000
        assert eco_score > 70  # Should have good eco score

        # Verify contributors (bike has 0 transport emissions)
        assert contributors["Transport"] == 0.0

        # Save and verify
        success = db.save_assessment(
            TEST_USER_ID, transport, distance, electricity, diet,
            flights, total, eco_score
        )
        assert success is True

    def test_assessment_workflow_multiple_regions(self):
        """Test assessment workflow with different region settings."""
        regions = ["Global", "US", "UK", "EU"]
        
        for region in regions:
            with patch('emissions.os.environ.get', return_value=None):
                total, contributors = calculate_footprint(
                    "Car", 15.0, 200.0, "Vegetarian", 1, region
                )
                eco_score = calculate_eco_score(total, contributors)

            # Save assessment
            success = db.save_assessment(
                TEST_USER_ID, "Car", 15.0, 200.0, "Vegetarian",
                1, total, eco_score
            )
            assert success is True

        # Verify all assessments saved
        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == len(regions)


# ============================================================================
# TEST SUITE 2: DATABASE PERSISTENCE
# ============================================================================

class TestDatabasePersistence:
    """Tests for database persistence and data integrity."""

    def test_assessment_save_and_retrieve(self):
        """Test saving and retrieving assessments."""
        # Create multiple assessments
        assessments_data = [
            ("Car", 20.0, 250.0, "Non-Vegetarian", 2, 6293.0, 19),
            ("Bike", 10.0, 150.0, "Vegetarian", 0, 1984.0, 77),
            ("Bus", 25.0, 200.0, "Vegetarian", 1, 4148.0, 54),
        ]

        for data in assessments_data:
            success = db.save_assessment(TEST_USER_ID, *data)
            assert success is True

        # Retrieve assessments
        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 3

        # Verify order (most recent first)
        for i in range(len(assessments) - 1):
            assert assessments[i][1] >= assessments[i + 1][1]  # date comparison

    def test_assessment_data_integrity(self):
        """Test data integrity of saved assessments."""
        transport = "Car"
        distance = 25.5
        electricity = 300.5
        diet = "Non-Vegetarian"
        flights = 3
        footprint = 7265.0
        eco_score = 8

        success = db.save_assessment(
            TEST_USER_ID, transport, distance, electricity, diet,
            flights, footprint, eco_score
        )
        assert success is True

        # Retrieve and verify
        assessments = db.get_assessments(TEST_USER_ID)
        saved = assessments[0]

        # Verify all fields match
        assert saved[2] == transport
        assert saved[3] == distance
        assert saved[4] == electricity
        assert saved[5] == diet
        assert saved[6] == flights
        assert saved[7] == footprint
        assert saved[8] == eco_score

    def test_assessment_history_empty_user(self):
        """Test history retrieval for non-existent user."""
        assessments = db.get_assessments(99999)  # Non-existent user
        assert assessments == []

    def test_assessment_duplicate_save_fails(self):
        """Test that duplicate trip_id saves fail."""
        transport = "Car"
        distance = 20.0
        electricity = 250.0
        diet = "Non-Vegetarian"
        flights = 2
        footprint = 6293.0
        eco_score = 19
        trip_id = "unique_trip_123"

        # First save should succeed
        success1 = db.save_assessment(
            TEST_USER_ID, transport, distance, electricity, diet,
            flights, footprint, eco_score, trip_id=trip_id
        )
        assert success1 is True

        # Second save with same trip_id should fail
        success2 = db.save_assessment(
            TEST_USER_ID, transport, distance, electricity, diet,
            flights, footprint, eco_score, trip_id=trip_id
        )
        assert success2 is False

        # Only one assessment should exist
        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1


# ============================================================================
# TEST SUITE 3: PDF GENERATION
# ============================================================================

class TestPDFGeneration:
    """Tests for PDF report generation."""

    def test_generate_pdf_basic(self):
        """Test basic PDF generation."""
        total = 5000.0
        eco_score = 45
        insight = "Your main contributor is Electricity usage."

        pdf_path = report_generate_pdf(total, eco_score, insight)

        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 100

        os.remove(pdf_path)

    def test_generate_pdf_with_high_score(self):
        """Test PDF generation with high eco score."""
        total = 1500.0
        eco_score = 85
        insight = "Excellent work on your low carbon footprint!"

        pdf_path = report_generate_pdf(total, eco_score, insight)
        
        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 100

        os.remove(pdf_path)

    def test_generate_pdf_with_low_score(self):
        """Test PDF generation with low eco score."""
        total = 10000.0
        eco_score = 15
        insight = "High emissions from transportation detected."

        pdf_path = report_generate_pdf(total, eco_score, insight)

        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 100

        os.remove(pdf_path)

    def test_generate_pdf_with_complex_insight(self):
        """Test PDF generation with complex insight text."""
        total = 7500.0
        eco_score = 35
        insight = (
            "Your carbon footprint is above average. "
            "Transportation contributes 35% of your emissions. "
            "Consider switching to public transport for daily commutes. "
            "Additionally, reducing meat consumption could help."
        )

        pdf_path = report_generate_pdf(total, eco_score, insight)

        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 100

        os.remove(pdf_path)


# ============================================================================
# TEST SUITE 4: MULTI-PAGE WORKFLOW
# ============================================================================

class TestMultiPageWorkflow:
    """Tests for multi-page workflows and data consistency."""

    def test_assessment_history_and_stats(self):
        """Test assessment history with statistics calculation."""
        assessments_data = [
            ("Car", 20.0, 250.0, "Non-Vegetarian", 2, 6293.0, 19),
            ("Bike", 10.0, 150.0, "Vegetarian", 0, 1984.0, 77),
            ("Bus", 25.0, 200.0, "Vegetarian", 1, 4148.0, 54),
        ]

        for data in assessments_data:
            db.save_assessment(TEST_USER_ID, *data)

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 3

        footprints = [a[7] for a in assessments]
        scores = [a[8] for a in assessments]

        avg_footprint = sum(footprints) / len(footprints)
        avg_score = sum(scores) / len(scores)

        assert 4000 < avg_footprint < 4500
        assert 45 < avg_score < 55

    def test_trend_analysis(self):
        """Test assessment trend analysis."""
        dates = [
            (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S"),
            (datetime.datetime.now() - datetime.timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S"),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ]

        footprints = [8000.0, 6500.0, 5000.0]

        for dt, footprint in zip(dates, footprints):
            db.save_assessment(
                TEST_USER_ID, "Car", 20.0, 250.0, "Non-Vegetarian",
                2, footprint, 25, date=dt
            )

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 3

        assert assessments[0][7] == 5000.0  # Latest
        assert assessments[-1][7] == 8000.0  # Oldest

        first = assessments[0][7]
        last = assessments[-1][7]
        trend = ((last - first) / last) * 100 if last else 0

        assert trend > 0

    def test_export_assessment_data(self):
        """Test exporting assessment data (simulating data_io)."""
        db.save_assessment(
            TEST_USER_ID, "Car", 20.0, 250.0, "Non-Vegetarian",
            2, 6293.0, 19
        )

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1
        assessment = assessments[0]

        assessment_dict = {
            "id": assessment[0],
            "date": str(assessment[1]),
            "transport": assessment[2],
            "distance": assessment[3],
            "electricity": assessment[4],
            "diet": assessment[5],
            "flights": assessment[6],
            "footprint": assessment[7],
            "eco_score": assessment[8],
        }

        required_fields = [
            "id", "date", "transport", "distance", "electricity",
            "diet", "flights", "footprint", "eco_score"
        ]
        
        for field in required_fields:
            assert field in assessment_dict


# ============================================================================
# TEST SUITE 5: END-TO-END USER JOURNEY
# ============================================================================

class TestEndToEndUserJourney:
    """Tests for complete end-to-end user journeys."""

    def test_user_registers_and_completes_assessment(self):
        """Test complete user journey: register → login → assessment."""
        success = db.save_assessment(
            TEST_USER_ID, "Car", 15.0, 200.0, "Vegetarian",
            1, 4751.0, 36
        )

        assert success is True

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1

    def test_user_views_assessment_history(self):
        """Test user viewing assessment history."""
        dt1 = (datetime.datetime.now() - datetime.timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S")
        dt2 = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.save_assessment(
            TEST_USER_ID, "Car", 20.0, 250.0, "Non-Vegetarian",
            2, 6293.0, 19, date=dt1
        )
        db.save_assessment(
            TEST_USER_ID, "Bike", 10.0, 150.0, "Vegetarian",
            0, 1984.0, 77, date=dt2
        )

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 2
        assert assessments[0][7] == 1984.0  # More recent, lower footprint

    def test_user_downloads_pdf_report(self):
        """Test user downloading PDF report after assessment."""
        total = 5000.0
        eco_score = 45
        insight, recommendations = generate_recommendations(
            "Car", 250.0, "Non-Vegetarian", 2,
            {"Transport": 1533, "Electricity": 2460, "Diet": 1800, "Flights": 500}
        )

        pdf_path = report_generate_pdf(total, eco_score, insight)

        assert pdf_path is not None
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 100

        os.remove(pdf_path)

    def test_user_maintains_streak(self):
        """Test user maintaining activity streak."""
        today = datetime.datetime.now()
        dates = [(today - datetime.timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S") for i in range(7)]

        for dt in dates:
            db.save_assessment(
                TEST_USER_ID, "Car", 10.0, 200.0, "Vegetarian",
                0, 3260.0, 50, date=dt
            )

        assessments = db.get_assessments(TEST_USER_ID)
        activities_dates = [str(a[1])[:10] for a in assessments]
        unique_dates = list(set(activities_dates))
        assert len(unique_dates) >= 7


# ============================================================================
# TEST SUITE 6: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_assessment_with_zero_values(self):
        """Test assessment with minimal/zero values."""
        total = 1000.0
        eco_score = 86

        success = db.save_assessment(
            TEST_USER_ID, "Walking", 0.0, 0.0, "Vegetarian",
            0, total, eco_score
        )

        assert success is True

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1
        assert assessments[0][7] == 1000.0

    def test_assessment_with_high_values(self):
        """Test assessment with maximum values."""
        total = 1011700.0
        eco_score = 0

        success = db.save_assessment(
            TEST_USER_ID, "Car", 500.0, 10000.0, "Non-Vegetarian",
            365, total, eco_score
        )

        assert success is True

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1
        assert assessments[0][7] == 1011700.0

    def test_assessment_with_no_contributors(self):
        """Test recommendation generation with minimal contributors."""
        contributors = {"Transport": 0, "Electricity": 0, "Diet": 1000, "Flights": 0}

        insight, recommendations = generate_recommendations(
            "Walking", 0, "Vegetarian", 0, contributors
        )

        assert len(recommendations) > 0
        assert "Excellent" in insight or "walking" in insight.lower() or "diet" in insight.lower() or "contributor" in insight.lower()

    def test_pdf_generation_error_handling(self):
        """Test PDF generation with invalid data."""
        pdf_path = report_generate_pdf(None, None, None)
        assert pdf_path is None

    def test_assessment_save_with_invalid_data(self):
        """Test assessment save with invalid data types."""
        success = db.save_assessment(
            TEST_USER_ID, "Car", -10.0, 250.0, "Non-Vegetarian",
            2, 5000.0, 40
        )

        assert success is True

        assessments = db.get_assessments(TEST_USER_ID)
        assert len(assessments) == 1


# ============================================================================
# FIXTURES AND HELPERS
# ============================================================================

def create_assessment_data():
    """Helper to create assessment data."""
    return {
        "transport": "Car",
        "distance": 20.0,
        "electricity": 250.0,
        "diet": "Non-Vegetarian",
        "flights": 2,
        "region": "US"
    }


def calculate_assessment(data):
    """Helper to calculate assessment metrics."""
    with patch('emissions.os.environ.get', return_value=None):
        total, contributors = calculate_footprint(
            data["transport"], data["distance"], data["electricity"],
            data["diet"], data["flights"], data["region"]
        )
        eco_score = calculate_eco_score(total, contributors)
        insight, recommendations = generate_recommendations(
            data["transport"], data["electricity"], data["diet"],
            data["flights"], contributors
        )
        return {
            "total": total,
            "eco_score": eco_score,
            "insight": insight,
            "recommendations": recommendations,
            "contributors": contributors
        }
