"""
Repository implementations for the Price Alert Trigger System.

This module provides repository classes for storing and retrieving alert rules
and alert history, supporting both local database and MCP server storage.
"""
import json
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

import requests
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.models import AlertHistory, AlertRule


class BaseRepository(ABC):
    """Base repository class with common functionality."""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the repository with an optional database session.

        Args:
            db: Optional database session. If not provided, will be created when needed
        """
        self._db = db

    def _get_db(self) -> Session:
        """
        Get a database session.

        Returns:
            Active SQLAlchemy database session
        """
        return self._db if self._db else next(get_db())

    @abstractmethod
    def save(self, entity: Any) -> Dict[str, Any]:
        """Save an entity to the repository."""
        pass


class AlertRuleRepository(BaseRepository):
    """Repository for managing alert rules in the database."""

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize the alert rule repository.

        Args:
            db: Optional database session. If not provided, will be created when needed
        """
        super().__init__(db)

    def _get_db(self) -> Session:
        """
        Get a database session.

        Returns:
            Active SQLAlchemy database session
        """
        return self._db if self._db else next(get_db())

    def get_rules_for_product(self, model: str, country: str) -> List[AlertRule]:
        """
        Get all active alert rules for a specific product model and country.

        Args:
            model: Product model name
            country: Country code

        Returns:
            List of active alert rules
        """
        db = self._get_db()
        return (
            db.query(AlertRule)
            .filter(
                AlertRule.product_model == model,
                AlertRule.country == country,
                AlertRule.is_active == True,
            )
            .all()
        )

    def get_rule_by_id(self, rule_id: str) -> Optional[AlertRule]:
        """
        Get an alert rule by its ID.

        Args:
            rule_id: The ID of the rule to retrieve

        Returns:
            The alert rule or None if not found
        """
        db = self._get_db()
        return db.query(AlertRule).filter(AlertRule.id == rule_id).first()

    def create_rule(self, rule: AlertRule) -> AlertRule:
        """
        Create a new alert rule.

        Args:
            rule: The alert rule to create

        Returns:
            The created alert rule
        """
        if not rule.id:
            rule.id = str(uuid.uuid4())

        db = self._get_db()
        db.add(rule)
        db.commit()
        db.refresh(rule)
        return rule

    def update_rule(self, rule: AlertRule) -> AlertRule:
        """
        Update an existing alert rule.

        Args:
            rule: The alert rule to update

        Returns:
            The updated alert rule

        Raises:
            ValueError: If the rule doesn't exist
        """
        db = self._get_db()
        existing_rule = db.query(AlertRule).filter(AlertRule.id == rule.id).first()

        if not existing_rule:
            raise ValueError(f"Alert rule with ID {rule.id} not found")

        # Update fields
        existing_rule.product_model = rule.product_model
        existing_rule.country = rule.country
        existing_rule.condition_type = rule.condition_type
        existing_rule.threshold = rule.threshold
        existing_rule.time_period_days = rule.time_period_days
        existing_rule.notification_channels = rule.notification_channels
        existing_rule.is_active = rule.is_active
        existing_rule.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_rule)
        return existing_rule

    def delete_rule(self, rule_id: str) -> bool:
        """
        Delete an alert rule.

        Args:
            rule_id: The ID of the rule to delete

        Returns:
            True if the rule was deleted, False if it wasn't found
        """
        db = self._get_db()
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()

        if not rule:
            return False

        db.delete(rule)
        db.commit()
        return True


class AlertHistoryRepository(BaseRepository):
    """Repository for storing alert history in the database."""

    def __init__(
        self,
        db: Optional[Session] = None,
        use_mcp: bool = False,
        mcp_url: Optional[str] = None,
    ):
        """
        Initialize the alert history repository.

        Args:
            db: Optional database session. If not provided, will be created when needed
            use_mcp: Whether to use MCP server for history storage
            mcp_url: URL of the MCP server when use_mcp is True
        """
        super().__init__(db)
        self._use_mcp = use_mcp
        self._mcp_url = mcp_url

    def save(self, alert_history: AlertHistory) -> Dict[str, Any]:
        """
        Save an alert history record.

        Args:
            alert_history: The alert history to save

        Returns:
            Dictionary with save result information
        """
        if not alert_history.id:
            alert_history.id = str(uuid.uuid4())

        # Always try to save to the local database
        try:
            db = self._get_db()
            db.add(alert_history)
            db.commit()
            db.refresh(alert_history)
            result = {"id": alert_history.id, "success": True}
        except Exception as error:
            logging.error(f"Failed to save alert history to database: {str(error)}")
            result = {"success": False, "error": str(error)}

        # If MCP is enabled, also send to MCP server
        if self._use_mcp and self._mcp_url:
            try:
                mcp_result = self._save_to_mcp(alert_history)
                result["mcp"] = mcp_result
            except Exception as error:
                logging.error(
                    f"Failed to save alert history to MCP server: {str(error)}"
                )
                result["mcp"] = {"success": False, "error": str(error)}

        return result

    def _save_to_mcp(self, alert_history: AlertHistory) -> Dict[str, Any]:
        """
        Save alert history to MCP server.

        Args:
            alert_history: The alert history to save

        Returns:
            Dictionary with MCP save result information
        """
        if not self._mcp_url:
            return {"success": False, "error": "MCP URL not configured"}

        # Prepare payload for MCP
        payload = {
            "event_type": "price_alert",
            "alert_id": alert_history.id,
            "rule_id": alert_history.rule_id,
            "user_id": alert_history.user_id,
            "product_model": alert_history.product_model,
            "condition_type": alert_history.condition_type,
            "threshold": alert_history.threshold,
            "triggered_value": alert_history.triggered_value,
            "notification_channels": alert_history.notification_channels,
            "notification_status": alert_history.notification_status,
            "timestamp": alert_history.created_at.isoformat(),
        }

        # Send to MCP server
        response = requests.post(
            f"{self._mcp_url}/track_alert_history",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )

        # Process response
        if response.status_code < 300:
            return {"success": True, "mcp_id": response.json().get("id")}
        else:
            error = f"MCP request failed with status {response.status_code}"
            logging.error(error)
            return {"success": False, "error": error}

    def get_history_for_user(
        self, user_id: str, limit: int = 100
    ) -> List[AlertHistory]:
        """
        Get alert history for a specific user.

        Args:
            user_id: The ID of the user to get history for
            limit: Maximum number of records to return

        Returns:
            List of alert history records
        """
        db = self._get_db()
        return (
            db.query(AlertHistory)
            .filter(AlertHistory.user_id == user_id)
            .order_by(AlertHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def get_history_for_product(
        self, model: str, country: str, limit: int = 100
    ) -> List[AlertHistory]:
        """
        Get alert history for a specific product model and country.

        Args:
            model: Product model name
            country: Country code
            limit: Maximum number of records to return

        Returns:
            List of alert history records
        """
        db = self._get_db()
        # Query alert history for the specified model and join with alert rules to filter by country
        return (
            db.query(AlertHistory)
            .join(AlertRule, AlertHistory.rule_id == AlertRule.id)
            .filter(AlertHistory.product_model == model, AlertRule.country == country)
            .order_by(AlertHistory.created_at.desc())
            .limit(limit)
            .all()
        )
