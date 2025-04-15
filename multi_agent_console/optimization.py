"""
Performance optimization module for MultiAgentConsole.

This module provides utilities for optimizing the performance of MultiAgentConsole,
including caching, memoization, and resource management.

Author: Sai Sunkara
"""

import time
import functools
import threading
import weakref
import gc
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, TypeVar, Union, cast

from multi_agent_console.monitoring import get_logger

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Set up logger
logger = get_logger(__name__)


class Cache:
    """
    A simple in-memory cache with LRU (Least Recently Used) eviction policy.
    """
    
    def __init__(self, max_size: int = 1000, ttl: Optional[float] = None):
        """
        Initialize the cache.
        
        Args:
            max_size: Maximum number of items to store in the cache
            ttl: Time-to-live in seconds (None for no expiration)
        """
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found or expired
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            value, timestamp = self.cache[key]
            current_time = time.time()
            
            # Check if the item has expired
            if self.ttl is not None and current_time - timestamp > self.ttl:
                del self.cache[key]
                del self.access_times[key]
                self.misses += 1
                return None
            
            # Update access time
            self.access_times[key] = current_time
            self.hits += 1
            
            return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            current_time = time.time()
            
            # Evict items if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                self._evict()
            
            # Store the value with timestamp
            self.cache[key] = (value, current_time)
            self.access_times[key] = current_time
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
        
        Returns:
            True if the key was found and deleted, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.access_times[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.hits = 0
            self.misses = 0
    
    def _evict(self) -> None:
        """Evict the least recently used item from the cache."""
        if not self.access_times:
            return
        
        # Find the least recently used key
        lru_key = min(self.access_times.items(), key=lambda x: x[1])[0]
        
        # Remove the item
        del self.cache[lru_key]
        del self.access_times[lru_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self.lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "hits": self.hits,
                "misses": self.misses,
                "hit_ratio": self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0
            }


# Global cache instance
_global_cache = Cache()


def get_cache() -> Cache:
    """
    Get the global cache instance.
    
    Returns:
        Global cache instance
    """
    return _global_cache


def cached(ttl: Optional[float] = None) -> Callable[[Callable[..., R]], Callable[..., R]]:
    """
    Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds (None for no expiration)
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            # Create a cache key from the function name and arguments
            key_parts = [func.__module__, func.__name__]
            
            # Add positional arguments
            for arg in args:
                key_parts.append(str(arg))
            
            # Add keyword arguments (sorted for consistency)
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            
            cache_key = ":".join(key_parts)
            
            # Try to get from cache
            cached_result = _global_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            _global_cache.set(cache_key, result)
            
            return result
        
        return wrapper
    
    return decorator


def memoize(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator for memoizing function results (caching for the lifetime of the program).
    
    Args:
        func: Function to memoize
    
    Returns:
        Decorated function
    """
    cache: Dict[Tuple, R] = {}
    
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        # Create a cache key from the arguments
        key = (args, tuple(sorted(kwargs.items())))
        
        # Try to get from cache
        if key in cache:
            return cache[key]
        
        # Call the function and cache the result
        result = func(*args, **kwargs)
        cache[key] = result
        
        return result
    
    # Add a clear_cache method to the wrapper
    def clear_cache() -> None:
        cache.clear()
    
    wrapper.clear_cache = clear_cache  # type: ignore
    
    return wrapper


class ResourceManager:
    """
    Resource manager for tracking and limiting resource usage.
    """
    
    def __init__(self, max_memory_mb: Optional[int] = None, max_cpu_percent: Optional[float] = None):
        """
        Initialize the resource manager.
        
        Args:
            max_memory_mb: Maximum memory usage in MB (None for no limit)
            max_cpu_percent: Maximum CPU usage in percent (None for no limit)
        """
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.resources: Dict[str, Any] = {}
        self.lock = threading.RLock()
        
        # Import psutil if available
        try:
            import psutil
            self.psutil = psutil
        except ImportError:
            self.psutil = None
            logger.warning("psutil not available, resource monitoring will be limited")
    
    def register_resource(self, name: str, resource: Any, cleanup_func: Optional[Callable[[Any], None]] = None) -> None:
        """
        Register a resource for tracking.
        
        Args:
            name: Resource name
            resource: Resource object
            cleanup_func: Function to call when cleaning up the resource
        """
        with self.lock:
            self.resources[name] = {
                "resource": resource,
                "cleanup_func": cleanup_func,
                "created_at": time.time()
            }
    
    def get_resource(self, name: str) -> Optional[Any]:
        """
        Get a registered resource.
        
        Args:
            name: Resource name
        
        Returns:
            Resource object or None if not found
        """
        with self.lock:
            if name in self.resources:
                return self.resources[name]["resource"]
            return None
    
    def release_resource(self, name: str) -> bool:
        """
        Release a resource.
        
        Args:
            name: Resource name
        
        Returns:
            True if the resource was found and released, False otherwise
        """
        with self.lock:
            if name in self.resources:
                resource_info = self.resources[name]
                
                # Call cleanup function if provided
                if resource_info["cleanup_func"] is not None:
                    try:
                        resource_info["cleanup_func"](resource_info["resource"])
                    except Exception as e:
                        logger.error(f"Error cleaning up resource {name}: {e}")
                
                del self.resources[name]
                return True
            return False
    
    def release_all_resources(self) -> None:
        """Release all registered resources."""
        with self.lock:
            for name in list(self.resources.keys()):
                self.release_resource(name)
    
    def check_memory_usage(self) -> Tuple[float, bool]:
        """
        Check current memory usage.
        
        Returns:
            Tuple of (memory_usage_mb, is_over_limit)
        """
        if self.psutil is None:
            return 0.0, False
        
        process = self.psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        is_over_limit = False
        if self.max_memory_mb is not None and memory_mb > self.max_memory_mb:
            is_over_limit = True
            logger.warning(f"Memory usage ({memory_mb:.2f} MB) exceeds limit ({self.max_memory_mb} MB)")
        
        return memory_mb, is_over_limit
    
    def check_cpu_usage(self) -> Tuple[float, bool]:
        """
        Check current CPU usage.
        
        Returns:
            Tuple of (cpu_percent, is_over_limit)
        """
        if self.psutil is None:
            return 0.0, False
        
        process = self.psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        
        is_over_limit = False
        if self.max_cpu_percent is not None and cpu_percent > self.max_cpu_percent:
            is_over_limit = True
            logger.warning(f"CPU usage ({cpu_percent:.2f}%) exceeds limit ({self.max_cpu_percent}%)")
        
        return cpu_percent, is_over_limit
    
    def optimize_memory(self) -> None:
        """Optimize memory usage by running garbage collection."""
        # Run garbage collection
        gc.collect()
        
        # Check memory usage after optimization
        memory_mb, is_over_limit = self.check_memory_usage()
        logger.info(f"Memory usage after optimization: {memory_mb:.2f} MB")


# Global resource manager instance
_resource_manager = ResourceManager()


def get_resource_manager() -> ResourceManager:
    """
    Get the global resource manager instance.
    
    Returns:
        Global resource manager instance
    """
    return _resource_manager


class LazyLoader:
    """
    Lazy loader for importing modules only when needed.
    """
    
    def __init__(self, module_name: str):
        """
        Initialize the lazy loader.
        
        Args:
            module_name: Name of the module to load
        """
        self.module_name = module_name
        self.module: Optional[Any] = None
    
    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute from the module, loading it if necessary.
        
        Args:
            name: Attribute name
        
        Returns:
            Attribute value
        
        Raises:
            AttributeError: If the attribute is not found
        """
        if self.module is None:
            self.module = __import__(self.module_name)
        
        return getattr(self.module, name)


def optimize_function(func: Callable[..., R]) -> Callable[..., R]:
    """
    Decorator for optimizing function execution.
    
    This decorator:
    1. Checks resource usage before and after function execution
    2. Logs execution time
    3. Runs garbage collection if memory usage is high
    
    Args:
        func: Function to optimize
    
    Returns:
        Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> R:
        # Check resource usage before execution
        resource_manager = get_resource_manager()
        memory_before, _ = resource_manager.check_memory_usage()
        
        # Record start time
        start_time = time.time()
        
        try:
            # Execute the function
            result = func(*args, **kwargs)
            
            # Record end time
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Check resource usage after execution
            memory_after, is_over_limit = resource_manager.check_memory_usage()
            memory_diff = memory_after - memory_before
            
            # Log execution time and memory usage
            logger.debug(
                f"Function {func.__name__} executed in {execution_time:.4f} seconds, "
                f"memory change: {memory_diff:.2f} MB"
            )
            
            # Optimize memory if usage is high
            if is_over_limit:
                logger.info(f"Optimizing memory after {func.__name__}")
                resource_manager.optimize_memory()
            
            return result
        except Exception as e:
            # Log error
            logger.error(f"Error in optimized function {func.__name__}: {e}")
            raise
    
    return wrapper


def batch_process(items: List[T], process_func: Callable[[T], R], batch_size: int = 10) -> List[R]:
    """
    Process items in batches to optimize memory usage.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        batch_size: Number of items to process in each batch
    
    Returns:
        List of processed items
    """
    results = []
    
    for i in range(0, len(items), batch_size):
        # Process a batch of items
        batch = items[i:i + batch_size]
        batch_results = [process_func(item) for item in batch]
        results.extend(batch_results)
        
        # Run garbage collection between batches
        gc.collect()
    
    return results


def parallel_process(items: List[T], process_func: Callable[[T], R], max_workers: int = 4) -> List[R]:
    """
    Process items in parallel to optimize CPU usage.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        max_workers: Maximum number of worker threads
    
    Returns:
        List of processed items
    """
    from concurrent.futures import ThreadPoolExecutor
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_func, items))
    
    return results


def optimize_imports() -> None:
    """
    Optimize imports by using lazy loading for heavy modules.
    
    This function replaces heavy imports with lazy loaders.
    """
    import sys
    
    # List of modules to lazy load
    lazy_modules = [
        "numpy",
        "pandas",
        "matplotlib",
        "tensorflow",
        "torch",
        "sklearn"
    ]
    
    # Replace modules with lazy loaders
    for module_name in lazy_modules:
        if module_name in sys.modules:
            continue
        
        sys.modules[module_name] = LazyLoader(module_name)
        logger.debug(f"Lazy loaded module: {module_name}")


def setup_optimization(
    max_cache_size: int = 1000,
    cache_ttl: Optional[float] = None,
    max_memory_mb: Optional[int] = None,
    max_cpu_percent: Optional[float] = None,
    lazy_loading: bool = True
) -> None:
    """
    Set up optimization features.
    
    Args:
        max_cache_size: Maximum number of items in the cache
        cache_ttl: Time-to-live for cached items in seconds
        max_memory_mb: Maximum memory usage in MB
        max_cpu_percent: Maximum CPU usage in percent
        lazy_loading: Whether to use lazy loading for heavy modules
    """
    global _global_cache, _resource_manager
    
    # Configure cache
    _global_cache = Cache(max_size=max_cache_size, ttl=cache_ttl)
    
    # Configure resource manager
    _resource_manager = ResourceManager(
        max_memory_mb=max_memory_mb,
        max_cpu_percent=max_cpu_percent
    )
    
    # Set up lazy loading
    if lazy_loading:
        optimize_imports()
    
    logger.info(
        f"Optimization set up: cache_size={max_cache_size}, "
        f"cache_ttl={cache_ttl}, max_memory={max_memory_mb}MB, "
        f"max_cpu={max_cpu_percent}%, lazy_loading={lazy_loading}"
    )


def get_optimization_stats() -> Dict[str, Any]:
    """
    Get optimization statistics.
    
    Returns:
        Dictionary with optimization statistics
    """
    cache_stats = _global_cache.get_stats()
    
    memory_usage, _ = _resource_manager.check_memory_usage()
    cpu_usage, _ = _resource_manager.check_cpu_usage()
    
    return {
        "cache": cache_stats,
        "memory_usage_mb": memory_usage,
        "cpu_usage_percent": cpu_usage,
        "gc_stats": {
            "collected": gc.get_count(),
            "objects": len(gc.get_objects())
        }
    }
