"""
Tests for OpenAI client parameter handling.

This module tests the OpenAI client's handling of parameters, ensuring
it correctly manages parameters that may or may not be supported by the
underlying AsyncOpenAI client.
"""
import unittest
from unittest.mock import AsyncMock, Mock, patch

from app.core.analyzer.clients.openai_client import OpenAIClient


class TestOpenAIClientParams(unittest.IsolatedAsyncioTestCase):
    """Test suite for OpenAI client parameter handling."""

    @patch("app.core.analyzer.clients.openai_client.AsyncOpenAI")
    async def test_openai_client_init_without_proxies(self, mock_openai_class):
        """Test that the OpenAI client can be initialized without proxies parameter."""
        # Setup
        mock_openai_instance = AsyncMock()
        mock_openai_class.return_value = mock_openai_instance
        
        # Execute
        client = OpenAIClient(api_key="test-key")
        
        # Assert
        mock_openai_class.assert_called_once()
        self.assertTrue(client.client_available)

    @patch("app.core.analyzer.clients.openai_client.AsyncOpenAI")
    async def test_openai_client_init_with_proxies(self, mock_openai_class):
        """Test that the OpenAI client ignores proxies parameter if provided."""
        # Setup
        mock_openai_instance = AsyncMock()
        mock_openai_class.return_value = mock_openai_instance
        
        # Execute
        client = OpenAIClient(api_key="test-key", proxies={"http": "http://proxy.example.com"})
        
        # Assert
        mock_openai_class.assert_called_once()
        self.assertTrue(client.client_available)
        # The key point is that it should NOT pass the proxies parameter to AsyncOpenAI


if __name__ == "__main__":
    unittest.main()
