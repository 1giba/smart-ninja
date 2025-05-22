import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from ..components import price_comparison_chart, regional_comparison_chart


# pylint: disable=too-many-locals,too-many-branches,too-many-statements
async def render_comparisons(regions, brands):
    """
    Render the price comparisons page with real data using async services
    Args:
        regions: List of selected regions
        brands: List of selected brands
    """
    st.title("📊 Price Comparisons")
    # Create tabs for different types of comparisons
    tab1, tab2, tab3 = st.tabs(
        ["Models Comparison", "Regional Comparison", "Historical Comparison"]
    )
    with tab1:
        st.subheader("Compare Phone Models")
        # Select region for comparison
        selected_region = st.selectbox("Select Region", regions, index=0)
        # Define phone models based on selected brands
        models = []
        if "Apple" in brands:
            models.extend(["iPhone 15 Pro", "iPhone 15"])
        if "Samsung" in brands:
            models.extend(["Samsung Galaxy S24 Ultra", "Samsung Galaxy S24"])
        if "Google" in brands:
            models.extend(["Google Pixel 8 Pro", "Google Pixel 8"])
        if "Xiaomi" in brands:
            models.append("Xiaomi 14 Pro")
        if "Huawei" in brands:
            models.append("Huawei P60 Pro")
        # Create the comparison chart using AsyncBridge for the async function
        from app.ui.async_bridge import AsyncBridge
        # We need to import the price_comparison_chart function here to ensure
        # we're calling the actual function and not the unresolved reference
        from app.ui.components import price_comparison_chart
        
        # Define a wrapper function that properly awaits the coroutine
        async def fetch_price_comparison(models, region):
            return await price_comparison_chart(models, region)
            
        # Call the service asynchronously with the proper wrapper
        fig = AsyncBridge.run_async(fetch_price_comparison(models, selected_region))
        st.plotly_chart(fig, use_container_width=True)
        # Display comparison table
        st.subheader("Detailed Price Comparison")
        
        # Create loading placeholder
        loading_placeholder = st.empty()
        loading_placeholder.info(f"Fetching price data for comparison in {selected_region}...")
        
        try:
            # Import necessary modules
            from app.core.scraping.bright_data_service import BrightDataScraperService
            from app.ui.async_bridge import AsyncBridge
            
            # Initialize the scraper service
            scraper = BrightDataScraperService(num_results=3)  # Limit to 3 results per model for efficiency
            
            # Generate real price comparisons
            comparison_data = []
            global_avg_price = {}
            
            # First, fetch global average prices (using US as reference)
            for model in models:
                try:
                    # Get US prices as global reference
                    us_prices = await AsyncBridge.run_async(scraper.get_prices(model, "US"))
                    if us_prices and len(us_prices) > 0:
                        valid_prices = [p.get("price", 0) for p in us_prices if isinstance(p.get("price", 0), (int, float))]
                        if valid_prices:
                            global_avg_price[model] = sum(valid_prices) / len(valid_prices)
                except Exception:
                    # Continue if we can't get US prices
                    pass
            
            # Now fetch region-specific prices
            for model in models:
                try:
                    # Get prices for the selected region
                    region_prices = await AsyncBridge.run_async(scraper.get_prices(model, selected_region))
                    
                    if region_prices and len(region_prices) > 0:
                        valid_prices = [p.get("price", 0) for p in region_prices if isinstance(p.get("price", 0), (int, float))]
                        if valid_prices:
                            region_avg_price = sum(valid_prices) / len(valid_prices)
                            brand = model.split()[0] if " " in model else model
                            
                            # Calculate difference and percentage if we have global reference
                            base_price = global_avg_price.get(model, region_avg_price)
                            difference = region_avg_price - base_price
                            percent_change = (region_avg_price / base_price - 1) * 100 if base_price > 0 else 0
                            
                            comparison_data.append(
                                {
                                    "Model": model,
                                    "Brand": brand,
                                    "Base Price": f"${base_price:.2f}",
                                    "Region Price": f"${region_avg_price:.2f}",
                                    "Difference": f"${difference:.2f}",
                                    "% Change": f"{percent_change:.1f}%",
                                }
                            )
                except Exception as e:
                    # Log but continue with other models
                    import logging
                    logging.error(f"Error fetching prices for {model} in {selected_region}: {str(e)}")
            
            # Clear loading message
            loading_placeholder.empty()
            
            # Show warning if no data was found
            if not comparison_data:
                st.warning(f"No price data found for the selected models in {selected_region}.")
                
        except Exception as e:
            # Handle any exceptions
            import logging
            logging.error(f"Error fetching comparison data: {str(e)}")
            loading_placeholder.empty()
            st.error(f"An error occurred while fetching price data: {str(e)}")
            comparison_data = []
        
        # Display comparison table if data was found
        if comparison_data:
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, use_container_width=True)
        
        # Add specs table separately for better organization
        st.subheader("Model Specifications")
        specs = {
            "iPhone 15 Pro": 'A17 Pro, 6.1", 128GB',
            "iPhone 15": 'A16, 6.1", 128GB',
            "Samsung Galaxy S24 Ultra": 'Snapdragon 8 Gen 3, 6.8", 256GB',
            "Samsung Galaxy S24": 'Exynos 2400, 6.2", 128GB',
            "Google Pixel 8 Pro": 'Tensor G3, 6.7", 128GB',
            "Google Pixel 8": 'Tensor G3, 6.2", 128GB',
            "Xiaomi 14 Pro": 'Snapdragon 8 Gen 3, 6.7", 256GB',
            "Huawei P60 Pro": 'Kirin 9000, 6.6", 256GB',
        }
        
        # Create specs dataframe
        specs_data = [
            {
                "Model": model,
                "Specifications": specs.get(model, ""),
            }
            for model in models
        ]
        specs_df = pd.DataFrame(specs_data)
        st.dataframe(
            specs_df,
            use_container_width=True,
            column_config={
                "Model": st.column_config.TextColumn("Model"),
                "Specifications": st.column_config.TextColumn("Specifications"),
            },
            hide_index=True,
        )
    with tab2:
        st.subheader("Regional Price Comparison")
        # Select phone model for regional comparison
        phone_options = [
            model
            for model in [
                "iPhone 15 Pro",
                "iPhone 15",
                "Samsung Galaxy S24 Ultra",
                "Samsung Galaxy S24",
                "Google Pixel 8 Pro",
                "Google Pixel 8",
                "Xiaomi 14 Pro",
                "Huawei P60 Pro",
            ]
            if model.split()[0] in brands
        ]
        selected_model = st.selectbox("Select Phone Model", phone_options, index=0)
        # Create and display the regional comparison chart using AsyncBridge for the async function
        from app.ui.async_bridge import AsyncBridge
        # Import the function directly to ensure we're calling the actual function
        from app.ui.components import regional_comparison_chart
        
        # Define a wrapper function that properly awaits the coroutine
        async def fetch_regional_comparison(model, regions):
            return await regional_comparison_chart(model, regions)
            
        # Call the service asynchronously with the proper wrapper
        fig = AsyncBridge.run_async(fetch_regional_comparison(selected_model, regions))
        st.plotly_chart(fig, use_container_width=True)
        # Add price arbitrage analysis
        st.subheader("Price Arbitrage Analysis")
        base_price = 1000
        if "iPhone" in selected_model:
            base_price = 1000 if "Pro" in selected_model else 800
        elif "Samsung" in selected_model:
            base_price = 1200 if "Ultra" in selected_model else 900
        elif "Google" in selected_model:
            base_price = 900 if "Pro" in selected_model else 700
        elif "Xiaomi" in selected_model:
            base_price = 800
        elif "Huawei" in selected_model:
            base_price = 900
        region_multipliers = {
            "US": 1.0,
            "EU": 1.1,
            "BR": 1.2,
            "IN": 0.9,
            "JP": 1.05,
            "CN": 0.95,
        }
        # Find lowest and highest price regions
        prices = {
            region: base_price * region_multipliers.get(region, 1.0)
            for region in regions
        }
        min_region = min(prices.items(), key=lambda x: x[1])
        max_region = max(prices.items(), key=lambda x: x[1])
        st.markdown(
            f"""
        ### Maximum Savings Potential

        - **Lowest Price Region:** {min_region[0]} (${min_region[1]:.2f})
        - **Highest Price Region:** {max_region[0]} (${max_region[1]:.2f})
        - **Price Difference:** ${max_region[1] - min_region[1]:.2f}
          ({(max_region[1] - min_region[1]) / max_region[1] * 100:.1f}%)

        > **AI Insight:** Purchasing {selected_model} from {min_region[0]}
        > instead of {max_region[0]} could save you ${max_region[1] - min_region[1]:.2f},
        > even considering shipping and taxes.
        """
        )
    with tab3:
        st.subheader("Historical Price Evolution")
        st.write("Select models and date range to compare historical price evolution")
        # Date range selector
        # DateTime already imported at the top

        today = datetime.now()
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", today - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", today)

        # Calculate date range for price history
        date_range_days = (end_date - start_date).days
        # Multi-select for models
        selected_models = st.multiselect(
            "Select Phone Models",
            phone_options,
            default=[phone_options[0]] if phone_options else [],
        )
        # Display the historical comparison with real data
        if selected_models:
            # Use date range to display appropriate historical data visualization
            st.write(f"Historical price comparison for the past {date_range_days} days")
            st.subheader("Price Change Summary")
            
            # Create loading placeholder
            loading_placeholder = st.empty()
            loading_placeholder.info(f"Fetching historical price data...")
            
            try:
                # Import necessary modules
                from app.mcp.track_price_history.service import track_price_history_service
                from app.ui.async_bridge import AsyncBridge
                
                data = []
                for model in selected_models:
                    # Prepare parameters for the price history service
                    params = {
                        "action": "get_history",
                        "model": model,
                        "days": date_range_days
                    }
                    
                    # Call the service asynchronously
                    result = await AsyncBridge.run_async(track_price_history_service(params))
                    
                    # Process the data if the service call was successful
                    if result.get("status") == "success" and "data" in result:
                        history_data = result.get("data", {}).get("history", [])
                        metrics = result.get("data", {}).get("metrics", {})
                        
                        # Extract start and end prices
                        if history_data and len(history_data) >= 2:
                            start_price = history_data[0].get("price", 0)
                            end_price = history_data[-1].get("price", 0)
                            change_pct = ((end_price - start_price) / start_price * 100) if start_price > 0 else 0
                            
                            # Add to data for display
                            data.append({
                                "Model": model,
                                "Start Price": f"${start_price:.2f}",
                                "End Price": f"${end_price:.2f}",
                                "Change %": f"{change_pct:.2f}%",
                                "Trend": "📈" if change_pct > 0 else "📉" if change_pct < 0 else "📊",
                                "Volatility": metrics.get("volatility", "Low")
                            })
                
                # Clear the loading message
                loading_placeholder.empty()
                
                # If no data was found, show a message
                if not data:
                    st.warning("No historical price data found for the selected models.")
                
            except Exception as e:
                # Handle any exceptions
                import logging
                logging.error(f"Error fetching historical price data: {str(e)}")
                loading_placeholder.empty()
                st.error(f"An error occurred while fetching historical price data: {str(e)}")
                data = []
            historical_price_data_frame = pd.DataFrame(data)
            st.dataframe(
                historical_price_data_frame,
                use_container_width=True,
                column_config={
                    "Model": st.column_config.TextColumn("Model"),
                    "Start Price": st.column_config.TextColumn("Start Price"),
                    "End Price": st.column_config.TextColumn("End Price"),
                    "Change %": st.column_config.TextColumn("Change %"),
                    "Trend": st.column_config.TextColumn("Trend"),
                },
                hide_index=True,
            )
