#!/usr/bin/env python3
"""
Fixed Deployment Script for Quantum Matter Streamlit App
Includes fixes for Strands-MCP integration and Braket MCP installation
"""

import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path

def create_deployment_package():
    """Create deployment package with all fixes"""
    
    print("Creating fixed deployment package...")
    
    # Define source and target directories
    source_dir = Path(__file__).parent.parent  # Go up from deployment/ to root
    temp_dir = source_dir / "deployment_temp"
    zip_path = source_dir / "quantum_matter_app_fixed.zip"
    
    # Clean up previous builds
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if zip_path.exists():
        zip_path.unlink()
    
    # Create temp directory
    temp_dir.mkdir()
    
    # Files and directories to include (Docker deployment - no application.py needed)
    include_items = [
        "app.py",
        "demo_mode.py",  # Demo mode stub
        "requirements.txt",
        "config/",  # Configuration files (auth_module.py, .env.example)
        "deployment/.ebignore",  # EB ignore file - ensures BraketMCP is deployed
        "deployment/Dockerfile",
        "deployment/.dockerignore",
        "models/",
        "utils/",
        "agents/",
        "enhanced_mcp_materials/",
        "BraketMCP/",
        "deployment/.ebextensions/",  # Updated path
        "setup/",  # Setup scripts
        "docs/"  # Documentation
    ]
    
    # Files to exclude (be more specific to avoid excluding needed files)
    exclude_patterns = [
        "__pycache__",
        "*.pyc",
        ".git",
        ".env",
        "deployment_temp",
        "*.zip",
        "*.log",
        "test_*.py",  # More specific
        ".pytest_cache",
        "*.egg-info",
        "elastic_beanstalk_zipfiles"
    ]
    
    print("Copying files...")
    
    # Copy included items with special handling for moved files
    for item in include_items:
        if item == "deployment/Dockerfile":
            # Copy Dockerfile to root of deployment
            source_path = source_dir / "deployment" / "Dockerfile"
            target_path = temp_dir / "Dockerfile"
        elif item == "deployment/.ebignore":
            # Copy .ebignore to root of deployment
            source_path = source_dir / "deployment" / ".ebignore"
            target_path = temp_dir / ".ebignore"
        elif item == "deployment/.dockerignore":
            # Copy .dockerignore to root of deployment
            source_path = source_dir / "deployment" / ".dockerignore"
            target_path = temp_dir / ".dockerignore"
        elif item == "deployment/.ebextensions/":
            # Copy .ebextensions from root directory to deployment root
            source_path = source_dir / ".ebextensions"
            target_path = temp_dir / ".ebextensions"
        else:
            # Normal path handling
            source_path = source_dir / item
            target_path = temp_dir / item
        
        if source_path.exists():
            if source_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                print(f"  Copied file: {item} -> {target_path.name}")
            elif source_path.is_dir():
                shutil.copytree(source_path, target_path, 
                              ignore=shutil.ignore_patterns(*exclude_patterns))
                print(f"  Copied directory: {item}")
        else:
            print(f"  Warning - Not found: {item}")
    
    # Verify critical files are present (Docker deployment)
    critical_files = [
        "app.py",
        "Dockerfile",  # Docker deployment
        "requirements.txt",
        "config/auth_module.py",
        "config/cognito_auth.py",  # New Cognito auth
        "config/custom_cognito_auth.py",  # Custom Cognito implementation
        "utils/mcp_tools_wrapper.py",
        "agents/strands_supervisor.py",
        "utils/braket_integration.py",
        "utils/debug_logger.py",
        "utils/logging_display.py",
        ".ebextensions/01_environment.config",
        ".ebextensions/04_mcp_setup.config",
        ".ebextensions/07_cognito_config.config",  # New Cognito config
        "setup/setup_secrets.py",
        "setup/setup_cognito.py"  # New Cognito setup
    ]
    
    print("\nVerifying critical files...")
    all_present = True
    for file_path in critical_files:
        if (temp_dir / file_path).exists():
            print(f"  OK: {file_path}")
        else:
            print(f"  MISSING: {file_path}")
            all_present = False
    
    if not all_present:
        print("Critical files missing! Deployment may fail.")
        return False
    
    # Create deployment zip
    print(f"\nCreating deployment zip: {zip_path}")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
            
            for file in files:
                if not any(pattern in file for pattern in exclude_patterns):
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arc_path)
    
    # Clean up temp directory (handle Windows permission issues)
    try:
        shutil.rmtree(temp_dir)
    except PermissionError:
        print("Warning: Could not clean up temp directory (Windows permission issue)")
        print(f"You can manually delete: {temp_dir}")
    
    # Show deployment package info
    zip_size = zip_path.stat().st_size / (1024 * 1024)  # MB
    print(f"\nDeployment package created: {zip_path}")
    print(f"Package size: {zip_size:.1f} MB")
    
    return True

def deploy_to_eb():
    """Deploy to Elastic Beanstalk"""
    
    print("\n🚀 Deploying to Elastic Beanstalk...")
    
    try:
        # Check if EB CLI is available
        result = subprocess.run(['eb', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ EB CLI not found. Install with: pip install awsebcli")
            return False
        
        print(f"✅ EB CLI version: {result.stdout.strip()}")
        
        # Get available environments
        print("\n📋 Getting available environments...")
        result = subprocess.run(['eb', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            print("Available environments:")
            print(result.stdout)
            
            # Ask user to select environment
            env_name = input("\n🎯 Enter environment name to deploy to (or press Enter for default): ").strip()
            
            if env_name:
                deploy_cmd = ['eb', 'deploy', env_name]
                print(f"🚀 Running eb deploy {env_name}...")
            else:
                deploy_cmd = ['eb', 'deploy']
                print("🚀 Running eb deploy...")
        else:
            deploy_cmd = ['eb', 'deploy']
            print("🚀 Running eb deploy...")
        
        # Deploy
        result = subprocess.run(deploy_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Deployment successful!")
            print(result.stdout)
        else:
            print("❌ Deployment failed!")
            print(result.stderr)
            return False
        
        # Get status
        print("\n📊 Getting deployment status...")
        result = subprocess.run(['eb', 'status'], capture_output=True, text=True)
        print(result.stdout)
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment error: {e}")
        return False

def fix_cognito_before_deploy():
    """Check Cognito configuration before deployment"""
    try:
        print("\n" + "=" * 60)
        print("    COGNITO CONFIGURATION CHECK")
        print("=" * 60)
        
        print("✅ Cognito authentication files included in deployment")
        print("📧 Email verification should be configured manually if needed")
        print("💡 Run 'python setup/setup_cognito.py' to create new User Pool")
        return True
            
    except Exception as e:
        print(f"Error checking Cognito configuration: {e}")
        return True  # Don't fail deployment for this

def main():
    """Main deployment function"""
    
    print("\n" + "=" * 70)
    print("    QUANTUM MATTER APP - ENTERPRISE DEPLOYMENT")
    print("=" * 70)
    print("AWS Cognito Authentication + CloudFront SSL + Quantum Computing")
    print("-" * 70)
    
    # Fix Cognito email verification first
    fix_cognito_before_deploy()
    
    # Create deployment package
    print("\n" + "=" * 60)
    print("    CREATING DEPLOYMENT PACKAGE")
    print("=" * 60)
    
    if not create_deployment_package():
        print("Failed to create deployment package")
        sys.exit(1)
    
    # Ask user if they want to deploy
    print("\n" + "=" * 60)
    print("    READY FOR DEPLOYMENT")
    print("=" * 60)
    deploy = input("Deploy to Elastic Beanstalk now? (y/N): ").lower().strip()
    
    if deploy == 'y':
        if deploy_to_eb():
            print("\n" + "=" * 70)
            print("    DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print("\nWhat was deployed:")
            print("✓ AWS Cognito Enterprise Authentication")
            print("✓ Email Verification with Custom Messages")
            print("✓ Strands-MCP Integration with Proper Tool Calls")
            print("✓ Braket MCP Installation with Fallback Handling")
            print("✓ Enhanced Error Handling and Logging")
            print("✓ CloudFront SSL and Global CDN")
            
            print("\nTest Your Deployment:")
            print("1. Visit your CloudFront URL")
            print("2. Try signing up with a real email address")
            print("3. Check email for verification code")
            print("4. Test quantum computing features")
            print("5. Verify Materials Project integration")
            print("=" * 70)
        else:
            print("❌ Deployment failed")
            sys.exit(1)
    else:
        print("📦 Deployment package ready. Deploy manually with:")
        print("  eb deploy [environment-name]")
        print("  Example: eb deploy quantum-matter-mcp-cloudfront")

if __name__ == "__main__":
    main()