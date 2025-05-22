"""
Tests for the track_price_history MCP service.

This module tests the functionality of the MCP service that stores and retrieves
price history data using async/await patterns for non-blocking operations.
"""
import asyncio
import unittest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

from app.core.history import (
    AlertNotifier,
    PriceHistoryAnalyzer,
    PriceHistoryRepository,
)
from app.mcp.track_price_history.service import (
    create_history_components,
    track_price_history_service,
    handle_store_action,
    handle_get_history_action
)


class TestTrackPriceHistoryMCPService(unittest.IsolatedAsyncioTestCase):
    """Test suite for the track_price_history MCP service with async implementation."""

    def setUp(self):
        """Set up test fixtures."""
        # Sample price entry data
        self.sample_price_entry = {
            "model": "iPhone 15 Pro",
            "country": "US",
            "price": 999.99,
            "currency": "USD",
            "source": "Amazon",
            "url": "https://www.amazon.com/example",
            "timestamp": datetime.now().isoformat(),
        }

        # Mock database components
        self.mock_repository = AsyncMock(spec=PriceHistoryRepository)
        self.mock_analyzer = AsyncMock(spec=PriceHistoryAnalyzer)
        self.mock_notifier = AsyncMock(spec=AlertNotifier)

        # Configure mock repository
        self.mock_repository.store_price_entry.return_value = "price-entry-123"
        self.mock_repository.get_history_for_model.return_value = [self.sample_price_entry]

        # Configure mock analyzer
        self.mock_analyzer.calculate_metrics.return_value = {
            "average_price": 999.99,
            "min_price": 899.99,
            "max_price": 1099.99,
            "trend": "stable",
        }

        # Configure mock notifier
        self.mock_notifier.check_alert_rules.return_value = []
        self.mock_notifier.send_alerts.return_value = True

    @patch("app.mcp.track_price_history.service.create_history_components")
    @unittest.skip("Temporariamente desabilitado durante a migração do FastAPI para módulos async puros")
    async def test_handle_store_action(self, mock_create_components):
        """Test handling store action."""
        # Configure mock components
        mock_create_components.return_value = (
            self.mock_repository,
            self.mock_analyzer,
            self.mock_notifier,
        )

        # Prepare request params
        params = {
            "action": "store",
            "price_entry": self.sample_price_entry,
        }

        # Call the function being tested
        result = await track_price_history_service(params)

        # Verify response format
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("processing_time_ms", result)

        # Verify expected values
        self.assertEqual(result["status"], "success")
        self.assertIn("stored", result["message"].lower())
        self.assertIn("entry_id", result["data"])
        self.assertEqual(result["data"]["entry_id"], "price-entry-123")
        
        # Verify component interactions
        self.mock_repository.store_price_entry.assert_called_once()
        self.mock_analyzer.calculate_metrics.assert_called_once()

    @unittest.skip("Temporariamente desabilitado durante a migração do FastAPI para módulos async puros")
    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_handle_get_history_action(self, mock_create_components):
        """Test handling get_history action."""
        # Configure mock components
        mock_create_components.return_value = (
            self.mock_repository,
            self.mock_analyzer,
            self.mock_notifier,
        )

        # Prepare request params
        params = {
            "action": "get_history",
            "model": "iPhone 15 Pro",
            "country": "US",
            "days": 30,
        }

        # Call the function being tested
        result = await track_price_history_service(params)

        # Verify response format
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("processing_time_ms", result)

        # Verify expected values
        self.assertEqual(result["status"], "success")
        self.assertIn("history", result["message"].lower())
        self.assertIn("entries", result["data"])
        self.assertIn("metrics", result["data"])
        
        # Verify component interactions
        self.mock_repository.get_history_for_model.assert_called_once()
        self.mock_analyzer.calculate_metrics.assert_called_once()

    @unittest.skip("Temporariamente desabilitado durante a migração do FastAPI para módulos async puros")
    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_handle_invalid_action(self, mock_create_components):
        """Test handling invalid action."""
        # Configure mock components
        mock_create_components.return_value = (
            self.mock_repository,
            self.mock_analyzer,
            self.mock_notifier,
        )

        # Prepare request params with invalid action
        params = {
            "action": "invalid_action",
            "price_entry": self.sample_price_entry,
        }

        # Call the function being tested
        result = await track_price_history_service(params)

        # Verify response format
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("processing_time_ms", result)

        # Verify expected values
        self.assertEqual(result["status"], "error")
        self.assertIn("invalid action", result["message"].lower())
        self.assertEqual(result["data"], [])
        
        # Verify no component interactions
        self.mock_repository.store_price_entry.assert_not_called()
        self.mock_analyzer.calculate_metrics.assert_not_called()

    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_handle_missing_action(self, mock_create_components):
        """Test handling missing action parameter."""
        # Configure mock components
        mock_create_components.return_value = (
            self.mock_repository,
            self.mock_analyzer,
            self.mock_notifier,
        )

        # Prepare request params without action
        params = {
            "price_entry": self.sample_price_entry,
        }

        # Call the function being tested
        result = await track_price_history_service(params)

        # Verify response format
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("processing_time_ms", result)

        # Verify expected values
        self.assertEqual(result["status"], "error")
        self.assertIn("missing", result["message"].lower())
        self.assertEqual(result["data"], [])
        
        # Verify no component interactions
        self.mock_repository.store_price_entry.assert_not_called()
        self.mock_analyzer.calculate_metrics.assert_not_called()

    @unittest.skip("Temporariamente desabilitado durante a migração do FastAPI para módulos async puros")
    @patch("app.mcp.track_price_history.service.create_history_components")
    async def test_handle_repository_error(self, mock_create_components):
        """Test handling repository error."""
        # Configure mock components
        mock_create_components.return_value = (
            self.mock_repository,
            self.mock_analyzer,
            self.mock_notifier,
        )
        
        # Configure repository to raise exception
        self.mock_repository.store_price_entry.side_effect = Exception("Database error")

        # Prepare request params
        params = {
            "action": "store",
            "price_entry": self.sample_price_entry,
        }

        # Call the function being tested
        result = await track_price_history_service(params)

        # Verify response format
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("data", result)
        self.assertIn("processing_time_ms", result)

        # Verify expected values
        self.assertEqual(result["status"], "error")
        self.assertIn("failed", result["message"].lower())
        self.assertEqual(result["data"], [])
        
        # Verify component interactions
        self.mock_repository.store_price_entry.assert_called_once()
        self.mock_analyzer.calculate_metrics.assert_not_called()

    async def test_create_history_components(self):
        """Test creation of history components."""
        # Apply patch to SQLitePriceHistoryRepository
        with patch("app.mcp.track_price_history.service.SQLitePriceHistoryRepository") as mock_repo_class:
            # Configure mocks
            mock_repo = AsyncMock(spec=PriceHistoryRepository)
            mock_repo_class.return_value = mock_repo
            
            # Call the function
            repository, analyzer, notifier = await create_history_components()
            
            # Verify component types
            self.assertEqual(repository, mock_repo)
            self.assertIsInstance(analyzer, PriceHistoryAnalyzer)
            self.assertIsInstance(notifier, AlertNotifier)


if __name__ == "__main__":
    unittest.main()
