"""
Analysis agent module for the SmartNinja application.
Provides AI-powered price analysis capabilities.

This implementation uses the SmartNinjaToolSet for unified tool access,
following the SOLID principle of dependency inversion.
"""

from datetime import datetime
import logging
import statistics
from typing import Any, Dict, List, Optional

from app.core.agents.base_agent import BaseAgent
from app.core.interfaces.tool_factory import create_tool_set
from app.core.interfaces.tool_set import ISmartNinjaToolSet


class AnalysisAgent(BaseAgent):
    """
    Agent responsible for analyzing price data.
    Uses SmartNinjaToolSet for all external tool interactions.

    This agent encapsulates the logic for analyzing price data from various sources,
    generating insights, and providing recommendations based on the data.
    """

    def __init__(self, tool_set: Optional[ISmartNinjaToolSet] = None):
        """
        Initialize the analysis agent with a SmartNinjaToolSet.

        Args:
            tool_set: Unified toolset for all external interactions (optional)
        """
        # BaseAgent doesn't need initialization
        self._tool_set = tool_set or create_tool_set()
        logger = logging.getLogger(__name__)
        logger.debug("AnalysisAgent initialized with SmartNinjaToolSet")

    def _calculate_price_statistics(
        self, price_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate statistical metrics for the price data.

        Args:
            price_data: List of price dictionaries with price and other metadata

        Returns:
            Dictionary with statistical metrics
        """
        if not price_data:
            return {
                "average_price": 0,
                "lowest_price": 0,
                "highest_price": 0,
                "price_range": 0,
                "price_std_dev": 0,
                "store_count": 0,
            }

        # Extract numeric prices and store information
        prices = []
        stores = set()
        for item in price_data:
            if "price" in item and isinstance(item["price"], (int, float)):
                prices.append(float(item["price"]))
            if "store" in item:
                stores.add(item["store"])

        # Calculate statistics
        stats = {
            "average_price": statistics.mean(prices) if prices else 0,
            "lowest_price": min(prices) if prices else 0,
            "highest_price": max(prices) if prices else 0,
            "price_range": max(prices) - min(prices) if len(prices) > 1 else 0,
            "store_count": len(stores),
        }

        # Calculate standard deviation if there's more than one price
        if len(prices) > 1:
            stats["price_std_dev"] = statistics.stdev(prices)
        else:
            stats["price_std_dev"] = 0

        return stats

    def _detect_price_trend(self, price_data: List[Dict[str, Any]]) -> Optional[str]:
        """
        Detect price trend based on time-series data if available.

        Args:
            price_data: List of price dictionaries with price and timestamp

        Returns:
            String indicating trend ('increasing', 'decreasing', 'stable') or None
        """
        # Filter items with both price and timestamp
        trend_data = [
            item for item in price_data if "price" in item and "timestamp" in item
        ]

        if len(trend_data) <= 1:
            return None

        try:
            # Sort by timestamp
            sorted_data = sorted(
                trend_data, key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d")
            )

            # Extract sorted prices
            sorted_prices = [float(item["price"]) for item in sorted_data]

            # Simple trend analysis (could be more sophisticated)
            first_price = sorted_prices[0]
            last_price = sorted_prices[-1]

            # Determine trend based on first and last price
            if last_price > first_price * 1.02:  # 2% increase threshold
                return "increasing"
            elif first_price > last_price * 1.02:  # 2% decrease threshold
                return "decreasing"
            else:
                return "stable"
        except (ValueError, KeyError, TypeError) as e:
            logging.warning(f"Error detecting price trend: {str(e)}")
            return None

    async def analyze_prices(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Asynchronously analyze price data to generate insights and recommendations.

        Args:
            price_data: List of dictionaries containing price data

        Returns:
            Dictionary with analysis results, including insights and recommendations
        """
        if not price_data:
            logger = logging.getLogger(__name__)
            logger.warning("No price data provided for analysis")
            return {
                "analysis": "No price data available for analysis.",
                "confidence": 0.0,
                "reasoning": "No data was provided for analysis.",
                "explanation": "No price data available",
                "fallback_used": False
            }

        try:
            # Format data using the normalizer from tool set
            formatted_data = await self._tool_set.normalize_data(price_data)

            # Generate prompt using the prompt generator from tool set
            prompt = await self._tool_set.generate_prompt(formatted_data)

            # Get analysis from the LLM client in tool set
            response = await self._tool_set.get_ai_analysis(prompt)

            # If we got a response, return it directly
            if response:
                logger = logging.getLogger(__name__)
                logger.info("Successfully generated AI analysis")
                # Return the direct string response as expected by tests
                return response

            # If no response, fall back to rule-based analysis
            logger = logging.getLogger(__name__)
            logger.warning(
                "Failed to get AI analysis, falling back to rule-based analysis"
            )
            rule_analysis = await self._tool_set.get_rule_analysis(price_data)
            
            # Return the rule-based analysis string
            return rule_analysis

        except Exception as e:
            # Log error and fall back to rule-based analysis
            logger = logging.getLogger(__name__)
            logger.error("Error during price analysis: %s", str(e))

            try:
                # Attempt rule-based analysis as fallback
                rule_analysis = await self._tool_set.get_rule_analysis(price_data)
                
                # Return the direct rule-based analysis string result
                return rule_analysis
            except Exception as fallback_error:
                # If even the fallback fails, return a generic message
                logger.error("Rule-based analysis also failed: %s", str(fallback_error))
                return "Unable to analyze price data due to technical difficulties."

    async def process_analysis_request(self, model: str, country: str) -> str:
        """
        Asynchronously process a complete analysis request from scraping to final analysis.

        Args:
            model: The product model to analyze
            country: The country to analyze prices for

        Returns:
            Complete analysis result as a string
            
        Note:
            In the future, this should be refactored to return a complete
            result dictionary similar to analyze_prices, but for compatibility
            with existing code, it currently returns just the analysis string.
        """
        try:
            # Use the tool set to handle the entire process
            result = await self._tool_set.process_price_analysis(model, country)

            if result:
                return result

            return "Unable to complete price analysis. Please try again later."

        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error processing analysis request: %s", str(e))
            return f"An error occurred while processing your analysis request: {str(e)}"

    def _generate_explanation(self, stats: Dict[str, Any], trend: Optional[str]) -> str:
        """
        Generate a concise explanation of the analysis.

        Args:
            stats: Dictionary with statistical metrics
            trend: String indicating price trend or None

        Returns:
            Concise explanation string
        """
        # Start with price range context
        if stats["store_count"] > 0 and stats["lowest_price"] > 0:
            price_diff = stats["highest_price"] - stats["lowest_price"]
            if price_diff > 0:
                price_diff_pct = (price_diff / stats["lowest_price"]) * 100
                explanation = f"Price varies by ${price_diff:.2f} (±{price_diff_pct:.1f}%)"
            else:
                explanation = f"All stores selling at ${stats['lowest_price']:.2f}"
        else:
            explanation = "Price data unavailable"
        
        # Add trend information if available
        if trend == "increasing":
            explanation += ", prices trending upward"
        elif trend == "decreasing":
            explanation += ", prices trending downward"
        elif trend == "stable":
            explanation += ", prices stable recently"
        
        return explanation

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the analysis agent with input data.

        Args:
            input_data: Dictionary containing input data required for analysis
                Required keys:
                - 'model': The product model to analyze (if doing a full analysis)
                - 'country': The country to analyze prices for (if doing a full analysis)
                - 'price_data': List of price data dictionaries (if doing direct price analysis)

        Returns:
            Dictionary containing analysis results with detailed data including:
            - 'analysis': The generated analysis text
            - 'confidence': Numeric confidence score (0.0 to 1.0)
            - 'reasoning': Detailed reasoning behind the analysis
            - 'explanation': Short, concise explanation of key findings
            - 'detailed_data': Additional structured data for detailed view

        Raises:
            ValueError: If required input data is missing
        """
        # Check if we're doing a full analysis or just analyzing existing price data
        try:
            if "price_data" in input_data:
                price_data = input_data["price_data"]
                result = self.analyze_prices(price_data)
            elif "model" in input_data and "country" in input_data:
                model = input_data["model"]
                country = input_data["country"]
                
                # This returns a string, so we'll need to add metadata
                analysis_text = self.process_analysis_request(model, country)
                
                if "Unable to complete" in analysis_text or "Error processing" in analysis_text:
                    # Error case
                    result = {
                        "analysis": analysis_text,
                        "confidence": 0.3,
                        "reasoning": "Analysis process encountered difficulties with the full request.",
                        "explanation": "Error processing full analysis request",
                        "detailed_data": {
                            "model": model,
                            "country": country,
                            "error": "Process failure"
                        }
                    }
                else:
                    # Success case, but with limited metadata
                    result = {
                        "analysis": analysis_text,
                        "confidence": 0.75,
                        "reasoning": f"Analysis based on price data for {model} in {country}.",
                        "explanation": f"Analysis of {model} prices in {country}",
                        "detailed_data": {
                            "model": model,
                            "country": country
                        }
                    }
            else:
                raise ValueError(
                    "Input must contain either 'price_data' or both 'model' and 'country'"
                )
            
            return result
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error("Error in analysis agent execution: %s", str(e))
            
            return {
                "analysis": f"Error in analysis: {str(e)}",
                "confidence": 0.0,
                "reasoning": "Analysis process encountered an unexpected error.",
                "explanation": "Unexpected error in analysis",
                "detailed_data": {
                    "error": str(e),
                    "input_keys_provided": list(input_data.keys())
                }
            }
