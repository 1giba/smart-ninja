"""
Scraping interfaces for the SmartNinja application.
These interfaces define the contracts that scrapers must implement.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


# pylint: disable=too-few-public-methods
class IPriceScraper(ABC):
    """
    Interface for price scrapers that fetch individual price data.
    Implementations of this interface should handle the details of
    scraping from specific sources.
    """

    @abstractmethod
    async def scrape_prices(self, phone_model: str, region: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """
        Asynchronously scrape prices for a specific phone model and region
        
        Args:
            phone_model: The phone model to scrape
            region: The region to scrape from
            timeout: Maximum time in seconds to wait for scraping to complete
            
        Returns:
            List of dictionaries containing scraped price data
            
        Raises:
            TimeoutError: If the scraping operation exceeds the timeout
            ValueError: If credentials or parameters are invalid
            ConnectionError: If there's a network issue
        """


# pylint: disable=too-few-public-methods
class IScraperService(ABC):
    """
    Interface for scraper services that orchestrate multiple scrapers.
    Implementations of this interface should handle validating inputs,
    aggregating results, and error handling.
    """

    @abstractmethod
    async def get_prices(self, model: str, country: str) -> List[Dict[str, Any]]:
        """
        Asynchronously get price data for a specific phone model and country from multiple sources
        
        Args:
            model: The phone model to search for (e.g., "iPhone 15")
            country: The country to search prices in (e.g., "US", "BR")
            
        Returns:
            List of dictionaries containing phone offers with price information
            
        Raises:
            ValueError: If model or country parameters are invalid
            RuntimeError: If scraping fails
        """


# pylint: disable=too-few-public-methods
class IPriceAnalyzer(ABC):
    """
    Interface for price analyzers that analyze price data to provide insights.
    Implementations of this interface should handle analyzing price trends,
    identifying opportunities, and generating recommendations.
    """

    @abstractmethod
    async def analyze_market(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Asynchronously analyze market data to provide insights
        
        Args:
            price_data: List of price data dictionaries
            
        Returns:
            Analysis text with insights about the price data
            
        Raises:
            Exception: If analysis fails
        """
