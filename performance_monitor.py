"""Lightweight performance monitoring for EcoBuddy AI."""

import time
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from functools import wraps
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance metric data structure."""
    operation: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata
        }


class PerformanceMonitor:
    """
    Lightweight performance monitoring with:
    - Operation timing
    - Success/failure tracking
    - Statistical aggregation
    - Threshold alerts
    - Thread-safe
    """
    
    def __init__(self, max_samples: int = 1000, alert_threshold_ms: int = 5000):
        self.max_samples = max_samples
        self.alert_threshold_ms = alert_threshold_ms
        self._metrics: List[PerformanceMetric] = []
        self._aggregates: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._enabled = True
        self._alert_callbacks: List[Callable] = []
        
    def record(self, operation: str, duration_ms: float, 
               success: bool = True, error: Optional[str] = None,
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record a performance metric."""
        if not self._enabled:
            return
        
        metric = PerformanceMetric(
            operation=operation,
            duration_ms=duration_ms,
            success=success,
            error=error,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics.append(metric)
            if len(self._metrics) > self.max_samples:
                self._metrics.pop(0)
            
            self._update_aggregates(metric)
        
        # Check threshold alert
        if duration_ms > self.alert_threshold_ms:
            self._trigger_alert(operation, duration_ms, metadata)
    
    def _update_aggregates(self, metric: PerformanceMetric) -> None:
        """Update aggregate statistics."""
        op = metric.operation
        
        if op not in self._aggregates:
            self._aggregates[op] = {
                "count": 0,
                "total_ms": 0,
                "min_ms": float('inf'),
                "max_ms": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_ms": 0,
                "p50_ms": 0,
                "p90_ms": 0,
                "p95_ms": 0,
                "p99_ms": 0
            }
        
        agg = self._aggregates[op]
        agg["count"] += 1
        agg["total_ms"] += metric.duration_ms
        agg["min_ms"] = min(agg["min_ms"], metric.duration_ms)
        agg["max_ms"] = max(agg["max_ms"], metric.duration_ms)
        
        if metric.success:
            agg["success_count"] += 1
        else:
            agg["error_count"] += 1
        
        agg["avg_ms"] = agg["total_ms"] / agg["count"]
        
        # Calculate percentiles
        recent_metrics = [m for m in self._metrics if m.operation == op]
        if recent_metrics:
            durations = sorted([m.duration_ms for m in recent_metrics])
            agg["p50_ms"] = self._percentile(durations, 50)
            agg["p90_ms"] = self._percentile(durations, 90)
            agg["p95_ms"] = self._percentile(durations, 95)
            agg["p99_ms"] = self._percentile(durations, 99)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        index = int(len(data) * percentile / 100)
        return data[min(index, len(data) - 1)]
    
    def _trigger_alert(self, operation: str, duration_ms: float, 
                       metadata: Optional[Dict[str, Any]]) -> None:
        """Trigger alert for slow operation."""
        logger.warning(
            f"Performance alert: {operation} took {duration_ms:.2f}ms "
            f"(threshold: {self.alert_threshold_ms}ms)"
        )
        
        for callback in self._alert_callbacks:
            try:
                callback(operation, duration_ms, metadata)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")
    
    def register_alert_callback(self, callback: Callable) -> None:
        """Register a callback for performance alerts."""
        self._alert_callbacks.append(callback)
    
    def get_stats(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics."""
        with self._lock:
            if operation:
                return self._aggregates.get(operation, {})
            
            return self._aggregates
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent metrics."""
        with self._lock:
            return [m.to_dict() for m in self._metrics[-limit:]]
    
    def get_slow_operations(self, threshold_ms: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get operations that exceeded threshold."""
        threshold = threshold_ms or self.alert_threshold_ms
        with self._lock:
            slow = [m for m in self._metrics if m.duration_ms > threshold]
            return [m.to_dict() for m in slow]
    
    def get_error_rate(self, operation: Optional[str] = None) -> float:
        """Get error rate for operations."""
        with self._lock:
            if operation:
                agg = self._aggregates.get(operation)
                if not agg or agg["count"] == 0:
                    return 0
                return agg["error_count"] / agg["count"]
            
            total_count = sum(a["count"] for a in self._aggregates.values())
            total_errors = sum(a["error_count"] for a in self._aggregates.values())
            return total_errors / total_count if total_count > 0 else 0
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._aggregates.clear()
            logger.info("Performance monitor reset")
    
    def enable(self) -> None:
        """Enable monitoring."""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable monitoring."""
        self._enabled = False
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        with self._lock:
            total_ops = len(self._metrics)
            success_count = sum(1 for m in self._metrics if m.success)
            error_count = total_ops - success_count
            
            if total_ops == 0:
                return {
                    "total_operations": 0,
                    "success_rate": 0,
                    "avg_duration_ms": 0,
                    "slow_operations": 0,
                    "categories": {}
                }
            
            avg_duration = sum(m.duration_ms for m in self._metrics) / total_ops
            
            return {
                "total_operations": total_ops,
                "success_count": success_count,
                "error_count": error_count,
                "success_rate": round((success_count / total_ops) * 100, 1),
                "avg_duration_ms": round(avg_duration, 2),
                "slow_operations": len([m for m in self._metrics 
                                       if m.duration_ms > self.alert_threshold_ms]),
                "categories": {
                    op: {
                        "count": agg["count"],
                        "avg_ms": round(agg["avg_ms"], 2),
                        "p95_ms": round(agg["p95_ms"], 2)
                    }
                    for op, agg in self._aggregates.items()
                }
            }
    
    def export_to_json(self, file_path: str) -> None:
        """Export metrics to JSON file."""
        data = {
            "summary": self.get_summary(),
            "aggregates": self._aggregates,
            "recent_metrics": self.get_recent_metrics(limit=50)
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Exported performance metrics to {file_path}")


# Global monitor instance
_monitor = None
_monitor_lock = threading.Lock()


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _monitor
    with _monitor_lock:
        if _monitor is None:
            _monitor = PerformanceMonitor()
        return _monitor


def timed_operation(operation_name: str = None):
    """Decorator to time operations."""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            op_name = operation_name or func.__name__
            
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start_time) * 1000
                monitor.record(op_name, duration_ms, success=True)
                return result
            except Exception as e:
                duration_ms = (time.perf_counter() - start_time) * 1000
                monitor.record(op_name, duration_ms, success=False, error=str(e))
                raise
        return wrapper
    return decorator


class PerformanceContext:
    """Context manager for performance monitoring."""
    
    def __init__(self, operation: str, metadata: Optional[Dict[str, Any]] = None):
        self.operation = operation
        self.metadata = metadata or {}
        self.start_time = None
        self.monitor = get_performance_monitor()
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        success = exc_type is None
        error = str(exc_val) if exc_val else None
        self.monitor.record(self.operation, duration_ms, success, error, self.metadata)


# Convenience functions

def record_operation(operation: str, duration_ms: float, 
                     success: bool = True, error: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
    """Record an operation performance metric."""
    monitor = get_performance_monitor()
    monitor.record(operation, duration_ms, success, error, metadata)


def get_performance_stats(operation: Optional[str] = None) -> Dict[str, Any]:
    """Get performance statistics."""
    monitor = get_performance_monitor()
    return monitor.get_stats(operation)


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary."""
    monitor = get_performance_monitor()
    return monitor.get_summary()


def get_slow_operations(threshold_ms: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get slow operations."""
    monitor = get_performance_monitor()
    return monitor.get_slow_operations(threshold_ms)


def get_error_rate(operation: Optional[str] = None) -> float:
    """Get error rate."""
    monitor = get_performance_monitor()
    return monitor.get_error_rate(operation)


def reset_performance_metrics() -> None:
    """Reset all performance metrics."""
    monitor = get_performance_monitor()
    monitor.reset()


def disable_performance_monitoring() -> None:
    """Disable performance monitoring."""
    monitor = get_performance_monitor()
    monitor.disable()


def enable_performance_monitoring() -> None:
    """Enable performance monitoring."""
    monitor = get_performance_monitor()
    monitor.enable()