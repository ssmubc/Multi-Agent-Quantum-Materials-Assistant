"""
Role-based Admin Authentication for Quantum Matter Platform
Uses Cognito Groups to control admin access
"""

import boto3
import streamlit as st
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class CognitoAdminAuth:
    """Admin authentication using Cognito Groups"""
    
    def __init__(self):
        self.pool_id = os.getenv('COGNITO_POOL_ID')
        self.region = os.getenv('COGNITO_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        
        if self.pool_id:
            self.cognito = boto3.client('cognito-idp', region_name=self.region)
        else:
            self.cognito = None
    
    def is_user_admin(self, username: str) -> bool:
        """Check if user is in admin group"""
        if not self.cognito or not username:
            return False
        
        try:
            response = self.cognito.admin_list_groups_for_user(
                UserPoolId=self.pool_id,
                Username=username
            )
            
            groups = [group['GroupName'] for group in response['Groups']]
            return 'admin' in groups
            
        except Exception as e:
            logger.error(f"Failed to check admin status: {e}")
            return False
    
    def create_admin_group(self):
        """Create admin group in Cognito (run once)"""
        try:
            self.cognito.create_group(
                GroupName='admin',
                UserPoolId=self.pool_id,
                Description='Platform administrators with user management access'
            )
            logger.info("✅ Admin group created")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'GroupExistsException':
                logger.info("ℹ️ Admin group already exists")
                return True
            else:
                logger.error(f"Failed to create admin group: {e}")
                return False
    
    def add_user_to_admin_group(self, username: str) -> bool:
        """Add user to admin group"""
        try:
            self.cognito.admin_add_user_to_group(
                UserPoolId=self.pool_id,
                Username=username,
                GroupName='admin'
            )
            # Sanitize username for logging to prevent log injection
            safe_username = username.replace('\n', '').replace('\r', '')[:100]
            logger.info(f"✅ Added {safe_username} to admin group")
            return True
        except Exception as e:
            logger.error(f"Failed to add user to admin group: {e}")
            return False
    
    def remove_user_from_admin_group(self, username: str) -> bool:
        """Remove user from admin group"""
        try:
            self.cognito.admin_remove_user_from_group(
                UserPoolId=self.pool_id,
                Username=username,
                GroupName='admin'
            )
            logger.info(f"✅ Removed {username} from admin group")
            return True
        except Exception as e:
            logger.error(f"Failed to remove user from admin group: {e}")
            return False
    
    def create_user(self, email: str, is_admin: bool = False) -> tuple[bool, str]:
        """Create user and optionally make them admin"""
        try:
            # Generate secure temporary password
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%") for _ in range(12))
            temp_password = temp_password[:8] + "A1!"
            
            # Create user
            self.cognito.admin_create_user(
                UserPoolId=self.pool_id,
                Username=email,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {'Name': 'email_verified', 'Value': 'true'}
                ],
                TemporaryPassword=temp_password
                # MessageAction defaults to 'SEND' - AWS will email the user automatically
            )
            
            # Add to admin group if requested
            if is_admin:
                self.add_user_to_admin_group(email)
            
            return True, f"User created successfully. Welcome email sent to {email}"
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UsernameExistsException':
                return False, f"User {email} already exists"
            else:
                return False, f"Failed to create user: {e.response['Error']['Message']}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
    
    def list_users_with_roles(self) -> list:
        """List all users with their admin status"""
        try:
            users = []
            paginator = self.cognito.get_paginator('list_users')
            
            for page in paginator.paginate(UserPoolId=self.pool_id):
                for user in page['Users']:
                    username = user['Username']
                    status = user['UserStatus']
                    created = user['UserCreateDate']
                    
                    # Get email
                    email = username
                    for attr in user.get('Attributes', []):
                        if attr['Name'] == 'email':
                            email = attr['Value']
                            break
                    
                    # Check admin status
                    is_admin = self.is_user_admin(username)
                    
                    users.append({
                        'username': username,
                        'email': email,
                        'status': status,
                        'created': created,
                        'is_admin': is_admin
                    })
            
            return users
            
        except Exception as e:
            if "AccessDenied" in str(e):
                st.error("❌ **IAM Permissions Missing**: EC2 role needs Cognito permissions")
                st.info("📝 Add `cognito-idp:ListUsers` and `cognito-idp:AdminListGroupsForUser` to your EC2 IAM role")
            else:
                st.error(f"❌ Failed to list users: {e}")
            logger.error(f"Failed to list users: {e}")
            return []
    
    def render_admin_panel(self):
        """Render admin panel in Streamlit"""
        if not self.cognito:
            st.error("🔧 Cognito not configured")
            return
        
        # Check if current user is admin using Cognito username
        current_user = st.session_state.get('username')
        cognito_username = st.session_state.get('cognito_username', current_user)
        if not current_user or not self.is_user_admin(cognito_username):
            st.error("🚫 **Access Denied** - Admin privileges required")
            st.info("Contact a platform administrator to request admin access")
            return
        
        st.markdown("## 👑 Admin Panel")
        st.success(f"✅ **Admin Access**: {current_user}")
        
        # Admin tabs
        tab1, tab2, tab3 = st.tabs(["👤 Create User", "📋 Manage Users", "👑 Admin Roles"])
        
        with tab1:
            st.markdown("### Create New User")
            with st.form("create_user_form"):
                email = st.text_input("Email Address")
                is_admin = st.checkbox("Grant Admin Privileges")
                create_btn = st.form_submit_button("Create User")
                
                if create_btn and email:
                    success, message = self.create_user(email, is_admin)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
        
        with tab2:
            st.markdown("### User Management")
            users = self.list_users_with_roles()
            
            if users:
                for user in users:
                    col1, col2, col3 = st.columns([4, 2, 1])
                    
                    with col1:
                        role_badge = "👑 Admin" if user['is_admin'] else "👤 User"
                        st.write(f"**{user['email']}** {role_badge}")
                        st.caption(f"Created: {user['created'].strftime('%Y-%m-%d')}")
                    
                    with col2:
                        if user['username'] != cognito_username:  # Can't modify own role
                            if not user['is_admin']:  # Only show "Make Admin" for regular users
                                if st.button("Make Admin", key=f"admin_{user['username']}"):
                                    if self.add_user_to_admin_group(user['username']):
                                        st.success("Admin privileges granted")
                                        st.rerun()
                    
                    with col3:
                        # Only allow deleting regular users, not other admins or yourself
                        if user['username'] != cognito_username and not user['is_admin']:
                            if st.button("Delete", key=f"delete_{user['username']}"):
                                try:
                                    self.cognito.admin_delete_user(
                                        UserPoolId=self.pool_id,
                                        Username=user['username']
                                    )
                                    st.success("User deleted")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Failed: {e}")
            else:
                st.info("No users found")
        
        with tab3:
            st.markdown("### Admin Role Management")
            st.info("👑 **Current Admins** have full user management access")
            
            # Get admin users from already loaded list
            admin_users = [user for user in users if user['is_admin']]
            
            if admin_users:
                st.success(f"Found {len(admin_users)} admin user(s):")
                for admin in admin_users:
                    st.write(f"👑 **{admin['email']}**")
            else:
                st.warning("No admin users found")

def get_admin_auth():
    """Get admin auth handler"""
    return CognitoAdminAuth()