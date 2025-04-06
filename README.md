# Sentry MCP (Mission Control Program)

A Python-based tool for interacting with Sentry's API to monitor and analyze error tracking data. This tool provides comprehensive error analysis and reporting capabilities through a Model Context Protocol (MCP) server.

## Features

- **Project Statistics**: Get comprehensive error statistics across your project
  - Total error counts
  - Users affected
  - Custom time ranges
  - Environment-specific stats
  
- **Error Trend Analysis**: Identify and analyze error patterns
  - Trending issues
  - Frequency analysis
  - User impact metrics
  - First/last seen timestamps

- **Impact Analysis**: Understand how errors affect your users and sessions
  - Session statistics
  - Crash-free rates
  - Release tracking
  - User impact metrics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/hientm1707/sentry-mcp.git
cd sentry-mcp
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` with your Sentry credentials:
```env
SENTRY_AUTH_TOKEN=your_sentry_auth_token
SENTRY_ORG_SLUG=your_organization_slug
SENTRY_PROJECT_SLUG=your_project_slug
LOG_LEVEL=INFO
```

## Usage

### Starting the Server

Run the MCP server:
```bash
./run.sh
```

### Available Tools

1. `get_project_stats`
   ```python
   {
     "tool": "get_project_stats",
     "parameters": {
       "time_range": "24h",  # Options: "24h", "7d", "all"
       "group_by": "type",   # Optional: Group results by field
       "environment": "prod" # Optional: Filter by environment
     }
   }
   ```

2. `get_error_trends`
   ```python
   {
     "tool": "get_error_trends",
     "parameters": {
       "time_range": "7d",
       "min_occurrences": 10  # Minimum number of occurrences to include
     }
   }
   ```

3. `get_impact_analysis`
   ```python
   {
     "tool": "get_impact_analysis",
     "parameters": {
       "time_range": "24h",
       "issue_id": "1234"  # Optional: Focus on specific issue
     }
   }
   ```

### Time Range Format
- Hours: e.g., "24h", "48h"
- Days: e.g., "7d", "30d"
- All time: "all"

## Development

Requirements:
- Python 3.8+
- Poetry for dependency management
- Structured logging with `structlog`
- Unit tests with `pytest`

### Running Tests

```bash
poetry run pytest
```

### Project Structure

```
sentry-mcp/
├── sentry_mcp.py        # Main MCP server implementation
├── sentry_reports.py    # Core reporting functionality
├── run.sh              # Server startup script
├── tests/              # Test suite
└── pyproject.toml      # Project dependencies and metadata
```

## Response Format

All tools return JSON responses with the following structure:

```json
{
  "time_range": {
    "start": "2024-04-06T00:00:00",
    "end": "2024-04-06T23:59:59"
  },
  "data": {
    // Tool-specific data
  },
  "error": "Error message if something went wrong"
}
```

## Error Handling

The server handles various error cases:
- Invalid authentication
- Missing environment variables
- API request failures
- Invalid time ranges
- Project not found

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

This project is inspired by and compatible with the [MCP-100/mcp-sentry](https://github.com/MCP-100/mcp-sentry) implementation. 