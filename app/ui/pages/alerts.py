# pylint: disable=unused-import
import pandas as pd  # Required by tests
import streamlit as st

from ..components import alert_card


# pylint: disable=too-many-branches
def render_alerts(regions, brands):
    """
    Render the price alerts page
    Args:
        regions: List of selected regions
        brands: List of selected brands
    """
    st.title("🔔 Price Alerts")
    # Create tabs for active alerts and create new alerts
    tab1, tab2 = st.tabs(["Active Alerts", "Create Alert"])
    with tab1:
        st.subheader("Your Active Price Alerts")
        # Display sample active alerts
        if "sample_alerts" not in st.session_state:
            st.session_state.sample_alerts = [
                {
                    "model": "iPhone 15 Pro",
                    "condition": "Price drops below",
                    "target_price": 899.99,
                    "current_price": 999.99,
                    "region": "US",
                },
                {
                    "model": "Samsung Galaxy S24 Ultra",
                    "condition": "Price drops below",
                    "target_price": 1099.99,
                    "current_price": 1199.99,
                    "region": "EU",
                },
                {
                    "model": "Google Pixel 8",
                    "condition": "Price drops below",
                    "target_price": 649.99,
                    "current_price": 699.99,
                    "region": "US",
                },
            ]
        # Display each alert as a card
        if not st.session_state.sample_alerts:
            st.info(
                "You don't have any active alerts. Create one in the 'Create Alert' tab."
            )
        else:
            for alert in st.session_state.sample_alerts:
                alert_card(
                    alert["model"],
                    alert["condition"],
                    alert["target_price"],
                    alert["current_price"],
                )
                st.markdown("---")
    with tab2:
        st.subheader("Create New Price Alert")
        # Form for creating a new alert
        with st.form("create_alert_form"):
            # Select phone model
            phone_options = []
            if "Apple" in brands:
                phone_options.extend(["iPhone 15 Pro", "iPhone 15"])
            if "Samsung" in brands:
                phone_options.extend(["Samsung Galaxy S24 Ultra", "Samsung Galaxy S24"])
            if "Google" in brands:
                phone_options.extend(["Google Pixel 8 Pro", "Google Pixel 8"])
            if "Xiaomi" in brands:
                phone_options.append("Xiaomi 14 Pro")
            if "Huawei" in brands:
                phone_options.append("Huawei P60 Pro")
            model = st.selectbox(
                "Select Phone Model", phone_options, index=0 if phone_options else None
            )
            # Select region
            region = st.selectbox(
                "Select Region", regions, index=0 if regions else None
            )
            # Select condition
            condition = st.selectbox(
                "Alert Condition",
                ["Price drops below", "Price increases above"],
                index=0,
            )
            # Enter price threshold
            base_prices = {
                "iPhone 15 Pro": 1000,
                "iPhone 15": 800,
                "Samsung Galaxy S24 Ultra": 1200,
                "Samsung Galaxy S24": 900,
                "Google Pixel 8 Pro": 900,
                "Google Pixel 8": 700,
                "Xiaomi 14 Pro": 800,
                "Huawei P60 Pro": 900,
            }
            default_price = (
                base_prices.get(model, 1000) * 0.9
                if condition == "Price drops below"
                else base_prices.get(model, 1000) * 1.1
            )
            price = st.number_input(
                "Price Threshold (USD)",
                min_value=0.0,
                max_value=5000.0,
                value=default_price,
                step=10.0,
            )
            # Form submission
            submitted = st.form_submit_button("Create Alert")
            if submitted:
                # Add the new alert to the sample alerts
                new_alert = {
                    "model": model,
                    "condition": condition,
                    "target_price": price,
                    "current_price": base_prices.get(model, 1000),
                    "region": region,
                }
                if "sample_alerts" in st.session_state:
                    st.session_state.sample_alerts.append(new_alert)
                else:
                    st.session_state.sample_alerts = [new_alert]
                st.success(f"Alert created successfully for {model} in {region}!")
        # Instructions for alerts
        st.markdown(
            """
        ### How Alerts Work
        
        1. Set a price threshold for a specific phone model in a region
        2. SmartNinja will continuously monitor prices across markets
        3. You'll be notified when the price meets your condition
        4. Alerts will remain active until you delete them
        
        > **Tip:** Set realistic price thresholds based on historical data for better results.
        """
        )
        # Alert notifications settings
        st.subheader("Alert Notifications")
        st.checkbox("Email notifications", value=True)
        st.checkbox("In-app notifications", value=True)
        # Store notification preference in session state for future use
        st.session_state.notify_frequency = st.radio(
            "Notification Frequency",
            ["Immediately", "Daily summary", "Weekly summary"],
            index=0,
        )
