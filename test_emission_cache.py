import time
import logging
from emission_factors import get_emission_db, get_emission_factor, calculate_emission

logging.basicConfig(level=logging.INFO)

def test_cache_performance():
    """Test cache performance"""
    print("Testing emission factor cache performance...")
    
    db = get_emission_db()
    
    # Test 1: Get factor without cache (first time)
    print("\nTest 1: First retrieval (cache miss)")
    start = time.time()
    factor = get_emission_factor("ef_001")
    first_time = time.time() - start
    print(f"First retrieval: {first_time:.6f}s")
    
    # Test 2: Get factor with cache (second time)
    print("\nTest 2: Second retrieval (cache hit)")
    start = time.time()
    factor = get_emission_factor("ef_001")
    second_time = time.time() - start
    print(f"Second retrieval: {second_time:.6f}s")
    
    # Test 3: Calculate emissions
    print("\nTest 3: Calculate emissions")
    start = time.time()
    emission = calculate_emission("ef_001", 100)
    calc_time = time.time() - start
    print(f"Calculation time: {calc_time:.6f}s")
    print(f"Emissions for 100 kWh: {emission:.2f} kg CO2")
    
    # Test 4: Get category factors
    print("\nTest 4: Get factors by category")
    start = time.time()
    factors = db.get_factor_by_category("energy")
    category_time = time.time() - start
    print(f"Category retrieval: {category_time:.6f}s")
    print(f"Found {len(factors)} energy factors")
    
    # Test 5: Get cache stats
    print("\nTest 5: Cache statistics")
    stats = db.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Test 6: Calculate total emissions
    print("\nTest 6: Calculate total emissions for multiple items")
    items = [
        {"factor_id": "ef_001", "quantity": 100},  # Electricity
        {"factor_id": "ef_003", "quantity": 50},   # Gasoline
        {"factor_id": "ef_016", "quantity": 10},   # Beef
        {"factor_id": "ef_010", "quantity": 20},   # Plastic
    ]
    start = time.time()
    result = db.calculate_total_emissions(items)
    calc_total_time = time.time() - start
    print(f"Total calculation time: {calc_total_time:.6f}s")
    print(f"Total emissions: {result['total_emission']:.2f} kg CO2")
    print(f"Items processed: {result['item_count']}")
    
    print("\n✅ Cache test complete!")
    print(f"Performance improvement: {(first_time/second_time):.2f}x faster with cache")

def test_warm_cache():
    """Test cache warming"""
    print("\nTesting cache warming...")
    db = get_emission_db()
    
    # Get stats before warming
    stats_before = db.get_cache_stats()
    print(f"Cache size before warming: {stats_before['size']}")
    
    # Warm cache
    db.warm_cache()
    
    # Get stats after warming
    stats_after = db.get_cache_stats()
    print(f"Cache size after warming: {stats_after['size']}")
    print(f"Cache entries: {stats_after['total_entries']}")

if __name__ == "__main__":
    test_cache_performance()
    test_warm_cache()