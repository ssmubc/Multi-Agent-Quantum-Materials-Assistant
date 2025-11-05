#!/usr/bin/env python3
"""
Deploy script to ensure MCP materials package is included
"""
import os
import zipfile
import subprocess
import sys
from pathlib import Path

def create_deployment_zip():
    """Create deployment zip with all necessary files including MCP materials"""
    
    # Files and directories to include
    include_patterns = [
        "*.py",
        "*.txt", 
        "*.toml",
        "*.md",
        "*.yml",
        "*.yaml",
        "*.json",
        "Dockerfile",
        "Dockerrun.aws.json",
        ".streamlit/",
        ".ebextensions/",
        "models/",
        "utils/", 
        "agents/",
        "auth/",
        "enhanced_mcp_materials/",  # Critical: include MCP package
    ]
    
    # Files to exclude
    exclude_patterns = [
        "__pycache__/",
        "*.pyc",
        ".git/",
        ".elasticbeanstalk/",
        "elastic_beanstalk_zipfiles/",
        "MaterialProjectMCP/",
        "simple_mcp_materials/",
        "*.zip",
        "*.exe",
        "*.key",
        "*.crt",
        ".env",
        "run_app.bat",
        "vs_buildtools.exe"
    ]
    
    zip_name = "quantum-matter-app-mcp-fixed.zip"
    
    print(f"🚀 Creating deployment zip: {zip_name}")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk('.'):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(d.startswith(pattern.rstrip('/')) for pattern in exclude_patterns)]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, '.')
                
                # Skip excluded files
                if any(pattern in rel_path for pattern in exclude_patterns):
                    continue
                
                # Include files matching patterns
                if any(rel_path.endswith(pattern.lstrip('*')) or pattern.rstrip('/') in rel_path for pattern in include_patterns):
                    print(f"  ✅ Adding: {rel_path}")
                    zipf.write(file_path, rel_path)
    
    print(f"✅ Created {zip_name}")
    
    # Verify MCP package is included
    with zipfile.ZipFile(zip_name, 'r') as zipf:
        files = zipf.namelist()
        mcp_files = [f for f in files if 'enhanced_mcp_materials' in f]
        
        if mcp_files:
            print(f"✅ MCP package included ({len(mcp_files)} files):")
            for f in mcp_files[:5]:  # Show first 5
                print(f"    {f}")
            if len(mcp_files) > 5:
                print(f"    ... and {len(mcp_files) - 5} more")
        else:
            print("❌ ERROR: MCP package NOT included!")
            return False
    
    return zip_name

def deploy_to_eb(zip_name):
    """Deploy to Elastic Beanstalk"""
    print(f"🚀 Deploying {zip_name} to Elastic Beanstalk...")
    
    try:
        # Upload and deploy
        result = subprocess.run([
            'eb', 'deploy', '--staged'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Deployment successful!")
            print(result.stdout)
        else:
            print("❌ Deployment failed!")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ EB CLI not found. Install with: pip install awsebcli")
        return False
    
    return True

if __name__ == "__main__":
    print("🔧 MCP Materials Deployment Script")
    print("=" * 50)
    
    # Change to script directory
    os.chdir(Path(__file__).parent)
    
    # Create deployment zip
    zip_name = create_deployment_zip()
    if not zip_name:
        sys.exit(1)
    
    # Ask user if they want to deploy
    deploy = input(f"\n📤 Deploy {zip_name} to Elastic Beanstalk? (y/n): ").lower().strip()
    
    if deploy == 'y':
        if deploy_to_eb(zip_name):
            print("\n🎉 Deployment complete! MCP server should now work.")
        else:
            print(f"\n📁 Manual upload: Use {zip_name} in AWS Console")
    else:
        print(f"\n📁 Manual deployment: Upload {zip_name} to AWS Elastic Beanstalk Console")