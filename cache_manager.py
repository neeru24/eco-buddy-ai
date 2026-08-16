import time
import threading
import json
import hashlib
from typing import Any, Dict, Optional, Tuple, Callable
from functools import lru_cache, wraps
import logging
from collections import OrderedDict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class EmissionFactorCache:
    """Cache manager for emission factors with TTL and LRU eviction"""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 86400):
        """
        Initialize cache with max size and default TTL (24 hours)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.lock = threading.RLock()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size": 0,
            "total_entries": 0
        }
        self._cleanup_thread = None
        self._stop_cleanup = False
        self._start_cleanup_thread()
        
    def _start_cleanup_thread(self):
        """Start background thread for cache cleanup"""
        def cleanup_worker():
            while not self._stop_cleanup:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.info("Emission factor cache cleanup thread started")
    
    def _cleanup_expired(self):
        """Remove expired entries from cache"""
        with self.lock:
            current_time = time.time()
            expired_keys = []
            for key, (value, expiry) in self.cache.items():
                if expiry <= current_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.cache[key]
                self.stats["evictions"] += 1
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def _generate_key(self, factor_type: str, **kwargs) -> str:
        """Generate a unique cache key based on factor type and parameters"""
        key_data = {"type": factor_type, **kwargs}
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, factor_type: str, **kwargs) -> Optional[Any]:
        """Get cached emission factor"""
        key = self._generate_key(factor_type, **kwargs)
        
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if expiry > time.time():
                    # Move to end (LRU)
                    self.cache.move_to_end(key)
                    self.stats["hits"] += 1
                    logger.debug(f"Cache hit for {factor_type}: {kwargs}")
                    return value
                else:
                    # Expired
                    del self.cache[key]
                    self.stats["evictions"] += 1
            
            self.stats["misses"] += 1
            logger.debug(f"Cache miss for {factor_type}: {kwargs}")
            return None
    
    def set(self, value: Any, factor_type: str, ttl: Optional[int] = None, **kwargs):
        """Set emission factor in cache"""
        key = self._generate_key(factor_type, **kwargs)
        ttl = ttl or self.default_ttl
        expiry = time.time() + ttl
        
        with self.lock:
            # Check if key exists and update
            if key in self.cache:
                self.cache.move_to_end(key)
                self.cache[key] = (value, expiry)
                logger.debug(f"Updated cache entry for {factor_type}: {kwargs}")
                return
            
            # Evict oldest if cache is full
            if len(self.cache) >= self.max_size:
                oldest_key, _ = self.cache.popitem(last=False)
                self.stats["evictions"] += 1
                logger.debug(f"Evicted oldest entry: {oldest_key}")
            
            # Add new entry
            self.cache[key] = (value, expiry)
            self.stats["total_entries"] += 1
            self.stats["size"] = len(self.cache)
            logger.debug(f"Cached {factor_type}: {kwargs}")
    
    def get_or_compute(self, factor_type: str, compute_func: Callable, 
                      ttl: Optional[int] = None, **kwargs) -> Any:
        """Get from cache or compute if not present"""
        cached_value = self.get(factor_type, **kwargs)
        if cached_value is not None:
            return cached_value
        
        # Compute and cache
        value = compute_func(**kwargs)
        self.set(value, factor_type, ttl, **kwargs)
        return value
    
    def invalidate(self, factor_type: Optional[str] = None, **kwargs):
        """Invalidate cache entries"""
        with self.lock:
            if factor_type is None:
                # Clear all cache
                self.cache.clear()
                logger.info("Cleared entire cache")
                return
            
            key = self._generate_key(factor_type, **kwargs)
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Invalidated {factor_type}: {kwargs}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            hit_rate = 0
            total = self.stats["hits"] + self.stats["misses"]
            if total > 0:
                hit_rate = (self.stats["hits"] / total) * 100
            
            return {
                **self.stats,
                "hit_rate": f"{hit_rate:.2f}%",
                "current_size": len(self.cache),
                "ttl_seconds": self.default_ttl
            }
    
    def stop(self):
        """Stop cleanup thread"""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)


class EmissionFactor:
    """Emission factor data structure"""
    
    def __init__(self, factor_id: str, name: str, value: float, unit: str, 
                 category: str, source: str, year: int, region: str = "global"):
        self.factor_id = factor_id
        self.name = name
        self.value = value
        self.unit = unit
        self.category = category
        self.source = source
        self.year = year
        self.region = region
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "factor_id": self.factor_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "category": self.category,
            "source": self.source,
            "year": self.year,
            "region": self.region,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EmissionFactor":
        """Create from dictionary"""
        factor = cls(
            factor_id=data["factor_id"],
            name=data["name"],
            value=data["value"],
            unit=data["unit"],
            category=data["category"],
            source=data["source"],
            year=data["year"],
            region=data.get("region", "global")
        )
        if "created_at" in data:
            factor.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            factor.updated_at = datetime.fromisoformat(data["updated_at"])
        return factor


# Global cache instance
_emission_cache = None
_cache_lock = threading.Lock()

def get_emission_cache() -> EmissionFactorCache:
    """Get global emission factor cache instance"""
    global _emission_cache
    with _cache_lock:
        if _emission_cache is None:
            _emission_cache = EmissionFactorCache(max_size=2000, default_ttl=86400)
        return _emission_cache


def cached_emission_factor(ttl: Optional[int] = None):
    """Decorator for caching emission factor computations"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_emission_cache()
            # Extract factor type from function name
            factor_type = func.__name__
            
            # Use arguments as part of cache key
            cache_key_kwargs = {}
            if args:
                # Use position args as key components
                for i, arg in enumerate(args):
                    cache_key_kwargs[f"arg_{i}"] = str(arg)
            cache_key_kwargs.update(kwargs)
            
            return cache.get_or_compute(
                factor_type,
                lambda **kw: func(*args, **kw),
                ttl=ttl,
                **cache_key_kwargs
            )
        return wrapper
    return decorator