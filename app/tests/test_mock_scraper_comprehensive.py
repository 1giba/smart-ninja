"""
Comprehensive tests for the MockPriceScraper and MockScraperService components.
These tests ensure that the mock scraper implementations function correctly
and maintain compatibility with their interfaces. This follows the test-first
approach specified in the development rules.
"""
import asyncio
import logging
from unittest.mock import patch, AsyncMock

import pytest

# pylint: disable=protected-access,attribute-defined-outside-init,no-name-in-module
from app.core.interfaces.scraping import IPriceScraper, IScraperService
from app.core.scraping.mock_scraper import MockPriceScraper, MockScraperService

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestMockPriceScraper:
    """Test suite for the MockPriceScraper implementation"""

    def setup_method(self):
        """Set up the test environment before each test"""
        self.scraper = MockPriceScraper()

    def test_implements_interface(self):
        """Test that MockPriceScraper implements IPriceScraper interface"""
        assert isinstance(self.scraper, IPriceScraper)

    @pytest.mark.asyncio
    async def test_scrape_prices_basic(self):
        """Test basic functionality of scrape_prices method"""
        model = "iPhone 15"
        region = "US"
        results = await self.scraper.scrape_prices(model, region)
        
        # Verify results is a non-empty list
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check the first result
        result = results[0]
        
        # Verify structure
        assert isinstance(result, dict)
        # Check required fields
        assert "title" in result, "Result should have a title"
        assert "price" in result, "Result should have a price"
        assert "currency" in result, "Result should have a currency"
        assert "url" in result, "Result should have a URL"
        assert "store" in result, "Result should have a store"
        assert "date" in result, "Result should have a date"
        
        # Check values
        assert model in result["title"], "Title should contain model name"
        assert isinstance(result["price"], float), "Price should be a float"
        assert result["price"] > 0, "Price should be positive"
        assert isinstance(result["currency"], str), "Currency should be a string"
        assert isinstance(result["date"], str), "Date should be a string"
        assert isinstance(result["store"], str), "Store should be a string"

    @pytest.mark.asyncio
    async def test_scrape_prices_different_models(self):
        """Test that different models produce different prices"""
        region = "US"
        iphone_results = await self.scraper.scrape_prices("iPhone 15", region)
        samsung_results = await self.scraper.scrape_prices("Samsung Galaxy S24", region)
        pixel_results = await self.scraper.scrape_prices("Google Pixel 8", region)
        
        # Ensure all result lists are non-empty
        assert iphone_results and samsung_results and pixel_results
        
        # Get the first result from each list for comparison
        iphone_result = iphone_results[0]
        samsung_result = samsung_results[0]
        pixel_result = pixel_results[0]

        # Prices should be different for different models
        assert iphone_result["price"] != samsung_result["price"]
        assert iphone_result["price"] != pixel_result["price"]
        assert samsung_result["price"] != pixel_result["price"]

        # Currency should be the same for the same region
        assert iphone_result["currency"] == samsung_result["currency"]

        # Each result should follow the expected price ranges
        for result in [iphone_result, samsung_result, pixel_result]:
            assert 300 <= result["price"] <= 2000, f"Price {result['price']} outside expected range"

    @pytest.mark.asyncio
    async def test_scrape_prices_different_regions(self):
        """Test that different regions produce different prices or currencies"""
        model = "iPhone 15"  # Keep model constant
        us_results = await self.scraper.scrape_prices(model, "US")
        eu_results = await self.scraper.scrape_prices(model, "EU")
        jp_results = await self.scraper.scrape_prices(model, "JP")
        
        # Ensure all result lists are non-empty
        assert us_results and eu_results and jp_results
        
        # Get the first result from each list for comparison
        us_result = us_results[0]
        eu_result = eu_results[0]
        jp_result = jp_results[0]
        # Currencies should be different by region
        assert us_result["currency"] != eu_result["currency"], "US and EU should have different currencies"
        
        # All should have valid prices
        for r in [us_result, eu_result, jp_result]:
            assert 300 <= r["price"] <= 2000, f"Price {r['price']} outside expected range"
            
        # Model name should be in all titles
        assert model in us_result["title"]
        assert model in eu_result["title"]
        assert model in jp_result["title"]

    def test_get_mock_price(self):
        """Test the _get_mock_price method"""
        # Test with iPhone model
        iphone_price = self.scraper._get_mock_price("iPhone 15", "US")
        assert isinstance(iphone_price, float)
        assert iphone_price > 0
        # Test with Samsung model
        samsung_price = self.scraper._get_mock_price("Samsung Galaxy S24", "US")
        assert isinstance(samsung_price, float)
        assert samsung_price > 0
        # Test with unknown model (should use default price)
        unknown_price = self.scraper._get_mock_price("Unknown Model", "US")
        assert isinstance(unknown_price, float)
        assert unknown_price > 0
        # Test different regions
        us_price = self.scraper._get_mock_price("iPhone 15", "US")
        eu_price = self.scraper._get_mock_price("iPhone 15", "EU")
        # Prices should be different based on region
        assert abs(us_price - eu_price) > 0.01

    def test_get_currency_for_region(self):
        """Test the _get_currency_for_region method"""
        # Test common regions
        assert self.scraper._get_currency_for_region("US") == "USD"
        assert self.scraper._get_currency_for_region("EU") == "EUR"
        assert self.scraper._get_currency_for_region("UK") == "GBP"
        # Test fallback for unknown region
        assert isinstance(self.scraper._get_currency_for_region("ZZ"), str)
        assert (
            len(self.scraper._get_currency_for_region("ZZ")) == 3
        )  # Currency codes are 3 chars

    def test_get_random_source(self):
        """Test the _get_random_source method"""
        # Test that we get a string
        source = self.scraper._get_random_source()
        assert isinstance(source, str)
        assert len(source) > 0
        # Test that we can get different sources
        sources = [self.scraper._get_random_source() for _ in range(10)]
        assert len(set(sources)) > 1  # At least some should be different

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in scrape_prices method"""
        # Create an async mock that raises an exception
        async def mock_error(*args, **kwargs):
            raise Exception("Test error")
            
        # Patch the internal method with our async mock
        with patch.object(MockPriceScraper, "_get_mock_price", side_effect=mock_error):
            # Should raise an exception with our error message
            with pytest.raises(Exception) as excinfo:
                await self.scraper.scrape_prices("iPhone 15", "US")
            
            # Verify the error message
            assert "Error generating mock price data" in str(excinfo.value)


class TestMockScraperService:
    """Test suite for the MockScraperService implementation"""

    def setup_method(self):
        """Set up the test environment before each test"""
        self.service = MockScraperService(num_results=5)

    def test_implements_interface(self):
        """Test that MockScraperService implements IScraperService interface"""
        assert isinstance(self.service, IScraperService)

    def test_initialization(self):
        """Test initialization of MockScraperService"""
        # Default initialization
        service = MockScraperService()
        assert hasattr(service, "scraper")
        assert isinstance(service.scraper, MockPriceScraper)
        assert hasattr(service, "num_results")
        # Custom initialization
        custom_service = MockScraperService(num_results=10)
        assert custom_service.num_results == 10

    def test_validate_parameters_valid(self):
        """Test validate_parameters with valid inputs"""
        # These should not raise exceptions
        self.service._validate_parameters("iPhone 15", "US")
        self.service._validate_parameters("Samsung Galaxy S24", "EU")

    def test_validate_parameters_invalid(self):
        """Test validate_parameters with invalid inputs"""
        # Test with empty model
        with pytest.raises(ValueError) as excinfo:
            self.service._validate_parameters("", "US")
        assert "model" in str(excinfo.value).lower()
        # Test with None model
        with pytest.raises(ValueError) as excinfo:
            self.service._validate_parameters(None, "US")
        assert "model" in str(excinfo.value).lower()
        # Test with empty country
        with pytest.raises(ValueError) as excinfo:
            self.service._validate_parameters("iPhone 15", "")
        assert "country" in str(excinfo.value).lower()
        # Test with None country
        with pytest.raises(ValueError) as excinfo:
            self.service._validate_parameters("iPhone 15", None)
        assert "country" in str(excinfo.value).lower()

    @pytest.mark.asyncio
    async def test_generate_mock_results(self):
        """Test _generate_mock_results method"""
        model = "iPhone 15"
        country = "US"
        # Default number of results
        results = await self.service._generate_mock_results(model, country)
        assert isinstance(results, list)
        assert len(results) > 0
        # Check first result structure
        first_result = results[0]
        assert isinstance(first_result, dict)
        assert "title" in first_result
        assert "price" in first_result
        assert "currency" in first_result
        assert "url" in first_result
        # Check that the model appears in the title
        assert model in first_result["title"]

    @pytest.mark.asyncio
    async def test_get_prices(self):
        """Test the get_prices method"""
        model = "iPhone 15"
        country = "US"
        
        # Create a mock scraper that returns predictable results with expected fields
        sample_results = [
            {"title": f"{model} Sample {i}", "price": 999.99, "currency": "USD", 
             "url": "https://example.com/sample", "store": "SampleStore", 
             "date": "2023-01-01"} 
            for i in range(self.service.num_results)  # Match exactly what we need
        ]
        
        # Create an async mock that returns our sample
        async def mock_scrape(*args, **kwargs):
            return sample_results
            
        # Patch the scraper to use our mock
        with patch.object(self.service.scraper, "scrape_prices", side_effect=mock_scrape):
            results = await self.service.get_prices(model, country)
            
            # Check structure and content
            assert isinstance(results, list)
            # Verify we get the same number of results we put in
            assert len(results) == len(sample_results)
            
            for result in results:
                assert isinstance(result, dict)
                assert "title" in result, "Result should have a title"
                assert model in result["title"], "Title should contain model name"
                assert "price" in result, "Result should have a price"
                assert "currency" in result, "Result should have a currency"
                assert "url" in result, "Result should have a URL"
                assert "store" in result, "Result should have a store"
                assert "date" in result, "Result should have a date"
                
                # The MockScraperService also adds these fields
                assert "availability" in result
                assert "condition" in result
                
                assert isinstance(result["price"], float), "Price should be a float"
                assert result["price"] > 0, "Price should be positive"
                assert isinstance(result["currency"], str), "Currency should be a string"

    @pytest.mark.asyncio
    async def test_get_prices_validation_error(self):
        """Test get_prices with validation error"""
        # Test with empty model
        with pytest.raises(ValueError, match="Phone model cannot be empty"):
            await self.service.get_prices("", "US")
        # Test with empty country
        with pytest.raises(ValueError, match="Country cannot be empty"):
            await self.service.get_prices("iPhone 15", "")

    @pytest.mark.asyncio
    async def test_get_prices_scraping_error(self):
        """Test get_prices with scraping error"""
        # Mock the scrape_prices method to raise an exception
        async def mock_error(*args, **kwargs):
            raise Exception("Test error")
            
        # Patch the scraper's method
        with patch.object(self.service.scraper, "scrape_prices", side_effect=mock_error):
            # Should raise a RuntimeError from get_prices
            with pytest.raises(RuntimeError) as excinfo:
                await self.service.get_prices("iPhone 15", "US")
            # The error message should contain our test error
            assert "Failed to fetch prices" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_different_num_results(self):
        """Test that the same scraper can be reused with different services"""
        # In a real application, we might have different services configured differently
        # but reusing the same scraper
        
        # Create mock results for our test
        sample_results = [
            {"title": f"iPhone 15 Variant {i}", "price": 999.99, "currency": "USD", 
             "url": "https://example.com/sample", "store": "SampleStore", 
             "date": "2023-01-01"} 
            for i in range(10)  # Create a set number of results
        ]
        
        # Mock the scraper's scrape_prices method to return consistent results
        async def mock_scrape(*args, **kwargs):
            # For testing purposes, return the fixed sample results
            return sample_results
        
        # Create two separate service instances
        service1 = MockScraperService()
        service2 = MockScraperService()
        
        # They should be different instances
        assert service1 is not service2
        
        # Patch the scraper's method for consistent test results
        with patch.object(MockPriceScraper, "scrape_prices", side_effect=mock_scrape):
            # Both services should return results in the same format
            results1 = await service1.get_prices("iPhone 15", "US")
            results2 = await service2.get_prices("iPhone 15", "US")
            
            # Both should return the same number of results (from our mock)
            assert len(results1) == len(sample_results)
            assert len(results2) == len(sample_results)
            
            # Both results should have the expected structure (as processed by MockScraperService)
            for result in results1 + results2:
                assert "title" in result
                assert "price" in result
                assert "currency" in result
                assert "availability" in result  # Added by MockScraperService
                assert "condition" in result     # Added by MockScraperService


if __name__ == "__main__":
    pytest.main(["-v", "test_mock_scraper_comprehensive.py"])
