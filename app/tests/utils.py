"""
Utility functions for testing SmartNinja application.
Provides mock session states and other test helpers.
"""
# pylint: disable=unused-import
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import streamlit as st


def setup_test_env():
    """Set up the test environment"""
    # Add parent directory to path for imports
    parent = Path(__file__).parent.parent.parent
    if str(parent) not in sys.path:
        sys.path.insert(0, str(parent))


def mock_session_state():
    """
    Initialize a mock session state for Streamlit UI tests
    """
    # Initialize session state with default values
    # Create a dictionary with session state values
    default_values = {
        "api_settings": {
            "bright_data_key": "test_bright_data_key",
            "openai_api_key": "test_openai_api_key",
        },
        "selected_model": "iPhone 15 Pro",
        "selected_region": "US",
        "compare_models": [
            "iPhone 15 Pro",
            "Samsung Galaxy S24 Ultra",
            "Google Pixel 8 Pro",
        ],
        "compare_regions": ["US", "EU", "BR"],
        "price_alerts": [
            {
                "id": "alert-1",
                "model": "iPhone 15 Pro",
                "condition": "below",
                "price": 900,
                "region": "US",
                "active": True,
            },
            {
                "id": "alert-2",
                "model": "Samsung Galaxy S24",
                "condition": "above",
                "price": 1000,
                "region": "EU",
                "active": True,
            },
        ],
        "price_history": [
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 999,
                "date": "2025-05-01",
            },
            {
                "model": "iPhone 15 Pro",
                "region": "US",
                "price": 989,
                "date": "2025-05-02",
            },
        ],
    }
    # Apply all values to session state
    for key, value in default_values.items():
        if isinstance(st.session_state, dict):
            st.session_state[key] = value
        else:
            setattr(st.session_state, key, value)
    return st.session_state


class MockStreamlit:
    """
    A class to mock Streamlit components for testing
    """

    @staticmethod
    def patch_all():
        """Patch all Streamlit components"""
        patches = []
        # Define components to patch
        components = [
            "title",
            "header",
            "subheader",
            "markdown",
            "text",
            "button",
            "checkbox",
            "radio",
            "selectbox",
            "multiselect",
            "slider",
            "text_input",
            "number_input",
            "text_area",
            "date_input",
            "time_input",
            "file_uploader",
            "color_picker",
            "image",
            "video",
            "audio",
            "pyplot",
            "altair_chart",
            "line_chart",
            "area_chart",
            "bar_chart",
            "progress",
            "spinner",
            "balloons",
            "error",
            "warning",
            "info",
            "success",
            "exception",
            "sidebar",
            "columns",
            "tabs",
            "expander",
        ]
        # Create patches
        for component in components:
            mock = MagicMock()
            patch_obj = patch(f"streamlit.{component}", mock)
            patches.append((component, patch_obj, mock))
        return patches
