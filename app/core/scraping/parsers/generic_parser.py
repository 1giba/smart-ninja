"""
Generic parser for e-commerce websites.

This module provides a fallback parser that attempts to extract product information
from any e-commerce site using general patterns and heuristics.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup

from .base_parser import BaseEcommerceParser

# Configure logging
logger = logging.getLogger(__name__)


class GenericEcommerceParser(BaseEcommerceParser):
    """Generic parser for any e-commerce site."""
    
    async def parse(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content and extract product data using generic patterns.
        
        Args:
            html_content: HTML content to parse
            url: Source URL for reference
            
        Returns:
            List of dictionaries containing product data
        """
        if not html_content:
            logger.warning(f"Empty HTML content for {url}")
            return []
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            results = []
            
            # Try to find product containers using common class patterns
            product_containers = soup.select('.product-item, .product-card, .product-container, .product')
            
            if product_containers:
                logger.info(f"Found {len(product_containers)} product containers")
                
                # Extract from containers
                for container in product_containers:
                    product = self._extract_from_container(container, url)
                    if product:
                        results.append(product)
            else:
                # Try fallback extraction if no containers found
                logger.warning(f"No product containers found using generic selectors for {url}")
                fallback_product = self._extract_single_product(soup, url)
                if fallback_product:
                    results.append(fallback_product)
            
            logger.info(f"Successfully extracted {len(results)} products from {url}")
            return results
                
        except Exception as e:
            logger.error(f"Error parsing HTML content: {str(e)}")
            return []
    
    async def can_parse(self, url: str) -> bool:
        """
        Determine if this parser can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True as this is a generic fallback parser
        """
        return True
    
    def _extract_from_container(self, container, url: str) -> Optional[Dict[str, Any]]:
        """Extract product data from a container element."""
        try:
            # Try to find title using common patterns
            title_elem = (
                container.select_one('.product-title, .name, .title, h3, h2') or
                container.find('a', attrs={'title': True})
            )
            
            if not title_elem:
                return None
                
            title = title_elem.get_text().strip()
            if not title:
                return None
            
            # Try to find price using common patterns
            price_elem = container.select_one('.price, .product-price, .current-price, .sale-price')
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Extract price and currency
            price = self._extract_price(price_text)
            currency = self._extract_currency(price_text)
            
            # Try to find URL
            product_url = url
            url_elem = container.find('a', href=True)
            if url_elem and url_elem.get('href'):
                href = url_elem.get('href')
                if href.startswith('http'):
                    product_url = href
                elif href.startswith('/'):
                    # Handle relative URLs
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    product_url = f"{base_url}{href}"
            
            # Try to find rating
            rating = None
            rating_elem = container.select_one('.rating, .stars, .product-rating')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Extract store name from URL
            store = self._extract_store_name(url)
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": product_url,
                "store": store,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": True,  # Assume in stock if listed
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data from container: {str(e)}")
            return None
    
    def _extract_single_product(self, soup, url: str) -> Optional[Dict[str, Any]]:
        """Extract data from a single product page."""
        try:
            # Try to find product title in common header locations
            title_elem = (
                soup.select_one('h1.product-title, h1.title, h1.name, h1') or
                soup.select_one('.product-title, .title, .name')
            )
            
            if not title_elem:
                return None
                
            title = title_elem.get_text().strip()
            if not title:
                return None
            
            # Try to find price using common patterns
            price_elem = soup.select_one('.price, .product-price, .current-price, .sale-price')
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Extract price and currency
            price = self._extract_price(price_text)
            currency = self._extract_currency(price_text)
            
            # Try to find rating
            rating = None
            rating_elem = soup.select_one('.rating, .stars, .product-rating')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Extract store name from URL
            store = self._extract_store_name(url)
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": url,
                "store": store,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": True,  # Assume in stock if on page
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting single product data: {str(e)}")
            return None
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract numeric price value from text."""
        if not price_text:
            return None
            
        # Remove currency symbols and non-numeric characters except for . and ,
        clean_text = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle different number formats
        if ',' in clean_text and '.' in clean_text:
            # Determine which is decimal separator based on position
            if clean_text.rindex('.') > clean_text.rindex(','):
                # Format: 1,234.56
                clean_text = clean_text.replace(',', '')
            else:
                # Format: 1.234,56
                clean_text = clean_text.replace('.', '').replace(',', '.')
        elif ',' in clean_text:
            # Could be either 1,234 or 1,23
            if len(clean_text.split(',')[1]) == 2:
                # Likely a decimal: 1,23
                clean_text = clean_text.replace(',', '.')
            else:
                # Likely a thousand separator: 1,234
                clean_text = clean_text.replace(',', '')
        
        try:
            return float(clean_text)
        except ValueError:
            return None
    
    def _extract_currency(self, price_text: str) -> str:
        """Extract currency from price text."""
        if not price_text:
            return "USD"  # Default
            
        currency_map = {
            "$": "USD",
            "USD": "USD",
            "€": "EUR",
            "EUR": "EUR",
            "£": "GBP",
            "GBP": "GBP",
            "R$": "BRL",
            "BRL": "BRL"
        }
        
        for symbol, code in currency_map.items():
            if symbol in price_text:
                return code
                
        return "USD"  # Default to USD if no currency found
    
    def _extract_store_name(self, url: str) -> str:
        """Extract store name from URL."""
        from urllib.parse import urlparse
        
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        # Remove www. prefix and get the domain name
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Extract the main domain part
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            return domain_parts[-2].capitalize()  # Use the second-to-last part as store name
        
        return domain.capitalize()  # Fallback to full domain
