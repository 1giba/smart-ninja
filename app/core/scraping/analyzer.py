"""
Price analyzer implementation for the SmartNinja application.
This module provides implementations of the price analyzer interfaces that
analyze price data to provide insights, trends, and recommendations.
"""
import logging
import os
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv

from app.core.interfaces.scraping import IPriceAnalyzer

# Load environment variables
load_dotenv()
# Get Ollama configuration from environment
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "30"))
# Configure logger
logger = logging.getLogger(__name__)


class PriceAnalyzer(IPriceAnalyzer):
    """
    Implementation of a price analyzer that analyzes price data to provide insights.
    This class implements the IPriceAnalyzer interface and uses Ollama (or a fallback
    mechanism) to generate analysis of price data, including trends, opportunities,
    and recommendations.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Initialize the price analyzer.
        Args:
            api_url: Optional custom Ollama API URL
            model: Optional custom Ollama model name
            timeout: Optional custom request timeout in seconds
        """
        self.api_url = api_url or OLLAMA_API_URL
        self.model = model or OLLAMA_MODEL
        self.timeout = timeout or OLLAMA_TIMEOUT
        logger.info(
            f"PriceAnalyzer initialized with model={self.model}, API URL={self.api_url}"
        )

    def analyze_market(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Analyze market data to provide insights.
        Args:
            price_data: List of price data dictionaries
        Returns:
            Analysis text with insights about the price data
        Raises:
            Exception: If analysis fails
        """
        try:
            if not price_data:
                return "No price data available for analysis."
            logger.info(f"Analyzing market data with {len(price_data)} price points")
            # Format price data for the prompt
            price_info = self._format_price_data(price_data)
            # Prepare prompt for LLM
            prompt = self._create_analysis_prompt(price_info)
            # Try to use Ollama for analysis
            try:
                analysis = self._query_ollama(prompt)
                if analysis:
                    return analysis
            except Exception as error:
                logger.warning(f"Failed to use Ollama for analysis: {str(error)}")
            # Fall back to rule-based analysis if Ollama fails
            return self._perform_rule_based_analysis(price_data)
        except Exception as error:
            logger.error(f"Error analyzing market data: {str(error)}")
            return self._get_fallback_analysis()

    def _format_price_data(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Format price data for inclusion in the prompt.
        Args:
            price_data: List of price data dictionaries
        Returns:
            Formatted string representation of the price data
        """
        # Create a formatted string with the price data
        lines = []
        for item in price_data:
            model = item.get("model", "Unknown Model")
            region = item.get("region", "Unknown Region")
            price = item.get("price", "N/A")
            currency = item.get("currency", "USD")
            source = item.get("source", "Unknown Source")
            line = f"- {model} in {region}: {price} {currency} (from {source})"
            lines.append(line)
        return "\n".join(lines)

    def _create_analysis_prompt(self, price_info: str) -> str:
        """
        Create a prompt for the LLM to analyze price data.
        Args:
            price_info: Formatted price data string
        Returns:
            Complete prompt to send to the LLM
        """
        return f"""Analyze the following mobile phone price data and provide insights:
        
{price_info}
        
Please provide a structured analysis including:
1. Price comparison across regions and models
2. Price trends if discernible
3. Buying recommendations and opportunities
4. Any other relevant insights
Format your analysis in clear, concise paragraphs."""

    def _query_ollama(self, prompt: str) -> Optional[str]:
        """
        Query the Ollama API for analysis.
        Args:
            prompt: The prompt to send to Ollama
        Returns:
            Analysis text if successful, None otherwise
        Raises:
            Exception: If API call fails
        """
        headers = {"Content-Type": "application/json"}
        payload = {"model": self.model, "prompt": prompt}
        try:
            response = requests.post(
                f"{self.api_url}/api/generate",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json().get("response")
            logger.warning(f"Ollama API returned status code {response.status_code}")
            return None
        except Exception as error:
            logger.error(f"Error querying Ollama API: {str(error)}")
            return None

    def _perform_rule_based_analysis(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis when Ollama is unavailable.
        Args:
            price_data: List of price data dictionaries
        Returns:
            Analysis text generated from rules
        """
        # Extract all models and regions
        models = {
            item.get("model", "Unknown") for item in price_data if "model" in item
        }
        regions = {
            item.get("region", "Unknown") for item in price_data if "region" in item
        }
        # Start building the analysis
        analysis_parts = ["# Market Analysis"]
        # Analyze each model
        for model in models:
            model_data = [item for item in price_data if item.get("model") == model]
            if not model_data:
                continue
            # Calculate average price
            prices = [item.get("price", 0) for item in model_data if "price" in item]
            if not prices:
                continue
            avg_price = statistics.mean(prices)
            min_price = min(prices)
            max_price = max(prices)
            model_section = [f"\n## {model}"]
            model_section.append(f"- Average price: ${avg_price:.2f}")
            model_section.append(f"- Price range: ${min_price:.2f} - ${max_price:.2f}")
            # Compare prices across regions
            if len(regions) > 1:
                region_comparison = []
                for region in regions:
                    region_prices = [
                        item.get("price", 0)
                        for item in model_data
                        if item.get("region") == region and "price" in item
                    ]
                    if region_prices:
                        region_avg = statistics.mean(region_prices)
                        region_comparison.append(f"{region}: ${region_avg:.2f}")
                if region_comparison:
                    model_section.append("\nRegional price comparison:")
                    for comparison in region_comparison:
                        model_section.append(f"- {comparison}")
            # Add recommendations
            model_section.append("\nRecommendations:")
            # Find the best deal
            best_deals = sorted(
                [item for item in model_data if "price" in item],
                key=lambda x: x.get("price", float("inf")),
            )
            if best_deals:
                best_deal = best_deals[0]
                model_section.append(
                    f"- Best deal: {best_deal.get('price', 'N/A')} "
                    f"{best_deal.get('currency', 'USD')} from {best_deal.get('source', 'Unknown')} "
                    f"in {best_deal.get('region', 'Unknown')}"
                )
            # Add the model section to the analysis
            analysis_parts.extend(model_section)
        # Add general insights
        analysis_parts.append("\n## General Insights")
        analysis_parts.append("- Prices tend to vary significantly across regions.")
        analysis_parts.append(
            "- High-end models often show greater price variation than mid-range models."
        )
        analysis_parts.append(
            "- Consider importing from regions with lower prices if feasible."
        )
        return "\n".join(analysis_parts)

    def _get_fallback_analysis(self) -> str:
        """
        Provide a fallback analysis when all else fails.
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
