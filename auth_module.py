"""
Simple authentication for Streamlit app
"""
import streamlit as st
import os

# Demo credentials from environment variables (no fallbacks for security)
DEMO_USERS = {}
if os.getenv("DEMO_USERNAME") and os.getenv("DEMO_PASSWORD"):
    DEMO_USERS[os.getenv("DEMO_USERNAME")] = os.getenv("DEMO_PASSWORD")

def require_auth():
    """Simple authentication handler"""
    
    # Check if user is already authenticated
    if 'authenticated' in st.session_state and st.session_state.authenticated:
        return True
    
    # Show login page
    st.title("🔐 Quantum Matter LLM Platform - Login")
    
    # Simple authentication form
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not DEMO_USERS:
                st.error("❌ Authentication not configured. Set DEMO_USERNAME and DEMO_PASSWORD environment variables.")
            elif username in DEMO_USERS and DEMO_USERS[username] == password:
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("✅ Login successful!")
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
    
    return False