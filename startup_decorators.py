import functools
import time
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from .optimized_loader import StartupOptimizer, LoadPriority, LoadTask
import logging
import weakref
from contextlib import contextmanager
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

_global_optimizer: Optional[StartupOptimizer] = None
_optimizer_lock = threading.Lock()

def get_optimizer() -> StartupOptimizer:
    global _global_optimizer
    with _optimizer_lock:
        if _global_optimizer is None:
            _global_optimizer = StartupOptimizer(max_workers=4, enable_async=True)
        return _global_optimizer

def lazy_load(func: Callable) -> Callable:
    optimizer = get_optimizer()
    task_name = f"lazy_{func.__module__}.{func.__qualname__}"
    
    task = LoadTask(
        name=task_name,
        priority=LoadPriority.LAZY,
        func=func,
        cache_result=True,
        cache_ttl=3600
    )
    optimizer.register_task(task)
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        proxy = optimizer.get_proxy(task_name)
        return proxy(*args, **kwargs)
    
    return wrapper

def background_load(priority: Union[LoadPriority, str] = "low") -> Callable:
    if isinstance(priority, str):
        priority_map = {
            "critical": LoadPriority.CRITICAL,
            "high": LoadPriority.HIGH,
            "medium": LoadPriority.MEDIUM,
            "low": LoadPriority.LOW,
            "background": LoadPriority.BACKGROUND,
            "lazy": LoadPriority.LAZY
        }
        priority = priority_map.get(priority.lower(), LoadPriority.LOW)
    
    def decorator(func: Callable) -> Callable:
        optimizer = get_optimizer()
        task_name = f"bg_{func.__module__}.{func.__qualname__}"
        
        task = LoadTask(
            name=task_name,
            priority=priority,
            func=func,
            cache_result=True,
            cache_ttl=1800
        )
        optimizer.register_task(task)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if task_name in optimizer.loaded_tasks:
                return func(*args, **kwargs)
            
            if priority == LoadPriority.CRITICAL:
                return optimizer._execute_task(task)
            else:
                future = optimizer.executor.submit(optimizer._execute_task, task)
                return future
        
        return wrapper
    return decorator

def priority_load(priority: Union[LoadPriority, str] = "medium", dependencies: List[str] = None) -> Callable:
    if isinstance(priority, str):
        priority_map = {
            "critical": LoadPriority.CRITICAL,
            "high": LoadPriority.HIGH,
            "medium": LoadPriority.MEDIUM,
            "low": LoadPriority.LOW,
            "background": LoadPriority.BACKGROUND,
            "lazy": LoadPriority.LAZY
        }
        priority = priority_map.get(priority.lower(), LoadPriority.MEDIUM)
    
    dependencies = dependencies or []
    
    def decorator(func: Callable) -> Callable:
        optimizer = get_optimizer()
        task_name = f"{priority.name.lower()}_{func.__module__}.{func.__qualname__}"
        
        task = LoadTask(
            name=task_name,
            priority=priority,
            func=func,
            dependencies=dependencies,
            cache_result=True,
            cache_ttl=7200
        )
        optimizer.register_task(task)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if priority == LoadPriority.CRITICAL:
                if task_name not in optimizer.loaded_tasks:
                    optimizer._execute_task(task)
                return func(*args, **kwargs)
            
            if task_name not in optimizer.loaded_tasks:
                logger.warning(f"Function {func.__name__} not loaded yet, loading now...")
                optimizer._execute_task(task)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def cache_result(ttl: int = 3600) -> Callable:
    def decorator(func: Callable) -> Callable:
        cache = {}
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(kwargs.items()))
            
            with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if time.time() - timestamp < ttl:
                        logger.debug(f"Cache hit for {func.__name__}")
                        return result
            
            result = func(*args, **kwargs)
            
            with lock:
                cache[key] = (result, time.time())
                current_time = time.time()
                stale_keys = [k for k, (_, t) in cache.items() if current_time - t > ttl]
                for k in stale_keys:
                    del cache[k]
            
            return result
        
        return wrapper
    return decorator

def async_init(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if inspect.iscoroutinefunction(func):
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(func(*args, **kwargs))
            finally:
                loop.close()
        else:
            return func(*args, **kwargs)
    return wrapper

def throttled_load(max_calls: int = 10, per_second: int = 60) -> Callable:
    def decorator(func: Callable) -> Callable:
        calls = []
        lock = threading.Lock()
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                calls[:] = [c for c in calls if now - c < per_second]
                
                if len(calls) >= max_calls:
                    sleep_time = per_second - (now - calls[0]) + 0.1
                    logger.debug(f"Throttling {func.__name__}, sleeping {sleep_time:.2f}s")
                    time.sleep(max(0, sleep_time))
                
                calls.append(now)
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

def batch_load(batch_size: int = 5) -> Callable:
    def decorator(func: Callable) -> Callable:
        batch = []
        lock = threading.Lock()
        timer = None
        executor = ThreadPoolExecutor(max_workers=1)
        
        def process_batch():
            with lock:
                items = batch.copy()
                batch.clear()
            if items:
                try:
                    return func(items)
                except Exception as e:
                    logger.error(f"Batch processing failed: {e}")
                    return []
        
        @functools.wraps(func)
        def wrapper(item):
            with lock:
                batch.append(item)
                if len(batch) >= batch_size:
                    return process_batch()
                else:
                    if timer is None:
                        timer = threading.Timer(0.1, process_batch)
                        timer.daemon = True
                        timer.start()
            
            return None
        
        return wrapper
    return decorator

def preload(priority: Union[LoadPriority, str] = "medium") -> Callable:
    def decorator(func: Callable) -> Callable:
        optimizer = get_optimizer()
        task_name = f"preload_{func.__module__}.{func.__qualname__}"
        
        task = LoadTask(
            name=task_name,
            priority=priority if isinstance(priority, LoadPriority) else LoadPriority.MEDIUM,
            func=func,
            cache_result=True,
            cache_ttl=86400
        )
        optimizer.register_task(task)
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if task_name not in optimizer.loaded_tasks:
                logger.info(f"Preloading {func.__name__}...")
                optimizer._execute_task(task)
            return func(*args, **kwargs)
        
        return wrapper
    return decorator

@contextmanager
def startup_phase(name: str):
    logger.info(f"Starting startup phase: {name}")
    start_time = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Completed startup phase: {name} in {elapsed:.2f}s")

def measure_load_time(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"Load time for {func.__name__}: {elapsed:.4f}s")
        return result
    return wrapper

def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt+1}/{max_retries} for {func.__name__}")
                        time.sleep(delay * (2 ** attempt))
            raise last_exception
        return wrapper
    return decorator