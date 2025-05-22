"""
UI components for displaying the Sequential Agent Pipeline.

This module provides functions to render the agent pipeline flow
(Planning → Scraping → Analysis → Recommendation → Notification)
with expandable sections and visual indicators for each step.
"""
import time
from typing import Any, Dict, List, Optional, Callable

import pandas as pd
import streamlit as st

from .components import add_section_header, create_tooltip, generate_summary_insight, display_price_source


def render_agent_pipeline(
    input_data: Dict[str, Any], results: Optional[Dict[str, Any]] = None
):
    """
    Render the complete agent pipeline visualization.

    Args:
        input_data: The original search input data (model, country)
        results: The results from each agent in the pipeline
    """
    if not results:
        results = {}

    # Display a title for the pipeline visualization with enhanced styling
    add_section_header(
        "SmartNinja Agent Pipeline",
        "🤖",
        "This pipeline shows how our AI agents work together to provide product price insights and recommendations."
    )

    # Add help tooltip for the pipeline
    pipeline_description = (
        "The SmartNinja agent pipeline breaks down complex tasks into specialized steps. "
        "Each agent handles one part of the process, from planning what to search for "
        "to making final recommendations."
    )
    create_tooltip(pipeline_description)

    # Create a progress bar to visualize the sequential flow
    progress_bar = st.progress(0)

    # Render each agent in sequence with animated progress
    with st.spinner("Processing through agent pipeline..."):
        # Step 1: Planning Agent
        planning_data = results.get("planning_result", input_data)
        render_planning_agent(planning_data)
        progress_bar.progress(20)
        time.sleep(0.3)  # Brief pause for visual effect

        # Step 2: Scraping Agent
        scraping_data = results.get("scraping_result", [])
        render_scraping_agent(scraping_data)
        progress_bar.progress(40)
        time.sleep(0.3)  # Brief pause for visual effect

        # Step 3: Analysis Agent
        analysis_data = results.get("analysis_result", {})
        render_analysis_agent(analysis_data)
        progress_bar.progress(60)
        time.sleep(0.3)  # Brief pause for visual effect

        # Step 4: Recommendation Agent
        recommendation_data = results.get("recommendation_result", {})
        render_recommendation_agent(recommendation_data)
        progress_bar.progress(80)
        time.sleep(0.3)  # Brief pause for visual effect

        # Step 5: Notification Agent (if triggered)
        notification_data = results.get("notification_result", {})
        if notification_data and notification_data.get("alerts_triggered"):
            render_notification_agent(notification_data)
        else:
            with st.expander("🔔 Notification Agent (Not Triggered)"):
                st.markdown(
                    """No price alerts were triggered during this search.
                
                    Configure price alerts in the Settings page to receive notifications
                    when prices match your criteria.
                    """
                )
                # Add help tooltip
                create_tooltip(
                    "Price alerts will notify you when the price drops below your target. We'll check prices daily and send you an alert when the condition is met."
                )
        progress_bar.progress(100)
        st.success("Pipeline processing complete!")
    
        # Add final summary insight if results are available
        # The function will handle empty or incomplete results appropriately
        generate_summary_insight(results)


def render_agent_with_header(
    agent_name: str,
    emoji: str,
    description: str,
    data: Dict[str, Any],
    render_function: Callable[[Dict[str, Any]], None]
) -> None:
    """
    Render an agent section with a standardized header and description.

    Creates a consistent agent UI section with a recognizable header that includes
    an emoji, a descriptive title, explanatory text, and a tooltip for additional
    information. Content specific to each agent type is rendered by the provided
    render_function.

    This function follows the Single Responsibility Principle by separating the
    common agent header rendering from the specific agent content rendering.

    Args:
        agent_name: Name of the agent (e.g., "Planning", "Analysis")
        emoji: Emoji to display in the header for visual identification
        description: Description of the agent's function shown as text and tooltip
        data: Data to pass to the render function for agent-specific content
        render_function: Function that renders the agent's specific content
    """
    # Create a container as the tests expect
    container = st.container()
    
    with container:
        # Add enhanced header with emoji - using container.markdown as tests expect
        container.markdown(f"## {emoji} {agent_name}")
        container.markdown(description)
        
        # Add help tooltip - tests specifically check for this
        st.help(description)
        
        # Render agent specific content
        render_function(data)


def render_planning_agent(planning_data: Dict[str, Any]) -> None:
    """
    Render the Planning Agent section.

    Args:
        planning_data: Data from the planning agent
    """
    def render_planning_content(data):
        # Display planning data
        if data.get("model") and data.get("country"):
            st.write(
                f"Searching for **{data['model']}** in **{data['country']}**"
            )

        # Show reasoning if available with improved styling
        if data.get("reasoning"):
            with st.expander("🧠 Planning Logic & Reasoning"):
                st.markdown(
                    f"<div style='background-color:#2E2E2E; padding:1em; border-radius:8px;'>{data['reasoning']}</div>",
                    unsafe_allow_html=True
                )

    # Render the agent with standardized header
    render_agent_with_header(
        "Planning Agent",
        "📋",
        "The Planning Agent determines which smartphone models to search for and in which regions.",
        planning_data,
        render_planning_content
    )


def render_scraping_agent(scraping_data: List[Dict[str, Any]]) -> None:
    """
    Render the Scraping Agent section.

    Args:
        scraping_data: Data from the scraping agent
    """
    def render_scraping_content(response):
        # Check if we have a valid response
        if not response:
            st.info("No scraping data available yet.")
            return
            
        # Check for standardized MCP response format
        if isinstance(response, dict):
            # Handle standard MCP response format
            if response.get("status") == "success":
                data = response.get("data", [])
                processing_time = response.get("processing_time_ms")
                
                try:
                    # Try to create a dataframe from scraped data
                    if data:
                        price_data_frame = pd.DataFrame(data)
                        if not price_data_frame.empty:
                            # Display scraped data in a table with improved styling
                            st.dataframe(
                                price_data_frame.style.background_gradient(
                                    cmap="Blues", subset=["price"], low=0.1, high=0.9
                                ),
                                height=400,
                            )
                            
                            # Display processing time if available
                            if processing_time:
                                st.caption(f"Processing time: {processing_time} ms")
                                
                            # Display price sources with links if available
                            if len(data) > 0 and "source_url" in data[0] and "source" in data[0]:
                                source_data = {
                                    "name": data[0]["source"],
                                    "url": data[0]["source_url"]
                                }
                                display_price_source(source_data)
                        else:
                            st.info("No price data found in the response.")
                    else:
                        st.info("No data available in the response.")
                        
                except Exception as error:
                    st.error(f"Error displaying scraping results: {error}")
                    
            elif response.get("status") == "error":
                # Display error message from the response
                error_message = response.get("message", "An error occurred during price scraping.")
                st.error(error_message)
                
            else:
                # Handle unexpected response format
                st.warning("Unexpected response format from scraping service.")
                
        # Legacy handling for backward compatibility
        elif isinstance(response, list) or (isinstance(response, dict) and response.get("results")):
            # For legacy response format
            results = response if isinstance(response, list) else response.get("results", [])
            
            try:
                if results:
                    price_data_frame = pd.DataFrame(results)
                    if not price_data_frame.empty:
                        st.dataframe(
                            price_data_frame.style.background_gradient(
                                cmap="Blues", subset=["price"], low=0.1, high=0.9
                            ),
                            height=400,
                        )
                    st.warning("Using legacy data format. Please update the response format.")
                else:
                    st.info("No scraping data available in legacy format.")
            except Exception as error:
                st.error(f"Error displaying legacy scraping results: {error}")
        else:
            st.info("No scraping data available yet.")

    # Render the agent with standardized header
    render_agent_with_header(
        "Scraping",
        "🔍",
        "The Scraping Agent collects price information from various online retailers and aggregates data from multiple sources.",
        scraping_data,
        render_scraping_content
    )


def render_analysis_agent(analysis_data: Dict[str, Any]) -> None:
    """
    Render the Analysis Agent section.

    Args:
        analysis_data: Analysis results from the analysis agent
    """
    def render_analysis_content(response):
        # Check if we have a valid response
        if not response:
            st.info("No analysis data available yet.")
            return
        
        # Check for standardized MCP response format
        if isinstance(response, dict):
            # Handle success response with standard format
            if response.get("status") == "success":
                data = response.get("data", {})
                processing_time = response.get("processing_time_ms")
                
                # Check if data is available
                if data:
                    # Display analysis metrics
                    col1, col2 = st.columns(2)
                    # Left column: Price statistics
                    with col1:
                        # Display price statistics
                        if "price_data" in data:
                            price_data = data["price_data"]
                            st.metric("Minimum Price", f"${price_data.get('min_price', 0):.2f}")
                            st.metric(
                                "Average Price", 
                                f"${price_data.get('avg_price', 0):.2f}",
                                delta=f"{price_data.get('price_difference_percent', 0):.1f}%"
                            )
                
                    # Right column: Confidence and summary
                    with col2:
                        # Display confidence if available
                        if "confidence" in data:
                            confidence = data["confidence"]
                            confidence_color = "normal" if confidence > 0.7 else "off" if confidence > 0.4 else "inverse"
                            st.metric(
                                "Analysis Confidence", 
                                f"{confidence * 100:.1f}%",
                                delta_color=confidence_color
                            )
                    
                    # Display processing time if available
                    if processing_time:
                        st.caption(f"Analysis completed in {processing_time} ms")
                else:
                    st.info("No analysis data found in the response.")
            
            # Handle error response
            elif response.get("status") == "error":
                error_message = response.get("message", "An error occurred during price analysis.")
                st.error(error_message)
            
            # Handle unexpected response format
            else:
                st.warning("Unexpected response format from analysis service.")
        
        # Legacy format support for backward compatibility
        elif isinstance(response, dict) and ("price_data" in response or "confidence" in response):
            # Handle legacy format directly
            data = response
            
            # Display analysis metrics
            col1, col2 = st.columns(2)
            # Left column: Price statistics
            with col1:
                # Display price statistics
                if "price_data" in data:
                    price_data = data["price_data"]
                    st.metric("Minimum Price", f"${price_data.get('min_price', 0):.2f}")
                    st.metric(
                        "Average Price", 
                        f"${price_data.get('avg_price', 0):.2f}",
                        delta=f"{price_data.get('price_difference_percent', 0):.1f}%"
                    )
                    st.warning("Using legacy data format. Please update the response format.")
        
            # Right column: Confidence and summary
            with col2:
                # Display confidence if available
                if "confidence" in data:
                    confidence = data["confidence"]
                    confidence_color = "normal" if confidence > 0.7 else "off" if confidence > 0.4 else "inverse"
                    st.metric(
                        "Analysis Confidence", 
                        f"{confidence * 100:.1f}%",
                        delta_color=confidence_color
                    )
            
            # Display market opinion if available
            if "market_opinion" in data:
                st.info(f"Market assessment: {data['market_opinion']}")

            # Show reasoning if available with improved styling
            if "reasoning" in data:
                with st.expander("🧠 Analysis Logic & Reasoning"):
                    st.markdown(
                        f"<div style='background-color:#2E2E2E; padding:1em; border-radius:8px;'>{data['reasoning']}</div>",
                        unsafe_allow_html=True
                    )

            # Show explanation if available with better styling
            if "explanation" in data:
                st.markdown(
                    f"<div style='background-color:#1B2A41; border-left:4px solid #50FA7B; padding:1em; border-radius:8px;'>{data['explanation']}</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No analysis data available yet.")

    # Render the agent with standardized header
    render_agent_with_header(
        "Analysis",
        "🧮",
        "The Analysis Agent evaluates price data to identify patterns and trends using statistical methods.",
        analysis_data,
        render_analysis_content
    )


def render_recommendation_agent(recommendation_data: Dict[str, Any]) -> None:
    """
    Render the Recommendation Agent section.

    Args:
        recommendation_data: Recommendation results
    """
    def render_recommendation_content(response):
        # Check if we have a valid response
        if not response:
            st.info("No recommendation data available yet.")
            return
            
        # Check for standardized MCP response format
        if isinstance(response, dict):
            # Handle standard MCP response format
            if response.get("status") == "success":
                data = response.get("data", {})
                processing_time = response.get("processing_time_ms")
                
                # Extract recommendations from data
                recommendations = data.get("recommendations", [])
                explanation = data.get("explanation")
                reasoning = data.get("reasoning")
                
                if recommendations:
                    # Create columns for each recommendation
                    num_recommends = min(3, len(recommendations))
                    cols = st.columns(num_recommends)
                
                    # Display each recommendation in its own column
                    for i, (col, rec) in enumerate(zip(cols, recommendations[:num_recommends])):
                        with col:
                            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "✨"
                            st.markdown(f"### {medal} **{rec.get('model', 'Unknown')}**")
                            st.metric(
                                "Price", 
                                f"${rec.get('price', 0):.2f}", 
                                delta=rec.get('price_difference', '0') if 'price_difference' in rec else None
                            )
                            if "attributes" in rec:
                                for attribute, value in rec["attributes"].items():
                                    st.write(f"**{attribute}:** {value}")
                        
                            # Add a purchase button (for demonstration) with a better call-to-action
                            st.button("🛒 View Deal", key=f"deal_{i}")
                    
                            # Show source website if available
                            if "source" in rec and "source_url" in rec:
                                st.markdown(
                                    f"<small>Source: <a href='{rec['source_url']}' target='_blank'>{rec['source']}</a></small>", 
                                    unsafe_allow_html=True
                                )
                    
                    # Display processing time if available
                    if processing_time:
                        st.caption(f"Recommendations generated in {processing_time} ms")
                        
                    # Show explanation if available with better styling
                    if explanation:
                        st.markdown(
                            f"<div style='background-color:#1B2A41; border-left:4px solid #50FA7B; padding:1em; border-radius:8px;'>{explanation}</div>",
                            unsafe_allow_html=True
                        )
                    
                    # Show reasoning if available with improved styling
                    if reasoning:
                        with st.expander("🧠 Recommendation Logic & Reasoning"):
                            st.markdown(
                                f"<div style='background-color:#2E2E2E; padding:1em; border-radius:8px;'>{reasoning}</div>",
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No recommendation data found in the response.")
                    
            elif response.get("status") == "error":
                # Display error message from the response
                error_message = response.get("message", "An error occurred during recommendation generation.")
                st.error(error_message)
                
            else:
                # Handle unexpected response format
                st.warning("Unexpected response format from recommendation service.")
                
        # Legacy handling for backward compatibility
        elif isinstance(response, dict) and "recommendations" in response:
            # Show recommendations from legacy format
            recommendations = response.get("recommendations", [])
            
            if recommendations:
                # Create columns for each recommendation
                num_recommends = min(3, len(recommendations))
                cols = st.columns(num_recommends)
            
                # Display each recommendation in its own column
                for i, (col, rec) in enumerate(zip(cols, recommendations[:num_recommends])):
                    with col:
                        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "✨"
                        st.markdown(f"### {medal} **{rec.get('model', 'Unknown')}**")
                        st.metric(
                            "Price", 
                            f"${rec.get('price', 0):.2f}", 
                            delta=rec.get('price_difference', '0') if 'price_difference' in rec else None
                        )
                        if "attributes" in rec:
                            for attribute, value in rec["attributes"].items():
                                st.write(f"**{attribute}:** {value}")
                    
                        # Add a purchase button (for demonstration) with a better call-to-action
                        st.button("🛒 View Deal", key=f"legacy_deal_{i}")
                
                        # Show source website if available
                        if "source" in rec and "source_url" in rec:
                            st.markdown(
                                f"<small>Source: <a href='{rec['source_url']}' target='_blank'>{rec['source']}</a></small>", 
                                unsafe_allow_html=True
                            )
                
                # Display warning about legacy format
                st.warning("Using legacy data format. Please update the response format.")
            else:
                st.info("No recommendation data available in legacy format.")
        else:
            st.info("No recommendation data available yet.")

    # Render the agent with standardized header
    render_agent_with_header(
        "Recommendation",
        "📊",
        "The Recommendation Agent uses analysis to suggest the best buying options based on price, features, and value.",
        recommendation_data,
        render_recommendation_content
    )


def render_notification_agent(notification_data: Dict[str, Any]) -> None:
    """
    Render the Notification Agent section.

    Args:
        notification_data: Notification results
    """
    def render_notification_content(data):
        # Display notification settings
        if data.get("alert"):
            alert_data = data.get("alert", {})
            # Extract relevant alert data for display
            alert_active = alert_data.get("active", False)
            if alert_active:
                st.write(f"**{len(alert_data.get('alerts', []))} active price alerts:**")
                for alert in alert_data.get('alerts', []):
                    status = alert.get("status", "pending")
                    price = alert.get("price", 0)
                    target = alert.get("target_price", 0)
                    model = alert.get("model", "")
                
                    # Display each alert with colored status and improved styling
                    alert_color = "#50FA7B" if status == "triggered" else "#6272A4"
                    # Break long lines for better readability
                    alert_style = (
                        f"<div style='display:flex; justify-content:space-between; "
                        f"padding:0.7em; background-color:#2E2E2E; border-radius:7px; "
                        f"margin-bottom:0.5em; border-left:4px solid {alert_color};'>"
                        f"<div><b>{model}</b> - current: ${price:.2f}</div>"
                        f"<div>target: <b>${target:.2f}</b></div>"
                        f"<div style='color:{alert_color};'>{status}</div>"
                        f"</div>"
                    )
                    st.markdown(alert_style, unsafe_allow_html=True)

            # Show creation form with better layout
            st.markdown("### 🔔 Create Price Alert")
        
            # Create form columns
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                # Using descriptive variable names
                phone_model = st.text_input("Model", key="alert_model")
            with col2:
                price_threshold = st.number_input("Target Price ($)", 
                                               min_value=0.0, 
                                               step=10.0, 
                                               key="alert_price")
            with col3:
                st.write("\n")
                # Create button with icon
                st.button("➕ Create", key="create_alert_btn")
            
            # Add help tooltip
            help_text = (
                "Price alerts will notify you when the price drops below your target. "
                "We'll check prices daily and send you an alert when the condition is met."
            )
            create_tooltip(help_text)
        else:
            st.info("Notification system ready. Set up alerts to track prices over time.")

    # Render the agent with standardized header
    render_agent_with_header(
        "Notification",
        "🔔",
        "The Notification Agent sets up alerts for price changes and helps you track prices over time.",
        notification_data,
        render_notification_content
    )
