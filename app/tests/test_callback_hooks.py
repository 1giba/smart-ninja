"""
Tests for the Callback Hooks System.

This module tests the callback mechanism that supports hooks
like before_scraping, after_analysis, and on_error.
"""
import unittest
from unittest.mock import Mock, patch

from app.core.agents.base_agent import BaseAgent
from app.core.hooks.callback_events import AgentLifecycleEvent
from app.core.hooks.callback_registry import CallbackRegistry


class TestCallbackHooks(unittest.TestCase):
    """Test suite for the callback hooks system.

    Tests basic functionality of the CallbackRegistry class including:
    - Registering and unregistering callbacks
    - Triggering callbacks
    - Handling multiple callbacks for the same event
    - Context modification by callbacks
    """

    def setUp(self):
        """Set up the test environment before each test."""
        # Create a fresh registry for each test
        self.callback_registry = CallbackRegistry()

        # Create mock callbacks
        self.before_scraping_mock = Mock()
        self.after_analysis_mock = Mock()
        self.on_error_mock = Mock()

    def test_register_callback(self):
        """Test registering callbacks for different events."""
        # Register callbacks
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.before_scraping_mock
        )
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, self.after_analysis_mock
        )
        self.callback_registry.register(
            AgentLifecycleEvent.ON_ERROR, self.on_error_mock
        )

        # Verify callbacks were registered
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(
                    AgentLifecycleEvent.BEFORE_SCRAPING
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(AgentLifecycleEvent.AFTER_ANALYSIS)
            ),
            1,
        )
        self.assertEqual(
            len(self.callback_registry.get_callbacks(AgentLifecycleEvent.ON_ERROR)), 1
        )

    def test_trigger_callbacks(self):
        """Test triggering callbacks for an event."""
        # Register callbacks
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.before_scraping_mock
        )

        # Prepare test data
        context = {"model": "iPhone 15", "country": "US"}

        # Trigger callbacks
        self.callback_registry.trigger(AgentLifecycleEvent.BEFORE_SCRAPING, context)

        # Verify callback was called with the context
        self.before_scraping_mock.assert_called_once_with(context)

    def test_trigger_multiple_callbacks(self):
        """Test triggering multiple callbacks for the same event."""
        # Create additional mock
        second_callback = Mock()

        # Register multiple callbacks for the same event
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, self.after_analysis_mock
        )
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, second_callback
        )

        # Prepare test data
        context = {"analysis_result": "This is a test analysis"}

        # Trigger callbacks
        self.callback_registry.trigger(AgentLifecycleEvent.AFTER_ANALYSIS, context)

        # Verify both callbacks were called with the context
        self.after_analysis_mock.assert_called_once_with(context)
        second_callback.assert_called_once_with(context)

    def test_unregister_callback(self):
        """Test unregistering a callback."""
        # Register callback
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.before_scraping_mock
        )

        # Verify it was registered
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(
                    AgentLifecycleEvent.BEFORE_SCRAPING
                )
            ),
            1,
        )

        # Unregister callback
        self.callback_registry.unregister(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.before_scraping_mock
        )

        # Verify it was unregistered
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(
                    AgentLifecycleEvent.BEFORE_SCRAPING
                )
            ),
            0,
        )

    def test_trigger_nonexistent_event(self):
        """Test triggering an event with no registered callbacks."""
        # Prepare test data
        context = {"test": "data"}

        # Trigger event with no callbacks (should not raise an exception)
        self.callback_registry.trigger(AgentLifecycleEvent.ON_ERROR, context)

    def test_callback_context_modification(self):
        """Test that callbacks can modify the context."""

        # Define a callback that modifies the context
        def modifier_callback(context):
            context["modified"] = True
            context["value"] *= 2

        # Register the modifier callback
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, modifier_callback
        )

        # Prepare test data
        context = {"value": 5, "modified": False}

        # Trigger the callback
        self.callback_registry.trigger(AgentLifecycleEvent.BEFORE_SCRAPING, context)

        # Verify the context was modified
        self.assertTrue(context["modified"])
        self.assertEqual(context["value"], 10)


class TestCallbackIntegration(unittest.TestCase):
    """Test the integration of callbacks with the agent execution flow."""

    @patch("app.core.interfaces.tool_set.ISmartNinjaToolSet")
    def test_agent_with_callbacks(self, mock_tool_set):
        """Test that agents properly integrate with the callback system."""

        # Create mock agent class for testing
        class TestAgent(BaseAgent):
            def __init__(self, tool_set, callback_registry=None):
                super().__init__(callback_registry)
                self._tool_set = tool_set

            def execute(self, input_data):
                # Trigger before execution callback
                self.trigger_callback(AgentLifecycleEvent.BEFORE_EXECUTION, input_data)

                try:
                    # Do some processing
                    result = {"processed": True}

                    # Trigger after execution callback
                    self.trigger_callback(AgentLifecycleEvent.AFTER_EXECUTION, result)
                    return result
                except Exception as error:
                    # Trigger error callback
                    error_context = {"error": str(error), "input_data": input_data}
                    self.trigger_callback(AgentLifecycleEvent.ON_ERROR, error_context)
                    raise

        # Create callback registry and mock callbacks
        callback_registry = CallbackRegistry()
        before_execution_mock = Mock()
        after_execution_mock = Mock()

        # Register callbacks
        callback_registry.register(
            AgentLifecycleEvent.BEFORE_EXECUTION, before_execution_mock
        )
        callback_registry.register(
            AgentLifecycleEvent.AFTER_EXECUTION, after_execution_mock
        )

        # Create agent with the registry
        agent = TestAgent(mock_tool_set, callback_registry)

        # Execute agent
        input_data = {"test": "data"}
        agent.execute(input_data)

        # Verify callbacks were triggered
        before_execution_mock.assert_called_once_with(input_data)
        after_execution_mock.assert_called_once_with({"processed": True})

    @patch("app.core.interfaces.tool_set.ISmartNinjaToolSet")
    def test_error_handling_with_callbacks(self, mock_tool_set):
        """Test that errors in agent execution trigger appropriate callbacks."""

        # Create mock agent class for testing
        class ErrorAgent(BaseAgent):
            def __init__(self, tool_set, callback_registry=None):
                super().__init__(callback_registry)
                self._tool_set = tool_set

            def execute(self, input_data):
                self.trigger_callback(AgentLifecycleEvent.BEFORE_EXECUTION, input_data)
                raise ValueError("Test error")

        # Create callback registry and mock callbacks
        callback_registry = CallbackRegistry()
        before_execution_mock = Mock()
        error_mock = Mock()

        # Register callbacks
        callback_registry.register(
            AgentLifecycleEvent.BEFORE_EXECUTION, before_execution_mock
        )
        callback_registry.register(AgentLifecycleEvent.ON_ERROR, error_mock)

        # Create agent with the registry
        agent = ErrorAgent(mock_tool_set, callback_registry)

        # Execute agent and expect exception
        input_data = {"test": "data"}
        with self.assertRaises(ValueError):
            agent.execute(input_data)

        # Verify before_execution callback was triggered
        before_execution_mock.assert_called_once_with(input_data)

        # Verify error callback was not triggered (since we didn't implement it in the agent)
        error_mock.assert_not_called()


class TestBulkOperations(unittest.TestCase):
    """Test suite for bulk operations in the CallbackRegistry."""

    def setUp(self):
        """Set up the test environment before each test."""
        self.callback_registry = CallbackRegistry()

        # Create mock callbacks
        self.callback1 = Mock()
        self.callback2 = Mock()
        self.callback3 = Mock()

    def test_bulk_register(self):
        """Test registering multiple callbacks at once."""
        # Prepare registrations
        registrations = {
            AgentLifecycleEvent.BEFORE_SCRAPING: self.callback1,
            AgentLifecycleEvent.AFTER_ANALYSIS: [self.callback2, self.callback3],
        }

        # Register multiple callbacks
        self.callback_registry.bulk_register(registrations)

        # Verify callbacks were registered
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(
                    AgentLifecycleEvent.BEFORE_SCRAPING
                )
            ),
            1,
        )
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(AgentLifecycleEvent.AFTER_ANALYSIS)
            ),
            2,
        )

    def test_bulk_unregister(self):
        """Test unregistering multiple callbacks at once."""
        # Register callbacks
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.callback1
        )
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, self.callback2
        )
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, self.callback3
        )

        # Prepare unregistrations
        unregistrations = {
            AgentLifecycleEvent.BEFORE_SCRAPING: self.callback1,
            AgentLifecycleEvent.AFTER_ANALYSIS: [self.callback2],
        }

        # Unregister multiple callbacks
        self.callback_registry.bulk_unregister(unregistrations)

        # Verify callbacks were unregistered
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(
                    AgentLifecycleEvent.BEFORE_SCRAPING
                )
            ),
            0,
        )
        self.assertEqual(
            len(
                self.callback_registry.get_callbacks(AgentLifecycleEvent.AFTER_ANALYSIS)
            ),
            1,
        )

    def test_bulk_trigger(self):
        """Test triggering multiple callbacks at once."""
        # Register callbacks
        self.callback_registry.register(
            AgentLifecycleEvent.BEFORE_SCRAPING, self.callback1
        )
        self.callback_registry.register(
            AgentLifecycleEvent.AFTER_ANALYSIS, self.callback2
        )

        # Prepare contexts
        scraping_context = {"model": "Test"}
        analysis_context = {"result": "Test result"}

        # Trigger callbacks
        self.callback_registry.trigger(
            AgentLifecycleEvent.BEFORE_SCRAPING, scraping_context
        )
        self.callback_registry.trigger(
            AgentLifecycleEvent.AFTER_ANALYSIS, analysis_context
        )

        # Verify callbacks were triggered with the right contexts
        self.callback1.assert_called_once_with(scraping_context)
        self.callback2.assert_called_once_with(analysis_context)
