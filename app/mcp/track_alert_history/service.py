"""
Alert History Tracking Service.

This module implements asynchronous alert history tracking functionality
for storing and retrieving price alert data.
"""
import logging
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AlertHistoryRequest(BaseModel):
    """Request model for alert history tracking.

    This model defines the structure and validation rules for alert history
    tracking requests. It ensures all required data is present and properly formatted.
    """

    # Required fields with appropriate descriptions and examples
    event_type: str = Field(
        ..., description="Type of event, should be 'price_alert'", example="price_alert"
    )
    alert_id: str = Field(
        ..., description="Unique identifier for the alert", example="alert-123"
    )
    rule_id: str = Field(
        ...,
        description="ID of the alert rule that triggered this alert",
        example="rule-456",
    )
    user_id: str = Field(
        ..., description="ID of the user who received this alert", example="user-789"
    )
    product_model: str = Field(
        ..., description="Product model this alert was for", example="iPhone 15"
    )
    condition_type: str = Field(
        ...,
        description="Type of condition that triggered the alert",
        example="price_drop",
    )
    threshold: float = Field(
        ..., description="Rule threshold value", example=15.0, gt=0
    )
    triggered_value: float = Field(
        ..., description="Actual value that triggered the alert", example=20.0
    )
    notification_channels: List[str] = Field(
        ...,
        description="List of notification channels used",
        example=["email", "telegram"],
    )
    notification_status: Dict[str, bool] = Field(
        ...,
        description="Success/failure status by channel",
        example={"email": True, "telegram": True},
    )
    timestamp: str = Field(
        ...,
        description="ISO formatted timestamp when the alert was triggered",
        example="2025-05-19T12:00:00Z",
    )

    # Add validators
    @validator("event_type")
    def validate_event_type(cls, value: str) -> str:
        """Validate that event_type is 'price_alert'."""
        if value != "price_alert":
            raise ValueError("event_type must be 'price_alert'")
        return value

    @validator("condition_type")
    def validate_condition_type(cls, value: str) -> str:
        """Validate condition_type is a recognized value."""
        valid_types = ["price_drop", "price_increase", "availability", "price_target"]
        if value not in valid_types:
            raise ValueError(
                f"condition_type must be one of {', '.join(valid_types)}"
            )
        return value

    @validator("notification_channels")
    def validate_notification_channels(cls, value: List[str]) -> List[str]:
        """Validate notification channels are recognized values."""
        valid_channels = ["email", "sms", "push", "telegram", "webhook"]
        for channel in value:
            if channel not in valid_channels:
                raise ValueError(
                    f"notification_channels must contain only valid channels: {', '.join(valid_channels)}"
                )
        return value

    @validator("timestamp")
    def validate_timestamp(cls, value: str) -> str:
        """Validate timestamp is in ISO format."""
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
            return value
        except ValueError:
            raise ValueError("timestamp must be in ISO format (YYYY-MM-DDTHH:MM:SSZ)")

    @validator("notification_status")
    def validate_notification_status(
        cls, value: Dict[str, bool], values: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Validate that notification_status contains only channels from notification_channels."""
        if "notification_channels" not in values:
            return value

        channels = values["notification_channels"]
        extra_keys = set(value.keys()) - set(channels)
        if extra_keys:
            raise ValueError(
                f"notification_status contains channels not in notification_channels: {', '.join(extra_keys)}"
            )
        return value


async def save_alert_history(alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save alert history to database asynchronously.

    This function stores alert history data in the database and returns a response
    with the operation result. In a production environment, this would use a proper
    database connection, but for this example it simply logs the data.

    Args:
        alert_data: Alert history data to save, must contain all required fields

    Returns:
        Dictionary with save result information including:
            - id: Unique identifier for this alert history record
            - success: Boolean indicating if the save operation succeeded
            - timestamp: ISO-formatted timestamp of when the record was saved
            - alert_id: The original alert ID provided in the request
            - product_model: The product model this alert was for
    """
    # Generate a unique identifier for this history record
    record_id = str(uuid.uuid4())
    
    # Get current timestamp
    save_timestamp = datetime.now().isoformat()
    
    # In a real implementation, this would save to a database
    # For this example, we just log the data
    logger.info(
        "Saving alert history: ID=%s, AlertID=%s, Model=%s, User=%s",
        record_id,
        alert_data.get("alert_id", "unknown"),
        alert_data.get("product_model", "unknown"),
        alert_data.get("user_id", "unknown"),
    )
    
    # Log detailed information at debug level
    logger.debug("Alert data: %s", alert_data)
    
    # Simulate database latency for realistic testing
    await asyncio.sleep(0.1)
    
    # Return success response
    return {
        "id": record_id,
        "success": True,
        "timestamp": save_timestamp,
        "alert_id": alert_data.get("alert_id"),
        "product_model": alert_data.get("product_model"),
    }


async def track_alert_history_service(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Track price alert history asynchronously.

    This function receives price alert data, validates it and stores it in the database.

    Args:
        request_data: Alert history data to track

    Returns:
        Standardized response with status, message, data, and processing_time_ms
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Initialize empty response with error defaults
    response = {
        "status": "error",
        "message": "",
        "data": {},
        "processing_time_ms": 0
    }

    # Validate the request data
    try:
        # Convert the dictionary to a Pydantic model for validation
        request = AlertHistoryRequest(**request_data)

        # Log the request
        logger.info(
            "Processing alert history request: AlertID=%s, Model=%s, Type=%s",
            request.alert_id,
            request.product_model,
            request.condition_type,
        )

        # Save the alert history
        result = await save_alert_history(request.dict())

        # Build successful response
        response["status"] = "success"
        response["message"] = "Alert history tracked successfully"
        response["data"] = result

    except Exception as e:
        # Handle validation errors from Pydantic
        error_message = f"Error processing alert history: {str(e)}"
        logger.error(error_message)
        response["message"] = error_message

    # Calculate processing time
    response["processing_time_ms"] = int((time.time() - start_time) * 1000)
    logger.info("Alert history request processed in %d ms", response["processing_time_ms"])

    return response


async def handle_alert_history_request(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming requests for alert history tracking asynchronously.

    Args:
        params: Dictionary containing alert history data

    Returns:
        Standardized response with status, message, data, and processing_time_ms
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Initialize empty response with error defaults
    response = {
        "status": "error",
        "message": "",
        "data": {},
        "processing_time_ms": 0
    }

    try:
        # Process the request asynchronously
        result = await track_alert_history_service(params)
        return result

    except Exception as e:
        # Handle any unexpected errors
        error_message = f"Unexpected error processing alert history: {str(e)}"
        logger.error(error_message)
        response["message"] = error_message
        response["processing_time_ms"] = int((time.time() - start_time) * 1000)
        return response
