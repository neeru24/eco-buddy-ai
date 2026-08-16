"""Unit tests for Open Environmental Data Explorer functionality."""

import json
from database import (
    init_environmental_datasets_db,
    seed_environmental_datasets,
    get_environmental_datasets,
    add_environmental_dataset,
)
from environmental_data_explorer import _parse_data_json, _slugify


def test_init_and_seed_datasets():
    """Verify initialization and seeding of environmental datasets."""
    assert init_environmental_datasets_db() is True
    seed_environmental_datasets()

    datasets = get_environmental_datasets()
    assert len(datasets) >= 5
    titles = [d["title"] for d in datasets]
    assert any("CO2 Concentration" in t for t in titles)


def test_filter_datasets_by_category_and_search():
    """Verify filtering by category and keyword search."""
    co2_ds = get_environmental_datasets(category="Global Carbon Emissions")
    assert len(co2_ds) >= 1
    assert co2_ds[0]["category"] == "Global Carbon Emissions"

    aqi_ds = get_environmental_datasets(search_query="Air Quality")
    assert len(aqi_ds) >= 1
    assert aqi_ds[0]["category"] == "Air Quality Index"


def test_add_environmental_dataset():
    """Verify adding a new open environmental dataset."""
    import uuid
    title = f"Global Plastic Waste Generation in Oceans {uuid.uuid4().hex[:6]}"
    data = {"headers": ["Year", "Metric_Tons"], "records": [[2020, 11.5], [2025, 14.2]]}
    success = add_environmental_dataset(
        title=title,
        category="Deforestation Rates",
        provider="Ocean Conservancy",
        license="CC-BY-4.0",
        update_frequency="Annual",
        description="Estimates of plastic waste entering oceans annually.",
        data_json=json.dumps(data),
    )
    assert success is True

    fetched = get_environmental_datasets(search_query=title)
    assert len(fetched) == 1
    parsed = _parse_data_json(fetched[0]["data_json"])
    assert parsed["headers"] == ["Year", "Metric_Tons"]
    assert parsed["records"][0] == [2020, 11.5]



def test_slugify_and_json_parsing():
    """Verify slugify helper and JSON parse helper."""
    assert _slugify("Global CO2 Levels (2025)!") == "global_co2_levels__2025"
    parsed = _parse_data_json('{"a": 1}')
    assert parsed == {"a": 1}
    assert _parse_data_json("invalid json") is None

