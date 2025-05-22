"""
Interfaces for the analyzer module.

Defines the contracts for components in the analyzer system, including
both synchronous and asynchronous interfaces for flexibility.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class PriceFormatter(ABC):
    """Interface for formatting price data."""

    @abstractmethod
    def format_for_analysis(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Format price data into a readable string format for analysis.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Formatted string representation of the price data
        """


class PromptGenerator(ABC):
    """Interface for generating analysis prompts."""

    @abstractmethod
    def generate_prompt(self, formatted_data: str) -> str:
        """
        Generate a prompt for analysis based on formatted data.

        Args:
            formatted_data: Formatted price data string

        Returns:
            Prompt text for LLM analysis
        """

    @abstractmethod
    def generate_prompt_with_justification(self, formatted_data: str) -> str:
        """
        Generate a prompt for analysis with detailed justification.

        Args:
            formatted_data: Formatted price data string

        Returns:
            Prompt text for LLM analysis with justification requirement
        """


class LLMClient(ABC):
    """Interface for synchronous LLM API clients (legacy)."""

    @abstractmethod
    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Generate a response from the LLM with a prompt synchronously.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text if successful, None otherwise
        """


class AsyncLLMClient(ABC):
    """Interface for asynchronous LLM API clients."""

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        """
        Generate a response from the LLM with a prompt asynchronously.

        Args:
            prompt: The prompt to send to the LLM

        Returns:
            Response text if successful, empty string otherwise
        """


class RuleBasedAnalyzer(ABC):
    """Interface for rule-based analysis."""

    @abstractmethod
    def generate_analysis(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis on price data.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text generated from rules
        """

    @abstractmethod
    def generate_analysis_with_justification(self, price_data: List[Dict[str, Any]]) -> str:
        """
        Perform rule-based analysis with detailed justification.

        Args:
            price_data: List of price data dictionaries

        Returns:
            Analysis text with justification generated from rules
        """
