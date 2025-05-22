"""
Unit tests for the Notification Agent.
Tests the agent that evaluates alert conditions and triggers notifications.
"""
import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.core.agents.notification_agent import NotificationAgent
from app.core.models import AlertRule


class TestNotificationAgent(unittest.TestCase):
    """Test suite for the Notification Agent implementation"""

    def setUp(self):
        """Set up test dependencies"""
        # Create mock email service
        self.mock_email_service = MagicMock()
        self.mock_email_service.send_notification.return_value = {"success": True}

        # Create mock webhook service
        self.mock_webhook_service = MagicMock()
        self.mock_webhook_service.send_notification.return_value = {"success": True}

        # Create mock telegram service
        self.mock_telegram_service = MagicMock()
        self.mock_telegram_service.send_notification.return_value = {"success": True}

        # Create mock alert history repository
        self.mock_alert_history_repo = MagicMock()
        self.mock_alert_history_repo.save.return_value = {"id": "alert-123"}

        # Create a notification agent with mock dependencies
        self.notification_agent = NotificationAgent(
            email_service=self.mock_email_service,
            webhook_service=self.mock_webhook_service,
            telegram_service=self.mock_telegram_service,
            alert_history_repository=self.mock_alert_history_repo,
        )

        # Sample analysis data with price drop
        self.sample_analysis_data = {
            "analysis": "Prices have dropped significantly over the past 7 days.",
            "average_price": 899.99,
            "lowest_price": 799.99,
            "highest_price": 999.99,
            "price_range": 200.0,
            "previous_average_price": 999.99,  # Price from 7 days ago
            "price_trend": "decreasing",
            "price_data": [
                {
                    "price": 799.99,
                    "store": "Amazon",
                    "region": "US",
                    "model": "iPhone 15",
                    "timestamp": datetime.now().isoformat(),
                    "previous_price": 999.99,  # Price from 7 days ago
                    "price_change_percent": -20.0,  # 20% price drop
                },
                {
                    "price": 849.99,
                    "store": "BestBuy",
                    "region": "US",
                    "model": "iPhone 15",
                    "timestamp": datetime.now().isoformat(),
                    "previous_price": 949.99,  # Price from 7 days ago
                    "price_change_percent": -10.5,  # 10.5% price drop
                },
            ],
            "model": "iPhone 15",
            "country": "US",
        }

        # Sample alert rule for price drop
        self.price_drop_rule = AlertRule(
            id="rule-123",
            user_id="user-456",
            product_model="iPhone 15",
            country="US",
            condition_type="price_drop",
            threshold=15.0,  # 15% price drop
            time_period_days=7,
            notification_channels=["email", "telegram"],
            is_active=True,
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=10),
        )

        # Sample alert rule for price threshold
        self.price_threshold_rule = AlertRule(
            id="rule-789",
            user_id="user-456",
            product_model="iPhone 15",
            country="US",
            condition_type="price_below",
            threshold=850.0,  # Alert when price is below $850
            notification_channels=["webhook"],
            is_active=True,
            created_at=datetime.now() - timedelta(days=15),
            updated_at=datetime.now() - timedelta(days=5),
        )

    def test_evaluate_alert_conditions_price_drop(self):
        """Test alert condition evaluation for price drop rule.

        This test verifies that when a price drop is detected that meets the alert
        rule threshold, the system properly sends notifications via the configured
        channels and saves the alert to the history repository.
        """
        # Mock get_alert_rules to return price drop rule
        with patch.object(
            self.notification_agent,
            "get_alert_rules",
            return_value=[self.price_drop_rule],
        ):
            # Execute the agent
            result = self.notification_agent.execute(self.sample_analysis_data)

            # Verify alert was triggered for price drop rule
            self.assertEqual(
                len(result["alerts_triggered"]),
                1,
                "Should trigger exactly one alert for price drop rule",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["rule_id"],
                "rule-123",
                "The triggered alert should have the correct rule_id",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["condition_type"],
                "price_drop",
                "The triggered alert should have the correct condition_type",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["triggered_value"],
                20.0,
                "The triggered alert should have the correct triggered_value",
            )

            # Verify notifications were sent to correct channels
            self.mock_email_service.send_notification.assert_called_once()
            self.mock_telegram_service.send_notification.assert_called_once()
            self.mock_webhook_service.send_notification.assert_not_called()

            # Verify alert history was saved exactly once (this is failing)
            self.assertEqual(
                self.mock_alert_history_repo.save.call_count,
                1,
                "Alert history should be saved exactly once",
            )

    def test_evaluate_alert_conditions_price_threshold(self):
        """Test alert condition evaluation for price threshold rule.

        This test verifies that when a price falls below a threshold defined in an alert rule,
        the system properly sends notifications via the configured channels and saves the
        alert to the history repository.
        """
        # Mock get_alert_rules to return price threshold rule
        with patch.object(
            self.notification_agent,
            "get_alert_rules",
            return_value=[self.price_threshold_rule],
        ):
            # Execute the agent
            result = self.notification_agent.execute(self.sample_analysis_data)

            # Verify alert was triggered for price threshold rule
            self.assertEqual(
                len(result["alerts_triggered"]),
                1,
                "Should trigger exactly one alert for price threshold rule",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["rule_id"],
                "rule-789",
                "The triggered alert should have the correct rule_id",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["condition_type"],
                "price_below",
                "The triggered alert should have the correct condition_type",
            )
            self.assertEqual(
                result["alerts_triggered"][0]["triggered_value"],
                799.99,
                "The triggered alert should have the correct triggered_value",
            )

            # Verify notifications were sent to correct channels
            self.mock_email_service.send_notification.assert_not_called()
            self.mock_telegram_service.send_notification.assert_not_called()
            self.mock_webhook_service.send_notification.assert_called_once()

            # Verify alert history was saved exactly once
            self.assertEqual(
                self.mock_alert_history_repo.save.call_count,
                1,
                "Alert history should be saved exactly once",
            )

    def test_no_alerts_triggered(self):
        """Test when no alert conditions are met"""
        # Sample data with no significant price changes
        no_change_data = {
            "analysis": "Prices are stable across retailers.",
            "average_price": 999.99,
            "lowest_price": 989.99,
            "highest_price": 1009.99,
            "price_range": 20.0,
            "previous_average_price": 999.99,
            "price_trend": "stable",
            "price_data": [
                {
                    "price": 989.99,
                    "store": "Amazon",
                    "region": "US",
                    "model": "iPhone 15",
                    "timestamp": datetime.now().isoformat(),
                    "previous_price": 989.99,
                    "price_change_percent": 0.0,
                },
            ],
            "model": "iPhone 15",
            "country": "US",
        }

        # Mock get_alert_rules to return price drop rule
        with patch.object(
            self.notification_agent,
            "get_alert_rules",
            return_value=[self.price_drop_rule],
        ):
            # Execute the agent
            result = self.notification_agent.execute(no_change_data)

            # Verify no alerts were triggered
            self.assertEqual(len(result["alerts_triggered"]), 0)

            # Verify no notifications were sent
            self.mock_email_service.send_notification.assert_not_called()
            self.mock_telegram_service.send_notification.assert_not_called()
            self.mock_webhook_service.send_notification.assert_not_called()

            # Verify alert history was not saved
            self.mock_alert_history_repo.save.assert_not_called()

    def test_multiple_rules_evaluation(self):
        """Test evaluation of multiple alert rules.

        This test verifies that when multiple alert rules are triggered for the same price data,
        the system properly handles each rule independently, sends notifications for all
        configured channels, and saves each alert to the history repository.
        """
        # Mock get_alert_rules to return both rules
        with patch.object(
            self.notification_agent,
            "get_alert_rules",
            return_value=[self.price_drop_rule, self.price_threshold_rule],
        ):
            # Execute the agent
            result = self.notification_agent.execute(self.sample_analysis_data)

            # Verify both alerts were triggered
            self.assertEqual(
                len(result["alerts_triggered"]),
                2,
                "Should trigger exactly two alerts, one for each rule",
            )

            # Verify all notification channels were used
            self.mock_email_service.send_notification.assert_called_once()
            self.mock_telegram_service.send_notification.assert_called_once()
            self.mock_webhook_service.send_notification.assert_called_once()

            # Verify alert history was saved twice (once per rule)
            self.assertEqual(
                self.mock_alert_history_repo.save.call_count,
                2,
                "Alert history should be saved exactly twice, once for each rule",
            )

    def test_inactive_rule_not_triggered(self):
        """Test that inactive rules don't trigger alerts"""
        # Create inactive rule
        inactive_rule = AlertRule(
            id="rule-inactive",
            user_id="user-456",
            product_model="iPhone 15",
            country="US",
            condition_type="price_drop",
            threshold=5.0,  # 5% price drop (would trigger with our sample data)
            time_period_days=7,
            notification_channels=["email"],
            is_active=False,  # Inactive rule
            created_at=datetime.now() - timedelta(days=30),
            updated_at=datetime.now() - timedelta(days=10),
        )

        # Mock get_alert_rules to return inactive rule
        with patch.object(
            self.notification_agent, "get_alert_rules", return_value=[inactive_rule]
        ):
            # Execute the agent
            result = self.notification_agent.execute(self.sample_analysis_data)

            # Verify no alerts were triggered due to inactive rule
            self.assertEqual(len(result["alerts_triggered"]), 0)

            # Verify no notifications were sent
            self.mock_email_service.send_notification.assert_not_called()
            self.mock_telegram_service.send_notification.assert_not_called()
            self.mock_webhook_service.send_notification.assert_not_called()

    def test_error_in_notification_channel(self):
        """Test handling of errors in notification channels.

        This test verifies that when a notification channel encounters an error,
        the system properly handles the exception, continues processing other channels,
        records the error in the result, and still saves the alert to history.
        """
        # Configure email service to raise an exception
        self.mock_email_service.send_notification.side_effect = Exception(
            "Email service error"
        )

        # Mock get_alert_rules to return price drop rule (which uses email)
        with patch.object(
            self.notification_agent,
            "get_alert_rules",
            return_value=[self.price_drop_rule],
        ):
            # Execute the agent
            result = self.notification_agent.execute(self.sample_analysis_data)

            # Verify alert was still triggered
            self.assertEqual(
                len(result["alerts_triggered"]),
                1,
                "Should trigger exactly one alert despite notification error",
            )

            # Verify notification errors were reported
            self.assertEqual(
                len(result["notification_errors"]),
                1,
                "Should report exactly one notification error",
            )
            self.assertIn(
                "email",
                result["notification_errors"][0],
                "Error should reference the failed email channel",
            )

            # Verify other channel was still used
            self.mock_telegram_service.send_notification.assert_called_once()

            # Verify alert history was still saved
            self.assertEqual(
                self.mock_alert_history_repo.save.call_count,
                1,
                "Alert history should still be saved despite notification error",
            )


if __name__ == "__main__":
    unittest.main()
