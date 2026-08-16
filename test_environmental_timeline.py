import sqlite3

import database
from environmental_timeline import (
    MilestoneDefinition,
    evaluate_milestones,
    sync_environmental_milestones,
)


def assessment(footprint=10.0, eco_score=50):
    return (1, "2026-07-29", "Car", 10, 100, "Veg", 0, footprint, eco_score)


def test_evaluate_milestones_supports_current_rules():
    rows = [assessment(4.5, 88) for _ in range(5)]
    types = {item["milestone_type"] for item in evaluate_milestones(rows)}
    assert types == {
        "first_assessment",
        "five_assessments",
        "eco_score_70",
        "eco_score_85",
        "footprint_under_5",
    }


def test_future_milestone_type_can_be_added_without_engine_changes():
    custom = MilestoneDefinition(
        "future_type",
        "Future",
        "Extensible",
        "🔮",
        lambda rows: bool(rows),
        lambda rows: {"count": len(rows)},
    )
    assert evaluate_milestones([assessment()], [custom]) == [
        {
            "milestone_type": "future_type",
            "title": "Future",
            "description": "Extensible",
            "icon": "🔮",
            "metadata": {"count": 1},
        }
    ]


def test_record_and_get_milestones_are_user_scoped(tmp_path, monkeypatch):
    db_path = tmp_path / "timeline.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    conn = sqlite3.connect(db_path)
    from migrations.migrate_v5 import migrate
    migrate(conn)
    conn.close()

    assert database.record_environmental_milestone(
        1, "first_assessment", "Journey Started", "Done"
    )
    assert not database.record_environmental_milestone(
        1, "first_assessment", "Journey Started", "Done"
    )
    assert database.record_environmental_milestone(
        2, "first_assessment", "Journey Started", "Done"
    )

    assert len(database.get_environmental_milestones(1)) == 1
    assert len(database.get_environmental_milestones(2)) == 1


def test_sync_only_reports_new_milestones(monkeypatch):
    monkeypatch.setattr(
        "environmental_timeline.get_assessments",
        lambda user_id: [assessment(4.0, 90)],
    )
    inserted = []

    def fake_record(**kwargs):
        inserted.append(kwargs["milestone_type"])
        return True

    monkeypatch.setattr(
        "environmental_timeline.record_environmental_milestone",
        fake_record,
    )
    count = sync_environmental_milestones(7)
    assert count == 4
    assert set(inserted) == {
        "first_assessment",
        "eco_score_70",
        "eco_score_85",
        "footprint_under_5",
    }


def test_init_and_seed_historical_events():
    """Verify initialization and seeding of historical environmental events."""
    assert database.init_historical_events_db() is True
    database.seed_historical_events()

    events = database.get_historical_events()
    assert len(events) >= 7
    titles = [e["title"] for e in events]
    assert "First Earth Day Founded" in titles
    assert "Paris Climate Agreement Adopted" in titles


def test_filter_and_search_historical_events():
    """Verify filtering by category and searching by keyword/year."""
    policy_events = database.get_historical_events(category="Policy & Treaties")
    assert len(policy_events) >= 4
    for e in policy_events:
        assert e["category"] == "Policy & Treaties"

    paris_search = database.get_historical_events(search_query="Paris")
    assert len(paris_search) == 1
    assert paris_search[0]["title"] == "Paris Climate Agreement Adopted"

    year_search = database.get_historical_events(search_query="1970")
    assert len(year_search) == 1
    assert year_search[0]["year"] == 1970


def test_add_historical_event():
    """Verify adding a custom historical climate milestone event."""
    import uuid
    unique_title = f"Global Plastics Treaty High-Level Summit {uuid.uuid4().hex[:6]}"
    success = database.add_historical_event(
        year=2025,
        title=unique_title,
        category="Policy & Treaties",
        description="Legally binding global treaty on plastic pollution finalized.",
        impact_summary="Targeted 80% reduction in global ocean plastic leakage.",
        educational_resources="UN Environment Programme Plastics Brief",
        source_url="https://unep.org/plastics",
    )
    assert success is True

    fetched = database.get_historical_events(search_query=unique_title)
    assert len(fetched) == 1
    assert fetched[0]["year"] == 2025
    assert fetched[0]["title"] == unique_title
    assert "UN Environment Programme" in fetched[0]["educational_resources"]

