"""
Tests for the MockPriceScraper and MockScraperService implementations.
Ensures that mock implementations correctly follow the defined interfaces.
"""
import asyncio
import logging
import re
from unittest.mock import patch

import pytest

# pylint: disable=protected-access,attribute-defined-outside-init,invalid-name,unused-import,no-name-in-module
from app.core.interfaces.scraping import IPriceScraper, IScraperService
from app.core.scraping.mock_scraper import MockPriceScraper, MockScraperService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestMockPriceScraper:
    """Test suite for the MockPriceScraper class"""

    def setup_method(self):
        """Set up the test environment before each test"""
        self.scraper = MockPriceScraper()

    def test_implements_interface(self):
        """Test that MockPriceScraper implements IPriceScraper interface"""
        assert isinstance(
            self.scraper, IPriceScraper
        ), "MockPriceScraper deve implementar IPriceScraper"

    @pytest.mark.asyncio
    async def test_scrape_prices_structure(self):
        """Test structure of price data returned by scrape_prices"""
        # Arrange
        phone_model = "iPhone 15 Pro"
        region = "US"
        # Act
        results = await self.scraper.scrape_prices(phone_model, region)
        # Assert
        assert isinstance(results, list), "Results should be a list"
        assert len(results) > 0, "Results should not be empty"
        
        # Check the first result structure
        result = results[0]
        assert isinstance(result, dict), "Each result should be a dictionary"
        assert "title" in result, "Result should have a title"
        assert "price" in result, "Result should have a price"
        assert "currency" in result, "Result should have a currency"
        assert "url" in result, "Result should have a URL"
        assert "store" in result, "Result should have a store"
        assert "date" in result, "Result should have a date"
        
        assert isinstance(result["price"], float)
        assert isinstance(result["currency"], str)
        assert isinstance(result["store"], str)

    @pytest.mark.asyncio
    async def test_scrape_prices_different_regions(self):
        """Test price differences between regions"""
        # Arrange
        phone_model = "iPhone 15 Pro"
        regions = ["US", "EU", "BR", "UK"]
        # Act
        results = {}
        for region in regions:
            region_results = await self.scraper.scrape_prices(phone_model, region)
            results[region] = region_results[0] if region_results else None
            
        # Assert
        # Check that all regions returned results
        assert all(results.values()), "All regions should return results"
        
        # Check that prices vary by region
        prices = [results[region]["price"] for region in regions]
        assert len(set(prices)) > 1, "Prices should vary by region"
        
        # Check that currencies are different by region
        currencies = {results[region]["currency"] for region in regions}
        assert len(currencies) > 1, "Moedas devem variar por região"

    def test_get_mock_price(self):
        """Test the _get_mock_price internal method"""
        # Arrange
        phone_model = "iPhone 15 Pro"
        region = "US"
        # Act
        price = self.scraper._get_mock_price(phone_model, region)
        # Assert
        assert isinstance(price, float)
        assert price > 0
        # Test with unknown model (should use default)
        unknown_price = self.scraper._get_mock_price("Unknown Model", region)
        assert isinstance(unknown_price, float)
        assert unknown_price > 0

    def test_get_currency_for_region(self):
        """Test the _get_currency_for_region internal method"""
        # Test common regions
        assert self.scraper._get_currency_for_region("US") == "USD"
        assert self.scraper._get_currency_for_region("EU") == "EUR"
        assert self.scraper._get_currency_for_region("UK") == "GBP"
        # Test with unknown region (should default to USD)
        assert self.scraper._get_currency_for_region("XYZ") == "USD"

    def test_get_random_source(self):
        """Test the _get_random_source internal method"""
        # Should return a non-empty string
        source = self.scraper._get_random_source()
        assert isinstance(source, str)
        assert len(source) > 0
        # Test multiple calls to ensure randomness
        sources = {self.scraper._get_random_source() for _ in range(10)}
        assert len(sources) > 1, "Sources should vary with multiple calls"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in scrape_prices"""
        # Arrange
        phone_model = "iPhone 15 Pro"
        region = "US"
        
        # Create an async mock that raises an exception
        async def mock_error(*args, **kwargs):
            raise Exception("Test error")
        
        # Mock the scraper's method to raise an exception
        with patch.object(MockPriceScraper, "_get_mock_price", side_effect=mock_error):
            # Act & Assert
            with pytest.raises(Exception) as excinfo:
                await self.scraper.scrape_prices(phone_model, region)
            # Check that error message contains our test message
            assert "Error generating mock price data" in str(excinfo.value)


class TestMockScraperService:
    """Test suite for the MockScraperService class"""

    def setup_method(self):
        """Set up the test environment before each test"""
        self.service = MockScraperService()

    def test_implements_interface(self):
        """Test that MockScraperService implements IScraperService interface"""
        assert isinstance(
            self.service, IScraperService
        ), "MockScraperService must implement IScraperService"

    def test_init_with_num_results(self):
        """Test initialization with custom number of results"""
        # Arrange & Act
        service_with_custom_results = MockScraperService(num_results=10)
        # Assert
        assert service_with_custom_results.num_results == 10
        # Test with default num_results
        assert self.service.num_results == 5

    @pytest.mark.asyncio
    async def test_get_prices(self):
        """Test the get_prices method returns appropriate structure"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"
        
        # Create mock results for consistent testing
        sample_results = [
            {"title": f"{model} Sample {i}", "price": 999.99, "currency": "USD", 
             "url": "https://example.com/sample", "store": "SampleStore", 
             "date": "2023-01-01"} 
            for i in range(self.service.num_results)
        ]
        
        # Create an async mock that returns our sample
        async def mock_scrape(*args, **kwargs):
            return sample_results
            
        # Patch the scraper to use our mock
        with patch.object(self.service.scraper, "scrape_prices", side_effect=mock_scrape):
            # Act
            results = await self.service.get_prices(model, country)
            
            # Assert
            assert isinstance(results, list)
            assert len(results) == len(sample_results)
            
            # Check structure of results
            for result in results:
                assert isinstance(result, dict)
                # Check required fields based on the actual implementation
                assert "title" in result, "Result should have a title"
                assert "price" in result, "Result should have a price"
                assert "currency" in result, "Result should have a currency"
                assert "url" in result, "Result should have a URL"
                assert "store" in result, "Result should have a store"
                assert "date" in result, "Result should have a date"
                
                # The MockScraperService adds these additional fields
                assert "availability" in result, "Result should have availability"
                assert "condition" in result, "Result should have condition"
                
                assert model in result["title"], "Title should contain model name"
                assert isinstance(result["price"], float), "Price should be a float"
                assert isinstance(result["currency"], str), "Currency should be a string"
                assert isinstance(result["store"], str), "Store should be a string"

    def test_validate_parameters(self):
        """Test parameter validation in _validate_parameters"""
        # Valid parameters should not raise exception
        try:
            self.service._validate_parameters("iPhone 15 Pro", "US")
        except ValueError:
            pytest.fail("_validate_parameters failed with valid parameters")
        # Test with empty model
        with pytest.raises(ValueError, match="Phone model cannot be empty"):
            self.service._validate_parameters("", "US")
        # Test with None model
        with pytest.raises(ValueError, match="Phone model cannot be empty"):
            self.service._validate_parameters(None, "US")
        # Test with empty country
        with pytest.raises(ValueError, match="Country cannot be empty"):
            self.service._validate_parameters("iPhone 15 Pro", "")
        # Test with None country
        with pytest.raises(ValueError, match="Country cannot be empty"):
            self.service._validate_parameters("iPhone 15 Pro", None)

    @pytest.mark.asyncio
    async def test_generate_mock_results(self):
        """Test the _generate_mock_results internal method"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"
        
        # Create sample results for the scraper to return
        sample_results = [
            {"title": f"{model} Test {i}", "price": 999.99, "currency": "USD",
             "url": "https://example.com/test", "store": "TestStore",
             "date": "2023-01-01"}
            for i in range(5)
        ]
        
        # Create an async mock for the scraper
        async def mock_scrape(*args, **kwargs):
            return sample_results
        
        # Patch the scraper's method
        with patch.object(self.service.scraper, "scrape_prices", side_effect=mock_scrape):
            # Act - call the async method
            results = await self.service._generate_mock_results(model, country)
            
            # Assert
            assert isinstance(results, list)
            assert len(results) > 0
            
            # Check the structure of the results
            for result in results:
                assert isinstance(result, dict)
                # These fields come from our mock
                assert "title" in result
                assert "price" in result
                assert "currency" in result
                assert "url" in result
                assert "store" in result
                
                # These fields are added by the service
                assert "availability" in result, "Field availability not found"
                assert "condition" in result, "Field condition not found"
                
                # Type checking
                assert isinstance(result["price"], float)
                assert isinstance(result["currency"], str)

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in get_prices"""
        # Arrange
        model = "iPhone 15 Pro"
        country = "US"
        
        # Test with _validate_parameters raising exception
        with patch.object(
            self.service,
            "_validate_parameters",
            side_effect=ValueError("Test validation error"),
        ):
            with pytest.raises(ValueError) as excinfo:
                await self.service.get_prices(model, country)
            assert "Test validation error" in str(excinfo.value)
        
        # Create an async mock that raises an exception
        async def mock_error(*args, **kwargs):
            raise Exception("Test generation error")
        
        # Test with _generate_mock_results raising exception
        with patch.object(
            self.service,
            "_generate_mock_results",
            side_effect=mock_error,
        ):
            with pytest.raises(RuntimeError) as excinfo:
                await self.service.get_prices(model, country)
            assert "Failed to fetch prices" in str(excinfo.value)


if __name__ == "__main__":
    pytest.main(["-v", "test_mock_scraper.py"])
