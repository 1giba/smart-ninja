"""
Unittests for the scraping-based price analyzer module.
Test the functionality of the PriceAnalyzer implementation in the scraping package.
"""
import unittest
from unittest.mock import MagicMock, patch

from app.core.analyzer.factory import create_price_analyzer_components

# Importar diretamente da implementação para evitar problemas de linting
from app.core.analyzer.service import PriceAnalyzerService as PriceAnalyzer


class TestPriceAnalyzerScraping(unittest.TestCase):
    """Test suite for the scraping-based PriceAnalyzer class"""

    def setUp(self):
        """Set up test environment with mock components"""
        self.mock_formatter = MagicMock()
        self.mock_prompt_generator = MagicMock()
        self.mock_llm_client = MagicMock()
        self.mock_rule_based_analyzer = MagicMock()

        self.api_url = "http://test.ollama.api"
        self.model = "test-model"
        self.timeout = 10

        self.mock_llm_client.api_url = self.api_url
        self.mock_llm_client.model = self.model
        self.mock_llm_client.timeout = self.timeout

        self.analyzer = PriceAnalyzer(
            formatter=self.mock_formatter,
            prompt_generator=self.mock_prompt_generator,
            llm_client=self.mock_llm_client,
            rule_based_analyzer=self.mock_rule_based_analyzer,
        )

        self.sample_data = [
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 999.99,
                "currency": "USD",
                "source": "Amazon",
            },
            {
                "model": "iPhone 15 Pro",
                "region": "EU",
                "price": 1149.99,
                "currency": "EUR",
                "source": "MediaMarkt",
            },
            {
                "model": "Samsung Galaxy S24",
                "region": "US",
                "price": 899.99,
                "currency": "USD",
                "source": "Best Buy",
            },
        ]

    def test_initialization(self):
        """Test proper initialization of the analyzer"""
        mock_formatter = MagicMock()
        mock_prompt_generator = MagicMock()
        mock_llm_client = MagicMock()
        mock_rule_based_analyzer = MagicMock()

        mock_llm_client.api_url = "http://custom.ollama.api"
        mock_llm_client.model = "llama3"
        mock_llm_client.timeout = 20

        analyzer = PriceAnalyzer(
            formatter=mock_formatter,
            prompt_generator=mock_prompt_generator,
            llm_client=mock_llm_client,
            rule_based_analyzer=mock_rule_based_analyzer,
        )

        self.assertEqual(analyzer.llm_client.api_url, "http://custom.ollama.api")
        self.assertEqual(analyzer.llm_client.model, "llama3")
        self.assertEqual(analyzer.llm_client.timeout, 20)

    def test_create_price_analyzer_components(self):
        """Test que os componentes da factory podem ser usados para criar um PriceAnalyzer válido"""
        # Obter componentes da factory
        (
            formatter,
            prompt_generator,
            llm_client,
            rule_based_analyzer,
        ) = create_price_analyzer_components()

        # Criar analisador com os componentes
        analyzer = PriceAnalyzer(
            formatter=formatter,
            prompt_generator=prompt_generator,
            llm_client=llm_client,
            rule_based_analyzer=rule_based_analyzer,
        )

        # Verificar que o analisador foi criado corretamente
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer, PriceAnalyzer)

    def test_format_price_data(self):
        """Test price data formatting"""
        expected_formatted_data = {
            "prices": [
                "iPhone 15 Pro: $999.99 (USD) from Amazon in US",
                "iPhone 15: $899.99 (USD) from Best Buy in US",
            ]
        }
        self.mock_formatter.format_price_data.return_value = expected_formatted_data

        self.analyzer.analyze_market(self.sample_data)

        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        # Verify formatted data
        expected = expected_formatted_data
        actual = self.mock_formatter.format_price_data.return_value
        self.assertEqual(expected, actual)

    def test_create_analysis_prompt(self):
        """Test analysis prompt generation"""
        formatted_data = {
            "prices": [
                "iPhone 15 Pro: $999.99 (USD) from Amazon in US",
                "iPhone 15: $899.99 (USD) from Best Buy in US",
            ]
        }
        self.mock_formatter.format_price_data.return_value = formatted_data

        expected_prompt = "Analyze these iPhone prices and provide market insights"
        self.mock_prompt_generator.generate_prompt.return_value = expected_prompt

        self.analyzer.analyze_market(self.sample_data)

        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            formatted_data
        )

    def test_query_ollama_success(self):
        """Test successful API interaction with Ollama"""
        analysis_result = "This is an analysis result"
        self.mock_llm_client.generate_response.return_value = analysis_result

        formatted_data = {"prices": ["iPhone 15: $999.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        result = self.analyzer.analyze_market(self.sample_data)

        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.assertEqual(result, analysis_result)

    def test_query_ollama_error_status(self):
        """Test handling of error status code from Ollama API"""
        error_msg = "APIError: 500 Internal Server Error"
        self.mock_llm_client.generate_response.side_effect = Exception(error_msg)

        formatted_data = {"prices": ["iPhone 15: $999.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        fallback_result = "Fallback analysis due to API error"
        self.mock_rule_based_analyzer.analyze.return_value = fallback_result

        result = self.analyzer.analyze_market(self.sample_data)

        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.assertEqual(result, fallback_result)

    def test_query_ollama_exception(self):
        """Test handling of exceptions during API calls"""
        self.mock_llm_client.generate_response.side_effect = Exception(
            "Connection error"
        )

        formatted_data = {"prices": ["iPhone 15: $999.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        fallback_result = "Fallback analysis due to connection error"
        self.mock_rule_based_analyzer.analyze.return_value = fallback_result

        result = self.analyzer.analyze_market(self.sample_data)

        self.mock_llm_client.generate_response.assert_called_once_with(prompt)
        self.assertEqual(result, fallback_result)

    def test_analyze_market_with_ollama_success(self):
        """Test market analysis using Ollama"""
        analysis_text = "Successful market analysis from Ollama"
        self.mock_llm_client.generate_response.return_value = analysis_text

        formatted_data = {"prices": ["iPhone 15 Pro: $999.99", "iPhone 15: $899.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these iPhone prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        result = self.analyzer.analyze_market(self.sample_data)

        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        self.mock_prompt_generator.generate_prompt.assert_called_once_with(
            formatted_data
        )
        self.mock_llm_client.generate_response.assert_called_once_with(prompt)

        self.assertEqual(result, analysis_text)

    def test_analyze_market_with_ollama_failure(self):
        """Test market analysis fallback when Ollama fails"""
        self.mock_llm_client.generate_response.side_effect = Exception("APIError")

        formatted_data = {"prices": ["iPhone 15 Pro: $999.99", "iPhone 15: $899.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these iPhone prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        fallback_result = "Basic price comparison: iPhone 15 Pro costs more"
        self.mock_rule_based_analyzer.analyze.return_value = fallback_result

        analysis = self.analyzer.analyze_market(self.sample_data)

        self.mock_formatter.format_price_data.assert_called_once_with(self.sample_data)
        # Verify prompt generator was called
        self.mock_prompt_generator.generate_prompt.assert_called_once()
        self.mock_rule_based_analyzer.analyze.assert_called_once()

        self.assertEqual(analysis, fallback_result)
        self.assertIn("Basic price comparison", analysis)

    def test_analyze_market_empty_data(self):
        """Test market analysis with empty data"""
        # When passing an empty list, the service should return early
        # without calling any of the components
        expected_message = "No price data available for analysis."

        # Run the analysis with empty data
        result = self.analyzer.analyze_market([])

        # Verify the service returns the expected message
        self.assertEqual(result, expected_message)

        # Verify none of the components were called
        self.mock_formatter.format_price_data.assert_not_called()
        self.mock_prompt_generator.generate_prompt.assert_not_called()
        self.mock_llm_client.generate_response.assert_not_called()
        self.mock_rule_based_analyzer.analyze.assert_not_called()

    def test_perform_rule_based_analysis(self):
        """Test rule-based analysis fallback"""
        expected_result = "iPhone models vary in price by $100 between models"
        self.mock_rule_based_analyzer.analyze.return_value = expected_result

        self.mock_llm_client.generate_response.side_effect = Exception("APIError")

        formatted_data = {"prices": ["iPhone 15 Pro: $999.99", "iPhone 15: $899.99"]}
        self.mock_formatter.format_price_data.return_value = formatted_data

        prompt = "Analyze these iPhone prices"
        self.mock_prompt_generator.generate_prompt.return_value = prompt

        # Execute market analysis
        self.analyzer.analyze_market(self.sample_data)

        # Verify rule-based analyzer was called
        self.mock_rule_based_analyzer.analyze.assert_called_once()

    def test_perform_rule_based_analysis_with_empty_data(self):
        """Test rule-based analysis with empty data"""
        empty_result = "No price data available for analysis."
        self.mock_rule_based_analyzer.analyze.return_value = empty_result

        empty_formatted_data = {"prices": []}
        self.mock_formatter.format_price_data.return_value = empty_formatted_data

        result = self.analyzer.analyze_market([])

        self.assertEqual(result, empty_result)

    def test_can_be_created_with_factory_components(self):
        """Test that the PriceAnalyzer can be created with components from factory"""
        # Obter componentes da factory
        (
            formatter,
            prompt_generator,
            llm_client,
            rule_based_analyzer,
        ) = create_price_analyzer_components()

        # Criar analisador com os componentes
        analyzer = PriceAnalyzer(
            formatter=formatter,
            prompt_generator=prompt_generator,
            llm_client=llm_client,
            rule_based_analyzer=rule_based_analyzer,
        )

        # Verificar que o analisador foi criado corretamente
        self.assertIsNotNone(analyzer)
        self.assertIsInstance(analyzer, PriceAnalyzer)
