"""
Factory for creating SmartNinjaToolSet instances.
Centralizes the creation of tool sets with their dependencies.
"""
import logging
from typing import Optional

from app.core.analyzer.factory import create_price_analyzer_components
from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.interfaces.scraping import IScraperService
from app.core.interfaces.tool_set import ISmartNinjaToolSet, SmartNinjaToolSet
from app.core.scraping.bright_data_service import BrightDataScraperService

# Configure logger
logger = logging.getLogger(__name__)


def create_tool_set(
    scraper_service: Optional[IScraperService] = None,
    price_formatter: Optional[PriceFormatter] = None,
    prompt_generator: Optional[PromptGenerator] = None,
    llm_client: Optional[LLMClient] = None,
    rule_based_analyzer: Optional[RuleBasedAnalyzer] = None,
) -> ISmartNinjaToolSet:
    """
    Create a SmartNinjaToolSet instance with default or custom components.

    Args:
        scraper_service: Optional custom scraper service
        price_formatter: Optional custom price formatter
        prompt_generator: Optional custom prompt generator
        llm_client: Optional custom LLM client
        rule_based_analyzer: Optional custom rule-based analyzer

    Returns:
        A fully initialized SmartNinjaToolSet instance
    """
    # Create default components if not provided
    if scraper_service is None:
        scraper_service = BrightDataScraperService()

    # If any of the analyzer components are None, create all of them together
    # This follows the existing pattern in the codebase
    if any(
        component is None
        for component in [
            price_formatter,
            prompt_generator,
            llm_client,
            rule_based_analyzer,
        ]
    ):
        # Get default components from the existing factory
        (
            default_formatter,
            default_prompt_gen,
            default_llm,
            default_analyzer,
        ) = create_price_analyzer_components()

        # Only use defaults for components that weren't provided
        price_formatter = price_formatter or default_formatter
        prompt_generator = prompt_generator or default_prompt_gen
        llm_client = llm_client or default_llm
        rule_based_analyzer = rule_based_analyzer or default_analyzer

    logger.debug("Creating SmartNinjaToolSet with components")

    return SmartNinjaToolSet(
        scraper_service=scraper_service,
        price_formatter=price_formatter,
        prompt_generator=prompt_generator,
        llm_client=llm_client,
        rule_based_analyzer=rule_based_analyzer,
    )
