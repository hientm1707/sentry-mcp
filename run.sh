#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | sed 's/#.*//g' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

# Run the MCP server using Poetry
poetry run python sentry_mcp.py 