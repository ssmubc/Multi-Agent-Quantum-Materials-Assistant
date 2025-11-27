"""
AWS Cognito Authentication Module for Quantum Matter Platform
Replaces demo authentication with enterprise-grade AWS Cognito
"""

import os
import streamlit as st
from streamlit_cognito_auth import CognitoAuthenticator
import logging

logger = logging.getLogger(__name__)

class QuantumCognitoAuth:
    """Cognito authentication wrapper for Quantum Matter Platform"""
    
    def __init__(self):
        # Get Cognito configuration from environment variables
        self.pool_id = os.getenv('COGNITO_POOL_ID')
        self.app_client_id = os.getenv('COGNITO_APP_CLIENT_ID') 
        self.app_client_secret = os.getenv('COGNITO_APP_CLIENT_SECRET')
        
        # Initialize authenticator if config is available
        self.authenticator = None
        if self.pool_id and self.app_client_id:
            try:
                self.authenticator = CognitoAuthenticator(
                    pool_id=self.pool_id,
                    app_client_id=self.app_client_id,
                    app_client_secret=self.app_client_secret
                )
                logger.info("✅ Cognito authenticator initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Cognito authenticator: {e}")
                self.authenticator = None
    
    def is_configured(self) -> bool:
        """Check if Cognito is properly configured"""
        return self.authenticator is not None
    
    def authenticate(self) -> bool:
        """Perform Cognito authentication"""
        if not self.authenticator:
            return False
        
        try:
            # Perform login
            is_logged_in = self.authenticator.login()
            
            if is_logged_in:
                # Store user info in session state
                username = self.authenticator.get_username()
                st.session_state['authenticated'] = True
                st.session_state['username'] = username
                st.session_state['auth_method'] = 'cognito'
                logger.info(f"✅ User {username} authenticated via Cognito")
                return True
            else:
                # Clear session state on failed login
                st.session_state['authenticated'] = False
                if 'username' in st.session_state:
                    del st.session_state['username']
                return False
                
        except Exception as e:
            logger.error(f"❌ Cognito authentication error: {e}")
            st.error(f"Authentication error: {e}")
            return False
    
    def logout(self):
        """Perform Cognito logout"""
        if self.authenticator:
            try:
                self.authenticator.logout()
                logger.info("✅ User logged out via Cognito")
            except Exception as e:
                logger.error(f"❌ Cognito logout error: {e}")
        
        # Clear session state
        st.session_state['authenticated'] = False
        if 'username' in st.session_state:
            del st.session_state['username']
        if 'auth_method' in st.session_state:
            del st.session_state['auth_method']
    
    def get_username(self) -> str:
        """Get current username"""
        if self.authenticator and st.session_state.get('authenticated', False):
            return st.session_state.get('username', 'Unknown')
        return 'Not authenticated'
    
    def render_auth_ui(self):
        """Render authentication UI"""
        if not self.is_configured():
            st.error("🔧 **Cognito Configuration Missing**")
            st.info("Set COGNITO_POOL_ID, COGNITO_APP_CLIENT_ID, and COGNITO_APP_CLIENT_SECRET environment variables")
            return False
        
        # Check if already authenticated
        if st.session_state.get('authenticated', False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ **Authenticated as**: {self.get_username()}")
            with col2:
                if st.button("🚪 Logout", key="cognito_logout"):
                    self.logout()
                    st.rerun()
            return True
        
        # Prevent infinite cookie deletion loops
        if 'cognito_init' not in st.session_state:
            st.session_state['cognito_init'] = True
            
        # Show login form with clear instructions
        st.markdown("### 🔐 AWS Cognito Authentication")
        
        # Clear signup instructions (always visible)
        st.markdown("**New Users - Account Creation:**")
        st.markdown("• Enter your **email address** as username")
        st.markdown("• Create a **strong password** (8+ characters, uppercase, lowercase, number)")
        st.markdown("• Click **Login** to create your account")
        st.markdown("• **Check your email** (including spam folder) for verification code")
        st.markdown("• Enter the verification code when prompted")
        st.markdown("• Complete registration and login with your credentials")
        
        st.info("📧 **Email Issues?** Check spam folder or try a different email provider (Gmail, Outlook)")
        st.warning("⚠️ **Not receiving emails?** Contact admin - email verification may need configuration")
        
        st.markdown("---")
        st.markdown("**Existing Users:** Simply enter your email and password below.")
        
        # Perform authentication with error handling
        try:
            return self.authenticate()
        except Exception as e:
            logger.error(f"Cognito authentication error: {e}")
            # Check if it's a user not found error (new user)
            if "UserNotFoundException" in str(e):
                st.warning("🔄 **Account Creation in Progress**")
                st.info("If you're a new user, please check your email (including spam folder) for a verification code and try logging in again.")
            elif "NotAuthorizedException" in str(e):
                st.error("❌ **Login Failed**")
                st.info("Please check your email and password. If you're a new user, make sure you've verified your email address.")
            elif "UserNotConfirmedException" in str(e):
                st.warning("📧 **Email Verification Required**")
                st.info("Please check your email for a verification code. If you didn't receive it, check your spam folder or contact support.")
            else:
                st.error("Authentication temporarily unavailable. Please try again.")
            return False


def get_auth_handler():
    """Factory function to get authentication handler"""
    # Try custom Cognito first
    from .custom_cognito_auth import get_custom_auth_handler
    custom_auth = get_custom_auth_handler()
    if custom_auth.cognito:
        return custom_auth
    
    # Try streamlit-cognito-auth as backup
    cognito_auth = QuantumCognitoAuth()
    if cognito_auth.is_configured():
        return cognito_auth
    
    # Fallback to demo auth if Cognito not configured
    logger.info("🔄 Cognito not configured, falling back to demo authentication")
    from .auth_module import DemoAuth
    return DemoAuth()