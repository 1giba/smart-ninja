"""
Price History Tracking Service.

This module implements asynchronous price history tracking functionality,
stores price data, computes historical trends and optionally triggers alerts.
"""
import logging
import os
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

from dotenv import load_dotenv

from app.core.history import (
    AlertNotifier,
    AlertRule,
    ConsoleAlertNotifier,
    PriceHistoryAnalyzer,
    PriceHistoryRepository,
    SQLitePriceHistoryRepository,
    WebhookAlertNotifier,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def create_history_components() -> Tuple[
    PriceHistoryRepository, PriceHistoryAnalyzer, AlertNotifier
]:
    """
    Create and configure the components for price history tracking with dependency injection.

    Returns:
        Tuple containing PriceHistoryRepository, PriceHistoryAnalyzer, and AlertNotifier instances
    """
    # Start timing for performance monitoring
    start_time = time.time()

    try:
        # Create the repository
        db_path = os.getenv("PRICE_HISTORY_DB_PATH", "price_history.db")
        repository = SQLitePriceHistoryRepository(db_path)

        # Create the analyzer
        analyzer = PriceHistoryAnalyzer()

        # Create the notifier with appropriate configuration
        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if webhook_url:
            notifier = WebhookAlertNotifier(webhook_url)
            logger.info("Using WebhookAlertNotifier with URL: %s", webhook_url)
        else:
            notifier = ConsoleAlertNotifier()
            logger.info("Using ConsoleAlertNotifier (fallback)")

        # Measure and log initialization time
        init_time = time.time() - start_time
        logger.info("History components initialized in %.2f seconds", init_time)

        return repository, analyzer, notifier

    except Exception as error:
        logger.error("Failed to initialize history components: %s", str(error))
        raise


async def track_price_history_service(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle price history tracking requests asynchronously.

    Args:
        params: Dictionary containing request parameters
               Required: 'action' - Action to perform (store, get_history)
               Other parameters depend on the action

    Returns:
        Dict containing standardized response with status, message, data and processing time
    """
    # Start timing for performance monitoring
    start_time = time.time()

    # Initialize default error response
    response = {
        "status": "error",
        "message": "An error occurred while processing the request",
        "data": [],
        "processing_time_ms": 0
    }

    try:
        # Check for required action parameter
        if not params or "action" not in params:
            response["message"] = "Missing required parameter: 'action'"
            response["processing_time_ms"] = int((time.time() - start_time) * 1000)
            return response

        # Get action parameter
        action = params["action"].lower()
        logger.info("Processing price history request with action: %s", action)

        # Create components with dependency injection
        repository, analyzer, notifier = await create_history_components()

        # Process based on action
        if action == "store":
            result = await handle_store_action(params, repository, analyzer, notifier)
            response.update(result)
        elif action == "get_history":
            result = await handle_get_history_action(params, repository, analyzer)
            response.update(result)
        else:
            response["message"] = f"Unsupported action: {action}"
            logger.warning("Unsupported action requested: %s", action)

    except Exception as error:
        # Handle errors
        error_message = f"Error processing request: {str(error)}"
        logger.error(error_message)
        response["message"] = error_message
    
    # Calculate processing time
    response["processing_time_ms"] = int((time.time() - start_time) * 1000)
    logger.info("Request processed in %d ms", response["processing_time_ms"])
    
    return response


async def handle_store_action(
    params: Dict[str, Any],
    repository: PriceHistoryRepository,
    analyzer: PriceHistoryAnalyzer,
    notifier: AlertNotifier,
) -> Dict[str, Any]:
    """
    Handle the 'store' action to store a price entry asynchronously.

    Args:
        params: Request parameters containing price_entry
        repository: Repository for storing price data
        analyzer: Analyzer for computing metrics
        notifier: Notifier for triggering alerts

    Returns:
        Dictionary with operation results
    """
    # Initialize response with defaults
    response = {
        "status": "error",
        "message": "Failed to store price entry",
        "data": {}
    }

    # Check for required price_entry
    if "price_entry" not in params:
        response["message"] = "Missing required parameter: 'price_entry'"
        return response

    price_entry = params["price_entry"]
    
    # Validate price entry
    if not isinstance(price_entry, dict):
        response["message"] = "Invalid price_entry: must be a dictionary"
        return response

    required_fields = ["model", "price", "currency", "source", "country"]
    missing_fields = [field for field in required_fields if field not in price_entry]
    
    if missing_fields:
        response["message"] = f"Invalid price_entry: missing required fields: {', '.join(missing_fields)}"
        return response

    # Add timestamp if not provided
    if "timestamp" not in price_entry:
        price_entry["timestamp"] = datetime.now().isoformat()

    # Check for alert rules
    alert_rules = params.get("alert_rules", [])
    if alert_rules and not isinstance(alert_rules, list):
        response["message"] = "Invalid alert_rules: must be a list"
        return response

    # Store the price entry
    try:
        # Store price entry
        entry_id = await repository.store_price(price_entry)
        
        # Get history for the model to compute metrics
        model = price_entry["model"]
        history = await repository.get_price_history(model)
        
        # Compute metrics
        metrics = await analyzer.compute_metrics(history)
        
        # Check for alerts if rules provided
        alerts_triggered = []
        if alert_rules:
            for rule_dict in alert_rules:
                try:
                    # Create rule object
                    rule = AlertRule(
                        type=rule_dict.get("type", "price_drop"),
                        threshold=rule_dict.get("threshold", 5.0),
                        model=model,
                        min_price_count=rule_dict.get("min_price_count", 2)
                    )
                    
                    # Check if rule matches
                    if analyzer.check_alert_rule(history, rule):
                        # Trigger alert
                        await notifier.send_alert(rule, price_entry, metrics)
                        alerts_triggered.append(rule_dict)
                except Exception as rule_error:
                    logger.error("Error processing alert rule: %s", str(rule_error))
        
        # Build successful response
        response["status"] = "success"
        response["message"] = "Price entry stored successfully"
        response["data"] = {
            "entry_id": entry_id,
            "metrics": metrics,
            "alerts_triggered": alerts_triggered
        }
        
        return response
        
    except Exception as store_error:
        logger.error("Error storing price entry: %s", str(store_error))
        response["message"] = f"Failed to store price entry: {str(store_error)}"
        return response


async def handle_get_history_action(
    params: Dict[str, Any],
    repository: PriceHistoryRepository,
    analyzer: PriceHistoryAnalyzer,
) -> Dict[str, Any]:
    """
    Handle the 'get_history' action to retrieve price history and metrics asynchronously.

    Args:
        params: Request parameters containing model and optional filters
        repository: Repository for retrieving price data
        analyzer: Analyzer for computing metrics

    Returns:
        Dictionary with price history and metrics
    """
    # Initialize response with defaults
    response = {
        "status": "error",
        "message": "Failed to retrieve price history",
        "data": {}
    }

    # Check for required model and country parameters
    if "model" not in params:
        response["message"] = "Missing required parameter: 'model'"
        return response
        
    if "country" not in params:
        response["message"] = "Missing required parameter: 'country'"
        return response

    model = params["model"]
    country = params["country"]
    
    # Get optional parameters with defaults
    days = params.get("days", 30)
    start_date = params.get("start_date")
    end_date = params.get("end_date")
    
    try:
        # Convert dates if provided
        start_datetime = None
        if start_date:
            start_datetime = datetime.fromisoformat(start_date)
        
        end_datetime = None
        if end_date:
            end_datetime = datetime.fromisoformat(end_date)
        
        # If no dates provided, use days parameter
        if not start_datetime and not end_datetime:
            end_datetime = datetime.now()
            start_datetime = end_datetime - timedelta(days=days)
        
        # Get price history with filters
        # Using the correct method name and ensuring it's properly awaited
        history = await repository.get_history_for_model(
            model=model,
            country=country,
            start_date=start_datetime,
            end_date=end_datetime
        )
        
        # Compute metrics
        metrics = await analyzer.compute_metrics(history)
        
        # Build successful response
        response["status"] = "success"
        response["message"] = f"Retrieved {len(history)} price points for {model}"
        response["data"] = {
            "history": history,
            "metrics": metrics,
            "filters": {
                "model": model,
                "country": country,
                "start_date": start_datetime.isoformat() if start_datetime else None,
                "end_date": end_datetime.isoformat() if end_datetime else None
            }
        }
        
        return response
        
    except Exception as fetch_error:
        logger.error("Error retrieving price history: %s", str(fetch_error))
        response["message"] = f"Failed to retrieve price history: {str(fetch_error)}"
        return response
