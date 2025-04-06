"""Tests for the SentryMCPServer class."""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from sentry_mcp.core.server import SentryMCPServer
from sentry_mcp.utils.exceptions import (
    SentryAPIError,
    SentryConfigError,
    SentryValidationError
)

@pytest.fixture
def mock_env():
    """Set up test environment variables."""
    with patch.dict(os.environ, {
        'SENTRY_AUTH_TOKEN': 'test_token',
        'SENTRY_ORG': 'test_org',
        'SENTRY_PROJECT': 'test_project'
    }):
        yield

@pytest.fixture
def server(mock_env):
    """Create a SentryMCPServer instance."""
    with patch('sentry_mcp.core.reporter.SentryReporter._get_project_id') as mock:
        mock.return_value = 'test_project_id'
        return SentryMCPServer()

def test_init_success(mock_env):
    """Test successful server initialization."""
    with patch('sentry_mcp.core.reporter.SentryReporter._get_project_id') as mock:
        mock.return_value = 'test_project_id'
        server = SentryMCPServer()
        assert server.auth_token == 'test_token'
        assert server.org_slug == 'test_org'
        assert server.project_slug == 'test_project'

def test_init_missing_env():
    """Test server initialization with missing environment variables."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(SentryConfigError):
            SentryMCPServer()

def test_handle_request_invalid_json(server):
    """Test handling invalid JSON request."""
    response = server.handle_request('invalid json')
    assert 'error' in response
    assert 'Invalid JSON request' in response['error']

def test_handle_request_missing_tool(server):
    """Test handling request with missing tool."""
    response = server.handle_request(json.dumps({'parameters': {}}))
    assert response['error'] == 'Missing required field: tool'

def test_handle_request_unknown_tool(server):
    """Test handling request with unknown tool."""
    response = server.handle_request(json.dumps({
        'tool': 'unknown_tool',
        'parameters': {}
    }))
    assert 'Unknown tool' in response['error']

def test_handle_request_project_stats(server):
    """Test handling get_project_stats request."""
    with patch('sentry_mcp.core.reporter.SentryReporter.get_project_stats') as mock:
        mock.return_value = {'total_errors': 0}
        response = server.handle_request(json.dumps({
            'tool': 'get_project_stats',
            'parameters': {'time_range': '24h'}
        }))
        assert response == {'total_errors': 0}
        mock.assert_called_once_with(time_range='24h')

def test_handle_request_error_trends(server):
    """Test handling get_error_trends request."""
    with patch('sentry_mcp.core.reporter.SentryReporter.get_error_trends') as mock:
        mock.return_value = {'trends': []}
        response = server.handle_request(json.dumps({
            'tool': 'get_error_trends',
            'parameters': {'time_range': '7d', 'min_occurrences': 5}
        }))
        assert response == {'trends': []}
        mock.assert_called_once_with(time_range='7d', min_occurrences=5)

def test_handle_request_impact_analysis(server):
    """Test handling get_impact_analysis request."""
    with patch('sentry_mcp.core.reporter.SentryReporter.get_impact_analysis') as mock:
        mock.return_value = {'error_stats': {}}
        response = server.handle_request(json.dumps({
            'tool': 'get_impact_analysis',
            'parameters': {'time_range': '24h'}
        }))
        assert response == {'error_stats': {}}
        mock.assert_called_once_with(time_range='24h')

def test_handle_request_validation_error(server):
    """Test handling request that raises validation error."""
    with patch(
        'sentry_mcp.core.reporter.SentryReporter.get_project_stats'
    ) as mock:
        mock.side_effect = SentryValidationError('Invalid time range')
        response = server.handle_request(json.dumps({
            'tool': 'get_project_stats',
            'parameters': {'time_range': 'invalid'}
        }))
        assert 'error' in response
        assert 'Invalid time range' in response['error']

def test_handle_request_api_error(server):
    """Test handling request that raises API error."""
    with patch(
        'sentry_mcp.core.reporter.SentryReporter.get_project_stats'
    ) as mock:
        mock.side_effect = SentryAPIError('API error')
        response = server.handle_request(json.dumps({
            'tool': 'get_project_stats',
            'parameters': {'time_range': '24h'}
        }))
        assert 'error' in response
        assert 'API error' in response['error']

def test_handle_request_unexpected_error(server):
    """Test handling request that raises unexpected error."""
    with patch(
        'sentry_mcp.core.reporter.SentryReporter.get_project_stats'
    ) as mock:
        mock.side_effect = Exception('Unexpected error')
        response = server.handle_request(json.dumps({
            'tool': 'get_project_stats',
            'parameters': {'time_range': '24h'}
        }))
        assert 'error' in response
        assert 'Unexpected error' in response['error'] 