"""
Tests for Price Analysis Prompt Generator.

This module tests the PriceAnalysisPromptGenerator's handling of parameters
like include_justification to ensure backward compatibility and proper behavior.
"""
import unittest

from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator


class TestPromptGeneratorParams(unittest.TestCase):
    """Test suite for prompt generator parameter handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.prompt_generator = PriceAnalysisPromptGenerator()
        self.formatted_data = "Sample formatted price data"

    def test_generate_prompt_basic(self):
        """Test generating a basic prompt without justification."""
        prompt = self.prompt_generator.generate_prompt(self.formatted_data)
        
        # Verify the prompt contains the sample data
        self.assertIn(self.formatted_data, prompt)
        # Verify it contains typical analysis instructions
        self.assertIn("Price comparison", prompt)
        self.assertIn("recommendations", prompt)

    def test_generate_prompt_with_include_justification_param(self):
        """Test that generate_prompt handles the include_justification parameter."""
        # Generate prompt with include_justification=False (should be same as basic)
        basic_prompt = self.prompt_generator.generate_prompt(
            self.formatted_data, include_justification=False
        )
        
        # Generate prompt with include_justification=True
        justified_prompt = self.prompt_generator.generate_prompt(
            self.formatted_data, include_justification=True
        )
        
        # Basic prompt should not contain justification wording
        self.assertNotIn("detailed justification", basic_prompt.lower())
        
        # Justified prompt should contain justification wording
        self.assertIn("justification", justified_prompt.lower())
        
        # Justified prompt should be longer
        self.assertGreater(len(justified_prompt), len(basic_prompt))


if __name__ == "__main__":
    unittest.main()
