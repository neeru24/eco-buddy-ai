"""
Unit tests for Carbon Footprint Replay (#332).
"""

import pandas as pd
import pytest
from carbon_footprint_replay import (
    aggregate_historical_emissions,
    detect_milestones,
    export_replay_gif,
)


def test_aggregate_historical_emissions_default():
    df_weekly = aggregate_historical_emissions(user_id=1, period="weekly")
    assert isinstance(df_weekly, pd.DataFrame)
    assert not df_weekly.empty
    assert "footprint" in df_weekly.columns
    assert "eco_score" in df_weekly.columns
    assert "date_label" in df_weekly.columns


def test_aggregate_historical_emissions_monthly():
    df_monthly = aggregate_historical_emissions(user_id=1, period="monthly")
    assert isinstance(df_monthly, pd.DataFrame)
    assert not df_monthly.empty
    assert "period_key" in df_monthly.columns


def test_detect_milestones():
    data = [
        {"date_label": "Week 1", "footprint": 400.0, "eco_score": 60},
        {"date_label": "Week 2", "footprint": 200.0, "eco_score": 85},
        {"date_label": "Week 3", "footprint": 300.0, "eco_score": 75},
    ]
    df = pd.DataFrame(data)
    milestones = detect_milestones(df)
    
    assert len(milestones) >= 2
    titles = [m["title"] for m in milestones]
    assert any("All-Time Low" in t for t in titles)
    assert any("Peak Eco Score" in t for t in titles)
    assert any("Biggest Emission Cut" in t for t in titles)


def test_export_replay_gif():
    data = [
        {"date_label": "Week 1", "footprint": 400.0, "eco_score": 60},
        {"date_label": "Week 2", "footprint": 200.0, "eco_score": 85},
    ]
    df = pd.DataFrame(data)
    gif_bytes = export_replay_gif(df)
    
    assert isinstance(gif_bytes, bytes)
    assert len(gif_bytes) > 0
    # GIF header signature starts with GIF87a or GIF89a
    assert gif_bytes.startswith(b"GIF8")
