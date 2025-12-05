"""
MCP Server Monitoring and Debugging Utility
"""
import logging
import time
import psutil
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MCPServerMonitor:
    """Monitor MCP server health and performance"""
    
    def __init__(self):
        self.start_time = time.time()
        self.call_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.timeout_count = 0
        self.restart_count = 0
        self.last_health_check = 0
        
    def log_call_start(self, tool_name: str, arguments: Dict[str, Any]):
        """Log the start of an MCP call"""
        self.call_count += 1
        logger.info(f"📊 MCP MONITOR: Call #{self.call_count} - {tool_name} started")
        
    def log_call_success(self, tool_name: str, response_size: int = 0):
        """Log successful MCP call"""
        self.success_count += 1
        logger.info(f"✅ MCP MONITOR: {tool_name} succeeded (response: {response_size} items)")
        
    def log_call_failure(self, tool_name: str, error: str):
        """Log failed MCP call"""
        self.failure_count += 1
        logger.error(f"❌ MCP MONITOR: {tool_name} failed - {error}")
        
    def log_call_timeout(self, tool_name: str, timeout_seconds: int):
        """Log timeout MCP call"""
        self.timeout_count += 1
        logger.error(f"⏰ MCP MONITOR: {tool_name} timed out after {timeout_seconds}s")
        
    def log_server_restart(self, reason: str):
        """Log server restart"""
        self.restart_count += 1
        logger.warning(f"🔄 MCP MONITOR: Server restart #{self.restart_count} - {reason}")
        
    def get_stats(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        uptime = time.time() - self.start_time
        success_rate = (self.success_count / self.call_count * 100) if self.call_count > 0 else 0
        
        return {
            "uptime_seconds": uptime,
            "uptime_minutes": uptime / 60,
            "total_calls": self.call_count,
            "successful_calls": self.success_count,
            "failed_calls": self.failure_count,
            "timeout_calls": self.timeout_count,
            "server_restarts": self.restart_count,
            "success_rate_percent": success_rate,
            "calls_per_minute": (self.call_count / (uptime / 60)) if uptime > 0 else 0
        }
        
    def log_stats(self):
        """Log current statistics"""
        stats = self.get_stats()
        logger.info(f"📊 MCP MONITOR STATS:")
        logger.info(f"   Uptime: {stats['uptime_minutes']:.1f} minutes")
        logger.info(f"   Total calls: {stats['total_calls']}")
        logger.info(f"   Success rate: {stats['success_rate_percent']:.1f}%")
        logger.info(f"   Server restarts: {stats['server_restarts']}")
        logger.info(f"   Calls per minute: {stats['calls_per_minute']:.1f}")
        
    def check_system_resources(self) -> Dict[str, Any]:
        """Check system resources that might affect MCP server"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Check for MCP server processes
            mcp_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    if proc.info['cmdline'] and any('mcp' in arg.lower() for arg in proc.info['cmdline']):
                        mcp_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cpu_percent': proc.info['cpu_percent'],
                            'memory_percent': proc.info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "mcp_processes": mcp_processes
            }
        except Exception as e:
            logger.error(f"💥 MCP MONITOR: Failed to check system resources: {e}")
            return {}
    
    def log_system_resources(self):
        """Log system resource usage"""
        resources = self.check_system_resources()
        if resources:
            logger.info(f"🖥️ MCP MONITOR RESOURCES:")
            logger.info(f"   CPU: {resources.get('cpu_percent', 0):.1f}%")
            logger.info(f"   Memory: {resources.get('memory_percent', 0):.1f}% ({resources.get('memory_available_gb', 0):.1f}GB free)")
            logger.info(f"   Disk: {resources.get('disk_percent', 0):.1f}% ({resources.get('disk_free_gb', 0):.1f}GB free)")
            logger.info(f"   MCP processes: {len(resources.get('mcp_processes', []))}")
            
    def health_check(self, force: bool = False) -> bool:
        """Perform periodic health check"""
        current_time = time.time()
        if not force and (current_time - self.last_health_check) < 30:  # Check every 30 seconds
            return True
            
        self.last_health_check = current_time
        
        # Log stats every health check
        self.log_stats()
        self.log_system_resources()
        
        # Check for concerning patterns
        stats = self.get_stats()
        if stats['success_rate_percent'] < 50 and stats['total_calls'] > 5:
            logger.warning(f"⚠️ MCP MONITOR: Low success rate detected: {stats['success_rate_percent']:.1f}%")
            return False
            
        if stats['server_restarts'] > 3:
            logger.warning(f"⚠️ MCP MONITOR: High restart count: {stats['server_restarts']}")
            return False
            
        return True

# Global monitor instance
mcp_monitor = MCPServerMonitor()

def get_mcp_monitor() -> MCPServerMonitor:
    """Get the global MCP monitor instance"""
    return mcp_monitor