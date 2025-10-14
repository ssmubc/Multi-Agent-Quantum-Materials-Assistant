#!/usr/bin/env python3
"""
Quantum Matter LLM Testing Platform
Run script with environment setup and error handling
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'boto3',
        'qiskit',
        'numpy',
        'scipy'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def check_aws_config():
    """Check basic AWS configuration"""
    aws_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_PROFILE']
    has_aws_config = any(os.getenv(var) for var in aws_vars)
    
    if not has_aws_config:
        logger.warning("No AWS credentials detected in environment variables")
        logger.info("Configure AWS credentials using one of these methods:")
        logger.info("1. aws configure")
        logger.info("2. Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY")
        logger.info("3. Set AWS_PROFILE")
        logger.info("4. Use IAM roles (if running on EC2)")
    
    return has_aws_config

def main():
    """Main entry point"""
    logger.info("Starting Quantum Matter LLM Testing Platform...")
    
    # Check current directory
    current_dir = Path.cwd()
    app_file = current_dir / "app.py"
    
    if not app_file.exists():
        logger.error(f"app.py not found in {current_dir}")
        logger.info("Make sure you're running this from the app directory")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check AWS configuration
    check_aws_config()
    
    # Set environment variables for better Streamlit experience
    os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
    os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
    
    # Run Streamlit app
    try:
        logger.info("Launching Streamlit app...")
        logger.info("Access the app at: http://localhost:8501")
        
        cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
        subprocess.run(cmd, check=True)
        
    except KeyboardInterrupt:
        logger.info("App stopped by user")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running Streamlit: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()