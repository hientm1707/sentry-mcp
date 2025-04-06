"""Tests for the SentryReporter class."""
import json
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
import requests

from sentry_mcp.core.reporter import SentryReporter
from sentry_mcp.utils.exceptions import (
    SentryAPIError,
    SentryConfigError,
    SentryValidationError
)

@pytest.fixture
def mock_response():
    """Create a mock response object."""
    response = MagicMock()
    response.json.return_value = {'data': 'test'}
    response.raise_for_status.return_value = None
    return response

@pytest.fixture
def reporter():
    """Create a SentryReporter instance with test credentials."""
    with patch('sentry_mcp.core.reporter.SentryReporter._get_project_id') as mock:
        mock.return_value = 'test_project_id'
        return SentryReporter(
            'test_token',
            'test_org',
            'test_project'
        )

def test_init(reporter):
    """Test reporter initialization."""
    assert reporter.auth_token == 'test_token'
    assert reporter.org_slug == 'test_org'
    assert reporter.project_slug == 'test_project'
    assert reporter.project_id == 'test_project_id'

def test_make_request_success(reporter, mock_response):
    """Test successful API request."""
    with patch('requests.request', return_value=mock_response):
        response = reporter._make_request('GET', 'test/endpoint')
        assert response == {'data': 'test'}

def test_make_request_failure(reporter):
    """Test API request failure."""
    with patch('requests.request') as mock:
        mock.side_effect = requests.exceptions.RequestException('Test error')
        with pytest.raises(SentryAPIError):
            reporter._make_request('GET', 'test/endpoint')

def test_get_project_id_success(reporter):
    """Test successful project ID retrieval."""
    mock_projects = [
        {'id': '123', 'slug': 'wrong_project'},
        {'id': '456', 'slug': 'test_project'}
    ]
    with patch('sentry_mcp.core.reporter.SentryReporter._make_request') as mock:
        mock.return_value = mock_projects
        assert reporter._get_project_id() == '456'

def test_get_project_id_not_found():
    """Test project ID not found."""
    with patch('sentry_mcp.core.reporter.SentryReporter._make_request') as mock:
        mock.return_value = [{'id': '123', 'slug': 'wrong_project'}]
        with pytest.raises(SentryConfigError):
            SentryReporter('token', 'org', 'nonexistent')._get_project_id()

def test_parse_time_range_all(reporter):
    """Test parsing 'all' time range."""
    creation_date = datetime(2023, 1, 1)
    with patch(
        'sentry_mcp.core.reporter.SentryReporter._get_project_creation_date',
        return_value=creation_date
    ):
        start, end = reporter._parse_time_range('all')
        assert start == creation_date
        assert isinstance(end, datetime)

def test_parse_time_range_hours(reporter):
    """Test parsing hour-based time range."""
    start, end = reporter._parse_time_range('24h')
    assert end - start == timedelta(hours=24)

def test_parse_time_range_days(reporter):
    """Test parsing day-based time range."""
    start, end = reporter._parse_time_range('7d')
    assert end - start == timedelta(days=7)

def test_get_project_stats(reporter, mock_response):
    """Test getting project statistics."""
    mock_response.json.return_value = [
        {'count': 10, 'userCount': 5},
        {'count': 20, 'userCount': 8}
    ]
    with patch('requests.request', return_value=mock_response):
        stats = reporter.get_project_stats('24h')
        assert stats['total_errors'] == 30
        assert stats['total_users_affected'] == 13
        assert 'time_range' in stats

def test_get_error_trends(reporter, mock_response):
    """Test getting error trends."""
    mock_response.json.return_value = [
        {
            'type': 'error',
            'title': 'Test Error',
            'count': 10,
            'userCount': 5,
            'firstSeen': '2023-01-01T00:00:00Z',
            'lastSeen': '2023-01-02T00:00:00Z'
        }
    ]
    with patch('requests.request', return_value=mock_response):
        trends = reporter.get_error_trends('7d', 5)
        assert len(trends['trends']) == 1
        assert trends['trends'][0]['error_type'] == 'error'
        assert 'time_range' in trends

def test_get_impact_analysis(reporter, mock_response):
    """Test getting impact analysis."""
    mock_stats = [(0, 10), (1, 20)]
    mock_session = {
        'groups': [{
            'totals': {
                'sum(session)': 100,
                'count_unique(user)': 50,
                'crash_free_rate': 99.9
            }
        }],
        'intervals': ['2023-01-01T00:00:00Z']
    }
    mock_releases = [
        {
            'version': 'v1.0.0',
            'dateCreated': '2023-01-01T00:00:00Z',
            'status': 'active'
        }
    ]
    
    def mock_request(*args, **kwargs):
        endpoint = args[1]
        if 'stats' in endpoint:
            mock_response.json.return_value = mock_stats
        elif 'sessions' in endpoint:
            mock_response.json.return_value = mock_session
        elif 'releases' in endpoint:
            mock_response.json.return_value = mock_releases
        return mock_response
        
    with patch('requests.request', side_effect=mock_request):
        analysis = reporter.get_impact_analysis('24h')
        assert analysis['error_stats']['total_errors'] == 30
        assert analysis['session_stats']['total_sessions'] == 100
        assert len(analysis['release_stats']['latest_releases']) == 1
        assert 'time_range' in analysis 