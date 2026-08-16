"""Performance monitoring dashboard for EcoBuddy AI."""

import streamlit as st
import time
from typing import Dict, Any, Optional
import pandas as pd
from performance_monitor import (
    get_performance_monitor,
    get_performance_summary,
    get_performance_stats,
    get_slow_operations,
    get_error_rate,
    reset_performance_metrics,
    PerformanceMonitor
)
import logging

logger = logging.getLogger(__name__)


def render_performance_dashboard():
    """Render the performance monitoring dashboard."""
    st.title("⚡ Performance Monitoring Dashboard")
    
    monitor = get_performance_monitor()
    
    # Controls
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("📊 Reset Metrics", use_container_width=True):
            reset_performance_metrics()
            st.success("Metrics reset!")
    with col3:
        if st.button("📝 Enable Monitoring", use_container_width=True):
            monitor.enable()
            st.success("Monitoring enabled!")
    with col4:
        if st.button("⏹️ Disable Monitoring", use_container_width=True):
            monitor.disable()
            st.warning("Monitoring disabled!")
    
    st.divider()
    
    # Summary Statistics
    st.subheader("📈 Summary")
    summary = get_performance_summary()
    
    if summary["total_operations"] == 0:
        st.info("No performance metrics recorded yet. Run some operations to collect data.")
        return
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Operations", summary["total_operations"])
    col2.metric("Success Rate", f"{summary['success_rate']}%")
    col3.metric("Avg Duration", f"{summary['avg_duration_ms']}ms")
    col4.metric("Error Count", summary["error_count"])
    col5.metric("Slow Operations", summary["slow_operations"])
    
    st.divider()
    
    # Performance by Category
    st.subheader("📊 Performance by Operation")
    
    if summary["categories"]:
        df = pd.DataFrame([
            {
                "Operation": op,
                "Count": data["count"],
                "Avg (ms)": data["avg_ms"],
                "P95 (ms)": data["p95_ms"]
            }
            for op, data in summary["categories"].items()
        ])
        df = df.sort_values("Avg (ms)", ascending=False)
        st.dataframe(df, use_container_width=True)
        
        # Bar chart
        st.bar_chart(df.set_index("Operation")["Avg (ms)"])
    
    st.divider()
    
    # Slow Operations
    st.subheader("🐌 Slow Operations")
    slow_ops = get_slow_operations()
    
    if slow_ops:
        slow_df = pd.DataFrame(slow_ops)
        slow_df["timestamp"] = pd.to_datetime(slow_df["timestamp"], unit='s')
        slow_df = slow_df[["operation", "duration_ms", "timestamp", "success"]]
        slow_df = slow_df.sort_values("duration_ms", ascending=False)
        st.dataframe(slow_df, use_container_width=True)
    else:
        st.success("No slow operations detected!")
    
    st.divider()
    
    # Error Rate
    st.subheader("❌ Error Rate by Operation")
    error_rates = {}
    for op in summary.get("categories", {}):
        error_rates[op] = get_error_rate(op)
    
    if error_rates:
        error_df = pd.DataFrame([
            {"Operation": op, "Error Rate": f"{rate * 100:.1f}%"}
            for op, rate in error_rates.items()
            if rate > 0
        ])
        if not error_df.empty:
            st.dataframe(error_df, use_container_width=True)
        else:
            st.success("No errors detected!")
    
    st.divider()
    
    # Recent Metrics
    st.subheader("🕐 Recent Operations")
    recent = monitor.get_recent_metrics(limit=20)
    
    if recent:
        recent_df = pd.DataFrame(recent)
        recent_df["timestamp"] = pd.to_datetime(recent_df["timestamp"], unit='s')
        recent_df = recent_df[["operation", "duration_ms", "timestamp", "success"]]
        recent_df = recent_df.sort_values("timestamp", ascending=False)
        st.dataframe(recent_df, use_container_width=True)
    
    st.divider()
    
    # Settings
    st.subheader("⚙️ Settings")
    col1, col2 = st.columns(2)
    with col1:
        new_threshold = st.number_input(
            "Alert Threshold (ms)",
            value=monitor.alert_threshold_ms,
            min_value=100,
            max_value=30000,
            step=100
        )
        if new_threshold != monitor.alert_threshold_ms:
            monitor.alert_threshold_ms = new_threshold
            st.success(f"Threshold updated to {new_threshold}ms")
    
    with col2:
        new_max = st.number_input(
            "Max Samples",
            value=monitor.max_samples,
            min_value=100,
            max_value=10000,
            step=100
        )
        if new_max != monitor.max_samples:
            monitor.max_samples = new_max
            st.success(f"Max samples updated to {new_max}")


def render_performance_sidebar():
    """Render performance metrics in sidebar."""
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚡ Performance")
        
        summary = get_performance_summary()
        
        if summary["total_operations"] == 0:
            st.caption("No metrics yet")
            return
        
        col1, col2 = st.columns(2)
        col1.metric("Operations", summary["total_operations"])
        col2.metric("Avg Time", f"{summary['avg_duration_ms']}ms")
        
        col1, col2 = st.columns(2)
        col1.metric("Success Rate", f"{summary['success_rate']}%")
        col2.metric("Errors", summary["error_count"])
        
        if summary["slow_operations"] > 0:
            st.warning(f"⚠️ {summary['slow_operations']} slow operations")
        
        if st.button("📊 View Dashboard", use_container_width=True):
            st.session_state["show_performance"] = True


def render_performance_metrics_widget(operation: str, duration_ms: float, 
                                       success: bool = True) -> None:
    """Render a single performance metric widget."""
    status = "✅" if success else "❌"
    color = "normal"
    if duration_ms > 5000:
        color = "red"
    elif duration_ms > 2000:
        color = "orange"
    
    st.text(f"{status} {operation}: {duration_ms:.2f}ms")


# Integration helpers

def performance_monitor_app():
    """Render the full performance monitoring app."""
    st.set_page_config(
        page_title="Performance Dashboard",
        page_icon="⚡",
        layout="wide"
    )
    
    render_performance_dashboard()


# Alert callbacks

def send_alert_to_log(operation: str, duration_ms: float, 
                      metadata: Optional[Dict[str, Any]] = None) -> None:
    """Send alert to log."""
    logger.warning(
        f"Performance alert: {operation} took {duration_ms:.2f}ms"
    )


def send_alert_to_streamlit(operation: str, duration_ms: float, 
                            metadata: Optional[Dict[str, Any]] = None) -> None:
    """Send alert to Streamlit."""
    st.warning(f"⚠️ Performance alert: {operation} took {duration_ms:.2f}ms")


def setup_alerts():
    """Set up performance alerts."""
    monitor = get_performance_monitor()
    monitor.register_alert_callback(send_alert_to_log)
    monitor.register_alert_callback(send_alert_to_streamlit)


# Initialize monitoring
def init_performance_monitoring():
    """Initialize performance monitoring."""
    setup_alerts()
    logger.info("Performance monitoring initialized")


if __name__ == "__main__":
    performance_monitor_app()