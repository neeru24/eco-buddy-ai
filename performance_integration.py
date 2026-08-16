"""Performance monitoring integration with EcoBuddy AI components."""

import time
from typing import Dict, Any, Optional
from performance_monitor import (
    get_performance_monitor,
    timed_operation,
    PerformanceContext,
    record_operation
)
from performance_dashboard import render_performance_sidebar
import logging

logger = logging.getLogger(__name__)


# Integration with existing operations

def monitor_footprint_calculation():
    """Monitor footprint calculation operations."""
    return timed_operation("footprint_calculation")


def monitor_database_access():
    """Monitor database access operations."""
    return timed_operation("database_access")


def monitor_chart_preparation():
    """Monitor chart preparation operations."""
    return timed_operation("chart_preparation")


def monitor_report_generation():
    """Monitor report generation operations."""
    return timed_operation("report_generation")


def monitor_api_call():
    """Monitor API call operations."""
    return timed_operation("api_call")


def monitor_cache_operation():
    """Monitor cache operations."""
    return timed_operation("cache_operation")


def monitor_recommendation_generation():
    """Monitor recommendation generation."""
    return timed_operation("recommendation_generation")


# Specialized monitoring contexts

def monitor_operation(operation: str, metadata: Optional[Dict[str, Any]] = None):
    """Context manager for monitoring an operation."""
    return PerformanceContext(operation, metadata)


def monitor_db_query(query: str, params: Optional[Dict[str, Any]] = None):
    """Monitor a database query."""
    metadata = {"query": query[:100], "params": params}
    return PerformanceContext("database_query", metadata)


def monitor_api_request(endpoint: str, method: str = "GET"):
    """Monitor an API request."""
    metadata = {"endpoint": endpoint, "method": method}
    return PerformanceContext("api_request", metadata)


def monitor_computation(computation_type: str, size: Optional[int] = None):
    """Monitor a computation operation."""
    metadata = {"type": computation_type, "size": size}
    return PerformanceContext("computation", metadata)


def monitor_file_operation(operation: str, file_path: str):
    """Monitor a file operation."""
    metadata = {"operation": operation, "file": file_path}
    return PerformanceContext("file_operation", metadata)


# Integration with existing code

def integrate_with_app(app):
    """Integrate performance monitoring with the main app."""
    # Patch existing functions
    _patch_function(app, "calculate_footprint", "footprint_calculation")
    _patch_function(app, "get_assessments", "database_access")
    _patch_function(app, "generate_recommendations", "recommendation_generation")
    _patch_function(app, "prepare_chart", "chart_preparation")
    _patch_function(app, "generate_report", "report_generation")
    
    # Add sidebar metrics
    if hasattr(app, "add_sidebar"):
        app.add_sidebar(render_performance_sidebar)
    
    logger.info("Performance monitoring integrated with app")


def _patch_function(obj, func_name: str, operation: str):
    """Patch a function to add performance monitoring."""
    if hasattr(obj, func_name):
        original = getattr(obj, func_name)
        
        @timed_operation(operation)
        def patched(*args, **kwargs):
            return original(*args, **kwargs)
        
        setattr(obj, func_name, patched)
        logger.info(f"Patched {func_name} with performance monitoring")


# Performance report generation

def generate_performance_report() -> Dict[str, Any]:
    """Generate a comprehensive performance report."""
    monitor = get_performance_monitor()
    
    return {
        "timestamp": time.time(),
        "summary": monitor.get_summary(),
        "slow_operations": monitor.get_slow_operations(limit=10),
        "error_rate": monitor.get_error_rate(),
        "top_operations": monitor.get_stats()
    }


def print_performance_report():
    """Print a performance report to console."""
    report = generate_performance_report()
    
    print("=" * 60)
    print("PERFORMANCE MONITORING REPORT")
    print("=" * 60)
    
    summary = report["summary"]
    print(f"\nTotal Operations: {summary['total_operations']}")
    print(f"Success Rate: {summary['success_rate']}%")
    print(f"Average Duration: {summary['avg_duration_ms']}ms")
    print(f"Slow Operations: {summary['slow_operations']}")
    print(f"Errors: {summary['error_count']}")
    
    print("\n--- Top Operations ---")
    for op, data in summary.get("categories", {}).items():
        print(f"  {op}: {data['count']} ops, avg {data['avg_ms']}ms")
    
    print("\n--- Slow Operations ---")
    for op in report.get("slow_operations", [])[:5]:
        print(f"  {op['operation']}: {op['duration_ms']}ms")
    
    print("=" * 60)


def save_performance_report(file_path: str = "performance_report.json"):
    """Save performance report to JSON file."""
    monitor = get_performance_monitor()
    monitor.export_to_json(file_path)
    logger.info(f"Performance report saved to {file_path}")