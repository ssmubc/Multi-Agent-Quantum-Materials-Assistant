"""
Bootstrap Admin System - First-time setup for platform deployer
Allows the deployer to make themselves admin on first login
"""

import boto3
import streamlit as st
import os
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

class BootstrapAdmin:
    """Handle first-time admin setup for platform deployer"""
    
    def __init__(self):
        self.pool_id = os.getenv('COGNITO_POOL_ID')
        self.region = os.getenv('COGNITO_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        
        if self.pool_id:
            self.cognito = boto3.client('cognito-idp', region_name=self.region)
        else:
            self.cognito = None
    
    def is_bootstrap_needed(self) -> bool:
        """Check if bootstrap is needed (no admin group or no admins)"""
        if not self.cognito:
            return False
        
        # Check if bootstrap is disabled via environment variable
        if os.getenv('DISABLE_BOOTSTRAP', '').lower() == 'true':
            logger.info("Bootstrap disabled via DISABLE_BOOTSTRAP env var")
            return False
        
        try:
            # Check if admin group exists
            try:
                self.cognito.get_group(
                    GroupName='admin',
                    UserPoolId=self.pool_id
                )
                logger.info("Admin group exists")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info("No admin group exists - bootstrap needed")
                    return True  # No admin group exists
            
            # Try to check if any users are in admin group
            try:
                response = self.cognito.list_users_in_group(
                    UserPoolId=self.pool_id,
                    GroupName='admin'
                )
                admin_count = len(response['Users'])
                logger.info(f"Admin group has {admin_count} users")
                if admin_count == 0:
                    logger.info("No admin users found - bootstrap needed")
                    return True
                else:
                    logger.info(f"Found {admin_count} admin users - bootstrap not needed")
                    return False
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    logger.warning(f"Cannot list admin users due to permissions: {e}")
                    # If we can't list users, assume bootstrap is not needed if group exists
                    # This prevents infinite bootstrap loops when permissions are missing
                    logger.info("Admin group exists but cannot list users - assuming bootstrap not needed")
                    return False
                else:
                    logger.error(f"Could not list admin users: {e}")
                    return True  # Other errors, assume bootstrap needed
                
        except Exception as e:
            logger.error(f"Bootstrap check failed: {e}")
            return False
    
    def create_admin_group(self) -> bool:
        """Create admin group if it doesn't exist"""
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
                return True  # Already exists
            else:
                logger.error(f"Failed to create admin group: {e}")
                return False
    
    def make_user_admin(self, username: str) -> bool:
        """Add user to admin group"""
        try:
            self.cognito.admin_add_user_to_group(
                UserPoolId=self.pool_id,
                Username=username,
                GroupName='admin'
            )
            logger.info(f"✅ Made {username} an admin")
            return True
        except Exception as e:
            logger.error(f"Failed to make user admin: {e}")
            return False
    
    def render_bootstrap_ui(self, current_user: str) -> bool:
        """Render bootstrap UI for first-time setup"""
        # Debug: Log session state info
        cognito_username = st.session_state.get('cognito_username', current_user)
        logger.info(f"Bootstrap check - current_user: {current_user}, cognito_username: {cognito_username}")
        
        # Try both the cognito_username and email to check admin status
        is_admin = False
        if cognito_username and self.is_user_admin(cognito_username):
            is_admin = True
            logger.info(f"User {cognito_username} is admin via cognito_username")
        elif current_user and self.is_user_admin(current_user):
            is_admin = True
            logger.info(f"User {current_user} is admin via current_user")
        
        if is_admin:
            logger.info("Bootstrap not needed - user is already admin")
            return False  # Current user is already admin, no bootstrap needed
        

        
        if not self.is_bootstrap_needed():
            logger.info("Bootstrap not needed - admin group has users")
            return False  # Bootstrap not needed
        
        st.warning("🚀 **First-Time Setup Required**")
        st.info("No platform administrators found. As the deployer, you can make yourself the first admin.")
        

        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Current User:** {current_user}")
            st.markdown("**Action:** Make yourself platform administrator")
            
            st.markdown("**Admin Privileges:**")
            st.markdown("• Create and manage user accounts")
            st.markdown("• Grant/revoke admin access to other users")
            st.markdown("• Reset user passwords")
            st.markdown("• Delete user accounts")
        
        with col2:
            if st.button("👑 Become Admin", type="primary"):
                # Get actual Cognito username for group operations
                cognito_username = st.session_state.get('cognito_username', current_user)
                
                # Create admin group first
                if self.create_admin_group():
                    # Make current user admin using Cognito username
                    success = self.make_user_admin(cognito_username)
                    if success:
                        st.success("🎉 **Success!** You are now a platform administrator")
                        st.info("🔄 Refreshing page to activate admin features...")
                        # Clear any cached admin status
                        if 'admin_status_cache' in st.session_state:
                            del st.session_state['admin_status_cache']
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to grant admin privileges to {cognito_username}")
                        st.error("Check AWS CloudWatch logs for detailed error information")
                else:
                    st.error("❌ Failed to create admin group")
            
            # Add refresh button for users already in admin group
            if st.button("🔄 Refresh Status", help="If you're already admin, click to refresh"):
                # Clear session cache and recheck
                if 'admin_status_cache' in st.session_state:
                    del st.session_state['admin_status_cache']
                st.rerun()
            

        
        st.markdown("---")
        st.markdown("**Security Note:** Only the first user can use this bootstrap process. Once an admin exists, new users must be created by existing admins.")
        
        # Show current admin group members for debugging
        with st.expander("👥 Current Admin Group Members"):
            try:
                response = self.cognito.list_users_in_group(
                    UserPoolId=self.pool_id,
                    GroupName='admin'
                )
                if response['Users']:
                    st.write("Current admins:")
                    for user in response['Users']:
                        username = user['Username']
                        email = next((attr['Value'] for attr in user['Attributes'] if attr['Name'] == 'email'), 'No email')
                        st.write(f"• {username} ({email})")
                else:
                    st.write("No admin users found")
            except ClientError as e:
                if e.response['Error']['Code'] == 'AccessDeniedException':
                    st.warning("⚠️ Missing IAM permission: cognito-idp:ListUsersInGroup")
                    st.info("📝 You're already in the admin group but the system can't verify it due to missing permissions.")
                else:
                    st.error(f"Could not list admin users: {e}")
            except Exception as e:
                st.error(f"Could not list admin users: {e}")
        
        return True  # Bootstrap UI was shown

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
            is_admin = 'admin' in groups
            logger.info(f"Admin check for {username}: {is_admin} (groups: {groups})")
            return is_admin
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'AccessDeniedException':
                logger.warning(f"Cannot check admin status for {username} due to permissions: {e}")
                # If we can't check due to permissions, assume not admin for security
                logger.warning(f"Cannot verify admin status for {username} - assuming not admin")
                return False
            else:
                logger.error(f"Failed to check admin status for {username}: {e}")
                return False
        except Exception as e:
            logger.error(f"Failed to check admin status for {username}: {e}")
            return False

def get_bootstrap_admin():
    """Get bootstrap admin handler"""
    return BootstrapAdmin()