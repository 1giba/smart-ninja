"""
Retry utilities for handling transient errors.

This module provides utilities for retrying operations that may fail
due to transient errors such as network issues or rate limiting.
"""

import asyncio
import logging
import random
from functools import wraps
from typing import Any, Callable, Optional, Type, Union

# Configure logging
logger = logging.getLogger(__name__)


async def retry_with_backoff(
    coroutine: Callable,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_exceptions: Optional[Union[Type[Exception], tuple]] = None,
    jitter: bool = True,
    **kwargs
) -> Any:
    """
    Retry a coroutine with exponential backoff.
    
    Args:
        coroutine: Async function to retry
        *args: Arguments to pass to the coroutine
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_exceptions: Exception or tuple of exceptions to retry on
                         (default: Exception)
        jitter: Whether to add random jitter to delay
        **kwargs: Keyword arguments to pass to the coroutine
        
    Returns:
        Result of the coroutine
        
    Raises:
        The last exception raised by the coroutine if all retries fail
    """
    if retry_exceptions is None:
        retry_exceptions = Exception
        
    attempt = 0
    last_exception = None
    
    while attempt <= max_retries:
        try:
            return await coroutine(*args, **kwargs)
        except retry_exceptions as e:
            attempt += 1
            last_exception = e
            
            if attempt > max_retries:
                logger.error(
                    f"Operation failed after {max_retries} retries: {str(e)}"
                )
                raise
                
            # Calculate exponential backoff with optional jitter
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            
            if jitter:
                # Add up to 25% random jitter
                jitter_amount = random.uniform(0, 0.25) * delay
                delay += jitter_amount
                
            logger.info(
                f"Retry attempt {attempt}/{max_retries} after error: {str(e)}. "
                f"Retrying in {delay:.2f} seconds."
            )
            
            await asyncio.sleep(delay)
    
    # This should never be reached, but just in case
    if last_exception:
        raise last_exception
    raise Exception("Retry failed for unknown reason")


def with_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    retry_exceptions: Optional[Union[Type[Exception], tuple]] = None,
    jitter: bool = True
):
    """
    Decorator to retry an async function with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        retry_exceptions: Exception or tuple of exceptions to retry on
                         (default: Exception)
        jitter: Whether to add random jitter to delay
        
    Returns:
        Decorated async function that will retry on failure
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_with_backoff(
                func,
                *args,
                max_retries=max_retries,
                base_delay=base_delay,
                max_delay=max_delay,
                retry_exceptions=retry_exceptions,
                jitter=jitter,
                **kwargs
            )
        return wrapper
    return decorator
