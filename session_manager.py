"""Optimized session state management for EcoBuddy AI."""

import streamlit as st
import time
import threading
import hashlib
import json
from typing import Any, Dict, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from collections import defaultdict
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure with metadata."""
    key: str
    value: Any
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    ttl: Optional[int] = None  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """Check if session data has expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed,
            "ttl": self.ttl
        }


class OptimizedSessionManager:
    """
    Optimized session state manager with:
    - Lazy loading
    - TTL support
    - Memory optimization
    - Access tracking
    - Automatic cleanup
    """
    
    def __init__(self, max_size: int = 100, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._data: Dict[str, SessionData] = {}
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._stop_cleanup = False
        self._start_cleanup_thread()
        self._session_id = None
        
    def _start_cleanup_thread(self):
        """Start background cleanup thread."""
        def cleanup_worker():
            while not self._stop_cleanup:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired()
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
        logger.debug("Session cleanup thread started")
    
    def _cleanup_expired(self):
        """Remove expired session data."""
        with self._lock:
            expired_keys = []
            for key, data in self._data.items():
                if data.is_expired():
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self._data[key]
                logger.debug(f"Removed expired session data: {key}")
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired session entries")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a consistent key from parts."""
        key_parts = [prefix]
        for arg in args:
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return ":".join(key_parts)
    
    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        with self._lock:
            if len(self._data) < self.max_size:
                return
            
            # Sort by last accessed time
            sorted_keys = sorted(
                self._data.keys(),
                key=lambda k: self._data[k].last_accessed
            )
            
            # Evict oldest 20%
            evict_count = max(1, int(self.max_size * 0.2))
            for key in sorted_keys[:evict_count]:
                del self._data[key]
                logger.debug(f"Evicted session data: {key}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from session with automatic expiration check."""
        with self._lock:
            if key in self._data:
                data = self._data[key]
                if not data.is_expired():
                    data.access_count += 1
                    data.last_accessed = time.time()
                    return data.value
                else:
                    del self._data[key]
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in session with optional TTL."""
        with self._lock:
            self._evict_if_needed()
            
            if key in self._data:
                data = self._data[key]
                data.value = value
                data.updated_at = time.time()
                data.ttl = ttl or self.default_ttl
                if data.ttl:
                    data.created_at = time.time()  # Reset TTL
            else:
                self._data[key] = SessionData(
                    key=key,
                    value=value,
                    ttl=ttl or self.default_ttl
                )
    
    def delete(self, key: str) -> bool:
        """Delete a session key."""
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all session data."""
        with self._lock:
            self._data.clear()
            logger.info("Cleared all session data")
    
    def get_or_set(self, key: str, compute_func: Callable, 
                   ttl: Optional[int] = None) -> Any:
        """Get value or compute and set if not exists."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = compute_func()
        self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self._lock:
            total = len(self._data)
            expired = sum(1 for d in self._data.values() if d.is_expired())
            total_access = sum(d.access_count for d in self._data.values())
            
            return {
                "total_keys": total,
                "expired_entries": expired,
                "active_entries": total - expired,
                "total_access_count": total_access,
                "max_size": self.max_size,
                "utilization": round((total / self.max_size) * 100, 1),
                "keys": list(self._data.keys())
            }
    
    def get_session_id(self) -> str:
        """Get or create session ID."""
        if self._session_id is None:
            import uuid
            self._session_id = str(uuid.uuid4())
        return self._session_id
    
    def stop(self):
        """Stop cleanup thread."""
        self._stop_cleanup = True
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)


class SessionStateOptimizer:
    """
    Optimized Streamlit session state wrapper with:
    - Automatic cleanup
    - Lazy loading
    - Memory optimization
    - Duplicate prevention
    """
    
    def __init__(self, app_prefix: str = "ecobuddy"):
        self.prefix = app_prefix
        self.manager = OptimizedSessionManager()
        self._initialized = False
        self._init_session()
    
    def _init_session(self):
        """Initialize session state if not already."""
        if not self._initialized:
            if "session_manager" not in st.session_state:
                st.session_state["session_manager"] = self.manager
            if "session_initialized" not in st.session_state:
                st.session_state["session_initialized"] = True
                st.session_state["session_id"] = self.manager.get_session_id()
            self._initialized = True
    
    def _get_key(self, key: str) -> str:
        """Get fully qualified session key."""
        return f"{self.prefix}_{key}"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from session state."""
        full_key = self._get_key(key)
        
        # Check if in Streamlit session state
        if full_key in st.session_state:
            return st.session_state[full_key]
        
        # Check in manager
        value = self.manager.get(full_key, default)
        if value is not None:
            st.session_state[full_key] = value
        
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in session state."""
        full_key = self._get_key(key)
        
        # Set in both places for consistency
        st.session_state[full_key] = value
        self.manager.set(full_key, value, ttl)
    
    def delete(self, key: str) -> None:
        """Delete a session key."""
        full_key = self._get_key(key)
        if full_key in st.session_state:
            del st.session_state[full_key]
        self.manager.delete(full_key)
    
    def clear(self) -> None:
        """Clear all session data for this app."""
        # Clear Streamlit session state
        keys_to_delete = [k for k in st.session_state.keys() 
                         if k.startswith(self.prefix)]
        for key in keys_to_delete:
            del st.session_state[key]
        
        # Clear manager
        self.manager.clear()
    
    def get_or_set(self, key: str, compute_func: Callable, 
                   ttl: Optional[int] = None) -> Any:
        """Get value or compute and set."""
        value = self.get(key)
        if value is not None:
            return value
        
        value = compute_func()
        self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        return self.manager.get_stats()


# Optimized session state getters for common data types

def get_user_session() -> SessionStateOptimizer:
    """Get the global session state optimizer."""
    if "session_optimizer" not in st.session_state:
        st.session_state["session_optimizer"] = SessionStateOptimizer()
    return st.session_state["session_optimizer"]


def get_session_value(key: str, default: Any = None) -> Any:
    """Get a session value using the optimizer."""
    optimizer = get_user_session()
    return optimizer.get(key, default)


def set_session_value(key: str, value: Any, ttl: Optional[int] = None) -> None:
    """Set a session value using the optimizer."""
    optimizer = get_user_session()
    optimizer.set(key, value, ttl)


def delete_session_value(key: str) -> None:
    """Delete a session value."""
    optimizer = get_user_session()
    optimizer.delete(key)


def clear_session() -> None:
    """Clear all session data."""
    optimizer = get_user_session()
    optimizer.clear()


def get_session_id() -> str:
    """Get current session ID."""
    optimizer = get_user_session()
    return optimizer.manager.get_session_id()


def is_session_initialized() -> bool:
    """Check if session is initialized."""
    return st.session_state.get("session_initialized", False)


@dataclass
class SessionCache:
    """Lightweight session cache for specific data types."""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamps: Dict[str, float] = field(default_factory=dict)
    ttl: int = 300  # 5 minutes default
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value if not expired."""
        if key in self.data:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.data[key]
            else:
                del self.data[key]
                del self.timestamps[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set cached value."""
        self.data[key] = value
        self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear all cached data."""
        self.data.clear()
        self.timestamps.clear()


# Lazy loading utilities

def lazy_session_property(ttl: Optional[int] = None):
    """Decorator for lazy-loading session properties."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = f"lazy_{func.__name__}"
            optimizer = get_user_session()
            
            value = optimizer.get(key)
            if value is not None:
                return value
            
            value = func(*args, **kwargs)
            optimizer.set(key, value, ttl)
            return value
        return wrapper
    return decorator


# Session cleanup utilities

def cleanup_old_sessions(max_age_hours: int = 24) -> Dict[str, Any]:
    """Clean up session data older than max_age_hours."""
    optimizer = get_user_session()
    manager = optimizer.manager
    
    with manager._lock:
        current_time = time.time()
        cutoff = max_age_hours * 3600
        
        old_keys = []
        for key, data in manager._data.items():
            age = current_time - data.created_at
            if age > cutoff:
                old_keys.append(key)
        
        for key in old_keys:
            del manager._data[key]
            # Also clean from Streamlit session state
            if key in st.session_state:
                del st.session_state[key]
        
        return {
            "cleaned": len(old_keys),
            "remaining": len(manager._data)
        }


def get_session_stats() -> Dict[str, Any]:
    """Get comprehensive session statistics."""
    optimizer = get_user_session()
    manager = optimizer.manager
    
    base_stats = manager.get_stats()
    
    # Add Streamlit session state info
    total_streamlit_keys = len(st.session_state)
    prefixed_keys = sum(1 for k in st.session_state.keys() 
                       if k.startswith("ecobuddy_"))
    
    return {
        **base_stats,
        "streamlit_total_keys": total_streamlit_keys,
        "streamlit_prefixed_keys": prefixed_keys,
        "session_id": manager.get_session_id()
    }


# Session data migration utilities

def migrate_session_data(old_prefix: str, new_prefix: str) -> Dict[str, Any]:
    """Migrate session data from one prefix to another."""
    optimizer = get_user_session()
    manager = optimizer.manager
    
    migrated = []
    with manager._lock:
        keys_to_migrate = [k for k in manager._data.keys() 
                          if k.startswith(old_prefix)]
        
        for old_key in keys_to_migrate:
            data = manager._data[old_key]
            new_key = old_key.replace(old_prefix, new_prefix)
            
            # Check if new key exists
            if new_key not in manager._data:
                # Move data
                manager._data[new_key] = data
                del manager._data[old_key]
                migrated.append(old_key)
                
                # Update Streamlit session state
                if old_key in st.session_state:
                    st.session_state[new_key] = st.session_state[old_key]
                    del st.session_state[old_key]
    
    return {
        "migrated": len(migrated),
        "keys": migrated
    }


# Context manager for session operations

class session_scope:
    """Context manager for session operations."""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.optimizer = get_user_session()
        self.manager = self.optimizer.manager
    
    def __enter__(self):
        """Enter session context."""
        if self.session_id:
            self._original_id = self.manager.get_session_id()
            # Use provided session ID
        return self.optimizer
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit session context."""
        pass