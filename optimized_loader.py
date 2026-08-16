import asyncio
import threading
import time
from functools import lru_cache
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import logging
from dataclasses import dataclass, field
from enum import Enum
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, Future
import weakref
from collections import defaultdict, deque
import hashlib
import pickle
import gc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LoadPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    LAZY = 4
    BACKGROUND = 5

@dataclass
class LoadTask:
    name: str
    priority: LoadPriority
    func: Callable
    args: tuple = ()
    kwargs: dict = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    max_retries: int = 3
    timeout: float = 30.0
    cache_result: bool = True
    cache_ttl: int = 3600
    loaded: bool = False
    result: Any = None
    error: Optional[Exception] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    retry_count: int = 0

class StartupOptimizer:
    def __init__(self, max_workers: int = 4, enable_async: bool = True):
        self.tasks: Dict[str, LoadTask] = {}
        self.loaded_tasks: Set[str] = set()
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.new_event_loop() if enable_async else None
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.futures: Dict[str, Future] = {}
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_deps: Dict[str, Set[str]] = defaultdict(set)
        self._shutdown_flag = False
        self._background_tasks: List[Future] = []
        self.stats = {
            "total_tasks": 0,
            "loaded_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0,
            "async_tasks": 0,
            "cached_hits": 0,
            "cached_misses": 0
        }
        self.lazy_registry: Dict[str, Callable] = {}
        self.proxies: Dict[str, Any] = {}
        self.initialization_lock = threading.RLock()
        
    def register_task(self, task: LoadTask) -> None:
        with self.initialization_lock:
            self.tasks[task.name] = task
            self.stats["total_tasks"] += 1
            for dep in task.dependencies:
                self.dependency_graph[dep].add(task.name)
                self.reverse_deps[task.name].add(dep)
            logger.debug(f"Registered task: {task.name} (priority: {task.priority.value})")

    def register_lazy(self, name: str, loader: Callable) -> None:
        self.lazy_registry[name] = loader
        logger.debug(f"Registered lazy component: {name}")

    def get_proxy(self, name: str) -> Any:
        if name not in self.proxies:
            self.proxies[name] = LazyProxy(lambda: self.load_lazy(name))
        return self.proxies[name]

    def load_lazy(self, name: str) -> Any:
        if name in self.lazy_registry:
            logger.info(f"Loading lazy component: {name}")
            result = self.lazy_registry[name]()
            self.lazy_registry[name] = None
            return result
        raise KeyError(f"No lazy component registered: {name}")

    def topological_sort(self) -> List[str]:
        visited = set()
        temp_visited = set()
        order = []
        
        def dfs(task_name: str) -> None:
            if task_name in temp_visited:
                raise RuntimeError(f"Circular dependency detected: {task_name}")
            if task_name in visited:
                return
            
            temp_visited.add(task_name)
            for dep in self.reverse_deps.get(task_name, set()):
                if dep in self.tasks:
                    dfs(dep)
            temp_visited.remove(task_name)
            visited.add(task_name)
            order.append(task_name)
        
        for task_name in self.tasks:
            if task_name not in visited:
                dfs(task_name)
        
        return order

    def _execute_task(self, task: LoadTask) -> Any:
        task.start_time = time.time()
        
        if task.cache_result and task.name in self.cache:
            cached_result, cached_time = self.cache[task.name]
            if time.time() - cached_time < task.cache_ttl:
                self.stats["cached_hits"] += 1
                task.result = cached_result
                task.loaded = True
                task.end_time = time.time()
                self.loaded_tasks.add(task.name)
                self.stats["loaded_tasks"] += 1
                return cached_result
        
        self.stats["cached_misses"] += 1
        attempt = 0
        while attempt < task.max_retries:
            try:
                if asyncio.iscoroutinefunction(task.func):
                    if self.loop is None:
                        result = asyncio.run(task.func(*task.args, **task.kwargs))
                    else:
                        result = self.loop.run_until_complete(
                            asyncio.wait_for(
                                task.func(*task.args, **task.kwargs),
                                timeout=task.timeout
                            )
                        )
                    self.stats["async_tasks"] += 1
                else:
                    result = task.func(*task.args, **task.kwargs)
                
                task.result = result
                task.loaded = True
                task.end_time = time.time()
                self.loaded_tasks.add(task.name)
                self.stats["loaded_tasks"] += 1
                
                if task.cache_result:
                    self.cache[task.name] = (result, time.time())
                
                return result
                
            except Exception as e:
                task.retry_count = attempt + 1
                logger.warning(f"Task '{task.name}' failed (attempt {attempt+1}/{task.max_retries}): {e}")
                if attempt == task.max_retries - 1:
                    task.error = e
                    task.end_time = time.time()
                    self.stats["failed_tasks"] += 1
                    raise
                time.sleep(2 ** attempt)
                attempt += 1

    def load_critical_tasks(self) -> None:
        logger.info("Loading critical tasks...")
        critical_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.CRITICAL]
        
        task_order = self.topological_sort()
        critical_order = [name for name in task_order if name in {t.name for t in critical_tasks}]
        
        for task_name in critical_order:
            task = self.tasks[task_name]
            if task_name in self.loaded_tasks:
                continue
            try:
                self._execute_task(task)
            except Exception as e:
                logger.error(f"Critical task '{task_name}' failed: {e}")
                raise

    def load_high_priority_tasks(self) -> None:
        logger.info("Loading high priority tasks...")
        high_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.HIGH 
                     and t.name not in self.loaded_tasks]
        
        if not high_tasks:
            return
            
        task_order = self.topological_sort()
        high_order = [name for name in task_order if name in {t.name for t in high_tasks}]
        
        futures = []
        for task_name in high_order:
            task = self.tasks[task_name]
            if task_name in self.loaded_tasks:
                continue
            future = self.executor.submit(self._execute_task, task)
            futures.append(future)
            self.futures[task_name] = future
        
        for future in futures:
            try:
                future.result(timeout=60)
            except Exception as e:
                logger.error(f"High priority task failed: {e}")

    def load_medium_priority_tasks(self) -> None:
        logger.info("Loading medium priority tasks...")
        medium_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.MEDIUM 
                       and t.name not in self.loaded_tasks]
        
        if not medium_tasks:
            return
            
        task_order = self.topological_sort()
        medium_order = [name for name in task_order if name in {t.name for t in medium_tasks}]
        
        chunk_size = 3
        for i in range(0, len(medium_order), chunk_size):
            chunk = medium_order[i:i+chunk_size]
            futures = []
            for task_name in chunk:
                task = self.tasks[task_name]
                if task_name in self.loaded_tasks:
                    continue
                future = self.executor.submit(self._execute_task, task)
                futures.append(future)
                self.futures[task_name] = future
            
            for future in futures:
                try:
                    future.result(timeout=30)
                except Exception as e:
                    logger.error(f"Medium priority task failed: {e}")

    def schedule_low_priority_tasks(self) -> None:
        logger.info("Scheduling low priority tasks...")
        low_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.LOW 
                    and t.name not in self.loaded_tasks]
        
        if not low_tasks:
            return
            
        task_order = self.topological_sort()
        low_order = [name for name in task_order if name in {t.name for t in low_tasks}]
        
        def background_loader():
            time.sleep(2)
            for task_name in low_order:
                task = self.tasks[task_name]
                if task_name in self.loaded_tasks:
                    continue
                try:
                    self._execute_task(task)
                    logger.info(f"Low priority task '{task_name}' loaded in background")
                except Exception as e:
                    logger.error(f"Low priority task '{task_name}' failed: {e}")
        
        thread = threading.Thread(target=background_loader, daemon=True)
        thread.start()
        self._background_tasks.append(thread)

    def schedule_background_tasks(self) -> None:
        logger.info("Scheduling background tasks...")
        bg_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.BACKGROUND 
                   and t.name not in self.loaded_tasks]
        
        if not bg_tasks:
            return
            
        task_order = self.topological_sort()
        bg_order = [name for name in task_order if name in {t.name for t in bg_tasks}]
        
        def bg_loader():
            time.sleep(10)
            for task_name in bg_order:
                task = self.tasks[task_name]
                if task_name in self.loaded_tasks:
                    continue
                try:
                    self._execute_task(task)
                    logger.info(f"Background task '{task_name}' loaded")
                except Exception as e:
                    logger.error(f"Background task '{task_name}' failed: {e}")
        
        thread = threading.Thread(target=bg_loader, daemon=True)
        thread.start()
        self._background_tasks.append(thread)

    def load_lazy_tasks(self) -> None:
        logger.info("Configuring lazy tasks...")
        lazy_tasks = [t for t in self.tasks.values() if t.priority == LoadPriority.LAZY]
        
        for task in lazy_tasks:
            self.register_lazy(task.name, lambda t=task: self._execute_task(t))
            logger.info(f"Task '{task.name}' configured for lazy loading")

    def run_startup_optimization(self) -> None:
        start_time = time.time()
        logger.info("Starting optimized startup pipeline...")
        
        try:
            self.load_critical_tasks()
            self.load_high_priority_tasks()
            self.load_medium_priority_tasks()
            self.schedule_low_priority_tasks()
            self.schedule_background_tasks()
            self.load_lazy_tasks()
            
            self.stats["total_time"] = time.time() - start_time
            logger.info(f"Startup optimization completed in {self.stats['total_time']:.2f}s")
            logger.info(f"Tasks loaded: {self.stats['loaded_tasks']}/{self.stats['total_tasks']}")
            
        except Exception as e:
            logger.error(f"Startup optimization failed: {e}")
            raise
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        if not self._shutdown_flag:
            self._shutdown_flag = True
            if self.loop:
                self.loop.close()

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.stats,
            "pending_tasks": len(self.tasks) - len(self.loaded_tasks),
            "cache_size": len(self.cache),
            "background_tasks": len(self._background_tasks),
            "futures_pending": len(self.futures)
        }

    def wait_for_background_tasks(self, timeout: float = 30.0) -> None:
        deadline = time.time() + timeout
        for thread in self._background_tasks:
            if thread.is_alive():
                remaining = max(0, deadline - time.time())
                if remaining > 0:
                    thread.join(timeout=remaining)

class LazyProxy:
    def __init__(self, loader: Callable):
        self._loader = loader
        self._obj = None
        self._loaded = False
        self._lock = threading.Lock()

    def __getattr__(self, name):
        with self._lock:
            if not self._loaded:
                self._obj = self._loader()
                self._loaded = True
        return getattr(self._obj, name)

    def __call__(self, *args, **kwargs):
        with self._lock:
            if not self._loaded:
                self._obj = self._loader()
                self._loaded = True
        return self._obj(*args, **kwargs)

    def is_loaded(self) -> bool:
        return self._loaded