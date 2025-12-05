"""
Security audit logging for tracking user actions
"""
import time
import streamlit as st
from utils.structured_logger import get_structured_logger

# Dedicated audit logger
audit_logger = get_structured_logger('security_audit')

def audit_log(action: str, resource: str, result: str, **kwargs):
    """Log security-relevant events"""
    user = st.session_state.get('username', 'anonymous')
    correlation_id = st.session_state.get('correlation_id', 'unknown')
    
    audit_data = {
        'event_type': 'security_audit',
        'action': action,
        'resource': resource,
        'user': user,
        'result': result,
        'correlation_id': correlation_id,
        'timestamp': time.time(),
        **kwargs
    }
    
    audit_logger.info(f"AUDIT: {action} on {resource} by {user} - {result}", **audit_data)

def audit_authentication(action: str, user: str, result: str):
    """Audit authentication events"""
    audit_log('authentication', f'user:{user}', result, auth_action=action)

def audit_api_call(endpoint: str, user: str, result: str):
    """Audit API calls"""
    audit_log('api_call', endpoint, result, user=user)

def audit_model_usage(model: str, query_length: int, result: str):
    """Audit model usage"""
    audit_log('model_usage', f'model:{model}', result, query_length=query_length)