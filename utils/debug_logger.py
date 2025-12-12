"""
Debug logging utilities for capturing detailed MCP processing information
"""
import streamlit as st
import logging
from typing import List, Dict, Any
from datetime import datetime

class DebugLogger:
    """Captures and formats detailed processing logs for debug view"""
    
    def __init__(self):
        self.logs = []
        self.mcp_calls = []
        self.processing_steps = []
    
    def log_mcp_call(self, tool_name: str, description: str, result: Any = None):
        """Log an MCP tool call"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'mcp_call',
            'tool': tool_name,
            'description': description,
            'result': result
        }
        
        self.mcp_calls.append(log_entry)
        self.logs.append(log_entry)
    
    def log_processing_step(self, step: str, details: str = None):
        """Log a processing step"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        log_entry = {
            'timestamp': timestamp,
            'type': 'processing',
            'step': step,
            'details': details
        }
        
        self.processing_steps.append(log_entry)
        self.logs.append(log_entry)
    
    def log_material_extraction(self, formula: str, source: str):
        """Log material formula extraction"""
        self.log_processing_step(
            f"✅ Formula extracted: {formula}",
            f"Source: {source}"
        )
    
    def log_data_parsing(self, data_type: str, value: Any):
        """Log data parsing results"""
        self.log_processing_step(
            f"✅ {data_type} extracted: {value}",
            f"Parsed from MCP response"
        )
    
    def log_mcp_response(self, tool_number: int, description: str, items_count: int = None):
        """Log MCP response details"""
        if items_count:
            self.log_mcp_call(
                f"MCP Tool {tool_number}",
                f"{description}",
                f"📋 Raw MCP response: {items_count} items received"
            )
        else:
            self.log_mcp_call(
                f"MCP Tool {tool_number}",
                description
            )
    
    def log_structure_uri(self, uri: str):
        """Log structure URI"""
        self.log_processing_step(
            f"🔗 Structure URI: {uri}",
            "Retrieved from Materials Project"
        )
    
    def log_timeout_protection(self, operation: str, timeout_seconds: int):
        """Log timeout protection"""
        self.log_processing_step(
            f"⏰ Timeout protection: {timeout_seconds} second limit for {operation}",
            "Preventing long-running operations"
        )
    
    def log_geometry_extraction(self, char_count: int):
        """Log geometry data extraction"""
        self.log_processing_step(
            f"🧬 Geometry extracted: {char_count} chars",
            "Atomic coordinates processed"
        )
    
    def log_final_data(self, data_keys: List[str]):
        """Log final structured data"""
        self.log_processing_step(
            f"📊 Final parsed data keys: {data_keys}",
            "Complete dataset ready for LLM"
        )
    
    def format_debug_output(self) -> str:
        """Format all logs for debug display"""
        if not self.logs:
            return "No debug information available"
        
        output = []
        
        # Group logs by type
        mcp_logs = [log for log in self.logs if log['type'] == 'mcp_call']
        processing_logs = [log for log in self.logs if log['type'] == 'processing']
        
        # Format MCP calls
        if mcp_logs:
            output.append("### 🔍 MCP Tool Calls")
            for i, log in enumerate(mcp_logs, 1):
                output.append(f"**{log['timestamp']}** - 🔍 {log['tool']}: {log['description']}")
                if log.get('result'):
                    output.append(f"   {log['result']}")
        
        # Format processing steps
        if processing_logs:
            output.append("### ⚙️ Processing Steps")
            for log in processing_logs:
                output.append(f"**{log['timestamp']}** - {log['step']}")
                if log.get('details'):
                    output.append(f"   _{log['details']}_")
        
        return "\n\n".join(output)
    
    def display_in_streamlit(self):
        """Display debug logs in Streamlit"""
        if not self.logs:
            st.info("No debug information captured")
            return
        
        # Show MCP activity
        mcp_logs = [log for log in self.logs if log['type'] == 'mcp_call']
        if mcp_logs:
            st.markdown("#### 🔍 MCP Activity Log")
            for log in mcp_logs:
                with st.container():
                    st.markdown(f"**{log['timestamp']}** - {log['description']}")
                    if log.get('result'):
                        st.code(log['result'], language="text")
        
        # Show processing steps
        processing_logs = [log for log in self.logs if log['type'] == 'processing']
        if processing_logs:
            st.markdown("#### ⚙️ Processing Steps")
            for log in processing_logs:
                st.markdown(f"**{log['timestamp']}** - {log['step']}")
                if log.get('details'):
                    st.caption(log['details'])
    
    def clear(self):
        """Clear all logs"""
        self.logs.clear()
        self.mcp_calls.clear()
        self.processing_steps.clear()

# Global debug logger instance
debug_logger = DebugLogger()

def get_debug_logger() -> DebugLogger:
    """Get the global debug logger instance"""
    return debug_logger

def simulate_mcp_processing_logs(material_id: str = "mp-2657", formula: str = "Ti4 O8"):
    """Simulate the detailed MCP processing logs for demo purposes"""
    logger = get_debug_logger()
    logger.clear()
    
    # Simulate the processing sequence you showed
    logger.log_mcp_response(2, f"Getting material data for ID: {material_id}", 2)
    logger.log_structure_uri(f"structure://{material_id}")
    logger.log_processing_step("🔍 Raw MCP Description: Structure Information [ENHANCED]")
    
    # Material data extraction
    logger.log_processing_step(
        f"Material id: {material_id} Formula: {formula}Spacegroup: P4_2/mnm (#136) Crystal System: tetragonal Band Gap: 1.781 eV Formation Energy: -3.464 eV/atom Lattice Parameters: a=5.4695, b=5.4695, c=5.4695 Angles: alpha=114.4913, beta=107.0185, gamma=107.0237 Number of atoms: 12 ..."
    )
    
    # Data extraction steps
    logger.log_material_extraction(f"{formula}Spacegroup: P4_2/mnm (#136)", "MCP response parsing")
    logger.log_data_parsing("Band Gap", "1.781 eV")
    logger.log_data_parsing("Formation Energy", "-3.464 eV/atom")
    logger.log_data_parsing("Crystal System", "tetragonal")
    
    # Final data keys
    data_keys = ['material_id', 'structure_uri', 'source', 'formula', 'band_gap', 'formation_energy', 'crystal_system']
    logger.log_final_data(data_keys)
    
    # POSCAR generation
    logger.log_mcp_response(3, f"Getting POSCAR data for structure://{material_id}")
    logger.log_timeout_protection("POSCAR generation", 60)
    logger.log_processing_step("✅ Retrieved POSCAR data: 1045 characters")
    logger.log_geometry_extraction(86)
    
    # Final structured data
    final_data = {
        'material_id': material_id,
        'structure_uri': f'structure://{material_id}',
        'source': 'MCP Materials Project Server',
        'formula': f'{formula}Spacegroup: P4_2/mnm (#136)',
        'band_gap': 1.781,
        'formation_energy': -3.464,
        'crystal_system': 'tetragonal',
        'geometry': 'Ti 2.715 4.072 4.072; O 2.715 1.358 1.358; Ti -0.000 0.000 2.715; O -0.000 2.715 0.000'
    }
    
    logger.log_processing_step(
        f"✅ Final structured data for LLM: {str(final_data)[:100]}...",
        "Complete dataset ready for model processing"
    )
    
    return logger