"""
Application configuration with environment variable support
"""
import os

class AppConfig:
    """Centralized configuration with environment variable fallbacks"""
    
    # MCP Client Configuration
    MCP_TIMEOUT_SECONDS = int(os.getenv('MCP_TIMEOUT_SECONDS', '45'))
    MCP_MAX_CALLS_BEFORE_RESTART = int(os.getenv('MCP_MAX_CALLS_BEFORE_RESTART', '1'))
    MCP_MIN_CALL_INTERVAL = float(os.getenv('MCP_MIN_CALL_INTERVAL', '1.0'))
    MCP_MAX_CONSECUTIVE_FAILURES = int(os.getenv('MCP_MAX_CONSECUTIVE_FAILURES', '2'))
    
    # Model Configuration
    DEFAULT_CLAUDE_MODEL = os.getenv('DEFAULT_CLAUDE_MODEL', 'us.anthropic.claude-sonnet-4-5-20250929-v1:0')
    DEFAULT_NOVA_MODEL = os.getenv('DEFAULT_NOVA_MODEL', 'amazon.nova-pro-v1:0')
    
    # Session Management
    SESSION_CLEANUP_INTERVAL = int(os.getenv('SESSION_CLEANUP_INTERVAL', '3600'))
    MAX_OBJECT_SIZE_MB = int(os.getenv('MAX_OBJECT_SIZE_MB', '10'))
    
    # Retry Configuration
    DEFAULT_MAX_RETRIES = int(os.getenv('DEFAULT_MAX_RETRIES', '2'))
    RETRY_BASE_DELAY = float(os.getenv('RETRY_BASE_DELAY', '1.0'))
    RETRY_MAX_DELAY = int(os.getenv('RETRY_MAX_DELAY', '10'))