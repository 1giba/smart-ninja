"""
Parser factory for e-commerce websites.

This module implements a factory for creating appropriate site-specific parsers
based on the URL, following the Factory pattern and Dependency Inversion Principle.
"""

import logging
from typing import Dict, Type

from .base_parser import BaseEcommerceParser

# Import site-specific parsers
from .amazon_parser import AmazonParser
from .magazineluiza_parser import MagazineLuizaParser
from .americanas_parser import AmericanasParser
from .kabum_parser import KabumParser
from .submarino_parser import SubmarinoParser

# Configure logging
logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for creating appropriate parsers based on the URL."""
    
    # Registry of parsers
    _parsers: Dict[str, Type[BaseEcommerceParser]] = {
        "amazon": AmazonParser,
        "magazineluiza": MagazineLuizaParser,
        "americanas": AmericanasParser,
        "kabum": KabumParser,
        "submarino": SubmarinoParser,
    }
    
    @classmethod
    async def create_parser(cls, url: str) -> BaseEcommerceParser:
        """
        Create and return the appropriate parser for the given URL.
        
        Args:
            url: URL to create parser for
            
        Returns:
            Instance of an appropriate parser for the URL
        """
        # Check each parser's domain pattern
        for domain, parser_class in cls._parsers.items():
            if domain in url.lower():
                logger.info(f"Using {parser_class.__name__} for {url}")
                return parser_class()
        
        # If no specific parser found, use a generic one
        from .generic_parser import GenericEcommerceParser
        logger.info(f"Using GenericEcommerceParser for {url}")
        return GenericEcommerceParser()
    
    @classmethod
    def register_parser(cls, domain: str, parser_class: Type[BaseEcommerceParser]) -> None:
        """
        Register a new parser for a specific domain.
        
        Args:
            domain: Domain identifier (e.g., 'amazon')
            parser_class: Parser class to register
        """
        cls._parsers[domain] = parser_class
        logger.info(f"Registered {parser_class.__name__} for domain '{domain}'")
