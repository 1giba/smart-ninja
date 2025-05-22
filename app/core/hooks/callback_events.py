"""
Callback events for the hooks system.

This module defines the standard events that can trigger callbacks
in the agent execution flow.
"""
from enum import Enum, auto


class AgentLifecycleEvent(Enum):
    """
    Enumeration of supported lifecycle events in the agent execution flow.

    These events represent different points in the agent's lifecycle where callbacks can be triggered.
    Using these predefined events ensures consistency across the system.
    """

    # General execution events
    BEFORE_EXECUTION = auto()
    AFTER_EXECUTION = auto()
    ON_ERROR = auto()

    # Scraping related events
    BEFORE_SCRAPING = auto()
    AFTER_SCRAPING = auto()

    # Analysis related events
    BEFORE_ANALYSIS = auto()
    AFTER_ANALYSIS = auto()

    # Prompt related events
    BEFORE_PROMPT = auto()
    AFTER_PROMPT = auto()

    # AI interaction events
    BEFORE_AI_REQUEST = auto()
    AFTER_AI_REQUEST = auto()

    # Recommendation events
    BEFORE_RECOMMENDATION = auto()
    AFTER_RECOMMENDATION = auto()


# For backward compatibility with existing code
# This alias allows existing code to continue working while we transition to the new name
CallbackEvent = AgentLifecycleEvent
