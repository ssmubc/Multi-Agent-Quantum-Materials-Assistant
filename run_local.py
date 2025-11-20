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
if not os.environ.get('AWS_PROFILE'):
    os.environ['AWS_PROFILE'] = 'your-aws-profile-name'

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

print("Setting up local environment...")
print("Demo credentials: demo / quantum2025")
print("AWS Profile: deploy-quantum")
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