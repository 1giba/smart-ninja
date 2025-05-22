"""
Factory for notification services and repositories.

This module provides factory functions for creating properly configured
notification components with dependencies properly injected.
"""
from typing import Optional

from app.core.constants import (
    FROM_EMAIL,
    MCP_SERVER_URL,
    NOTIFICATION_CHANNELS,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USERNAME,
    TELEGRAM_BOT_TOKEN,
    USE_MCP_FOR_ALERTS,
)
from app.core.notification.repositories import (
    AlertHistoryRepository,
    AlertRuleRepository,
)
from app.core.notification.services import EmailService, TelegramService, WebhookService


def create_email_service() -> EmailService:
    """
    Create a properly configured email notification service.

    Returns:
        Configured EmailService instance
    """
    return EmailService(
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        from_email=FROM_EMAIL,
    )


def create_webhook_service() -> WebhookService:
    """
    Create a properly configured webhook notification service.

    Returns:
        Configured WebhookService instance
    """
    return WebhookService()


def create_telegram_service() -> TelegramService:
    """
    Create a properly configured Telegram notification service.

    Returns:
        Configured TelegramService instance
    """
    return TelegramService(bot_token=TELEGRAM_BOT_TOKEN)


def create_alert_rule_repository() -> AlertRuleRepository:
    """
    Create a properly configured alert rule repository.

    Returns:
        Configured AlertRuleRepository instance
    """
    return AlertRuleRepository()


def create_alert_history_repository() -> AlertHistoryRepository:
    """
    Create a properly configured alert history repository.

    Returns:
        Configured AlertHistoryRepository instance
    """
    return AlertHistoryRepository(
        use_mcp=USE_MCP_FOR_ALERTS,
        mcp_url=MCP_SERVER_URL,
    )


def create_notification_services(channels: Optional[list] = None):
    """
    Create all requested notification services.

    Args:
        channels: List of notification channels to create services for.
                 If None, creates services for all supported channels.

    Returns:
        Dictionary mapping channel names to service instances
    """
    if channels is None:
        channels = NOTIFICATION_CHANNELS

    services = {}

    if "email" in channels:
        services["email"] = create_email_service()

    if "webhook" in channels:
        services["webhook"] = create_webhook_service()

    if "telegram" in channels:
        services["telegram"] = create_telegram_service()

    return services
