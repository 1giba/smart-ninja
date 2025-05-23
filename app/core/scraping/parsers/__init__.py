"""
Site-specific parsers for e-commerce websites.

This module provides a collection of parsers for different e-commerce sites,
following SOLID principles and enabling more maintainable and adaptable scraping.
"""

from .base_parser import BaseEcommerceParser
from .parser_factory import ParserFactory

__all__ = ["BaseEcommerceParser", "ParserFactory"]
