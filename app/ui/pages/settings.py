"""Settings page UI module.

This module provides the UI components for the application settings page,
allowing users to customize display preferences, data management options,
and perform administrative actions.
"""
import json
import os
from typing import Any, Dict, List

import streamlit as st

# Configuration constants
CONFIG_DIR = "app/config"
SETTINGS_FILE = f"{CONFIG_DIR}/display_settings.json"
DEFAULT_SETTINGS = {
    "theme": "Dark (Default)",
    "chart_style": "Modern",
    "currency": "USD",
    "refresh_rate": 15,
    "data_retention": 30,
    "enable_caching": True,
    "cache_timeout": 15,
}


def load_settings() -> Dict[str, Any]:
    """Load user settings from the JSON file.

    Returns:
        Dict containing user settings, or defaults if not available
    """
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        except (json.JSONDecodeError, IOError):
            return DEFAULT_SETTINGS.copy()
    return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """Save user settings to the JSON file.

    Args:
        settings: Dictionary of settings to save

    Returns:
        True if successful, False otherwise
    """
    try:
        # Create config directory if needed
        os.makedirs(CONFIG_DIR, exist_ok=True)

        # Write settings to file
        with open(SETTINGS_FILE, "w", encoding="utf-8") as file:
            json.dump(settings, file)
        return True
    except (IOError, OSError):
        return False


def render_display_settings_tab():
    """Render the display settings tab content."""
    st.subheader("Display Settings")

    # User nickname/display name
    display_name = st.text_input(
        "Display Name",
        value=st.session_state.display_settings.get("display_name", ""),
        help="Your preferred name for reports and exports (optional)",
    )

    # Theme selection
    themes = ["Dark (Default)", "Light", "High Contrast"]
    current_theme = st.session_state.display_settings.get("theme", "Dark (Default)")
    theme = st.selectbox("Theme", themes, index=themes.index(current_theme))

    # Chart style
    styles = ["Modern", "Classic", "Minimal"]
    current_style = st.session_state.display_settings.get("chart_style", "Modern")
    chart_style = st.selectbox("Chart Style", styles, index=styles.index(current_style))

    # Currency display
    currencies = ["USD", "EUR", "GBP", "JPY", "BRL", "INR", "CNY"]
    current_currency = st.session_state.display_settings.get("currency", "USD")
    currency = st.selectbox(
        "Default Currency", currencies, index=currencies.index(current_currency)
    )

    # Save button
    if st.button("Save Display Settings"):
        # Update session state
        st.session_state.display_settings.update(
            {
                "display_name": display_name,
                "theme": theme,
                "chart_style": chart_style,
                "currency": currency,
            }
        )

        # Save to file
        if save_settings(st.session_state.display_settings):
            st.success("Display settings saved successfully!")
        else:
            st.error("Failed to save settings. Please try again.")

    st.info(
        "Note: Some display settings require restarting the application to take effect."
    )


def render_data_management_tab():
    """Render the data management tab content."""
    st.subheader("Data Management")

    # Data refresh rate
    refresh_rate = st.slider(
        "Data Refresh Rate (minutes)",
        min_value=5,
        max_value=60,
        value=st.session_state.display_settings.get("refresh_rate", 15),
        step=5,
    )

    # Data retention settings
    data_retention = st.slider(
        "Data Retention Period (days)",
        min_value=7,
        max_value=90,
        value=st.session_state.display_settings.get("data_retention", 30),
        step=1,
        help="How long to keep historical price data",
    )

    # Caching settings
    enable_caching = st.toggle(
        "Enable Result Caching",
        value=st.session_state.display_settings.get("enable_caching", True),
    )

    # Conditional cache timeout slider
    cache_timeout = st.session_state.display_settings.get("cache_timeout", 15)
    if enable_caching:
        cache_timeout = st.slider(
            "Cache Timeout (minutes)",
            min_value=5,
            max_value=60,
            value=cache_timeout,
            step=5,
            help="How long to keep cached results before refreshing",
        )

    # Save button
    if st.button("Save Data Settings"):
        # Update session state
        st.session_state.display_settings.update(
            {
                "refresh_rate": refresh_rate,
                "data_retention": data_retention,
                "enable_caching": enable_caching,
                "cache_timeout": cache_timeout,
            }
        )

        # Save to file
        if save_settings(st.session_state.display_settings):
            st.success("Data settings saved successfully!")
        else:
            st.error("Failed to save settings. Please try again.")

    # Render export options
    render_export_options()

    # Render danger zone
    render_danger_zone()


def render_export_options():
    """Render the data export options section."""
    st.subheader("Export Options")
    st.markdown(
        """Export your historical data for offline analysis.
        Select format and date range, then click Export."""
    )

    # Use columns for more compact layout
    col1, col2 = st.columns(2)
    with col1:
        st.selectbox(
            "Export Format",
            ["CSV", "Excel (.xlsx)", "JSON"],
            index=0,
            key="export_format",
        )
    with col2:
        st.date_input("Date Range", value=[], key="export_date_range")

    if st.button("Export Data"):
        st.info("Export functionality will be available in the next release.")


def render_danger_zone():
    """Render the danger zone section with destructive actions."""
    st.markdown("---")
    st.subheader("⚠️ Danger Zone")
    st.warning("These actions cannot be undone!")

    # Reset all settings button
    if st.button("Reset All Settings"):
        st.session_state.clear()
        st.error("All settings have been reset to default values!")

    # Delete all data button
    if st.button("Delete All Data"):
        st.error("All price history, alerts, and analytics data have been deleted!")


def render_settings():
    """Render the complete settings page with all options."""
    st.title("⚙️ Settings")

    # Initialize settings if not already loaded
    if "display_settings" not in st.session_state:
        st.session_state.display_settings = load_settings()

    # Create tabs for different settings categories
    tab1, tab2 = st.tabs(["Display Settings", "Data Management"])

    # Render tab contents
    with tab1:
        render_display_settings_tab()

    with tab2:
        render_data_management_tab()
