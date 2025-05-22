"""
Base agent interface for the sequential agent pipeline.

This module defines the base interface that all agents in the pipeline must implement.
Following the principle of dependency injection, agents can be composed and easily tested.
"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional, Awaitable

from app.core.hooks.callback_events import AgentLifecycleEvent
from app.core.hooks.callback_registry import CallbackRegistry


class BaseAgent(ABC):
    """
    Base interface for all agents in the sequential pipeline architecture.

    All concrete agent implementations must inherit from this class
    and implement the execute method. The class now supports callback hooks
    for extending agent functionality without modifying core logic.
    """

    def __init__(self, callback_registry: Optional[CallbackRegistry] = None):
        """
        Initialize the base agent with an optional callback registry.

        Args:
            callback_registry: Registry for callback hooks, a new one is created if None
        """
        self._callback_registry = callback_registry or CallbackRegistry()

    def register_callback(
        self, event: AgentLifecycleEvent, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a callback for a specific event.

        Args:
            event: The event that will trigger this callback
            callback: The function to call when the event occurs
        """
        self._callback_registry.register(event, callback)

    def unregister_callback(
        self, event: AgentLifecycleEvent, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Remove a previously registered callback.

        Args:
            event: The event the callback was registered for
            callback: The callback function to remove
        """
        self._callback_registry.unregister(event, callback)

    def trigger_callback(
        self, event: AgentLifecycleEvent, context: Dict[str, Any]
    ) -> None:
        """
        Trigger all callbacks registered for an event.

        Args:
            event: The event that occurred
            context: Data to pass to the callbacks
        """
        self._callback_registry.trigger(event, context)

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic with the provided input data asynchronously.

        Args:
            input_data: Dictionary containing input data required for agent execution

        Returns:
            Dictionary containing agent execution results

        Raises:
            ValueError: If required input data is missing
        """
        pass
