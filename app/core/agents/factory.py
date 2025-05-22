"""
Factory for creating agent instances.

This module provides factory functions for creating properly configured
agents with dependencies properly injected.
"""
from app.core.agents.analysis_agent import AnalysisAgent
from app.core.agents.notification_agent import NotificationAgent
from app.core.agents.planning_agent import PlanningAgent
from app.core.agents.recommendation_agent import RecommendationAgent
from app.core.agents.scraping_agent import ScrapingAgent
from app.core.agents.sequential_agent import SequentialAgent
from app.core.interfaces.tool_factory import create_tool_set
from app.core.notification.factory import (
    create_alert_history_repository,
    create_email_service,
    create_telegram_service,
    create_webhook_service,
)


def create_planning_agent():
    """
    Create a properly configured planning agent.

    Returns:
        Configured PlanningAgent instance
    """
    tool_set = create_tool_set()
    return PlanningAgent(tool_set=tool_set)


def create_scraping_agent():
    """
    Create a properly configured scraping agent.

    Returns:
        Configured ScrapingAgent instance
    """
    tool_set = create_tool_set()
    return ScrapingAgent(tool_set=tool_set)


def create_analysis_agent():
    """
    Create a properly configured analysis agent.

    Returns:
        Configured AnalysisAgent instance
    """
    tool_set = create_tool_set()
    return AnalysisAgent(tool_set=tool_set)


def create_recommendation_agent():
    """
    Create a properly configured recommendation agent.

    Returns:
        Configured RecommendationAgent instance
    """
    tool_set = create_tool_set()
    return RecommendationAgent(tool_set=tool_set)


def create_notification_agent(enable_notifications=True):
    """
    Create a properly configured notification agent.

    Args:
        enable_notifications: Whether to enable notifications
                             If False, returns None

    Returns:
        Configured NotificationAgent instance or None
    """
    if not enable_notifications:
        return None

    # Create notification services
    email_service = create_email_service()
    webhook_service = create_webhook_service()
    telegram_service = create_telegram_service()

    # Create alert history repository
    alert_history_repository = create_alert_history_repository()

    # Create and return the notification agent
    return NotificationAgent(
        email_service=email_service,
        webhook_service=webhook_service,
        telegram_service=telegram_service,
        alert_history_repository=alert_history_repository,
    )


def create_sequential_agent(enable_notifications=True):
    """
    Create a properly configured sequential agent with all child agents.

    Args:
        enable_notifications: Whether to enable notifications in the pipeline

    Returns:
        Configured SequentialAgent instance
    """
    # Create child agents
    planning_agent = create_planning_agent()
    scraping_agent = create_scraping_agent()
    analysis_agent = create_analysis_agent()
    recommendation_agent = create_recommendation_agent()
    notification_agent = create_notification_agent(enable_notifications)

    # Create sequential agent with all child agents
    return SequentialAgent(
        planning_agent=planning_agent,
        scraping_agent=scraping_agent,
        analysis_agent=analysis_agent,
        recommendation_agent=recommendation_agent,
        notification_agent=notification_agent,
    )
