"""
Base parser interface for e-commerce websites.

This module defines the base parser interface that all site-specific parsers
must implement, following the Interface Segregation Principle from SOLID.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseEcommerceParser(ABC):
    """Base parser with common functionality for all e-commerce sites."""
    
    @abstractmethod
    async def parse(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content and extract product data.
        
        Args:
            html_content: HTML content to parse
            url: Source URL for reference
            
        Returns:
            List of dictionaries containing product data
        """
        raise NotImplementedError("Subclasses must implement parse method")
    
    async def can_parse(self, url: str) -> bool:
        """
        Determine if this parser can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if this parser can handle the URL, False otherwise
        """
        return False
