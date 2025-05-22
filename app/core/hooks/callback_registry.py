"""
Callback registry system for agent hooks.

This module provides a registry for managing callbacks that can be triggered
at specific points in the agent execution flow. It follows the observer pattern
to enable loose coupling between the agent logic and callback implementations.
"""
import logging
from typing import Any, Callable, Collection, Dict, List, Optional, Union

from app.core.hooks.callback_events import AgentLifecycleEvent


class CallbackRegistry:
    """Registry for managing callbacks triggered at different execution points.

    This class follows the observer pattern, allowing multiple callbacks to be
    registered for the same event and triggered when that event occurs.

    Example:
        ```python
        # Create a registry
        registry = CallbackRegistry()

        # Define a callback function
        def log_before_execution(context):
            print(f"Before execution with data: {context}")

        # Register the callback
        registry.register(AgentLifecycleEvent.BEFORE_EXECUTION, log_before_execution)

        # Trigger the callback
        registry.trigger(AgentLifecycleEvent.BEFORE_EXECUTION, {"input": "test"})
        ```
    """

    def __init__(self):
        """Initialize an empty callback registry."""
        # Initialize empty dictionary to store callbacks for each event
        self._callbacks: Dict[
            AgentLifecycleEvent, List[Callable[[Dict[str, Any]], None]]
        ] = {}
        self._logger = logging.getLogger(__name__)

    def register(
        self, event: AgentLifecycleEvent, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Register a callback function for a specific event.

        Args:
            event: The event that will trigger this callback
            callback: The function to call when the event occurs
                      Must accept a single dict argument with context data
        """
        if event not in self._callbacks:
            self._callbacks[event] = []

        self._callbacks[event].append(callback)
        self._logger.debug(f"Registered callback for event {event.name}")

    def unregister(
        self, event: AgentLifecycleEvent, callback: Callable[[Dict[str, Any]], None]
    ) -> None:
        """
        Remove a previously registered callback.

        Args:
            event: The event the callback was registered for
            callback: The callback function to remove
        """
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
            self._logger.debug(f"Unregistered callback for event {event.name}")

    def get_callbacks(
        self, event: AgentLifecycleEvent
    ) -> List[Callable[[Dict[str, Any]], None]]:
        """
        Get all callbacks registered for a specific event.

        Args:
            event: The event to get callbacks for

        Returns:
            List of callback functions registered for the event
        """
        return self._callbacks.get(event, [])

    def bulk_register(
        self,
        registrations: Dict[
            AgentLifecycleEvent,
            Union[
                Callable[[Dict[str, Any]], None],
                Collection[Callable[[Dict[str, Any]], None]],
            ],
        ],
    ) -> None:
        """
        Register multiple callbacks for different events at once.

        Args:
            registrations: Dictionary mapping events to callbacks or collections of callbacks

        Example:
            ```python
            registry.bulk_register({
                AgentLifecycleEvent.BEFORE_EXECUTION: log_before_execution,
                AgentLifecycleEvent.AFTER_EXECUTION: [log_after_execution, notify_after_execution]
            })
            ```
        """
        for event, callbacks in registrations.items():
            if isinstance(callbacks, Collection) and not isinstance(callbacks, str):
                for callback in callbacks:
                    self.register(event, callback)
            else:
                self.register(event, callbacks)  # type: ignore

    def bulk_unregister(
        self,
        registrations: Dict[
            AgentLifecycleEvent,
            Union[
                Callable[[Dict[str, Any]], None],
                Collection[Callable[[Dict[str, Any]], None]],
            ],
        ],
    ) -> None:
        """
        Unregister multiple callbacks for different events at once.

        Args:
            registrations: Dictionary mapping events to callbacks or collections of callbacks to unregister
        """
        for event, callbacks in registrations.items():
            if isinstance(callbacks, Collection) and not isinstance(callbacks, str):
                for callback in callbacks:
                    self.unregister(event, callback)
            else:
                self.unregister(event, callbacks)  # type: ignore

    def trigger(self, event: AgentLifecycleEvent, context: Dict[str, Any]) -> None:
        """
        Trigger all callbacks registered for an event.

        Args:
            event: The event that occurred
            context: Data to pass to the callbacks
        """
        callbacks = self.get_callbacks(event)

        if not callbacks:
            self._logger.debug(f"No callbacks registered for event {event.name}")
            return

        self._logger.debug(
            f"Triggering {len(callbacks)} callbacks for event {event.name}"
        )
        for callback in callbacks:
            try:
                callback(context)
            except Exception as e:
                self._logger.error(
                    f"Error in callback for event {event.name}: {str(e)}", exc_info=True
                )
