"""
Site Selector module for determining optimal scraping targets.

This module implements logic to select the most relevant websites to scrape
based on device model, user region, past performance, and user preferences.
"""
from typing import Any, Dict, List, Optional


class SiteSelector:
    """
    Selects optimal websites for scraping based on multiple criteria.

    This class analyzes the input model, country, user preferences, and historical
    performance data to determine the most relevant websites to search for price information.
    """

    def __init__(self):
        """Initialize the site selector with website knowledge base"""
        # Country-specific website mappings
        self._country_websites = {
            "US": [
                "amazon.com",
                "bestbuy.com",
                "walmart.com",
                "apple.com",
                "target.com",
                "bhphotovideo.com",
                "samsung.com",
                "google.com/store",
            ],
            "UK": [
                "amazon.co.uk",
                "currys.co.uk",
                "johnlewis.com",
                "argos.co.uk",
                "apple.com/uk",
                "samsung.com/uk",
            ],
            "CA": [
                "amazon.ca",
                "bestbuy.ca",
                "walmart.ca",
                "thesource.ca",
                "apple.com/ca",
                "samsung.com/ca",
            ],
            "AU": [
                "amazon.com.au",
                "jbhifi.com.au",
                "harveynorman.com.au",
                "apple.com/au",
                "samsung.com/au",
            ],
            "IN": [
                "amazon.in",
                "flipkart.com",
                "croma.com",
                "reliance.in",
                "apple.com/in",
                "samsung.com/in",
            ],
        }

        # Default international websites for countries not explicitly supported
        self._international_websites = [
            "amazon.com",
            "apple.com",
            "ebay.com",
            "samsung.com",
        ]

        # Brand-specific websites
        self._brand_websites = {
            "apple": ["apple.com", "store.apple.com"],
            "samsung": ["samsung.com", "shop.samsung.com"],
            "google": ["google.com/store", "store.google.com"],
            "microsoft": ["microsoft.com", "surface.com"],
            "dell": ["dell.com"],
            "lenovo": ["lenovo.com"],
            "asus": ["asus.com"],
            "hp": ["hp.com"],
            "xiaomi": ["mi.com", "xiaomi.com"],
        }

        # Regional store preferences (for US, can be expanded for other countries)
        self._region_stores = {
            "US": {
                "West Coast": [
                    "frys.com",
                    "microcenter.com",
                    "costco.com",
                ],
                "East Coast": [
                    "microcenter.com",
                    "costco.com",
                    "adorama.com",
                ],
                "Midwest": [
                    "microcenter.com",
                    "costco.com",
                    "cdw.com",
                ],
                "South": [
                    "costco.com",
                    "officedepot.com",
                    "samsclub.com",
                ],
            }
        }

    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate required inputs for site selection.

        Args:
            input_data: Dictionary containing input parameters

        Raises:
            ValueError: If required parameters are missing
        """
        if "model" not in input_data:
            raise ValueError("Input must include 'model' information")
        if "country" not in input_data:
            raise ValueError("Input must include 'country' information")

    def _extract_brand_from_model(self, model: str) -> Optional[str]:
        """
        Extract the brand from the model name using brand-specific keywords.

        Args:
            model: The product model name

        Returns:
            Brand name if identified, None otherwise
        """
        model_lower = model.lower()

        # Define brand-specific keywords mapping for cleaner detection
        brand_keywords = {
            "apple": ["iphone", "ipad", "macbook", "imac", "apple"],
            "samsung": ["galaxy", "samsung", "note"],
            "google": ["pixel", "google"],
            "microsoft": ["surface", "microsoft"],
            "xiaomi": ["xiaomi", "redmi", "mi"],
            "lenovo": ["thinkpad", "ideapad", "lenovo"],
            "dell": ["xps", "inspiron", "dell"],
            "asus": ["zenbook", "vivobook", "asus", "rog"],
            "hp": ["spectre", "pavilion", "envy", "hp"],
        }

        # Check if any brand keywords are in the model name
        for brand, keywords in brand_keywords.items():
            if any(keyword in model_lower for keyword in keywords):
                return brand

        return None

    def _retrieve_site_performance_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Retrieve historical performance metrics for websites.

        In a real implementation, this would retrieve data from a database
        tracking success rates and data quality for various sites.

        Returns:
            Dictionary mapping website domains to their performance metrics:
            {
                "domain.com": {
                    "success_rate": float, # 0.0-1.0 success rate of scraping
                    "data_quality": float,  # 0.0-1.0 quality score of data
                }
            }
        """
        # This would normally come from a database, but for now we'll use static data
        return {
            "amazon.com": {"success_rate": 0.92, "data_quality": 0.95},
            "bestbuy.com": {"success_rate": 0.88, "data_quality": 0.90},
            "walmart.com": {"success_rate": 0.85, "data_quality": 0.82},
            "apple.com": {"success_rate": 0.95, "data_quality": 0.98},
            "target.com": {"success_rate": 0.80, "data_quality": 0.75},
            "bhphotovideo.com": {"success_rate": 0.90, "data_quality": 0.92},
            "samsung.com": {"success_rate": 0.93, "data_quality": 0.94},
            "google.com/store": {"success_rate": 0.91, "data_quality": 0.93},
        }

    def _prioritize_sites_by_performance(self, sites: List[str]) -> List[str]:
        """
        Prioritize websites based on their historical performance metrics.

        Args:
            sites: List of website domains to prioritize

        Returns:
            Reordered list of websites with highest-performing sites first
        """
        performance_metrics = self._retrieve_site_performance_metrics()

        # Calculate a composite score for each site (success_rate * data_quality)
        # Higher scores indicate better overall performance
        site_performance_scores: Dict[str, float] = {}

        for site in sites:
            if site in performance_metrics:
                metrics = performance_metrics[site]
                # Combine metrics into a single score between 0.0-1.0
                site_performance_scores[site] = (
                    metrics["success_rate"] * metrics["data_quality"]
                )
            else:
                # Default middle score for sites with no performance data
                site_performance_scores[site] = 0.5

        # Sort sites by their performance score (descending order)
        return sorted(
            sites, key=lambda site: site_performance_scores.get(site, 0), reverse=True
        )

    def _prioritize_user_preferred_retailers(
        self, sites: List[str], user_preferences: Dict[str, Any]
    ) -> List[str]:
        """
        Reorder sites to prioritize user's preferred retailers at the top of the list.

        Args:
            sites: List of website domains to prioritize
            user_preferences: Dictionary containing user preferences including:
                - preferred_retailers: Optional list of preferred retailer domains

        Returns:
            Reordered list with user's preferred retailers at the beginning
        """
        if not user_preferences:
            return sites

        preferred_retailers = user_preferences.get("preferred_retailers", [])
        if not preferred_retailers:
            return sites

        # Extract user's preferred retailers that exist in our site list
        prioritized_sites = []
        remaining_sites = []

        # First add all preferred retailers that are in the site list, maintaining their order
        for retailer in preferred_retailers:
            if retailer in sites:
                prioritized_sites.append(retailer)

        # Then add all the other sites that weren't in the preferred list
        for site in sites:
            if site not in prioritized_sites:
                remaining_sites.append(site)

        # Return combined list: preferred sites first, then remaining sites
        return prioritized_sites + remaining_sites

    def _find_region_specific_retailers(
        self, country: str, region: Optional[str]
    ) -> List[str]:
        """
        Find retailers specific to a geographical region within a country.

        Args:
            country: ISO country code (e.g. 'US', 'UK')
            region: Geographical region within the country (e.g. 'West Coast', 'East Coast')

        Returns:
            List of region-specific retailer domains, or empty list if none available
        """
        # Return empty list if no region specified or country not in our region database
        if not region or country not in self._region_stores:
            return []

        # Get all regions for this country
        country_region_mapping = self._region_stores[country]

        # Return empty list if the specified region isn't in our database for this country
        if region not in country_region_mapping:
            return []

        # Return the list of region-specific retailer domains
        return country_region_mapping[region]

    def determine_optimal_scraping_targets(
        self, input_data: Dict[str, Any]
    ) -> List[str]:
        """
        Determine the optimal websites to scrape based on multiple criteria.

        Args:
            input_data: Dictionary containing selection criteria including:
                - model: Device model name (required)
                - country: Country code (required)
                - region: Optional geographical region within country
                - user_preferences: Optional dictionary of user preferences
                - max_sites: Optional limit on number of sites to return

        Returns:
            List of website domains ordered by relevance for scraping

        Raises:
            ValueError: If required inputs (model or country) are missing
        """
        # Validate required inputs
        self._validate_input(input_data)

        # Extract parameters from input data
        model = input_data["model"]
        country = input_data["country"]
        region = input_data.get("region")
        user_preferences = input_data.get("user_preferences", {})
        max_sites = input_data.get("max_sites")

        # Build initial candidate site list
        # 1. Start with country-specific websites or fall back to international websites
        candidate_sites = self._country_websites.get(
            country, self._international_websites
        ).copy()

        # 2. Add brand-specific websites based on device model
        brand = self._extract_brand_from_model(model)
        if brand and brand in self._brand_websites:
            brand_sites = self._brand_websites[brand]
            # Add brand sites that aren't already in the candidate list
            for site in brand_sites:
                if site not in candidate_sites:
                    candidate_sites.append(site)

        # 3. Add region-specific retailers if available
        region_retailers = self._find_region_specific_retailers(country, region)
        for site in region_retailers:
            if site not in candidate_sites:
                candidate_sites.append(site)

        # Prioritize sites based on multiple factors
        # 1. First by historical performance data
        prioritized_sites = self._prioritize_sites_by_performance(candidate_sites)

        # 2. Then by user's preferred retailers
        prioritized_sites = self._prioritize_user_preferred_retailers(
            prioritized_sites, user_preferences
        )

        # Apply site limit if specified
        if max_sites and max_sites > 0:
            prioritized_sites = prioritized_sites[:max_sites]

        return prioritized_sites

    # Alias the main method for backward compatibility
    select_sites = determine_optimal_scraping_targets
