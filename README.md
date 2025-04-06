# Sentry MCP (Model Context Protocol)

A Model Context Protocol server for retrieving and analyzing issues from Sentry.io. This server provides tools to inspect error reports, stacktraces, and other debugging information from your Sentry account.

## Overview

This MCP server enables AI assistants (like Claude) to interact with your Sentry data, providing:
- Project-wide error statistics
- Error trend analysis
- Impact analysis on users/sessions
- Customizable time ranges for analysis
- Structured logging

### Tools Provided

1. `get_sentry_issue`
   * Retrieve and analyze a Sentry issue by ID or URL
   * Returns detailed issue information including:
     - Title and Issue ID
     - Status and Level
     - First/Last seen timestamps
     - Event count
     - Full stacktrace

2. `get_list_issues`
   * Retrieve and analyze Sentry issues by project
   * Returns a list of issues with basic information

## Installation Options

### 1. Using Poetry (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/hientm1707/sentry-mcp.git
cd sentry-mcp

# Install dependencies
poetry install

# Set up environment variables
cp .env.example .env
```

### 2. Using uv (Alternative)

```bash
# Install using uv
uv pip install -e .

# Run directly
python -m mcp_sentry
```

### 3. Using pip

```bash
pip install mcp-sentry
```

## Configuration

### 1. Environment Setup

Edit your `.env` file with the following:
```env
SENTRY_AUTH_TOKEN=your_sentry_token
SENTRY_ORG=your_organization_slug
SENTRY_PROJECT=your_project_slug
LOG_LEVEL=INFO  # Optional, defaults to INFO
```

### 2. IDE Integration

#### For Cursor:
Add to your `mcp.json`:
```json
{
  "context_servers": {
    "mcp-sentry": {
      "command": {
        "path": "python",
        "args": [
          "-m",
          "mcp_sentry",
          "--auth-token",
          "YOUR_SENTRY_TOKEN",
          "--project-slug",
          "YOUR_PROJECT_SLUG",
          "--organization-slug",
          "YOUR_ORGANIZATION_SLUG"
        ]
      }
    }
  }
}
```

#### For Zed:
Add to your `settings.json`:
```json
"context_servers": {
  "mcp-sentry": {
    "command": "python",
    "args": [
      "-m",
      "mcp_sentry",
      "--auth-token",
      "YOUR_SENTRY_TOKEN",
      "--project-slug",
      "YOUR_PROJECT_SLUG",
      "--organization-slug",
      "YOUR_ORGANIZATION_SLUG"
    ]
  }
}
```

## Usage

1. Start the MCP server:
```bash
./run.sh
```

2. The server will now be available to your AI assistant through your IDE integration.

## Debugging

Use the MCP inspector to debug the server:

```bash
npx @modelcontextprotocol/inspector python -m mcp_sentry \
  --auth-token YOUR_SENTRY_TOKEN \
  --project-slug YOUR_PROJECT_SLUG \
  --organization-slug YOUR_ORGANIZATION_SLUG
```

## Development

Requirements:
- Python 3.8+
- Poetry for dependency management
- Structured logging with `structlog`
- Unit tests with `pytest`

Run tests:
```bash
poetry run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project is inspired by and compatible with the [MCP-100/mcp-sentry](https://github.com/MCP-100/mcp-sentry) implementation. 