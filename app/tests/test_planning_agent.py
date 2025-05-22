"""
Unit tests for the Planning Agent.
Tests the agent that determines target websites based on model and country.
"""
import unittest
import asyncio
from unittest.mock import Mock, patch

from app.core.agents.planning_agent import PlanningAgent


class TestPlanningAgent(unittest.IsolatedAsyncioTestCase):
    """Test suite for the Planning Agent implementation"""

    def setUp(self):
        """Set up test dependencies"""
        # Create a basic planning agent
        self.planning_agent = PlanningAgent()

    async def test_execute_with_valid_input(self):
        """Test planning agent execution with valid input"""
        # Sample input data
        input_data = {"model": "iPhone 15", "country": "US"}

        # Execute the agent
        result = await self.planning_agent.execute(input_data)

        # Verify result structure
        self.assertIn("websites", result)
        self.assertIsInstance(result["websites"], list)
        # We expect the agent to return at least one website for a popular model
        self.assertGreater(len(result["websites"]), 0)

        # Each website should be a string
        for website in result["websites"]:
            self.assertIsInstance(website, str)

    async def test_execute_with_missing_model(self):
        """Test planning agent execution with missing model information"""
        # Input with missing model
        input_data = {"country": "US"}

        # Execute the agent and expect ValueError
        with self.assertRaises(ValueError) as context:
            await self.planning_agent.execute(input_data)

        self.assertIn("model", str(context.exception))

    async def test_execute_with_missing_country(self):
        """Test planning agent execution with missing country information"""
        # Input with missing country
        input_data = {"model": "iPhone 15"}

        # Execute the agent and expect ValueError
        with self.assertRaises(ValueError) as context:
            await self.planning_agent.execute(input_data)

        self.assertIn("country", str(context.exception))

    async def test_execute_with_unsupported_country(self):
        """Test planning agent execution with unsupported country"""
        # Input with unsupported country
        input_data = {
            "model": "iPhone 15",
            "country": "XYZ",  # Non-existent country code
        }

        # Execute the agent
        result = await self.planning_agent.execute(input_data)

        # Should return default international websites
        self.assertIn("websites", result)
        self.assertIsInstance(result["websites"], list)
        # Should contain some fallback international websites
        self.assertGreater(len(result["websites"]), 0)

    async def test_execute_with_unknown_model(self):
        """Test planning agent execution with unknown model"""
        # Input with an obscure model that might not be in the database
        input_data = {"model": "CompletelyUnknownDeviceXYZ123", "country": "US"}

        # Execute the agent
        result = await self.planning_agent.execute(input_data)

        # Should still return some generic electronics websites for the country
        self.assertIn("websites", result)
        self.assertIsInstance(result["websites"], list)
        self.assertGreater(len(result["websites"]), 0)

    async def test_execute_returns_metadata(self):
        """Test that planning agent includes metadata in results"""
        # Sample input data
        input_data = {"model": "iPhone 15", "country": "US"}

        # Execute the agent
        result = await self.planning_agent.execute(input_data)

        # Verify result contains metadata like model and country
        self.assertIn("model", result)
        self.assertEqual(result["model"], "iPhone 15")
        self.assertIn("country", result)
        self.assertEqual(result["country"], "US")


if __name__ == "__main__":
    unittest.main()
