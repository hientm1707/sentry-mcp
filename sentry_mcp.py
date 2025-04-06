#!/usr/bin/env python3
"""
Main entry point for the Sentry MCP server.
This script sets up logging and starts the server.
"""
import logging.config
import os
import sys
import json
from typing import Dict, Any
from sentry_reports import SentryReporter

import structlog

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def configure_logging() -> None:
    """Configure structured logging with console output."""
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': structlog.stdlib.ProcessorFormatter,
                'processor': structlog.processors.JSONRenderer(),
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
                'stream': 'ext://sys.stderr',
            }
        },
        'loggers': {
            '': {
                'handlers': ['console'],
                'level': 'INFO',
            }
        }
    })
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt='iso'),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def handle_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incoming MCP requests."""
    try:
        # Get environment variables
        auth_token = os.getenv('SENTRY_AUTH_TOKEN')
        org_slug = os.getenv('SENTRY_ORG_SLUG')
        project_slug = os.getenv('SENTRY_PROJECT_SLUG')

        if not all([auth_token, org_slug, project_slug]):
            return {'error': 'Missing required environment variables'}

        reporter = SentryReporter(auth_token, org_slug, project_slug)
        tool = request_data.get('tool')
        params = request_data.get('parameters', {})

        if tool == 'get_project_stats':
            return reporter.get_project_stats(
                time_range=params.get('time_range', '24h'),
                group_by=params.get('group_by'),
                environment=params.get('environment')
            )
        elif tool == 'get_error_trends':
            return reporter.get_error_trends(
                time_range=params.get('time_range', '7d'),
                min_occurrences=params.get('min_occurrences', 10)
            )
        elif tool == 'get_impact_analysis':
            return reporter.get_impact_analysis(
                time_range=params.get('time_range', '24h'),
                issue_id=params.get('issue_id')
            )
        else:
            return {'error': f'Unknown tool: {tool}'}

    except json.JSONDecodeError:
        return {'error': 'Invalid JSON request'}
    except Exception as e:
        return {
            'error': str(e),
            'type': type(e).__name__
        }

def main():
    """Main MCP server loop."""
    while True:
        try:
            # Read request from stdin
            request_line = sys.stdin.readline()
            if not request_line:
                break

            # Parse and handle request
            try:
                request_data = json.loads(request_line)
                response = handle_request(request_data)
            except json.JSONDecodeError:
                response = {'error': 'Invalid JSON request'}
            except Exception as e:
                response = {
                    'error': str(e),
                    'type': type(e).__name__
                }

            # Send response
            print(json.dumps(response))
            sys.stdout.flush()

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(json.dumps({
                'error': str(e),
                'type': type(e).__name__
            }))
            sys.stdout.flush()

if __name__ == '__main__':
    configure_logging()
    from sentry_mcp.core.server import main
    main() 