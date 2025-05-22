"""
Unit tests for the Scraping Agent with MCP integration.

Tests the agent that retrieves raw price data from MCP scrape_prices service.
"""
import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from app.core.agents.scraping_agent import ScrapingAgent


class TestScrapingAgentMCP(unittest.IsolatedAsyncioTestCase):
    """Test suite for the Scraping Agent implementation with MCP integration"""

    def setUp(self):
        """Set up test dependencies"""
        # Sample planning data
        self.planning_data = {
            "model": "iPhone 15",
            "country": "US",
        }
        
        # Mock response data
        self.mock_mcp_response = {
            "status": "success",
            "message": "Found 2 results for iPhone 15 in US",
            "data": [
                {
                    "price": 999.99,
                    "store": "Amazon",
                    "region": "US",
                    "model": "iPhone 15",
                    "currency": "USD",
                    "timestamp": "2025-05-17",
                    "url": "https://amazon.com/product/iphone-15",
                },
                {
                    "price": 989.99,
                    "store": "BestBuy",
                    "region": "US",
                    "model": "iPhone 15",
                    "currency": "USD",
                    "timestamp": "2025-05-17",
                    "url": "https://bestbuy.com/product/iphone-15",
                }
            ],
            "processing_time_ms": 1200
        }

    async def test_execute_with_valid_input(self):
        """Test scraping agent execution with valid input"""
        # Use a more direct patching approach at the module level
        with patch('app.core.agents.scraping_agent.scrape_prices_service', new_callable=AsyncMock) as mock_service:
            # Configure mock response
            mock_service.return_value = self.mock_mcp_response
    
            # Create scraping agent
            scraping_agent = ScrapingAgent()
            
            # Execute the agent
            result = await scraping_agent.execute(self.planning_data)
            
            # Verify results
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["store"], "Amazon")
            self.assertEqual(result[1]["store"], "BestBuy")

    async def test_execute_with_missing_model(self):
        """Test scraping agent execution with missing model information"""
        # Planning data with missing model
        invalid_planning_data = {"country": "US"}
        
        # Create scraping agent
        scraping_agent = ScrapingAgent()
        
        # Execute the agent and expect ValueError
        with self.assertRaises(ValueError) as context:
            await scraping_agent.execute(invalid_planning_data)
            
        self.assertIn("model", str(context.exception))

    async def test_execute_with_missing_country(self):
        """Test scraping agent execution with missing country information"""
        # Planning data with missing country
        invalid_planning_data = {"model": "iPhone 15"}
        
        # Create scraping agent
        scraping_agent = ScrapingAgent()
        
        # Execute the agent and expect ValueError
        with self.assertRaises(ValueError) as context:
            await scraping_agent.execute(invalid_planning_data)
            
        self.assertIn("country", str(context.exception))

    async def test_execute_with_custom_timeout(self):
        """Test scraping agent execution with custom timeout"""
        # Use a more direct patching approach at the module level
        with patch('app.core.agents.scraping_agent.scrape_prices_service', new_callable=AsyncMock) as mock_service:
            # Configure mock response
            mock_service.return_value = self.mock_mcp_response
    
            # Create scraping agent with custom timeout
            custom_timeout = 60
            scraping_agent = ScrapingAgent(mcp_timeout=custom_timeout)
            
            # Execute the agent
            result = await scraping_agent.execute(self.planning_data)
            
            # Verify results
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["store"], "Amazon")
            self.assertEqual(result[1]["store"], "BestBuy")

    async def test_execute_with_mcp_error_response(self):
        """Test scraping agent execution when MCP returns an error response"""
        with patch('app.core.agents.scraping_agent.scrape_prices_service', new_callable=AsyncMock) as mock_service:
            # Configure mock error response
            mock_service.return_value = {
                "status": "error",
                "message": "Invalid request parameters",
                "data": []
            }
            
            # Create scraping agent
            scraping_agent = ScrapingAgent()
            
            # Execute the agent
            result = await scraping_agent.execute(self.planning_data)
            
            # Verify empty result is returned
            self.assertEqual(result, [])

    async def test_execute_with_connection_error(self):
        """Test scraping agent execution when connection to MCP fails"""
        with patch('app.core.agents.scraping_agent.scrape_prices_service', 
                  side_effect=Exception("Connection error")) as mock_service:
            # Create scraping agent
            scraping_agent = ScrapingAgent()
            
            # Execute the agent
            result = await scraping_agent.execute(self.planning_data)
            
            # Verify empty result is returned
            self.assertEqual(result, [])

    async def test_execute_with_timeout(self):
        """Test scraping agent execution when MCP request times out"""
        with patch('app.core.agents.scraping_agent.scrape_prices_service', 
                  side_effect=asyncio.TimeoutError()) as mock_service:
            # Create scraping agent
            scraping_agent = ScrapingAgent()
            
            # Execute the agent
            result = await scraping_agent.execute(self.planning_data)
            
            # Verify empty result is returned
            self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
