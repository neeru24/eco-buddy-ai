import pytest
import eco_persona as ep


def _metrics(**overrides):
    metrics = dict(ep.EMPTY_METRICS)
    metrics.update(overrides)
    return metrics


# ─── Persona assignment ─────────────────────────────────────────────────────

def test_assign_persona_rookie_for_empty_user():
    assert ep.assign_persona(ep.EMPTY_METRICS) == "eco_rookie"


def test_assign_persona_explorer_with_low_activity():
    metrics = _metrics(assessment_count=1, total_xp=0)
    assert ep.assign_persona(metrics) == "earth_explorer"


def test_assign_persona_streak_star():
    metrics = _metrics(assessment_count=8, total_xp=400, streak=10)
    assert ep.assign_persona(metrics) == "streak_star"


def test_assign_persona_challenge_champion():
    metrics = _metrics(assessment_count=4, total_xp=600, completed_challenges=5)
    assert ep.assign_persona(metrics) == "challenge_champion"


def test_assign_persona_transport_titan():
    metrics = _metrics(
        assessment_count=4, assessments_with_transport=4,
        active_transport_ratio=0.75, total_xp=100,
    )
    assert ep.assign_persona(metrics) == "transport_titan"


def test_assign_persona_plant_powered_pal():
    metrics = _metrics(
        assessment_count=4, total_xp=100,
        plant_based_days=5, plant_based_ratio=0.85,
    )
    assert ep.assign_persona(metrics) == "plant_powered_pal"


def test_assign_persona_energy_mentor():
    metrics = _metrics(assessment_count=2, total_xp=50, has_energy_audit=True, appliance_count=4)
    assert ep.assign_persona(metrics) == "energy_mentor"


def test_assign_persona_carbon_crusader():
    metrics = _metrics(assessment_count=3, total_xp=100, total_offsets_tonnes=2.5, offset_count=1)
    assert ep.assign_persona(metrics) == "carbon_crusader"


def test_assign_persona_green_guardian():
    metrics = _metrics(assessment_count=5, total_xp=200, avg_eco_score=85, best_eco_score=92)
    assert ep.assign_persona(metrics) == "green_guardian"


def test_assign_persona_eco_legend_with_breadth():
    metrics = _metrics(
        assessment_count=6, total_xp=1200,
        streak=10, completed_challenges=4,
        plant_based_ratio=0.8, active_transport_ratio=0.6,
        has_energy_audit=True, water_assessment_count=2,
        waste_assessment_count=2, total_offsets_tonnes=1.0,
    )
    assert ep.assign_persona(metrics) == "eco_legend"


def test_assign_persona_is_always_valid():
    for i in range(1, 30):
        metrics = _metrics(
            assessment_count=i % 8, total_xp=i * 50,
            streak=i % 15, completed_challenges=i % 6,
            avg_eco_score=(i * 7) % 100,
        )
        persona_id = ep.assign_persona(metrics)
        assert persona_id in ep.PERSONAS


# ─── Rarity ─────────────────────────────────────────────────────────────────

def test_legendary_rarity_for_long_streak():
    metrics = _metrics(assessment_count=10, total_xp=500, streak=35)
    rarity = ep._persona_rarity("streak_star", metrics)
    assert rarity == "legendary"


def test_common_rarity_untouched_by_default():
    metrics = _metrics(assessment_count=2, total_xp=10, streak=2)
    assert ep._persona_rarity("streak_star", metrics) == "rare"


# ─── Profile content ────────────────────────────────────────────────────────

def test_strengths_never_empty():
    for metrics in (
        ep.EMPTY_METRICS,
        _metrics(assessment_count=1, total_xp=20),
        _metrics(assessment_count=6, total_xp=800, streak=10, completed_challenges=4),
    ):
        assert len(ep.get_strengths(metrics)) >= 1


def test_improvement_opportunities_never_empty():
    for metrics in (
        ep.EMPTY_METRICS,
        _metrics(assessment_count=3, total_xp=300, streak=40, plant_based_ratio=1.0,
                 has_energy_audit=True, water_assessment_count=2,
                 waste_assessment_count=2, total_offsets_tonnes=5.0,
                 active_transport_ratio=1.0, avg_electricity_kwh=80),
    ):
        assert len(ep.get_improvement_opportunities(metrics)) >= 1


def test_achievements_reflect_data():
    metrics = _metrics(streak=8, completed_challenges=3, best_eco_score=90)
    achievements = ep.get_achievements(metrics)
    assert any("8-day" in a for a in achievements)
    assert any("3 eco challenge" in a for a in achievements)
    assert any("90" in a for a in achievements)


def test_next_steps_never_empty():
    for persona_id in ep.PERSONAS:
        steps = ep.get_persona_next_steps(_metrics(assessment_count=2), persona_id)
        assert len(steps) >= 1


def test_generate_persona_profile_structure():
    profile = ep.generate_persona_profile(user_id=99999)
    for key in ("user_id", "persona", "persona_id", "metrics", "strengths",
                "improvement_opportunities", "achievements", "next_steps",
                "active_domains"):
        assert key in profile
    assert profile["persona_id"] in ep.PERSONAS
    assert profile["persona"]["name"] == ep.PERSONAS[profile["persona_id"]]["name"]


def test_all_personas_well_formed():
    for persona_id, persona in ep.PERSONAS.items():
        for field in ("name", "icon", "tagline", "description", "rarity", "color", "accent", "text_color", "focus"):
            assert persona_id in ep.PERSONAS
            assert persona[field] is not None, f"{persona_id}.{field} missing"
        assert len(persona["color"]) == 3
        assert len(persona["accent"]) == 3


# ─── Integration with a real database ───────────────────────────────────────

def test_analyze_user_behavior_with_db(monkeypatch, tmp_path):
    import os
    import sqlite3
    import database as db
    from invalidation import invalidate_all_db_caches

    test_db = str(tmp_path / "persona_test.db")
    original_db_name = db.DB_NAME
    db.DB_NAME = test_db
    # The @cached decorators wrap streamlit's session-wide cache, which can
    # hold stale reads from earlier tests pointing at other database files.
    invalidate_all_db_caches()

    try:
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                anonymous_leaderboard INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                transport TEXT,
                distance REAL,
                electricity REAL,
                diet TEXT,
                flights INTEGER,
                footprint REAL,
                eco_score INTEGER,
                trip_id TEXT
            )
        """)
        cursor.execute("""
            INSERT INTO assessments
                (user_id, date, transport, distance, electricity, diet, flights, footprint, eco_score)
            VALUES
                (1, '2026-07-20 10:00:00', 'Bike', 12.0, 120.0, 'Vegan', 0, 3400.0, 88),
                (1, '2026-07-21 10:00:00', 'Bike', 8.0, 110.0, 'Vegan', 0, 3200.0, 91)
        """)
        conn.commit()
        conn.close()

        metrics = ep.analyze_user_behavior(1)

        assert metrics["assessment_count"] == 2
        assert metrics["best_eco_score"] == 91
        assert metrics["avg_eco_score"] == 89.5
        assert metrics["active_transport_ratio"] == 1.0
        assert metrics["plant_based_days"] >= 1
        assert metrics["avg_electricity_kwh"] == 115.0

        profile = ep.generate_persona_profile(1)
        assert profile["persona_id"] in ("green_guardian", "transport_titan", "plant_powered_pal")
    finally:
        db.DB_NAME = original_db_name
        if os.path.exists(test_db):
            os.remove(test_db)
