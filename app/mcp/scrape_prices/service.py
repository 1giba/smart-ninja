"""
Smartphone Price Scraping Service.

This module provides asynchronous smartphone price scraping capabilities
using dependency injection and clean architecture principles.
"""
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

from app.core.scraping.bright_data_scraper import BrightDataPriceScraper
from app.core.scraping.error_handler import DefaultScrapingErrorHandler
from app.core.scraping.interfaces import (
    PriceScraper,
    ResultNormalizer,
    ScrapingErrorHandler,
)
from app.core.scraping.normalizer import PriceResultNormalizer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def create_scraping_components() -> Tuple[PriceScraper, ResultNormalizer, ScrapingErrorHandler]:
    """
    Create and configure the components for asynchronous price scraping with dependency injection.

    Returns:
        Tuple containing PriceScraper, ResultNormalizer, and ScrapingErrorHandler instances
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Create components
    try:
        # Check if credentials are available, raise error if not
        if not os.getenv("BRIGHT_DATA_USERNAME") or not os.getenv("BRIGHT_DATA_PASSWORD"):
            logger.error("Bright Data credentials are not available. Set BRIGHT_DATA_USERNAME and BRIGHT_DATA_PASSWORD environment variables.")
            raise ValueError("Bright Data credentials are required for price scraping. Please set the appropriate environment variables.")
            
        # Initialize the real scraper
        price_scraper = BrightDataPriceScraper()
        logger.info("Using BrightDataPriceScraper for price scraping")

        result_normalizer = PriceResultNormalizer()
        error_handler = DefaultScrapingErrorHandler()

        # Log the component creation time for monitoring
        elapsed = time.time() - start_time
        logger.debug("Created scraping components in %.3f seconds", elapsed)

        return price_scraper, result_normalizer, error_handler
    except Exception as e:
        logger.error("Error creating scraping components: %s", str(e))
        raise


async def scrape_prices_service(params: Dict) -> Dict:
    """
    Handle price scraping requests asynchronously.

    Args:
        params: Dictionary containing request parameters
               Required: 'model' - Smartphone model to search for
               Optional: 'country' - Country code for regional pricing (default: 'us')
               Optional: 'timeout' - Maximum time in seconds for the operation (default: 30)

    Returns:
        Dict containing scraped price data or error information
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Validate required parameters
    if not params or "model" not in params:
        logger.warning("Missing 'model' parameter in request")
        return {
            "status": "error",
            "message": "Missing required parameter: 'model'",
            "data": [],
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

    # Get parameters with defaults
    model = params["model"]
    country = params.get("country", "us").lower()
    timeout = params.get("timeout", 30)

    # Validate model parameter
    if not model or not isinstance(model, str):
        logger.warning("Invalid 'model' parameter: %s", model)
        return {
            "status": "error",
            "message": "Invalid 'model' parameter. Must be a non-empty string.",
            "data": [],
            "processing_time_ms": int((time.time() - start_time) * 1000)
        }

    # Create response template
    response = {
        "status": "error",
        "message": "",
        "data": [],
        "processing_time_ms": 0,
        "request": {
            "model": model,
            "country": country,
            "timeout": timeout
        }
    }

    # Start scraping
    logger.info("Starting price scraping for model '%s' in country '%s'", model, country)
    try:
        # Create components with proper dependency injection
        price_scraper, result_normalizer, error_handler = await create_scraping_components()
        
        # Perform the actual scraping
        raw_results = await price_scraper.scrape(model, country, timeout)
        
        # Process and normalize results
        if raw_results:
            normalized_results = result_normalizer.normalize(raw_results, model, country)
            response["status"] = "success"
            response["message"] = f"Successfully scraped {len(normalized_results)} price entries"
            response["data"] = normalized_results
            logger.info("Scraped %d price entries for '%s' in '%s'", len(normalized_results), model, country)
        else:
            response["status"] = "warning"
            response["message"] = f"No price data found for '{model}' in '{country}'"
            logger.warning("No price data found for '%s' in '%s'", model, country)
    except Exception as e:
        # Handle errors with proper component
        error_message = f"Error during price scraping: {str(e)}"
        logger.error(error_message)
        response["message"] = error_message
        
        # Try to use error handler component if available
        try:
            _, _, error_handler = await create_scraping_components()
            # Pass all required parameters (model and country) to the error handler
            await error_handler.handle_error(e, model, country)
        except Exception as handler_error:
            logger.error("Error in error handler: %s", str(handler_error))
    
    # Calculate and add processing time
    response["processing_time_ms"] = int((time.time() - start_time) * 1000)
    
    return response
