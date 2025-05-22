"""
Test cases for the SmartNinjaToolSet factory.
Tests the functionality of the tool_factory module.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.core.analyzer.interfaces import (
    LLMClient,
    PriceFormatter,
    PromptGenerator,
    RuleBasedAnalyzer,
)
from app.core.interfaces.scraping import IScraperService
from app.core.interfaces.tool_factory import create_tool_set
from app.core.interfaces.tool_set import ISmartNinjaToolSet, SmartNinjaToolSet


class TestToolFactory:
    """Tests for the tool_factory module."""

    def test_create_tool_set_with_defaults(self):
        """Test creating a tool set with default components."""
        # Arrange
        mock_scraper = MagicMock(spec=IScraperService)
        mock_formatter = MagicMock(spec=PriceFormatter)
        mock_prompt_gen = MagicMock(spec=PromptGenerator)
        mock_llm = MagicMock(spec=LLMClient)
        mock_rule_analyzer = MagicMock(spec=RuleBasedAnalyzer)

        # Act & Assert
        with patch(
            "app.core.interfaces.tool_factory.BrightDataScraperService",
            return_value=mock_scraper,
        ):
            with patch(
                "app.core.interfaces.tool_factory.create_price_analyzer_components",
                return_value=(
                    mock_formatter,
                    mock_prompt_gen,
                    mock_llm,
                    mock_rule_analyzer,
                ),
            ):
                tool_set = create_tool_set()

                assert isinstance(tool_set, ISmartNinjaToolSet)
                assert isinstance(tool_set, SmartNinjaToolSet)
                assert tool_set.scraper_service == mock_scraper
                assert tool_set.price_formatter == mock_formatter
                assert tool_set.prompt_generator == mock_prompt_gen
                assert tool_set.llm_client == mock_llm
                assert tool_set.rule_based_analyzer == mock_rule_analyzer

    def test_create_tool_set_with_custom_components(self):
        """Test creating a tool set with custom components."""
        # Arrange
        mock_scraper = MagicMock(spec=IScraperService)
        mock_formatter = MagicMock(spec=PriceFormatter)
        mock_prompt_gen = MagicMock(spec=PromptGenerator)
        mock_llm = MagicMock(spec=LLMClient)
        mock_rule_analyzer = MagicMock(spec=RuleBasedAnalyzer)

        # Ensure create_price_analyzer_components is not called when all components are provided
        with patch(
            "app.core.interfaces.tool_factory.BrightDataScraperService"
        ) as mock_create_scraper:
            with patch(
                "app.core.interfaces.tool_factory.create_price_analyzer_components"
            ) as mock_create_components:
                # Act
                tool_set = create_tool_set(
                    scraper_service=mock_scraper,
                    price_formatter=mock_formatter,
                    prompt_generator=mock_prompt_gen,
                    llm_client=mock_llm,
                    rule_based_analyzer=mock_rule_analyzer,
                )

                # Assert
                assert isinstance(tool_set, ISmartNinjaToolSet)
                assert tool_set.scraper_service == mock_scraper
                assert tool_set.price_formatter == mock_formatter
                assert tool_set.prompt_generator == mock_prompt_gen
                assert tool_set.llm_client == mock_llm
                assert tool_set.rule_based_analyzer == mock_rule_analyzer

                # Verify that the factory functions were not called
                mock_create_scraper.assert_not_called()
                mock_create_components.assert_not_called()

    def test_create_tool_set_with_partial_custom_components(self):
        """Test creating a tool set with some custom components and some defaults."""
        # Arrange
        mock_scraper = MagicMock(spec=IScraperService)
        mock_formatter = MagicMock(spec=PriceFormatter)
        default_prompt_gen = MagicMock(spec=PromptGenerator)
        default_llm = MagicMock(spec=LLMClient)
        default_rule_analyzer = MagicMock(spec=RuleBasedAnalyzer)

        # Act & Assert
        with patch(
            "app.core.interfaces.tool_factory.BrightDataScraperService",
            return_value=mock_scraper,
        ), patch(
            "app.core.interfaces.tool_factory.create_price_analyzer_components",
            return_value=(
                MagicMock(
                    spec=PriceFormatter
                ),  # We won't use this as we provide custom formatter
                default_prompt_gen,
                default_llm,
                default_rule_analyzer,
            ),
        ):
            # Only provide custom scraper and formatter
            tool_set = create_tool_set(
                scraper_service=mock_scraper, price_formatter=mock_formatter
            )

            # Assert
            assert isinstance(tool_set, ISmartNinjaToolSet)
            assert tool_set.scraper_service == mock_scraper
            assert tool_set.price_formatter == mock_formatter
            assert tool_set.prompt_generator == default_prompt_gen
            assert tool_set.llm_client == default_llm
            assert tool_set.rule_based_analyzer == default_rule_analyzer
