"""
Price analysis module using LLM for market insights with rule-based fallback.

This module contains functions for price analysis using language models (LLM)
and fallback to rule-based analysis when the LLM is not available.
Implements the dependency injection principle for greater testability and maintainability.
"""
import logging
import re
from typing import Any, Dict, List, Optional, Set

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer


def analyze_prices(
    price_data: List[Dict[str, Any]],
    formatter: PriceFormatter,
    prompt_generator: PriceAnalysisPromptGenerator,
    llm_client: OpenAIClient,
    fallback_analyzer: FallbackAnalyzer,
) -> str:
    """
    Analyze price data using dependency injection pattern.

    Args:
        price_data: List of price dictionaries with price and other metadata
        formatter: Component to format price data into text
        prompt_generator: Component to generate prompts for the LLM
        llm_client: Client for communicating with the language model
        fallback_analyzer: Component to generate fallback analysis when LLM fails

    Returns:
        String with analysis of price data
    """
    # Return early if no data provided
    if not price_data:
        return fallback_analyzer.generate_analysis(price_data)

    try:
        # Format data using the formatter component
        formatted_data = formatter.format_price_data(price_data)

        # Generate prompt using the prompt generator component
        prompt = prompt_generator.generate_prompt(formatted_data)

        # Get response from the LLM client
        response = llm_client.generate_response(prompt)

        # If response is empty or too short, use fallback
        if not response or len(response.strip()) < 10:
            logging.warning("LLM returned empty or very short response, using fallback")
            return fallback_analyzer.generate_analysis(price_data)

        return response

    except Exception as error:
        logging.error("Error in AI price analysis: %s", str(error))
        return fallback_analyzer.generate_analysis(price_data)


def generate_fallback_analysis(price_data: List[Dict]) -> str:
    """
    Generate basic price analysis using rule-based logic when AI services are unavailable.

    Args:
        price_data: List of price dictionaries containing price information

    Returns:
        str: Basic price analysis insights
    """
    if not price_data:
        return "No price data available for analysis."

    try:
        # Extract numerical prices
        prices = []
        stores = set()
        countries = set()
        currencies = set()
        models = set()

        for item in price_data:
            # Lidar com preços armazenados como floats ou strings
            price_value = item.get("price")
            if isinstance(price_value, (int, float)):
                prices.append(float(price_value))
            elif isinstance(price_value, str):
                # Try to extract numeric value from price string
                numeric_price = "".join(
                    c for c in price_value if c.isdigit() or c == "."
                )
                if numeric_price:
                    try:
                        price = float(numeric_price)
                        prices.append(price)
                    except ValueError:
                        # Skip if conversion fails
                        pass

            # Collect metadata
            if "store" in item:
                stores.add(item["store"])
            if "region" in item:
                countries.add(item["region"])
            if "currency" in item:
                currencies.add(item["currency"])
            if "model" in item:
                models.add(item["model"])

        # Generate insights
        insights = []

        if prices:
            avg_price = sum(prices) / len(prices)
            min_price = min(prices)
            max_price = max(prices)
            price_range = max_price - min_price

            # Iniciar com identificador de fallback e estatísticas de preço
            insights.append(
                f"[FALLBACK ANALYSIS] Based on the available data, we can provide the following insights."
            )
            insights.append(
                f"The average price is ${avg_price:.2f}, with prices ranging from ${min_price:.2f} to ${max_price:.2f}."
            )

            # Add price dispersion insight
            if len(prices) > 1:
                if price_range > avg_price * 0.2:  # More than 20% variation
                    insights.append(
                        "There is significant price variation between stores."
                    )
                    insights.append("Consider comparing prices before purchasing.")
                else:
                    insights.append("Prices are relatively consistent across stores.")

        # Add store and region insights
        if len(stores) > 1:
            insights.append(f"Available at {len(stores)} different retailers.")

        if len(countries) > 1:
            insights.append(f"Price data from {len(countries)} different regions.")

        if not insights:
            return "[FALLBACK ANALYSIS] Insufficient data for price analysis. Try adding more regions or products."

        # Garantir que analisamos a tendência de preços e adicionamos uma recomendação
        if len(prices) > 1:
            # Ordenar preços temporalmente se possível
            sorted_prices = []
            try:
                # Tentar ordenar os dados por timestamp, se disponível
                sorted_data = sorted(price_data, key=lambda x: x.get("timestamp", ""))
                sorted_prices = [
                    float(item.get("price", 0))
                    for item in sorted_data
                    if item.get("price")
                ]
            except (KeyError, TypeError):
                # If it's not possible to order, use the original list
                sorted_prices = prices

            if sorted_prices and len(sorted_prices) > 1:
                if sorted_prices[-1] < sorted_prices[0]:
                    insights.append(
                        "Based on the decreasing price trend, this may be a good time to buy."
                    )
                elif sorted_prices[-1] > sorted_prices[0]:
                    insights.append(
                        "With prices trending upward, you may want to wait for potential drops."
                    )
                else:
                    insights.append(
                        "Prices appear stable, suggesting standard market conditions."
                    )
            else:
                insights.append(
                    "Based on the price trends, consider monitoring prices over time for better insights."
                )
        else:
            insights.append(
                "Based on the price trends, consider monitoring prices over time for better insights."
            )

        # Formatar como texto em vez de lista, para melhor legibilidade
        return " ".join(insights)

    except Exception as error:
        logging.error("Error in fallback analysis: %s", str(error))
        return "[FALLBACK ANALYSIS] Unable to analyze price data due to technical issues. Please try again with valid price information."


def analyze_prices_with_justification(
    price_data: List[Dict[str, Any]],
    formatter: PriceFormatter,
    prompt_generator: PriceAnalysisPromptGenerator,
    llm_client: OpenAIClient,
    fallback_analyzer: FallbackAnalyzer,
) -> str:
    """
    Analyze price data with detailed decision justification using dependency injection pattern.

    Args:
        price_data: List of price dictionaries with price and other metadata
        formatter: Component to format price data into text
        prompt_generator: Component to generate prompts for the LLM
        llm_client: Client for communicating with the language model
        fallback_analyzer: Component to generate fallback analysis when LLM fails

    Returns:
        String with analysis of price data including decision justification
    """
    # Return early if no data provided
    if not price_data:
        return fallback_analyzer.generate_analysis(price_data)

    try:
        # Format data using the formatter component
        formatted_data = formatter.format_price_data(price_data)

        # Generate prompt using the prompt generator component with justification
        prompt = prompt_generator.generate_prompt_with_justification(formatted_data)

        # Get response from the LLM client
        response = llm_client.generate_response(prompt)

        # If response is empty or too short, use fallback
        if not response or len(response.strip()) < 10:
            logging.warning("LLM returned empty or very short response, using fallback")
            return fallback_analyzer.generate_analysis_with_justification(price_data)

        return response

    except Exception as error:
        logging.error("Error in AI price analysis with justification: %s", str(error))
        return fallback_analyzer.generate_analysis_with_justification(price_data)
