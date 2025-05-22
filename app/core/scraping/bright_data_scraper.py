"""
Implementation of the PriceScraper interface using Bright Data.

This module provides a concrete implementation of the PriceScraper interface
that uses the Bright Data service to scrape smartphone prices asynchronously.
Supports concurrent scraping operations with configurable timeouts.
"""
import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from app.core.scraping.interfaces import PriceScraper

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class BrightDataPriceScraper(PriceScraper):
    """Implementation of PriceScraper using Bright Data."""

    def __init__(self):
        """Initialize the BrightDataPriceScraper."""
        # Initialize Bright Data settings from environment
        self.username = os.getenv("BRIGHT_DATA_USERNAME")
        self.password = os.getenv("BRIGHT_DATA_PASSWORD")
        self.host = os.getenv("BRIGHT_DATA_HOST", "brd.superproxy.io")
        self.port = os.getenv("BRIGHT_DATA_PORT", "22225")

    async def scrape(self, model: str, country: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """Alias for scrape_prices to maintain backward compatibility."""
        return await self.scrape_prices(model, country, timeout)

    def _get_search_urls(self, model: str, country: str) -> List[str]:
        """
        Generate a list of search URLs for different retailers based on model and country.

        Args:
            model: Smartphone model to search for
            country: Country code for regional pricing

        Returns:
            List of search URLs to scrape
        """
        from urllib.parse import quote

        # Encode model name for URL
        encoded_model = quote(model)

        # Base URLs for different retailers by country
        if country.lower() == "us":
            return [
                f"https://www.amazon.com/s?k={encoded_model}",
                f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_model}",
                f"https://www.walmart.com/search?q={encoded_model}",
                f"https://www.target.com/s?searchTerm={encoded_model}"
            ]
        elif country.lower() == "br":
            return [
                f"https://www.amazon.com.br/s?k={encoded_model}",
                f"https://www.magazineluiza.com.br/busca/{encoded_model}",
                f"https://www.americanas.com.br/busca/{encoded_model}"
            ]
        else:
            # Default to international Amazon if country not specifically supported
            return [f"https://www.amazon.com/s?k={encoded_model}"]

    async def _scrape_single_url(self, session, url: str, proxy_url: str, timeout) -> List[Dict[str, Any]]:
        """
        Scrape a single URL using the Bright Data proxy.

        Args:
            session: aiohttp ClientSession to use for requests
            url: URL to scrape
            proxy_url: Proxy URL with authentication
            timeout: Request timeout

        Returns:
            List of dictionaries containing scraped price data from this URL

        Raises:
            Exception: If scraping fails
        """
        import aiohttp
        from bs4 import BeautifulSoup
        import re

        logger.info(f"Scraping URL: {url}")

        try:
            # Make request through proxy
            proxy_settings = {"http": proxy_url, "https": proxy_url}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

            # In development mode, disable SSL verification
            ssl_context = None
            env = os.getenv("ENV", "development")
            if env.lower() == "development":
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.info(f"SSL verification disabled for {url} in development mode")

            # Use SSL context for development, normal verification for production
            async with session.get(url, proxy=proxy_url, headers=headers, timeout=timeout, ssl=ssl_context) as response:
                if response.status != 200:
                    logger.warning(f"Received status code {response.status} for {url}")
                    return []

                # Get HTML content
                html_content = await response.text()

                # Extract store name from URL
                store_name = self._extract_store_name(url)

                # Parse HTML and extract data
                return self._parse_product_data(html_content, store_name, url)

        except aiohttp.ClientError as e:
            logger.error(f"Network error when scraping {url}: {str(e)}")
            # Return empty list instead of raising so other URLs can still be processed
            return []
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []

    def _extract_store_name(self, url: str) -> str:
        """
        Extract store name from URL.

        Args:
            url: URL to extract store name from

        Returns:
            Store name
        """
        if "amazon" in url:
            return "Amazon"
        elif "bestbuy" in url:
            return "BestBuy"
        elif "walmart" in url:
            return "Walmart"
        elif "target" in url:
            return "Target"
        elif "magazineluiza" in url:
            return "Magazine Luiza"
        elif "americanas" in url:
            return "Americanas"
        else:
            # Extract domain as fallback
            import re
            match = re.search(r'https?://(?:www\.)?([^/]+)', url)
            if match:
                return match.group(1).split('.')[0].title()
            return "Unknown Store"

    def _parse_product_data(self, html_content: str, store_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content to extract product data.

        Args:
            html_content: HTML content to parse
            store_name: Name of the store
            url: Source URL

        Returns:
            List of product data dictionaries
        """
        from bs4 import BeautifulSoup
        import re

        soup = BeautifulSoup(html_content, 'html.parser')
        results = []

        # Implementation would vary by retailer
        # This is a simplified example that attempts to find common patterns

        # Find product containers, specific implementation depends on the website structure
        product_containers = soup.select('.product-container') or \
                           soup.select('.s-result-item') or \
                           soup.select('.product-card')

        if not product_containers:
            logger.warning(f"No product containers found for {store_name}")
            # Attempt a more generic approach if specific containers not found
            # Try to find price patterns in the entire document
            return self._fallback_price_extraction(html_content, store_name, url)

        for product in product_containers[:5]:  # Limit to 5 results per page
            try:
                # Extract title - look for common patterns
                title_elem = product.select_one('.product-title') or \
                            product.select_one('h2') or \
                            product.select_one('.item-title')

                title = title_elem.text.strip() if title_elem else "Unknown Product"

                # Extract price - look for common patterns
                price_elem = product.select_one('.price') or \
                           product.select_one('.product-price') or \
                           product.select_one('.a-price')

                price_text = price_elem.text.strip() if price_elem else ""

                # Clean and convert price
                price = self._extract_price_value(price_text)
                if not price:
                    continue

                # Extract currency
                currency = self._extract_currency(price_text)

                # Extract URL if available
                product_url = url
                link_elem = product.select_one('a')
                if link_elem and 'href' in link_elem.attrs:
                    product_url = link_elem['href']
                    # Handle relative URLs
                    if product_url.startswith('/'):
                        from urllib.parse import urlparse
                        parsed_url = urlparse(url)
                        product_url = f"{parsed_url.scheme}://{parsed_url.netloc}{product_url}"

                # Extract rating if available
                rating = None
                rating_elem = product.select_one('.rating') or \
                             product.select_one('.stars')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'([0-9.]+)\s*out of\s*([0-9.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                    else:
                        rating_match = re.search(r'([0-9.]+)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))

                # Determine if in stock
                in_stock = True  # Default to true
                stock_elem = product.select_one('.stock-status') or \
                            product.select_one('.availability')
                if stock_elem:
                    stock_text = stock_elem.text.lower().strip()
                    if 'out of stock' in stock_text or 'unavailable' in stock_text:
                        in_stock = False

                results.append({
                    "title": title,
                    "price": price,
                    "currency": currency,
                    "url": product_url,
                    "store": store_name,
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "in_stock": in_stock,
                    "rating": rating
                })

            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue

        return results

    def _fallback_price_extraction(self, html_content: str, store_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Fallback method to extract prices when structured containers aren't found.

        Args:
            html_content: HTML content to parse
            store_name: Name of the store
            url: Source URL

        Returns:
            List of product data dictionaries
        """
        import re
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html_content, 'html.parser')

        # Try to find product title in common header locations
        title_elem = soup.select_one('h1') or \
                    soup.select_one('.product-title') or \
                    soup.select_one('.product-name')

        title = title_elem.text.strip() if title_elem else "Unknown Product"

        # Look for price patterns in the entire HTML
        price_pattern = r'\$\s*([0-9,]+\.[0-9]{2})'
        price_matches = re.findall(price_pattern, html_content)

        if not price_matches:
            return []

        # Use the first price found
        price = float(price_matches[0].replace(',', ''))

        return [{
            "title": title,
            "price": price,
            "currency": "USD",
            "url": url,
            "store": store_name,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "in_stock": True,  # Assume in stock if we found a price
            "rating": None  # No rating available in fallback mode
        }]

    def _extract_price_value(self, price_text: str) -> Optional[float]:
        """
        Extract numeric price value from price text.

        Args:
            price_text: Text containing the price

        Returns:
            Extracted price as float or None if extraction fails
        """
        if not price_text:
            return None

        # Common pattern: $1,234.56 or 1.234,56 € or ¥1234
        import re

        # For $ and similar prefixed currencies
        match = re.search(r'[\$\£\€]\s*([0-9,\.]+)', price_text)
        if match:
            # Handle both 1,234.56 and 1.234,56 formats
            price_str = match.group(1)
            if ',' in price_str and '.' in price_str:
                if price_str.find(',') > price_str.find('.'):
                    # Format: 1.234,56
                    price_str = price_str.replace('.', '').replace(',', '.')
                else:
                    # Format: 1,234.56
                    price_str = price_str.replace(',', '')
            elif ',' in price_str:
                # Could be 1,234 or 1,23
                if len(price_str.split(',')[1]) == 2:
                    # Likely 1,23 format
                    price_str = price_str.replace(',', '.')
                else:
                    # Likely 1,234 format
                    price_str = price_str.replace(',', '')

            try:
                return float(price_str)
            except ValueError:
                return None

        # For postfixed currencies like 1234 €
        match = re.search(r'([0-9,\.]+)\s*[\$\£\€]', price_text)
        if match:
            price_str = match.group(1)
            # Apply same conversion logic as above
            if ',' in price_str and '.' in price_str:
                if price_str.find(',') > price_str.find('.'):
                    price_str = price_str.replace('.', '').replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')
            elif ',' in price_str:
                if len(price_str.split(',')[1]) == 2:
                    price_str = price_str.replace(',', '.')
                else:
                    price_str = price_str.replace(',', '')

            try:
                return float(price_str)
            except ValueError:
                return None

        return None

    def _extract_currency(self, price_text: str) -> str:
        """
        Extract currency from price text.

        Args:
            price_text: Text containing the price

        Returns:
            Currency code
        """
        if '$' in price_text:
            return "USD"
        elif '€' in price_text:
            return "EUR"
        elif '£' in price_text:
            return "GBP"
        elif '¥' in price_text:
            return "JPY"
        elif 'R$' in price_text:
            return "BRL"
        else:
            return "USD"  # Default to USD

    async def scrape_prices(self, model: str, country: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """
        Scrape smartphone prices from multiple sources asynchronously.

        Args:
            model: Smartphone model to search for
            country: Country code for regional pricing
            timeout: Request timeout in seconds

        Returns:
            List of dictionaries containing scraped price data
        """
        import aiohttp
        import ssl

        # Log start of scraping operation
        logger.info(
            "Asynchronously scraping prices for model: %s, country: %s, timeout: %s",
            model,
            country,
            timeout,
        )

        # Check if Bright Data credentials are available
        if not self.username or not self.password:
            logger.error("Bright Data credentials not configured")
            raise ValueError("Bright Data proxy not configured. Check environment variables.")

        try:
            # Get search URLs based on model and country
            search_urls = self._get_search_urls(model, country)

            if not search_urls:
                logger.warning("No search URLs generated for %s in %s", model, country)
                return []

            # Create a proxy URL with authentication
            proxy_url = f"http://{self.username}:{self.password}@{self.host}:{self.port}"

            # Create a timeout object
            timeout_obj = aiohttp.ClientTimeout(total=timeout)

            # Create a custom SSL context that ignores certificate verification for development environment
            # In production, you would want to use proper certificate verification
            ssl_context = None
            env = os.getenv("ENV", "development")
            if env.lower() == "development":
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                logger.info("Running in development mode with SSL verification disabled")

            # Use aiohttp for async HTTP requests with custom SSL context for development
            connector = aiohttp.TCPConnector(ssl=ssl_context if env.lower() == "development" else True)
            async with aiohttp.ClientSession(connector=connector) as session:
                # Configure timeout
                timeout_obj = aiohttp.ClientTimeout(total=timeout)

                # List to collect all results
                results = []

                # Track start time for logging
                start_time = asyncio.get_event_loop().time()

                # Process each URL in parallel
                tasks = []
                for url in search_urls:
                    task = asyncio.create_task(
                        self._scrape_single_url(session, url, proxy_url, timeout_obj)
                    )
                    tasks.append(task)

                # Wait for all scraping tasks to complete
                completed_results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results, filtering out exceptions
                for result in completed_results:
                    if isinstance(result, list):
                        results.extend(result)
                    elif isinstance(result, Exception):
                        logger.warning(f"Error in one of the scraping tasks: {str(result)}")

                elapsed = asyncio.get_event_loop().time() - start_time
                logger.info("Successfully scraped %d results in %.2f seconds", len(results), elapsed)

                # Return the combined results
                return results

        except asyncio.TimeoutError:
            logger.error("Scraping operation timed out after %s seconds", timeout)
            raise TimeoutError(f"Scraping operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error("Error during async scraping: %s", str(e))
            raise
