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

def create_cognito_user_pool():
    """Create Cognito User Pool for Quantum Matter Platform"""
    
    # Initialize Cognito client
    try:
        cognito = boto3.client('cognito-idp', region_name='us-east-1')
        print("✅ Connected to AWS Cognito")
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
            'AllowAdminCreateUserOnly': False
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
            'region': 'us-east-1'
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
    """Create a test user in the User Pool"""
    try:
        cognito = boto3.client('cognito-idp', region_name='us-east-1')
        
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
        
        # Set permanent password
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=temporary_password,
            Permanent=True
        )
        
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
        eb = boto3.client('elasticbeanstalk')
        environments = eb.describe_environments()
        
        if not environments['Environments']:
            print("⚠️ No Elastic Beanstalk environments found")
            return None
        
        # Find quantum-matter environments
        quantum_envs = [env for env in environments['Environments'] if 'quantum-matter' in env['EnvironmentName'].lower()]
        
        if quantum_envs:
            if len(quantum_envs) == 1:
                env = quantum_envs[0]
                print(f"✅ Found EB environment: {env['EnvironmentName']}")
                return env['EnvironmentName']
            else:
                print("📋 Multiple Quantum Matter environments found:")
                for i, env in enumerate(quantum_envs, 1):
                    status = env.get('Status', 'Unknown')
                    health = env.get('Health', 'Unknown')
                    print(f"  {i}. {env['EnvironmentName']} ({status}, {health})")
                
                while True:
                    try:
                        choice = input(f"\n🎯 Select environment (1-{len(quantum_envs)}): ").strip()
                        if choice:
                            idx = int(choice) - 1
                            if 0 <= idx < len(quantum_envs):
                                selected_env = quantum_envs[idx]
                                print(f"✅ Selected: {selected_env['EnvironmentName']}")
                                return selected_env['EnvironmentName']
                        else:
                            return None
                    except (ValueError, KeyboardInterrupt):
                        return None
        
        # Show all environments if no quantum-matter found
        print("📋 Available EB environments:")
        for i, env in enumerate(environments['Environments'], 1):
            status = env.get('Status', 'Unknown')
            health = env.get('Health', 'Unknown')
            print(f"  {i}. {env['EnvironmentName']} ({status}, {health})")
        
        while True:
            try:
                choice = input(f"\n🎯 Select environment (1-{len(environments['Environments'])}): ").strip()
                if choice:
                    idx = int(choice) - 1
                    if 0 <= idx < len(environments['Environments']):
                        selected_env = environments['Environments'][idx]
                        print(f"✅ Selected: {selected_env['EnvironmentName']}")
                        return selected_env['EnvironmentName']
                else:
                    return None
            except (ValueError, KeyboardInterrupt):
                return None
                
    except ClientError as e:
        print(f"❌ Failed to get EB environments: {e}")
        return None

def set_eb_environment_variables(config):
    """Set Cognito environment variables in Elastic Beanstalk"""
    try:
        import subprocess
        
        # Check if EB CLI is available
        result = subprocess.run(['eb', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️ EB CLI not found. Skipping automatic EB configuration.")
            return False
        
        # Get available environments using AWS API
        print("\n🔍 Checking EB environments...")
        env_name = get_eb_environments()
        
        if not env_name:
            print("⏭️ Skipping EB configuration")
            return False
        
        # Set environment variables
        print(f"🔄 Setting Cognito variables in EB environment: {env_name}")
        print("🔒 Configuring sensitive credentials (values hidden for security)...")
        
        cmd = [
            'eb', 'setenv',
            f"COGNITO_POOL_ID={config['user_pool_id']}",
            f"COGNITO_APP_CLIENT_ID={config['app_client_id']}",
            f"COGNITO_APP_CLIENT_SECRET={config['app_client_secret']}",
            'AUTH_MODE=cognito',
            '-e', env_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Cognito variables set in EB environment: {env_name}")
            print("🔄 Environment update in progress...")
            return True
        else:
            print(f"❌ Failed to set EB variables: {result.stderr}")
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
    create_test = input("\\n🧪 Create test user? (y/n): ").lower().strip()
    if create_test == 'y':
        email = input("📧 Test user email: ").strip()
        password = getpass.getpass("🔑 Test user password (min 8 chars): ").strip()
        
        if email and password and len(password) >= 8:
            create_test_user(config['user_pool_id'], email, password)
        else:
            print("❌ Invalid email or password")
    
    # Display final configuration
    print("\\n" + "=" * 50)
    print("🎉 Cognito Setup Complete!")
    print("=" * 50)
    print("✅ Cognito resources configured")
    print(f"Region: {config['region']}")
    print("\\n📋 Next Steps:")
    if eb_configured:
        print("1. ✅ EB environment variables configured automatically")
        print("2. Deploy your application: python deployment/deploy_fixed_integration.py")
        print("3. Users can sign up at your app URL")
    else:
        print("1. Set environment variables in Elastic Beanstalk manually:")
        print("   eb setenv [COGNITO_VARIABLES_CONFIGURED]")
        print("2. Deploy your application")
        print("3. Users can sign up at your app URL")
    print("\\n🔐 Authentication is now enterprise-ready!")

if __name__ == "__main__":
    main()