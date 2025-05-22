"""
Analyze Prices MCP Service.

This module provides asynchronous price analysis capabilities using AI with
dependency injection and clean architecture principles.
"""
import logging
import time
from typing import Any, Dict, List, Tuple

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_analyzer_components() -> Tuple[
    PriceFormatter, PriceAnalysisPromptGenerator, OpenAIClient, FallbackAnalyzer
]:
    """
    Create analyzer components with proper dependency injection asynchronously.

    Returns:
        Tuple of (formatter, prompt_generator, llm_client, fallback_analyzer)
    """
    formatter = PriceFormatter()
    prompt_generator = PriceAnalysisPromptGenerator()
    llm_client = OpenAIClient()
    fallback_analyzer = FallbackAnalyzer()

    return formatter, prompt_generator, llm_client, fallback_analyzer


async def analyze_prices_service(params: Dict) -> Dict:
    """
    Handle a request for price analysis asynchronously.

    Args:
        params: Dictionary containing request parameters
               Expected to have a 'prices' key with a list of price dictionaries

    Returns:
        Dictionary containing standardized response with status, message, data, and processing time
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Initialize empty response with error defaults
    response = {
        "status": "error",
        "message": "",
        "data": [],
        "processing_time_ms": 0
    }

    # Validate parameters
    if not params or "prices" not in params:
        logger.warning("Missing 'prices' parameter in request")
        response["message"] = "Missing 'prices' parameter"
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return response

    prices = params["prices"]
    if not isinstance(prices, list):
        logger.warning("Invalid 'prices' parameter, must be a list")
        response["message"] = "'prices' parameter must be a list"
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return response

    if not prices:
        logger.warning("Empty 'prices' list provided")
        response["message"] = "Empty 'prices' list"
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return response

    # Check if justification is requested
    include_justification = params.get("include_justification", False)

    # Generate analysis using AI with dependency injection
    try:
        logger.info("Analyzing %d price data points", len(prices))

        # Create components with proper dependency injection
        formatter, prompt_generator, llm_client, fallback_analyzer = await create_analyzer_components()

        # Generate analysis based on requested detail level
        if include_justification:
            result = await analyze_prices_with_justification(
                prices, formatter, prompt_generator, llm_client, fallback_analyzer
            )
        else:
            result = await analyze_prices(
                prices, formatter, prompt_generator, llm_client, fallback_analyzer
            )

        # Build successful response
        response["status"] = "success"
        response["message"] = "Analysis completed successfully"
        response["data"] = result
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        logger.info("Analysis completed in %d ms", response["processing_time_ms"])
        return response

    except Exception as e:
        # Handle any errors during analysis
        error_message = f"Error during price analysis: {str(e)}"
        logger.error(error_message)
        response["message"] = error_message
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return response


async def analyze_prices_with_justification(
    prices: List[Dict[str, Any]],
    formatter: PriceFormatter,
    prompt_generator: PriceAnalysisPromptGenerator,
    llm_client: OpenAIClient,
    fallback_analyzer: FallbackAnalyzer,
) -> Dict[str, Any]:
    """
    Generate a detailed price analysis with justification using AI.

    Args:
        prices: List of price dictionaries
        formatter: Component for formatting price data
        prompt_generator: Component for generating prompts
        llm_client: Component for generating text from LLM
        fallback_analyzer: Component for fallback analysis

    Returns:
        Analysis text with justification
    """
    try:
        # Format the price data for analysis
        formatted_data = formatter.format_for_analysis(prices)
        
        # Generate the analysis prompt with justification flag
        prompt = prompt_generator.generate_prompt(
            formatted_data, include_justification=True
        )
        
        # Get analysis from LLM asynchronously
        analysis = await llm_client.generate_text(prompt)
        
        # Return the analysis as a dictionary
        return {
            "analysis": analysis,
            "data_points": len(prices),
            "has_justification": True
        }
    except Exception as e:
        logger.warning("AI analysis failed, using fallback: %s", str(e))
        # Use rule-based fallback if AI analysis fails
        fallback_result = fallback_analyzer.analyze(prices)
        return {
            "analysis": fallback_result,
            "data_points": len(prices),
            "has_justification": False,
            "used_fallback": True
        }


async def analyze_prices(
    prices: List[Dict[str, Any]],
    formatter: PriceFormatter,
    prompt_generator: PriceAnalysisPromptGenerator,
    llm_client: OpenAIClient,
    fallback_analyzer: FallbackAnalyzer,
) -> Dict[str, Any]:
    """
    Generate a price analysis using AI.

    Args:
        prices: List of price dictionaries
        formatter: Component for formatting price data
        prompt_generator: Component for generating prompts
        llm_client: Component for generating text from LLM
        fallback_analyzer: Component for fallback analysis

    Returns:
        Analysis text
    """
    try:
        # Format the price data for analysis
        formatted_data = formatter.format_for_analysis(prices)
        
        # Generate the analysis prompt
        prompt = prompt_generator.generate_prompt(formatted_data)
        
        # Get analysis from LLM asynchronously
        analysis = await llm_client.generate_text(prompt)
        
        # Return the analysis as a dictionary
        return {
            "analysis": analysis,
            "data_points": len(prices)
        }
    except Exception as e:
        logger.warning("AI analysis failed, using fallback: %s", str(e))
        # Use rule-based fallback if AI analysis fails
        fallback_result = fallback_analyzer.analyze(prices)
        return {
            "analysis": fallback_result,
            "data_points": len(prices),
            "used_fallback": True
        }
