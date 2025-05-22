"""
Price Scraping MCP Service.

This module exposes asynchronous price scraping functionality as a direct importable module.
"""

from .service import scrape_prices_service, create_scraping_components

__all__ = ['scrape_prices_service', 'create_scraping_components']
