"""
Custom AWS Cognito Authentication for Quantum Matter Platform
Handles both signup and login with proper email verification
"""

import os
import boto3
import streamlit as st
import hmac
import hashlib
import base64
import time
import logging
from botocore.exceptions import ClientError

try:
    import jwt
    from jwt import PyJWKClient
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    logging.warning("PyJWT not available - token validation disabled")

logger = logging.getLogger(__name__)

class CustomCognitoAuth:
    def __init__(self):
        self.pool_id = os.getenv('COGNITO_POOL_ID')
        self.app_client_id = os.getenv('COGNITO_APP_CLIENT_ID') 
        self.app_client_secret = os.getenv('COGNITO_APP_CLIENT_SECRET')
        self.region = 'us-east-1'
        
        if self.pool_id and self.app_client_id:
            self.cognito = boto3.client('cognito-idp', region_name=self.region)
        else:
            self.cognito = None
    
    def _calculate_secret_hash(self, username):
        """Calculate secret hash for Cognito"""
        if not self.app_client_secret:
            return None
        
        message = username + self.app_client_id
        dig = hmac.new(
            str(self.app_client_secret).encode('utf-8'), 
            msg=str(message).encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        return base64.b64encode(dig).decode()
    
    def validate_cognito_token(self, token: str) -> dict:
        """Validate Cognito JWT token with signature verification"""
        if not JWT_AVAILABLE:
            logger.warning("JWT validation unavailable - install PyJWT")
            return {"valid": False, "error": "JWT library not available"}
        
        try:
            jwks_url = f"https://cognito-idp.{self.region}.amazonaws.com/{self.pool_id}/.well-known/jwks.json"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True, "verify_aud": False}
            )
            
            logger.info(f"Token validated for user: {decoded.get('username', 'unknown')}")
            return {"valid": True, "payload": decoded}
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return {"valid": False, "error": "Token expired"}
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return {"valid": False, "error": "Invalid token"}
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return {"valid": False, "error": str(e)}
    
    def signup_user(self, email, password):
        """Sign up a new user"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'Username': email,
                'Password': password,
                'UserAttributes': [
                    {'Name': 'email', 'Value': email}
                ]
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            response = self.cognito.sign_up(**params)
            return True, "Signup successful! Check your email for verification code."
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                return False, "User already exists. Try logging in instead."
            elif error_code == 'InvalidPasswordException':
                return False, "Password must be at least 8 characters with uppercase, lowercase, and number."
            else:
                return False, f"Signup failed: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def confirm_signup(self, email, verification_code):
        """Confirm user signup with verification code"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'Username': email,
                'ConfirmationCode': verification_code
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito.confirm_sign_up(**params)
            return True, "Email verified successfully! You can now log in."
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                return False, "Invalid verification code. Please try again."
            elif error_code == 'ExpiredCodeException':
                return False, "Verification code expired. Request a new one."
            else:
                return False, f"Verification failed: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def login_user(self, email, password):
        """Log in an existing user"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'AuthFlow': 'USER_PASSWORD_AUTH',
                'AuthParameters': {
                    'USERNAME': email,
                    'PASSWORD': password
                }
            }
            
            if secret_hash:
                params['AuthParameters']['SECRET_HASH'] = secret_hash
            
            response = self.cognito.initiate_auth(**params)
            
            # Check if user needs to set permanent password
            if response.get('ChallengeName') == 'NEW_PASSWORD_REQUIRED':
                # Store challenge info for password change
                st.session_state['temp_session'] = response['Session']
                st.session_state['temp_username'] = email
                st.session_state['needs_password_change'] = True
                return True, "temporary_password"
            
            # Validate and store tokens
            access_token = response['AuthenticationResult']['AccessToken']
            validation_result = self.validate_cognito_token(access_token)
            
            if validation_result.get('valid'):
                # Get actual Cognito username from token for group membership
                cognito_username = validation_result['payload'].get('username', email)
                
                st.session_state['authenticated'] = True
                st.session_state['username'] = email  # Display email
                st.session_state['cognito_username'] = cognito_username  # Actual Cognito username for groups
                st.session_state['auth_method'] = 'custom_cognito'
                st.session_state['access_token'] = access_token
                st.session_state['token_validated'] = True
                logger.info(f"User {email} authenticated with validated token (Cognito username: {cognito_username})")
                return True, "Login successful!"
            else:
                logger.error(f"Token validation failed for {email}: {validation_result.get('error')}")
                return False, "Authentication failed - invalid token"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NotAuthorizedException':
                return False, "Invalid email or password."
            elif error_code == 'UserNotConfirmedException':
                return False, "Please verify your email first. Check your inbox for verification code."
            else:
                return False, f"Login failed: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def set_permanent_password(self, new_password):
        """Set permanent password for new user"""
        try:
            secret_hash = self._calculate_secret_hash(st.session_state['temp_username'])
            
            params = {
                'ClientId': self.app_client_id,
                'ChallengeName': 'NEW_PASSWORD_REQUIRED',
                'Session': st.session_state['temp_session'],
                'ChallengeResponses': {
                    'USERNAME': st.session_state['temp_username'],
                    'NEW_PASSWORD': new_password
                }
            }
            
            if secret_hash:
                params['ChallengeResponses']['SECRET_HASH'] = secret_hash
            
            response = self.cognito.respond_to_auth_challenge(**params)
            
            # Now authenticate normally
            access_token = response['AuthenticationResult']['AccessToken']
            validation_result = self.validate_cognito_token(access_token)
            
            if validation_result.get('valid'):
                cognito_username = validation_result['payload'].get('username', st.session_state['temp_username'])
                
                st.session_state['authenticated'] = True
                st.session_state['username'] = st.session_state['temp_username']
                st.session_state['cognito_username'] = cognito_username
                st.session_state['auth_method'] = 'custom_cognito'
                st.session_state['access_token'] = access_token
                st.session_state['token_validated'] = True
                
                # Clean up temporary session data
                del st.session_state['temp_session']
                del st.session_state['temp_username']
                del st.session_state['needs_password_change']
                
                return True, "Password set successfully! Welcome to the platform."
            else:
                return False, "Authentication failed after password change"
            
        except ClientError as e:
            return False, f"Failed to set password: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def forgot_password(self, email):
        """Send password reset code"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'Username': email
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito.forgot_password(**params)
            return True, "Password reset code sent! Check your email."
            
        except ClientError as e:
            return False, f"Failed to send reset code: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def confirm_forgot_password(self, email, confirmation_code, new_password):
        """Confirm password reset with new password"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'Username': email,
                'ConfirmationCode': confirmation_code,
                'Password': new_password
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito.confirm_forgot_password(**params)
            return True, "Password reset successfully! You can now log in with your new password."
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'CodeMismatchException':
                return False, "Invalid reset code. Please try again."
            elif error_code == 'ExpiredCodeException':
                return False, "Reset code expired. Request a new one."
            elif error_code == 'InvalidPasswordException':
                return False, "Password must be at least 8 characters with uppercase, lowercase, and number."
            else:
                return False, f"Password reset failed: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def resend_verification(self, email):
        """Resend verification code"""
        try:
            secret_hash = self._calculate_secret_hash(email)
            
            params = {
                'ClientId': self.app_client_id,
                'Username': email
            }
            
            if secret_hash:
                params['SecretHash'] = secret_hash
            
            self.cognito.resend_confirmation_code(**params)
            return True, "Verification code sent! Check your email."
            
        except ClientError as e:
            return False, f"Failed to resend code: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def logout(self):
        """Log out user"""
        st.session_state['authenticated'] = False
        if 'username' in st.session_state:
            del st.session_state['username']
        if 'auth_method' in st.session_state:
            del st.session_state['auth_method']
        if 'access_token' in st.session_state:
            del st.session_state['access_token']
    
    def render_auth_ui(self):
        """Render complete authentication UI"""
        if not self.cognito:
            st.error("🔧 **Cognito Configuration Missing**")
            st.info("Set COGNITO_POOL_ID, COGNITO_APP_CLIENT_ID, and COGNITO_APP_CLIENT_SECRET environment variables")
            return False
        
        # Check if user needs to set permanent password
        if st.session_state.get('needs_password_change', False):
            st.warning("🔑 **Set Your Permanent Password**")
            st.info(f"Welcome {st.session_state.get('temp_username')}! Please set your permanent password to continue.")
            
            with st.form("set_permanent_password"):
                new_password = st.text_input("New Password", type="password", 
                                           help="At least 8 characters with uppercase, lowercase, and number")
                confirm_password = st.text_input("Confirm Password", type="password")
                set_password_btn = st.form_submit_button("🔑 Set Password")
                
                if set_password_btn and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = self.set_permanent_password(new_password)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
            return False
        
        # Check if already authenticated
        if st.session_state.get('authenticated', False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.success(f"✅ **Authenticated as**: {st.session_state.get('username', 'Unknown')}")
            with col2:
                if st.button("🚪 Logout", key="custom_logout"):
                    self.logout()
                    st.rerun()
            return True
        
        st.markdown("### 🔐 Quantum Matter Platform Authentication")
        
        # Tab selection (signup disabled - admin creates users)
        tab1, tab2 = st.tabs(["🔑 Login", "🔑 Reset Password"])
        
        with tab1:
            st.markdown("**Existing Users:**")
            with st.form("login_form"):
                email = st.text_input("Email Address", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                login_btn = st.form_submit_button("🔑 Login")
                
                if login_btn and email and password:
                    success, message = self.login_user(email, password)
                    if success:
                        if message == "temporary_password":
                            st.info("🔑 **New User Detected**: You're using a temporary password. Please set your permanent password below.")
                            st.rerun()
                        else:
                            st.success(message)
                            st.rerun()
                    else:
                        st.error(message)
            
            # Forgot password section
            st.markdown("---")
            st.markdown("**Forgot Password?**")
            with st.form("forgot_password_form"):
                forgot_email = st.text_input("Enter your email address", key="forgot_email")
                forgot_btn = st.form_submit_button("📧 Send Reset Code")
                
                if forgot_btn and forgot_email:
                    success, message = self.forgot_password(forgot_email)
                    if success:
                        st.success(message)
                        st.info("👆 Go to 'Reset Password' tab to enter the reset code")
                    else:
                        st.error(message)
        
        # Only show new user info if not authenticated
        if not st.session_state.get('authenticated', False):
            st.markdown("---")
            st.markdown("**👥 New Users:**")
            st.info("🛡️ Self-registration is disabled. Contact your administrator to create an account.")
            st.markdown("**Admin will:**")
            st.markdown("• Create your account with your email address")
            st.markdown("• Send you a temporary password via email")
            st.markdown("• **Login here with your temporary password** (not on Reset tab)")
            st.markdown("• You'll be prompted to set a permanent password immediately")
        
        with tab2:
            st.markdown("**Reset Password:**")
            st.info("💡 If you received a password reset code, enter it here with your new password")
            st.warning("⚠️ **New Users**: Don't use this tab! Login with your temporary password on the Login tab first.")
            
            with st.form("reset_password_form"):
                reset_email = st.text_input("Email Address", key="reset_email")
                reset_code = st.text_input("Reset Code", key="reset_code", 
                                          help="Enter the 6-digit code from your password reset email")
                new_password = st.text_input("New Password", type="password", key="new_password",
                                           help="At least 8 characters with uppercase, lowercase, and number")
                confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")
                
                reset_confirm_btn = st.form_submit_button("🔑 Set New Password")
                
                if reset_confirm_btn and reset_email and reset_code and new_password and confirm_password:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = self.confirm_forgot_password(reset_email, reset_code, new_password)
                        if success:
                            st.success(message)
                            st.info("👆 Go to 'Login' tab to sign in with your new password")
                        else:
                            st.error(message)
        
        return False

def get_custom_auth_handler():
    """Factory function for custom Cognito auth"""
    return CustomCognitoAuth()