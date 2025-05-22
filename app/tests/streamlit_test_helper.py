"""
Streamlit test helper module.
This module provides mocking utilities for Streamlit UI testing.
"""
import unittest
from unittest.mock import MagicMock, patch


class MockStreamlit:
    """Mock Streamlit object for testing"""

    def __init__(self):
        # Basic UI components
        self.markdown = MagicMock()
        self.text = MagicMock()
        self.header = MagicMock()
        self.subheader = MagicMock()
        self.title = MagicMock()
        self.caption = MagicMock()
        self.code = MagicMock()
        
        # Layout components
        self.expander = MagicMock()
        self.container = MagicMock()
        self.columns = MagicMock()
        self.tabs = MagicMock()
        self.sidebar = MagicMock()
        
        # Input components
        self.button = MagicMock()
        self.checkbox = MagicMock()
        self.radio = MagicMock()
        self.selectbox = MagicMock()
        self.multiselect = MagicMock()
        self.slider = MagicMock()
        self.text_input = MagicMock()
        self.text_area = MagicMock()
        self.number_input = MagicMock()
        self.date_input = MagicMock()
        self.time_input = MagicMock()
        self.file_uploader = MagicMock()
        
        # Display data components
        self.metric = MagicMock()
        self.dataframe = MagicMock()
        self.table = MagicMock()
        self.json = MagicMock()
        self.line_chart = MagicMock()
        self.bar_chart = MagicMock()
        self.area_chart = MagicMock()
        self.pyplot = MagicMock()
        
        # Status elements
        self.progress = MagicMock()
        self.spinner = MagicMock()
        self.balloons = MagicMock()
        self.snow = MagicMock()
        self.success = MagicMock()
        self.info = MagicMock()
        self.warning = MagicMock()
        self.error = MagicMock()
        self.exception = MagicMock()

        # Set up sidebar methods
        self.sidebar.container = MagicMock()
        self.sidebar.subheader = MagicMock()
        self.sidebar.title = MagicMock()
        self.sidebar.header = MagicMock()
        self.sidebar.markdown = MagicMock()
        self.sidebar.text = MagicMock()
        self.sidebar.metric = MagicMock()
        self.sidebar.progress = MagicMock()
        self.sidebar.button = MagicMock()
        self.sidebar.selectbox = MagicMock()

    def setup_context_managers(self):
        """Set up common context managers for Streamlit components."""
        mock_context = MagicMock()
        
        # Setup container-like components that need context managers
        for component in [self.expander, self.container, self.sidebar.container, self.spinner]:
            component.return_value.__enter__ = MagicMock(return_value=mock_context)
            component.return_value.__exit__ = MagicMock(return_value=None)
        
        # Make columns return a list of mocked contexts
        def mock_columns(*args, **kwargs):
            return [mock_context for _ in range(args[0] if args else kwargs.get('spec', 1))]
        
        self.columns.side_effect = mock_columns
        self.sidebar.columns.side_effect = mock_columns

        # Add all the common methods to the mock context
        mock_context.markdown = MagicMock()
        mock_context.text = MagicMock()
        mock_context.header = MagicMock()
        mock_context.subheader = MagicMock()
        mock_context.metric = MagicMock()
        mock_context.dataframe = MagicMock()
        mock_context.success = MagicMock()
        mock_context.info = MagicMock()
        mock_context.warning = MagicMock()
        mock_context.error = MagicMock()
        mock_context.button = MagicMock()
        mock_context.selectbox = MagicMock()

        return mock_context


def patch_streamlit(target_module):
    """Create a patch decorator that replaces streamlit with mock in the target module"""
    def decorator(test_func):
        @patch(f"{target_module}.st")
        def wrapper(self, mock_st, *args, **kwargs):
            # Configure the mock streamlit
            mock_streamlit = MockStreamlit()
            mock_context = mock_streamlit.setup_context_managers()
            
            # Transfer all attributes from our mock to the patch mock
            for attr_name in dir(mock_streamlit):
                if not attr_name.startswith('_'):
                    setattr(mock_st, attr_name, getattr(mock_streamlit, attr_name))
            
            # Add the mock_context to the test arguments
            return test_func(self, mock_st, mock_context, *args, **kwargs)
        return wrapper
    return decorator


def reset_mock(mock):
    """Reset all the Streamlit mock calls."""
    for name in dir(mock):
        if not name.startswith('_'):
            attr = getattr(mock, name)
            if hasattr(attr, 'reset_mock'):
                attr.reset_mock()
        
        # Reset column mocks
        cols = mock.columns.return_value
        for col in cols:
            col.reset_mock()
            col.__exit__.reset_mock()
