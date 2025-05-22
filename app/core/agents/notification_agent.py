"""
Notification Agent for evaluating alert conditions and triggering notifications.

This agent is responsible for checking if price data meets user-defined alert
conditions and sending notifications through configured channels.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.agents.base_agent import BaseAgent
from app.core.models import AlertHistory, AlertRule


class NotificationAgent(BaseAgent):
    """
    Agent that evaluates price alert conditions and triggers notifications.

    This agent checks incoming price data against user-defined alert rules,
    and sends notifications through configured channels when conditions are met.
    """

    def __init__(
        self,
        email_service: Optional[Any] = None,
        webhook_service: Optional[Any] = None,
        telegram_service: Optional[Any] = None,
        alert_history_repository: Optional[Any] = None,
    ):
        """
        Initialize the notification agent with notification services.

        Args:
            email_service: Service for sending email notifications
            webhook_service: Service for sending webhook notifications
            telegram_service: Service for sending Telegram notifications
            alert_history_repository: Repository for storing alert history
        """
        self._email_service = email_service
        self._webhook_service = webhook_service
        self._telegram_service = telegram_service
        self._alert_history_repository = alert_history_repository

    def get_alert_rules(self, model: str, country: str) -> List[AlertRule]:
        """
        Retrieve alert rules for the specified model and country.

        Args:
            model: Product model name
            country: Country code

        Returns:
            List of alert rules applicable to the model and country
        """
        # This would typically query a database
        # For testing purposes, this may be mocked
        # In a real implementation, this would be replaced with database access
        return []  # Placeholder that will be mocked in tests

    def evaluate_price_drop_condition(
        self, rule: AlertRule, analysis_data: Dict[str, Any]
    ) -> Optional[float]:
        """
        Evaluate if a price drop condition is met.

        Args:
            rule: The alert rule to evaluate
            analysis_data: Analysis data containing price information

        Returns:
            The trigger value (percentage drop) if condition is met, None otherwise
        """
        # Check if we have price drop information
        price_data = analysis_data.get("price_data", [])
        if not price_data:
            return None

        # Find the item with the largest price drop
        max_drop_percent = 0.0
        for item in price_data:
            if (
                "price_change_percent" in item
                and item["price_change_percent"] < 0  # Negative means price drop
            ):
                drop_percent = abs(item["price_change_percent"])
                max_drop_percent = max(max_drop_percent, drop_percent)

        # Check if the maximum drop meets the threshold
        if max_drop_percent >= rule.threshold:
            return max_drop_percent

        return None

    def evaluate_price_below_condition(
        self, rule: AlertRule, analysis_data: Dict[str, Any]
    ) -> Optional[float]:
        """
        Evaluate if a price below threshold condition is met.

        Args:
            rule: The alert rule to evaluate
            analysis_data: Analysis data containing price information

        Returns:
            The trigger value (lowest price) if condition is met, None otherwise
        """
        # Check if we have price data
        price_data = analysis_data.get("price_data", [])
        if not price_data:
            return None

        # Find the lowest price
        lowest_price = float("inf")
        for item in price_data:
            if "price" in item:
                lowest_price = min(lowest_price, float(item["price"]))

        # Check if the lowest price is below the threshold
        if lowest_price < rule.threshold:
            return lowest_price

        return None

    def evaluate_condition(
        self, rule: AlertRule, analysis_data: Dict[str, Any]
    ) -> Optional[float]:
        """
        Evaluate if an alert condition is met based on the rule type.

        Args:
            rule: The alert rule to evaluate
            analysis_data: Analysis data containing price information

        Returns:
            The trigger value if condition is met, None otherwise
        """
        if not rule.is_active:
            return None

        if rule.condition_type == "price_drop":
            return self.evaluate_price_drop_condition(rule, analysis_data)
        elif rule.condition_type == "price_below":
            return self.evaluate_price_below_condition(rule, analysis_data)
        else:
            logging.warning(f"Unknown condition type: {rule.condition_type}")
            return None

    def send_notification(
        self, rule: AlertRule, trigger_value: float, analysis_data: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Send notifications to all channels configured in the rule.

        Args:
            rule: The alert rule that was triggered
            trigger_value: The value that triggered the alert
            analysis_data: Analysis data containing price information

        Returns:
            Dictionary mapping channel names to notification success status
        """
        notification_status = {}

        # Prepare notification data
        notification_data = {
            "rule_id": rule.id,
            "user_id": rule.user_id,
            "product_model": rule.product_model,
            "condition_type": rule.condition_type,
            "threshold": rule.threshold,
            "triggered_value": trigger_value,
            "best_price": analysis_data.get("lowest_price"),
            "best_store": None,
            "price_trend": analysis_data.get("price_trend"),
        }

        # Find the best store (lowest price)
        price_data = analysis_data.get("price_data", [])
        if price_data:
            best_price_item = min(
                price_data, key=lambda x: float(x.get("price", float("inf")))
            )
            notification_data["best_store"] = best_price_item.get("store")

        # Send to each configured channel
        for channel in rule.notification_channels:
            try:
                if channel == "email" and self._email_service:
                    result = self._email_service.send_notification(notification_data)
                    notification_status["email"] = result.get("success", False)
                elif channel == "webhook" and self._webhook_service:
                    result = self._webhook_service.send_notification(notification_data)
                    notification_status["webhook"] = result.get("success", False)
                elif channel == "telegram" and self._telegram_service:
                    result = self._telegram_service.send_notification(notification_data)
                    notification_status["telegram"] = result.get("success", False)
                else:
                    logging.warning(f"Unsupported notification channel: {channel}")
                    notification_status[channel] = False
            except Exception as error:
                logging.error(f"Error sending {channel} notification: {str(error)}")
                notification_status[channel] = False

        return notification_status

    def save_alert_history(
        self,
        rule: AlertRule,
        trigger_value: float,
        notification_status: Dict[str, bool],
    ) -> Dict[str, Any]:
        """
        Save a record of the triggered alert in the history.

        Args:
            rule: The alert rule that was triggered
            trigger_value: The value that triggered the alert
            notification_status: Status of each notification channel

        Returns:
            Dict with save result information
        """
        if not self._alert_history_repository:
            return {"success": False, "error": "No alert history repository available"}

        # Create alert history instance
        alert_history = AlertHistory(
            id=f"alert-{rule.id}",  # Simplified ID generation for example
            rule_id=rule.id,
            user_id=rule.user_id,
            product_model=rule.product_model,
            condition_type=rule.condition_type,
            threshold=rule.threshold,
            triggered_value=trigger_value,
            notification_channels=rule.notification_channels,
            notification_status=notification_status,
        )

        # Save to repository
        return self._alert_history_repository.save(alert_history)

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate alert conditions and trigger notifications if needed.

        Args:
            input_data: Dictionary containing analysis results and price data
                Must include 'model' and 'country' for rule retrieval

        Returns:
            Dictionary with alert evaluation results and any triggered alerts

        Raises:
            ValueError: If required data is missing
            RuntimeError: If there's a critical failure in alert processing
        """
        try:
            # Validate required inputs
            if "model" not in input_data:
                raise ValueError("Input data must include 'model'")
            if "country" not in input_data:
                raise ValueError("Input data must include 'country'")

            model = input_data.get("model")
            country = input_data.get("country")

            logging.info(f"Checking alert rules for {model} in {country}")

            # Initialize result
            result = {
                "alerts_triggered": [],
                "notification_errors": [],
                "rules_evaluated": 0,
                "rules_triggered": 0,
                "model": model,
                "country": country,
            }

            # Get alert rules for this model and country
            alert_rules = self.get_alert_rules(model, country)
            if not alert_rules:
                logging.info(f"No alert rules found for {model} in {country}")
                return result

            # Evaluate each rule
            for rule in alert_rules:
                # Increment counter for monitored metrics
                result["rules_evaluated"] += 1

                # Skip inactive rules
                if not rule.is_active:
                    logging.info(f"Skipping inactive rule {rule.id}")
                    continue

                try:
                    # Evaluate rule condition
                    trigger_value = self.evaluate_condition(rule, input_data)

                    # If condition is met, trigger notification
                    if trigger_value is not None:
                        logging.info(
                            f"Alert rule {rule.id} triggered with value {trigger_value}"
                        )
                        result["rules_triggered"] += 1

                        # Send notifications
                        notification_status = self.send_notification(
                            rule, trigger_value, input_data
                        )

                        # Save alert history using the established method
                        history_result = self.save_alert_history(
                            rule=rule,
                            trigger_value=trigger_value,
                            notification_status=notification_status,
                        )

                        # Check if history was successfully saved
                        history_saved = "id" in history_result

                        # Add to result
                        alert_result = {
                            "rule_id": rule.id,
                            "user_id": rule.user_id,
                            "condition_type": rule.condition_type,
                            "threshold": rule.threshold,
                            "triggered_value": trigger_value,
                            "notification_status": notification_status,
                            "history_saved": history_saved,
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                        result["alerts_triggered"].append(alert_result)

                        # Track notification errors
                        for channel, success in notification_status.items():
                            if not success:
                                error_msg = f"Failed to send {channel} notification for rule {rule.id}"
                                logging.warning(error_msg)
                                result["notification_errors"].append(error_msg)
                except Exception as rule_error:
                    error_msg = f"Error processing rule {rule.id}: {rule_error}"
                    logging.error(error_msg)
                    result["notification_errors"].append(error_msg)
                    # Continue processing other rules

            return result
        except Exception as error:
            logging.error(f"Critical error in NotificationAgent.execute: {error}")
            # Re-raise with more context for better error handling upstream
            raise RuntimeError(f"Failed to process alerts: {error}") from error
