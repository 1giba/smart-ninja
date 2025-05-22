"""
Planning Agent for determining target websites based on model and country.

This agent is responsible for planning the scraping strategy by identifying
the most relevant websites to search for a specific model in a specific country.
It uses the SiteSelector to intelligently choose optimal scraping targets.
"""
from typing import Any, Dict, List

from app.core.agents.base_agent import BaseAgent
from app.core.scraping.site_selector import SiteSelector


class PlanningAgent(BaseAgent):
    """
    Agent that determines target websites based on product model and country.

    This agent analyzes the input model and country to determine the most
    relevant websites to search for price information.
    """

    def __init__(self):
        """Initialize the planning agent with SiteSelector"""
        # Create site selector for smart site planning
        self.site_selector = SiteSelector()

        # Keep product category mappings for determining product type
        self._product_categories = {
            "phone": ["iPhone", "Galaxy", "Pixel", "Xiaomi"],
            "laptop": ["MacBook", "ThinkPad", "XPS", "Surface", "Zenbook"],
            "tablet": ["iPad", "Galaxy Tab", "Surface"],
            "desktop": ["iMac", "Mac", "Surface Studio"],
            "wearable": ["Watch", "Galaxy Watch", "Fitbit"],
        }

        # Fallback websites if site_selector is unavailable
        self._international_websites = ["amazon.com", "apple.com", "ebay.com"]

    def _get_category_from_model(self, model: str) -> str:
        """
        Determine product category from model name.

        Args:
            model: The product model name

        Returns:
            The identified product category or "unknown"
        """
        model_lower = model.lower()
        for category, keywords in self._product_categories.items():
            for keyword in keywords:
                if keyword.lower() in model_lower:
                    return category
        return "unknown"

    def _get_fallback_websites_for_country(self, country: str) -> List[str]:
        """
        Get fallback websites if SiteSelector is unavailable.
        This is only used if the site_selector attribute is not available.

        Args:
            country: The country code (e.g., US, UK)

        Returns:
            List of fallback international websites
        """
        return self._international_websites

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan which websites to target based on model and country.

        Args:
            input_data: Dictionary containing 'model' and 'country' keys

        Returns:
            Dictionary with 'websites' list and additional metadata

        Raises:
            ValueError: If model or country is missing from input_data
        """
        # Validate required inputs
        if "model" not in input_data:
            raise ValueError("Input must include 'model' information")
        if "country" not in input_data:
            raise ValueError("Input must include 'country' information")

        model = input_data["model"]
        country = input_data["country"]

        # Use SiteSelector to get targeted websites
        try:
            # Prepare input data for site selection
            selection_data = input_data.copy()

            # Get optimal scraping targets from site selector
            websites = self.site_selector.determine_optimal_scraping_targets(
                selection_data
            )
        except (AttributeError, ImportError):
            # Fallback if SiteSelector is not available
            websites = self._get_fallback_websites_for_country(country)

        # Create result with metadata
        result = {
            "websites": websites,
            "model": model,
            "country": country,
            "category": self._get_category_from_model(model),
        }

        # Include additional metadata from input
        if "region" in input_data:
            result["region"] = input_data["region"]

        if "user_preferences" in input_data:
            result["user_preferences"] = input_data["user_preferences"]

        return result
