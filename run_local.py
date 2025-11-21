#!/usr/bin/env python3
"""
Local development runner with auth bypass
"""
import os
import sys
import subprocess

# Set demo credentials for local testing (only if not already set)
if not os.environ.get('DEMO_USERNAME'):
    os.environ['DEMO_USERNAME'] = 'demo'
if not os.environ.get('DEMO_PASSWORD'):
    os.environ['DEMO_PASSWORD'] = 'quantum2025'
# Auto-detect AWS profile or use default
if not os.environ.get('AWS_PROFILE'):
    # Try to find available AWS profiles
    import configparser
    try:
        config_path = os.path.expanduser('~/.aws/config')
        credentials_path = os.path.expanduser('~/.aws/credentials')
        
        print(f"[DEBUG] Checking AWS config at: {config_path}")
        print(f"[DEBUG] Checking AWS credentials at: {credentials_path}")
        
        profiles = []
        
        # Check config file
        if os.path.exists(config_path):
            config = configparser.ConfigParser()
            config.read(config_path)
            config_profiles = [section.replace('profile ', '') for section in config.sections() if section.startswith('profile ')]
            profiles.extend(config_profiles)
            print(f"[DEBUG] Found profiles in config: {config_profiles}")
        
        # Check credentials file
        if os.path.exists(credentials_path):
            creds = configparser.ConfigParser()
            creds.read(credentials_path)
            cred_profiles = [section for section in creds.sections()]
            profiles.extend(cred_profiles)
            print(f"[DEBUG] Found profiles in credentials: {cred_profiles}")
        
        # Remove duplicates and prioritize
        profiles = list(dict.fromkeys(profiles))  # Remove duplicates while preserving order
        
        # Prioritize 'default' and 'qmi_streamlit'
        priority_profiles = ['qmi_streamlit', 'default']
        for priority in priority_profiles:
            if priority in profiles:
                profiles.remove(priority)
                profiles.insert(0, priority)
        
        print(f"[DEBUG] All available profiles: {profiles}")
        
        if profiles:
            selected_profile = profiles[0]
            os.environ['AWS_PROFILE'] = selected_profile
            print(f"[INFO] Auto-selected AWS profile: {selected_profile}")
            if len(profiles) > 1:
                print(f"[INFO] Other available profiles: {', '.join(profiles[1:])}")
                print(f"[INFO] To use a different profile: set AWS_PROFILE=<profile_name>")
        else:
            print("[WARN] No AWS profiles found. Please run 'aws configure' or 'aws configure sso'")
            
    except Exception as e:
        print(f"[WARN] Could not detect AWS profiles: {e}")
        print(f"[DEBUG] Error details: {str(e)}")
        print("[INFO] Please set AWS_PROFILE environment variable manually")
else:
    print(f"[INFO] Using existing AWS_PROFILE: {os.environ.get('AWS_PROFILE')}")

# Set Materials Project API key for local development
# You need to get a NEW 32-character API key from https://materialsproject.org/api
# The old 16-character keys don't work with the new mp-api
if not os.environ.get('MP_API_KEY'):
    # Put your Materials Project API key here:
    os.environ['MP_API_KEY'] = 'PUT_YOUR_32_CHARACTER_MP_API_KEY_HERE'
    print("[INFO] Using MP_API_KEY from run_local.py file")

# Fix MCP server Python path for local development
os.environ['MCP_PYTHON_PATH'] = sys.executable
os.environ['PYTHONPATH'] = os.getcwd() + os.pathsep + os.path.join(os.getcwd(), 'enhanced_mcp_materials')

print("=== Setting up local environment ===")
print("Demo credentials: demo / quantum2025")
print(f"Current working directory: {os.getcwd()}")
aws_profile = os.environ.get('AWS_PROFILE', 'Not set')
print(f"Final AWS Profile: {aws_profile}")

# Test AWS credentials
if aws_profile != 'Not set':
    try:
        import boto3
        session = boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        print(f"[SUCCESS] AWS credentials working! Account: {identity.get('Account', 'Unknown')}")
    except Exception as e:
        print(f"[ERROR] AWS credentials test failed: {e}")
        print("[FIX] Try: aws sso login")
else:
    print("[SETUP] To configure AWS:")
    print("  1. For SSO: aws configure sso")
    print("  2. For access keys: aws configure")
    print("  3. Or set: set AWS_PROFILE=your-profile-name")
mp_key = os.environ.get('MP_API_KEY', '')
print(f"MP_API_KEY: {'VALID' if len(mp_key) == 32 and mp_key != 'PUT_YOUR_32_CHARACTER_MP_API_KEY_HERE' else 'NEEDS_SETUP'}")
if len(mp_key) != 32 or mp_key == 'PUT_YOUR_32_CHARACTER_MP_API_KEY_HERE':
    print("\n[ERROR] Please set your real MP_API_KEY in run_local.py file!")
    print("Replace 'PUT_YOUR_32_CHARACTER_MP_API_KEY_HERE' with your actual key\n")
print(f"Python path: {sys.executable}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print(f"MCP Python: {os.environ.get('MCP_PYTHON_PATH', 'Not set')}")

# Setup local MCP environment with optimized settings
try:
    from utils.local_mcp_wrapper import initialize_local_mcp
    initialize_local_mcp()
    print("[OK] Local MCP environment configured with 120s timeout")
except Exception as e:
    print(f"[WARN] MCP setup warning: {e}")
    print("App will use fallback mode if MCP fails")

# Set additional local optimizations
os.environ['MCP_LOCAL_MODE'] = '1'
print("[INFO] Local development mode enabled with real MCP server")
print("=== Environment Setup Complete ===")

# Run streamlit with smart port selection
try:
    print("Starting Streamlit...")
    # Try port 8501 first, fall back to 8502 if busy
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8501"], check=True)
    except subprocess.CalledProcessError:
        print("Port 8501 busy, trying 8502...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8502"], check=True)
except KeyboardInterrupt:
    print("\nStopped by user")
except Exception as e:
    print(f"Error: {e}")