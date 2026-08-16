"""
Unit tests for Local Biodiversity Explorer (#352).
"""

import pytest
from local_biodiversity import (
    get_all_species,
    search_species,
    get_conservation_stats,
)


def test_get_all_species():
    species = get_all_species()
    assert len(species) >= 5
    assert "common_name" in species[0]
    assert "conservation_status" in species[0]


def test_search_species_keyword():
    results = search_species(query="Oak")
    assert len(results) >= 1
    assert "Oak" in results[0]["common_name"]


def test_search_species_filters():
    results = search_species(region="Asia", category="Wildlife & Mammals")
    assert len(results) >= 1
    assert "Red Panda" in results[0]["common_name"]


def test_get_conservation_stats():
    species = get_all_species()
    stats = get_conservation_stats(species)
    assert isinstance(stats, dict)
    assert "LC" in stats
    assert "EN" in stats
    assert stats["LC"] >= 1
