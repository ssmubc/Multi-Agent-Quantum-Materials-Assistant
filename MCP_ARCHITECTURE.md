# MCP Architecture Organization

## Overview
The MCP (Model Context Protocol) system is now organized for clear separation between local development and AWS deployment environments.

## File Structure

### Server Components
- **`enhanced_mcp_materials/server.py`** - Dispatcher that auto-detects environment and routes to appropriate server
- **`enhanced_mcp_materials/local_server.py`** - Local development server (top-level imports, fast startup)
- **`enhanced_mcp_materials/aws_server.py`** - AWS Elastic Beanstalk server (lazy imports, comprehensive logging)
- **`enhanced_mcp_materials/oldserver.py`** - Reference implementation (keep for comparison)

### Client Components  
- **`utils/enhanced_mcp_client.py`** - Dispatcher that auto-detects environment and routes to appropriate client
- **`utils/local_client.py`** - Local development client (simple, fast, 10s timeouts)
- **`utils/aws_client.py`** - AWS deployment client (comprehensive logging, environment detection, 30s/180s timeouts)
- **`utils/oldclient.py`** - Reference implementation (keep for comparison)

## Environment Detection

Both dispatchers automatically detect the environment using:
```python
is_aws = any([
    os.environ.get('AWS_EXECUTION_ENV'),
    os.environ.get('LAMBDA_RUNTIME_DIR'), 
    os.path.exists('/var/app/current'),
    os.environ.get('EB_IS_COMMAND_LEADER')
])
```

## Local Development
- **Server**: `local_server.py` - Uses top-level imports like the working `oldserver.py`
- **Client**: `local_client.py` - Simple UV-based startup, 10s timeouts
- **Benefits**: Fast startup, no API hanging issues, clean Materials Project API responses

## AWS Deployment  
- **Server**: `aws_server.py` - Uses lazy imports, comprehensive logging, `ensure_structure_object()`
- **Client**: `aws_client.py` - Environment detection, UV/Python fallback, detailed error capture
- **Benefits**: Handles AWS environment constraints, detailed debugging, robust error handling

## Usage

### For Local Development
```bash
# Uses local_server.py and local_client.py automatically
python run_local.py
```

### For AWS Deployment
```bash
# Uses aws_server.py and aws_client.py automatically  
eb deploy
```

### Manual Override (if needed)
```python
# Force local client
from utils.local_client import LocalMCPAgent
agent = LocalMCPAgent(api_key)

# Force AWS client  
from utils.aws_client import EnhancedMCPAgent
agent = EnhancedMCPAgent(api_key)
```

## Key Differences

| Component | Local | AWS |
|-----------|-------|-----|
| **Imports** | Top-level | Lazy (inside functions) |
| **Logging** | Minimal | Comprehensive |
| **Timeouts** | 10s | 30s (AWS) / 180s (local fallback) |
| **Error Handling** | Simple | Detailed capture |
| **Startup** | Fast UV | UV + Python fallback |
| **Structure Handling** | Direct access | `ensure_structure_object()` |

## Benefits of This Organization

1. **Clean Separation**: Local and AWS code don't interfere with each other
2. **Automatic Detection**: No manual configuration needed
3. **Optimized Performance**: Each environment uses optimal settings
4. **Easy Debugging**: Clear logging shows which components are being used
5. **Backward Compatibility**: Existing code continues to work unchanged
6. **Future Maintenance**: Easy to update local or AWS components independently

## Troubleshooting

### Local Issues
- Check `local_server.py` and `local_client.py` logs
- Verify UV installation and MP_API_KEY
- 10s timeout should prevent hanging

### AWS Issues  
- Check `aws_server.py` and `aws_client.py` logs
- Verify AWS credentials and Secrets Manager access
- Comprehensive logging shows exact failure points

### Environment Detection Issues
- Check dispatcher logs to see which environment was detected
- Manually verify environment variables if needed