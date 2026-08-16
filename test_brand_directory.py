"""Unit tests for Sustainable Brand Directory functionality."""

from database import (
    init_brand_directory_db,
    seed_sustainable_brands,
    get_sustainable_brands,
    add_sustainable_brand,
)


def test_init_and_seed_brands():
    """Verify initialization and initial seeding of sustainable brands."""
    assert init_brand_directory_db() is True
    seed_sustainable_brands()
    brands = get_sustainable_brands()
    assert len(brands) >= 10
    names = [b["name"] for b in brands]
    assert "Patagonia" in names
    assert "Allbirds" in names
    assert "Fairphone" in names


def test_get_brands_filter_by_category():
    """Verify category filtering."""
    apparel_brands = get_sustainable_brands(category="Apparel & Footwear")
    assert len(apparel_brands) > 0
    for b in apparel_brands:
        assert b["category"] == "Apparel & Footwear"


def test_get_brands_filter_by_search_query():
    """Verify text search by name and keywords."""
    patagonia = get_sustainable_brands(search_query="Patagonia")
    assert len(patagonia) == 1
    assert patagonia[0]["name"] == "Patagonia"

    bcorp_brands = get_sustainable_brands(search_query="B Corp")
    assert len(bcorp_brands) >= 5


def test_add_sustainable_brand():
    """Verify adding a new brand entry."""
    import uuid
    unique_name = f"Test Eco Brand {uuid.uuid4().hex[:6]}"
    result = add_sustainable_brand(
        name=unique_name,
        category="Personal Care",
        sustainability_rating="A+",
        eco_score=99,
        certifications="B Corp, Organic",
        description="A test brand focused on plastic-free products.",
        website="https://testecobrand.com",
    )
    assert result is True

    fetched = get_sustainable_brands(search_query=unique_name)
    assert len(fetched) == 1
    assert fetched[0]["name"] == unique_name
    assert fetched[0]["eco_score"] == 99
    assert fetched[0]["sustainability_rating"] == "A+"

