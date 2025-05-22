"""
Price analyzer service implementation.
This module provides the main service that orchestrates the various components 
of the price analyzer system.
"""
import logging
from typing import Any, Dict, List

from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.analyzer.rule_based.fallback_analyzer import get_fallback_analysis
from app.core.interfaces.scraping import IPriceAnalyzer

# Configure logger
logger = logging.getLogger(__name__)


class PriceAnalyzerService(IPriceAnalyzer):
    """
    Service that orchestrates price analysis using various components.
    This service implements the IPriceAnalyzer interface and coordinates
    the formatter, prompt generator, LLM client, and fallback analyzer
    to provide comprehensive price analysis.
    """

    def __init__(
        self,
        formatter: PriceFormatter,
        prompt_generator: PromptGenerator,
        llm_client: LLMClient,
        rule_based_analyzer: RuleBasedAnalyzer,
    ):
        """
        Initialize the price analyzer service with its component dependencies.

        Args:
            formatter: Component for formatting price data
            prompt_generator: Component for generating LLM prompts
            llm_client: Client for communicating with LLM API
            rule_based_analyzer: Analyzer for rule-based fallback analysis
        """
        self.formatter = formatter
        self.prompt_generator = prompt_generator
        self.llm_client = llm_client
        self.rule_based_analyzer = rule_based_analyzer
        logger.info("PriceAnalyzerService initialized with all components")

    def analyze_market(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Analyze market data to provide insights by orchestrating all analyzer components.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text with insights about the price data
        """
        try:
            if not price_data:
                return "No price data available for analysis."

            logger.info("Analyzing market data with %s price points", len(price_data))

            # Format the price data
            formatted_data = self.formatter.format_price_data(price_data)

            # Generate the analysis prompt
            prompt = self.prompt_generator.generate_prompt(formatted_data)

            # Try to use LLM for analysis
            try:
                analysis = self.llm_client.generate_response(prompt)
                if analysis:
                    return analysis
            except Exception as exception:
                logger.warning("Failed to use LLM for analysis: %s", str(exception))

            # Fall back to rule-based analysis if LLM fails
            return self.rule_based_analyzer.analyze(price_data)

        except Exception as exception:
            logger.error("Error analyzing market data: %s", str(exception))
            # Ultimate fallback when everything else fails
            return get_fallback_analysis()
