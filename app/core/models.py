"""Database models for the SmartNinja application.
This module defines all SQLAlchemy models used in the application,
following the DRY principle and SOLID design.
"""
from datetime import datetime
from typing import Dict, List, Optional, Union

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

# Import Base from database module
from app.core.database import Base


# pylint: disable=too-few-public-methods
class Phone(Base):
    """Model for mobile phones (ORM entity, deliberately has few methods)"""

    __tablename__ = "phones"
    id = Column(Integer, primary_key=True)
    model = Column(String(100), nullable=False)
    brand = Column(String(50), nullable=False)
    storage = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    prices = relationship("Price", back_populates="phone", cascade="all, delete-orphan")


class Price(Base):
    """Model for phone prices (ORM entity, deliberately has few methods)"""

    __tablename__ = "prices"
    id = Column(Integer, primary_key=True)
    phone_id = Column(Integer, ForeignKey("phones.id"), nullable=False)
    region = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False)
    source = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    phone = relationship("Phone", back_populates="prices")


class Alert(Base):
    """Model for price alerts (ORM entity, deliberately has few methods)"""

    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    phone_id = Column(Integer, ForeignKey("phones.id"), nullable=False)
    threshold = Column(Float, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    phone = relationship("Phone")


class Analysis(Base):
    """Model for AI analysis results (ORM entity, deliberately has few methods)"""

    __tablename__ = "analysis"
    id = Column(Integer, primary_key=True)
    phone_id = Column(Integer, ForeignKey("phones.id"))
    region = Column(String(50))
    insights = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    phone = relationship("Phone")


class AlertRule(Base):
    """
    Model for alert rule configurations.

    This model defines the conditions that trigger price alerts
    and the notification channels to use when triggered.
    """

    __tablename__ = "alert_rules"
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False)
    product_model = Column(String(100), nullable=False)
    country = Column(String(2), nullable=False)
    condition_type = Column(String(20), nullable=False)  # price_drop, price_below, etc.
    threshold = Column(Float, nullable=False)
    time_period_days = Column(Integer)  # Only relevant for some condition types
    notification_channels = Column(JSON, nullable=False)  # Array of strings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(
        self,
        id: str,
        user_id: str,
        product_model: str,
        country: str,
        condition_type: str,
        threshold: float,
        notification_channels: List[str],
        is_active: bool = True,
        time_period_days: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """
        Initialize an AlertRule instance.

        Args:
            id: Unique identifier for the rule
            user_id: User who owns this rule
            product_model: Product model this rule applies to
            country: Country code this rule applies to
            condition_type: Type of condition (price_drop, price_below, etc.)
            threshold: Threshold value for the condition
            notification_channels: List of notification channels to use
            is_active: Whether this rule is currently active
            time_period_days: Time period for conditions that need it
            created_at: Creation timestamp
            updated_at: Last update timestamp
        """
        self.id = id
        self.user_id = user_id
        self.product_model = product_model
        self.country = country
        self.condition_type = condition_type
        self.threshold = threshold
        self.notification_channels = notification_channels
        self.is_active = is_active
        self.time_period_days = time_period_days
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()


class AlertHistory(Base):
    """
    Model for alert history tracking.

    Records triggered alerts for historical reference and analytics.
    """

    __tablename__ = "alert_history"
    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), ForeignKey("alert_rules.id"), nullable=False)
    user_id = Column(String(36), nullable=False)
    product_model = Column(String(100), nullable=False)
    condition_type = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    triggered_value = Column(Float, nullable=False)
    notification_channels = Column(JSON, nullable=False)
    notification_status = Column(JSON, nullable=False)  # Success/failure by channel
    created_at = Column(DateTime, default=datetime.utcnow)

    def __init__(
        self,
        id: str,
        rule_id: str,
        user_id: str,
        product_model: str,
        condition_type: str,
        threshold: float,
        triggered_value: float,
        notification_channels: List[str],
        notification_status: Dict[str, bool],
        created_at: Optional[datetime] = None,
    ):
        """
        Initialize an AlertHistory instance.

        Args:
            id: Unique identifier for the history record
            rule_id: ID of the rule that triggered this alert
            user_id: User who received this alert
            product_model: Product model this alert was for
            condition_type: Type of condition that triggered the alert
            threshold: Rule threshold value
            triggered_value: Actual value that triggered the alert
            notification_channels: List of notification channels used
            notification_status: Success/failure status by channel
            created_at: Creation timestamp
        """
        self.id = id
        self.rule_id = rule_id
        self.user_id = user_id
        self.product_model = product_model
        self.condition_type = condition_type
        self.threshold = threshold
        self.triggered_value = triggered_value
        self.notification_channels = notification_channels
        self.notification_status = notification_status
        self.created_at = created_at or datetime.utcnow()
