"""
Shared exception classes for better error handling
"""

class QuantumMatterError(Exception):
    """Base exception for Quantum Matter application"""
    pass

class ValidationError(QuantumMatterError):
    """Raised when input validation fails"""
    pass

class ServiceUnavailableError(QuantumMatterError):
    """Raised when external service is unavailable"""
    pass

class AuthenticationError(QuantumMatterError):
    """Raised when authentication fails"""
    pass

class ConfigurationError(QuantumMatterError):
    """Raised when configuration is invalid"""
    pass