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
from botocore.exceptions import ClientError

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
            
            # Store tokens in session
            st.session_state['authenticated'] = True
            st.session_state['username'] = email
            st.session_state['auth_method'] = 'custom_cognito'
            st.session_state['access_token'] = response['AuthenticationResult']['AccessToken']
            
            return True, "Login successful!"
            
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
        
        # Tab selection
        tab1, tab2, tab3 = st.tabs(["🔑 Login", "📝 Sign Up", "✉️ Verify Email"])
        
        with tab1:
            st.markdown("**Existing Users:**")
            with st.form("login_form"):
                email = st.text_input("Email Address", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                login_btn = st.form_submit_button("🔑 Login")
                
                if login_btn and email and password:
                    success, message = self.login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
        
        with tab2:
            st.markdown("**New Users - Create Account:**")
            with st.form("signup_form"):
                email = st.text_input("Email Address", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password", 
                                       help="8+ characters, uppercase, lowercase, number")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                signup_btn = st.form_submit_button("📝 Create Account")
                
                if signup_btn and email and password:
                    if password != confirm_password:
                        st.error("Passwords don't match!")
                    elif len(password) < 8:
                        st.error("Password must be at least 8 characters!")
                    else:
                        success, message = self.signup_user(email, password)
                        if success:
                            st.success(message)
                            st.info("👆 Go to 'Verify Email' tab to enter your verification code")
                        else:
                            st.error(message)
        
        with tab3:
            st.markdown("**Email Verification:**")
            with st.form("verify_form"):
                email = st.text_input("Email Address", key="verify_email")
                code = st.text_input("Verification Code", key="verify_code", 
                                    help="Check your email for 6-digit code")
                col1, col2 = st.columns(2)
                
                with col1:
                    verify_btn = st.form_submit_button("✅ Verify Email")
                with col2:
                    resend_btn = st.form_submit_button("📧 Resend Code")
                
                if verify_btn and email and code:
                    success, message = self.confirm_signup(email, code)
                    if success:
                        st.success(message)
                        st.info("👆 Go to 'Login' tab to sign in")
                    else:
                        st.error(message)
                
                if resend_btn and email:
                    success, message = self.resend_verification(email)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        return False

def get_custom_auth_handler():
    """Factory function for custom Cognito auth"""
    return CustomCognitoAuth()