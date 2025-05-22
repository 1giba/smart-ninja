"""
Fallback analyzer implementation.
Provides a simple fallback analysis when other methods fail.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from app.core.analyzer.interfaces import RuleBasedAnalyzer


class FallbackAnalyzer(RuleBasedAnalyzer):
    """
    Fallback price analyzer that provides basic analysis when AI analysis fails.

    This analyzer uses rule-based logic to generate insights about price data.
    """

    def analyze(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis on price data.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text generated from rules
        """
        return self.generate_analysis(price_data)

    def generate_analysis(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Generate a fallback analysis when the AI service is unavailable.

        Args:
            price_data: List of price dictionaries

        Returns:
            A fallback analysis text
        """
        # Extract basic information from the prices
        if not price_data:
            return "[FALLBACK ANALYSIS] No price data available for analysis."

        try:
            model = price_data[0].get("model", "unknown model")

            # Calculate price trends if multiple data points
            if len(price_data) > 1:
                # Try to sort by timestamp if available
                try:
                    sorted_prices = sorted(
                        price_data, key=lambda x: x.get("timestamp", "")
                    )
                except (TypeError, KeyError):
                    # If sorting fails, use the original order
                    sorted_prices = price_data

                # Get first and last prices, handling potential missing or non-numeric values
                try:
                    first_price = float(sorted_prices[0].get("price", 0))
                    last_price = float(sorted_prices[-1].get("price", 0))

                    if last_price < first_price:
                        trend = "decreasing"
                        recommendation = "may be a good time to buy"
                    elif last_price > first_price:
                        trend = "increasing"
                        recommendation = "you may want to wait for price drops"
                    else:
                        trend = "stable"
                        recommendation = "neutral buying conditions"

                    return (
                        f"[FALLBACK ANALYSIS] Based on the price trends for {model}, "
                        f"prices are {trend}. This suggests it {recommendation}. "
                        f"Consider comparing prices across different retailers for the best deal."
                    )
                except (ValueError, TypeError):
                    # If price conversion fails
                    return (
                        f"[FALLBACK ANALYSIS] Based on the available data for {model}, "
                        f"we could not determine clear price trends due to data format issues. "
                        f"Consider checking multiple sources for current prices and market conditions."
                    )
            else:
                # Single price point
                try:
                    price_value = float(price_data[0].get("price", 0))
                    currency = price_data[0].get("currency", "USD")
                    return (
                        f"[FALLBACK ANALYSIS] Based on limited data for {model}, "
                        f"we have insufficient information to determine price trends. "
                        f"Current price point is {price_value} {currency}. "
                        f"Consider monitoring prices over time for better insights."
                    )
                except (ValueError, TypeError):
                    return (
                        f"[FALLBACK ANALYSIS] Based on limited data for {model}, "
                        f"we have insufficient information to determine price trends. "
                        f"Consider monitoring prices over time for better insights."
                    )
        except Exception as error:
            logging.error("Error in fallback analysis: %s", str(error))
            return (
                "[FALLBACK ANALYSIS] Unable to analyze price data. "
                "Based on the price trends, consider comparing prices across retailers "
                "and monitoring changes over time for better purchase decisions."
            )

    def generate_analysis_with_justification(
        self, price_data: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a fallback analysis with decision justification when the AI service is unavailable.

        Args:
            price_data: List of price dictionaries with price information

        Returns:
            str: Basic price analysis with decision justification
        """
        if not price_data:
            return "[FALLBACK ANALYSIS] No price data available for analysis."

        try:
            # Extract basic information from price data
            model = self._extract_common_model(price_data)
            prices = self._extract_numeric_prices(price_data)
            if not prices:
                return "[FALLBACK ANALYSIS] No valid price data available."

            # Calculate statistics
            current_price = prices[-1]
            avg_price = sum(prices) / len(prices)
            price_trend = self._determine_price_trend(prices)

            # Generate decision and justification
            if price_trend == "decreasing" or current_price < avg_price * 0.95:
                decision = "BUY"
                price_diff = ((avg_price - current_price) / avg_price) * 100
                justification = (
                    f"- Current price: ${current_price:.2f}\n"
                    f"- Average price: ${avg_price:.2f} ({price_diff:.1f}% lower)\n"
                    f"- Price trend: {price_trend.capitalize()}\n"
                    f"- Market context: Limited historical data available"
                )
            else:
                decision = "WAIT"
                price_diff = (
                    ((current_price - avg_price) / avg_price) * 100
                    if avg_price > 0
                    else 0
                )
                justification = (
                    f"- Current price: ${current_price:.2f}\n"
                    f"- Average price: ${avg_price:.2f} ({price_diff:.1f}% higher)\n"
                    f"- Price trend: {price_trend.capitalize()}\n"
                    f"- Market context: Limited historical data available"
                )

            return (
                f"[FALLBACK ANALYSIS] Based on the available data for {model}, "
                f"prices are {price_trend}.\n\n"
                f"DECISION: {decision}\n"
                f"JUSTIFICATION: \n{justification}\n\n"
                f"This analysis is based on limited data and should be considered a basic approximation."
            )

        except Exception as error:
            logging.error(
                "Error in fallback analysis with justification: %s", str(error)
            )
            return (
                "[FALLBACK ANALYSIS] Unable to analyze price data. "
                "Consider comparing prices across retailers and monitoring changes over time."
            )

    def _extract_common_model(self, price_data: List[Dict[str, Any]]) -> str:
        """Extract the most common model from price data."""
        models = [
            item.get("model", "Unknown Model") for item in price_data if "model" in item
        ]
        if not models:
            return "Unknown Model"
        return max(set(models), key=models.count)

    def _extract_numeric_prices(self, price_data: List[Dict[str, Any]]) -> List[float]:
        """Extract and sort numeric prices from price data."""
        prices = []
        for item in price_data:
            price_value = item.get("price")
            if isinstance(price_value, (int, float)):
                prices.append(float(price_value))
            elif isinstance(price_value, str):
                try:
                    price = float(
                        "".join(c for c in price_value if c.isdigit() or c == ".")
                    )
                    prices.append(price)
                except (ValueError, TypeError):
                    pass

        # Sort by date if available
        try:
            sorted_data = sorted(
                [item for item in price_data if "date" in item and "price" in item],
                key=lambda x: x.get("date", ""),
            )
            if sorted_data:
                sorted_prices = []
                for item in sorted_data:
                    price_value = item.get("price")
                    if isinstance(price_value, (int, float)):
                        sorted_prices.append(float(price_value))
                    elif isinstance(price_value, str):
                        try:
                            price = float(
                                "".join(
                                    c for c in price_value if c.isdigit() or c == "."
                                )
                            )
                            sorted_prices.append(price)
                        except (ValueError, TypeError):
                            pass
                if sorted_prices:
                    return sorted_prices
        except (KeyError, TypeError):
            pass

        return prices

    def _determine_price_trend(self, prices: List[float]) -> str:
        """Determine the price trend from a list of prices."""
        if len(prices) <= 1:
            return "stable"

        first_price = prices[0]
        last_price = prices[-1]

        if last_price < first_price * 0.98:  # 2% decrease
            return "decreasing"
        elif last_price > first_price * 1.02:  # 2% increase
            return "increasing"
        else:
            return "stable"


def get_fallback_analysis() -> str:
    """
    Provide a fallback analysis when all other methods fail.

    Returns:
        Generic fallback analysis text
    """
    return """# Market Analysis (Fallback)
Due to technical limitations, a detailed analysis couldn't be generated.
## General Insights
- Mobile phone prices typically vary by region due to taxes, import duties, and market competition.
- Flagship models generally hold their value better than mid-range or budget models.
- Prices tend to decrease over time, with significant drops after new model releases.
- Consider waiting for major shopping events (Black Friday, Cyber Monday) for the best deals.
## Recommendations
- Research prices across multiple retailers before purchasing.
- Consider previous generation models for better value.
- Check manufacturer refurbished options for discounts on like-new devices.
"""
