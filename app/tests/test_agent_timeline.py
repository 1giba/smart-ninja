"""
Tests for the agent timeline UI component in the SmartNinja application.
Tests the functionality of displaying the agent execution pipeline in the sidebar.
"""
import os
import sys
import unittest
from copy import deepcopy
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# pylint: disable=wrong-import-position
from app.ui.timeline_components import display_agent_timeline


class TestAgentTimeline(unittest.TestCase):
    """Test suite for agent timeline UI component"""

    def test_module_structure(self):
        """Test that the UI timeline_components module has the agent timeline function"""
        import app.ui.timeline_components

        # Verify that the module has the agent timeline function
        self.assertTrue(hasattr(app.ui.timeline_components, "display_agent_timeline"))

    def test_display_agent_timeline_empty(self):
        """Test that the agent timeline initializes correctly with no active steps"""
        # Use a more direct approach with proper context management to reduce test brittleness
        with patch("app.ui.timeline_components.st.sidebar.subheader") as mock_subheader, \
             patch("app.ui.timeline_components.st.sidebar.container") as mock_container, \
             patch("app.ui.timeline_components.render_agent_timeline") as mock_render:
            
            # Setup container mock to avoid context manager issues
            container_instance = MagicMock()
            mock_container.return_value.__enter__ = MagicMock(return_value=container_instance)
            mock_container.return_value.__exit__ = MagicMock(return_value=None)
            
            # Call function
            timeline = display_agent_timeline()
            
            # Core functionality checks - focus on behavior over implementation
            # 1. Verify the sidebar was accessed
            mock_subheader.assert_called_once_with("Agent Pipeline")
            mock_container.assert_called_once()
            
            # 2. Check the timeline structure (focus on the contract, not implementation)
            self.assertIsInstance(timeline, dict)
            
            # 3. Verify expected steps are present
            expected_steps = ["planning", "scraping", "analysis", "recommendation", "notification"]
            for step in expected_steps:
                self.assertIn(step, timeline)
                self.assertEqual(timeline[step]["status"], "pending")  # All steps should be pending initially

    def test_display_agent_timeline_with_active_step(self):
        """Test agent timeline with an active step"""
        # Use context managers for patching to avoid import-time issues
        with patch("app.ui.timeline_components.st.sidebar.container") as mock_container:
            with patch("app.ui.timeline_components.st.sidebar.subheader") as mock_subheader:
                with patch("app.ui.timeline_components.render_agent_timeline") as mock_render:
                    # Setup mock container with proper context manager behavior
                    container_instance = MagicMock()
                    mock_container.return_value.__enter__ = MagicMock(return_value=container_instance)
                    mock_container.return_value.__exit__ = MagicMock(return_value=None)
                    
                    # Call function with active step
                    timeline = display_agent_timeline(active_step="scraping")
                    
                    # Verify timeline has correct status
                    self.assertEqual(timeline["planning"]["status"], "pending")
                    self.assertEqual(timeline["scraping"]["status"], "active")
                    self.assertEqual(timeline["analysis"]["status"], "pending")
                    self.assertEqual(timeline["recommendation"]["status"], "pending")
                    self.assertEqual(timeline["notification"]["status"], "pending")
                    
                    # Verify scraping has start time
                    self.assertIn("start_time", timeline["scraping"])

    def test_display_agent_timeline_with_completed_steps(self):
        """Test that the agent timeline properly shows completed steps"""
        # Use context managers for patching to avoid import-time issues
        with patch("app.ui.timeline_components.st.sidebar.container") as mock_container:
            with patch("app.ui.timeline_components.st.sidebar.subheader") as mock_subheader:
                with patch("app.ui.timeline_components.render_agent_timeline") as mock_render:
                    # Setup mock container with proper context manager behavior
                    container_instance = MagicMock()
                    mock_container.return_value.__enter__ = MagicMock(return_value=container_instance)
                    mock_container.return_value.__exit__ = MagicMock(return_value=None)
                    
                    # Create timeline with existing data
                    previous_timeline = {
                        "planning": {"status": "completed", "start_time": "10:00", "end_time": "10:01"},
                        "scraping": {"status": "completed", "start_time": "10:01", "end_time": "10:03"},
                        "analysis": {"status": "active", "start_time": "10:03"},
                        "recommendation": {"status": "pending"},
                        "notification": {"status": "pending"}
                    }
                    
                    # Call with existing timeline and update to next step
                    timeline = display_agent_timeline(active_step="analysis", existing_timeline=previous_timeline)
                    
                    # Verify statuses are maintained correctly
                    self.assertEqual(timeline["planning"]["status"], "completed")
                    self.assertEqual(timeline["scraping"]["status"], "completed")
                    self.assertEqual(timeline["analysis"]["status"], "active")
                    self.assertEqual(timeline["recommendation"]["status"], "pending")
                    self.assertEqual(timeline["notification"]["status"], "pending")
                    
                    # Verify timestamps are preserved
                    self.assertEqual(timeline["planning"]["start_time"], "10:00")
                    self.assertEqual(timeline["planning"]["end_time"], "10:01")
                    self.assertEqual(timeline["scraping"]["start_time"], "10:01")
                    self.assertEqual(timeline["scraping"]["end_time"], "10:03")
                    self.assertEqual(timeline["analysis"]["start_time"], "10:03")

    def test_display_agent_timeline_with_failed_step(self):
        """Test that the agent timeline properly preserves failed steps and error messages"""
        # Use context managers for consistent patching approach
        with patch("app.ui.timeline_components.st.sidebar.subheader") as mock_subheader:
            with patch("app.ui.timeline_components.st.sidebar.container") as mock_container:
                with patch("app.ui.timeline_components.render_agent_timeline") as mock_render:
                    # Setup container mock
                    mock_container_instance = MagicMock()
                    mock_container.return_value.__enter__ = MagicMock(return_value=mock_container_instance)
                    mock_container.return_value.__exit__ = MagicMock(return_value=None)
                    
                    # Create timeline with a failed step
                    timeline = {
                        "planning": {"status": "completed", "duration": 1.5},
                        "scraping": {"status": "failed", "duration": 2.1, "error": "Network error"},
                        "analysis": {"status": "pending", "duration": None},
                        "recommendation": {"status": "pending", "duration": None},
                        "notification": {"status": "pending", "duration": None}
                    }
                    
                    # Create a deep copy to ensure isolation
                    timeline_copy = deepcopy(timeline)
                    
                    # Call function with existing timeline
                    updated_timeline = display_agent_timeline(existing_timeline=timeline_copy)
                    
                    # Verify timeline object has correct statuses
                    self.assertEqual(updated_timeline["planning"]["status"], "completed")
                    self.assertEqual(updated_timeline["scraping"]["status"], "failed")
                    self.assertEqual(updated_timeline["analysis"]["status"], "pending")
                    
                    # Verify error message was preserved
                    self.assertIn("error", updated_timeline["scraping"])
                    self.assertEqual(updated_timeline["scraping"]["error"], "Network error")

    def test_display_agent_timeline_reset(self):
        """Test that the reset parameter correctly resets the timeline"""
        # Use proper context management for patching
        with patch("app.ui.timeline_components.st.sidebar.subheader") as mock_subheader, \
             patch("app.ui.timeline_components.st.sidebar.container") as mock_container, \
             patch("app.ui.timeline_components.render_agent_timeline") as mock_render:
            
            # Setup container mock to avoid context manager issues
            container_instance = MagicMock()
            mock_container.return_value.__enter__ = MagicMock(return_value=container_instance)
            mock_container.return_value.__exit__ = MagicMock(return_value=None)
            
            # First create a timeline
            timeline = display_agent_timeline()
            
            # Update some steps to simulate pipeline execution
            timeline["planning"]["status"] = "completed"
            timeline["scraping"]["status"] = "active"
            
            # Reset the timeline
            reset_timeline = display_agent_timeline(reset=True, existing_timeline=timeline)
            
            # Verify all steps are back to pending
            expected_steps = ["planning", "scraping", "analysis", "recommendation", "notification"]
            for step in expected_steps:
                self.assertIn(step, reset_timeline)
                self.assertEqual(reset_timeline[step]["status"], "pending")
                self.assertIsNone(reset_timeline[step]["duration"])
