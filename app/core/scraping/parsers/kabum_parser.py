"""
Kabum specific parser implementation.

This module provides a parser specialized for Kabum product pages,
implementing the BaseEcommerceParser interface with site-specific HTML parsing logic.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from .base_parser import BaseEcommerceParser

# Configure logging
logger = logging.getLogger(__name__)


class KabumParser(BaseEcommerceParser):
    """Parser specialized for Kabum product pages."""
    
    async def parse(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse Kabum HTML content and extract product data.
        
        Args:
            html_content: HTML content to parse
            url: Source URL for reference
            
        Returns:
            List of dictionaries containing product data
        """
        if not html_content:
            logger.warning(f"Empty HTML content for Kabum URL: {url}")
            return []
            
        try:
            results = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Primary selector for search results
            product_containers = soup.select('.productCard, .cardProduct')
            
            if not product_containers:
                # Try alternative selectors
                product_containers = soup.select('.product-list__item, .productItem')
                
            if not product_containers:
                logger.warning(f"No product containers found for Kabum URL: {url}")
                # Try to determine if it's a single product page
                if self._is_product_page(soup):
                    single_product = self._extract_single_product(soup, url)
                    if single_product:
                        results.append(single_product)
                    return results
                return []
            
            logger.info(f"Found {len(product_containers)} product containers on Kabum")
            
            # Extract data from each container
            for container in product_containers:
                product = self._extract_from_container(container, url)
                if product:
                    results.append(product)
            
            logger.info(f"Successfully extracted {len(results)} products from Kabum URL: {url}")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing Kabum HTML content: {str(e)}")
            return []
    
    async def can_parse(self, url: str) -> bool:
        """
        Determine if this parser can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if this parser can handle the URL, False otherwise
        """
        return "kabum" in url.lower()
    
    def _is_product_page(self, soup: BeautifulSoup) -> bool:
        """Determine if the page is a single product page."""
        # Check for product page indicators
        product_title = soup.select_one('h1.product__title, .product-title')
        product_price = soup.select_one('.finalPrice, .price__value')
        
        return product_title is not None or product_price is not None
    
    def _extract_from_container(self, container, url: str) -> Dict[str, Any]:
        """Extract product data from a search result container."""
        try:
            # Extract title
            title_elem = container.select_one('.nameCard, .productName, .product-card__title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Extract price
            price_elem = container.select_one('.priceCard, .finalPrice, .price__value')
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Clean price text and extract numeric value
            price = self._extract_price(price_text)
            
            # Brazilian site uses BRL
            currency = "BRL"
            
            # Extract product URL
            link_elem = container.select_one('a[href]')
            product_url = url
            if link_elem and link_elem.get('href'):
                href = link_elem.get('href')
                if href.startswith('http'):
                    product_url = href
                elif href.startswith('/'):
                    # Handle relative URLs
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
                    product_url = f"{base_url}{href}"
            
            # Extract rating
            rating = None
            rating_elem = container.select_one('.rating, .stars')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Check if in stock
            in_stock = True
            availability_elem = container.select_one('.unavailable, .out-of-stock')
            if availability_elem:
                in_stock = False
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": product_url,
                "store": "Kabum",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": in_stock,
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data from Kabum container: {str(e)}")
            return {}
    
    def _extract_single_product(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract data from a single product page."""
        try:
            # Extract title
            title_elem = soup.select_one('h1.product__title, .product-title')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Extract price
            price_elem = soup.select_one('.finalPrice, .price__value')
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Clean price text and extract numeric value
            price = self._extract_price(price_text)
            
            # Brazilian site uses BRL
            currency = "BRL"
            
            # Extract rating
            rating = None
            rating_elem = soup.select_one('.rating, .stars')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Check if in stock
            in_stock = True
            availability_elem = soup.select_one('.unavailable, .out-of-stock')
            if availability_elem:
                in_stock = False
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": url,
                "store": "Kabum",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": in_stock,
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from Kabum product page: {str(e)}")
            return {}
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price value from text."""
        if not price_text:
            return None
            
        # Remove currency symbols and non-numeric characters except for . and ,
        clean_text = re.sub(r'[^\d.,]', '', price_text)
        
        # Brazilian format: 1.234,56
        if ',' in clean_text:
            # Replace decimal comma with dot
            clean_text = clean_text.replace('.', '').replace(',', '.')
        
        try:
            return float(clean_text)
        except ValueError:
            return None
