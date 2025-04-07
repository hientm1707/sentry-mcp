"""
Sentry MCP server implementation.
Handles incoming requests and routes them to the appropriate reporter methods.
"""
import json
import os
from typing import Dict, Optional

import structlog
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from sentry_mcp.core.reporter import SentryReporter
from sentry_mcp.utils.exceptions import (
    SentryAPIError,
    SentryConfigError,
    SentryValidationError
)

# Load environment variables
load_dotenv()

logger = structlog.get_logger(__name__)

class MCPRequest(BaseModel):
    """Model for MCP request validation"""
    tool: str
    parameters: Dict = {}

# Initialize FastAPI app
app = FastAPI(
    title="Sentry MCP Server",
    description="Model Context Protocol server for Sentry integration",
    version="0.1.0"
)

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
        
    async def handle_request(self, request: MCPRequest) -> Dict:
        """
        Handle an incoming MCP request.
        
        Args:
            request: Validated MCP request object
            
        Returns:
            Dict containing the response
            
        Raises:
            HTTPException: If request is invalid or there's an error
        """
        try:
            if request.tool == "get_project_stats":
                return await self.reporter.get_project_stats(**request.parameters)
            elif request.tool == "get_error_trends":
                return await self.reporter.get_error_trends(**request.parameters)
            elif request.tool == "get_impact_analysis":
                return await self.reporter.get_impact_analysis(**request.parameters)
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown tool: {request.tool}"
                )
                
        except (SentryValidationError, SentryConfigError) as e:
            logger.error(
                "request_validation_failed",
                tool=request.tool,
                error=str(e)
            )
            raise HTTPException(status_code=400, detail=str(e))
            
        except SentryAPIError as e:
            logger.error(
                "sentry_api_error",
                tool=request.tool,
                error=str(e)
            )
            raise HTTPException(status_code=502, detail=str(e))
            
        except Exception as e:
            logger.error(
                "unexpected_error",
                tool=request.tool,
                error=str(e)
            )
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )

# Initialize server instance
server = SentryMCPServer()

@app.post("/mcp")
async def handle_mcp_request(request: MCPRequest):
    """Handle incoming MCP requests"""
    return await server.handle_request(request) 