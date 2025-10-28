"""
Logging display utilities for Streamlit
"""
import streamlit as st
import logging
from io import StringIO
import sys

class StreamlitLogHandler(logging.Handler):
    """Custom log handler that captures logs for Streamlit display"""
    
    def __init__(self):
        super().__init__()
        self.log_buffer = StringIO()
        self.logs = []
        
    def emit(self, record):
        """Emit a log record"""
        try:
            msg = self.format(record)
            self.logs.append({
                'level': record.levelname,
                'message': msg,
                'timestamp': record.created
            })
            # Keep only last 50 logs
            if len(self.logs) > 50:
                self.logs = self.logs[-50:]
            
            # Print to console for terminal visibility
            if 'MCP' in msg:
                try:
                    print(f"[MCP LOG] {msg}", flush=True)
                except UnicodeEncodeError:
                    # Fallback for Unicode issues
                    clean_msg = msg.encode('ascii', 'ignore').decode('ascii')
                    print(f"[MCP LOG] {clean_msg}", flush=True)
        except Exception:
            self.handleError(record)
    
    def get_logs(self):
        """Get all captured logs"""
        return self.logs
    
    def get_mcp_logs(self):
        """Get only MCP-related logs"""
        return [log for log in self.logs if 'MCP' in log['message']]

# Global log handler instance
_log_handler = None

def setup_logging_display():
    """Setup logging to capture for Streamlit display"""
    global _log_handler
    
    if _log_handler is None:
        _log_handler = StreamlitLogHandler()
        _log_handler.setLevel(logging.INFO)
        
        # Set formatter
        formatter = logging.Formatter('%(message)s')
        _log_handler.setFormatter(formatter)
        
        # Add to root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(_log_handler)
        
        # Also add to specific loggers
        for logger_name in ['enhanced_mcp_client', 'app', 'utils.enhanced_mcp_client']:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.INFO)
            logger.addHandler(_log_handler)
    
    return _log_handler

def display_mcp_logs():
    """Display MCP-related logs in Streamlit"""
    handler = setup_logging_display()
    mcp_logs = handler.get_mcp_logs()
    
    if mcp_logs:
        st.subheader("🔍 MCP Activity Log")
        
        # Show last 10 MCP logs
        recent_logs = mcp_logs[-10:]
        
        for log in reversed(recent_logs):  # Show newest first
            level = log['level']
            message = log['message']
            
            # Color code by level
            if level == 'INFO':
                if '🚀' in message or '✅' in message:
                    st.success(f"**{level}:** {message}")
                else:
                    st.info(f"**{level}:** {message}")
            elif level == 'WARNING':
                st.warning(f"**{level}:** {message}")
            elif level == 'ERROR':
                st.error(f"**{level}:** {message}")
            else:
                st.text(f"**{level}:** {message}")
    else:
        st.info("No MCP activity detected yet. Check 'Include Materials Project data' and submit a query.")

def display_all_logs():
    """Display all captured logs"""
    handler = setup_logging_display()
    all_logs = handler.get_logs()
    
    if all_logs:
        st.subheader("📋 All Activity Logs")
        
        # Show last 20 logs
        recent_logs = all_logs[-20:]
        
        for log in reversed(recent_logs):  # Show newest first
            level = log['level']
            message = log['message']
            
            # Color code by level
            if level == 'INFO':
                st.info(f"**{level}:** {message}")
            elif level == 'WARNING':
                st.warning(f"**{level}:** {message}")
            elif level == 'ERROR':
                st.error(f"**{level}:** {message}")
            else:
                st.text(f"**{level}:** {message}")