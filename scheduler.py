"""
Task scheduling and background job management.

This module provides a simple interface for scheduling and managing background tasks.
It's designed to be compatible with the existing codebase while providing
flexibility for future enhancements.
"""
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps

logger = logging.getLogger(__name__)

def task(name: Optional[str] = None, **kwargs) -> Callable:
    """
    Decorator to mark a function as a scheduled task.
    
    Args:
        name: Optional name for the task. If not provided, the function name will be used.
        **kwargs: Additional keyword arguments that might be used by the scheduler.
    
    Returns:
        The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kw: Any) -> Any:
            try:
                logger.debug(f"Running task: {name or func.__name__}")
                return await func(*args, **kw)
            except Exception as e:
                logger.error(f"Error in task {name or func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator

# For backward compatibility
def register_task(name: Optional[str] = None, **kwargs) -> Callable:
    """Alias for the task decorator for backward compatibility."""
    return task(name, **kwargs)
