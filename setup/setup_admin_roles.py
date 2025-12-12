#!/usr/bin/env python3
"""
Setup Admin Roles in Cognito
Creates admin group and assigns first admin user
"""

import boto3
import os
import sys
from botocore.exceptions import ClientError

def setup_admin_system():
    """Setup admin group and first admin user"""
    
    pool_id = os.getenv('COGNITO_POOL_ID')
    if not pool_id:
        print("❌ COGNITO_POOL_ID environment variable not set")
        return False
    
    try:
        cognito = boto3.client('cognito-idp', region_name='us-east-1')
        print(f"✅ Connected to Cognito User Pool: {pool_id}")
        
        # Create admin group
        print("🔄 Creating admin group...")
        try:
            cognito.create_group(
                GroupName='admin',
                UserPoolId=pool_id,
                Description='Platform administrators with user management access'
            )
            print("✅ Admin group created")
        except ClientError as e:
            if e.response['Error']['Code'] == 'GroupExistsException':
                print("ℹ️ Admin group already exists")
            else:
                print(f"❌ Failed to create admin group: {e}")
                return False
        
        # List existing users
        print("\n📋 Existing users:")
        response = cognito.list_users(UserPoolId=pool_id)
        users = response['Users']
        
        if not users:
            print("⚠️ No users found. Create a user first, then run this script.")
            return False
        
        print("-" * 50)
        for i, user in enumerate(users, 1):
            username = user['Username']
            status = user['UserStatus']
            
            # Get email
            email = username
            for attr in user.get('Attributes', []):
                if attr['Name'] == 'email':
                    email = attr['Value']
                    break
            
            print(f"{i:2d}. {email:<30} | {status}")
        
        # Select admin user
        while True:
            try:
                choice = input(f"\n👑 Select user to make admin (1-{len(users)}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(users):
                        selected_user = users[idx]
                        break
                else:
                    print("❌ Setup cancelled")
                    return False
            except (ValueError, KeyboardInterrupt):
                print("❌ Setup cancelled")
                return False
        
        # Add user to admin group
        username = selected_user['Username']
        email = username
        for attr in selected_user.get('Attributes', []):
            if attr['Name'] == 'email':
                email = attr['Value']
                break
        
        print(f"🔄 Adding {email} to admin group...")
        try:
            cognito.admin_add_user_to_group(
                UserPoolId=pool_id,
                Username=username,
                GroupName='admin'
            )
            print(f"✅ {email} is now an admin")
        except Exception as e:
            print(f"❌ Failed to add user to admin group: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False

def main():
    """Main setup function"""
    print("👑 Setup Admin Roles for Quantum Matter Platform")
    print("=" * 50)
    
    if setup_admin_system():
        print("\n" + "=" * 50)
        print("🎉 Admin System Setup Complete!")
        print("=" * 50)
        print("✅ Admin group created")
        print("✅ First admin user assigned")
        print("\n📋 Next Steps:")
        print("1. Deploy your application")
        print("2. Login as the admin user")
        print("3. Access Admin Panel in the app")
        print("4. Create and manage users through the web interface")
        print("\n🔐 Security: Only users in 'admin' group can manage users")
    else:
        print("❌ Setup failed")

if __name__ == "__main__":
    main()