"""
CLI commands for sentry-mcp server.
"""
import os
import shutil
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

def create_server():
    """Create a new MCP server instance."""
    # Get the target directory
    target_dir = input("Enter directory name for your MCP server (default: mcp-server): ").strip() or "mcp-server"
    target_path = Path(target_dir)

    if target_path.exists():
        print(f"Error: Directory {target_dir} already exists")
        sys.exit(1)

    # Create directory structure
    target_path.mkdir(parents=True)
    
    # Create .env file
    env_template = """SENTRY_AUTH_TOKEN='your_sentry_auth_token_here'
SENTRY_ORG='your_sentry_org_here'
SENTRY_PROJECT='your_sentry_project_here'
LOG_LEVEL='INFO'
"""
    with open(target_path / ".env", "w") as f:
        f.write(env_template)

    print(f"""
MCP server created successfully in {target_dir}!

To get started:
1. cd {target_dir}
2. Edit .env file with your Sentry credentials
3. Run 'uv run my-server' to start the server
""")

def run_server():
    """Run the MCP server."""
    # Load environment variables
    load_dotenv()

    # Check for required environment variables
    required_vars = ["SENTRY_AUTH_TOKEN", "SENTRY_ORG", "SENTRY_PROJECT"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("Error: Missing required environment variables:")
        for var in missing_vars:
            print(f"- {var}")
        print("\nPlease set these variables in your .env file")
        sys.exit(1)

    # Run the server using the import string instead of importing directly
    uvicorn.run(
        "sentry_mcp.core.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    ) 