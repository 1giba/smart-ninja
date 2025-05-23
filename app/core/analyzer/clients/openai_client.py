"""
OpenAI LLM client implementation.

Provides an asynchronous client for communicating with the OpenAI API for price analysis.
"""
import asyncio
import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

from app.core.analyzer.interfaces import AsyncLLMClient

# Load environment variables
load_dotenv()

# Get OpenAI configuration from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))

# Try to get Ollama configuration if present (for fallback to local models)
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Configure logger
logger = logging.getLogger(__name__)

if not OPENAI_API_KEY and not OLLAMA_API_URL:
    logger.warning(
        "Neither OPENAI_API_KEY nor OLLAMA_API_URL set in environment variables. LLM client will not function."
    )


class OpenAIClient(AsyncLLMClient):
    """
    Asynchronous client for communicating with the OpenAI API.
    
    Handles API requests, error handling, and response processing with async/await
    patterns for non-blocking operations.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
        client: Optional[Any] = None,
        **kwargs  # Accept additional parameters for flexibility
    ):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key: Optional custom OpenAI API key
            model: Optional custom OpenAI model name
            timeout: Optional custom request timeout in seconds
            client: Optional pre-configured client (for testing)
            **kwargs: Additional parameters (ignored if not supported by AsyncOpenAI)
        """
        self.api_key = api_key or OPENAI_API_KEY
        self.model = model or OPENAI_MODEL
        self.timeout = timeout or OPENAI_TIMEOUT

        # Track if we should use OpenAI or Ollama
        self.use_ollama = False

        # Initialize the client
        if client:
            # Use provided client (for testing)
            self.client = client
            self.client_available = True
        elif self.api_key:
            # Use OpenAI with API key
            try:
                # Only pass parameters that AsyncOpenAI accepts
                # Create a whitelist of supported parameters
                supported_params = {
                    "api_key": self.api_key,
                    "timeout": self.timeout,
                    # Add other supported parameters as needed
                }
                
                # Filter out any parameters not supported by AsyncOpenAI
                # This prevents errors with parameters like 'proxies' that may be passed
                # from higher-level code but aren't supported by the AsyncOpenAI client
                self.client = AsyncOpenAI(**supported_params)
                self.client_available = True
                logger.info("OpenAIClient initialized with model=%s", self.model)
            except Exception as error:
                logger.error("Failed to initialize OpenAI client: %s", str(error))
                self.client = None
                self.client_available = False
        elif OLLAMA_API_URL:
            # Fall back to Ollama for local LLM if available
            try:
                import ollama

                ollama.BASE_URL = OLLAMA_API_URL
                self.model = OLLAMA_MODEL
                self.timeout = OLLAMA_TIMEOUT
                self.client = ollama
                self.client_available = True
                self.use_ollama = True
                logger.info("Initialized Ollama client with model=%s", self.model)
            except ImportError:
                logger.error(
                    "Failed to import ollama package. Please install with 'pip install ollama'"
                )
                self.client = None
                self.client_available = False
        else:
            # No API key or Ollama available
            logger.warning("No LLM client available (missing API keys and Ollama URL)")
            self.client = None
            self.client_available = False

    async def generate_text(self, prompt: str) -> str:
        """
        Generate a response from the LLM API (OpenAI or Ollama) asynchronously.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response text if successful, fallback message otherwise
        """
        if not self.client_available or not self.client:
            logger.warning("LLM client not available. Cannot query API.")
            return (
                "AI price analysis not available. Using basic price comparison instead."
            )

        try:
            if self.use_ollama:
                # Ollama doesn't have official async API - run in thread pool
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: self.client.generate(model=self.model, prompt=prompt)
                )
                return response.get("response", "").strip()
            else:
                # Use OpenAI API with async client
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4,
                    max_tokens=500,
                )
                # Extract the text from the response
                return response.choices[0].message.content.strip()
        except Exception as exception:
            logger.warning("Error querying OpenAI API: %s", str(exception))
            return ""

    # Keep the old method for backward compatibility
    def generate_response(self, prompt: str) -> Optional[str]:
        """
        Generate a response from the LLM API synchronously (legacy method).
        
        This method exists for backward compatibility and will be deprecated.
        New code should use the async generate_text method instead.
        
        Args:
            prompt: The prompt to send to the LLM
            
        Returns:
            Response text if successful, fallback message otherwise
        """
        logger.warning("Using deprecated synchronous generate_response method")
        
        # Use asyncio.run to call our async method
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.generate_text(prompt))
        except Exception as e:
            logger.error("Error in synchronous wrapper: %s", str(e))
            return ""
