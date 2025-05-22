"""
Price data formatting utilities.

Provides implementations for formatting price data into readable strings
for analysis purposes.
"""
from typing import Any, Dict, List

from app.core.analyzer.interfaces import PriceFormatter as PriceFormatterInterface


class PriceFormatter(PriceFormatterInterface):
    """Format price data for analysis."""

    def format_for_analysis(self, data: List[Dict[str, Any]]) -> str:
        """
        Format price data into a readable string format for analysis.

        Args:
            data: List of price dictionaries with price and other metadata

        Returns:
            Formatted string representation of price data
        """
        if not data:
            return ""

        formatted_items = []
        for item in data:
            # Extract price and format with appropriate precision
            price = item.get("price")
            if price is None:
                continue

            # Try to convert price to float if it's a string
            if isinstance(price, str):
                try:
                    price = float("".join(c for c in price if c.isdigit() or c == "."))
                except (ValueError, TypeError):
                    continue

            # Format price with 2 decimal places
            price_str = (
                f"${price:.2f}" if isinstance(price, (int, float)) else str(price)
            )

            # Add source information if available
            source = item.get("source") or item.get("store", "Unknown")
            
            # Add date/timestamp if available
            date = item.get("timestamp") or item.get("date", "")
            
            # Format the item with all available information
            formatted_item = f"{source}: {price_str}"
            if date:
                formatted_item += f" on {date}"
            
            # Add model information if available
            model = item.get("model", "")
            if model:
                formatted_item += f" for {model}"
                
            formatted_items.append(formatted_item)

        return (
            "Price Data:\n" + "\n".join(formatted_items) if formatted_items else "No valid price data available"
        )

    # Keep the original method for backward compatibility
    def format_price_data(self, data: List[Dict[str, Any]]) -> str:
        """
        Legacy method for formatting price data, maintained for backward compatibility.
        
        This delegates to format_for_analysis.

        Args:
            data: List of price dictionaries with price and other metadata

        Returns:
            Formatted string representation of price data
        """
        return self.format_for_analysis(data)


class BasicPriceFormatter:
    """Basic implementation of Price formatting module for the price analyzer."""

    def format_price_data(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Format price data for inclusion in analysis prompts.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Formatted string representation of the price data
        """
        if not price_data:
            return "No price data available."

        result = "Price data for analysis:\n"
        for idx, entry in enumerate(price_data, 1):
            price = entry.get("price", "N/A")
            currency = entry.get("currency", "USD")
            store = entry.get("store", "Unknown")
            date = entry.get("timestamp", "Unknown date")
            model = entry.get("model", "Unknown model")

            result += f"{idx}. {model} - {store}: {price} {currency} ({date})\n"

        return result
