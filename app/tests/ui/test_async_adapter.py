"""
Unit tests for the Async Bridge adapter.

These tests verify that the AsyncBridge correctly handles the conversion
of asynchronous function calls to synchronous ones for the Streamlit UI,
including proper error handling and timeout management.
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ui.async_adapter import (
    AnalysisAgentAdapter,
    AsyncBridge,
    RecommendationAgentAdapter,
    ScrapingAgentAdapter,
)


class TestAsyncBridge(unittest.TestCase):
    """Test cases for the AsyncBridge utility."""

    def setUp(self):
        """Set up test fixtures."""
        # Create event loop for async tests
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        """Clean up after tests."""
        self.loop.close()

    @pytest.mark.asyncio
    async def test_run_async_successful_execution(self):
        """Test that AsyncBridge.run_async executes an async function successfully."""
        # Define a sample async function
        async def sample_async_func(x, y):
            return x + y

        # Run it through the AsyncBridge
        result = AsyncBridge.run_async(sample_async_func, 10, 20)
        
        # Assert
        self.assertEqual(result, 30)

    @pytest.mark.asyncio
    async def test_run_async_with_exception(self):
        """Test that AsyncBridge.run_async properly raises exceptions from the async function."""
        # Define an async function that raises an exception
        async def async_func_with_error():
            raise ValueError("Test error")

        # Assert that the exception is properly raised
        with self.assertRaises(ValueError) as context:
            AsyncBridge.run_async(async_func_with_error)
            
        self.assertEqual(str(context.exception), "Test error")

    @pytest.mark.asyncio
    async def test_run_async_with_timeout(self):
        """Test that AsyncBridge.run_async handles timeouts correctly."""
        # Define an async function that takes longer than the timeout
        async def slow_async_func():
            await asyncio.sleep(0.5)  # This will be too slow
            return "This should never be returned"

        # Patch asyncio.new_event_loop to return a mock with controlled timeout
        with patch('asyncio.new_event_loop') as mock_new_loop:
            # Create a mock loop that raises TimeoutError on run_until_complete
            mock_loop = MagicMock()
            mock_loop.run_until_complete.side_effect = asyncio.TimeoutError()
            mock_new_loop.return_value = mock_loop
            
            # Assert that the timeout exception is properly raised
            with self.assertRaises(asyncio.TimeoutError):
                AsyncBridge.run_async(slow_async_func)


class TestAgentAdapters(unittest.TestCase):
    """Test cases for the agent adapter classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create mocks for the agents
        self.mock_scraping_agent = MagicMock()
        self.mock_analysis_agent = MagicMock()
        self.mock_recommendation_agent = MagicMock()
        
        # Patch the agent classes
        self.scraping_agent_patcher = patch('app.ui.async_adapter.ScrapingAgent', 
                                           return_value=self.mock_scraping_agent)
        self.analysis_agent_patcher = patch('app.ui.async_adapter.AnalysisAgent', 
                                           return_value=self.mock_analysis_agent)
        self.recommendation_agent_patcher = patch('app.ui.async_adapter.RecommendationAgent', 
                                                 return_value=self.mock_recommendation_agent)
        
        # Start the patches
        self.mock_scraping_agent_class = self.scraping_agent_patcher.start()
        self.mock_analysis_agent_class = self.analysis_agent_patcher.start()
        self.mock_recommendation_agent_class = self.recommendation_agent_patcher.start()
        
    def tearDown(self):
        """Clean up after tests."""
        # Stop the patches
        self.scraping_agent_patcher.stop()
        self.analysis_agent_patcher.stop()
        self.recommendation_agent_patcher.stop()
    
    @patch('app.ui.async_adapter.AsyncBridge.run_async')
    def test_scraping_agent_adapter_execute(self, mock_run_async):
        """Test that ScrapingAgentAdapter correctly uses AsyncBridge."""
        # Setup
        adapter = ScrapingAgentAdapter()
        input_data = {'model': 'iPhone 15', 'country': 'US'}
        mock_run_async.return_value = [{'title': 'iPhone 15', 'price': 999.99}]
        
        # Execute
        result = adapter.execute(input_data)
        
        # Assert
        mock_run_async.assert_called_once_with(self.mock_scraping_agent.execute, input_data)
        self.assertEqual(result, [{'title': 'iPhone 15', 'price': 999.99}])
    
    @patch('app.ui.async_adapter.AsyncBridge.run_async')
    def test_analysis_agent_adapter_analyze_prices(self, mock_run_async):
        """Test that AnalysisAgentAdapter correctly uses AsyncBridge for analyze_prices."""
        # Setup
        adapter = AnalysisAgentAdapter()
        price_data = [{'title': 'iPhone 15', 'price': 999.99}]
        mock_run_async.return_value = {'analysis': 'This is a good price'}
        
        # Execute
        result = adapter.analyze_prices(price_data)
        
        # Assert
        mock_run_async.assert_called_once_with(self.mock_analysis_agent.analyze_prices, price_data)
        self.assertEqual(result, {'analysis': 'This is a good price'})
    
    @patch('app.ui.async_adapter.AsyncBridge.run_async')
    def test_recommendation_agent_adapter_execute(self, mock_run_async):
        """Test that RecommendationAgentAdapter correctly uses AsyncBridge."""
        # Setup
        adapter = RecommendationAgentAdapter()
        input_data = {'price_data': [{'title': 'iPhone 15', 'price': 999.99}]}
        mock_run_async.return_value = {'best_offer': {'store': 'BestBuy', 'price': 999.99}}
        
        # Execute
        result = adapter.execute(input_data)
        
        # Assert
        mock_run_async.assert_called_once_with(self.mock_recommendation_agent.execute, input_data)
        self.assertEqual(result, {'best_offer': {'store': 'BestBuy', 'price': 999.99}})
