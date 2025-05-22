"""
Notification services for the Price Alert Trigger System.

This module implements various notification channel services that can be used
to send alerts to users when price alert conditions are met.
"""
import json
import logging
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

import requests

from app.core.constants import (
    FROM_EMAIL,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_SERVER,
    SMTP_USERNAME,
    TELEGRAM_BOT_TOKEN,
)


class EmailService:
    """Service for sending email notifications about price alerts."""

    def __init__(
        self,
        smtp_server: str = SMTP_SERVER,
        smtp_port: int = SMTP_PORT,
        username: str = SMTP_USERNAME,
        password: str = SMTP_PASSWORD,
        from_email: str = FROM_EMAIL,
    ):
        """
        Initialize the email service.

        Args:
            smtp_server: SMTP server hostname
            smtp_port: SMTP server port
            username: SMTP server username
            password: SMTP server password
            from_email: Email address to send notifications from
        """
        self._smtp_server = smtp_server
        self._smtp_port = smtp_port
        self._username = username
        self._password = password
        self._from_email = from_email

    def _create_message(self, to_email: str, data: Dict[str, Any]) -> MIMEMultipart:
        """
        Create email message for price alert notification.

        Args:
            to_email: Recipient email address
            data: Alert data with product and price information

        Returns:
            Formatted email message
        """
        message = MIMEMultipart("alternative")
        message["Subject"] = f"Price Alert: {data.get('product_model', 'Product')}"
        message["From"] = self._from_email
        message["To"] = to_email

        # Create HTML content
        condition_text = (
            "dropped" if data.get("condition_type") == "price_drop" else "is now below"
        )
        threshold_text = (
            f"{data.get('threshold')}%"
            if data.get("condition_type") == "price_drop"
            else f"${data.get('threshold')}"
        )

        html = f"""
        <html>
        <body>
            <h2>Price Alert for {data.get('product_model')}</h2>
            <p>Good news! The price has {condition_text} {threshold_text}.</p>
            <p>Current best price: <strong>${data.get('best_price', 'N/A')}</strong> at {data.get('best_store', 'N/A')}</p>
            <p>Price trend: {data.get('price_trend', 'Unknown')}</p>
            <hr>
            <p><small>This is an automated message from SmartNinja.</small></p>
        </body>
        </html>
        """

        # Attach HTML content
        message.attach(MIMEText(html, "html"))
        return message

    def send_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send email notification for price alert.

        Args:
            data: Alert data with product and price information
                Must include 'user_id' which is used to get user's email

        Returns:
            Dictionary with success status and any error information
        """
        try:
            # In a real implementation, we would look up the user's email
            # based on the user_id. For simplicity, we'll assume we already have it.
            user_email = f"{data.get('user_id')}@example.com"

            # Create message
            message = self._create_message(user_email, data)

            # Create secure connection with server and send email
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self._smtp_server, self._smtp_port, context=context
            ) as server:
                server.login(self._username, self._password)
                server.sendmail(self._from_email, user_email, message.as_string())

            logging.info(f"Email notification sent to {user_email}")
            return {"success": True}
        except smtplib.SMTPAuthenticationError as error:
            logging.error(
                f"SMTP authentication error while sending email notification: {error}"
            )
            return {
                "success": False,
                "error": "Authentication failed",
                "details": str(error),
            }
        except smtplib.SMTPException as error:
            logging.error(f"SMTP error while sending email notification: {error}")
            return {
                "success": False,
                "error": "Failed to send email",
                "details": str(error),
            }
        except (ConnectionError, TimeoutError) as error:
            logging.error(f"Connection error while sending email notification: {error}")
            return {
                "success": False,
                "error": "Connection failed",
                "details": str(error),
            }
        except Exception as error:
            logging.error(f"Unexpected error sending email notification: {error}")
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(error),
            }


class WebhookService:
    """Service for sending webhook notifications about price alerts."""

    def send_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send webhook notification for price alert.

        Args:
            data: Alert data with product and price information
                Must include 'user_id' which is used to get webhook URL

        Returns:
            Dictionary with success status and any error information
        """
        try:
            # In a real implementation, we would look up the user's webhook URL
            # based on the user_id. For simplicity, we'll use a placeholder.
            webhook_url = f"https://example.com/webhooks/{data.get('user_id')}"

            # Prepare data payload
            payload = {
                "event_type": "price_alert",
                "product_model": data.get("product_model"),
                "condition_type": data.get("condition_type"),
                "threshold": data.get("threshold"),
                "triggered_value": data.get("triggered_value"),
                "best_price": data.get("best_price"),
                "best_store": data.get("best_store"),
            }

            # Send webhook request
            response = requests.post(
                webhook_url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=5,
            )

            # Check response
            if response.status_code < 300:
                logging.info(f"Webhook notification sent to {webhook_url}")
                return {"success": True}
            else:
                error_msg = f"Webhook request failed with status {response.status_code}"
                logging.error(error_msg)
                return {
                    "success": False,
                    "error": "API error",
                    "status_code": response.status_code,
                    "details": response.text[:100],  # Limit response text size
                }
        except requests.ConnectionError as error:
            logging.error(f"Connection error sending webhook notification: {error}")
            return {
                "success": False,
                "error": "Connection failed",
                "details": str(error),
            }
        except requests.Timeout as error:
            logging.error(f"Timeout sending webhook notification: {error}")
            return {
                "success": False,
                "error": "Request timed out",
                "details": str(error),
            }
        except requests.RequestException as error:
            logging.error(f"Request error sending webhook notification: {error}")
            return {"success": False, "error": "Request failed", "details": str(error)}
        except Exception as error:
            logging.error(f"Unexpected error sending webhook notification: {error}")
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(error),
            }


class TelegramService:
    """Service for sending Telegram notifications about price alerts."""

    def __init__(self, bot_token: str = TELEGRAM_BOT_TOKEN):
        """
        Initialize the Telegram service.

        Args:
            bot_token: Telegram bot API token
        """
        self._bot_token = bot_token
        self._api_url = f"https://api.telegram.org/bot{bot_token}"

    def _get_chat_id(self, user_id: str) -> Optional[str]:
        """
        Get Telegram chat ID for the user.

        Args:
            user_id: User ID to get chat ID for

        Returns:
            Telegram chat ID or None if not found
        """
        # In a real implementation, this would query a database to find
        # the user's Telegram chat ID based on their user ID.
        # For simplicity, we'll use a placeholder.
        return f"telegram_{user_id}"

    def send_notification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send Telegram notification for price alert.

        Args:
            data: Alert data with product and price information
                Must include 'user_id' which is used to get Telegram chat ID

        Returns:
            Dictionary with success status and any error information
        """
        try:
            # Get chat ID for user
            chat_id = self._get_chat_id(data.get("user_id"))
            if not chat_id:
                error = f"No Telegram chat ID found for user {data.get('user_id')}"
                logging.error(error)
                return {"success": False, "error": error}

            # Create message text
            condition_text = (
                "dropped"
                if data.get("condition_type") == "price_drop"
                else "is now below"
            )
            threshold_text = (
                f"{data.get('threshold')}%"
                if data.get("condition_type") == "price_drop"
                else f"${data.get('threshold')}"
            )

            message = (
                f"🔔 *Price Alert for {data.get('product_model')}*\n\n"
                f"Good news! The price has {condition_text} {threshold_text}.\n"
                f"Current best price: *${data.get('best_price', 'N/A')}* at {data.get('best_store', 'N/A')}\n"
                f"Price trend: {data.get('price_trend', 'Unknown')}"
            )

            # Send message
            response = requests.post(
                f"{self._api_url}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                },
                timeout=5,
            )

            # Check response
            if response.status_code == 200:
                logging.info(f"Telegram notification sent to chat {chat_id}")
                return {"success": True}
            else:
                error_msg = (
                    f"Telegram request failed with status {response.status_code}"
                )
                logging.error(f"{error_msg}: {response.text[:100]}")
                return {
                    "success": False,
                    "error": "Telegram API error",
                    "status_code": response.status_code,
                    "details": response.text[:100],  # Limit response text size
                }
        except requests.ConnectionError as error:
            logging.error(f"Connection error sending Telegram notification: {error}")
            return {
                "success": False,
                "error": "Connection failed",
                "details": str(error),
            }
        except requests.Timeout as error:
            logging.error(f"Timeout sending Telegram notification: {error}")
            return {
                "success": False,
                "error": "Request timed out",
                "details": str(error),
            }
        except requests.RequestException as error:
            logging.error(f"Request error sending Telegram notification: {error}")
            return {"success": False, "error": "Request failed", "details": str(error)}
        except Exception as error:
            logging.error(f"Unexpected error sending Telegram notification: {error}")
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(error),
            }
