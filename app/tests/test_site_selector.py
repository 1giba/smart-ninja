"""
Unit tests for the Site Selector.
Tests the component that determines optimal scraping targets based on various criteria.
"""
import unittest

# pylint: disable=unused-import
from unittest.mock import Mock, patch

# pylint: disable=no-name-in-module,no-member,import-error
from app.core.scraping.site_selector import SiteSelector


class TestSiteSelector(unittest.TestCase):
    """Test suite for the Site Selector implementation"""

    def setUp(self):
        """Set up test dependencies"""
        self.selector = SiteSelector()

    def test_select_sites_with_model_and_country(self):
        """Test site selection based on model and country"""
        # Basic input data
        input_data = {"model": "iPhone 15", "country": "US"}

        # Execute the selector
        sites = self.selector.determine_optimal_scraping_targets(input_data)

        # Verify results
        self.assertIsInstance(sites, list)
        self.assertGreater(len(sites), 0)
        self.assertIn("amazon.com", sites)  # Expect amazon.com for US

    def test_select_sites_with_user_preferences(self):
        """Test site selection with user preferences"""
        # Input data with user preferences
        input_data = {
            "model": "Samsung Galaxy S23",
            "country": "US",
            "user_preferences": {"preferred_retailers": ["bestbuy.com", "samsung.com"]},
        }

        # Execute the selector
        sites = self.selector.determine_optimal_scraping_targets(input_data)

        # Verify the preferred retailers are at the beginning of the list
        self.assertIsInstance(sites, list)
        self.assertGreater(len(sites), 0)
        self.assertEqual(sites[0], "bestbuy.com")
        self.assertEqual(sites[1], "samsung.com")

    def test_select_sites_with_performance_data(self):
        """Test site selection with historical performance data"""
        # Mock performance data that shows amazon.com has higher success rate
        with patch.object(
            SiteSelector, "_retrieve_site_performance_metrics"
        ) as mock_perf:
            mock_perf.return_value = {
                "amazon.com": {"success_rate": 0.95, "data_quality": 0.9},
                "bestbuy.com": {"success_rate": 0.7, "data_quality": 0.8},
                "walmart.com": {"success_rate": 0.6, "data_quality": 0.7},
            }

            input_data = {"model": "iPhone 15", "country": "US"}

            # Execute the selector
            sites = self.selector.determine_optimal_scraping_targets(input_data)

            # Verify amazon.com is first due to better performance
            self.assertIsInstance(sites, list)
            self.assertGreater(len(sites), 0)
            self.assertEqual(sites[0], "amazon.com")

    def test_select_sites_with_device_specific_retailers(self):
        """Test selection of device-specific retail sites"""
        # Test with Apple product
        apple_input = {"model": "iPhone 15", "country": "US"}
        apple_sites = self.selector.determine_optimal_scraping_targets(apple_input)

        # Should include Apple's store
        self.assertIn("apple.com", apple_sites)

        # Test with Samsung product
        samsung_input = {"model": "Galaxy S23", "country": "US"}
        samsung_sites = self.selector.determine_optimal_scraping_targets(samsung_input)

        # Should include Samsung's store
        self.assertIn("samsung.com", samsung_sites)

    def test_limit_sites_returned(self):
        """Test limiting the number of sites returned"""
        input_data = {"model": "iPhone 15", "country": "US", "max_sites": 3}

        # Execute the selector
        sites = self.selector.determine_optimal_scraping_targets(input_data)

        # Verify we get exactly 3 sites
        self.assertEqual(len(sites), 3)

    def test_handle_invalid_input(self):
        """Test handling of invalid input"""
        # Missing model
        with self.assertRaises(ValueError):
            self.selector.determine_optimal_scraping_targets({"country": "US"})

        # Missing country
        with self.assertRaises(ValueError):
            self.selector.determine_optimal_scraping_targets({"model": "iPhone 15"})

    def test_select_sites_with_region_preference(self):
        """Test site selection with regional preferences"""
        # Input with region preference
        input_data = {"model": "iPhone 15", "country": "US", "region": "West Coast"}

        # Execute with region preference
        sites = self.selector.determine_optimal_scraping_targets(input_data)

        # Should return sites relevant to the region
        self.assertIsInstance(sites, list)
        self.assertGreater(len(sites), 0)
        # Regional logic will be implemented in the SiteSelector


if __name__ == "__main__":
    unittest.main()
