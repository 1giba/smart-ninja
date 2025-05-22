"""
Scraping Agent for retrieving raw price data using MCP services.

This agent is responsible for calling the MCP scrape_prices service directly
to obtain price data for a specific product model and country.
"""
import logging
import os
from typing import Any, Dict, List, Optional

from app.core.agents.base_agent import BaseAgent
from app.mcp.scrape_prices import scrape_prices_service

# Default timeout for MCP operations in seconds (configurable via environment)
DEFAULT_MCP_TIMEOUT_SECONDS = int(os.getenv("MCP_REQUEST_TIMEOUT", "30"))


class ScrapingAgent(BaseAgent):
    """
    Agent that retrieves raw price data using the MCP scrape_prices service.

    This agent calls the scrape_prices_service async module directly
    to collect price data for a specific product model and country.
    
    As part of the Model-Context-Protocol (MCP) architecture, this agent
    delegates the actual scraping operations to a dedicated service,
    focusing only on the communication and data handling aspects.
    This separation of concerns improves maintainability and allows
    independent scaling of scraping operations.
    """

    def __init__(self, mcp_timeout: Optional[int] = None):
        """
        Initialize the scraping agent with optional timeout configuration.

        Args:
            mcp_timeout: Timeout in seconds for MCP operations (for testing/overriding)
        """
        self._timeout = mcp_timeout or DEFAULT_MCP_TIMEOUT_SECONDS
        logging.info("ScrapingAgent initialized with timeout: %s seconds", self._timeout)

    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate that the input data contains required fields.
        
        Args:
            input_data: Dictionary to validate
            
        Raises:
            ValueError: If required fields are missing
        """
        if "model" not in input_data:
            raise ValueError("Input must include 'model' information")
        if "country" not in input_data:
            raise ValueError("Input must include 'country' information")
            
    async def execute(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Execute scraping operations by calling the MCP scrape_prices service.

        This method sends an HTTP request to the configured MCP endpoint to retrieve
        price data for the specified product model and country. The input data must
        include both 'model' and 'country' keys.

        Args:
            input_data: Dictionary containing 'model' and 'country' keys

        Returns:
            List of dictionaries containing normalized price data

        Raises:
            ValueError: If required input fields are missing
        """
        # Validate required inputs
        self._validate_input(input_data)

        model = input_data["model"]
        country = input_data["country"]

        logging.info(
            "Calling MCP scrape_prices service for model: %s, country: %s",
            model,
            country,
        )

        # Prepare request payload
        payload = {
            "model": model,
            "country": country.lower(),
            "timeout": self._timeout
        }
        
        try:
            # Call the MCP service directly as an async function
            result = await scrape_prices_service(payload)
            
            if result.get("status") != "success":
                logging.error(
                    "MCP service reported failure: %s",
                    result.get("message", "Unknown error")
                )
                return []
            
            # Extract the price data from the response
            price_data = result.get("data", [])
            logging.info(
                "Successfully retrieved %d price entries from MCP service",
                len(price_data)
            )
            return price_data

        except Exception as e:
            logging.error("Error while calling MCP scrape_prices service: %s", str(e))
            # In a production environment, we might want to report this error to a monitoring service
            return []
