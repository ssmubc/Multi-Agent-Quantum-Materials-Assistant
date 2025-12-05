"""
Base agent class to reduce code duplication across agent implementations
"""
import logging
from typing import Dict, Any, Optional
from utils.shared_exceptions import ValidationError, ServiceUnavailableError
from utils.mcp_decorators import mcp_error_handler

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agent implementations"""
    
    def __init__(self, mp_agent=None):
        self.mp_agent = mp_agent
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @mcp_error_handler
    def safe_mcp_call(self, method_name: str, *args, **kwargs) -> Any:
        """Safely execute MCP method with consistent error handling"""
        if not self.mp_agent:
            raise ServiceUnavailableError("MCP agent not available")
        
        method = getattr(self.mp_agent, method_name, None)
        if not method:
            raise ValidationError(f"MCP method '{method_name}' not found")
        
        self.logger.info(f"Calling MCP method: {method_name}")
        return method(*args, **kwargs)
    
    def validate_material_id(self, material_id: str) -> str:
        """Validate material ID format"""
        if not material_id or not material_id.strip():
            raise ValidationError("Material ID cannot be empty")
        
        material_id = material_id.strip()
        if not material_id.startswith('mp-'):
            raise ValidationError(f"Invalid material ID format: {material_id}")
        
        return material_id
    
    def extract_material_id_from_results(self, results: Any) -> Optional[str]:
        """Extract material ID from search results"""
        import re
        
        results_text = str(results)
        material_id_match = re.search(r'Material ID: (mp-\d+)', results_text)
        return material_id_match.group(1) if material_id_match else None
    
    def log_operation(self, operation: str, details: str = ""):
        """Consistent logging across agents"""
        self.logger.info(f"{operation}: {details}")