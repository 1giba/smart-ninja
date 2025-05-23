"""
LLM client implementations.
"""
from typing import Optional
from app.core.analyzer.clients.openai_client import OpenAIClient

__all__ = ["OpenAIClient", "get_default_llm_client"]


def get_default_llm_client(api_url: Optional[str] = None, model: Optional[str] = None, timeout: Optional[int] = None, **extra_kwargs):
    """Return a properly configured OpenAI client instance.
    
    Args:
        api_url: Optional API URL override
        model: Optional model name override
        timeout: Optional timeout override in seconds
        **extra_kwargs: Any additional keyword arguments (will be filtered by OpenAIClient)
        
    Returns:
        An instance of OpenAIClient configured with the provided options
    """
    kwargs = {}
    if api_url:
        kwargs["api_url"] = api_url
    if model:
        kwargs["model"] = model
    if timeout:
        kwargs["timeout"] = timeout
    
    # Forward any additional parameters - OpenAIClient will filter out unsupported ones
    kwargs.update(extra_kwargs)
    
    return OpenAIClient(**kwargs)
