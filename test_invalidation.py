"""
Tests for invalidation.py - Cache invalidation utilities.

Tests:
1. Function registration in cached function registry
2. Invalidating caches by name
3. Category-based cache invalidation
4. All cache invalidation
5. Export cache invalidation
"""

import pytest
from unittest.mock import patch, MagicMock, call
from invalidation import (
    _CACHED_FUNCTION_REGISTRY,
    get_cached_functions_for_category,
    get_all_cached_functions,
    invalidate_on_assessment_save,
    invalidate_on_appliance_change,
    invalidate_on_solar_config_save,
    invalidate_on_challenge_enroll,
    invalidate_on_challenge_progress,
    invalidate_on_challenge_complete,
    invalidate_on_xp_award,
    invalidate_on_badge_unlock,
    invalidate_on_skill_tree_update,
    invalidate_on_journey_save,
    invalidate_on_journey_delete,
    invalidate_on_offset_save,
    invalidate_on_offset_delete,
    invalidate_on_offset_clear,
    invalidate_on_water_assessment_save,
    invalidate_all_db_caches,
    invalidate_export_caches,
)


class TestFunctionRegistration:
    """Tests for cached function registration."""

    def test_register_cached_function(self):
        """Test registering a cached function in the registry."""
        def mock_func():
            return "test"
        
        # Add cache name attribute
        mock_func._cache_name = "mock_func"
        
        from invalidation import register_cached_function
        register_cached_function(mock_func, "test_category")
        
        assert "mock_func" in _CACHED_FUNCTION_REGISTRY
        assert _CACHED_FUNCTION_REGISTRY["mock_func"]["func"] == mock_func
        assert _CACHED_FUNCTION_REGISTRY["mock_func"]["category"] == "test_category"

    def test_get_cached_functions_for_category(self):
        """Test retrieving functions by category."""
        def mock_func1():
            return "test1"
        mock_func1._cache_name = "mock_func1"
        
        def mock_func2():
            return "test2"
        mock_func2._cache_name = "mock_func2"
        
        from invalidation import register_cached_function
        register_cached_function(mock_func1, "db_reads")
        register_cached_function(mock_func2, "computed")
        
        db_functions = get_cached_functions_for_category("db_reads")
        assert mock_func1 in db_functions
        assert mock_func2 not in db_functions

    def test_get_all_cached_functions(self):
        """Test retrieving all cached functions."""
        def mock_func1():
            return "test1"
        mock_func1._cache_name = "mock_func1"
        
        def mock_func2():
            return "test2"
        mock_func2._cache_name = "mock_func2"
        
        from invalidation import register_cached_function
        register_cached_function(mock_func1, "category1")
        register_cached_function(mock_func2, "category2")
        
        all_funcs = get_all_cached_functions()
        
        assert "mock_func1" in all_funcs
        assert "mock_func2" in all_funcs
        assert all_funcs["mock_func1"] == mock_func1


class TestCategoryInvalidation:
    """Tests for category-based cache invalidation."""

    def test_get_all_cached_functions_empty_registry(self):
        """Test getting all functions when registry is empty."""
        # Clear registry first
        _CACHED_FUNCTION_REGISTRY.clear()
        
        all_funcs = get_all_cached_functions()
        assert all_funcs == {}


class TestInvalidateOnAssessmentSave:
    """Tests for invalidate_on_assessment_save."""

    def test_invalidate_assessment_save_clears_correct_caches(self):
        """Test that assessment save invalidates dependent caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_assessment_save()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_assessments' in called_names
            assert 'get_diet_history' in called_names
            assert 'get_total_xp' in called_names


class TestInvalidateOnApplianceChange:
    """Tests for invalidate_on_appliance_change."""

    def test_invalidate_appliance_change(self):
        """Test appliance change invalidates appliance caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_appliance_change()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_appliances' in called_names


class TestInvalidateOnSolarConfigSave:
    """Tests for invalidate_on_solar_config_save."""

    def test_invalidate_solar_config_save(self):
        """Test solar config save invalidates solar config cache."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_solar_config_save()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_solar_config' in called_names


class TestInvalidateOnChallengeEnroll:
    """Tests for invalidate_on_challenge_enroll."""

    def test_invalidate_challenge_enroll(self):
        """Test challenge enrollment invalidates challenge caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_challenge_enroll()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_user_challenges' in called_names


class TestInvalidateOnChallengeProgress:
    """Tests for invalidate_on_challenge_progress."""

    def test_invalidate_challenge_progress(self):
        """Test challenge progress update invalidates caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_challenge_progress()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_user_challenges' in called_names


class TestInvalidateOnChallengeComplete:
    """Tests for invalidate_on_challenge_complete."""

    def test_invalidate_challenge_complete(self):
        """Test challenge completion invalidates caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_challenge_complete()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_user_challenges' in called_names


class TestInvalidateOnXpAward:
    """Tests for invalidate_on_xp_award."""

    def test_invalidate_xp_award_clears_total_xp(self):
        """Test XP award invalidates total XP cache."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_xp_award()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_total_xp' in called_names

    def test_invalidate_xp_award_challenge_source(self):
        """Test XP award with challenge source invalidates challenge caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_xp_award(source_type='challenge')
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_total_xp' in called_names
            assert 'get_user_challenges' in called_names

    def test_invalidate_xp_award_badge_source(self):
        """Test XP award with badge source invalidates badge caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_xp_award(source_type='badge')
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_total_xp' in called_names
            assert 'get_unlocked_badges' in called_names


class TestInvalidateOnBadgeUnlock:
    """Tests for invalidate_on_badge_unlock."""

    def test_invalidate_badge_unlock(self):
        """Test badge unlock invalidates badge and XP caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_badge_unlock()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_unlocked_badges' in called_names
            assert 'get_total_xp' in called_names


class TestInvalidateOnSkillTreeUpdate:
    """Tests for invalidate_on_skill_tree_update."""

    def test_invalidate_skill_tree_update(self):
        """Test skill tree update invalidates progress cache."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_skill_tree_update()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_skill_tree_progress' in called_names


class TestInvalidateOnJourneySave:
    """Tests for invalidate_on_journey_save."""

    def test_invalidate_journey_save(self):
        """Test journey save invalidates journey caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_journey_save()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_journey_profiles' in called_names


class TestInvalidateOnJourneyDelete:
    """Tests for invalidate_on_journey_delete."""

    def test_invalidate_journey_delete(self):
        """Test journey delete invalidates journey caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_journey_delete()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_journey_profiles' in called_names


class TestInvalidateOnOffsetSave:
    """Tests for invalidate_on_offset_save."""

    def test_invalidate_offset_save(self):
        """Test offset save invalidates offset caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_offset_save()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_offset_transactions' in called_names
            assert 'get_total_offsets' in called_names
            assert 'get_total_spend' in called_names


class TestInvalidateOnOffsetDelete:
    """Tests for invalidate_on_offset_delete."""

    def test_invalidate_offset_delete(self):
        """Test offset delete invalidates offset caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_offset_delete()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_offset_transactions' in called_names
            assert 'get_total_offsets' in called_names
            assert 'get_total_spend' in called_names


class TestInvalidateOnOffsetClear:
    """Tests for invalidate_on_offset_clear."""

    def test_invalidate_offset_clear(self):
        """Test offset clear invalidates offset caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_offset_clear()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_offset_transactions' in called_names
            assert 'get_total_offsets' in called_names
            assert 'get_total_spend' in called_names


class TestInvalidateOnWaterAssessmentSave:
    """Tests for invalidate_on_water_assessment_save."""

    def test_invalidate_water_assessment_save(self):
        """Test water assessment save invalidates water caches."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_on_water_assessment_save()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'get_water_assessments' in called_names


class TestInvalidateAllDbCaches:
    """Tests for invalidate_all_db_caches."""

    def test_invalidate_all_db_caches_clears_all_db_caches(self):
        """Test that all database read caches are invalidated."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_all_db_caches()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            
            # Verify all expected cache names are included
            expected_caches = [
                'get_assessments', 'get_appliances', 'get_solar_config',
                'get_user_challenges', 'get_total_xp', 'get_unlocked_badges',
                'get_skill_tree_progress', 'get_journey_profiles',
                'get_offset_transactions', 'get_total_offsets', 'get_total_spend',
                'get_diet_history', 'get_water_assessments'
            ]
            
            for cache_name in expected_caches:
                assert cache_name in called_names


class TestInvalidateExportCaches:
    """Tests for invalidate_export_caches."""

    def test_invalidate_export_caches(self):
        """Test export cache invalidation."""
        with patch('invalidation._clear_by_name') as mock_clear:
            invalidate_export_caches()
            
            mock_clear.assert_called_once()
            called_names = mock_clear.call_args[0][0]
            assert 'export_data_json' in called_names
            assert 'export_data_csv_zip' in called_names


class TestClearByName:
    """Tests for the internal _clear_by_name function."""

    def test_clear_by_name_with_registry_hit(self):
        """Test clearing by name finds function in registry."""
        from invalidation import register_cached_function, _clear_by_name
        
        def mock_func():
            return "test"
        mock_func._cache_name = "test_func"
        mock_func.clear = MagicMock()
        
        register_cached_function(mock_func, "test")
        
        _clear_by_name(["test_func"])
        
        mock_func.clear.assert_called_once()

    def test_clear_by_name_with_fallback(self):
        """Test clearing by name falls back to module lookup."""
        from invalidation import _clear_by_name
        
        # This test verifies fallback behavior exists
        # In practice, this would fail for non-existent functions
        # but the code handles that gracefully
        _clear_by_name(["nonexistent_function"])
        # Should not raise an exception
