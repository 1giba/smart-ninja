"""
Tests for PlanningAgent with SiteSelector integration.
Verifies that the PlanningAgent correctly uses the SiteSelector for determining target websites.
"""
import unittest
import asyncio

# pylint: disable=unused-import
from unittest.mock import MagicMock, Mock, patch, AsyncMock

from app.core.agents.planning_agent import PlanningAgent

# pylint: disable=no-name-in-module,no-member,import-error
from app.core.scraping.site_selector import SiteSelector


class TestPlanningAgentWithSiteSelector(unittest.IsolatedAsyncioTestCase):
    """Test suite for the PlanningAgent with SiteSelector integration"""

    def setUp(self):
        """Set up test dependencies"""
        self.planning_agent = PlanningAgent()

    @patch("app.core.agents.planning_agent.SiteSelector")
    async def test_planning_agent_uses_site_selector(self, mock_selector_class):
        """Test that PlanningAgent uses SiteSelector when available"""
        # Setup mock SiteSelector instance
        mock_selector = MagicMock()
        mock_selector.determine_optimal_scraping_targets.return_value = [
            "amazon.com",
            "bestbuy.com",
            "walmart.com",
        ]
        # Make the mock_selector_class return our mock_selector instance
        mock_selector_class.return_value = mock_selector

        # Create planning agent with mock selector
        planning_agent = PlanningAgent()

        # Execute the agent
        input_data = {"model": "iPhone 15", "country": "US"}
        result = await planning_agent.execute(input_data)

        # Verify SiteSelector was used
        mock_selector.determine_optimal_scraping_targets.assert_called_once_with(
            input_data
        )

        # Verify results match what SiteSelector returned
        self.assertEqual(
            result["websites"], ["amazon.com", "bestbuy.com", "walmart.com"]
        )

    async def test_planning_agent_with_user_preferences(self):
        """Test PlanningAgent handles user preferences and passes them to SiteSelector"""
        # Create agent with real SiteSelector
        planning_agent = PlanningAgent()

        # Execute with user preferences
        input_data = {
            "model": "iPhone 15",
            "country": "US",
            "user_preferences": {"preferred_retailers": ["apple.com", "bestbuy.com"]},
        }
        result = await planning_agent.execute(input_data)

        # Verify user preferences were considered in result
        self.assertIn("websites", result)
        self.assertIsInstance(result["websites"], list)
        # First two sites should be the user's preferred retailers
        self.assertEqual(result["websites"][0], "apple.com")
        self.assertEqual(result["websites"][1], "bestbuy.com")

    async def test_planning_agent_with_region_preference(self):
        """Test that PlanningAgent handles region preferences"""
        # Execute with region preference
        input_data = {
            "model": "Samsung Galaxy",
            "country": "US",
            "region": "East Coast",
        }
        result = await self.planning_agent.execute(input_data)

        # Verify result contains region metadata
        self.assertIn("region", result)
        self.assertEqual(result["region"], "East Coast")

        # Region should influence the websites list
        self.assertIn("websites", result)
        self.assertIsInstance(result["websites"], list)

    async def test_planning_agent_with_max_sites_limit(self):
        """Test that PlanningAgent respects max_sites limit"""
        # Execute with max_sites limit
        input_data = {"model": "iPhone 15", "country": "US", "max_sites": 2}
        result = await self.planning_agent.execute(input_data)

        # Verify only requested number of sites returned
        self.assertIn("websites", result)
        self.assertEqual(len(result["websites"]), 2)

    async def test_planning_agent_fallback_without_site_selector(self):
        """Test that PlanningAgent works without SiteSelector using fallback logic"""
        # Patch SiteSelector.select_sites to raise an AttributeError (simulating missing attribute)
        with patch.object(
            SiteSelector,
            "select_sites",
            side_effect=AttributeError("Testing fallback mechanism"),
        ):
            # Create a planning agent
            planning_agent = PlanningAgent()

            # Execute the agent
            input_data = {"model": "iPhone 15", "country": "US"}
            result = await planning_agent.execute(input_data)

            # Verify a fallback website list is still returned
            self.assertIn("websites", result)
            self.assertIsInstance(result["websites"], list)
            self.assertGreater(len(result["websites"]), 0)


if __name__ == "__main__":
    unittest.main()
