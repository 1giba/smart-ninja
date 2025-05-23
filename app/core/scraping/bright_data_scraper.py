"""
Implementation of the PriceScraper interface using Bright Data.

This module provides a concrete implementation of the PriceScraper interface
that uses the Bright Data service to scrape smartphone prices asynchronously.

It supports various e-commerce sites and handles different HTML structures.
"""
import asyncio
from datetime import datetime
import logging
import os
import re
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
        self.host = os.getenv("BRIGHTDATA_HOST", "brd.superproxy.io")  # Match .env.example naming
        self.port = os.getenv("BRIGHTDATA_PORT", "22225")  # Match .env.example naming

        # SSL verification configuration
        env = os.getenv("ENV", "development").lower()
        self.verify_ssl = env != "development"

        # Create SSL context if verification is disabled
        if not self.verify_ssl:
            import ssl
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.check_hostname = False
            self.ssl_context.verify_mode = ssl.CERT_NONE
            logger.warning(
                "SSL certificate verification is DISABLED. This is insecure and should only be used in development."
            )
        else:
            self.ssl_context = None
            logger.info("SSL certificate verification is enabled")

        # Log configuration status
        if not self.username or not self.password:
            logger.warning(
                "Bright Data credentials not fully configured. "
                "Set BRIGHT_DATA_USERNAME and BRIGHT_DATA_PASSWORD environment variables."
            )
        else:
            logger.info(
                "BrightDataPriceScraper initialized with host=%s, port=%s",
                self.host, self.port
            )

    async def scrape(self, model: str, country: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """Alias for scrape_prices to maintain backward compatibility."""
        return await self.scrape_prices(model, country, timeout)

    def _get_search_urls(self, model: str, country: str) -> List[str]:
        """
        Generate a list of search URLs for different retailers based on model and country.
        Focused on the main countries supported by SmartNinja: US, BR, and EU.

        Args:
            model: Smartphone model to search for
            country: Country code for regional pricing

        Returns:
            List of search URLs to scrape
        """
        from urllib.parse import quote

        # Encode model name for URL
        encoded_model = quote(model)
        logger.info(f"Generating search URLs for {model} in country: {country}")

        # Base URLs for different retailers by country - focused on SmartNinja supported countries
        if country.lower() == "us":
            return [
                f"https://www.amazon.com/s?k={encoded_model}",
                f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded_model}",
                f"https://www.walmart.com/search?q={encoded_model}"
            ]
        elif country.lower() == "br":
            return [
                f"https://www.amazon.com.br/s?k={encoded_model}",
                f"https://www.magazineluiza.com.br/busca/{encoded_model}",
                f"https://www.americanas.com.br/busca/{encoded_model}",
                f"https://www.kabum.com.br/busca/{encoded_model}",
                f"https://www.submarino.com.br/busca/{encoded_model}"
            ]
        elif country.lower() in ["eu", "de"]:
            # Focus on German sites for the European market
            return [
                f"https://www.amazon.de/s?k={encoded_model}",
                f"https://www.mediamarkt.de/de/search.html?query={encoded_model}",
                f"https://www.saturn.de/de/search.html?query={encoded_model}",
                f"https://www.otto.de/suche/{encoded_model}"
            ]
        else:
            # Default to US Amazon if country not specifically supported
            logger.warning(f"Country {country} is not specifically supported, using Amazon US as fallback")
            return [f"https://www.amazon.com/s?k={encoded_model}"]

    async def _scrape_single_url(self, session, url: str, proxy_url: str, timeout) -> List[Dict[str, Any]]:
        """
        Scrape a single URL using the Bright Data proxy and site-specific parsers.

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
            # Determine appropriate headers based on the target site
            headers = self._get_appropriate_headers(url)

            # Fetch HTML content using the new method
            html_content = await self._fetch_html(session, url, proxy_url, timeout, headers)

            if not html_content:
                logger.warning(f"Failed to fetch HTML content from {url}")
                return []

            # Extract store name from URL
            store_name = self._extract_store_name(url)

            # Parse HTML and extract data based on site-specific patterns using our parser system
            return await self._parse_product_data(html_content, store_name, url)

        except aiohttp.ClientError as e:
            logger.error(f"Network error when scraping {url}: {str(e)}")
            # Return empty list instead of raising so other URLs can still be processed
            return []
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return []

    def _get_appropriate_headers(self, url: str) -> Dict[str, str]:
        """
        Get appropriate headers based on the target URL.

        Args:
            url: Target URL

        Returns:
            Dictionary of HTTP headers
        """
        # Base headers that work for most sites
        base_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        }

        # Customize Accept-Language based on the target region
        if any(domain in url.lower() for domain in [".de", "mediamarkt.de", "saturn.de", "idealo.de"]):
            # German sites
            base_headers["Accept-Language"] = "de-DE,de;q=0.9,en;q=0.8"
        elif any(domain in url.lower() for domain in [".fr"]):
            # French sites
            base_headers["Accept-Language"] = "fr-FR,fr;q=0.9,en;q=0.8"
        elif any(domain in url.lower() for domain in [".it"]):
            # Italian sites
            base_headers["Accept-Language"] = "it-IT,it;q=0.9,en;q=0.8"
        elif any(domain in url.lower() for domain in [".co.uk", "currys", "argos"]):
            # UK sites
            base_headers["Accept-Language"] = "en-GB,en;q=0.9"
        elif any(domain in url.lower() for domain in [".com.br", "magazineluiza", "americanas"]):
            # Brazilian sites
            base_headers["Accept-Language"] = "pt-BR,pt;q=0.9,en;q=0.8"
        else:
            # Default to US English
            base_headers["Accept-Language"] = "en-US,en;q=0.9"

        return base_headers

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

    async def _parse_product_data(self, html_content: str, store_name: str, url: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content to extract product data using site-specific parsers.

        Args:
            html_content: HTML content to parse
            store_name: Name of the store
            url: Source URL

        Returns:
            List of product data dictionaries
        """
        try:
            # Import the parser factory
            from app.core.scraping.parsers import ParserFactory

            # Get an appropriate parser for this URL
            parser = await ParserFactory.create_parser(url)

            # Use the parser to extract product data
            results = await parser.parse(html_content, url)

            if results:
                logger.info(f"Successfully scraped {len(results)} products from {url}")
                return results
            else:
                logger.warning(f"No products found at {url}")
                return []
        except Exception as e:
            logger.error(f"Error parsing product data: {str(e)}")
            return []
        # Amazon sites have different structures
        if "amazon" in url.lower():
            # Amazon product grid items have data-asin attribute
            product_containers = soup.select('.s-result-item[data-asin]')
            if not product_containers:
                # Try other Amazon selectors
                product_containers = soup.select('.sg-col-inner .a-section') or \
                                   soup.select('.s-result-item') or \
                                   soup.select('[data-component-type="s-search-result"]')

        # MediaMarkt/Saturn (German electronics retailers)
        elif any(site in url.lower() for site in ["mediamarkt", "saturn"]):
            product_containers = soup.select('.product-wrapper') or \
                               soup.select('.general-product-tile')

        # Idealo (price comparison)
        elif "idealo" in url.lower():
            product_containers = soup.select('.offerList-item') or \
                               soup.select('.productList-item')

        # Magazine Luiza (Brazil)
        elif "magazineluiza" in url.lower():
            product_containers = soup.select('[data-testid="product-card"]') or \
                               soup.select('.product-li')

        # BestBuy
        elif "bestbuy" in url.lower():
            product_containers = soup.select('.sku-item') or \
                               soup.select('.list-item')

        # Walmart
        elif "walmart" in url.lower():
            product_containers = soup.select('[data-item-id]') or \
                               soup.select('.search-result-gridview-item')

        # Target
        elif "target" in url.lower():
            product_containers = soup.select('.styles__StyledCol-sc-fw90uk-0') or \
                               soup.select('.Col-favj32-0')

        # Fallback to generic selectors if none of the above matched
        if not product_containers:
            product_containers = soup.select('.product-container') or \
                               soup.select('.product-card') or \
                               soup.select('.item') or \
                               soup.select('article')

        if not product_containers:
            logger.warning(f"No product containers found for {store_name}")
            # Attempt a more generic approach if specific containers not found
            # Try to find price patterns in the entire document
            return self._fallback_price_extraction(html_content, store_name, url)

        logger.info(f"Found {len(product_containers)} product containers on {url}")

        # Limit to the first 5 products to avoid excessive processing
        for product in product_containers[:5]:
            try:
                # Extract title with site-specific selectors
                title_elem = None

                if "amazon" in url.lower():
                    title_elem = product.select_one('h2 a span') or \
                                product.select_one('.a-text-normal') or \
                                product.select_one('h2')
                elif any(site in url.lower() for site in ["mediamarkt", "saturn"]):
                    title_elem = product.select_one('.title') or \
                                product.select_one('.product-name')
                else:
                    # Generic title selectors
                    title_elem = product.select_one('.product-title') or \
                                product.select_one('h2') or \
                                product.select_one('.item-title') or \
                                product.select_one('h3') or \
                                product.select_one('h4')

                title = title_elem.text.strip() if title_elem else "Unknown Product"

                # Extract price with site-specific selectors
                price_elem = None

                if "amazon" in url.lower():
                    price_elem = product.select_one('.a-price .a-offscreen') or \
                               product.select_one('.a-price') or \
                               product.select_one('.a-color-price')
                elif any(site in url.lower() for site in ["mediamarkt", "saturn"]):
                    price_elem = product.select_one('.price') or \
                               product.select_one('.price-tag')
                elif "idealo" in url.lower():
                    price_elem = product.select_one('.productOfferPrice') or \
                               product.select_one('.price')
                else:
                    # Generic price selectors
                    price_elem = product.select_one('.price') or \
                               product.select_one('.product-price') or \
                               product.select_one('[data-price]') or \
                               product.select_one('[data-test="product-price"]')

                price_text = price_elem.text.strip() if price_elem else ""

                # Look for data attributes if no price text found
                if not price_text and price_elem and price_elem.has_attr('data-price'):
                    price_text = price_elem['data-price']

                # If we still don't have a price, look for other elements with price-related text
                if not price_text:
                    for elem in product.select('*'):
                        elem_text = elem.text.strip()
                        # Look for currency symbols in the text
                        if any(currency in elem_text for currency in ['$', '€', '£', '¥', 'R$']):
                            price_text = elem_text
                            break

                # Clean and convert price
                price = self._extract_price_value(price_text)
                if not price:
                    logger.debug(f"Could not extract price from text: {price_text}")
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
                             product.select_one('.stars') or \
                             product.select_one('[data-star-rating]')
                if rating_elem:
                    rating_text = rating_elem.text.strip()
                    rating_match = re.search(r'([0-9.]+)\s*out of\s*([0-9.]+)', rating_text)
                    if rating_match:
                        rating = float(rating_match.group(1))
                    else:
                        rating_match = re.search(r'([0-9.]+)', rating_text)
                        if rating_match:
                            rating = float(rating_match.group(1))
                # Check for data attributes for rating
                elif rating_elem and rating_elem.has_attr('data-star-rating'):
                    try:
                        rating = float(rating_elem['data-star-rating'])
                    except ValueError:
                        pass

                # Determine if in stock
                in_stock = True  # Default to true
                stock_elem = product.select_one('.stock-status') or \
                            product.select_one('.availability') or \
                            product.select_one('[data-availability]')
                if stock_elem:
                    stock_text = stock_elem.text.lower().strip()
                    if any(phrase in stock_text for phrase in ['out of stock', 'unavailable', 'nicht verfügbar', 'esgotado']):
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

                logger.debug(f"Extracted product: {title} - {currency} {price}")

            except Exception as e:
                logger.error(f"Error extracting product data: {str(e)}")
                continue

        return results

    async def _fetch_html(self, session, url: str, proxy_url: str, timeout, headers=None) -> str:
        """
        Fetch HTML content from a URL using the Bright Data proxy with retry capability.

        Args:
            session: aiohttp ClientSession to use for requests
            url: URL to fetch HTML from
            proxy_url: Proxy URL with authentication
            timeout: Request timeout
            headers: Optional HTTP headers to use (default: None)

        Returns:
            HTML content as string

        Raises:
            Exception: If fetching fails after all retries
        """
        import aiohttp
        from app.core.utils.retry import retry_with_backoff

        # Use default headers if none provided
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            }

        # Create a connector with the appropriate SSL context
        if not self.verify_ssl:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            logger.debug(f"Using custom SSL context with verification disabled for {url}")
        else:
            connector = None
            logger.debug(f"Using default SSL verification for {url}")

        async def _fetch_with_session():
            """Inner function to fetch HTML content that can be retried."""
            try:
                # Log auth details (without exposing password)
                masked_proxy = proxy_url.replace(self.password, '******')
                logger.debug(f"Using proxy: {masked_proxy}")

                # Create a session with the appropriate connector if needed
                async with aiohttp.ClientSession(connector=connector) as local_session:
                    try:
                        async with local_session.get(url, proxy=proxy_url, headers=headers, timeout=timeout) as response:
                            if response.status == 407:
                                logger.error(f"Authentication error (407) for Bright Data proxy. Check username format and credentials.")
                                # Detailed error message to help diagnose auth issues
                                response_text = await response.text()
                                logger.error(f"Proxy response: {response_text[:200]}...")
                                raise aiohttp.ClientResponseError(
                                    request_info=None,
                                    history=None,
                                    status=407,
                                    message=f"Authentication failed for Bright Data proxy",
                                    headers=None
                                )
                            elif response.status == 503:
                                logger.warning(f"Received service unavailable (503) for {url}, will retry")
                                raise aiohttp.ClientResponseError(
                                    request_info=None,
                                    history=None,
                                    status=503,
                                    message=f"Service unavailable for {url}",
                                    headers=None
                                )
                            elif response.status != 200:
                                logger.warning(f"Received status code {response.status} for {url}")
                                return ""

                            # Get HTML content
                            return await response.text()
                    except aiohttp.ClientProxyConnectionError as proxy_err:
                        logger.error(f"Failed to connect to Bright Data proxy: {str(proxy_err)}")
                        raise
            except aiohttp.ClientSSLError as ssl_err:
                logger.error(f"SSL certificate verification error for {url}: {str(ssl_err)}")
                if self.verify_ssl:
                    logger.error("Consider setting VERIFY_SSL=false for development if this is a trusted site")
                raise

        try:
            # Use retry mechanism for fetching HTML
            return await retry_with_backoff(
                _fetch_with_session,
                max_retries=3,
                base_delay=2.0,
                max_delay=15.0,
                retry_exceptions=(aiohttp.ClientError, aiohttp.ClientResponseError),
                jitter=True
            )
        except aiohttp.ClientError as e:
            logger.error(f"Network error when fetching HTML from {url} after retries: {str(e)}")
            return ""
        except Exception as e:
            logger.error(f"Error fetching HTML from {url} after retries: {str(e)}")
            return ""

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

        # Determine currency and price pattern based on URL/domain
        currency = "USD"
        price_matches = []

        # Check if it's a European site
        if any(domain in url.lower() for domain in [".de", ".fr", ".it", ".es", "mediamarkt", "saturn"]):
            currency = "EUR"
            # Euro price patterns (both 1.234,56 € and € 1.234,56 formats)
            price_patterns = [
                r'([0-9.]+,[0-9]{2})\s*€',  # 1.234,56 €
                r'€\s*([0-9.]+,[0-9]{2})',  # € 1.234,56
                r'([0-9.]+,[0-9]{2})\s*EUR'  # 1.234,56 EUR
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    # Convert from European format (1.234,56) to float (1234.56)
                    for match in matches:
                        try:
                            price_str = match.replace('.', '').replace(',', '.')
                            price = float(price_str)

                            return [{
                                "title": title,
                                "price": price,
                                "currency": currency,
                                "url": url,
                                "store": store_name,
                                "date": datetime.now().strftime("%Y-%m-%d"),
                                "in_stock": True,
                                "rating": None
                            }]
                        except ValueError:
                            continue

        # Check if it's a UK site
        elif any(domain in url.lower() for domain in [".co.uk", "currys", "argos"]):
            currency = "GBP"
            # UK price patterns
            price_patterns = [
                r'£\s*([0-9,]+\.[0-9]{2})',  # £ 999.99
                r'([0-9,]+\.[0-9]{2})\s*£'   # 999.99 £
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        price = float(matches[0].replace(',', ''))

                        return [{
                            "title": title,
                            "price": price,
                            "currency": currency,
                            "url": url,
                            "store": store_name,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "in_stock": True,
                            "rating": None
                        }]
                    except ValueError:
                        continue

        # Check if it's a Brazilian site
        elif any(domain in url.lower() for domain in [".com.br", "magazineluiza", "americanas"]):
            currency = "BRL"
            # Brazilian price patterns
            price_patterns = [
                r'R\$\s*([0-9.]+,[0-9]{2})',  # R$ 4.599,90
                r'([0-9.]+,[0-9]{2})\s*R\$'   # 4.599,90 R$
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        price_str = matches[0].replace('.', '').replace(',', '.')
                        price = float(price_str)

                        return [{
                            "title": title,
                            "price": price,
                            "currency": currency,
                            "url": url,
                            "store": store_name,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "in_stock": True,
                            "rating": None
                        }]
                    except ValueError:
                        continue

        # Default to USD pattern for US and other countries
        else:
            price_patterns = [
                r'\$\s*([0-9,]+\.[0-9]{2})',  # $1,299.99
                r'([0-9,]+\.[0-9]{2})\s*\$'   # 1,299.99 $
            ]

            for pattern in price_patterns:
                matches = re.findall(pattern, html_content)
                if matches:
                    try:
                        price = float(matches[0].replace(',', ''))

                        return [{
                            "title": title,
                            "price": price,
                            "currency": currency,
                            "url": url,
                            "store": store_name,
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "in_stock": True,
                            "rating": None
                        }]
                    except ValueError:
                        continue

        # No prices found with any pattern
        return []

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
            Currency code (USD, EUR, GBP, BRL)
        """
        # Main currencies supported by SmartNinja
        if '$' in price_text:
            # Special case for Brazilian Real
            if 'R$' in price_text:
                return "BRL"
            return "USD"
        elif '€' in price_text:
            return "EUR"
        elif '£' in price_text:
            return "GBP"

        # Check for currency codes in the text
        if ' USD' in price_text or 'USD ' in price_text:
            return "USD"
        elif ' EUR' in price_text or 'EUR ' in price_text:
            return "EUR"
        elif ' BRL' in price_text or 'BRL ' in price_text:
            return "BRL"
        elif ' GBP' in price_text or 'GBP ' in price_text:
            return "GBP"

        # Check for currency-related words
        lower_text = price_text.lower()
        if 'euro' in lower_text:
            return "EUR"
        elif 'dollar' in lower_text or 'usd' in lower_text:
            return "USD"
        elif 'real' in lower_text or 'reais' in lower_text:
            return "BRL"
        elif 'pound' in lower_text or 'gbp' in lower_text:
            return "GBP"

        # If the price is in European format (with comma as decimal separator)
        # and we're searching on European sites, assume EUR
        if ',' in price_text and any(c in price_text for c in ['.', ' ']):
            return "EUR"

        # Default to USD if no currency symbol is found
        logger.debug(f"No currency symbol found in '{price_text}', defaulting to USD")
        return "USD"

    async def scrape_prices(self, model: str, country: str, timeout: Optional[int] = 30) -> List[Dict[str, Any]]:
        """
        Scrape smartphone prices from multiple sources asynchronously with concurrency control.

        Args:
            model: Smartphone model to search for
            country: Country code for regional pricing
            timeout: Request timeout in seconds

        Returns:
            List of dictionaries containing scraped price data
        """
        import aiohttp
        import asyncio

        # If credentials are not set, return empty result
        if not self.username or not self.password:
            logger.error("Cannot scrape prices: Bright Data credentials are not configured")
            return []

        # Get URLs to scrape based on model and country
        urls = self._get_search_urls(model, country)
        if not urls:
            logger.warning(f"No URLs to scrape for {model} in {country}")
            return []

        # Prepare proxy URL with authentication
        bright_data_country = self._get_bright_data_country_code(country)
        session_id = f"session-{model.replace(' ', '-')}-{country}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        # Construct the Bright Data authentication URL in the correct format
        # Format: brd-customer-[customer_id]-zone-[zone]-zone-[zone]-country-[country]-session-[session_id]
        zone = os.getenv("BRIGHT_DATA_ZONE", "smartninja_res")

        # Construct auth username with proper format according to Bright Data documentation
        # IMPORTANT: self.username should NOT include the 'brd-customer-' prefix
        # NOTE: The zone parameter needs to be included twice as per Bright Data requirements
        auth_username = f"brd-customer-{self.username}-zone-{zone}-zone-{zone}-country-{bright_data_country}-sid-{session_id}"

        # Make sure the password doesn't contain any special characters that would need URL encoding
        proxy_url = f"https://{auth_username}:{self.password}@{self.host}:{self.port}"

        # Configure timeout
        if not timeout or timeout <= 0:
            timeout = 30

        # Limit concurrent scraping to avoid overwhelming resources
        semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests

        # Create connector with appropriate SSL settings
        if not self.verify_ssl:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            logger.info(f"Created session with SSL verification disabled for {model} scraping")
        else:
            connector = aiohttp.TCPConnector()
            logger.info(f"Created session with SSL verification enabled for {model} scraping")

        # Create async tasks for each URL
        async with aiohttp.ClientSession(connector=connector) as session:
            # Define inner function to scrape with semaphore control
            async def scrape_with_semaphore(url):
                async with semaphore:
                    try:
                        return await self._scrape_single_url(session, url, proxy_url, timeout)
                    except aiohttp.ClientSSLError as ssl_err:
                        logger.error(f"SSL error while scraping {url}: {str(ssl_err)}")
                        if self.verify_ssl:
                            logger.error("Consider setting VERIFY_SSL=false for development if this is a trusted site")
                        return []
                    except Exception as e:
                        logger.error(f"Error scraping {url}: {str(e)}")
                        return []

            # Create tasks
            tasks = [scrape_with_semaphore(url) for url in urls]

            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)

        # Process results
        all_products = []
        for result in results:
            if result:
                all_products.extend(result)

        logger.info(f"Scraped {len(all_products)} products for {model} in {country}")
        return all_products

    def _get_bright_data_country_code(self, country: str) -> str:
        """
        Map a country code to the appropriate Bright Data country code.

        Args:
            country: Country code (e.g., 'us', 'uk', 'eu')

        Returns:
            Bright Data country code
        """
        country_mapping = {
            'us': 'us',        # United States
            'uk': 'gb',        # United Kingdom
            'gb': 'gb',        # United Kingdom (alternate code)
            'br': 'br',        # Brazil
            'eu': 'de',        # Europe (default to Germany)
            'de': 'de',        # Germany
            'fr': 'fr',        # France
            'it': 'it',        # Italy
            'es': 'es',        # Spain
            'ca': 'ca',        # Canada
            'au': 'au',        # Australia
            'jp': 'jp',        # Japan
            'in': 'in',        # India
        }

        # Default to US if country not in mapping
        return country_mapping.get(country.lower(), 'us')
