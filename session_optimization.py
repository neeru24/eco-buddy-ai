"""Session state optimization utilities for EcoBuddy AI."""

import streamlit as st
from typing import Any, Dict, Optional, List
import time
import logging
from session_manager import (
    get_user_session,
    get_session_value,
    set_session_value,
    delete_session_value,
    clear_session,
    get_session_stats,
    cleanup_old_sessions,
    lazy_session_property,
    SessionCache
)

logger = logging.getLogger(__name__)


def optimize_session_state():
    """Apply session state optimizations."""
    optimizer = get_user_session()
    
    # Remove duplicate entries
    _remove_duplicates(optimizer)
    
    # Compress large objects
    _compress_large_objects(optimizer)
    
    # Clean up old entries
    cleanup_old_sessions()
    
    logger.info("Session state optimization applied")


def _remove_duplicates(optimizer):
    """Remove duplicate session entries."""
    session = st.session_state
    seen_keys = set()
    duplicates = []
    
    for key in list(session.keys()):
        # Check for duplicate data patterns
        if key.endswith("_copy") or key.endswith("_duplicate"):
            duplicates.append(key)
        elif key.startswith("ecobuddy_"):
            base_key = key.replace("ecobuddy_", "")
            if base_key in seen_keys:
                duplicates.append(key)
            else:
                seen_keys.add(base_key)
    
    for key in duplicates:
        del session[key]
        optimizer.manager.delete(key)
    
    if duplicates:
        logger.info(f"Removed {len(duplicates)} duplicate session entries")


def _compress_large_objects(optimizer):
    """Compress large session objects."""
    session = st.session_state
    compressed_count = 0
    
    for key, value in list(session.items()):
        # Check if object is large
        size = _estimate_size(value)
        if size > 100000:  # > 100KB
            # Store compressed version
            if hasattr(value, "__dict__"):
                # Convert to dict if possible
                if not isinstance(value, dict):
                    session[key] = value.__dict__
                    compressed_count += 1
    
    if compressed_count:
        logger.info(f"Compressed {compressed_count} large session objects")


def _estimate_size(obj: Any) -> int:
    """Estimate object size in bytes."""
    try:
        import sys
        return sys.getsizeof(obj)
    except:
        return 0


def get_session_memory_usage() -> Dict[str, Any]:
    """Get memory usage of session state."""
    session = st.session_state
    total_size = 0
    items = []
    
    for key, value in session.items():
        size = _estimate_size(value)
        total_size += size
        items.append({
            "key": key,
            "size_bytes": size,
            "size_kb": round(size / 1024, 2)
        })
    
    return {
        "total_keys": len(session),
        "total_size_bytes": total_size,
        "total_size_kb": round(total_size / 1024, 2),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "items": sorted(items, key=lambda x: x["size_bytes"], reverse=True)
    }


def cache_session_value(ttl: int = 300):
    """Decorator to cache session values with TTL."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = f"cache_{func.__name__}"
            cache = get_session_value(cache_key)
            
            if cache is None:
                cache = SessionCache(ttl=ttl)
                set_session_value(cache_key, cache)
            
            # Generate key from args
            key = f"{args}_{kwargs}"
            value = cache.get(key)
            
            if value is not None:
                return value
            
            value = func(*args, **kwargs)
            cache.set(key, value)
            return value
        return wrapper
    return decorator


@lazy_session_property()
def get_application_state() -> Dict[str, Any]:
    """Lazy load application state."""
    return {
        "initialized": True,
        "version": "1.0.0",
        "last_activity": time.time()
    }


def get_user_preferences() -> Dict[str, Any]:
    """Get user preferences from session."""
    return get_session_value("user_preferences", {})


def set_user_preferences(preferences: Dict[str, Any]) -> None:
    """Set user preferences in session."""
    set_session_value("user_preferences", preferences, ttl=3600)


def get_cached_footprint() -> Optional[Dict[str, Any]]:
    """Get cached footprint data."""
    return get_session_value("cached_footprint")


def set_cached_footprint(data: Dict[str, Any]) -> None:
    """Set cached footprint data."""
    set_session_value("cached_footprint", data, ttl=300)


def clear_cached_footprint() -> None:
    """Clear cached footprint data."""
    delete_session_value("cached_footprint")


def get_cached_recommendations() -> Optional[List[Dict[str, Any]]]:
    """Get cached recommendations."""
    return get_session_value("cached_recommendations")


def set_cached_recommendations(recommendations: List[Dict[str, Any]]) -> None:
    """Set cached recommendations."""
    set_session_value("cached_recommendations", recommendations, ttl=300)


def clear_cached_recommendations() -> None:
    """Clear cached recommendations."""
    delete_session_value("cached_recommendations")


def get_widget_preferences() -> Dict[str, Any]:
    """Get widget preferences from session."""
    return get_session_value("widget_preferences", {})


def set_widget_preferences(preferences: Dict[str, Any]) -> None:
    """Set widget preferences in session."""
    set_session_value("widget_preferences", preferences, ttl=86400)


def get_assessment_history() -> List[Dict[str, Any]]:
    """Get assessment history from session."""
    return get_session_value("assessment_history", [])


def add_assessment_to_history(assessment: Dict[str, Any]) -> None:
    """Add assessment to session history."""
    history = get_assessment_history()
    history.append({
        **assessment,
        "timestamp": time.time()
    })
    # Keep only last 50 assessments
    if len(history) > 50:
        history = history[-50:]
    set_session_value("assessment_history", history)


def clear_assessment_history() -> None:
    """Clear assessment history."""
    delete_session_value("assessment_history")


def get_user_progress() -> Dict[str, Any]:
    """Get user progress from session."""
    return get_session_value("user_progress", {
        "assessments_completed": 0,
        "recommendations_followed": 0,
        "co2_saved": 0,
        "badges_earned": []
    })


def update_user_progress(update: Dict[str, Any]) -> None:
    """Update user progress in session."""
    progress = get_user_progress()
    progress.update(update)
    set_session_value("user_progress", progress)


def reset_user_progress() -> None:
    """Reset user progress."""
    delete_session_value("user_progress")


def get_temporary_data(key: str, default: Any = None) -> Any:
    """Get temporary data from session."""
    temp_data = get_session_value("temporary_data", {})
    return temp_data.get(key, default)


def set_temporary_data(key: str, value: Any) -> None:
    """Set temporary data in session."""
    temp_data = get_session_value("temporary_data", {})
    temp_data[key] = value
    set_session_value("temporary_data", temp_data, ttl=60)  # 1 minute TTL


def clear_temporary_data() -> None:
    """Clear all temporary data."""
    delete_session_value("temporary_data")