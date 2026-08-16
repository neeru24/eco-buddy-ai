"""
Unit tests for AI Receipt Categorization (#349).
"""

import pytest
from receipt_categorization import (
    classify_product_name,
    parse_receipt_text,
    estimate_item_emissions,
    process_receipt,
    update_manual_corrections,
)


def test_classify_product_name():
    assert classify_product_name("Organic Milk") == "Dairy & Meat"
    assert classify_product_name("Fresh Spinach") == "Plant-based & Produce"
    assert classify_product_name("Unleaded Gasoline") == "Transport & Fuel"
    assert classify_product_name("Cotton T-Shirt") == "Apparel & Clothing"
    assert classify_product_name("Wireless Headphones") == "Electronics & Gadgets"


def test_parse_receipt_text():
    sample_text = "Organic Milk $4.99\nFresh Spinach $2.99"
    items = parse_receipt_text(sample_text)
    assert len(items) == 2
    assert items[0]["name"] == "Organic Milk"
    assert items[0]["price"] == 4.99
    assert items[0]["category"] == "Dairy & Meat"


def test_estimate_item_emissions():
    item = {"category": "Dairy & Meat", "price": 10.0, "quantity": 1}
    emissions = estimate_item_emissions(item)
    assert emissions == 12.0  # 10.0 * 1.20


def test_process_receipt():
    sample_text = "Organic Milk $10.00\nFresh Spinach $10.00"
    res = process_receipt(sample_text)
    assert res["total_price"] == 20.0
    assert len(res["items"]) == 2
    assert "category_breakdown" in res


def test_update_manual_corrections():
    items = [
        {"name": "Item 1", "price": 10.0, "quantity": 1, "category": "Dairy & Meat", "emissions": 12.0}
    ]
    updated = update_manual_corrections(items, 0, new_category="Plant-based & Produce", new_price=10.0)
    assert updated[0]["category"] == "Plant-based & Produce"
    assert updated[0]["emissions"] == 2.5  # 10.0 * 0.25
