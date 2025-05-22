"""
Result normalizer for price scraping.

This module implements the ResultNormalizer interface to standardize
and deduplicate scraped price data. Supports asynchronous operations.
"""
import asyncio
from datetime import datetime
from typing import Any, Dict, List, Set

from app.core.scraping.interfaces import ResultNormalizer


class PriceResultNormalizer(ResultNormalizer):
    """Implementation of the ResultNormalizer interface for price data."""

    async def normalize_results(
        self, results: List[Dict[str, Any]], model: str, country: str
    ) -> List[Dict[str, Any]]:
        """
        Normalize and deduplicate scraped results.

        Args:
            results: Raw scraped results
            model: Model that was searched for
            country: Country code that was used

        Returns:
            List of normalized price entries
        """
        normalized = []
        seen_urls: Set[str] = set()

        for item in results:
            # Skip duplicate URLs
            if item.get("url") in seen_urls:
                continue

            if item.get("url"):
                seen_urls.add(item["url"])

            # Normalize price format
            if "price" in item and isinstance(item["price"], (int, float)):
                price_value = f"${item['price']:.2f}"
            else:
                price_value = item.get("price", "N/A")

            # Create normalized entry
            normalized_item = {
                "product": item.get("title", item.get("name", model)),
                "price": price_value,
                "currency": item.get("currency", "USD"),
                "link": item.get("url", ""),
                "store": item.get("store", item.get("source", "Unknown")),
                "region": country.upper(),
                "date": item.get("date", datetime.now().strftime("%Y-%m-%d")),
            }

            normalized.append(normalized_item)

        return normalized
        
    async def normalize(self, results: List[Dict[str, Any]], model: str, country: str) -> List[Dict[str, Any]]:
        """
        Alias for normalize_results to maintain backward compatibility.
        
        Args:
            results: Raw scraped results
            model: Model that was searched for
            country: Country code that was used
            
        Returns:
            List of normalized price entries
        """
        return await self.normalize_results(results, model, country)
