"""
Core functionality for price history tracking and analysis.

This module provides components for storing, retrieving, analyzing price history data
and sending alerts when specific conditions are met. All components support async
operations for improved performance and scalability.
"""
import asyncio
import logging
import statistics
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PriceHistoryRepository(ABC):
    """Interface for price history data storage and retrieval with async support."""

    @abstractmethod
    async def store_price_entry(self, price_entry: Dict[str, Any]) -> str:
        """
        Store a price entry in the repository asynchronously.

        Args:
            price_entry: Dictionary containing price data with at least model, price,
                       currency, source, country, and timestamp.

        Returns:
            Unique identifier for the stored entry.
        """
        pass

    @abstractmethod
    async def get_history_for_model(
        self, model: str, country: str, days: int = 30, cursor: Optional[str] = None, limit: int = 100,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve price history for a model in a specific country asynchronously.

        Args:
            model: The model to retrieve history for.
            country: The country code.
            days: Number of days of history to retrieve (default: 30).
            cursor: Optional pagination cursor.
            limit: Maximum number of entries to return (default: 100).
            start_date: Optional start date for filtering entries.
            end_date: Optional end date for filtering entries.

        Returns:
            List of price entries sorted by timestamp (newest first).
        """
        pass

    # Legacy method for backward compatibility
    def get_price_history(
        self, model: str, country: str, days: int = 30, start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Legacy synchronous method for retrieving price history.
        
        This method is maintained for backward compatibility and delegates to the
        asynchronous implementation using asyncio.run.

        Args:
            model: The model to retrieve history for.
            country: The country code.
            days: Number of days of history to retrieve (default: 30).
            start_date: Optional start date for filtering entries.
            end_date: Optional end date for filtering entries.

        Returns:
            List of price entries sorted by timestamp (newest first).
        """
        logger.warning("Using deprecated synchronous get_price_history method")
        return asyncio.run(self.get_history_for_model(
            model, country, days, start_date=start_date, end_date=end_date
        ))


class SQLitePriceHistoryRepository(PriceHistoryRepository):
    """Implementation of PriceHistoryRepository using SQLite with async support."""

    def __init__(self, db_path: str = "price_history.db"):
        """
        Initialize the SQLite repository.

        Args:
            db_path: Path to the SQLite database file.
        """
        import sqlite3
        import threading
        from pathlib import Path

        self.db_path = db_path
        self.sqlite3 = sqlite3
        # Thread-local storage for database connections
        self.local = threading.local()

        # Ensure the directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Create tables on initialization
        with self._get_connection() as conn:
            self._create_tables(conn)
            
        logger.info(f"Initialized SQLite repository at {db_path}")

    def __del__(self):
        """Ensure database connection is closed when object is garbage collected."""
        # No need to explicitly close connections as they are managed by _get_connection context

    def _get_connection(self):
        """Get a thread-local database connection using context manager."""
        import contextlib

        @contextlib.contextmanager
        def connect():
            # Create a new connection if it doesn't exist for this thread
            if not hasattr(self.local, 'conn'):
                self.local.conn = self.sqlite3.connect(self.db_path)
                # Enable foreign keys
                self.local.conn.execute('PRAGMA foreign_keys = ON')

            try:
                yield self.local.conn
            except Exception as e:
                self.local.conn.rollback()
                logger.error(f"SQLite operation failed: {e}")
                raise
            finally:
                # Don't close the connection - keep it for thread reuse
                pass

        return connect()

    def _create_tables(self, conn):
        """Create the necessary tables if they don't exist."""
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_history (
                id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT,
                source TEXT,
                country TEXT,
                url TEXT,
                timestamp TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_model_country ON price_history (model, country)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_timestamp ON price_history (timestamp)
            """
        )
        conn.commit()
        cursor.close()

    async def store_price_entry(self, price_entry: Dict[str, Any]) -> str:
        """
        Store a price entry in the SQLite database asynchronously.

        This method runs SQLite operations in a thread pool to avoid blocking.

        Args:
            price_entry: Dictionary containing price data.

        Returns:
            Unique identifier for the stored entry.
        """
        # Validate required fields
        required_fields = ["model", "price", "timestamp"]
        for field in required_fields:
            if field not in price_entry:
                raise ValueError(f"Missing required field: {field}")

        # Run database operations in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._store_price_entry_sync, price_entry
        )

    def _store_price_entry_sync(self, price_entry: Dict[str, Any]) -> str:
        """Synchronous implementation of store_price_entry for thread pool execution."""
        import uuid

        # Generate a unique ID for the entry
        entry_id = str(uuid.uuid4())

        # Extract fields with defaults for optional values
        model = price_entry["model"]
        price = price_entry["price"]
        currency = price_entry.get("currency", "USD")
        source = price_entry.get("source", "unknown")
        country = price_entry.get("country", "global")
        url = price_entry.get("url", "")
        timestamp = price_entry["timestamp"]

        # Normalize timestamp if it's a datetime object
        if isinstance(timestamp, datetime):
            timestamp = timestamp.isoformat()

        # Insert into database using thread-local connection
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO price_history (id, model, price, currency, source, country, url, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (entry_id, model, price, currency, source, country, url, timestamp),
            )
            conn.commit()
            cursor.close()
            
            return entry_id

        logger.info(
            f"Stored price entry for {model} in {country}: {currency} {price} (ID: {entry_id})"
        )
        return entry_id

    async def get_history_for_model(
        self, model: str, country: str, days: int = 30, cursor: Optional[str] = None, limit: int = 100,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve price history from the SQLite database asynchronously.

        This method runs SQLite operations in a thread pool to avoid blocking.

        Args:
            model: The model to retrieve history for.
            country: The country code.
            days: Number of days of history to retrieve (default: 30).
            cursor: Optional pagination cursor (offset).
            limit: Maximum number of entries to return (default: 100).
            start_date: Optional start date for filtering entries.
            end_date: Optional end date for filtering entries.

        Returns:
            List of price entries sorted by timestamp (newest first).
        """
        # Run database operations in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._get_history_for_model_sync, model, country, days, cursor, limit, start_date, end_date
        )

    def _get_history_for_model_sync(
        self, model: str, country: str, days: int = 30, cursor: Optional[str] = None, limit: int = 100,
        start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Synchronous implementation of get_history_for_model for thread pool execution."""
        # Parse cursor as offset if provided
        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                logger.warning(f"Invalid cursor format: {cursor}, using offset 0")
                
        # Prepare query parameters
        query_params = [model, country]
        
        # Base query
        base_query = """
            SELECT id, model, price, currency, source, country, url, timestamp
            FROM price_history
            WHERE model = ? AND country = ?
        """
        
        # Handle date filtering
        date_conditions = []
        
        # If explicit dates are provided, use them instead of days
        if start_date:
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date)
            date_conditions.append("timestamp >= ?")
            query_params.append(start_date.isoformat())
            
        if end_date:
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date)
            date_conditions.append("timestamp <= ?")
            query_params.append(end_date.isoformat())
            
        # If no explicit dates, use days parameter
        if not date_conditions:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            date_conditions.append("timestamp >= ?")
            query_params.append(cutoff_date)
            
        # Add date conditions to query
        if date_conditions:
            base_query += " AND " + " AND ".join(date_conditions)
            
        # Add sorting and limits
        base_query += """
            ORDER BY timestamp DESC
            LIMIT ? OFFSET ?
        """
        query_params.extend([limit, offset])
        
        # Query the database using thread-local connection
        result = []
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(base_query, tuple(query_params))
            
            # Convert rows to dictionaries
            for row in cursor.fetchall():
                result.append({
                    "id": row[0],
                    "model": row[1],
                    "price": row[2],
                    "currency": row[3],
                    "source": row[4],
                    "country": row[5],
                    "url": row[6],
                    "timestamp": row[7],
                })
            
            cursor.close()
        return result


class AlertRule:
    """Represents a price alert rule for triggering notifications."""

    def __init__(
        self,
        enabled: bool = False,
        threshold_percent: float = 10.0,
        compared_to: str = "average",
    ):
        """
        Initialize an alert rule.

        Args:
            enabled: Whether the alert is enabled.
            threshold_percent: Percentage threshold for triggering the alert.
            compared_to: What to compare the current price against ('average',
                        'lowest', 'highest', 'rolling_7d', 'rolling_30d').
        """
        self.enabled = enabled
        self.threshold_percent = threshold_percent
        self.compared_to = compared_to

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlertRule":
        """
        Create an AlertRule from a dictionary.

        Args:
            data: Dictionary with alert rule parameters.

        Returns:
            AlertRule instance.
        """
        return cls(
            enabled=data.get("enabled", False),
            threshold_percent=data.get("threshold_percent", 10.0),
            compared_to=data.get("compared_to", "average"),
        )


class AlertNotifier(ABC):
    """Interface for sending price alerts with async support."""

    @abstractmethod
    async def check_alert_rules(
        self, 
        model: str, 
        country: str,
        price_entry: Dict[str, Any], 
        metrics: Dict[str, Any],
        alert_rules: List[AlertRule]
    ) -> List[Dict[str, Any]]:
        """
        Check if any alert rules are triggered by the current price data.

        Args:
            model: The model to check alerts for.
            country: The country to check alerts for.
            price_entry: The current price entry.
            metrics: Price metrics including trends and comparisons.
            alert_rules: List of alert rules to check.

        Returns:
            List of triggered alerts with details.
        """
        pass

    @abstractmethod
    async def send_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Send triggered price alerts asynchronously.

        Args:
            alerts: List of triggered alerts with details.

        Returns:
            True if all alerts were sent successfully, False otherwise.
        """
        pass


class ConsoleAlertNotifier(AlertNotifier):
    """Implementation of AlertNotifier that prints alerts to the console."""

    async def check_alert_rules(
        self, 
        model: str, 
        country: str,
        price_entry: Dict[str, Any], 
        metrics: Dict[str, Any],
        alert_rules: List[AlertRule]
    ) -> List[Dict[str, Any]]:
        """
        Check if any alert rules are triggered for the console notifier.

        Args:
            model: The model to check alerts for.
            country: The country to check alerts for.
            price_entry: The current price entry.
            metrics: Price metrics including trends and comparisons.
            alert_rules: List of alert rules to check.

        Returns:
            List of triggered alerts with details.
        """
        triggered_alerts = []
        current_price = price_entry.get("price", 0)
        
        for rule in alert_rules:
            if not rule.enabled:
                continue
                
            # Skip if the rule doesn't apply to this model/country
            rule_model = getattr(rule, "model", model)
            rule_country = getattr(rule, "country", country)
            if rule_model != model or (rule_country != country and rule_country != "global"):
                continue
            
            # Get the comparison value based on the rule type
            comparison_value = None
            if rule.compared_to == "average":
                comparison_value = metrics.get("average_price", 0)
            elif rule.compared_to == "lowest":
                comparison_value = metrics.get("min_price", 0)
            elif rule.compared_to == "highest":
                comparison_value = metrics.get("max_price", 0)
            elif rule.compared_to == "rolling_7d":
                comparison_value = metrics.get("rolling_7d_average", 0)
            elif rule.compared_to == "rolling_30d":
                comparison_value = metrics.get("rolling_30d_average", 0)
            
            # Skip if no valid comparison value
            if not comparison_value:
                continue
                
            # Calculate the percentage difference
            percent_diff = ((comparison_value - current_price) / comparison_value) * 100
            
            # Check if the difference exceeds the threshold
            if abs(percent_diff) >= rule.threshold_percent:
                triggered_alerts.append({
                    "model": model,
                    "country": country,
                    "price": current_price,
                    "comparison_value": comparison_value,
                    "compared_to": rule.compared_to,
                    "percent_diff": percent_diff,
                    "threshold": rule.threshold_percent,
                    "timestamp": datetime.now().isoformat(),
                    "rule": rule.__dict__
                })
        
        return triggered_alerts

    async def send_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Send price alerts to the console asynchronously.

        Args:
            alerts: List of triggered alerts with details.

        Returns:
            True if all alerts were logged, False otherwise.
        """
        try:
            for alert in alerts:
                model = alert.get("model", "Unknown model")
                price = alert.get("price", 0)
                compared_to = alert.get("compared_to", "unknown")
                percent_diff = alert.get("percent_diff", 0)
                
                message = (
                    f"🔔 PRICE ALERT: {model} is now ${price:.2f}, "
                    f"which is {abs(percent_diff):.1f}% {'lower' if percent_diff > 0 else 'higher'} "
                    f"than the {compared_to} price."
                )
                
                logger.info(message)
                print(message)
                
            return True
        except Exception as e:
            logger.error(f"Error sending console alerts: {str(e)}")
            return False


class WebhookAlertNotifier(AlertNotifier):
    """Implementation of AlertNotifier that sends alerts to a webhook."""

    def __init__(self, webhook_url: str):
        """
        Initialize the webhook notifier.

        Args:
            webhook_url: URL of the webhook to send alerts to.
        """
        import aiohttp

        self.webhook_url = webhook_url
        self.session = aiohttp.ClientSession()
        logger.info(f"Initialized webhook notifier with URL: {webhook_url}")

    async def check_alert_rules(
        self, 
        model: str, 
        country: str,
        price_entry: Dict[str, Any], 
        metrics: Dict[str, Any],
        alert_rules: List[AlertRule]
    ) -> List[Dict[str, Any]]:
        """
        Check if any alert rules are triggered for the webhook notifier.

        Implementation matches ConsoleAlertNotifier for consistency.

        Args:
            model: The model to check alerts for.
            country: The country to check alerts for.
            price_entry: The current price entry.
            metrics: Price metrics including trends and comparisons.
            alert_rules: List of alert rules to check.

        Returns:
            List of triggered alerts with details.
        """
        triggered_alerts = []
        current_price = price_entry.get("price", 0)
        
        for rule in alert_rules:
            if not rule.enabled:
                continue
                
            # Skip if the rule doesn't apply to this model/country
            rule_model = getattr(rule, "model", model)
            rule_country = getattr(rule, "country", country)
            if rule_model != model or (rule_country != country and rule_country != "global"):
                continue
            
            # Get the comparison value based on the rule type
            comparison_value = None
            if rule.compared_to == "average":
                comparison_value = metrics.get("average_price", 0)
            elif rule.compared_to == "lowest":
                comparison_value = metrics.get("min_price", 0)
            elif rule.compared_to == "highest":
                comparison_value = metrics.get("max_price", 0)
            elif rule.compared_to == "rolling_7d":
                comparison_value = metrics.get("rolling_7d_average", 0)
            elif rule.compared_to == "rolling_30d":
                comparison_value = metrics.get("rolling_30d_average", 0)
            
            # Skip if no valid comparison value
            if not comparison_value:
                continue
                
            # Calculate the percentage difference
            percent_diff = ((comparison_value - current_price) / comparison_value) * 100
            
            # Check if the difference exceeds the threshold
            if abs(percent_diff) >= rule.threshold_percent:
                triggered_alerts.append({
                    "model": model,
                    "country": country,
                    "price": current_price,
                    "comparison_value": comparison_value,
                    "compared_to": rule.compared_to,
                    "percent_diff": percent_diff,
                    "threshold": rule.threshold_percent,
                    "timestamp": datetime.now().isoformat(),
                    "rule": rule.__dict__
                })
        
        return triggered_alerts

    async def send_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """
        Send price alerts to the webhook asynchronously.

        Args:
            alerts: List of triggered alerts with details.

        Returns:
            True if all alerts were sent successfully, False otherwise.
        """
        import json
        
        try:
            # Send each alert to the webhook
            for alert in alerts:
                model = alert.get("model", "Unknown model")
                price = alert.get("price", 0)
                compared_to = alert.get("compared_to", "unknown")
                percent_diff = alert.get("percent_diff", 0)
                
                # Prepare the webhook payload
                payload = {
                    "type": "price_alert",
                    "model": model,
                    "price": price,
                    "compared_to": compared_to,
                    "percent_diff": percent_diff,
                    "direction": "lower" if percent_diff > 0 else "higher",
                    "timestamp": datetime.now().isoformat(),
                    "details": alert
                }
                
                # Post to the webhook asynchronously
                async with self.session.post(
                    self.webhook_url, 
                    json=payload, 
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status >= 400:
                        logger.warning(
                            f"Webhook alert failed with status {response.status}: {await response.text()}"
                        )
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error sending webhook alerts: {str(e)}")
            return False


class PriceHistoryAnalyzer:
    """Analyzes price history data and computes metrics."""

    async def compute_metrics(self, price_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Backward compatibility method that delegates to calculate_metrics.
        This implementation properly handles both awaited and non-awaited calls to avoid warnings.
        """
        import asyncio
        import inspect
        
        logger.info("Using deprecated compute_metrics method, use calculate_metrics instead")
        
        # Get the current coroutine or create a new event loop if not in a coroutine
        try:
            # If this method is awaited, return the awaitable result
            if inspect.iscoroutinefunction(self.calculate_metrics):
                return await self.calculate_metrics(price_entries)
            else:
                # If calculate_metrics is not a coroutine function, just call it directly
                return self.calculate_metrics(price_entries)
        except RuntimeError:
            # If we're not in a coroutine context, run in a new event loop
            logger.warning("compute_metrics called without await - this is deprecated")
            return asyncio.run(self.calculate_metrics(price_entries))

    async def calculate_metrics(self, price_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute metrics from price history asynchronously.

        Args:
            price_entries: List of price entries.

        Returns:
            Dictionary containing computed metrics.
        """
        # Run computation in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self._compute_metrics_sync, price_entries
        )

    def _compute_metrics_sync(self, price_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronous implementation of compute_metrics for thread pool execution."""
        if not price_entries:
            return {
                "count": 0,
                "min_price": None,
                "max_price": None,
                "average_price": None,
                "trend": "unknown",
            }

        # Extract prices and sort entries by timestamp
        try:
            prices = [entry["price"] for entry in price_entries if "price" in entry]
            # Sort entries by timestamp (newest first)
            sorted_entries = sorted(
                [e for e in price_entries if "timestamp" in e],
                key=lambda x: x["timestamp"],
                reverse=True,
            )
        except (KeyError, TypeError) as e:
            logger.error(f"Error processing price entries: {str(e)}")
            return {
                "count": len(price_entries),
                "error": f"Error processing price entries: {str(e)}",
                "trend": "unknown",
            }

        # Compute basic statistics
        min_price = min(prices) if prices else None
        max_price = max(prices) if prices else None
        avg_price = statistics.mean(prices) if prices else None

        # Compute rolling averages (last 7 and 30 days)
        now = datetime.now()
        days7_cutoff = (now - timedelta(days=7)).isoformat()
        days30_cutoff = (now - timedelta(days=30)).isoformat()

        prices_7d = [
            entry["price"]
            for entry in price_entries
            if "timestamp" in entry and entry["timestamp"] >= days7_cutoff
        ]
        prices_30d = [
            entry["price"]
            for entry in price_entries
            if "timestamp" in entry and entry["timestamp"] >= days30_cutoff
        ]

        rolling_7d_avg = statistics.mean(prices_7d) if prices_7d else None
        rolling_30d_avg = statistics.mean(prices_30d) if prices_30d else None

        # Determine price trend
        trend = "stable"
        if len(sorted_entries) >= 2:
            newest_price = sorted_entries[0]["price"]
            oldest_price = sorted_entries[-1]["price"]
            change_pct = ((newest_price - oldest_price) / oldest_price) * 100

            if change_pct < -5:
                trend = "decreasing"
            elif change_pct > 5:
                trend = "increasing"

        return {
            "count": len(price_entries),
            "min_price": min_price,
            "max_price": max_price,
            "average_price": avg_price,
            "rolling_7d_average": rolling_7d_avg,
            "rolling_30d_average": rolling_30d_avg,
            "trend": trend,
            "price_range": max_price - min_price if (max_price and min_price) else None,
        }
