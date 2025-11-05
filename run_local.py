#!/usr/bin/env python3
"""
Local development runner with auth bypass
"""
import os
import sys
import subprocess

# Set demo credentials for local testing
os.environ['DEMO_USERNAME'] = 'demo'
os.environ['DEMO_PASSWORD'] = 'quantum2025'
os.environ['AWS_PROFILE'] = 'qmi_streamlit'

# Set Materials Project API key for local development
# You need to get a NEW 32-character API key from https://materialsproject.org/api
# The old 16-character keys don't work with the new mp-api
if not os.environ.get('MP_API_KEY'):
    print("\n[WARNING] No MP_API_KEY found!")
    print("Please get a NEW 32-character API key from: https://materialsproject.org/api")
    print("Then set it with: set MP_API_KEY=your_32_character_key")
    print("\nFor now, using a placeholder key (MCP will fail)...")
    os.environ['MP_API_KEY'] = 'placeholder_key_get_real_32char_key_from_materialsproject_org'

# Fix MCP server Python path for local development
os.environ['MCP_PYTHON_PATH'] = sys.executable
os.environ['PYTHONPATH'] = os.getcwd() + os.pathsep + os.path.join(os.getcwd(), 'enhanced_mcp_materials')

print("Setting up local environment...")
print("Demo credentials: demo / quantum2025")
print(f"MP_API_KEY: {'SET' if len(os.environ.get('MP_API_KEY', '')) == 32 else 'MISSING/INVALID'}")
if len(os.environ.get('MP_API_KEY', '')) != 32:
    print("\n[ERROR] MCP will timeout because MP_API_KEY is missing or invalid!")
    print("Get a 32-character key from: https://materialsproject.org/api")
    print("Then run: set MP_API_KEY=your_key && python run_local.py\n")
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
os.environ['USE_DUMMY_MP_DATA'] = '1'  # Bypass MP API hanging locally
print("[INFO] Local development mode enabled with dummy MP data (bypasses API hanging)")

# Run streamlit
try:
    print("Starting Streamlit...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
except KeyboardInterrupt:
    print("\nStopped by user")
except Exception as e:
    print(f"Error: {e}")