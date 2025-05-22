"""
Tests for the SmartNinja scraper module.
Validates the functionality of the price scraping service.
"""
import logging
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from app.core.interfaces.scraping import IScraperService
from app.core.scraping.bright_data_service import BrightDataScraperService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestScraperService:
    """Test suite for the BrightDataScraperService class"""

    def setup_method(self):
        """Set up the test environment before each test"""
        self.scraper = BrightDataScraperService()

    def test_implements_interface(self):
        """Test that BrightDataScraperService implements IScraperService"""
        assert isinstance(
            self.scraper, IScraperService
        ), "BrightDataScraperService should implement IScraperService"

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_get_prices_valid_parameters(self, mock_service):
        """Test getting prices with valid parameters"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"

        # Configure mock to return test data
        mock_data = [
            {
                "name": "iPhone 15 Pro",
                "price": 999.99,
                "currency": "USD",
                "source": "TestStore",
                "link": "https://example.com/iphone15",
                "date": "2023-09-22",
                "country": "US"
            }
        ]
        mock_service.return_value = {"data": mock_data, "status": "success"}

        # Act - Call the async method
        result = await self.scraper.get_prices(model, country)

        # Assert - Verify results
        assert isinstance(result, list), "Result should be a list"
        assert len(result) > 0, "Result should not be empty"

        # Check the first result as a sample
        first_result = result[0]
        assert isinstance(first_result, dict), "Each item should be a dictionary"
        # Required fields
        assert "name" in first_result, "Each result should have a name"
        assert "price" in first_result, "Each result should have a price"
        assert "currency" in first_result, "Each result should have a currency"
        assert "source" in first_result, "Each result should have a source"
        assert "link" in first_result, "Each result should have a link"
        assert "date" in first_result, "Each result should have a date"
        assert "country" in first_result, "Each result should have a country"

    @pytest.mark.asyncio
    async def test_validation_success_via_get_prices(self):
        """Test that valid parameters pass validation in get_prices"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"

        # Mock the service to avoid real network calls
        with patch('app.mcp.scrape_prices.service.scrape_prices_service') as mock_service:
            # Configure mock to return test data
            mock_service.return_value = {"data": [], "status": "success"}

            # Act - Should not raise exception
            await self.scraper.get_prices(model, country)

            # Assert - Just verify the mock was called with the right parameters
            mock_service.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_prices_empty_model(self):
        """Test that empty model raises ValueError"""
        with pytest.raises(ValueError):
            await self.scraper.get_prices("", "US")

    @pytest.mark.asyncio
    async def test_get_prices_empty_country(self):
        """Test that empty country raises ValueError"""
        with pytest.raises(ValueError):
            await self.scraper.get_prices("iPhone 15", "")

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_get_prices_exception_handling(self, mock_service):
        """Test handling of unexpected exceptions during price retrieval"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"

        # Configure mock to raise an exception
        mock_service.side_effect = Exception("Test error")

        # Act & Assert - The implementation currently raises RuntimeError when an unexpected error occurs
        with pytest.raises(RuntimeError) as excinfo:
            await self.scraper.get_prices(model, country)

        # Verify the error message
        assert "Failed to scrape prices" in str(excinfo.value)

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_price_variation_across_countries(self, mock_service):
        """Test that prices vary appropriately across different countries"""
        # Arrange
        model = "iPhone 15 Pro"

        # Configure mock to return different prices for different countries
        async def mock_side_effect(payload):
            model = payload["model"]
            country = payload["country"]
            return {
                "data": [{
                    "name": model,
                    "price": 999.99 if country == "us" else 1199.99 if country == "uk" else 899.99,
                    "currency": "USD" if country == "us" else "GBP" if country == "uk" else "BRL",
                    "source": "TestStore",
                    "link": f"https://example.com/{model.lower().replace(' ', '-')}",
                    "date": "2023-09-22",
                    "country": country
                }],
                "status": "success"
            }

        mock_service.side_effect = mock_side_effect

        # Act - Get prices for each country
        us_results = await self.scraper.get_prices(model, "US")
        uk_results = await self.scraper.get_prices(model, "UK")
        br_results = await self.scraper.get_prices(model, "BR")

        # Calculate average prices
        avg_us_price = sum(result["price"] for result in us_results) / len(us_results)
        avg_uk_price = sum(result["price"] for result in uk_results) / len(uk_results)

        # Assert - UK prices should be higher than US (as configured in our mock)
        assert avg_uk_price > avg_us_price

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_currency_mapping(self, mock_service):
        """Test that currencies are correctly mapped to countries"""
        # Arrange - Configure mock to return country-specific currencies
        async def get_mock_data(payload):
            model = payload["model"]
            country = payload["country"]
            currency_map = {
                "us": "USD",
                "uk": "GBP",
                "br": "BRL",
                "fr": "EUR"
            }
            return {
                "data": [{
                    "name": model,
                    "price": 999.99,
                    "currency": currency_map.get(country, "USD"),
                    "source": "TestStore",
                    "link": f"https://example.com/{model.lower().replace(' ', '-')}",
                    "date": "2023-09-22",
                    "country": country
                }],
                "status": "success"
            }

        mock_service.side_effect = get_mock_data

        # Act - Get results for different countries
        us_result = (await self.scraper.get_prices("iPhone 15", "US"))[0]
        uk_result = (await self.scraper.get_prices("iPhone 15", "UK"))[0]
        br_result = (await self.scraper.get_prices("iPhone 15", "BR"))[0]
        fr_result = (await self.scraper.get_prices("iPhone 15", "FR"))[0]

        # Assert - Check that currencies match expected values
        assert us_result["currency"] == "USD"
        assert uk_result["currency"] == "GBP"
        assert br_result["currency"] == "BRL"
        assert fr_result["currency"] == "EUR"

    @pytest.mark.asyncio
    @patch('app.mcp.scrape_prices.service.scrape_prices_service')
    async def test_unknown_country_defaults(self, mock_service):
        """Test that unknown countries get default values"""
        # Arrange
        unknown_country = "ZZ"  # A country code that doesn't exist
        model = "iPhone 15"

        # Configure mock to return a response with USD as currency
        mock_service.return_value = {
            "data": [{
                "name": model,
                "price": 999.99,
                "currency": "USD",  # Default currency for unknown country
                "source": "TestStore",
                "link": f"https://example.com/{model.lower().replace(' ', '-')}",
                "date": "2023-09-22",
                "country": unknown_country
            }],
            "status": "success"
        }

        # Act
        results = await self.scraper.get_prices(model, unknown_country)

        # Assert - Should have results with default USD currency
        assert len(results) > 0
        assert results[0]["currency"] == "USD"  # Default currency


if __name__ == "__main__":
    pytest.main(["-v", "test_scraper.py"])
