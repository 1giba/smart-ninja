"""
Test module to verify the interface compliance and component integration of the PriceAnalyzer.
This module validates that the PriceAnalyzer properly implements its interface and
integrates correctly with its components following the dependency injection pattern.
"""
import unittest
from unittest.mock import MagicMock

from app.core.analyzer.factory import create_price_analyzer_components

# Direct import from implementation after dependency injection refactoring
from app.core.analyzer.service import PriceAnalyzerService as PriceAnalyzer


class TestPriceAnalyzerInterfaces(unittest.TestCase):
    """Test suite for verifying the PriceAnalyzer interfaces and component integration"""

    def test_price_analyzer_class_structure(self):
        """Test that PriceAnalyzer has the expected interface"""
        # Create mock components
        mock_formatter = MagicMock()
        mock_prompt_generator = MagicMock()
        mock_llm_client = MagicMock()
        mock_rule_based_analyzer = MagicMock()

        # Initialize the analyzer with the expected interface
        analyzer = PriceAnalyzer(
            formatter=mock_formatter,
            prompt_generator=mock_prompt_generator,
            llm_client=mock_llm_client,
            rule_based_analyzer=mock_rule_based_analyzer,
        )

        # Verify that the analyzer has the expected attributes
        self.assertTrue(hasattr(analyzer, "formatter"))
        self.assertTrue(hasattr(analyzer, "prompt_generator"))
        self.assertTrue(hasattr(analyzer, "llm_client"))
        self.assertTrue(hasattr(analyzer, "rule_based_analyzer"))

    def test_price_analyzer_factory_components(self):
        """Test that a PriceAnalyzer pode ser criado com os componentes da factory"""
        # Obter os componentes da factory
        (
            formatter,
            prompt_generator,
            llm_client,
            rule_based_analyzer,
        ) = create_price_analyzer_components()

        # Criar o analisador com os componentes
        analyzer = PriceAnalyzer(
            formatter=formatter,
            prompt_generator=prompt_generator,
            llm_client=llm_client,
            rule_based_analyzer=rule_based_analyzer,
        )

        # Verificar que é uma instância de PriceAnalyzer
        self.assertIsInstance(analyzer, PriceAnalyzer)

        # Verificar que tem os atributos esperados
        self.assertTrue(hasattr(analyzer, "formatter"))
        self.assertTrue(hasattr(analyzer, "prompt_generator"))
        self.assertTrue(hasattr(analyzer, "llm_client"))
        self.assertTrue(hasattr(analyzer, "rule_based_analyzer"))


if __name__ == "__main__":
    unittest.main()
