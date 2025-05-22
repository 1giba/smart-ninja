"""
Async Bridge Adapter for Streamlit UI.

This module provides an adapter that allows the synchronous Streamlit UI to 
interact with asynchronous agents and services by providing a clean interface
that handles the async/sync conversion seamlessly.
"""
import asyncio
import logging
from typing import Any, Callable, Dict, List, Optional, TypeVar, cast

from app.core.agents.analysis_agent import AnalysisAgent
from app.core.agents.recommendation_agent import RecommendationAgent
from app.core.agents.scraping_agent import ScrapingAgent
from app.core.interfaces.tool_set import ISmartNinjaToolSet

# Type variable for generic function return types
T = TypeVar('T')

class AsyncBridge:
    """
    Bridge adapter that converts asynchronous agent calls to synchronous calls.
    
    This class follows the Adapter pattern to provide a consistent interface
    for Streamlit to call asynchronous functions in a synchronous context,
    without blocking the UI thread unnecessarily.
    """
    
    @staticmethod
    def run_async(async_func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run an asynchronous function in a synchronous context.
        
        Args:
            async_func: The asynchronous function to run
            *args: Positional arguments to pass to the async function
            **kwargs: Keyword arguments to pass to the async function
            
        Returns:
            The result of the asynchronous function
            
        Raises:
            Exception: Any exception raised by the async function
        """
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()


class ScrapingAgentAdapter:
    """
    Adapter for the ScrapingAgent that provides a synchronous interface.
    """
    
    def __init__(self, mcp_url: Optional[str] = None):
        """
        Initialize the adapter with a ScrapingAgent.
        
        Args:
            mcp_url: Optional URL for the MCP service
        """
        self._agent = ScrapingAgent(mcp_url)
        self._logger = logging.getLogger(__name__)
    
    def execute(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute the scraping operation synchronously.
        
        Args:
            input_data: Dictionary containing 'model' and 'country' keys
            
        Returns:
            List of dictionaries containing normalized price data
            
        Raises:
            ValueError: If required input fields are missing
        """
        self._logger.info(f"Executing scraping with input: {input_data}")
        return AsyncBridge.run_async(self._agent.execute, input_data)


class AnalysisAgentAdapter:
    """
    Adapter for the AnalysisAgent that provides a synchronous interface.
    """
    
    def __init__(self, tool_set: Optional[ISmartNinjaToolSet] = None):
        """
        Initialize the adapter with an AnalysisAgent.
        
        Args:
            tool_set: Optional tool set for the agent
        """
        self._agent = AnalysisAgent(tool_set)
        self._logger = logging.getLogger(__name__)
    
    def analyze_prices(self, price_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze price data synchronously.
        
        Args:
            price_data: List of dictionaries containing price data
            
        Returns:
            Dictionary with analysis results
        """
        self._logger.info(f"Analyzing prices for {len(price_data)} items")
        return AsyncBridge.run_async(self._agent.analyze_prices, price_data)
    
    def process_analysis_request(self, model: str, country: str) -> str:
        """
        Process a complete analysis request synchronously.
        
        Args:
            model: The product model to analyze
            country: The country to analyze prices for
            
        Returns:
            Complete analysis result as a string
        """
        self._logger.info(f"Processing analysis request for {model} in {country}")
        return AsyncBridge.run_async(self._agent.process_analysis_request, model, country)


class RecommendationAgentAdapter:
    """
    Adapter for the RecommendationAgent that provides a synchronous interface.
    """
    
    def __init__(self, tool_set: Optional[ISmartNinjaToolSet] = None):
        """
        Initialize the adapter with a RecommendationAgent.
        
        Args:
            tool_set: Optional tool set for the agent
        """
        self._agent = RecommendationAgent(tool_set)
        self._logger = logging.getLogger(__name__)
    
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendations synchronously.
        
        Args:
            input_data: Dictionary containing analysis results and price data
            
        Returns:
            Dictionary with best offer and recommendation text
            
        Raises:
            ValueError: If price_data is missing from input_data
        """
        self._logger.info(f"Generating recommendations with input: {input_data.keys()}")
        return AsyncBridge.run_async(self._agent.execute, input_data)
