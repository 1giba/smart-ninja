"""
Test cases for the AnalysisAgent using SmartNinjaToolSet.
Tests the functionality of the agent with unified toolset integration.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.agents.analysis_agent import AnalysisAgent
from app.core.interfaces.tool_set import ISmartNinjaToolSet


class TestAnalysisAgent:
    """Tests for the AnalysisAgent using SmartNinjaToolSet."""

    @pytest.fixture
    def mock_tool_set(self):
        """Create a mock SmartNinjaToolSet with async methods."""
        mock = AsyncMock(spec=ISmartNinjaToolSet)
        mock.normalize_data.return_value = "Formatted data"
        mock.generate_prompt.return_value = "Analysis prompt"
        mock.get_ai_analysis.return_value = "AI analysis result"
        mock.get_rule_analysis.return_value = "Rule-based analysis result"
        mock.process_price_analysis.return_value = "Complete price analysis"
        return mock

    @pytest.fixture
    def analysis_agent(self, mock_tool_set):
        """Create an AnalysisAgent with a mock tool set."""
        return AnalysisAgent(tool_set=mock_tool_set)

    def test_initialization_with_default_tool_set(self):
        """Test initialization with default tool set."""
        with patch(
            "app.core.agents.analysis_agent.create_tool_set"
        ) as mock_create_tool_set:
            # Create a mock tool set that will be returned by create_tool_set
            mock_tool_set = MagicMock(spec=ISmartNinjaToolSet)
            mock_create_tool_set.return_value = mock_tool_set

            # Create the agent without providing a tool set
            agent = AnalysisAgent()

            # Verify create_tool_set was called
            mock_create_tool_set.assert_called_once()

            # Verify the agent was initialized with our mock tool set
            assert agent._tool_set is mock_tool_set  # Use 'is' for identity check

    @pytest.mark.asyncio
    async def test_analyze_prices_success(self, analysis_agent, mock_tool_set):
        """Test successful price analysis."""
        # Arrange
        price_data = [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}]

        # Act
        result = await analysis_agent.analyze_prices(price_data)

        # Assert
        mock_tool_set.normalize_data.assert_called_once_with(price_data)
        mock_tool_set.generate_prompt.assert_called_once_with("Formatted data")
        mock_tool_set.get_ai_analysis.assert_called_once_with("Analysis prompt")
        assert result == "AI analysis result"
        # Verify rule-based analysis wasn't used
        mock_tool_set.get_rule_analysis.assert_not_called()

    @pytest.mark.asyncio
    async def test_analyze_prices_fallback_to_rules(self, analysis_agent, mock_tool_set):
        """Test fallback to rule-based analysis when AI analysis fails."""
        # Arrange
        price_data = [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}]
        mock_tool_set.get_ai_analysis.return_value = None

        # Act
        result = await analysis_agent.analyze_prices(price_data)

        # Assert
        mock_tool_set.normalize_data.assert_called_once_with(price_data)
        mock_tool_set.generate_prompt.assert_called_once_with("Formatted data")
        mock_tool_set.get_ai_analysis.assert_called_once_with("Analysis prompt")
        mock_tool_set.get_rule_analysis.assert_called_once_with(price_data)
        assert result == "Rule-based analysis result"

    @pytest.mark.asyncio
    async def test_analyze_prices_with_error(self, analysis_agent, mock_tool_set):
        """Test handling of errors during analysis."""
        # Arrange
        price_data = [{"model": "iPhone 15", "price": 999.99, "currency": "USD"}]
        mock_tool_set.normalize_data.side_effect = Exception("Test error")

        # Act
        result = await analysis_agent.analyze_prices(price_data)

        # Assert
        mock_tool_set.normalize_data.assert_called_once_with(price_data)
        mock_tool_set.get_rule_analysis.assert_called_once_with(price_data)
        assert result == "Rule-based analysis result"

    @pytest.mark.asyncio
    async def test_process_analysis_request(self, analysis_agent, mock_tool_set):
        """Test the process_analysis_request method."""
        # Arrange
        model = "iPhone 15"
        country = "US"

        # Act
        result = await analysis_agent.process_analysis_request(model, country)

        # Assert
        mock_tool_set.process_price_analysis.assert_called_once_with(model, country)
        assert result == "Complete price analysis"
