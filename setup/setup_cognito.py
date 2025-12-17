#!/usr/bin/env python3
"""
AWS Cognito Setup Script for Quantum Matter Platform
Creates Cognito User Pool and App Client for authentication
"""

import boto3
import json
import os
import sys
import getpass
from botocore.exceptions import ClientError

def get_aws_region():
    """Get AWS region from environment or profile, with user prompt as fallback"""
    # Check environment variable first
    region = os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION')
    if region:
        return region
    
    # Try to get from AWS profile
    try:
        session = boto3.Session()
        if session.region_name:
            return session.region_name
    except:
        pass
    
    # Prompt user
    print("\n⚠️ AWS region not detected")
    region = input("🌍 Enter AWS region (e.g., us-east-1, ca-central-1): ").strip()
    if region:
        os.environ['AWS_REGION'] = region
        return region
    
    # Final fallback
    print("⚠️ No region specified, defaulting to us-east-1")
    return 'us-east-1'

def list_user_pools():
    """List all available User Pools and let user select one"""
    try:
        region = get_aws_region()
        cognito = boto3.client('cognito-idp', region_name=region)
        
        print("🔍 Finding your Cognito User Pools...")
        response = cognito.list_user_pools(MaxResults=60)
        pools = response['UserPools']
        
        if not pools:
            print("❌ No User Pools found")
            return None
        
        print("\n📋 Available User Pools:")
        print("-" * 60)
        for i, pool in enumerate(pools, 1):
            print(f"{i:2d}. {pool['Name']:<30} | {pool['Id']}")
        
        while True:
            try:
                choice = input(f"\n🎯 Select User Pool (1-{len(pools)}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(pools):
                        selected_pool = pools[idx]
                        print(f"✅ Selected: {selected_pool['Name']} ({selected_pool['Id']})")
                        return selected_pool['Id']
                else:
                    return None
            except (ValueError, KeyboardInterrupt):
                return None
                
    except Exception as e:
        print(f"❌ Failed to list User Pools: {e}")
        return None

def update_user_pool_to_admin_only(pool_id=None):
    """Update existing User Pool to disable self-signup"""
    
    # Try environment variable first, then interactive selection
    if not pool_id:
        pool_id = os.getenv('COGNITO_POOL_ID')
    
    if not pool_id:
        print("🔍 No COGNITO_POOL_ID set, showing available pools...")
        pool_id = list_user_pools()
        if not pool_id:
            print("❌ No User Pool selected")
            return False
    
    try:
        region = get_aws_region()
        cognito = boto3.client('cognito-idp', region_name=region)
        print(f"✅ Connected to Cognito User Pool: {pool_id}")
        
        # Get current User Pool configuration
        print("🔍 Getting current User Pool configuration...")
        response = cognito.describe_user_pool(UserPoolId=pool_id)
        current_config = response['UserPool']
        
        print(f"📋 Current User Pool: {current_config['Name']}")
        
        # Check current admin setting
        current_admin_only = current_config.get('AdminCreateUserConfig', {}).get('AllowAdminCreateUserOnly', False)
        print(f"🔐 Current AllowAdminCreateUserOnly: {current_admin_only}")
        
        if current_admin_only:
            print("✅ User Pool already configured for admin-only user creation")
            return True
        
        # Update User Pool to disable self-signup
        print("🔄 Updating User Pool to disable self-signup...")
        
        update_params = {
            'UserPoolId': pool_id,
            'AdminCreateUserConfig': {
                'AllowAdminCreateUserOnly': True
            }
        }
        
        # Preserve existing policies
        if 'Policies' in current_config:
            update_params['Policies'] = current_config['Policies']
        
        cognito.update_user_pool(**update_params)
        
        print("✅ User Pool updated successfully!")
        print("🛡️ Self-signup is now disabled - only admins can create users")
        
        return True
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Failed to update User Pool: {error_code}")
        print(f"   Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_cognito_user_pool():
    """Create Cognito User Pool for Quantum Matter Platform"""
    
    # Initialize Cognito client
    try:
        region = get_aws_region()
        cognito = boto3.client('cognito-idp', region_name=region)
        print(f"✅ Connected to AWS Cognito in {region}")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        return None
    
    # User Pool configuration
    pool_config = {
        'PoolName': 'quantum-matter-platform',
        'Policies': {
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': False
            }
        },
        'AutoVerifiedAttributes': ['email'],
        'UsernameAttributes': ['email'],
        'UsernameConfiguration': {
            'CaseSensitive': False
        },
        'Schema': [
            {
                'Name': 'email',
                'AttributeDataType': 'String',
                'Required': True,
                'Mutable': True
            },
            {
                'Name': 'name',
                'AttributeDataType': 'String',
                'Required': False,
                'Mutable': True
            }
        ],
        'AdminCreateUserConfig': {
            'AllowAdminCreateUserOnly': True
        },
        'DeviceConfiguration': {
            'ChallengeRequiredOnNewDevice': False,
            'DeviceOnlyRememberedOnUserPrompt': False
        }
    }
    
    try:
        # Create User Pool
        print("🔄 Creating Cognito User Pool...")
        response = cognito.create_user_pool(**pool_config)
        user_pool_id = response['UserPool']['Id']
        print("✅ User Pool created successfully")
        
        # Create App Client
        print("🔄 Creating App Client...")
        client_response = cognito.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='quantum-matter-app-client',
            GenerateSecret=True,
            ExplicitAuthFlows=[
                'ALLOW_USER_SRP_AUTH',
                'ALLOW_USER_PASSWORD_AUTH',
                'ALLOW_REFRESH_TOKEN_AUTH'
            ],
            SupportedIdentityProviders=['COGNITO'],
            ReadAttributes=['email', 'name'],
            WriteAttributes=['email', 'name'],
            RefreshTokenValidity=30,
            AccessTokenValidity=60,
            IdTokenValidity=60,
            TokenValidityUnits={
                'AccessToken': 'minutes',
                'IdToken': 'minutes',
                'RefreshToken': 'days'
            },
            PreventUserExistenceErrors='ENABLED'
        )
        
        app_client_id = client_response['UserPoolClient']['ClientId']
        app_client_secret = client_response['UserPoolClient']['ClientSecret']
        
        print("✅ App Client created successfully")
        
        # Return configuration
        config = {
            'user_pool_id': user_pool_id,
            'app_client_id': app_client_id,
            'app_client_secret': app_client_secret,
            'region': region
        }
        
        return config
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'LimitExceededException':
            print("❌ Cognito limit exceeded. You may already have a User Pool.")
            print("💡 Check existing pools: aws cognito-idp list-user-pools --max-items 10")
        else:
            print(f"❌ Failed to create Cognito resources: {error_code}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

def create_test_user(user_pool_id, email, temporary_password):
    """Create a bootstrap user in the User Pool"""
    try:
        region = get_aws_region()
        cognito = boto3.client('cognito-idp', region_name=region)
        
        print(f"🔄 Creating test user: {email}")
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'},
                {'Name': 'name', 'Value': 'Test User'}
            ],
            TemporaryPassword=temporary_password
        )
        
        # Let Cognito handle temporary password flow for security
        # User will be forced to change password on first login
        
        print(f"✅ Test user created: {email}")
        print("🔑 Test user password configured")
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'UsernameExistsException':
            print(f"⚠️ User {email} already exists")
        else:
            print(f"❌ Failed to create user: {error_code}")
    except Exception as e:
        print(f"❌ Unexpected error creating user: {e}")

def get_eb_environments():
    """Get Elastic Beanstalk environments using AWS API"""
    try:
        region = get_aws_region()
        eb = boto3.client('elasticbeanstalk', region_name=region)
        print(f"🔍 Looking for EB environments in {region}...")
        environments = eb.describe_environments()
        
        if not environments['Environments']:
            print("⚠️ No Elastic Beanstalk environments found")
            return None
        
        # Show all environments (no filtering)
        all_envs = environments['Environments']
        
        if len(all_envs) == 1:
            # Only one environment, auto-select it
            env = all_envs[0]
            print(f"✅ Found EB environment: {env['EnvironmentName']}")
            return env['EnvironmentName']
        
        # Multiple environments, let user choose
        print("📋 Available EB environments:")
        for i, env in enumerate(all_envs, 1):
            status = env.get('Status', 'Unknown')
            health = env.get('Health', 'Unknown')
            print(f"  {i}. {env['EnvironmentName']} ({status}, {health})")
        
        while True:
            try:
                choice = input(f"\n🎯 Select environment (1-{len(all_envs)}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(all_envs):
                        selected_env = all_envs[idx]
                        print(f"✅ Selected: {selected_env['EnvironmentName']}")
                        return selected_env['EnvironmentName']
                    else:
                        print("❌ Invalid selection. Please try again.")
                else:
                    return None
            except (ValueError, KeyboardInterrupt):
                print("\n❌ Selection cancelled.")
                return None
                
    except ClientError as e:
        print(f"❌ Failed to get EB environments: {e}")
        return None

def set_eb_environment_variables(config):
    """Set Cognito environment variables in Elastic Beanstalk using AWS API"""
    try:
        # Get available environments using AWS API
        print("\n🔍 Checking EB environments...")
        env_name = get_eb_environments()
        
        if not env_name:
            print("⏭️ Skipping EB configuration")
            return False
        
        # Use AWS API directly (more reliable than EB CLI)
        region = get_aws_region()
        eb = boto3.client('elasticbeanstalk', region_name=region)
        
        print(f"🔄 Setting Cognito variables in EB environment: {env_name}")
        print("🔒 Configuring sensitive credentials...")
        
        # Prepare environment variables
        option_settings = [
            {
                'Namespace': 'aws:elasticbeanstalk:application:environment',
                'OptionName': 'COGNITO_POOL_ID',
                'Value': config['user_pool_id']
            },
            {
                'Namespace': 'aws:elasticbeanstalk:application:environment',
                'OptionName': 'COGNITO_APP_CLIENT_ID',
                'Value': config['app_client_id']
            },
            {
                'Namespace': 'aws:elasticbeanstalk:application:environment',
                'OptionName': 'COGNITO_APP_CLIENT_SECRET',
                'Value': config['app_client_secret']
            },
            {
                'Namespace': 'aws:elasticbeanstalk:application:environment',
                'OptionName': 'COGNITO_REGION',
                'Value': config['region']
            },
            {
                'Namespace': 'aws:elasticbeanstalk:application:environment',
                'OptionName': 'AUTH_MODE',
                'Value': 'cognito'
            }
        ]
        
        # Update environment
        eb.update_environment(
            EnvironmentName=env_name,
            OptionSettings=option_settings
        )
        
        print(f"✅ Cognito variables set in EB environment: {env_name}")
        print("🔄 Environment update in progress (takes 2-5 minutes)...")
        return True
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"❌ Failed to set EB variables: {error_code}")
        print(f"   Error: {e.response['Error']['Message']}")
        return False
    except Exception as e:
        print(f"❌ Error setting EB variables: {e}")
        return False

def save_config_to_env(config):
    """Save configuration to .env file"""
    env_path = os.path.join(os.path.dirname(__file__), '..', 'config', '.env')
    
    try:
        # Read existing .env if it exists
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        env_vars[key] = value
        
        # Update with Cognito config
        env_vars['COGNITO_POOL_ID'] = config['user_pool_id']
        env_vars['COGNITO_APP_CLIENT_ID'] = config['app_client_id']
        env_vars['COGNITO_APP_CLIENT_SECRET'] = config['app_client_secret']
        env_vars['AUTH_MODE'] = 'cognito'
        
        # Write updated .env
        with open(env_path, 'w') as f:
            f.write("# AWS Cognito Configuration\\n")
            f.write("# Generated by setup_cognito.py\\n\\n")
            for key, value in env_vars.items():
                if 'SECRET' in key.upper():
                    f.write(f"{key}=<REDACTED>\\n")
                else:
                    f.write(f"{key}={value}\\n")
        
        print(f"✅ Configuration saved to: {env_path}")
        
    except Exception as e:
        print(f"❌ Failed to save configuration: {e}")

def setup_aws_credentials():
    """Setup AWS credentials with user selection"""
    try:
        session = boto3.Session()
        available_profiles = session.available_profiles
        if available_profiles:
            print(f"📋 Available AWS profiles: {', '.join(available_profiles)}")
            
            # Ask user to select profile
            while True:
                profile_name = input("\n🎯 Enter AWS profile name (or press Enter for default): ").strip()
                
                if not profile_name:
                    profile_name = 'default'
                
                if profile_name in available_profiles:
                    try:
                        # Test if the selected profile works
                        test_session = boto3.Session(profile_name=profile_name)
                        sts = test_session.client('sts')
                        identity = sts.get_caller_identity()
                        
                        # If we get here, credentials work
                        os.environ['AWS_PROFILE'] = profile_name
                        print(f"✅ Using AWS profile: {profile_name}")
                        print("✅ AWS credentials validated")
                        return True
                    except Exception as e:
                        print(f"❌ Profile '{profile_name}' has invalid credentials: {e}")
                        print("Please try another profile or run: aws sso login")
                        continue
                else:
                    print(f"❌ Profile '{profile_name}' not found. Available: {', '.join(available_profiles)}")
                    continue
        else:
            print("❌ No AWS profiles found")
    except Exception as e:
        print(f"❌ Error accessing AWS profiles: {e}")
    
    print("💡 Please run: aws configure or aws sso login")
    return False

def main():
    """Main setup function"""
    print("🚀 AWS Cognito Setup for Quantum Matter Platform")
    print("=" * 50)
    
    # Check if pool ID is provided as argument for update mode
    pool_id = None
    if len(sys.argv) > 1:
        pool_id = sys.argv[1]
        print(f"📋 Update mode - Using User Pool ID: {pool_id}")
        print("This will update an EXISTING User Pool to admin-only")
        
        confirm = input("\n⚠️ Continue with update? (y/n): ").lower().strip()
        if confirm != 'y':
            print("❌ Update cancelled")
            return
        
        if update_user_pool_to_admin_only(pool_id):
            print("\n" + "=" * 40)
            print("🎉 Update Complete!")
            print("=" * 40)
            print("✅ Self-signup disabled")
            print("✅ Admin-only user creation enabled")
            print("\n📋 Next Steps:")
            print("1. Deploy your application normally")
            print("2. Use bootstrap admin system for first-time setup")
            print("3. Users will see 'Contact admin' message")
        else:
            print("❌ Update failed")
        return
    
    # Check if user wants to update existing pool
    mode = input("\n🎯 Choose mode:\n1. Create NEW User Pool\n2. Update EXISTING User Pool\n\nEnter choice (1 or 2): ").strip()
    
    if mode == '2':
        pool_id = list_user_pools()
        if not pool_id:
            print("❌ No User Pool selected")
            return
        
        if update_user_pool_to_admin_only(pool_id):
            # Get pool details for EB configuration
            region = get_aws_region()
            cognito = boto3.client('cognito-idp', region_name=region)
            
            # Get app client details
            print("🔍 Getting app client details...")
            clients_response = cognito.list_user_pool_clients(UserPoolId=pool_id, MaxResults=60)
            
            if clients_response['UserPoolClients']:
                client_id = clients_response['UserPoolClients'][0]['ClientId']
                client_response = cognito.describe_user_pool_client(UserPoolId=pool_id, ClientId=client_id)
                client_secret = client_response['UserPoolClient'].get('ClientSecret', '')
                
                config = {
                    'user_pool_id': pool_id,
                    'app_client_id': client_id,
                    'app_client_secret': client_secret,
                    'region': region
                }
                
                # Save to .env
                save_config_to_env(config)
                
                # Offer to update EB environment
                update_eb = input("\n🔄 Update EB environment variables? (y/n): ").lower().strip()
                if update_eb == 'y':
                    set_eb_environment_variables(config)
            
            print("\n" + "=" * 40)
            print("🎉 Update Complete!")
            print("=" * 40)
            print("✅ Self-signup disabled")
            print("✅ Admin-only user creation enabled")
            print("\n📋 Next Steps:")
            print("1. Deploy your application normally")
            print("2. Use bootstrap admin system for first-time setup")
            print("3. Users will see 'Contact admin' message")
        else:
            print("❌ Update failed")
        return
    
    print("This creates a NEW User Pool with admin-only user creation")
    
    # Setup AWS credentials
    if not setup_aws_credentials():
        return
    
    # Create Cognito resources
    config = create_cognito_user_pool()
    if not config:
        print("❌ Setup failed")
        return
    
    # Save configuration
    save_config_to_env(config)
    
    # Set EB environment variables
    eb_configured = set_eb_environment_variables(config)
    
    # Create test user
    create_bootstrap = input("\\n🧪 Create bootstrap user for first-time deployment? (y/n): ").lower().strip()
    if create_bootstrap == 'y':
        email = input("📧 Bootstrap user email (deployer): ").strip()
        password = getpass.getpass("🔑 Bootstrap user password (min 8 chars): ").strip()
        
        if email and password and len(password) >= 8:
            create_test_user(config['user_pool_id'], email, password)
            print("\\n💡 This user can use the 'Become Admin' bootstrap button on first login")
        else:
            print("❌ Invalid email or password")
    else:
        print("\\n💡 You can create the first user manually through AWS Console later")
    
    # Display final configuration
    print("\\n" + "=" * 50)
    print("🎉 Cognito Setup Complete!")
    print("=" * 50)
    print("✅ Cognito resources configured")
    print("✅ Self-signup disabled")
    print("✅ Admin-only user creation enabled")
    print(f"Region: {config['region']}")
    print("\\n📋 Next Steps:")
    if eb_configured:
        print("1. ✅ EB environment variables configured automatically")
        print("2. Deploy your application: python deployment/deploy_fixed_integration.py")
        print("3. Create first admin account through AWS Console (see deployment guide)")
        print("4. Login and use 'Become Admin' button for bootstrap")
        print("5. Use admin panel to create additional users")
    else:
        print("1. Set environment variables in Elastic Beanstalk manually:")
        print("   eb setenv COGNITO_POOL_ID=[pool_id] COGNITO_APP_CLIENT_ID=[client_id] COGNITO_APP_CLIENT_SECRET=[secret]")
        print("2. Deploy your application")
        print("3. Create first admin account through AWS Console")
        print("4. Use bootstrap admin system for first-time setup")
        print("5. Users will see 'Contact admin' message for new accounts")
    print("\\n🔐 Admin-controlled authentication is now active!")

if __name__ == "__main__":
    main()