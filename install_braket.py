#!/usr/bin/env python3
"""
Installation script for Amazon Braket MCP integration
This script sets up the Braket MCP server and dependencies
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install required Python packages"""
    packages = [
        "amazon-braket-sdk>=1.70.0",
        "qiskit-braket-provider>=0.4.0", 
        "fastmcp>=0.5.0",
        "pydantic>=2.0.0"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    return True

def setup_workspace():
    """Create workspace directory for Braket visualizations"""
    workspace_dir = Path.home() / "quantum_workspace"
    workspace_dir.mkdir(exist_ok=True)
    print(f"✅ Workspace directory created: {workspace_dir}")
    
    # Create subdirectories
    (workspace_dir / "braket_visualizations").mkdir(exist_ok=True)
    (workspace_dir / "circuits").mkdir(exist_ok=True)
    (workspace_dir / "results").mkdir(exist_ok=True)
    
    return str(workspace_dir)

def check_aws_credentials():
    """Check if AWS credentials are configured"""
    try:
        import boto3
        
        # Try current session first
        session = boto3.Session()
        credentials = session.get_credentials()
        
        if credentials is None:
            # Try to find and suggest AWS profiles
            try:
                available_profiles = session.available_profiles
                if available_profiles:
                    print("⚠️ AWS credentials not found in current session")
                    print(f"💡 Available profiles: {', '.join(available_profiles)}")
                    print("💡 Set profile: export AWS_PROFILE=profile_name")
                    print("💡 Example: export AWS_PROFILE=your-profile-name")
                else:
                    print("⚠️ No AWS profiles found")
                    print("💡 Configure using: aws configure sso")
            except:
                print("⚠️ AWS credentials not found")
                print("💡 Configure using: aws configure, AWS_PROFILE, or environment variables")
            return False
        
        # Test STS access
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        profile_name = session.profile_name or "default"
        print(f"✅ AWS credentials configured (profile: {profile_name})")
        print(f"✅ Account: {identity.get('Account', 'Unknown')}")
        return True
        
    except Exception as e:
        print(f"⚠️ AWS credential check failed: {e}")
        print("💡 For local dev: export AWS_PROFILE=your-profile-name")
        print("💡 For AWS deployment: IAM role provides credentials automatically")
        return False

def test_braket_integration():
    """Test if Braket integration works"""
    try:
        from utils.braket_integration import braket_integration
        
        if not braket_integration.is_available():
            print("❌ Braket integration not available")
            return False
        
        # Test Bell pair creation
        result = braket_integration.create_bell_pair_circuit()
        if "error" in result:
            print(f"❌ Braket test failed: {result['error']}")
            return False
        
        print("✅ Braket integration test passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Braket test failed: {e}")
        return False

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("💡 Edit .env file to configure your AWS credentials and settings")
    elif env_file.exists():
        print("ℹ️ .env file already exists")
    else:
        print("⚠️ .env.example not found, skipping .env creation")

def main():
    """Main installation function"""
    print("🚀 Amazon Braket MCP Integration Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    print("\n📦 Installing Dependencies...")
    if not install_dependencies():
        print("❌ Dependency installation failed")
        sys.exit(1)
    
    # Setup workspace
    print("\n📁 Setting up Workspace...")
    workspace_dir = setup_workspace()
    
    # Create .env file
    print("\n⚙️ Configuration Setup...")
    create_env_file()
    
    # Check AWS credentials
    print("\n☁️ Checking AWS Configuration...")
    aws_ok = check_aws_credentials()
    
    # Test Braket integration
    print("\n🧪 Testing Braket Integration...")
    braket_ok = test_braket_integration()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Installation Summary:")
    print(f"✅ Dependencies: Installed")
    print(f"✅ Workspace: {workspace_dir}")
    print(f"{'✅' if aws_ok else '⚠️'} AWS Credentials: {'Configured' if aws_ok else 'Not configured'}")
    print(f"{'✅' if braket_ok else '❌'} Braket Integration: {'Working' if braket_ok else 'Failed'}")
    
    if aws_ok and braket_ok:
        print("\n🎉 Installation completed successfully!")
        print("💡 You can now use Amazon Braket features in the Streamlit app")
    else:
        print("\n⚠️ Installation completed with warnings")
        if not aws_ok:
            print("💡 For local testing: export AWS_PROFILE=your-profile-name")
            print("💡 For AWS deployment: No action needed (uses IAM role)")
        if not braket_ok:
            print("💡 Fix Qiskit version conflict first, then retry")

if __name__ == "__main__":
    main()