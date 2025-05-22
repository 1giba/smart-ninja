"""
Factory for creating price analyzer components and services.
Simplifies the instantiation and configuration of the analyzer system.
"""
from typing import Optional

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import BasicPriceFormatter
from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.market_analyzer import MarketRuleBasedAnalyzer
from app.core.analyzer.service import PriceAnalyzerService
from app.core.interfaces.scraping import IPriceAnalyzer


def create_price_analyzer_components(
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> tuple[PriceFormatter, PromptGenerator, LLMClient, RuleBasedAnalyzer]:
    """
    Create and return the individual components needed for price analysis.

    Args:
        api_url: Optional custom LLM API URL
        model: Optional custom LLM model name
        timeout: Optional custom request timeout in seconds

    Returns:
        A tuple containing (formatter, prompt_generator, llm_client, fallback_analyzer)
    """
    # Create the component instances
    formatter = BasicPriceFormatter()
    prompt_generator = PriceAnalysisPromptGenerator()

    # Create LLM client
    from app.core.analyzer.clients import get_default_llm_client

    llm_client_params = {}
    if api_url:
        llm_client_params["api_url"] = api_url
    if model:
        llm_client_params["model"] = model
    if timeout:
        llm_client_params["timeout"] = timeout
    llm_client = get_default_llm_client(**llm_client_params)

    # Create fallback analyzer
    fallback_analyzer = MarketRuleBasedAnalyzer()

    return formatter, prompt_generator, llm_client, fallback_analyzer


def create_analyzer_service(
    api_url: Optional[str] = None,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
    formatter: Optional[PriceFormatter] = None,
    prompt_generator: Optional[PromptGenerator] = None,
    llm_client: Optional[LLMClient] = None,
    rule_based_analyzer: Optional[RuleBasedAnalyzer] = None,
) -> IPriceAnalyzer:
    """
    Create a fully configured price analyzer service with all its dependencies.

    Args:
        api_url: Optional custom Ollama API URL
        model: Optional custom Ollama model name
        timeout: Optional custom request timeout in seconds
        formatter: Optional custom price formatter
        prompt_generator: Optional custom prompt generator
        llm_client: Optional custom LLM client
        rule_based_analyzer: Optional custom rule-based analyzer

    Returns:
        A fully configured IPriceAnalyzer implementation
    """
    # Create or use provided components
    formatter_instance = formatter or BasicPriceFormatter()
    prompt_generator_instance = prompt_generator or PriceAnalysisPromptGenerator()
    if llm_client:
        llm_client_instance = llm_client
    else:
        from app.core.analyzer.clients import get_default_llm_client

        llm_client_instance = get_default_llm_client()
    rule_based_analyzer_instance = rule_based_analyzer or MarketRuleBasedAnalyzer()

    # Create and return the service
    return PriceAnalyzerService(
        formatter=formatter_instance,
        prompt_generator=prompt_generator_instance,
        llm_client=llm_client_instance,
        rule_based_analyzer=rule_based_analyzer_instance,
    )
