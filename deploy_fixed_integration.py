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
    
    print("🚀 Creating fixed deployment package...")
    
    # Define source and target directories
    source_dir = Path(__file__).parent
    temp_dir = source_dir / "deployment_temp"
    zip_path = source_dir / "quantum_matter_app_fixed.zip"
    
    # Clean up previous builds
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    if zip_path.exists():
        zip_path.unlink()
    
    # Create temp directory
    temp_dir.mkdir()
    
    # Files and directories to include
    include_items = [
        "app.py",
        "application.py",  # EB entry point
        "requirements.txt",
        "demo_mode.py",
        "auth_module.py",  # Authentication module
        ".env.example",
        ".ebignore",  # EB ignore file - ensures BraketMCP is deployed
        "Dockerfile",
        ".dockerignore",
        "models/",
        "utils/",
        "agents/",
        "enhanced_mcp_materials/",
        "BraketMCP/",
        ".ebextensions/"
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
    
    print("📦 Copying files...")
    
    # Copy included items
    for item in include_items:
        source_path = source_dir / item
        target_path = temp_dir / item
        
        if source_path.exists():
            if source_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                print(f"  ✅ Copied file: {item}")
            elif source_path.is_dir():
                shutil.copytree(source_path, target_path, 
                              ignore=shutil.ignore_patterns(*exclude_patterns))
                print(f"  ✅ Copied directory: {item}")
        else:
            print(f"  ⚠️ Not found: {item}")
    
    # Verify critical files are present
    critical_files = [
        "app.py",
        "application.py",
        "requirements.txt",
        "auth_module.py",
        "demo_mode.py",
        "utils/mcp_tools_wrapper.py",
        "agents/strands_supervisor.py",
        "utils/braket_integration.py",
        "utils/debug_logger.py",
        "utils/logging_display.py",
        ".ebextensions/01_environment.config",
        ".ebextensions/04_mcp_setup.config"
    ]
    
    print("\n🔍 Verifying critical files...")
    all_present = True
    for file_path in critical_files:
        if (temp_dir / file_path).exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ MISSING: {file_path}")
            all_present = False
    
    if not all_present:
        print("❌ Critical files missing! Deployment may fail.")
        return False
    
    # Create deployment zip
    print(f"\n📦 Creating deployment zip: {zip_path}")
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
    print(f"\n✅ Deployment package created: {zip_path}")
    print(f"📊 Package size: {zip_size:.1f} MB")
    
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
        
        # Deploy
        print("🚀 Running eb deploy...")
        result = subprocess.run(['eb', 'deploy'], capture_output=True, text=True)
        
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

def main():
    """Main deployment function"""
    
    print("Quantum Matter App - Fixed Integration Deployment")
    print("=" * 60)
    
    # Create deployment package
    if not create_deployment_package():
        print("❌ Failed to create deployment package")
        sys.exit(1)
    
    # Ask user if they want to deploy
    deploy = input("\n🚀 Deploy to Elastic Beanstalk now? (y/N): ").lower().strip()
    
    if deploy == 'y':
        if deploy_to_eb():
            print("\n🎉 Deployment completed successfully!")
            print("\n📋 What was fixed:")
            print("  ✅ Strands-MCP integration with proper tool calls")
            print("  ✅ Braket MCP installation with fallback handling")
            print("  ✅ Correct Strands package versions (strands-agents>=1.17.0)")
            print("  ✅ MCP tools wrapper for easier integration")
            print("  ✅ Improved error handling and logging")
            
            print("\n🔗 Test your deployment:")
            print("  1. Check the main app functionality")
            print("  2. Test Strands agent with material queries")
            print("  3. Verify MCP tools are being called")
            print("  4. Test Braket integration (if available)")
        else:
            print("❌ Deployment failed")
            sys.exit(1)
    else:
        print("📦 Deployment package ready. Deploy manually with:")
        print("  eb deploy")

if __name__ == "__main__":
    main()