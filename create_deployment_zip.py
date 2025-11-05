#!/usr/bin/env python3
"""
Create deployment ZIP for Quantum Matter LLM Platform
Includes all necessary files and excludes development files
"""

import zipfile
import os
from pathlib import Path

def create_deployment_zip():
    """Create deployment ZIP with all required files"""
    
    # Files and directories to include (exact requirements)
    include_files = [
        'app.py',
        'requirements.txt',
        'requirements_minimal.txt',
        'Dockerfile',
        'Dockerrun.aws.json',
        '.dockerignore',
        'demo_mode.py',
        'auth_module.py',
        'test_mcp_deployment.py',
        'DEPLOYMENT_FIX_INSTRUCTIONS.md'
    ]
    
    include_dirs = [
        'models/',
        'agents/', 
        'utils/',
        'enhanced_mcp_materials/',  # Critical: MCP server package (flattened with setup.py)
        '.ebextensions/',
        '.streamlit/'
    ]
    
    # Files and directories to exclude
    exclude_patterns = [
        '.git',
        '.venv', 
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.env',
        'elastic_beanstalk_zipfiles',
        '*.log',
        'vs_buildtools.exe',
        '.pytest_cache',
        'node_modules',
        '.elasticbeanstalk',
        'MaterialProjectMCP',
        'simple_mcp_materials',   # Remove this, keep only enhanced_mcp_materials
        'local_server.py',        # Exclude local development files
        'local_client.py',        # Exclude local development files
        'oldserver.py',           # Exclude backup files
        'oldclient.py',           # Exclude backup files
        'elasticserver.py',       # Exclude old renamed files
        'elasticclient.py',       # Exclude old renamed files
        'local_mcp_patch.py',     # Exclude local MCP patches
        'local_mcp_wrapper.py',   # Exclude local MCP wrappers
        'mcp_materials_client.py', # Exclude old MCP client (not used)
        'server_debug.py',        # Exclude debug server files
        'server_minimal.py',      # Exclude minimal server files
        'server_raw.py',          # Exclude raw server files
        'server_working.py'       # Exclude working server files
    ]
    
    zip_filename = 'quantum-matter-cloudfront-deployment.zip'
    
    print(f"Creating deployment ZIP: {zip_filename}")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Add individual files
        for file_path in include_files:
            if os.path.exists(file_path):
                zipf.write(file_path)
                print(f"[OK] Added file: {file_path}")
            else:
                print(f"[WARN] File not found: {file_path}")
        
        # Add directories
        for dir_path in include_dirs:
            if os.path.exists(dir_path):
                for root, dirs, files in os.walk(dir_path):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                    
                    for file in files:
                        # Skip excluded files
                        if not any(pattern in file for pattern in exclude_patterns):
                            file_path = os.path.join(root, file)
                            arcname = file_path.replace('\\', '/')  # Use forward slashes in ZIP
                            zipf.write(file_path, arcname)
                            print(f"[OK] Added: {arcname}")
                
                print(f"[OK] Added directory: {dir_path}")
            else:
                print(f"[WARN] Directory not found: {dir_path}")
    
    # Verify MCP package is included (AWS deployment)
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        files = zipf.namelist()
        mcp_files = [f for f in files if 'enhanced_mcp_materials' in f]
        aws_server = [f for f in files if 'aws_server.py' in f]
        aws_client = [f for f in files if 'aws_client.py' in f]
        dispatcher = [f for f in files if 'enhanced_mcp_materials/server.py' in f]
        
        print(f"\n[VERIFICATION] MCP package for AWS deployment:")
        print(f"  - MCP files: {len(mcp_files)}")
        print(f"  - AWS server: {'✅' if aws_server else '❌'}")
        print(f"  - AWS client: {'✅' if aws_client else '❌'}")
        print(f"  - Dispatcher: {'✅' if dispatcher else '❌'}")
        
        # Check for excluded local files
        local_files = [f for f in files if any(x in f for x in [
            'local_server.py', 'local_client.py', 'oldserver.py', 'oldclient.py',
            'local_mcp_patch.py', 'local_mcp_wrapper.py', 'elasticserver.py', 'elasticclient.py',
            'mcp_materials_client.py', 'server_debug.py', 'server_minimal.py', 'server_raw.py', 'server_working.py'
        ])]
        if local_files:
            print(f"\n[WARNING] Local development files found (should be excluded):")
            for f in local_files:
                print(f"    {f}")
        else:
            print(f"\n[OK] No local development files included")
        
        if aws_server and aws_client and dispatcher:
            print(f"\n[SUCCESS] AWS deployment package ready")
        else:
            print(f"\n[ERROR] Missing critical AWS files - deployment will fail!")
    
    print(f"\n[SUCCESS] Deployment ZIP created: {zip_filename}")
    print(f"[INFO] Size: {os.path.getsize(zip_filename) / 1024 / 1024:.2f} MB")
    
    return zip_filename

if __name__ == "__main__":
    create_deployment_zip()