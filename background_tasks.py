"""
Background Task Processing Module for EcoBuddy AI.

Provides asynchronous background execution for long-running operations
(OCR, LLM calls, PDF generation, large file parsing, bulk import/export)
using Python's concurrent.futures.ThreadPoolExecutor.

Ensures UI responsiveness in Streamlit without blocking execution flow,
maintaining thread safety, database isolation, and integration with
st.cache_data / cache.py optimizations.
"""

import time
import uuid
import logging
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable, Any, Dict, Optional, Tuple
import streamlit as st

logger = logging.getLogger(__name__)

# Dedicated thread pool for background tasks
# Limit max_workers to avoid thread exhaustion on lightweight servers
_THREAD_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="ecobuddy_bg_worker")


class TaskStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class BackgroundTask:
    """Tracks state and output for an asynchronous background task."""

    def __init__(self, task_id: str, name: str):
        self.task_id = task_id
        self.name = name
        self.status = TaskStatus.PENDING
        self.progress = 0.0
        self.message = "Initializing..."
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.future: Optional[Future] = None
        self._lock = threading.Lock()

    def update_progress(self, progress: float, message: str = ""):
        with self._lock:
            self.progress = max(0.0, min(1.0, progress))
            if message:
                self.message = message

    def set_completed(self, result: Any):
        with self._lock:
            self.status = TaskStatus.COMPLETED
            self.progress = 1.0
            self.message = "Completed successfully."
            self.result = result
            self.completed_at = time.time()

    def set_failed(self, error_msg: str):
        with self._lock:
            self.status = TaskStatus.FAILED
            self.message = f"Failed: {error_msg}"
            self.error = error_msg
            self.completed_at = time.time()


# Session/Global Task Registry
_GLOBAL_TASKS: Dict[str, BackgroundTask] = {}
_REGISTRY_LOCK = threading.Lock()


def get_task(task_key: str) -> Optional[BackgroundTask]:
    """Retrieve task object by key from session state or global registry."""
    if "bg_tasks" in st.session_state and task_key in st.session_state.bg_tasks:
        return st.session_state.bg_tasks[task_key]
    with _REGISTRY_LOCK:
        return _GLOBAL_TASKS.get(task_key)


import inspect


def _accepts_progress_callback(func: Callable[..., Any]) -> bool:
    """
    Safely inspects whether a callable accepts a 'progress_callback' argument.
    Compatible with normal functions, Streamlit CachedFunc wrappers, partials, and classes.
    """
    try:
        unwrapped = getattr(func, "__wrapped__", func)
        sig = inspect.signature(unwrapped)
        return "progress_callback" in sig.parameters
    except (ValueError, TypeError, AttributeError):
        return False


try:
    from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
except ImportError:
    add_script_run_ctx = None
    get_script_run_ctx = None


def submit_background_task(
    task_key: str,
    func: Callable[..., Any],
    *args,
    task_name: str = "Background Operation",
    **kwargs
) -> BackgroundTask:
    """
    Submits a function to execute asynchronously in the background thread pool.

    Args:
        task_key: Unique identifier for the task (used to track state across reruns).
        func: The function to execute.
        *args, **kwargs: Arguments passed to func.
        task_name: Human-readable description of the operation.

    Returns:
        BackgroundTask instance tracking progress and results.
    """

    # Ensure session state registry exists
    if "bg_tasks" not in st.session_state:
        st.session_state.bg_tasks = {}

    # If task already exists and is running/completed, return existing task
    existing_task = get_task(task_key)
    if existing_task and existing_task.status in [TaskStatus.RUNNING, TaskStatus.COMPLETED]:
        return existing_task

    # Create new task
    task = BackgroundTask(task_id=task_key, name=task_name)
    task.status = TaskStatus.RUNNING
    task.message = f"Executing {task_name}..."

    st.session_state.bg_tasks[task_key] = task
    with _REGISTRY_LOCK:
        _GLOBAL_TASKS[task_key] = task

    ctx = get_script_run_ctx() if get_script_run_ctx else None

    def _worker_wrapper():
        if ctx is not None and add_script_run_ctx is not None:
            try:
                add_script_run_ctx(threading.current_thread(), ctx)
            except Exception:
                pass
        try:
            # Safely pass progress callback if function accepts progress_callback
            if _accepts_progress_callback(func):
                kwargs["progress_callback"] = task.update_progress

            res = func(*args, **kwargs)
            task.set_completed(res)
        except Exception as exc:
            logger.exception(f"Background task {task_name} failed: {exc}")
            task.set_failed(str(exc))

    future = _THREAD_POOL.submit(_worker_wrapper)
    task.future = future
    return task


def clear_background_task(task_key: str):
    """Removes completed/failed task from registry."""
    if "bg_tasks" in st.session_state and task_key in st.session_state.bg_tasks:
        del st.session_state.bg_tasks[task_key]
    with _REGISTRY_LOCK:
        if task_key in _GLOBAL_TASKS:
            del _GLOBAL_TASKS[task_key]


def render_task_progress(
    task_key: str,
    success_msg: str = "Operation completed!",
    error_msg: str = "Operation failed."
) -> Tuple[bool, Any]:
    """
    Streamlit helper component that renders non-blocking status UI for a background task.

    Returns:
        Tuple of (is_completed: bool, result: Any)
    """
    task = get_task(task_key)
    if not task:
        return False, None

    if task.status == TaskStatus.RUNNING:
        st.info(f"⏳ **{task.name} in progress...** ({task.message})")
        st.progress(task.progress)
        # Small delay & trigger rerun to poll status cleanly
        time.sleep(0.3)
        st.rerun()
        return False, None

    elif task.status == TaskStatus.COMPLETED:
        st.success(f"✅ {success_msg}")
        return True, task.result

    elif task.status == TaskStatus.FAILED:
        st.error(f"❌ {error_msg}: {task.error}")
        return False, None

    return False, None
