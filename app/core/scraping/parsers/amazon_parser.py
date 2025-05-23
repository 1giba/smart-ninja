"""
Amazon-specific parser implementation.

This module provides a parser specialized for Amazon product pages, implementing
the BaseEcommerceParser interface with Amazon-specific HTML parsing logic.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List

from bs4 import BeautifulSoup

from .base_parser import BaseEcommerceParser

# Configure logging
logger = logging.getLogger(__name__)


class AmazonParser(BaseEcommerceParser):
    """Parser specialized for Amazon product pages."""
    
    async def parse(self, html_content: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse Amazon HTML content and extract product data.
        
        Args:
            html_content: HTML content to parse
            url: Source URL for reference
            
        Returns:
            List of dictionaries containing product data
        """
        if not html_content:
            logger.warning(f"Empty HTML content for Amazon URL: {url}")
            return []
            
        try:
            results = []
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Check for captcha or robot check
            if self._is_blocked(soup):
                logger.warning(f"Access blocked by Amazon for URL: {url}")
                return []
            
            # Primary selector for search results
            product_containers = soup.select('div[data-component-type="s-search-result"]')
            
            if not product_containers:
                # Try alternative selectors
                product_containers = soup.select('.s-result-item')
                
            if not product_containers:
                logger.warning(f"No product containers found for Amazon URL: {url}")
                # Try to determine if it's a single product page
                if self._is_product_page(soup):
                    single_product = self._extract_single_product(soup, url)
                    if single_product:
                        results.append(single_product)
                    return results
                return []
            
            logger.info(f"Found {len(product_containers)} product containers on Amazon")
            
            # Extract data from each container
            for container in product_containers:
                product = self._extract_from_container(container, url)
                if product:
                    results.append(product)
            
            logger.info(f"Successfully extracted {len(results)} products from Amazon URL: {url}")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing Amazon HTML content: {str(e)}")
            return []
    
    async def can_parse(self, url: str) -> bool:
        """
        Determine if this parser can handle the given URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if this parser can handle the URL, False otherwise
        """
        return "amazon" in url.lower()
    
    def _is_blocked(self, soup: BeautifulSoup) -> bool:
        """Check if access is blocked by Amazon's anti-scraping measures."""
        title = soup.title.string.lower() if soup.title else ""
        
        block_indicators = [
            "robot check",
            "captcha",
            "sorry",
            "human?"
        ]
        
        for indicator in block_indicators:
            if indicator in title:
                return True
                
        # Check for captcha image
        captcha_img = soup.select_one('img[src*="captcha"]')
        if captcha_img:
            return True
            
        return False
    
    def _is_product_page(self, soup: BeautifulSoup) -> bool:
        """Determine if the page is a single product page."""
        # Check for product page indicators
        product_title = soup.select_one('#productTitle')
        product_price = soup.select_one('#priceblock_ourprice, .a-price')
        
        return product_title is not None or product_price is not None
    
    def _extract_from_container(self, container, url: str) -> Dict[str, Any]:
        """Extract product data from a search result container."""
        try:
            # Extract title
            title_elem = container.select_one('h2 a span, .a-text-normal')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Extract price
            price_elem = container.select_one('.a-price .a-offscreen, .a-price-whole')
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Clean price text and extract numeric value
            price = self._extract_price(price_text)
            
            # Determine currency based on domain
            currency = self._extract_currency_from_url(url)
            
            # Extract product URL
            link_elem = container.select_one('h2 a, .a-link-normal')
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
            rating_elem = container.select_one('.a-icon-star')
            if rating_elem:
                rating_text = rating_elem.get_text().strip()
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Check if in stock
            in_stock = True
            availability_elem = container.select_one('.a-color-price')
            if availability_elem and 'unavailable' in availability_elem.get_text().lower():
                in_stock = False
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": product_url,
                "store": "Amazon",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": in_stock,
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting product data from Amazon container: {str(e)}")
            return {}
    
    def _extract_single_product(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract data from a single product page."""
        try:
            # Extract title
            title_elem = soup.select_one('#productTitle')
            title = title_elem.get_text().strip() if title_elem else "Unknown Product"
            
            # Extract price (multiple possible selectors)
            price_elem = (
                soup.select_one('#priceblock_ourprice') or 
                soup.select_one('.a-price .a-offscreen') or
                soup.select_one('#price_inside_buybox')
            )
            price_text = price_elem.get_text().strip() if price_elem else ""
            
            # Clean price text and extract numeric value
            price = self._extract_price(price_text)
            
            # Determine currency based on domain
            currency = self._extract_currency_from_url(url)
            
            # Extract rating
            rating = None
            rating_elem = soup.select_one('#acrPopover')
            if rating_elem:
                rating_text = rating_elem.get('title', '')
                rating_match = re.search(r'(\d+(\.\d+)?)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            # Check if in stock
            in_stock = True
            availability_elem = soup.select_one('#availability')
            if availability_elem:
                availability_text = availability_elem.get_text().lower()
                if 'unavailable' in availability_text or 'out of stock' in availability_text:
                    in_stock = False
            
            return {
                "title": title,
                "price": price,
                "currency": currency,
                "url": url,
                "store": "Amazon",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "in_stock": in_stock,
                "rating": rating
            }
            
        except Exception as e:
            logger.error(f"Error extracting data from Amazon product page: {str(e)}")
            return {}
    
    def _extract_price(self, price_text: str) -> float:
        """Extract numeric price value from text."""
        if not price_text:
            return None
            
        # Remove currency symbols and non-numeric characters except for . and ,
        clean_text = re.sub(r'[^\d.,]', '', price_text)
        
        # Handle different number formats
        if ',' in clean_text and '.' in clean_text:
            # Amazon US format: 1,234.56
            clean_text = clean_text.replace(',', '')
        elif ',' in clean_text:
            # Amazon EU format: 1.234,56
            if len(clean_text.split(',')[1]) == 2:
                # It's a decimal separator
                clean_text = clean_text.replace(',', '.')
            else:
                # It's a thousand separator
                clean_text = clean_text.replace(',', '')
        
        try:
            return float(clean_text)
        except ValueError:
            return None
    
    def _extract_currency_from_url(self, url: str) -> str:
        """Determine currency based on Amazon domain."""
        domain_currency_map = {
            "amazon.com": "USD",
            "amazon.co.uk": "GBP",
            "amazon.de": "EUR",
            "amazon.fr": "EUR",
            "amazon.it": "EUR",
            "amazon.es": "EUR",
            "amazon.ca": "CAD",
            "amazon.com.br": "BRL",
            "amazon.com.mx": "MXN",
            "amazon.in": "INR",
            "amazon.co.jp": "JPY",
            "amazon.com.au": "AUD"
        }
        
        for domain, currency in domain_currency_map.items():
            if domain in url.lower():
                return currency
                
        return "USD"  # Default to USD
