"""
Mock Streamlit module for testing UI components.
This module replaces the actual streamlit import in tests.
"""
from unittest.mock import MagicMock

# Create a mock class for all streamlit components
class MockStreamlit:
    def __init__(self):
        # Text elements
        self.markdown = MagicMock()
        self.text = MagicMock()
        self.code = MagicMock()
        self.header = MagicMock()
        self.subheader = MagicMock()
        self.title = MagicMock()
        
        # Input widgets
        self.button = MagicMock()
        self.checkbox = MagicMock()
        self.slider = MagicMock()
        self.selectbox = MagicMock()
        self.multiselect = MagicMock()
        self.text_input = MagicMock()
        self.text_area = MagicMock()
        self.number_input = MagicMock()
        
        # Data display elements
        self.dataframe = MagicMock()
        self.table = MagicMock()
        self.json = MagicMock()
        self.metric = MagicMock()
        
        # Charts
        self.line_chart = MagicMock()
        self.area_chart = MagicMock()
        self.bar_chart = MagicMock()
        self.pyplot = MagicMock()
        
        # Layout elements
        self.sidebar = MagicMock()
        self.columns = MagicMock()
        self.container = MagicMock()
        self.expander = MagicMock()
        self.tabs = MagicMock()
        
        # Status elements
        self.success = MagicMock()
        self.info = MagicMock()
        self.warning = MagicMock()
        self.error = MagicMock()
        self.exception = MagicMock()
        self.progress = MagicMock()
        self.spinner = MagicMock()
        
        # Session state
        self.session_state = {}
        
        # Set up context managers
        self._setup_context_managers()
        
        # Set up nested attributes for sidebar
        self.sidebar.markdown = MagicMock()
        self.sidebar.text = MagicMock()
        self.sidebar.header = MagicMock()
        self.sidebar.subheader = MagicMock()
        self.sidebar.container = MagicMock()
        self.sidebar.expander = MagicMock()
        self.sidebar.selectbox = MagicMock()
        self.sidebar.button = MagicMock()
        
        # Set up context manager for sidebar components
        self._setup_sidebar_context_managers()
    
    def _setup_context_managers(self):
        """Set up all context managers for components that support with statements"""
        # Create a mock context for all container-like elements
        mock_context = MagicMock()
        
        # Add methods to the context
        mock_context.markdown = MagicMock()
        mock_context.text = MagicMock()
        mock_context.header = MagicMock()
        mock_context.subheader = MagicMock()
        mock_context.dataframe = MagicMock()
        mock_context.json = MagicMock()
        mock_context.metric = MagicMock()
        mock_context.success = MagicMock()
        mock_context.info = MagicMock()
        mock_context.warning = MagicMock()
        mock_context.error = MagicMock()
        
        # Set up container context manager
        self.container.return_value.__enter__ = MagicMock(return_value=mock_context)
        self.container.return_value.__exit__ = MagicMock(return_value=None)
        
        # Set up expander context manager
        self.expander.return_value.__enter__ = MagicMock(return_value=mock_context)
        self.expander.return_value.__exit__ = MagicMock(return_value=None)
        
        # Set up spinner context manager
        self.spinner.return_value.__enter__ = MagicMock(return_value=mock_context)
        self.spinner.return_value.__exit__ = MagicMock(return_value=None)
        
        # Make columns return a list of mock contexts
        columns_list = [mock_context for _ in range(3)]
        self.columns.return_value = columns_list
    
    def _setup_sidebar_context_managers(self):
        """Set up context managers for sidebar components"""
        mock_sidebar_context = MagicMock()
        
        # Add methods to the sidebar context
        mock_sidebar_context.markdown = MagicMock()
        mock_sidebar_context.text = MagicMock()
        mock_sidebar_context.header = MagicMock()
        mock_sidebar_context.subheader = MagicMock()
        
        # Set up sidebar container context manager
        self.sidebar.container.return_value.__enter__ = MagicMock(return_value=mock_sidebar_context)
        self.sidebar.container.return_value.__exit__ = MagicMock(return_value=None)
        
        # Set up sidebar expander context manager
        self.sidebar.expander.return_value.__enter__ = MagicMock(return_value=mock_sidebar_context)
        self.sidebar.expander.return_value.__exit__ = MagicMock(return_value=None)

# Create a global instance to be imported
st = MockStreamlit()
