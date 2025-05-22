"""
Scraping implementation module for the SmartNinja application.
This module provides concrete implementations of the scraping interfaces.
"""
# Import core implementations and components
from app.core.analyzer.formatting.price_formatter import BasicPriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
# Avoid circular import
# from app.core.analyzer.service import PriceAnalyzerService as PriceAnalyzer

# Import rule-based analyzer module (not the class directly) to avoid instantiation issues
import app.core.analyzer.rule_based

# Import interfaces for easy access
from app.core.interfaces.scraping import IPriceAnalyzer, IPriceScraper, IScraperService

# Import real scraper implementations
from .bright_data_scraper import BrightDataPriceScraper
from .bright_data_service import BrightDataScraperService

# Use real implementations as default exports
PriceScraper = BrightDataPriceScraper

# Import site selector for smart site planning
from .site_selector import SiteSelector

# Re-export classes for backward compatibility with existing tests
__all__ = [
    "PriceScraper",
    "PriceAnalyzer",
    "BrightDataPriceScraper",
    "BrightDataScraperService",
    "SiteSelector",
    "get_default_price_analyzer",
]

# Create all required components for the price analyzer
formatter = BasicPriceFormatter()
prompt_generator = PriceAnalysisPromptGenerator()
from app.core.analyzer.clients.openai_client import OpenAIClient


def get_default_llm_client():
    return OpenAIClient()


# Use lazy loading for rule-based analyzer to avoid instantiation at import time
def get_rule_based_analyzer():
    """Return a properly initialized rule-based analyzer instance."""
    from app.core.analyzer.rule_based.market_analyzer import MarketRuleBasedAnalyzer
    return MarketRuleBasedAnalyzer()

# Create default instances for singleton usage
scraper_service = BrightDataScraperService()


def get_default_price_analyzer(llm_client):
    """
    Factory for PriceAnalyzer. Requires llm_client to be provided explicitly.
    This avoids instantiating OpenAIClient at import time and uses lazy loading
    for rule-based analyzer.
    """
    from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer
    # Import PriceAnalyzerService here to avoid circular imports
    from app.core.analyzer.service import PriceAnalyzerService
    
    formatter = BasicPriceFormatter()
    prompt_generator = PriceAnalysisPromptGenerator()
    fallback = FallbackAnalyzer()
    
    return PriceAnalyzerService(
        llm_client=llm_client,
        formatter=formatter,
        prompt_generator=prompt_generator,
        rule_based_analyzer=fallback
    )


price_scraper = BrightDataPriceScraper()
