"""
Core Sentry reporting functionality.
Handles interaction with Sentry's API for error tracking and analysis.
"""
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import requests
import structlog

from sentry_mcp.utils.exceptions import SentryAPIError, SentryConfigError
from sentry_mcp.utils.validators import validate_time_range

logger = structlog.get_logger(__name__)

class SentryReporter:
    """Handles interaction with Sentry's API for error reporting and analysis."""

    def __init__(self, auth_token: str, org_slug: str, project_slug: str):
        """Initialize the reporter with authentication and project details."""
        self.auth_token = auth_token
        self.org_slug = org_slug
        self.project_slug = project_slug
        self.base_url = 'https://sentry.io/api/0'
        self.headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json'
        }
        self.project_id = self._get_project_id()
        logger.info(
            'initialized_sentry_reporter',
            org_slug=org_slug,
            project_slug=project_slug
        )

    def _make_request(
        self, method: str, endpoint: str, params: Optional[Dict] = None
    ) -> Dict:
        """Make a request to the Sentry API with error handling."""
        url = f'{self.base_url}/{endpoint.lstrip("/")}'
        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(
                'sentry_api_request_failed',
                error=str(e),
                endpoint=endpoint,
                status_code=getattr(e.response, 'status_code', None)
            )
            raise SentryAPIError(f'API request failed: {str(e)}')

    def _get_project_id(self) -> str:
        """Get the numeric project ID from the project slug."""
        try:
            projects = self._make_request(
                'GET',
                f'organizations/{self.org_slug}/projects/'
            )
            
            for project in projects:
                if project['slug'] == self.project_slug:
                    return str(project['id'])
            
            raise SentryConfigError(f'Project {self.project_slug} not found')
        except Exception as e:
            logger.error(
                'project_id_lookup_failed',
                error=str(e),
                project_slug=self.project_slug
            )
            raise

    def _get_project_creation_date(self) -> datetime:
        """Get the project creation date."""
        try:
            project_data = self._make_request(
                'GET',
                f'projects/{self.org_slug}/{self.project_slug}/'
            )
            return datetime.fromisoformat(
                project_data['dateCreated'].replace('Z', '+00:00')
            )
        except Exception as e:
            logger.error(
                'project_creation_date_lookup_failed',
                error=str(e),
                project_slug=self.project_slug
            )
            raise

    def _parse_time_range(self, time_range: str) -> Tuple[datetime, datetime]:
        """Convert time range string to start and end datetime."""
        now = datetime.now()
        
        if time_range == 'all':
            return self._get_project_creation_date(), now
            
        validate_time_range(time_range)
        unit = time_range[-1]
        value = int(time_range[:-1])
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
            
        return now - delta, now

    def get_project_stats(
        self,
        time_range: str = 'all',
        group_by: Optional[str] = None,
        environment: Optional[str] = None
    ) -> Dict:
        """Get project-wide error statistics."""
        start_time, end_time = self._parse_time_range(time_range)
        
        params = {
            'statsPeriod': time_range if time_range != 'all' else None,
            'start': start_time.isoformat() if time_range == 'all' else None,
            'end': end_time.isoformat() if time_range == 'all' else None,
            'field': ['count()', 'users_affected', 'timestamp'],
            'project': self.project_id
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        if environment:
            params['environment'] = environment
        if group_by:
            params['groupBy'] = group_by

        try:
            stats = self._make_request(
                'GET',
                f'organizations/{self.org_slug}/issues/',
                params=params
            )
            
            total_errors = sum(int(issue.get('count', 0)) for issue in stats)
            total_users = sum(int(issue.get('userCount', 0)) for issue in stats)
            
            return {
                'total_errors': total_errors,
                'total_users_affected': total_users,
                'error_breakdown': stats if group_by else None,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(
                'project_stats_retrieval_failed',
                error=str(e),
                time_range=time_range
            )
            raise

    def get_error_trends(
        self,
        time_range: str = 'all',
        min_occurrences: int = 10
    ) -> Dict:
        """Get trending error patterns and their impact."""
        start_time, end_time = self._parse_time_range(time_range)
        
        params = {
            'statsPeriod': time_range if time_range != 'all' else None,
            'start': start_time.isoformat() if time_range == 'all' else None,
            'end': end_time.isoformat() if time_range == 'all' else None,
            'query': f'times_seen:>={min_occurrences}',
            'sort': 'freq',
            'limit': 100,
            'project': self.project_id
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            trends = self._make_request(
                'GET',
                f'organizations/{self.org_slug}/issues/',
                params=params
            )
            
            return {
                'trends': [{
                    'error_type': issue['type'],
                    'message': issue['title'],
                    'count': issue['count'],
                    'users_affected': issue.get('userCount', 0),
                    'first_seen': issue['firstSeen'],
                    'last_seen': issue['lastSeen']
                } for issue in trends],
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(
                'error_trends_retrieval_failed',
                error=str(e),
                time_range=time_range
            )
            raise

    def get_impact_analysis(
        self,
        time_range: str,
        issue_id: Optional[str] = None
    ) -> Dict:
        """Get impact analysis of errors on users/sessions."""
        start_time, end_time = self._parse_time_range(time_range)
        
        try:
            # Get project stats
            stats_data = self._make_request(
                'GET',
                f'projects/{self.org_slug}/{self.project_slug}/stats/',
                params={
                    'stat': 'received',
                    'resolution': '1h',
                    'statsPeriod': time_range
                }
            )

            # Get session data with simplified fields
            session_params = {
                'project': self.project_id,
                'statsPeriod': time_range,
                'interval': '1h',
                'field': ['sum(session)', 'count_unique(user)']
            }
            if issue_id:
                session_params['query'] = f'issue:{issue_id}'
                
            session_data = self._make_request(
                'GET',
                f'organizations/{self.org_slug}/sessions/',
                params=session_params
            )

            # Get release data
            release_data = self._make_request(
                'GET',
                f'organizations/{self.org_slug}/releases/',
                params={
                    'project': self.project_id,
                    'statsPeriod': time_range
                }
            )

            return {
                'error_stats': {
                    'total_errors': sum(
                        count for timestamp, count in stats_data
                    ),
                    'error_timeline': stats_data
                },
                'session_stats': {
                    'total_sessions': session_data.get('groups', [{}])[0]
                    .get('totals', {})
                    .get('sum(session)', 0),
                    'total_users': session_data.get('groups', [{}])[0]
                    .get('totals', {})
                    .get('count_unique(user)', 0),
                    'timeline': session_data.get('intervals', [])
                },
                'release_stats': {
                    'total_releases': len(release_data),
                    'latest_releases': [
                        {
                            'version': release['version'],
                            'created': release['dateCreated'],
                            'status': release.get('status', 'unknown')
                        }
                        for release in release_data[:5]
                    ]
                },
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        except Exception as e:
            logger.error(
                'impact_analysis_failed',
                error=str(e),
                time_range=time_range,
                issue_id=issue_id
            )
            raise 