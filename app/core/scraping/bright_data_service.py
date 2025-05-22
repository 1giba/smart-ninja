"""
Real scraper service implementation for SmartNinja using direct async MCP services.

This module provides a production-ready implementation of the IScraperService 
interface that uses our async MCP services for scraping. It follows asynchronous patterns
and properly handles errors and edge cases.
"""
import logging
from typing import Any, Dict, List

from app.core.interfaces.scraping import IScraperService
# Importação movida para dentro dos métodos para evitar circular import
# from app.mcp.scrape_prices import scrape_prices_service

# Configure logger
logger = logging.getLogger(__name__)


class BrightDataScraperService(IScraperService):
    """
    Production implementation of the scraper service using direct async MCP services.
    
    This class implements the IScraperService interface and uses the
    scrape_prices_service to fetch price data without HTTP overhead.
    """

    def __init__(self, num_results: int = 5):
        """
        Initialize the scraper service.
        
        Args:
            num_results: Target number of results to return per request
        """
        self.num_results = num_results
        logger.info(
            "BrightDataScraperService initialized to target %s results per query",
            num_results,
        )

    async def get_prices(self, model: str, country: str) -> List[Dict[str, Any]]:
        """
        Get price data for a specific phone model and country using direct async MCP services.
        
        Args:
            model: The phone model to search for (e.g., "iPhone 15")
            country: The country to search prices in (e.g., "US", "BR")
            
        Returns:
            List of dictionaries containing normalized price data
            
        Raises:
            ValueError: If input parameters are invalid
            RuntimeError: If something goes wrong during scraping
        """
        # Validate parameters
        self._validate_parameters(model, country)
        
        try:
            # Log the request
            logger.info(f"Getting prices for {model} in {country}")
            
            # Prepare request payload
            payload = {
                "model": model,
                "country": country.lower()
            }
            
            # Importar o serviço localmente para evitar circular import
            from app.mcp.scrape_prices.service import scrape_prices_service
            
            # Call the MCP service directly
            result = await scrape_prices_service(payload)
            
            if result.get("status") != "success":
                error_message = result.get("message", "Unknown error")
                logger.error(f"Error from scrape_prices_service: {error_message}")
                raise RuntimeError(f"Failed to scrape prices: {error_message}")
            
            # Extract and limit the results
            price_data = result.get("data", [])
            results = price_data[:self.num_results] if price_data else []
            
            # Log the result count
            logger.info(f"Found {len(results)} results for {model} in {country}")
            
            return results
            
        except Exception as e:
            # Handle errors cleanly
            logger.error(f"Error scraping prices: {str(e)}")
            raise RuntimeError(f"Failed to scrape prices: {str(e)}")

    def _validate_parameters(self, model: str, country: str) -> None:
        """
        Validate input parameters.
        
        Args:
            model: The phone model to validate
            country: The country code to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        if not model or len(model) < 2:
            raise ValueError("Model name must be at least 2 characters long")
            
        if not country or len(country) < 2:
            raise ValueError("Country code must be at least 2 characters long")
