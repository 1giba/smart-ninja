"""
Tests for the price formatter components.
"""
# pylint: disable=missing-function-docstring,missing-class-docstring,attribute-defined-outside-init
import pytest

from app.core.analyzer.formatting.price_formatter import BasicPriceFormatter


class TestBasicPriceFormatter:
    """Test suite for the BasicPriceFormatter class."""

    def setup_method(self):
        """Set up test environment before each test method."""
        self.formatter = BasicPriceFormatter()
        self.sample_data = [
            {
                "model": "iPhone 13",
                "region": "US",
                "price": 799.99,
                "currency": "USD",
                "store": "Apple Store",
                "timestamp": "2023-01-01",
            },
            {
                "model": "iPhone 13",
                "region": "EU",
                "price": 899.99,
                "currency": "EUR",
                "store": "MediaMarkt",
                "timestamp": "2023-01-01",
            },
            {
                "model": "Samsung Galaxy S22",
                "region": "US",
                "price": 699.99,
                "currency": "USD",
                "store": "Best Buy",
                "timestamp": "2023-01-01",
            },
        ]

    def test_format_price_data(self):
        """Test that price data is formatted correctly."""
        formatted = self.formatter.format_price_data(self.sample_data)

        # Check that result is a string
        assert isinstance(formatted, str)

        # Check that all key information is included
        assert "iPhone 13 - Apple Store: 799.99 USD (2023-01-01)" in formatted
        assert "iPhone 13 - MediaMarkt: 899.99 EUR (2023-01-01)" in formatted
        assert "Samsung Galaxy S22 - Best Buy: 699.99 USD (2023-01-01)" in formatted

        # Check that the right number of lines are created
        assert len(formatted.strip().split("\n")) == 4  # Including header line

    def test_format_empty_data(self):
        """Test that empty data results in empty string."""
        formatted = self.formatter.format_price_data([])
        assert formatted == "No price data available."

    def test_format_incomplete_data(self):
        """Test that incomplete data is handled gracefully."""
        incomplete_data = [{"model": "Test Phone"}]
        formatted = self.formatter.format_price_data(incomplete_data)
        assert "Test Phone - Unknown: N/A USD" in formatted


if __name__ == "__main__":
    pytest.main(["-v", "test_price_formatter.py"])
