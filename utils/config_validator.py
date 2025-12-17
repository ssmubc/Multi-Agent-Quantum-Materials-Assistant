"""
Secure configuration validator for Quantum Matter App
Validates credentials and configuration at startup
"""
import os
import logging
import boto3
import re
from pathlib import Path
from botocore.exceptions import ClientError
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    pass

def validate_cognito_config() -> Dict[str, str]:
    """
    Validate Cognito configuration from environment or Parameter Store
    
    Returns:
        Dict with validated Cognito configuration
        
    Raises:
        ConfigurationError: If required configuration is missing or invalid
    """
    config = {}
    
    # Check if Cognito is required
    require_cognito = os.getenv('REQUIRE_COGNITO_CONFIG', 'false').lower() == 'true'
    auth_mode = os.getenv('AUTH_MODE', '')
    
    if auth_mode == 'cognito' and require_cognito:
        # Try environment variables first
        pool_id = os.getenv('COGNITO_POOL_ID')
        client_id = os.getenv('COGNITO_APP_CLIENT_ID')
        client_secret = os.getenv('COGNITO_APP_CLIENT_SECRET')
        
        # If not in environment, try Parameter Store
        if not all([pool_id, client_id, client_secret]):
            logger.info("Cognito config not in environment, checking Parameter Store...")
            try:
                ssm = boto3.client('ssm')
                
                if not pool_id:
                    pool_id = _get_parameter(ssm, '/quantum-matter/cognito/pool-id')
                if not client_id:
                    client_id = _get_parameter(ssm, '/quantum-matter/cognito/client-id')
                if not client_secret:
                    client_secret = _get_parameter(ssm, '/quantum-matter/cognito/client-secret')
                    
            except Exception as e:
                logger.error(f"Failed to retrieve from Parameter Store: {e}")
        
        # Validate all required values are present and non-empty
        missing = []
        if not pool_id or pool_id.strip() == '':
            missing.append('COGNITO_POOL_ID')
        if not client_id or client_id.strip() == '':
            missing.append('COGNITO_APP_CLIENT_ID')
        if not client_secret or client_secret.strip() == '':
            missing.append('COGNITO_APP_CLIENT_SECRET')
            
        if missing:
            raise ConfigurationError(
                f"Missing required Cognito configuration: {', '.join(missing)}. "
                f"Set these in environment variables or AWS Systems Manager Parameter Store."
            )
        
        config = {
            'COGNITO_POOL_ID': pool_id.strip(),
            'COGNITO_APP_CLIENT_ID': client_id.strip(),
            'COGNITO_APP_CLIENT_SECRET': client_secret.strip()
        }
        
        logger.info("✅ Cognito configuration validated successfully")
    
    return config

def _get_parameter(ssm_client, parameter_name: str) -> Optional[str]:
    """Get parameter from Systems Manager Parameter Store"""
    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            logger.warning(f"Parameter {parameter_name} not found in Parameter Store")
        else:
            logger.error(f"Error retrieving parameter {parameter_name}: {e}")
        return None

def validate_python_executable(python_path: str) -> str:
    """
    Validate Python executable path to prevent command injection
    
    Args:
        python_path: Path to Python executable
        
    Returns:
        Validated Python executable path
        
    Raises:
        ConfigurationError: If Python executable is invalid
    """
    import shutil
    
    # Sanitize the path - only allow alphanumeric, dots, slashes, backslashes, hyphens, and colons
    import re
    if not re.match(r'^[a-zA-Z0-9._/\\:-]+$', python_path):
        raise ConfigurationError(f"Invalid Python executable path: {python_path}")
    
    # Check if executable exists
    if not shutil.which(python_path):
        raise ConfigurationError(f"Python executable not found: {python_path}")
    
    logger.info(f"✅ Python executable validated: {python_path}")
    return python_path

def validate_working_directory(directory: str) -> str:
    """
    Validate working directory to prevent path traversal
    
    Args:
        directory: Working directory path
        
    Returns:
        Validated directory path
        
    Raises:
        ConfigurationError: If directory is invalid
    """
    import os.path
    
    # Resolve to absolute path to prevent relative path attacks
    abs_directory = os.path.abspath(directory)
    
    # Check if directory exists
    if not os.path.isdir(abs_directory):
        raise ConfigurationError(f"Invalid working directory: {abs_directory}")
    
    # Ensure it's within expected application directories
    allowed_patterns = [
        'Quantum_Matter_Project',
        'Multi-Agent-Quantum-Materials-Assistant',
        'enhanced_mcp_materials'
    ]
    
    if not any(pattern in abs_directory for pattern in allowed_patterns):
        logger.warning(f"Working directory outside expected paths: {abs_directory}")
    
    logger.info(f"✅ Working directory validated: {abs_directory}")
    return abs_directory

def get_secure_api_key() -> Optional[str]:
    """
    Securely retrieve Materials Project API key
    
    Returns:
        API key or None if not available
    """
    from .secrets_manager import get_mp_api_key
    
    # Try Secrets Manager first
    api_key = get_mp_api_key()
    if api_key:
        logger.info("✅ API key retrieved from Secrets Manager")
        return api_key
    
    # Fallback to environment variable (less secure)
    api_key = os.getenv('MP_API_KEY')
    if api_key and api_key.strip():
        logger.warning("⚠️ API key retrieved from environment variable (consider using Secrets Manager)")
        return api_key.strip()
    
    logger.error("❌ No API key found in Secrets Manager or environment")
    return None

def validate_formula(formula: str) -> str:
    """Validate chemical formula input to prevent injection"""
    if not formula or len(formula) > 100:
        raise ValueError("Invalid formula length (max 100 characters)")
    
    # Allow chemical formulas: letters, numbers, hyphens, parentheses, spaces
    if not re.match(r'^[A-Za-z0-9\-\(\)\s]+$', formula.strip()):
        raise ValueError("Invalid formula characters")
    
    return formula.strip()

def validate_query(query: str) -> str:
    """Validate user query input"""
    if not query or len(query) > 5000:
        raise ValueError("Invalid query length (max 5000 characters)")
    
    # Remove potential script tags and suspicious patterns
    cleaned = re.sub(r'<[^>]{0,200}>', '', query)
    if len(cleaned) != len(query):
        raise ValueError("HTML/XML tags not allowed in queries")
    
    return query.strip()

def validate_file_path(path: str, base_dir: str) -> Path:
    """Validate file path to prevent traversal attacks"""
    if not path or '..' in path or path.startswith('/'):
        raise ValueError("Invalid path format")
    
    base_path = Path(base_dir).resolve()
    resolved_path = (base_path / path).resolve()
    
    if not str(resolved_path).startswith(str(base_path)):
        raise ValueError("Path traversal detected")
    
    return resolved_path