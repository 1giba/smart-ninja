"""
Tests for the track_price_history service with required parameters.

This module tests that the track_price_history service correctly validates
and handles required parameters like 'country' in get_history operations.
"""
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

import pytest

from app.mcp.track_price_history.service import (
    track_price_history_service,
    handle_get_history_action
)


class TestTrackPriceHistoryParams(unittest.IsolatedAsyncioTestCase):
    """Test suite for track_price_history service parameter handling."""

    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_get_history_validates_country_parameter(self, mock_create_components):
        """Test that get_history action validates the country parameter."""
        # Set up mocks
        mock_repository = AsyncMock()
        mock_analyzer = MagicMock()
        mock_notifier = AsyncMock()
        mock_create_components.return_value = (mock_repository, mock_analyzer, mock_notifier)
        
        # Call the service without country parameter
        result = await track_price_history_service({
            "action": "get_history",
            "model": "iPhone 14"
        })
        
        # Verify error response
        self.assertEqual(result["status"], "error")
        self.assertIn("Missing required parameter: 'country'", result["message"])
        
        # Verify components were created but repository.get_price_history was not called
        mock_create_components.assert_called_once()
        mock_repository.get_price_history.assert_not_called()

    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_get_history_with_valid_parameters(self, mock_create_components):
        """Test that get_history action works with valid parameters."""
        # Set up mocks
        mock_repository = AsyncMock()
        mock_analyzer = MagicMock()
        mock_notifier = AsyncMock()
        
        # Set up mock return values
        mock_history_data = [
            {"date": "2023-01-01", "price": 999.99, "store": "Test Store"}
        ]
        mock_repository.get_price_history.return_value = mock_history_data
        mock_analyzer.compute_metrics.return_value = {"avg_price": 999.99}
        
        mock_create_components.return_value = (mock_repository, mock_analyzer, mock_notifier)
        
        # Call the service with all required parameters
        result = await track_price_history_service({
            "action": "get_history",
            "model": "iPhone 14",
            "country": "US",
            "days": 30
        })
        
        # Verify success response
        self.assertEqual(result["status"], "success")
        self.assertIn("Retrieved 1 price points", result["message"])
        
        # Verify repository was called with correct parameters
        mock_repository.get_price_history.assert_called_once()
        args, kwargs = mock_repository.get_price_history.call_args
        self.assertEqual(args[0], "iPhone 14")  # model
        self.assertEqual(args[1], "US")  # country
        
        # Verify response data structure
        self.assertIn("history", result["data"])
        self.assertIn("metrics", result["data"])
        self.assertIn("filters", result["data"])
        self.assertEqual(result["data"]["filters"]["model"], "iPhone 14")
        self.assertEqual(result["data"]["filters"]["country"], "US")

    @patch("app.mcp.track_price_history.service.PriceHistoryRepository", autospec=True)
    @patch("app.mcp.track_price_history.service.PriceHistoryAnalyzer", autospec=True)
    async def test_handle_get_history_passes_country_to_repository(self, mock_analyzer_class, mock_repository_class):
        """Test that handle_get_history_action passes country to repository.get_price_history."""
        # Set up mocks
        mock_repository = MagicMock()
        mock_repository.get_price_history = AsyncMock(return_value=[])
        
        mock_analyzer = MagicMock()
        mock_analyzer.compute_metrics.return_value = {}
        
        # Set up parameters
        params = {
            "model": "iPhone 14",
            "country": "US",
            "days": 30
        }
        
        # Call the function
        result = await handle_get_history_action(params, mock_repository, mock_analyzer)
        
        # Verify repository was called with correct parameters
        mock_repository.get_price_history.assert_called_once()
        args, kwargs = mock_repository.get_price_history.call_args
        self.assertEqual(args[0], "iPhone 14")  # model
        self.assertEqual(args[1], "US")  # country
        
        # Verify result has country in filters
        self.assertEqual(result["data"]["filters"]["country"], "US")


if __name__ == "__main__":
    unittest.main()
