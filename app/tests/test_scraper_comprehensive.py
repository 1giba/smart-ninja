"""
Comprehensive tests for the BrightDataScraperService implementation.
These tests ensure the BrightDataScraperService properly implements the IScraperService interface
and validates that all methods function correctly with various inputs.
"""
import logging
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

# pylint: disable=protected-access,attribute-defined-outside-init
from app.core.interfaces.scraping import IScraperService
from app.core.scraping.bright_data_service import BrightDataScraperService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestScraperService:
    """Test suite for the BrightDataScraperService class"""

    def setup_method(self):
        """Set up test fixtures before each test"""
        # Create a fresh instance for each test
        self.scraper = BrightDataScraperService()

    def test_service_instance(self):
        """Test that a BrightDataScraperService instance can be created and implements the correct interface"""
        scraper_service = BrightDataScraperService()
        assert isinstance(scraper_service, IScraperService)

    def test_implements_interface(self):
        """Test that BrightDataScraperService implements IScraperService interface"""
        assert isinstance(self.scraper, IScraperService)

    def test_initialization(self):
        """Test that BrightDataScraperService initializes with correct values"""
        # Check that num_results is properly initialized
        assert hasattr(self.scraper, "num_results")
        assert self.scraper.num_results > 0

    @pytest.mark.asyncio
    async def test_get_prices_with_invalid_parameters(self):
        """Test get_prices parameter validation with invalid inputs"""
        # Test with empty model
        with pytest.raises(ValueError) as excinfo:
            await self.scraper.get_prices("", "US")
        assert "model" in str(excinfo.value).lower()

        # Test with empty country
        with pytest.raises(ValueError) as excinfo:
            await self.scraper.get_prices("iPhone 15", "")
        assert "country" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_get_prices_result_structure(self, mock_service):
        """Test the structure of results from get_prices method"""
        # Mock the MCP service response
        mock_results = [
            {
                "price": 999.99,
                "currency": "USD",
                "source": "TestStore",
                "link": "https://example.com/iphone15",
                "model": "iPhone 15"
            }
        ]
        mock_service.return_value = {"data": mock_results, "status": "success"}

        # Import here to avoid circular imports during test execution
        from app.mcp.scrape_prices import service

        model = "iPhone 15"
        country = "US"

        # Get prices from the service
        results = await self.scraper.get_prices(model, country)

        # Verify the structure of results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check the first result
        first_result = results[0]
        assert isinstance(first_result, dict)

        # Validate required fields
        assert "price" in first_result
        assert "currency" in first_result
        assert "source" in first_result
        assert "link" in first_result
        assert "model" in first_result

    @pytest.mark.asyncio
    async def test_get_prices_integration(self):
        """Test the main get_prices method with a real async call (integration test)"""
        # Skip this test if no network connection is available
        pytest.skip("Skipping integration test to avoid network dependency")

        model = "iPhone 15"
        country = "US"

        # Get prices asynchronously
        results = await self.scraper.get_prices(model, country)

        # Verify results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check data integrity
        for result in results:
            assert "price" in result
            assert "source" in result
            assert "link" in result
            assert "currency" in result
            assert "model" in result

    @pytest.mark.asyncio
    async def test_get_prices_error_handling(self):
        """Test error handling in get_prices method"""
        # Test with invalid parameters
        with pytest.raises(ValueError):
            await self.scraper.get_prices("", "US")
        with pytest.raises(ValueError):
            await self.scraper.get_prices("iPhone 15", "")

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_instance_creation(self, mock_service):
        """Test that multiple BrightDataScraperService instances can be created independently"""
        # Mock the MCP service response
        mock_results = [
            {"price": 999.99, "currency": "USD", "source": "TestStore", "link": "https://example.com/iphone15"}
        ]
        mock_service.return_value = {"data": mock_results, "status": "success"}
        
        # Creating instances should return different objects
        # This verifies we're not accidentally using a singleton pattern
        service1 = BrightDataScraperService()
        service2 = BrightDataScraperService()
        assert isinstance(service1, BrightDataScraperService)
        assert isinstance(service2, BrightDataScraperService)
        assert service1 is not service2
        
        # But they should behave the same
        model = "iPhone 15"
        country = "US"
        
        # Both should return data in the same format (asynchronously)
        results1 = await service1.get_prices(model, country)
        results2 = await service2.get_prices(model, country)
        
        assert isinstance(results1, list)
        assert isinstance(results2, list)
        assert len(results1) > 0
        assert len(results2) > 0


if __name__ == "__main__":
    pytest.main(["-v", "test_scraper_comprehensive.py"])
