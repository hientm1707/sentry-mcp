"""
Sentry MCP server implementation.
Handles incoming requests and routes them to the appropriate reporter methods.
"""
import json
import os
from typing import Dict, Optional

import structlog
from dotenv import load_dotenv

from sentry_mcp.core.reporter import SentryReporter
from sentry_mcp.utils.exceptions import (
    SentryAPIError,
    SentryConfigError,
    SentryValidationError
)

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)

class SentryMCPServer:
    """Handles incoming MCP requests for Sentry operations."""
    
    def __init__(self):
        """Initialize the MCP server with configuration from environment."""
        self.auth_token = os.getenv("SENTRY_AUTH_TOKEN")
        self.org_slug = os.getenv("SENTRY_ORG")
        self.project_slug = os.getenv("SENTRY_PROJECT")
        
        if not all([self.auth_token, self.org_slug, self.project_slug]):
            raise SentryConfigError(
                "Missing required environment variables. "
                "Please set SENTRY_AUTH_TOKEN, SENTRY_ORG, and SENTRY_PROJECT."
            )
            
        self.reporter = SentryReporter(
            self.auth_token,
            self.org_slug,
            self.project_slug
        )
        logger.info("initialized_sentry_mcp_server")
        
    def handle_request(self, request_data: str) -> Dict:
        """
        Handle an incoming MCP request.
        
        Args:
            request_data: JSON string containing the request
            
        Returns:
            Dict containing the response
            
        Raises:
            SentryValidationError: If request format is invalid
            SentryAPIError: If there is an error communicating with Sentry
        """
        try:
            request = json.loads(request_data)
        except json.JSONDecodeError as e:
            logger.error("invalid_json_request", error=str(e))
            return {"error": f"Invalid JSON request: {str(e)}"}
            
        tool = request.get("tool")
        params = request.get("parameters", {})
        
        if not tool:
            return {"error": "Missing required field: tool"}
            
        try:
            if tool == "get_project_stats":
                return self.reporter.get_project_stats(**params)
            elif tool == "get_error_trends":
                return self.reporter.get_error_trends(**params)
            elif tool == "get_impact_analysis":
                return self.reporter.get_impact_analysis(**params)
            else:
                return {"error": f"Unknown tool: {tool}"}
                
        except (SentryValidationError, SentryAPIError, SentryConfigError) as e:
            logger.error(
                "request_handling_failed",
                tool=tool,
                error=str(e)
            )
            return {"error": str(e)}
        except Exception as e:
            logger.error(
                "unexpected_error",
                tool=tool,
                error=str(e)
            )
            return {"error": f"Unexpected error: {str(e)}"}
            
def main():
    """Main entry point for the MCP server."""
    try:
        server = SentryMCPServer()
        
        while True:
            try:
                request_data = input()
                if not request_data:
                    continue
                    
                response = server.handle_request(request_data)
                print(json.dumps(response))
                
            except EOFError:
                break
            except KeyboardInterrupt:
                break
                
    except Exception as e:
        logger.error("server_initialization_failed", error=str(e))
        print(json.dumps({"error": f"Server initialization failed: {str(e)}"}))
        
if __name__ == "__main__":
    main() 