"""
Unit tests for the Sequential Agent Pipeline with extensive debugging.
Tests the complete pipeline with Planning, Scraping, Analysis and Recommendation agents.
"""
import unittest
import asyncio
import traceback
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
        try:
            # Configure mocks to return appropriate data
            planning_result = {"websites": ["amazon.com", "bestbuy.com"]}
            self.mock_planning_agent.execute.return_value = planning_result
            print(f"Planning agent mock configured: {planning_result}")

            scraping_result = [
                {"price": 999.99, "store": "Amazon", "region": "US", "model": "iPhone 15"},
                {"price": 989.99, "store": "BestBuy", "region": "US", "model": "iPhone 15"},
            ]
            self.mock_scraping_agent.execute.return_value = scraping_result
            print(f"Scraping agent mock configured: {scraping_result}")

            analysis_result = {
                "average_price": 994.99,
                "trend": "stable",
                "insights": "Prices are stable across retailers.",
            }
            self.mock_analysis_agent.execute.return_value = analysis_result
            print(f"Analysis agent mock configured: {analysis_result}")

            recommendation_result = {
                "best_offer": {"price": 989.99, "store": "BestBuy"},
                "recommendation": "This is a good time to buy as prices are stable.",
            }
            self.mock_recommendation_agent.execute.return_value = recommendation_result
            print(f"Recommendation agent mock configured: {recommendation_result}")

            # Execute the pipeline
            print("Executing pipeline...")
            result = await self.sequential_agent.execute(self.sample_input)
            print(f"Pipeline execution completed with result: {result}")

            # Print mock call info
            print("Planning agent execute method calls:")
            print(f"  - Call count: {self.mock_planning_agent.execute.call_count}")
            print(f"  - Await count: {self.mock_planning_agent.execute.await_count}")
            print(f"  - Call args: {self.mock_planning_agent.execute.call_args}")
            print(f"  - Await args: {self.mock_planning_agent.execute.await_args}")
            
            print("Scraping agent execute method calls:")
            print(f"  - Call count: {self.mock_scraping_agent.execute.call_count}")
            print(f"  - Await count: {self.mock_scraping_agent.execute.await_count}")
            print(f"  - Call args: {self.mock_scraping_agent.execute.call_args}")
            print(f"  - Await args: {self.mock_scraping_agent.execute.await_args}")

            # Verify the correct sequence of execution
            print("Verifying execution sequence...")
            self.mock_planning_agent.execute.assert_awaited_once_with(self.sample_input)
            self.mock_scraping_agent.execute.assert_awaited_once_with(planning_result)
            self.mock_analysis_agent.execute.assert_awaited_once_with(scraping_result)
            self.mock_recommendation_agent.execute.assert_awaited_once_with(analysis_result)

            # Verify final result matches the recommendation agent's output
            print("Verifying results...")
            self.assertEqual(result, recommendation_result)

        except Exception as e:
            print(f"ERROR in test_sequential_execution: {e}")
            print(traceback.format_exc())
            raise

    async def test_basic_function(self):
        """A minimal test to ensure AsyncMock is working correctly"""
        try:
            # Create a simple AsyncMock
            mock_async = AsyncMock()
            mock_async.return_value = 42

            # Call the mock
            result = await mock_async()
            print(f"Mock called with result: {result}")
            print(f"Mock await count: {mock_async.await_count}")

            # Assert it was called
            mock_async.assert_awaited_once()
            self.assertEqual(result, 42)
            print("Basic async mock test passed")
        except Exception as e:
            print(f"ERROR in test_basic_function: {e}")
            print(traceback.format_exc())
            raise


if __name__ == "__main__":
    unittest.main()
