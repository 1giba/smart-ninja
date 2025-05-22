"""
Unit tests for the Sequential Agent Pipeline.
Tests the complete pipeline with Planning, Scraping, Analysis and Recommendation agents.
"""
import unittest
import asyncio
from unittest.mock import MagicMock, Mock, patch, AsyncMock

from app.core.agents.analysis_agent import AnalysisAgent
from app.core.agents.planning_agent import PlanningAgent
from app.core.agents.recommendation_agent import RecommendationAgent
from app.core.agents.scraping_agent import ScrapingAgent
from app.core.agents.sequential_agent import SequentialAgent


class TestSequentialAgentPipeline(unittest.IsolatedAsyncioTestCase):
    """Test suite for the Sequential Agent Pipeline architecture"""

    def setUp(self):
        """Set up test dependencies"""
        # Create mocks for each agent
        self.mock_planning_agent = AsyncMock(spec=PlanningAgent)
        self.mock_scraping_agent = AsyncMock(spec=ScrapingAgent)
        self.mock_analysis_agent = AsyncMock(spec=AnalysisAgent)
        self.mock_recommendation_agent = AsyncMock(spec=RecommendationAgent)

        # Configure the pipeline
        self.sequential_agent = SequentialAgent(
            planning_agent=self.mock_planning_agent,
            scraping_agent=self.mock_scraping_agent,
            analysis_agent=self.mock_analysis_agent,
            recommendation_agent=self.mock_recommendation_agent,
        )

        # Sample input data
        self.sample_input = {"model": "iPhone 15", "country": "US"}

    async def test_sequential_execution(self):
        """Test that the agents are executed in the correct sequence"""
        # Configure mocks to return appropriate data
        planning_result = {"websites": ["amazon.com", "bestbuy.com"]}
        self.mock_planning_agent.execute.return_value = planning_result

        scraping_result = [
            {"price": 999.99, "store": "Amazon", "region": "US", "model": "iPhone 15"},
            {"price": 989.99, "store": "BestBuy", "region": "US", "model": "iPhone 15"},
        ]
        self.mock_scraping_agent.execute.return_value = scraping_result

        analysis_result = {
            "average_price": 994.99,
            "trend": "stable",
            "insights": "Prices are stable across retailers.",
        }
        self.mock_analysis_agent.execute.return_value = analysis_result

        recommendation_result = {
            "best_offer": {"price": 989.99, "store": "BestBuy"},
            "recommendation": "This is a good time to buy as prices are stable.",
        }
        self.mock_recommendation_agent.execute.return_value = recommendation_result

        # Execute the pipeline
        result = await self.sequential_agent.execute(self.sample_input)

        # Verify the correct sequence of execution
        self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
        self.mock_scraping_agent.execute.assert_awaited_once_with(planning_result)
        self.mock_analysis_agent.execute.assert_awaited_once_with(scraping_result)
        self.mock_recommendation_agent.execute.assert_awaited_once_with(analysis_result)

        # Verify final result matches the recommendation agent's output
        self.assertEqual(result, recommendation_result)

    async def test_pipeline_halts_on_empty_planning(self):
        """Test that the pipeline stops if planning returns empty results"""
        # Configure planning agent to return empty results
        self.mock_planning_agent.execute.return_value = {"websites": []}

        # Execute the pipeline
        result = await self.sequential_agent.execute(self.sample_input)

        # Verify planning was called but not the other agents
        self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
        self.mock_scraping_agent.execute.assert_not_awaited()
        self.mock_analysis_agent.execute.assert_not_awaited()
        self.mock_recommendation_agent.execute.assert_not_awaited()

        # Verify result indicates no websites found
        self.assertEqual(
            result,
            {"error": "No websites found for scraping", "data": {"websites": []}},
        )

    async def test_pipeline_halts_on_empty_scraping(self):
        """Test that the pipeline stops if scraping returns empty results"""
        # Configure agents
        planning_result = {"websites": ["amazon.com"]}
        self.mock_planning_agent.execute.return_value = planning_result
        self.mock_scraping_agent.execute.return_value = []

        # Execute the pipeline
        result = await self.sequential_agent.execute(self.sample_input)

        # Verify first two agents were called but not the rest
        self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
        self.mock_scraping_agent.execute.assert_awaited_once_with(planning_result)
        self.mock_analysis_agent.execute.assert_not_awaited()
        self.mock_recommendation_agent.execute.assert_not_awaited()

        # Verify result indicates no price data found
        self.assertEqual(result, {"error": "No price data found", "data": []})

    async def test_planning_agent_error_handling(self):
        """Test error handling when planning agent raises an exception"""
        # Configure planning agent to raise an exception
        self.mock_planning_agent.execute.side_effect = Exception("Planning error")

        # Execute the pipeline
        result = await self.sequential_agent.execute(self.sample_input)

        # Verify planning was called but not the other agents
        self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
        self.mock_scraping_agent.execute.assert_not_awaited()
        self.mock_analysis_agent.execute.assert_not_awaited()
        self.mock_recommendation_agent.execute.assert_not_awaited()

        # Verify error result
        self.assertEqual(result["error"], "Error in planning stage: Planning error")
        self.assertTrue("traceback" in result)

    async def test_scraping_agent_error_handling(self):
        """Test error handling when scraping agent raises an exception"""
        # Configure agents
        planning_result = {"websites": ["amazon.com"]}
        self.mock_planning_agent.execute.return_value = planning_result
        self.mock_scraping_agent.execute.side_effect = Exception("Scraping error")

        # Execute the pipeline
        result = await self.sequential_agent.execute(self.sample_input)

        # Verify first two agents were called but not the rest
        self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
        self.mock_scraping_agent.execute.assert_awaited_once_with(planning_result)
        self.mock_analysis_agent.execute.assert_not_awaited()
        self.mock_recommendation_agent.execute.assert_not_awaited()

        # Verify error result
        self.assertEqual(result["error"], "Error in scraping stage: Scraping error")
        self.assertTrue("traceback" in result)


if __name__ == "__main__":
    unittest.main()
