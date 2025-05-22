"""
Configuration file for pytest.

This file contains configuration and fixtures for pytest,
specifically for supporting asynchronous tests.
"""
import asyncio

import pytest

# Configure pytest to automatically handle coroutines in test functions
pytest_plugins = ["pytest_asyncio"]


# Set asyncio as the default for all tests in this directory
def pytest_collection_modifyitems(config, items):
    """Automatically mark async tests with pytest.mark.asyncio"""
    for item in items:
        if asyncio.iscoroutinefunction(item.function):
            item.add_marker(pytest.mark.asyncio)


# Configure pytest-asyncio to use strict mode
pytest.mark_asyncio = pytest.mark.asyncio
