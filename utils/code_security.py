"""
Code security utilities for safe code handling
"""
import re
import ast
from typing import List, Dict, Any

class CodeSecurityValidator:
    """Validates generated code for security risks"""
    
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'eval', 'exec', 'compile',
        'open', '__import__', 'globals', 'locals', 'vars',
        'getattr', 'setattr', 'delattr', 'hasattr'
    }
    
    DANGEROUS_FUNCTIONS = {
        'eval', 'exec', 'compile', 'input', 'raw_input',
        'file', 'execfile', 'reload', '__import__'
    }
    
    @classmethod
    def validate_code_safety(cls, code: str) -> Dict[str, Any]:
        """Validate code for security risks without execution"""
        issues = []
        
        # Check for dangerous imports
        import_pattern = r'(?:from\s+(\w+)|import\s+(\w+))'
        imports = re.findall(import_pattern, code, re.IGNORECASE)
        
        for imp in imports:
            module = imp[0] or imp[1]
            if module.lower() in cls.DANGEROUS_IMPORTS:
                issues.append(f"Dangerous import detected: {module}")
        
        # Check for dangerous function calls
        for func in cls.DANGEROUS_FUNCTIONS:
            if re.search(rf'\b{func}\s*\(', code, re.IGNORECASE):
                issues.append(f"Dangerous function call: {func}")
        
        # Check for file operations
        file_ops = ['open(', 'file(', 'with open']
        for op in file_ops:
            if op in code.lower():
                issues.append(f"File operation detected: {op}")
        
        # Check for network operations
        network_patterns = [
            r'urllib', r'requests', r'socket', r'http',
            r'ftp', r'smtp', r'telnet'
        ]
        for pattern in network_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                issues.append(f"Network operation detected: {pattern}")
        
        return {
            'is_safe': len(issues) == 0,
            'issues': issues,
            'risk_level': 'HIGH' if issues else 'LOW'
        }
    
    @classmethod
    def sanitize_code_display(cls, code: str) -> str:
        """Sanitize code for safe display only"""
        if not code:
            return ""
        
        # Add security warning header
        warning = "# WARNING: This is generated code for DISPLAY ONLY\n"
        warning += "# DO NOT EXECUTE without proper security review\n"
        warning += "# Review all imports and function calls before use\n\n"
        
        return warning + code
    
    @classmethod
    def get_safe_code_guidelines(cls) -> str:
        """Return security guidelines for code usage"""
        return """
## 🔒 Code Security Guidelines

**IMPORTANT: Generated code is for educational/reference purposes only**

### Before Using Generated Code:
1. **Review all imports** - Remove unnecessary system imports
2. **Check function calls** - Verify no dangerous operations
3. **Test in sandbox** - Use isolated environment first
4. **Validate inputs** - Ensure all parameters are safe
5. **Use virtual environment** - Isolate dependencies

### Prohibited Operations:
- File system access (`open`, `os` module)
- System commands (`subprocess`, `os.system`)
- Network operations (`requests`, `urllib`)
- Dynamic code execution (`eval`, `exec`)

### Recommended Practice:
- Copy code to secure development environment
- Review with security team if applicable
- Test with minimal privileges
- Use containerized execution when possible
"""

def validate_generated_code(code: str) -> Dict[str, Any]:
    """Main function to validate generated code"""
    return CodeSecurityValidator.validate_code_safety(code)

def get_secure_code_display(code: str) -> str:
    """Get code with security warnings for display"""
    return CodeSecurityValidator.sanitize_code_display(code)