"""
UI components for displaying agent reasoning and confidence.

This module provides UI components to expose the internal decision-making process
and confidence levels of the SmartNinja AI agents, improving explainability
and user trust in the AI recommendations.
"""
from typing import Any, Dict

import streamlit as st


def display_agent_reasoning(agent_type: str, reasoning: str) -> None:
    """
    Display detailed reasoning from an agent in an expandable section.

    Args:
        agent_type: The type of agent (e.g., "Analysis" or "Recommendation")
        reasoning: The reasoning text to display
    """
    if not reasoning:
        return

    with st.container():
        # Create expander and access its content area
        with st.expander(f"📝 {agent_type} Reasoning") as expander:
            # Display the reasoning in the content area
            expander.markdown(
                f"<div style='background-color:#2E2E2E; padding:1em; "
                f"border-radius:8px; font-size:0.9em;'>{reasoning}</div>",
                unsafe_allow_html=True
            )


def display_confidence_metric(confidence: float) -> None:
    """
    Display the agent's confidence as a styled metric.

    Args:
        confidence: Confidence value between 0 and 1
    """
    if not isinstance(confidence, (int, float)) or confidence < 0 or confidence > 1:
        return

    # Format confidence as percentage
    confidence_pct = f"{int(confidence * 100)}%"

    # Determine confidence level for display purposes
    if confidence >= 0.8:
        confidence_level = "High"
        delta_color = "normal"  # Green for high confidence
    elif confidence >= 0.5:
        confidence_level = "Medium"
        delta_color = "normal"  # Green for medium confidence
    else:
        confidence_level = "Low"
        delta_color = "inverse"  # Red for low confidence

    # Display as metric with delta indicator
    st.metric(
        "Confidence",
        confidence_pct,
        delta=confidence_level,
        delta_color=delta_color
    )


def display_explanation_markdown(explanation: str) -> None:
    """
    Display a concise explanation in highlighted markdown format.

    Args:
        explanation: Short explanation text (e.g., "Price dropped 15% in 7 days")
    """
    if not explanation:
        return

    st.markdown(
        f"<div style='background-color:#1E3A5F; padding:0.7em; margin:0.5em 0; "
        f"border-left:4px solid #50FA7B; border-radius:4px; font-size:0.95em;'>"
        f"<b>Why?</b> {explanation}</div>",
        unsafe_allow_html=True
    )


def display_expanded_insight(insight_data: Dict[str, Any]) -> None:
    """
    Display expanded detailed data in a JSON viewer.

    Args:
        insight_data: Dictionary containing detailed insight data
    """
    if not insight_data:
        return

    # Create expander and display JSON data in its content area
    with st.expander("🔍 Detailed Insights") as expander:
        expander.json(insight_data)


def display_agent_insights(agent_type: str, agent_data: Dict[str, Any]) -> None:
    """
    Display all insight components for an agent.

    Args:
        agent_type: The type of agent (e.g., "Analysis" or "Recommendation")
        agent_data: Dictionary with agent output data including reasoning and confidence
    """
    if not agent_data:
        st.error(f"No {agent_type.lower()} data available")
        return

    # Main content is either analysis or recommendation
    main_content = agent_data.get("analysis") or agent_data.get("recommendation")
    if main_content:
        style = (
            "background-color:#2E2E2E; padding:1em; border-radius:8px; "
            "color:#50FA7B; font-size:1.1em;"
        )
        st.markdown(
            f"<div style='{style}'>🧠 <b>{agent_type}:</b> {main_content}</div>",
            unsafe_allow_html=True,
        )

    # Show confidence if available
    if "confidence" in agent_data:
        display_confidence_metric(agent_data["confidence"])

    # Show explanation if available
    if "explanation" in agent_data:
        display_explanation_markdown(agent_data["explanation"])

    # Show detailed reasoning if available
    if "reasoning" in agent_data:
        display_agent_reasoning(agent_type, agent_data["reasoning"])

    # Show expanded insights if available
    detailed_data = agent_data.get("detailed_data")
    if detailed_data:
        display_expanded_insight(detailed_data)
