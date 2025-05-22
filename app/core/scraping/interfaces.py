"""
Interfaces for the price scraping functionality.

This module defines the interfaces used in the scraping module
to enable dependency injection and better testability.
Includes asynchronous interfaces to support concurrent operations.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PriceScraper(ABC):
    """Interface for price scraping components."""

    @abstractmethod
    async def scrape_prices(
        self, model: str, country: str = "us", timeout: Optional[int] = 30
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously scrape prices for a given smartphone model in a specific country.

        Args:
            model: Smartphone model to search for
            country: Country code for regional pricing
            timeout: Maximum time in seconds to wait for scraping to complete

        Returns:
            List of dictionaries containing scraped price data

        Raises:
            TimeoutError: If the scraping operation exceeds the timeout
            ValueError: If parameters are invalid
            ConnectionError: If there's a network issue
        """
        pass


class ResultNormalizer(ABC):
    """Interface for normalizing scraping results."""

    @abstractmethod
    async def normalize_results(
        self, results: List[Dict[str, Any]], model: str, country: str
    ) -> List[Dict[str, Any]]:
        """
        Asynchronously normalize and deduplicate scraped results.

        Args:
            results: Raw scraped results
            model: Model that was searched for
            country: Country code that was used

        Returns:
            List of normalized price entries

        Raises:
            ValueError: If the results cannot be normalized
        """
        pass


class ScrapingErrorHandler(ABC):
    """Interface for handling scraping errors."""

    @abstractmethod
    async def handle_error(
        self, error: Exception, model: str, country: str
    ) -> Dict[str, Any]:
        """
        Asynchronously handle errors during the scraping process.

        Args:
            error: The exception that was raised
            model: Model that was searched for
            country: Country code that was used

        Returns:
            Dictionary with error information and standardized error response
        """
        pass
