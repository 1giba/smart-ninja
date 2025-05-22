"""
Scraping module for SmartNinja application.
Provides an asynchronous function to fetch mobile phone prices from various sources.
Implements modern async operations for better performance and compatibility with MCP services.
"""
import asyncio
import logging
import os
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from dotenv import load_dotenv

from app.core.constants import BASE_PRICES, REGION_MULTIPLIERS
from app.core.scraping.bright_data_scraper import BrightDataPriceScraper

# Configure logger
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration for scraping operations
SCRAPING_TIMEOUT = int(os.getenv("SCRAPING_TIMEOUT", "30"))


class MockDataGenerator:
    """
    Utility class for generating mock smartphone price data.
    Used for testing and development when real data is not available.
    """

    @staticmethod
    def generate_mock_results(model: str, country: str) -> List[Dict]:
        """
        Generate mock price results for testing and development.

        Args:
            model: The phone model to generate data for
            country: The country to simulate prices for

        Returns:
            List of dictionaries containing simulated price data
        """
        # Normalize country to lowercase for consistency
        country = country.lower()
        
        # Validation
        if not model or not country:
            raise ValueError("Model and country must be provided")
            
        # Mock data generation logic
        sources = ["Amazon", "BestBuy", "Walmart", "eBay", "TechStore"]
        results = []
        timestamp = datetime.now().strftime("%Y-%m-%d")
        
        # Get base price for model or use default
        base_price = BASE_PRICES.get(model.lower(), 999.99)
        
        # Get region multiplier or use default
        region_multiplier = REGION_MULTIPLIERS.get(country, 1.0)
        
        # Generate a result for each source with variation
        for source in sources:
            # Add random variation to price
            variation = random.uniform(0.9, 1.1)
            price = base_price * region_multiplier * variation
            
            # Create mock result
            result = {
                "price": round(price, 2),
                "store": source,
                "region": country,
                "model": model,
                "currency": "USD" if country == "us" else country.upper(),
                "timestamp": timestamp,
                "url": f"https://{source.lower()}.com/product/{model.lower().replace(' ', '-')}",
            }
            results.append(result)
            
        return results


async def scrape_mobile_prices_async(model: str, country: str) -> List[Dict]:
    """
    Asynchronous function for scraping mobile prices.
    This function is the main entry point for external modules and the MCP service
    to access the scraping functionality.

    Args:
        model: Mobile phone model to search for
        country: Country code for regional pricing

    Returns:
        List of dictionaries containing price information

    Example:
        >>> import asyncio
        >>> results = asyncio.run(scrape_mobile_prices_async("iPhone 15", "us"))
        >>> print(f"Found {len(results)} results")
    """
    try:
        logger.info(f"Asynchronously scraping prices for {model} in {country}")
        
        # Try to use BrightDataPriceScraper if environment variables are available
        try:
            scraper = BrightDataPriceScraper()
            results = await scraper.scrape_prices(model, country, SCRAPING_TIMEOUT)
            logger.info(f"Retrieved {len(results)} real price results for {model}")
            return results
        except (ValueError, Exception) as e:
            # Log the error but continue with mock data
            logger.warning(f"Could not use BrightDataPriceScraper: {str(e)}")
            logger.info("Falling back to mock data generation")
            
        # Generate mock data as fallback
        mock_results = MockDataGenerator.generate_mock_results(model, country)
        logger.info(f"Generated {len(mock_results)} mock price results for {model}")
        return mock_results
    except Exception as e:
        logger.error(f"Error in async mobile price scraping: {str(e)}")
        # Return empty list on error to avoid breaking callers
        return []
