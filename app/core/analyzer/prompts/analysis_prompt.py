"""
Prompt generators for price analysis.
Provides implementations for generating prompts for LLM-based price analysis.
"""
from typing import Optional

from app.core.analyzer.interfaces import PromptGenerator


class PriceAnalysisPromptGenerator(PromptGenerator):
    """
    Prompt generator for price analysis.
    Creates structured prompts requesting specific types of analysis.
    """

    def generate_prompt(self, formatted_data: str, include_justification: bool = False) -> str:
        """
        Generate a prompt for the LLM to analyze price data.

        Args:
            formatted_data: Formatted price data string
            include_justification: Whether to include detailed justification in the prompt

        Returns:
            Complete prompt to send to the LLM
        """
        # If justification is requested, use the detailed prompt
        if include_justification:
            return self.generate_prompt_with_justification(formatted_data)
            
        # Otherwise use the standard prompt
        return f"""Analyze the following mobile phone price data and provide insights:

{formatted_data}

Please provide a structured analysis including:
1. Price comparison across regions and models
2. Price trends if discernible
3. Buying recommendations and opportunities
4. Any other relevant insights
Format your analysis in clear, concise paragraphs."""

    def generate_prompt_with_justification(self, formatted_data: str) -> str:
        """
        Generate a prompt for the LLM to analyze price data and provide detailed
        justification for buying decisions.

        Args:
            formatted_data: Formatted price data string

        Returns:
            Complete prompt to send to the LLM
        """
        return f"""Analyze the following mobile phone price data and provide insights with detailed justification:

{formatted_data}

Please provide a structured analysis including:
1. Price comparison across regions and models
2. Price trends compared to 7-day and 30-day averages (if discernible)
3. Clear DECISION (BUY or WAIT) with detailed JUSTIFICATION

For the justification, include:
- Current price point relative to historical trends
- Percentage comparison with 7-day and 30-day averages
- Price trend direction and percentage change
- Any relevant market context influencing your decision

Format your output with:
DECISION: [BUY or WAIT]
JUSTIFICATION:
- Current price: [value]
- 7-day average: [value] ([x]% higher/lower)
- 30-day average: [value] ([x]% higher/lower)
- Price trend: [Increasing/Decreasing/Stable] ([x]% over [time period])
- Market context: [Any relevant market factors]

[Additional explanation in a paragraph if needed]"""
