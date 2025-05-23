import logging
import os
import time
from typing import List, Optional, Dict, Any

import pandas as pd
import requests
import streamlit as st

from ..async_adapter import ScrapingAgentAdapter, AnalysisAgentAdapter, RecommendationAgentAdapter

from ..components import create_logo, display_ai_insights, price_history_chart
from ..timeline_components import display_agent_timeline, mark_agent_step_failed
from ..agent_visual_feedback import display_agent_pipeline_visualization
from ..sequential_pipeline import render_agent_pipeline


def display_logo():
    """
    Display the SmartNinja logo at the top of the page
    """
    logo_path = create_logo()
    _, col2, _ = st.columns([1, 2, 1])
    with col2:
        st.image(logo_path, width=200)


def mobile_input() -> str:
    """
    Create an input field for mobile device models
    Returns:
        str: The entered mobile device model
    """
    return st.text_input(
        "Mobile Device Model",
        placeholder="e.g., iPhone 15 Pro, Samsung Galaxy S24",
        help="Enter the exact model name for best results",
    )


def country_selector(default_countries: Optional[List[str]] = None) -> List[str]:
    """
    Create a multi-select dropdown for countries
    Args:
        default_countries: List of countries to select by default
    Returns:
        List[str]: List of selected countries
    """
    countries = [
        "US",
        "UK",
        "EU",
        "CA",
        "AU",
        "JP",
        "KR",
        "SG",
        "BR",
        "MX",
        "IN",
        "CN",
    ]
    default = default_countries or ["US", "UK", "EU", "BR"]
    return st.multiselect(
        "Select Countries",
        options=countries,
        default=default,
        help="Select countries to compare prices across",
    )


async def fetch_prices(model: str, countries: list) -> List[dict]:
    """
    Fetch prices for the given model in the selected countries using the ScrapingAgentAdapter.
    Uses the AsyncBridge to properly convert between synchronous UI and asynchronous backend.

    Args:
        model: The model name to search for
        countries: List of country codes to search in
    Returns:
        List[dict]: List of price data dictionaries
    """
    from app.core.scraping.bright_data_service import BrightDataScraperService
    from app.ui.async_bridge import AsyncBridge
    
    results = []
    all_successful = True

    # Create status placeholder for feedback during scraping
    status_placeholder = st.empty()
    status_placeholder.info(f"Fetching prices for {model} across {len(countries)} countries...")

    try:
        # Initialize the scraper service
        scraper = BrightDataScraperService(num_results=5)

        # Process each country
        for i, country in enumerate(countries):
            # Update status for this specific country
            status_placeholder.info(f"Searching prices in {country} ({i+1}/{len(countries)})...")
            start_time = time.time()

            try:
                # Call the scraper service directly since we're already in an async function
                country_results = await scraper.get_prices(model, country)
                
                # Log performance
                elapsed = time.time() - start_time
                logging.info(f"Fetched {len(country_results)} results for {country} in {elapsed:.2f}s")

                # Add results to the combined list
                if country_results and len(country_results) > 0:
                    results.extend(country_results)
                else:
                    all_successful = False
                    logging.warning(f"No results found for {model} in {country}")
                    
            except Exception as e:
                all_successful = False
                logging.error(f"Error fetching prices for {country}: {str(e)}")
                continue

        # Clear the status message
        status_placeholder.empty()

        # If we got no results at all, inform the user
        if not results:
            logging.warning(f"No results found for {model} in any country")
            st.warning("No price data found. Please try a different model or countries.")
            return []

        # If successful, show a success message
        if all_successful:
            st.success(f"Found {len(results)} price entries across {len(countries)} countries")

        return results

    except Exception as error:
        # Log the error and display to user
        logging.error(f"Scraping error: {str(error)}")
        status_placeholder.empty()
        st.error(f"An error occurred while fetching prices: {str(error)}")
        return []


def display_price_results(results: List[dict]):
    """
    Display the price results in a table
    Args:
        results: List of price data dictionaries
    """
    if not results:
        st.info("No price data available. Try a different model or country.")
        return

    # Create a dataframe from the results
    results_dataframe = pd.DataFrame(results)

    # Add formatting
    st.dataframe(
        results_dataframe,
        use_container_width=True,
        column_config={
            "store": st.column_config.TextColumn("Store"),
            "price": st.column_config.TextColumn("Price"),
            "region": st.column_config.TextColumn("Region"),
            "currency": st.column_config.TextColumn("Currency"),
            "last_updated": st.column_config.DateColumn("Last Updated"),
            "url": st.column_config.LinkColumn("Link"),
        },
        hide_index=True,
    )


def insights_section(model: str, results: List[dict]):
    """
    Display the AI insights section using the async adapters to analyze
    price data and generate recommendations.

    Args:
        model: The mobile device model
        results: List of price data dictionaries
    """
    if not results:
        st.warning("No price data available for analysis")
        return

    # Create a status container for feedback during analysis
    status = st.empty()
    status.info("Analyzing price data...")

    try:
        # Initialize the analysis adapter
        analysis_adapter = AnalysisAgentAdapter()

        # Perform analysis using the adapter (handles async to sync conversion)
        analysis_result = analysis_adapter.analyze_prices(results)

        # Initialize the recommendation adapter
        recommendation_adapter = RecommendationAgentAdapter()

        # Prepare input for recommendation
        # Handle case where analysis_result is a string instead of a dictionary
        if isinstance(analysis_result, dict):
            average_price = analysis_result.get("average_price", 0)
            price_trend = analysis_result.get("price_trend", "stable")
        else:
            # If analysis_result is not a dictionary (e.g., it's a string), use default values
            logging.info(f"Analysis result is not a dictionary: {type(analysis_result)}, using defaults")
            average_price = 0
            price_trend = "stable"
            
        recommendation_input = {
            "price_data": results,
            "model": model,
            "analysis": analysis_result,
            "average_price": average_price,
            "price_trend": price_trend,
            "store_count": len(set(item.get("store", "") for item in results))
        }

        # Get recommendation using the adapter
        status.info("Generating recommendations...")
        recommendation_result = recommendation_adapter.execute(recommendation_input)

        # Clear status now that processing is complete
        status.empty()

        # Create results dictionary for UI display
        # Handle the case where analysis_result is a string instead of a dictionary
        if isinstance(analysis_result, str):
            # If analysis_result is a string, we need to pass just the results to display_ai_insights
            # as it will handle string analysis results appropriately
            display_ai_insights(results)
        else:
            # For dictionary results, ensure we're passing properly formatted data
            analysis_data = {
                "recommendation": recommendation_result
            }
            
            # Display the insights with the correctly formatted data
            display_ai_insights(results, analysis_data)

        # Show the full agent pipeline visualization if we have all the data
        if analysis_result and recommendation_result:
            if st.checkbox("Show Agent Pipeline Visualization", value=False):
                render_agent_pipeline(
                    {"model": model, "country": "All"},
                    {
                        "planning_result": {"model": model, "country": "All"},
                        "scraping_result": results,
                        "analysis_result": analysis_result,
                        "recommendation_result": recommendation_result,
                        "notification_result": {}
                    }
                )

    except Exception as e:
        st.error(f"Error analyzing price data: {str(e)}")
        logging.error(f"Error in insights_section: {str(e)}")
        # Fallback to the simple display method
        display_ai_insights(results)


# pylint: disable=unused-argument
def render_home(regions, brands):
    """
    Render the home page with dashboard overview
    Args:
        regions: List of selected regions
        brands: List of selected brands
    """
    # Display the logo at the top
    display_logo()

    # Main page title
    st.title("📱 Smartphone Price Tracker Agent")

    # Create a container for the welcome message
    with st.container():
        st.markdown(
            """
            ### Welcome to SmartNinja!

            Your AI-powered platform for smartphone price tracker agent.
            Compare prices across markets and get AI insights to make better purchasing decisions.
            """
        )

    # Create the search form
    with st.form("search_form"):
        st.subheader("🔍 Search for Smartphone Prices")
        model = mobile_input()
        countries = country_selector()
        submitted = st.form_submit_button("Search", type="primary")

        if submitted and model:
            st.session_state["last_search"] = {"model": model, "countries": countries}

        # Display results if a search has been submitted
    if "last_search" in st.session_state:
        search_data = st.session_state["last_search"]
        st.subheader(f"📊 Price Results for {search_data['model']}")

        # Initialize or reset the agent timeline
        if "agent_timeline" not in st.session_state or submitted:
            st.session_state["agent_timeline"] = display_agent_timeline(reset=True)

        # Update timeline for planning stage
        st.session_state["agent_timeline"] = display_agent_timeline(
            active_step="planning",
            existing_timeline=st.session_state["agent_timeline"]
        )
        time.sleep(0.5)  # Simulate planning delay

        # Update timeline for scraping stage
        st.session_state["agent_timeline"] = display_agent_timeline(
            active_step="scraping",
            existing_timeline=st.session_state["agent_timeline"]
        )

        # Fetch prices with timeline visualization and error handling
        try:
            # Use AsyncBridge to call the async fetch_prices function
            from app.ui.async_bridge import AsyncBridge
            
            # Define a wrapper function that properly awaits the coroutine
            async def execute_fetch_prices(model, countries):
                return await fetch_prices(model, countries)
                
            # Call the service asynchronously with the proper wrapper
            results = AsyncBridge.run_async(
                execute_fetch_prices(search_data["model"], search_data["countries"])
            )
        except Exception as e:
            # Mark scraping step as failed and display error message
            st.session_state["agent_timeline"] = mark_agent_step_failed(
                st.session_state["agent_timeline"],
                "scraping",
                f"Error fetching prices: {str(e)}"
            )
            st.error(f"An error occurred while fetching prices: {str(e)}")
            # Return early to prevent further processing
            return

        # Update timeline for analysis stage
        st.session_state["agent_timeline"] = display_agent_timeline(
            active_step="analysis",
            existing_timeline=st.session_state["agent_timeline"]
        )
        time.sleep(0.5)  # Simulate analysis delay

        # Update timeline for recommendation stage
        st.session_state["agent_timeline"] = display_agent_timeline(
            active_step="recommendation",
            existing_timeline=st.session_state["agent_timeline"]
        )

        display_price_results(results)

        # Display AI insights
        insights_section(search_data["model"], results)

        # Update timeline for notification stage if enabled
        if "trigger_notification" in st.session_state and st.session_state["trigger_notification"]:
            st.session_state["agent_timeline"] = display_agent_timeline(
                active_step="notification",
                existing_timeline=st.session_state["agent_timeline"]
            )

        # Display agent pipeline visualization
        st.markdown("---")

        # Prepare sample pipeline results to visualize the agent flow
        # In a real implementation, these would come from the SequentialAgent
        pipeline_input = {
            "model": search_data["model"],
            "country": ", ".join(search_data["countries"]),
        }

        # Simulate pipeline results based on the fetched data
        pipeline_results = {
            "planning_result": {
                "model": search_data["model"],
                "country": ", ".join(search_data["countries"]),
                "websites": [
                    "store1.example.com",
                    "store2.example.com",
                    "store3.example.com",
                ],
            },
            "scraping_result": results,
            "analysis_result": {
                "average_price": (
                    sum(
                        float(result_item.get("price", "$0").replace("$", ""))
                        for result_item in results
                    ) / max(len(results), 1)
                ),
                "price_range": (
                    "N/A" if not results else
                    # Calcula preço mínimo e máximo separadamente para evitar linhas longas
                    f"${min([float(item.get('price', '$0').replace('$', '')) for item in results])}"
                    f"-${max([float(item.get('price', '$0').replace('$', '')) for item in results])}"
                ),
                "price_trend": "Stable ↔️",
                "insights": (
                    "Prices are currently stable across all monitored stores. "
                    "No significant changes detected in the last 30 days."
                ),
            },
            "recommendation_result": {
                "best_offer": results[0] if results else {},
                "recommendation_reason": (
                    "This is the lowest price available from a trusted retailer"
                ),
                "alternative_offers": results[1:3] if len(results) > 1 else [],
            },
        }

        # Check if we should simulate a notification
        if (
            "trigger_notification" in st.session_state
            and st.session_state["trigger_notification"]
        ):
            pipeline_results["notification_result"] = {
                "alerts_triggered": [
                    {
                        "type": "price_drop",
                        "device": search_data["model"],
                        "message": "Price dropped below your target of $1000",
                    }
                ]
            }

        # Render the agent pipeline visualization with visual feedback
        display_agent_pipeline_visualization(pipeline_input, pipeline_results)

        # Render the sequential agent pipeline for deeper analysis
        render_agent_pipeline(pipeline_input, pipeline_results)

    # Display price trends if available
    if "last_search" in st.session_state:
        st.markdown("---")
        st.subheader("📈 Price Trends")
        # Use AsyncBridge to call the async price_history_chart function
        from app.ui.async_bridge import AsyncBridge
        
        # Define a wrapper function that properly awaits the coroutine
        async def fetch_price_history_chart(model, countries):
            return await price_history_chart(model, countries)
            
        # Call the service asynchronously with the proper wrapper
        fig = AsyncBridge.run_async(
            fetch_price_history_chart(
                st.session_state["last_search"]["model"],
                st.session_state["last_search"]["countries"],
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        # Add a way to simulate notification triggers for demo purposes
        st.sidebar.markdown("---")
        st.sidebar.subheader("Demo Controls")
        notification_toggle = st.sidebar.checkbox(
            "Simulate Price Alert",
            value=st.session_state.get("trigger_notification", False),
            key="demo_notification_toggle",
            help="Toggle this to simulate a price alert notification in the pipeline visualization",
        )
        st.session_state["trigger_notification"] = notification_toggle

        # Add a button to reset the timeline for testing
        if st.sidebar.button("Reset Pipeline", key="reset_pipeline_btn"):
            st.session_state["agent_timeline"] = display_agent_timeline(reset=True)

        # Display pipeline analytics if all steps are completed
        timeline = st.session_state.get("agent_timeline", {})
        all_completed = all(
            data.get("status") == "completed"
            for step, data in timeline.items()
            if step != "notification" # Notification step is optional
        )

        if all_completed and timeline:
            st.sidebar.markdown("---")
            st.sidebar.subheader("Pipeline Analytics")

            # Calculate total duration
            total_duration = sum(
                data.get("duration", 0)
                for data in timeline.values()
                if data.get("duration") is not None
            )

            # Display analytics
            st.sidebar.markdown(f"**Total time:** {total_duration:.2f}s")

            # Display individual step durations as percentage
            for step, data in timeline.items():
                if data.get("duration") is not None:
                    percentage = (data["duration"] / total_duration) * 100 if total_duration > 0 else 0
                    st.sidebar.markdown(
                        f"{step.capitalize()}: {data['duration']:.2f}s ({percentage:.1f}%)"
                    )
