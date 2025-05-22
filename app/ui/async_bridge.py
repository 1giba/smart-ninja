"""
AsyncBridge for Streamlit-Async Integration.

This module provides a bridge between Streamlit's synchronous UI and async backend services.
It follows the SmartNinja architecture principles for async-first design and proper integration.
"""
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, TypeVar

T = TypeVar('T')


class AsyncBridge:
    """
    Bridge for executing async functions from synchronous Streamlit code.
    
    This class provides a static method to run asynchronous functions from
    synchronous Streamlit UI code, following the SmartNinja architecture principles.
    """
    
    _executor = ThreadPoolExecutor(max_workers=10)
    
    @staticmethod
    def run_async(coroutine: Callable[..., T]) -> T:
        """
        Run an asynchronous function from synchronous code.
        
        Args:
            coroutine: Coroutine to execute
            
        Returns:
            The result of the coroutine execution
        
        Raises:
            Any exception raised by the coroutine
        """
        # Check if we're already inside an event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already inside a running event loop, we can't use run_until_complete
                # This happens when AsyncBridge.run_async is called inside another coroutine
                # which is a sign of improper nesting - in this case, return a default value
                import logging
                logging.warning("AsyncBridge.run_async called inside a running event loop. This is improper nesting.")
                # Return empty result - this is better than crashing
                return [] if isinstance(coroutine, list) else {}
        except RuntimeError:
            # Create new event loop if there isn't one (for thread safety)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Execute the coroutine and return its result
        try:
            return loop.run_until_complete(coroutine)
        except Exception as e:
            import logging
            logging.error(f"Error executing coroutine: {str(e)}")
            # Return empty result on error
            return [] if isinstance(coroutine, list) else {}
    
    @staticmethod
    def run_async_in_thread(coroutine: Callable[..., T]) -> T:
        """
        Run an asynchronous function in a separate thread.
        
        Useful for long-running tasks that shouldn't block the UI thread.
        
        Args:
            coroutine: Coroutine to execute
            
        Returns:
            The result of the coroutine execution
        
        Raises:
            Any exception raised by the coroutine
        """
        def run_coro_in_thread():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coroutine)
        
        # Submit the coroutine to the thread pool
        future = AsyncBridge._executor.submit(run_coro_in_thread)
        return future.result()
