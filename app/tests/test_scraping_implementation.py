"""Tests for the concrete implementations of the scraping components.
This module validates that the concrete implementations of PriceScraper and PriceAnalyzer
classes fulfill their interface contracts and handle various scenarios correctly.
"""
# pylint: disable=no-name-in-module
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List

from app.core.analyzer.service import PriceAnalyzerService as PriceAnalyzer
from app.core.analyzer.rule_based.fallback_analyzer import get_fallback_analysis
from app.core.scraping.mock_scraper import MockPriceScraper


@pytest.mark.asyncio
class TestPriceScraper:
    """Test suite for the PriceScraper class"""

    def setup_method(self):
        """Set up the test environment"""
        self.scraper = MockPriceScraper()

    def test_initialization(self):
        """Test that the scraper initializes correctly with expected properties"""
        # Verify it's the right class
        assert isinstance(self.scraper, MockPriceScraper)
        # Verify it has the required interface method
        assert hasattr(self.scraper, "scrape_prices")
        # Verify the method is async
        assert asyncio.iscoroutinefunction(self.scraper.scrape_prices)

    @pytest.mark.asyncio
    async def test_scrape_prices_success(self):
        """Test that the scraper returns price data in the expected format"""
        # Set up test data
        model = "iPhone 15 Pro"
        region = "US"
        
        # Call the method
        results = await self.scraper.scrape_prices(model, region)
        
        # Validate response
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check the structure of the first result
        result = results[0]
        assert isinstance(result, dict)
        assert "title" in result
        assert model in result["title"]
        assert "price" in result and isinstance(result["price"], float)
        assert "currency" in result and isinstance(result["currency"], str)
        assert "store" in result
        assert "url" in result
        assert "date" in result

    @pytest.mark.asyncio
    async def test_special_timeout_handling(self):
        """Test that timeout=1 triggers a simulated timeout error"""
        # The MockPriceScraper raises a TimeoutError when timeout=1 is passed
        # This special case is used for testing timeout handling
        with pytest.raises(Exception) as excinfo:
            await self.scraper.scrape_prices("iPhone 15 Pro", "US", timeout=1)
        
        # The error could be a TimeoutError or a wrapped Exception with timeout message
        assert "timeout" in str(excinfo.value).lower()


class TestPriceAnalyzer:
    """Test suite for the PriceAnalyzer class"""

    def setup_method(self):
        """Set up the test environment"""
        # Create mocks for required dependencies
        self.mock_formatter = MagicMock()
        self.mock_prompt_generator = MagicMock()
        self.mock_llm_client = MagicMock()
        self.mock_rule_based_analyzer = MagicMock()
        
        # Configure mocks with sensible return values
        self.mock_formatter.format_price_data.return_value = "Formatted: $999.99 at Store A, $1099.99 at Store B"
        self.mock_prompt_generator.generate_prompt.return_value = "Analyze these prices: $999.99, $1099.99"
        self.mock_llm_client.generate_response.return_value = "The market shows competitive pricing with an average of $1049.99."
        self.mock_rule_based_analyzer.analyze.return_value = "Based on rules: prices are within expected range."
        
        # Initialize the analyzer with mocked dependencies
        self.analyzer = PriceAnalyzer(
            formatter=self.mock_formatter,
            prompt_generator=self.mock_prompt_generator,
            llm_client=self.mock_llm_client,
            rule_based_analyzer=self.mock_rule_based_analyzer
        )
        
        # Sample data for testing
        self.sample_data = [
            {
                "price": 999.99,
                "currency": "USD",
                "store": "Store A",
                "model": "iPhone 15",
                "url": "https://example.com/iphone",
                "timestamp": datetime.now().isoformat()
            },
            {
                "price": 1099.99,
                "currency": "USD",
                "store": "Store B",
                "model": "iPhone 15",
                "url": "https://example.com/iphone-alt",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    def test_initialization(self):
        """Test proper initialization of the analyzer"""
        assert isinstance(self.analyzer, PriceAnalyzer)
        assert hasattr(self.analyzer, "analyze_market")
    
    def test_analyze_market_success_path(self):
        """Test the happy path through the analyze_market method"""
        # Act
        result = self.analyzer.analyze_market(self.sample_data)
        
        # Assert
        # Verify the formatter was called with our sample data
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        
        # Verify the prompt generator was called with formatted data
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            self.mock_formatter.format_price_data.return_value
        )
        
        # Verify the LLM client was called with the generated prompt
        self.mock_llm_client.generate_response.assert_called_once_with(
            self.mock_prompt_generator.generate_prompt.return_value
        )
        
        # Verify the rule-based analyzer was not called (since LLM succeeded)
        self.mock_rule_based_analyzer.analyze.assert_not_called()
        
        # Verify the result is the expected analysis from the LLM
        assert result == self.mock_llm_client.generate_response.return_value
    
    def test_analyze_market_llm_failure(self):
        """Test fallback to rule-based analysis when LLM fails"""
        # Arrange
        self.mock_llm_client.generate_response.side_effect = Exception("LLM unavailable")
        
        # Act
        result = self.analyzer.analyze_market(self.sample_data)
        
        # Assert
        # Verify the LLM client was called but failed
        self.mock_llm_client.generate_response.assert_called_once()
        
        # Verify fallback to rule-based analyzer
        self.mock_rule_based_analyzer.analyze.assert_called_once_with(self.sample_data)
        
        # Verify the result is from the rule-based analyzer
        assert result == self.mock_rule_based_analyzer.analyze.return_value
    
    def test_analyze_market_both_failures(self):
        """Test ultimate fallback when both LLM and rule-based analysis fail"""
        # Arrange - make both analyzers fail
        self.mock_llm_client.generate_response.side_effect = Exception("LLM unavailable")
        self.mock_rule_based_analyzer.analyze.side_effect = Exception("Rules broken")
        
        # Act
        result = self.analyzer.analyze_market(self.sample_data)
        
        # Assert
        # Verify both were called
        self.mock_llm_client.generate_response.assert_called_once()
        self.mock_rule_based_analyzer.analyze.assert_called_once()
        
        # The ultimate fallback should be a non-empty string with basic fallback text
        assert isinstance(result, str)
        assert len(result) > 0
        
        # Should contain standard fallback messaging
        fallback = get_fallback_analysis()
        assert result == fallback
    
    def test_analyze_market_empty_data(self):
        """Test handling of empty data"""
        # Act
        result = self.analyzer.analyze_market([])
        
        # Assert - should return a message about no data
        assert "no price data" in result.lower()
        
        # Confirm no unnecessary calls were made
        self.mock_formatter.format_price_data.assert_not_called()
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()


if __name__ == "__main__":
    unittest.main()
