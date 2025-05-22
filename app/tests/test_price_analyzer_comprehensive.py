"""
Comprehensive tests for the PriceAnalyzer component.
Ensures complete coverage of all methods and edge cases.
"""
import logging
from unittest.mock import MagicMock, Mock, patch

# pylint: disable=no-name-in-module,attribute-defined-outside-init,protected-access,unused-import
import pytest
import requests

from app.core.analyzer.clients.openai_client import OpenAIClient
from app.core.analyzer.formatting.price_formatter import BasicPriceFormatter
from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.analyzer.prompts.analysis_prompt import PriceAnalysisPromptGenerator
from app.core.analyzer.rule_based.fallback_analyzer import get_fallback_analysis
from app.core.analyzer.rule_based.market_analyzer import MarketRuleBasedAnalyzer
from app.core.analyzer.service import PriceAnalyzerService
from app.core.interfaces.scraping import IPriceAnalyzer

# Configure logging for tests
logging.basicConfig(level=logging.INFO)


class TestPriceAnalyzerComprehensive:
    """Comprehensive test suite for the PriceAnalyzer class"""

    def setup_method(self):
        """Set up the test environment before each test"""
        # Patch environment variables for testing
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "OPENAI_API_KEY": "sk-test-key",
                "OPENAI_MODEL": "gpt-3.5-turbo",
                "OPENAI_TIMEOUT": "5",
            },
        )
        self.env_patcher.start()
        # Create components for the price analyzer
        self.formatter = BasicPriceFormatter()
        self.prompt_generator = PriceAnalysisPromptGenerator()

        # Use a fake LLM client for isolation in most tests
        class FakeLLMClient:
            def generate_response(self, prompt):
                return "[FAKE]"

        self.fake_llm_client = FakeLLMClient()
        self.rule_based_analyzer = MarketRuleBasedAnalyzer()

        self.analyzer = PriceAnalyzerService(
            formatter=self.formatter,
            prompt_generator=self.prompt_generator,
            llm_client=self.fake_llm_client,
            rule_based_analyzer=self.rule_based_analyzer,
        )
        # Sample data for testing
        self.sample_data = [
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 999.99,
                "currency": "USD",
                "store": "Amazon",
                "timestamp": "2023-01-01",
            },
            {
                "model": "iPhone 15 Pro",
                "region": "EU",
                "price": 1149.99,
                "currency": "EUR",
                "store": "MediaMarkt",
                "timestamp": "2023-01-01",
            },
            {
                "model": "Samsung Galaxy S24",
                "region": "US",
                "price": 899.99,
                "currency": "USD",
                "store": "BestBuy",
                "timestamp": "2023-01-01",
            },
        ]

    def teardown_method(self):
        """Clean up after each test"""
        self.env_patcher.stop()

    def test_implements_interface(self):
        """Test that PriceAnalyzer implements IPriceAnalyzer interface"""
        assert isinstance(
            self.analyzer, IPriceAnalyzer
        ), "PriceAnalyzer should implement IPriceAnalyzer"

    def test_init_with_custom_settings(self):
        """Test initialization with custom API settings"""
        # For the refactored service, we verify it was properly constructed with dependencies
        assert isinstance(self.analyzer, PriceAnalyzerService)
        assert isinstance(self.formatter, BasicPriceFormatter)
        assert isinstance(self.prompt_generator, PriceAnalysisPromptGenerator)
        assert isinstance(self.fake_llm_client, object)
        assert isinstance(self.rule_based_analyzer, MarketRuleBasedAnalyzer)

    def test_format_price_data(self):
        """Test the formatter component formats data correctly"""
        formatted = self.formatter.format_price_data(self.sample_data)
        
        # Check that it's a string and has the expected header
        assert isinstance(formatted, str)
        assert formatted.startswith("Price data for analysis:")
        
        # Check that formatted string contains all model information
        assert "iPhone 15 Pro" in formatted
        assert "Samsung Galaxy S24" in formatted
        
        # Check that price information is included
        assert "999.99 USD" in formatted
        assert "1149.99 EUR" in formatted
        assert "899.99 USD" in formatted
        
        # Check that sources are included
        assert "Amazon" in formatted
        assert "MediaMarkt" in formatted
        assert "BestBuy" in formatted
        
        # Check that the timestamp is included
        assert "2023-01-01" in formatted

    def test_create_analysis_prompt(self):
        """Test the prompt generator creates a valid prompt"""
        price_info = "iPhone 15 Pro: $999.99 (US)\niPhone 15 Pro: €1149.99 (EU)"
        prompt = self.prompt_generator.generate_prompt(price_info)
        # Check that prompt contains instructions
        assert "analyze the following mobile phone price data" in prompt.lower()
        # Check that the data is included
        assert price_info in prompt
        # Check that it asks for structured analysis
        assert "structured analysis" in prompt.lower()

    @patch("app.core.analyzer.clients.openai_client.OpenAIClient.generate_response")
    def test_query_openai_success(self, mock_generate_response):
        """Test the LLM client with successful response"""
        # Configurar o mock para retornar uma resposta de sucesso
        mock_generate_response.return_value = "This is a successful analysis"

        from app.core.analyzer.clients.openai_client import OpenAIClient

        # Criar o cliente sem injetar o completion_create
        llm_client = OpenAIClient(api_key="test-key", model="gpt-3.5-turbo")

        # Chamar o método e verificar o resultado
        result = llm_client.generate_response("test prompt")
        assert result == "This is a successful analysis"

        # Verificar que o método foi chamado com o prompt correto
        mock_generate_response.assert_called_once_with("test prompt")

    @patch("openai.OpenAI")
    def test_query_openai_error_status(self, mock_openai_client):
        """Test the LLM client with error status code"""
        # Configurar o mock do cliente OpenAI para lançar uma exceção quando usado
        mock_chat = MagicMock()
        mock_completions = MagicMock()
        mock_create = MagicMock(side_effect=Exception("API error"))

        # Configurar a estrutura de chamada aninhada
        mock_openai_client.return_value.chat.completions.create = mock_create

        from app.core.analyzer.clients.openai_client import OpenAIClient

        # Criar o cliente com o mock
        llm_client = OpenAIClient(api_key="test-key", model="gpt-3.5-turbo")

        # Chamar o método e verificar se ele lida adequadamente com a exceção
        result = llm_client.generate_response("test prompt")

        # Verificar que a implementação retorna uma mensagem de fallback em caso de erro para manter robustez
        assert "using basic price comparison instead" in result.lower()

    def test_analyze_market_with_empty_data(self):
        """Test analyze_market with empty data"""
        result = self.analyzer.analyze_market([])
        assert isinstance(result, str)
        assert "no price data available" in result.lower()

    def test_analyze_market_with_openai_success(self):
        """Test analyze_market with successful LLM client response"""
        # Mock successful LLM client response
        mock_ollama_response = "# Market Analysis\nInsightful content..."
        with patch.object(
            self.fake_llm_client, "generate_response", return_value=mock_ollama_response
        ):
            result = self.analyzer.analyze_market(self.sample_data)
            # Should return the API response
            assert result == mock_ollama_response

    def test_analyze_market_with_openai_failure(self):
        """Test analyze_market when LLM client fails"""
        # Mock LLM client failure - should fall back to rules
        with patch.object(self.fake_llm_client, "generate_response", return_value=""):
            # Setup rule-based analysis to verify fallback
            with patch.object(
                self.rule_based_analyzer, "analyze", return_value="Fallback Analysis"
            ):
                result = self.analyzer.analyze_market(self.sample_data)
                # Should return the fallback result
                assert result == "Fallback Analysis"

    def test_perform_rule_based_analysis(self):
        """Test the rule-based analyzer component"""
        analysis = self.rule_based_analyzer.analyze(self.sample_data)
        # Rule-based analysis should contain some key analysis points
        assert "analysis" in analysis.lower()
        assert "price" in analysis.lower()
        # Test with empty data
        empty_analysis = self.rule_based_analyzer.analyze([])
        assert isinstance(empty_analysis, str)
        assert len(empty_analysis) > 0

    def test_get_fallback_analysis(self):
        """Test the fallback analysis function"""
        fallback = get_fallback_analysis()
        assert isinstance(fallback, str)
        assert len(fallback) > 0
        # Fallback analysis should contain meaningful text
        assert "market analysis" in fallback.lower()

    def test_analyze_market_end_to_end(self):
        """Test analyze_market end-to-end with all components"""
        # This is a more comprehensive test that combines multiple aspects
        # Case 1: With mocked LLM client (success)
        mock_ollama_response = "# Comprehensive Market Analysis\nDetailed insights..."
        with patch.object(
            self.fake_llm_client, "generate_response", return_value=mock_ollama_response
        ):
            result1 = self.analyzer.analyze_market(self.sample_data)
            assert result1 == mock_ollama_response

        # Case 2: With LLM client failure, falling back to rule-based analysis
        with patch.object(self.fake_llm_client, "generate_response", return_value=""):
            # Also mock the rule-based analysis
            rule_analysis = (
                "# Rule-Based Market Analysis\nInsights generated by rules..."
            )
            with patch.object(
                self.rule_based_analyzer, "analyze", return_value=rule_analysis
            ):
                result2 = self.analyzer.analyze_market(self.sample_data)
                assert result2 == rule_analysis

        # Case 3: With empty data
        result3 = self.analyzer.analyze_market([])
        assert "no price data" in result3.lower()


if __name__ == "__main__":
    pytest.main(["-v", "test_price_analyzer_comprehensive.py"])
