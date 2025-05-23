"""
Tests for price history date parameters functionality.

This module contains tests for the date parameter functionality in the
price history repository and service, following async patterns.
"""
import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from app.core.history import (
    PriceHistoryRepository,
    SQLitePriceHistoryRepository
)
from app.mcp.track_price_history.service import handle_get_history_action


class TestPriceHistoryDateParameters(unittest.IsolatedAsyncioTestCase):
    """Test suite for price history date parameter functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample price entries
        self.sample_entries = [
            {
                "model": "iPhone 15 Pro",
                "country": "US",
                "price": 999.99,
                "currency": "USD",
                "source": "Amazon",
                "url": "https://www.amazon.com/example",
                "timestamp": datetime.now().isoformat(),
            }
        ]

        # Mock components
        self.mock_repository = AsyncMock(spec=PriceHistoryRepository)
        self.mock_analyzer = AsyncMock()
        
        # Configure repository
        self.mock_repository.get_history_for_model.return_value = self.sample_entries

    async def test_get_history_with_date_parameters(self):
        """Test retrieving history with start_date and end_date parameters."""
        # Prepare test data
        model = "iPhone 15 Pro"
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
        end_date = datetime.now().isoformat()
        
        # Prepare request params
        params = {
            "model": model,
            "country": "US",
            "start_date": start_date,
            "end_date": end_date
        }
        
        # Call the function being tested
        result = await handle_get_history_action(params, self.mock_repository, self.mock_analyzer)
        
        # Verify result format
        self.assertEqual(result["status"], "success")
        self.assertIn("data", result)
        
        # Verify repository was called with correct parameters
        self.mock_repository.get_history_for_model.assert_called_once()
        
        # The parameters should be model, country, days, cursor, limit
        # Not start_date or end_date, as these should be used internally
        args, kwargs = self.mock_repository.get_history_for_model.call_args
        self.assertEqual(args[0], model)  # Model parameter
        self.assertEqual(args[1], "US")   # Country parameter


if __name__ == "__main__":
    unittest.main()
