"""
Dependency-aware cache invalidation registry for EcoBuddy AI.

Maps write operations to the set of cached functions they should invalidate.
This replaces scattered `.clear()` calls with a centralized, maintainable registry.

Usage:
    from invalidation import invalidate_on_assessment_save, invalidate_all_db_caches

    # In database.py save_assessment():
    invalidate_on_assessment_save()

    # In data_io.py import_data_json():
    invalidate_all_db_caches()
"""

import streamlit as st

from collections.abc import Callable
from typing import Any

# Registry of all cached functions, populated by the @cached decorator
_CACHED_FUNCTION_REGISTRY = {}


def register_cached_function(func: Callable[..., Any], category: str) -> None:
    """
    Register a cached function in the global registry.

    Called automatically by the @cached decorator in cache.py.
    """
    name = getattr(func, '_cache_name', func.__qualname__)
    _CACHED_FUNCTION_REGISTRY[name] = {
        'func': func,
        'category': category,
    }


def get_cached_functions_for_category(category: str) -> list[Callable[..., Any]]:
    """
    Retrieve all cached functions registered under a given category.

    Args:
        category: The cache category string.

    Returns:
        List of cached function objects.
    """
    return [
        entry['func']
        for entry in _CACHED_FUNCTION_REGISTRY.values()
        if entry['category'] == category
    ]


def get_all_cached_functions() -> dict[str, Callable[..., Any]]:
    """
    Retrieve all registered cached functions.

    Returns:
        Dict of {name: func_object} for all registered cached functions.
    """
    return {name: entry['func'] for name, entry in _CACHED_FUNCTION_REGISTRY.items()}


# ---------------------------------------------------------------------------
# Write-operation invalidation helpers
# Each function maps a specific write operation to its dependent cache keys.
# ---------------------------------------------------------------------------

def invalidate_on_assessment_save() -> None:
    """Invalidate caches dependent on assessment writes."""
    _clear_by_name([
        'get_assessments',
        'get_diet_history',
        'get_total_xp',
    ])


def invalidate_on_assessment_undo() -> None:
    """Invalidate caches dependent on assessment undo or restore operations."""
    invalidate_on_assessment_save()



def invalidate_on_appliance_change() -> None:
    """Invalidate caches dependent on appliance add/delete."""
    _clear_by_name([
        'get_appliances',
    ])


def invalidate_on_solar_config_save() -> None:
    """Invalidate caches dependent on solar config changes."""
    _clear_by_name([
        'get_solar_config',
    ])


def invalidate_on_challenge_enroll() -> None:
    """Invalidate caches dependent on challenge enrollment."""
    _clear_by_name([
        'get_user_challenges',
    ])


def invalidate_on_challenge_progress() -> None:
    """Invalidate caches dependent on challenge progress update."""
    _clear_by_name([
        'get_user_challenges',
    ])


def invalidate_on_challenge_complete() -> None:
    """Invalidate caches dependent on challenge completion."""
    _clear_by_name([
        'get_user_challenges',
    ])


def invalidate_on_xp_award(source_type: str | None = None) -> None:
    """Invalidate caches dependent on XP award."""
    names = ['get_total_xp']
    if source_type == 'challenge':
        names.append('get_user_challenges')
    elif source_type == 'badge':
        names.append('get_unlocked_badges')
    _clear_by_name(names)


def invalidate_on_badge_unlock() -> None:
    """Invalidate caches dependent on badge unlock."""
    _clear_by_name([
        'get_unlocked_badges',
        'get_total_xp',
    ])


def invalidate_on_skill_tree_update() -> None:
    """Invalidate caches dependent on skill tree node update."""
    _clear_by_name([
        'get_skill_tree_progress',
    ])


def invalidate_on_journey_save() -> None:
    """Invalidate caches dependent on journey profile save."""
    _clear_by_name([
        'get_journey_profiles',
    ])


def invalidate_on_journey_delete() -> None:
    """Invalidate caches dependent on journey profile delete."""
    _clear_by_name([
        'get_journey_profiles',
    ])


def invalidate_on_offset_save() -> None:
    """Invalidate caches dependent on offset transaction save."""
    _clear_by_name([
        'get_offset_transactions',
        'get_total_offsets',
        'get_total_spend',
    ])


def invalidate_on_offset_delete() -> None:
    """Invalidate caches dependent on offset transaction delete."""
    _clear_by_name([
        'get_offset_transactions',
        'get_total_offsets',
        'get_total_spend',
    ])


def invalidate_on_offset_clear() -> None:
    """Invalidate caches dependent on clearing all offset transactions."""
    _clear_by_name([
        'get_offset_transactions',
        'get_total_offsets',
        'get_total_spend',
    ])


def invalidate_on_water_assessment_save() -> None:
    """Invalidate caches dependent on water assessment save."""
    _clear_by_name([
        'get_water_assessments',
    ])


def invalidate_on_freeze_token_change() -> None:
    """Invalidate caches dependent on freeze token or streak freeze changes."""
    _clear_by_name([
        'get_freeze_token_balance',
        'get_streak_freeze_dates',
        'get_total_freeze_tokens_earned',
    ])


def invalidate_on_reduction_goal_change() -> None:
    """Invalidate caches dependent on reduction goal create/archive/complete."""
    _clear_by_name([
        'get_active_goal',
        'get_goal_history',
    ])


def invalidate_on_time_capsule_change() -> None:
    """Invalidate caches dependent on time capsule operations."""
    _clear_by_name([
        'get_time_capsules',
    ])


def invalidate_all_db_caches() -> None:
    """
    Invalidate ALL database read caches.

    Used during bulk data import (data_io.import_data_json) where
    any table could have changed.
    """
    db_read_names = [
        'get_assessments',
        'get_appliances',
        'get_solar_config',
        'get_user_challenges',
        'get_total_xp',
        'get_unlocked_badges',
        'get_skill_tree_progress',
        'get_journey_profiles',
        'get_offset_transactions',
        'get_total_offsets',
        'get_total_spend',
        'get_diet_history',
        'get_water_assessments',
        'get_freeze_token_balance',
        'get_streak_freeze_dates',
        'get_total_freeze_tokens_earned',
        'get_active_goal',
        'get_goal_history',
        'get_time_capsules',
    ]
    _clear_by_name(db_read_names)


def invalidate_export_caches() -> None:
    """Invalidate export caches (used after data import)."""
    _clear_by_name([
        'export_data_json',
        'export_data_csv_zip',
    ])


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _clear_by_name(names: list[str]) -> None:
    """
    Clear cache for functions by their registered name.

    Falls back to trying module-level lookups if not in registry.
    """
    for name in names:
        # Try registry first
        if name in _CACHED_FUNCTION_REGISTRY:
            func = _CACHED_FUNCTION_REGISTRY[name]['func']
            if hasattr(func, 'clear'):
                func.clear()
            continue

        # Fallback: try to find in common modules
        for module_name in ['database', 'data_io']:
            try:
                import importlib
                module = importlib.import_module(module_name)
                func = getattr(module, name, None)
                if func and hasattr(func, 'clear'):
                    func.clear()
                    break
            except ImportError:
                pass
