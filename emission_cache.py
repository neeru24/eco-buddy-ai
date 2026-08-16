"""Emission factor caching implementation for EcoBuddy AI."""

import time
import threading
from typing import Any, Optional, Callable, Dict, List
from functools import wraps
import logging
from cache_manager import get_emission_cache, EmissionFactor
from cache_metrics import (
    record_emission_cache_hit,
    record_emission_cache_miss,
    record_emission_cache_set,
    record_emission_cache_eviction,
    record_prevented_duplicate
)

logger = logging.getLogger(__name__)


def get_emission_factor_cached(factor_id: str, compute_func: Optional[Callable] = None) -> Optional[Any]:
    """Get an emission factor from cache or compute it."""
    cache = get_emission_cache()
    
    # Try cache first
    cached = cache.get("emission_factor", factor_id=factor_id)
    if cached is not None:
        record_emission_cache_hit("factor")
        return cached
    
    record_emission_cache_miss("factor")
    
    # Compute if function provided
    if compute_func:
        start_time = time.time()
        value = compute_func()
        computation_time = (time.time() - start_time) * 1000
        
        cache.set(value, "emission_factor", factor_id=factor_id)
        record_emission_cache_set("factor", computation_time)
        return value
    
    return None


def invalidate_emission_factor(factor_id: str) -> None:
    """Invalidate a specific emission factor in cache."""
    cache = get_emission_cache()
    cache.invalidate("emission_factor", factor_id=factor_id)
    logger.info(f"Invalidated emission factor: {factor_id}")


def clear_emission_cache() -> None:
    """Clear all emission factor cache."""
    cache = get_emission_cache()
    cache.invalidate()
    logger.info("Cleared all emission factor cache")


def get_emission_cache_stats() -> Dict[str, Any]:
    """Get emission factor cache statistics."""
    cache = get_emission_cache()
    return cache.get_stats()


def warm_emission_cache(factors: List[Dict[str, Any]]) -> None:
    """Warm the emission factor cache with a list of factors."""
    cache = get_emission_cache()
    logger.info(f"Warming cache with {len(factors)} factors...")
    
    for factor in factors:
        factor_id = factor.get("factor_id")
        if factor_id:
            cache.set(factor, "emission_factor", factor_id=factor_id)
    
    logger.info("Cache warming complete")


def cached_emission_factor(ttl: Optional[int] = None):
    """Decorator for caching emission factor computations."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_emission_cache()
            factor_type = func.__name__
            
            # Build cache key from arguments
            cache_kwargs = {}
            if args:
                for i, arg in enumerate(args):
                    cache_kwargs[f"arg_{i}"] = str(arg)
            cache_kwargs.update(kwargs)
            
            start_time = time.time()
            
            # Try cache
            cached = cache.get(factor_type, **cache_kwargs)
            if cached is not None:
                record_emission_cache_hit("factor")
                return cached
            
            record_emission_cache_miss("factor")
            
            # Compute and cache
            value = func(*args, **kwargs)
            computation_time = (time.time() - start_time) * 1000
            
            cache.set(value, factor_type, ttl, **cache_kwargs)
            record_emission_cache_set("factor", computation_time)
            
            return value
        return wrapper
    return decorator


# Convenience function for calculating emissions with caching
def calculate_emission_cached(factor_id: str, quantity: float) -> float:
    """Calculate emission with caching."""
    cache = get_emission_cache()
    
    # Try cache
    cached = cache.get("emission_calculation", factor_id=factor_id, quantity=quantity)
    if cached is not None:
        record_emission_cache_hit("calculation")
        return cached
    
    record_emission_cache_miss("calculation")
    
    # Get factor
    factor = cache.get("emission_factor", factor_id=factor_id)
    if factor is None:
        raise ValueError(f"Emission factor not found: {factor_id}")
    
    # Calculate
    emission = quantity * factor["value"] if isinstance(factor, dict) else quantity * factor.value
    
    # Cache result
    cache.set(emission, "emission_calculation", factor_id=factor_id, quantity=quantity)
    record_emission_cache_set("calculation", 0.0)
    
    return emission


def get_factors_by_category_cached(category: str) -> List[Dict[str, Any]]:
    """Get factors by category with caching."""
    cache = get_emission_cache()
    
    # Try cache
    cached = cache.get("category_factors", category=category)
    if cached is not None:
        record_emission_cache_hit("category")
        return cached
    
    record_emission_cache_miss("category")
    return []