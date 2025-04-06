# Sentry MCP (Mission Control Program)

A Python-based tool for interacting with Sentry's API to monitor and analyze error tracking data.

## Features

- Project-wide error statistics
- Error trend analysis
- Impact analysis on users/sessions
- Customizable time ranges for analysis
- Structured logging

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
Then edit `.env` with your Sentry credentials:
- `SENTRY_AUTH_TOKEN`: Your Sentry authentication token
- `SENTRY_ORG`: Your organization slug
- `SENTRY_PROJECT`: Your project slug
- `LOG_LEVEL`: Logging level (default: INFO)

## Usage

Run the MCP server:
```bash
./run.sh
```

## Development

- Python 3.8+
- Poetry for dependency management
- Structured logging with `structlog`
- Unit tests with `pytest`

## Testing

Run tests:
```bash
poetry run pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 