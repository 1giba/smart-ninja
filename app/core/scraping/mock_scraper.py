"""
Mock scraper implementation for the SmartNinja application.
This module provides mock implementations of the scraping interfaces for development
and testing purposes. In production, these would be replaced with real implementations
that use Bright Data or other scraping services.
"""
import asyncio
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.constants import BASE_PRICES, REGION_MULTIPLIERS
from app.core.interfaces.scraping import IPriceScraper, IScraperService

# Configure logger
logger = logging.getLogger(__name__)


class MockPriceScraper(IPriceScraper):
    """
    Mock implementation of a price scraper that generates random price data.
    This class implements the IPriceScraper interface and is used for development
    and testing purposes. It generates mock price data that simulates what would
    be returned by a real scraping service.
    """

    def __init__(self):
        """Initialize the mock price scraper"""
        logger.debug("Initializing MockPriceScraper")

    async def scrape_prices(self, phone_model: str, region: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """
        Asynchronously scrape mock prices for a specific phone model and region.
        
        Args:
            phone_model: The phone model to generate data for
            region: The region to generate price for
            timeout: Maximum time to wait (for interface compatibility)
            
        Returns:
            List of dictionaries containing mock price data
            
        Raises:
            TimeoutError: If the operation times out (simulated)
            ValueError: If parameters are invalid
            ConnectionError: If there's a simulated network issue
        """
        try:
            logger.debug("Generating mock price data for %s in %s", phone_model, region)
            
            # Simulate async operation with a small delay
            await asyncio.sleep(0.1)
            
            # Simulate timeout if requested (for testing)
            if timeout == 1:  # Special case for testing timeouts
                raise TimeoutError("Simulated timeout for testing")
                
            # Generate 3-5 mock price entries
            results = []
            variants = ["Standard", "Plus", "Pro", "Pro Max", "Ultra"]
            storage_options = ["64GB", "128GB", "256GB", "512GB", "1TB"]
            
            num_results = random.randint(3, 5)
            for i in range(num_results):
                variant = random.choice(variants)
                storage = random.choice(storage_options)
                store = self._get_random_source()
                
                base_price = self._get_mock_price(phone_model, region)
                # Add slight variations for different configurations
                adjusted_price = base_price * (1 + (i * 0.05))
                
                results.append({
                    "title": f"{phone_model} {variant} {storage}",
                    "price": adjusted_price,
                    "currency": self._get_currency_for_region(region),
                    "url": f"https://example.com/{store.lower()}/{phone_model.lower().replace(' ', '-')}",
                    "store": store,
                    "date": datetime.utcnow().strftime("%Y-%m-%d"),
                    "in_stock": random.choice([True, True, True, False]),  # 75% chance of being in stock
                    "rating": round(random.uniform(3.0, 5.0), 1),
                })
                
            return results
            
        except asyncio.TimeoutError:
            logger.error("Mock scraping operation timed out after %s seconds", timeout)
            raise TimeoutError(f"Scraping operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error("Error generating mock price data: %s", str(e))
            raise Exception(
                f"Error generating mock price data: {str(e)}"
            ) from e

    def _get_mock_price(self, phone_model: str, region: str) -> float:
        """
        Generate a mock price based on phone model and region.
        Args:
            phone_model: The phone model to generate price for
            region: The region to adjust price for
        Returns:
            Float price value
        """
        # Use base prices from constants module
        base_prices = BASE_PRICES
        # Default price if model not found
        default_price = 899
        # Use region multipliers from constants module
        region_multipliers = REGION_MULTIPLIERS
        # Get base price, default if not found
        base_price = base_prices.get(phone_model, default_price)
        # Get region multiplier, default to 1.0 if not found
        region_multiplier = region_multipliers.get(region, 1.0)
        # Add some randomness for variation between stores
        random_factor = random.uniform(0.9, 1.1)
        # Calculate final price
        price = base_price * region_multiplier * random_factor
        return round(price, 2)

    def _get_currency_for_region(self, region: str) -> str:
        """
        Get the currency code for a region.
        Args:
            region: The region code
        Returns:
            Currency code as string
        """
        region_currencies = {
            "US": "USD",
            "EU": "EUR",
            "UK": "GBP",
            "JP": "JPY",
            "BR": "BRL",
            "IN": "INR",
            "AU": "AUD",
        }
        return region_currencies.get(region, "USD")

    def _get_random_source(self) -> str:
        """
        Get a random store name as a source.
        Returns:
            Store name as string
        """
        sources = [
            "Amazon",
            "BestBuy",
            "Walmart",
            "eBay",
            "TechStore",
            "Newegg",
            "Target",
            "B&H",
            "Costco",
            "Flipkart",
        ]
        return random.choice(sources)
        
    def _generate_mock_results(self, phone_model: str, region: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Generate a list of mock results for a phone model and region.
        
        Args:
            phone_model: The phone model to generate data for
            region: The region to generate prices for
            count: Number of results to generate
            
        Returns:
            List of dictionaries containing mock price data
        """
        results = []
        variants = ["Standard", "Plus", "Pro", "Pro Max", "Ultra"]
        storage_options = ["64GB", "128GB", "256GB", "512GB", "1TB"]
        
        for i in range(count):
            variant = random.choice(variants)
            storage = random.choice(storage_options)
            store = self._get_random_source()
            
            base_price = self._get_mock_price(phone_model, region)
            # Add slight variations for different configurations
            adjusted_price = base_price * (1 + (i * 0.05))
            
            results.append({
                "title": f"{phone_model} {variant} {storage}",
                "price": adjusted_price,
                "currency": self._get_currency_for_region(region),
                "url": f"https://example.com/{store.lower()}/{phone_model.lower().replace(' ', '-')}",
                "store": store,
                "date": datetime.utcnow().strftime("%Y-%m-%d"),
                "in_stock": random.choice([True, True, True, False]),  # 75% chance of being in stock
                "rating": round(random.uniform(3.0, 5.0), 1),
            })
            
        return results


class MockScraperService(IScraperService):
    """
    Mock implementation of a scraper service that orchestrates price scraping.
    This class implements the IScraperService interface and is used for development
    and testing purposes. It simulates what would be done by a real scraping service,
    including input validation, error handling, and result aggregation.
    """

    def __init__(self, num_results: int = 5):
        """
        Initialize the mock scraper service.
        Args:
            num_results: Number of mock results to generate per request
        """
        self.scraper = MockPriceScraper()
        self.num_results = num_results
        logger.info(
            "MockScraperService initialized to generate %s results per query",
            num_results,
        )

    async def get_prices(self, model: str, country: str) -> List[Dict[str, Any]]:
        """
        Asynchronously get mock price data for a specific phone model and country.
        
        Args:
            model: The phone model to search for (e.g., "iPhone 15")
            country: The country to search prices in (e.g., "US", "BR")
            
        Returns:
            List of dictionaries containing mock price data
            
        Raises:
            ValueError: If input parameters are invalid
            RuntimeError: If something goes wrong during scraping
        """
        try:
            # Validate input parameters
            self._validate_parameters(model, country)
            logger.info("Asynchronously fetching mock prices for %s in %s", model, country)
            
            # Simulate network delay for more realistic async behavior
            await asyncio.sleep(0.2)
            
            # Generate multiple results
            results = await self._generate_mock_results(model, country)
            logger.info(
                "Generated %s mock results for %s in %s", len(results), model, country
            )
            return results
        except ValueError as validation_error:
            logger.error("Validation error: %s", str(validation_error))
            raise
        except Exception as exception:
            logger.error("Error fetching prices: %s", str(exception))
            raise RuntimeError(
                f"Failed to fetch prices: {str(exception)}"
            ) from exception

    def _validate_parameters(self, model: str, country: str) -> None:
        """
        Validate input parameters.
        Args:
            model: The phone model to validate
            country: The country code to validate
        Raises:
            ValueError: If parameters are invalid
        """
        if not model or len(model.strip()) == 0:
            raise ValueError("Phone model cannot be empty")
        if not country or len(country.strip()) == 0:
            raise ValueError("Country cannot be empty")
        # Could add more validation for supported countries, models, etc.

    async def _generate_mock_results(self, model: str, country: str) -> List[Dict[str, Any]]:
        """
        Asynchronously generate multiple mock price results.
        
        Args:
            model: The phone model to generate data for
            country: The country to generate prices for
            
        Returns:
            List of dictionaries containing mock price data
        """
        # Use the scraper to get price data
        base_results = await self.scraper.scrape_prices(model, country, timeout=30)
        
        # Process and enhance the results
        for result in base_results:
            # Add some fields specific to the aggregated results if not already present
            if "timestamp" not in result:
                result["timestamp"] = datetime.utcnow().isoformat()
                
            # Add additional metadata
            result["availability"] = random.choice(
                ["In Stock", "Limited Stock", "Pre-order", "Ships in 1-2 days"]
            )
            result["condition"] = random.choice(
                ["New", "New", "New", "Refurbished", "Open Box"]
            )
            # Update URL if source exists and URL is empty
            if "url" not in result and "source" in result:
                result["url"] = f"https://example.com/{result['source'].lower()}/{model.replace(' ', '-').lower()}"
                
        # Return the enhanced results
        return base_results
