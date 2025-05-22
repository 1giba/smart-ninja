"""
Unit tests for the price analysis module.

Tests the price analysis functionality using LLM with dependency injection.
"""
import unittest
from unittest.mock import Mock

from app.core.ai_agent import analyze_prices
from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import PriceFormatter
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import FallbackAnalyzer


class TestPriceAnalysis(unittest.TestCase):
    """Test suite for the price analysis module with dependency injection"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mocks for dependencies
        self.mock_formatter = Mock(spec=PriceFormatter)
        self.mock_prompt_generator = Mock(spec=PriceAnalysisPromptGenerator)
        self.mock_llm_client = Mock(spec=OpenAIClient)
        self.mock_fallback_analyzer = Mock(spec=FallbackAnalyzer)

        # Sample data for tests
        self.sample_data = [
            {
                "price": 999.99,
                "date": "2025-05-15",
                "model": "iPhone 15",
                "region": "US",
            },
            {
                "price": 989.99,
                "date": "2025-05-16",
                "model": "iPhone 15",
                "region": "US",
            },
            {
                "price": 979.99,
                "date": "2025-05-17",
                "model": "iPhone 15",
                "region": "US",
            },
        ]

    def test_should_use_fallback_analyzer_when_data_is_empty(self):
        """Verifica se o analisador de fallback é usado quando os dados estão vazios"""
        # Configurar mocks
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "Análise fallback para dados vazios"
        )

        # Testar com dados vazios
        result = analyze_prices(
            [],
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verificações
        self.mock_formatter.format_price_data.assert_not_called()
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with([])
        self.assertEqual(result, "Análise fallback para dados vazios")

    def test_should_use_llm_client_when_formatting_and_prompt_generation_succeed(self):
        """Verifica se o cliente LLM é utilizado quando formatação e geração de prompts funcionam corretamente"""
        # Configurar mocks
        self.mock_formatter.format_price_data.return_value = "Dados formatados"
        self.mock_prompt_generator.generate_prompt.return_value = "Prompt para análise"
        self.mock_llm_client.generate_response.return_value = (
            "Análise detalhada dos preços"
        )

        # Testar fluxo normal
        result = analyze_prices(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verificações
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            "Dados formatados"
        )
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Prompt para análise"
        )
        self.mock_fallback_analyzer.generate_analysis.assert_not_called()
        self.assertEqual(result, "Análise detalhada dos preços")

    def test_should_use_fallback_analyzer_when_llm_client_fails(self):
        """Verifica se o analisador de fallback é usado quando o cliente LLM falha"""
        # Configurar mocks
        self.mock_formatter.format_price_data.return_value = "Dados formatados"
        self.mock_prompt_generator.generate_prompt.return_value = "Prompt para análise"
        self.mock_llm_client.generate_response.side_effect = Exception("Erro na API")
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "Análise fallback devido a erro"
        )

        # Testar fluxo de erro no LLM
        result = analyze_prices(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verificações
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            "Dados formatados"
        )
        self.mock_llm_client.generate_response.assert_called_once_with(
            "Prompt para análise"
        )
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )
        self.assertEqual(result, "Análise fallback devido a erro")

    def test_should_use_fallback_analyzer_when_formatter_fails(self):
        """Verifica se o analisador de fallback é usado quando o formatador falha"""
        # Configurar mocks
        self.mock_formatter.format_price_data.side_effect = Exception(
            "Erro na formatação"
        )
        self.mock_fallback_analyzer.generate_analysis.return_value = (
            "Análise fallback devido a erro de formatação"
        )

        # Testar fluxo de erro na formatação
        result = analyze_prices(
            self.sample_data,
            self.mock_formatter,
            self.mock_prompt_generator,
            self.mock_llm_client,
            self.mock_fallback_analyzer,
        )

        # Verificações
        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_fallback_analyzer.generate_analysis.assert_called_once_with(
            self.sample_data
        )
        self.assertEqual(result, "Análise fallback devido a erro de formatação")


if __name__ == "__main__":
    unittest.main()
