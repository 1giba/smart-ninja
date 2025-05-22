import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
async def render_history(regions, brands):
    """
    Render the price history page using async services
    
    Args:
        regions: List of selected regions
        brands: List of selected brands
    """
    st.title("📜 Price History")
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
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
        selected_model = st.selectbox(
            "Select Phone Model", phone_options, index=0 if phone_options else None
        )
    with col2:
        # Select region
        selected_region = st.selectbox(
            "Select Region", regions, index=0 if regions else None
        )
    with col3:
        # Select time period
        time_period = st.selectbox(
            "Time Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "Last year"],
            index=1,
        )
    # Fetch real price history data for the selected filters
    if selected_model and selected_region:
        # Create loading placeholder
        loading_placeholder = st.empty()
        loading_placeholder.info(f"Fetching price history for {selected_model} in {selected_region}...")
        
        # Convert time period to days
        days = {
            "Last 7 days": 7,
            "Last 30 days": 30,
            "Last 90 days": 90,
            "Last year": 365,
        }.get(time_period, 30)
        
        try:
            # Import necessary modules here to avoid circular imports
            from app.mcp.track_price_history.service import track_price_history_service
            from app.ui.async_bridge import AsyncBridge
            
            # Prepare parameters for the price history service
            params = {
                "action": "get_history",
                "model": selected_model,
                "country": selected_region,
                "days": days
            }
            
            # Define a wrapper function that properly awaits the coroutine
            async def fetch_price_history(params):
                return await track_price_history_service(params)
                
            # Call the service asynchronously with the proper wrapper
            result = AsyncBridge.run_async(fetch_price_history(params))
            loading_placeholder.empty()
            
            # Check if the service call was successful
            if result.get("status") == "success":
                history_data = result.get("data", {}).get("history", [])
                
                # If data was found, format it for the chart
                if history_data:
                    price_data = [
                        {
                            "Date": entry.get("date"),
                            "Price": entry.get("price"),
                            "Model": selected_model,
                            "Region": selected_region,
                        }
                        for entry in history_data
                    ]
                else:
                    st.warning(f"No price history found for {selected_model} in {selected_region}.")
                    price_data = []
            else:
                # Handle error from the service
                error_message = result.get("message", "Unknown error fetching price history")
                st.error(error_message)
                price_data = []
                
        except Exception as e:
            # Handle any exceptions
            import logging
            logging.error(f"Error fetching price history: {str(e)}")
            st.error(f"An error occurred while fetching price history: {str(e)}")
            price_data = []
        # Create dataframe
        price_history_frame = pd.DataFrame(price_data)
        
        # Create the price history chart if we have data
        if not price_history_frame.empty and "Date" in price_history_frame.columns and "Price" in price_history_frame.columns:
            fig = px.line(
                price_history_frame,
                x="Date",
                y="Price",
                title=f"{selected_model} Price History in {selected_region}",
                labels={"Price": "Price (USD)", "Date": "Date"},
                template="plotly_dark",
            )
        else:
            # Create empty figure with message if no data
            fig = px.line(title=f"No price history data for {selected_model} in {selected_region}")
            fig.add_annotation(
                text="No data available. Try a different model or region.",
                showarrow=False,
                font={"size": 14, "color": "#FFFFFF"},
                xref="paper", yref="paper",
                x=0.5, y=0.5
            )
        fig.update_layout(
            plot_bgcolor="#1B2A41",
            paper_bgcolor="#1B2A41",
            font={"color": "#FFFFFF"},
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Calculate price statistics only if we have data with the right columns
        if not price_history_frame.empty and "Price" in price_history_frame.columns and len(price_history_frame) > 1:
            # Calculate price statistics
            min_price = price_history_frame["Price"].min()
            max_price = price_history_frame["Price"].max()
            avg_price = price_history_frame["Price"].mean()
            current_price = price_history_frame["Price"].iloc[-1]
            price_change = current_price - price_history_frame["Price"].iloc[0]
            price_change_pct = (price_change / price_history_frame["Price"].iloc[0]) * 100 if price_history_frame["Price"].iloc[0] != 0 else 0
            
            # Display price statistics
            st.subheader("Price Statistics")
            stat_col1, stat_col2, stat_col3 = st.columns(3)
            with stat_col1:
                st.metric(
                    "Current Price", f"${current_price:.2f}", f"{price_change_pct:.2f}%"
                )
            with stat_col2:
                st.metric("Average Price", f"${avg_price:.2f}")
            with stat_col3:
                st.metric("Price Range", f"${min_price:.2f} - ${max_price:.2f}")
                
            # Price history table
            st.subheader("Price History Table")
            # Resample the data to show fewer points based on the time period
            resampled_df = price_history_frame.copy()
            if days > 60:
                # For longer periods, show weekly data
                weekly_data = []
                for i in range(0, len(price_history_frame), 7):
                    if i + 7 <= len(price_history_frame):
                        weekly_data.append(
                            {
                                "Date": price_history_frame["Date"].iloc[i],
                                "Price": f"${price_history_frame['Price'].iloc[i]:.2f}",
                                "Model": selected_model,
                                "Region": selected_region,
                            }
                        )
                resampled_df = pd.DataFrame(weekly_data)
            else:
                # For shorter periods, show daily data with formatted price
                resampled_df["Price"] = resampled_df["Price"].apply(lambda x: f"${x:.2f}")
                
            # Display the table
            if not resampled_df.empty and "Date" in resampled_df.columns and "Price" in resampled_df.columns:
                st.dataframe(
                    resampled_df,
                    use_container_width=True,
                    column_config={
                        "Date": st.column_config.TextColumn("Date"),
                        "Price": st.column_config.TextColumn("Price (USD)"),
                    },
                    hide_index=True,
                )
            else:
                st.warning("No price history data available to display statistics.")
                st.info("Try selecting a different model or region.")
        else:
            st.warning("No price history data available to display statistics.")
            st.info("Try selecting a different model or region.")
        # Export options - only show if we have data
        if not price_history_frame.empty:
            st.download_button(
                label="Export Data (CSV)",
                data=price_history_frame.to_csv(index=False).encode("utf-8"),
                file_name=f"{selected_model.replace(' ', '_')}_{selected_region}_price_history.csv",
                mime="text/csv",
            )
    else:
        st.warning("Please select a phone model and region to view price history.")
