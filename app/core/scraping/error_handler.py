"""
Error handler for price scraping.

This module implements error handling functionality for price scraping operations.
Supports asynchronous error handling for concurrent operations.
"""
import asyncio
import logging
import traceback
from typing import Any, Dict

from app.core.scraping.interfaces import ScrapingErrorHandler

# Configure logging
logger = logging.getLogger(__name__)


class DefaultScrapingErrorHandler(ScrapingErrorHandler):
    """Default implementation of the ScrapingErrorHandler interface."""

    async def handle_error(
        self, error: Exception, model: str, country: str
    ) -> Dict[str, Any]:
        """
        Handle errors during the scraping process.

        Args:
            error: The exception that was raised
            model: Model that was searched for
            country: Country code that was used

        Returns:
            Dictionary with error information
        """
        error_message = str(error)
        logger.error(
            "Error during async price scraping for %s (%s): %s",
            model,
            country,
            error_message,
        )
        # Log detailed traceback at debug level
        logger.debug("Error traceback: %s", traceback.format_exc())

        # Categorize errors for better client-side handling
        error_type = error.__class__.__name__

        return {
            "status": "error",
            "message": f"Failed to scrape prices: {error_message}",
            "data": [],
            "error_type": error_type,
        }
