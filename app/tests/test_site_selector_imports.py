"""
Test imports for the site_selector module.
Verify that the site_selector module can be imported correctly.
"""
import unittest

# pylint: disable=no-name-in-module,no-member,import-error
from app.core.scraping.site_selector import SiteSelector


class TestSiteSelectorImports(unittest.TestCase):
    """Test proper imports for the SiteSelector module"""

    def test_site_selector_can_be_imported(self):
        """Test that SiteSelector can be imported from the correct module"""
        try:
            site_selector = SiteSelector()
            self.assertIsNotNone(site_selector)
            self.assertTrue(
                hasattr(site_selector, "determine_optimal_scraping_targets")
            )
        except ImportError:
            self.fail(
                "Failed to import SiteSelector from app.core.scraping.site_selector"
            )


if __name__ == "__main__":
    unittest.main()
