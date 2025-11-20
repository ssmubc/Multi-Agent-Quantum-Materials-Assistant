#!/usr/bin/env python3
"""
Elastic Beanstalk entry point for Quantum Materials Platform
This file is required for EB deployment
"""

import os
import sys
import subprocess

# Set environment for Streamlit
os.environ['STREAMLIT_SERVER_PORT'] = '8501'
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'

def application(environ, start_response):
    """WSGI application entry point for Elastic Beanstalk"""
    
    # Start Streamlit app
    try:
        # Run Streamlit in the background
        subprocess.Popen([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.port=8501',
            '--server.address=0.0.0.0',
            '--server.headless=true',
            '--server.enableCORS=false'
        ])
        
        # Simple WSGI response
        status = '200 OK'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [b'Quantum Materials Platform is starting...']
        
    except Exception as e:
        status = '500 Internal Server Error'
        headers = [('Content-type', 'text/plain')]
        start_response(status, headers)
        return [f'Error starting application: {str(e)}'.encode()]

if __name__ == '__main__':
    # For local testing
    import subprocess
    subprocess.run([
        sys.executable, '-m', 'streamlit', 'run', 'app.py',
        '--server.port=8501'
    ])