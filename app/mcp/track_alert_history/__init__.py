"""
Alert History Tracking MCP Service.

This module exposes asynchronous alert history tracking functionality as a direct importable module.
"""

from .service import track_alert_history_service, handle_alert_history_request, save_alert_history

__all__ = ["track_alert_history_service", "handle_alert_history_request", "save_alert_history"]

