"""
MCP Server Dispatcher - Automatically chooses between local and AWS servers
"""
import os

def main():
    """Dispatch to appropriate server based on environment"""
    # Detect AWS environment
    is_aws = any([
        os.environ.get('AWS_EXECUTION_ENV'),
        os.environ.get('LAMBDA_RUNTIME_DIR'),
        os.path.exists('/var/app/current'),
        os.environ.get('EB_IS_COMMAND_LEADER')
    ])
    
    if is_aws:
        print("🚀 MCP DISPATCHER: AWS environment detected, using aws_server.py")
        from . import aws_server
        aws_server.main()
    else:
        print("🚀 MCP DISPATCHER: Local environment detected, using local_server.py")
        from . import local_server
        local_server.main()

if __name__ == "__main__":
    main()