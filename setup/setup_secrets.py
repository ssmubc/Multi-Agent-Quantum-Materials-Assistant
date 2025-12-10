#!/usr/bin/env python3
"""
Setup script for storing Materials Project API key in AWS Secrets Manager
"""

import sys
import logging
import getpass
from utils.secrets_manager import store_mp_api_key, get_mp_api_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main setup function"""
    print("🔧 Quantum Matter App - Secrets Setup")
    print("=" * 50)
    
    # Get API key from user (secure input)
    api_key = getpass.getpass("Enter your Materials Project API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided")
        sys.exit(1)
    
    # Optional: custom secret name
    secret_name = input("Secret name (press Enter for default 'materials-project/api-key'): ").strip()
    if not secret_name:
        secret_name = "materials-project/api-key"
    
    # Optional: custom region
    region = input("AWS region (press Enter for default 'us-east-1'): ").strip()
    if not region:
        region = "us-east-1"
    
    print(f"\n📡 Storing API key in AWS Secrets Manager...")
    print(f"   Secret name: {secret_name}")
    print(f"   Region: {region}")
    
    # Store the secret
    success = store_mp_api_key(api_key, secret_name, region)
    
    if success:
        print("✅ API key stored successfully!")
        
        # Test retrieval
        print("\n🧪 Testing retrieval...")
        retrieved_key = get_mp_api_key(secret_name, region)
        
        if retrieved_key and retrieved_key == api_key:
            print("✅ API key retrieval test passed!")
            print("\n🎉 Setup complete! You can now run the Streamlit app.")
            print("   The app will automatically use the stored API key.")
        else:
            print("⚠️ API key retrieval test failed")
            print("   You may need to enter the API key manually in the app")
    else:
        print("❌ Failed to store API key")
        print("   Check your AWS credentials and permissions")
        print("   You can enter the API key manually in the app")

if __name__ == "__main__":
    main()