"""
Local MCP wrapper with optimized settings for development
"""
import os
import logging

logger = logging.getLogger(__name__)

def initialize_local_mcp():
    """Initialize local MCP environment with optimized settings"""
    try:
        # Set longer timeout for local development (MP API is slower locally)
        os.environ['MCP_LOCAL_TIMEOUT'] = '120'
        
        # Enable debug logging for MCP
        os.environ['MCP_DEBUG'] = '1'
        
        # Set local API cache to avoid repeated calls
        os.environ['MP_API_CACHE'] = '1'
        
        logger.info("✅ Local MCP environment configured with optimized settings")
        
    except Exception as e:
        logger.error(f"💥 Local MCP setup failed: {e}")
        raise