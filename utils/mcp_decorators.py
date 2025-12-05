"""
Decorators for common MCP operations to reduce code duplication
"""
import logging
import functools
from typing import Callable, Any
from .shared_exceptions import ServiceUnavailableError, ValidationError

logger = logging.getLogger(__name__)

def mcp_error_handler(func: Callable) -> Callable:
    """Decorator for consistent MCP error handling"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except ConnectionError as e:
            logger.error(f"MCP connection failed in {func.__name__}: {e}", exc_info=True)
            raise ServiceUnavailableError("Materials Project service unavailable")
        except ValueError as e:
            logger.warning(f"Invalid input in {func.__name__}: {e}")
            raise ValidationError(f"Invalid input: {e}")
        except Exception as e:
            logger.critical(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise
    return wrapper

def retry_on_failure(max_retries: int = 2, delay: float = 1.0):
    """Decorator for retrying failed operations"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                    from config.app_config import AppConfig
                    wait_time = min(delay * (2 ** attempt), AppConfig.RETRY_MAX_DELAY)
                    time.sleep(wait_time)  # Exponential backoff with cap
            
        return wrapper
    return decorator