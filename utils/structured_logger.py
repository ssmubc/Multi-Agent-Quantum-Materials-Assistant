"""
Structured logging with correlation IDs and security-aware formatting
"""
import logging
import json
import time
import uuid
import streamlit as st
from typing import Dict, Any, Optional

class StructuredLogger:
    """Structured logger with correlation IDs and security filtering"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.setup_structured_logging()
    
    def setup_structured_logging(self):
        """Setup JSON structured logging"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = StructuredFormatter()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def get_correlation_id(self) -> str:
        """Get or create correlation ID for request tracking"""
        if 'correlation_id' not in st.session_state:
            st.session_state.correlation_id = str(uuid.uuid4())[:8]
        return st.session_state.correlation_id
    
    def log_with_context(self, level: str, message: str, **kwargs):
        """Log with request context and security filtering"""
        context = {
            'correlation_id': self.get_correlation_id(),
            'user': st.session_state.get('username', 'anonymous'),
            'timestamp': time.time(),
            'component': self.logger.name
        }
        
        # Filter sensitive data
        filtered_kwargs = self._filter_sensitive_data(kwargs)
        
        log_data = {**context, **filtered_kwargs, 'message': message}
        
        getattr(self.logger, level.lower())(json.dumps(log_data))
    
    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from log data"""
        sensitive_keys = ['api_key', 'password', 'token', 'secret', 'credential']
        filtered = {}
        
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                filtered[key] = '[REDACTED]'
            elif isinstance(value, str) and len(value) > 100:
                filtered[key] = value[:100] + '...[TRUNCATED]'
            else:
                filtered[key] = value
        
        return filtered
    
    def debug(self, message: str, **kwargs):
        self.log_with_context('debug', message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self.log_with_context('info', message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self.log_with_context('warning', message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self.log_with_context('error', message, **kwargs)

class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logs"""
    
    def format(self, record):
        try:
            # Try to parse as JSON first
            return record.getMessage()
        except:
            # Fallback to standard formatting
            return super().format(record)

def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance"""
    return StructuredLogger(name)