"""
Rate limiting for API calls and user requests
"""
import time
import streamlit as st
from functools import wraps
from typing import Dict, List
from utils.shared_exceptions import ServiceUnavailableError

class TooManyRequestsError(ServiceUnavailableError):
    """Raised when rate limit is exceeded"""
    pass

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.calls: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str, max_calls: int, period: int) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        if key not in self.calls:
            self.calls[key] = []
        
        # Clean old calls
        self.calls[key] = [c for c in self.calls[key] if c > now - period]
        
        if len(self.calls[key]) >= max_calls:
            return False
        
        self.calls[key].append(now)
        return True

# Global rate limiter instance
_rate_limiter = RateLimiter()

def rate_limit(max_calls: int = 10, period: int = 60):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Use session-based key for user rate limiting
            user_key = st.session_state.get('correlation_id', 'anonymous')
            
            if not _rate_limiter.is_allowed(user_key, max_calls, period):
                raise TooManyRequestsError(f"Rate limit exceeded: {max_calls} calls per {period}s")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator