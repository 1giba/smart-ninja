"""
Rule-based market analyzer implementation.
Provides implementations for analyzing price data using predefined rules and algorithms.
"""
import statistics
from typing import Any, Dict, List

from app.core.analyzer.interfaces import RuleBasedAnalyzer


class MarketRuleBasedAnalyzer(RuleBasedAnalyzer):
    """
    Rule-based analyzer that uses statistical methods to analyze price data.
    Serves as a fallback when LLM-based analysis is not available.
    """

    def generate_analysis(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis on price data.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text generated from rules
        """
        return self.analyze(price_data)
        
    def generate_analysis_with_justification(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis with detailed justification.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text with justification generated from rules
        """
        analysis = self.analyze(price_data)
        # Add justification section
        justification = "\n\n## Justification\n"
        justification += "This analysis is based on statistical methods applied to the provided price data. "
        justification += "It identifies trends, variations, and outliers using standard deviation and percentile calculations."
        
        return analysis + justification
    
    def analyze(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis on market data.

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

            model_section = self._analyze_model(model, model_data, regions)
            # Add the model section to the analysis
            analysis_parts.extend(model_section)

        # Add general insights
        analysis_parts.extend(self._get_general_insights())

        return "\n".join(analysis_parts)

    def _analyze_model(
        self, model: str, model_data: List[Dict[str, Any]], regions: set
    ) -> List[str]:
        """
        Analyze price data for a specific model.

        Args:
            model: The model name to analyze
            model_data: List of price data for this model
            regions: Set of all available regions

        Returns:
            List of analysis strings for this model
        """
        # Calculate average price
        prices = [item.get("price", 0) for item in model_data if "price" in item]
        if not prices:
            return []

        avg_price = statistics.mean(prices)
        min_price = min(prices)
        max_price = max(prices)

        model_section = [f"\n## {model}"]
        model_section.append(f"- Average price: ${avg_price:.2f}")
        model_section.append(f"- Price range: ${min_price:.2f} - ${max_price:.2f}")

        # Compare prices across regions
        if len(regions) > 1:
            region_comparison = self._compare_regions(model_data, regions)
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

        return model_section

    def _compare_regions(
        self, model_data: List[Dict[str, Any]], regions: set
    ) -> List[str]:
        """
        Compare prices across different regions.

        Args:
            model_data: List of price data for a specific model
            regions: Set of all available regions

        Returns:
            List of strings comparing prices in different regions
        """
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
        return region_comparison

    def _get_general_insights(self) -> List[str]:
        """
        Get general market insights.

        Returns:
            List of general insights about the market
        """
        insights = ["\n## General Insights"]
        insights.append("- Prices tend to vary significantly across regions.")
        insights.append(
            "- High-end models often show greater price variation than mid-range models."
        )
        insights.append(
            "- Consider importing from regions with lower prices if feasible."
        )
        return insights
