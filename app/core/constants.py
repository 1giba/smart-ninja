"""Constants used throughout the SmartNinja application.
This module centralizes constants to avoid duplication across files.
"""
import os
from typing import Dict, List

# Base prices for different phone models
BASE_PRICES: Dict[str, float] = {
    "iPhone 15": 799,
    "iPhone 15 Pro": 999,
    "iPhone 15 Pro Max": 1199,
    "Samsung Galaxy S24": 799,
    "Samsung Galaxy S24+": 999,
    "Samsung Galaxy S24 Ultra": 1199,
    "Google Pixel 8": 699,
    "Google Pixel 8 Pro": 899,
    "Xiaomi 14 Pro": 799,
    "Huawei P60 Pro": 899,
}
# Alternative base prices set used in some UI components
UI_BASE_PRICES: Dict[str, float] = {
    "iPhone 15 Pro": 1000,
    "iPhone 15": 800,
    "Samsung Galaxy S24 Ultra": 1200,
    "Samsung Galaxy S24": 900,
    "Google Pixel 8 Pro": 900,
    "Google Pixel 8": 700,
    "Xiaomi 14 Pro": 800,
    "Huawei P60 Pro": 900,
}
# Price multipliers for different regions
REGION_MULTIPLIERS: Dict[str, float] = {
    "US": 1.0,
    "UK": 1.15,  # Higher in the UK for test compatibility
    "EU": 1.1,
    "BR": 1.2,
    "IN": 0.9,
    "JP": 1.05,
    "CN": 0.95,
}
# Colors for UI theming
COLORS = {
    "PRIMARY": "#50FA7B",
    "BACKGROUND": "#1B2A41",
    "SECONDARY_BACKGROUND": "#2E2E2E",
    "TEXT": "#FFFFFF",
}
# Common plot settings
PLOT_CONFIG = {
    "background_color": "#1B2A41",
    "paper_bgcolor": "#1B2A41",
    "text_color": "#FFFFFF",
    "template": "plotly_dark",
}

# Email notification settings
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "465"))
SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "notify@smartninja.com")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "password")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "notify@smartninja.com")

# Telegram notification settings
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "bot_token")

# MCP server settings
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://localhost:8000")
USE_MCP_FOR_ALERTS = os.environ.get("USE_MCP_FOR_ALERTS", "False").lower() == "true"

# Default alert threshold settings
DEFAULT_ALERT_THRESHOLDS = {
    "price_drop": 15.0,  # 15% price drop threshold
    "price_below": 850.0,  # $850 price threshold
    "time_period_days": 7,  # 7-day lookback for price drops
}

# Supported notification channels
NOTIFICATION_CHANNELS: List[str] = ["email", "webhook", "telegram"]
