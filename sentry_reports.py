import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests

class SentryReporter:
    def __init__(self, auth_token: str, org_slug: str, project_slug: str):
        self.auth_token = auth_token
        self.org_slug = org_slug
        self.project_slug = project_slug
        self.base_url = "https://sentry.io/api/0"
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
        self.project_id = self._get_project_id()

    def _get_project_id(self) -> str:
        """Get the numeric project ID from the project slug."""
        url = f"{self.base_url}/organizations/{self.org_slug}/projects/"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            projects = response.json()
            
            for project in projects:
                if project["slug"] == self.project_slug:
                    return str(project["id"])
            
            raise ValueError(f"Project {self.project_slug} not found")
            
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get project ID: {str(e)}")

    def _get_project_creation_date(self) -> datetime:
        """Get the project creation date."""
        url = f"{self.base_url}/projects/{self.org_slug}/{self.project_slug}/"
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            project_data = response.json()
            return datetime.fromisoformat(project_data["dateCreated"].replace("Z", "+00:00"))
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Failed to get project creation date: {str(e)}")

    def _parse_time_range(self, time_range: str) -> tuple[datetime, datetime]:
        """Convert time range string to start and end datetime."""
        now = datetime.now()
        
        if time_range == "all":
            return self._get_project_creation_date(), now
            
        unit = time_range[-1]
        value = int(time_range[:-1])
        
        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'd':
            delta = timedelta(days=value)
        else:
            raise ValueError("Invalid time range format. Use '24h', '7d', or 'all' for entire history.")
            
        return now - delta, now

    def get_project_stats(self, time_range: str = "all", group_by: Optional[str] = None, environment: Optional[str] = None) -> Dict:
        """Get project-wide error statistics."""
        start_time, end_time = self._parse_time_range(time_range)
        
        # Build query parameters
        params = {
            "statsPeriod": time_range if time_range != "all" else None,
            "start": start_time.isoformat() if time_range == "all" else None,
            "end": end_time.isoformat() if time_range == "all" else None,
            "field": ["count()", "users_affected", "timestamp"],
            "project": self.project_id
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        if environment:
            params["environment"] = environment
        if group_by:
            params["groupBy"] = group_by

        # Get issue stats
        url = f"{self.base_url}/organizations/{self.org_slug}/issues/"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            # Process and format the data
            stats = response.json()
            return {
                "total_errors": sum(issue["count"] for issue in stats),
                "total_users_affected": sum(issue.get("userCount", 0) for issue in stats),
                "error_breakdown": stats if group_by else None,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API Error: {str(e)}",
                "details": response.text if hasattr(response, 'text') else None
            }

    def get_error_trends(self, time_range: str = "all", min_occurrences: int = 10) -> Dict:
        """Get trending error patterns and their impact."""
        start_time, end_time = self._parse_time_range(time_range)
        
        # Get trending issues
        url = f"{self.base_url}/organizations/{self.org_slug}/issues/"
        params = {
            "statsPeriod": time_range if time_range != "all" else None,
            "start": start_time.isoformat() if time_range == "all" else None,
            "end": end_time.isoformat() if time_range == "all" else None,
            "query": f"times_seen:>={min_occurrences}",
            "sort": "freq",
            "limit": 100,
            "project": self.project_id
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            trends = response.json()
            return {
                "trends": [{
                    "error_type": issue["type"],
                    "message": issue["title"],
                    "count": issue["count"],
                    "users_affected": issue.get("userCount", 0),
                    "first_seen": issue["firstSeen"],
                    "last_seen": issue["lastSeen"]
                } for issue in trends],
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API Error: {str(e)}",
                "details": response.text if hasattr(response, 'text') else None
            }

    def get_impact_analysis(self, time_range: str, issue_id: Optional[str] = None) -> Dict:
        """Get impact analysis of errors on users/sessions."""
        start_time, end_time = self._parse_time_range(time_range)
        
        try:
            # Get project stats first
            stats_url = f"{self.base_url}/projects/{self.org_slug}/{self.project_slug}/stats/"
            stats_response = requests.get(
                stats_url,
                headers=self.headers,
                params={
                    "stat": "received",
                    "resolution": "1h",
                    "statsPeriod": time_range
                }
            )
            stats_response.raise_for_status()
            stats_data = stats_response.json()

            # Get session data
            session_url = f"{self.base_url}/organizations/{self.org_slug}/sessions/"
            session_params = {
                "project": self.project_id,
                "statsPeriod": time_range,
                "interval": "1h",
                "field": ["sum(session)","sum(user)","count_unique(user)","crash_free_rate"]
            }
            if issue_id:
                session_params["query"] = f"issue:{issue_id}"
                
            session_response = requests.get(session_url, headers=self.headers, params=session_params)
            session_response.raise_for_status()
            session_data = session_response.json()

            # Get release data
            release_url = f"{self.base_url}/organizations/{self.org_slug}/releases/"
            release_params = {
                "project": self.project_id,
                "statsPeriod": time_range
            }
            release_response = requests.get(release_url, headers=self.headers, params=release_params)
            release_response.raise_for_status()
            release_data = release_response.json()

            return {
                "error_stats": {
                    "total_errors": sum(count for timestamp, count in stats_data),
                    "error_timeline": stats_data
                },
                "session_stats": {
                    "total_sessions": session_data.get("groups", [{}])[0].get("totals", {}).get("sum(session)", 0),
                    "total_users": session_data.get("groups", [{}])[0].get("totals", {}).get("count_unique(user)", 0),
                    "crash_free_rate": session_data.get("groups", [{}])[0].get("totals", {}).get("crash_free_rate", 100),
                    "timeline": session_data.get("intervals", [])
                },
                "release_stats": {
                    "total_releases": len(release_data),
                    "latest_releases": [
                        {
                            "version": release["version"],
                            "created": release["dateCreated"],
                            "status": release.get("status", "unknown")
                        }
                        for release in release_data[:5]  # Show only the 5 most recent releases
                    ]
                },
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
        except requests.exceptions.RequestException as e:
            last_response = None
            if 'stats_response' in locals():
                last_response = stats_response
            elif 'session_response' in locals():
                last_response = session_response
            elif 'release_response' in locals():
                last_response = release_response
                
            return {
                "error": f"API Error: {str(e)}",
                "details": last_response.text if last_response and hasattr(last_response, 'text') else str(e)
            }

def main():
    """CLI interface for the reporter."""
    if len(sys.argv) < 2:
        print("Usage: python sentry_reports.py <command> [params...]")
        sys.exit(1)

    # Get environment variables
    auth_token = os.getenv("SENTRY_AUTH_TOKEN")
    org_slug = os.getenv("SENTRY_ORG_SLUG")
    project_slug = os.getenv("SENTRY_PROJECT_SLUG")

    if not all([auth_token, org_slug, project_slug]):
        print("Error: Missing required environment variables")
        sys.exit(1)

    reporter = SentryReporter(auth_token, org_slug, project_slug)
    command = sys.argv[1]
    args = sys.argv[2:]

    try:
        if command == "get_project_stats":
            result = reporter.get_project_stats(
                time_range=args[0],
                group_by=args[1] if len(args) > 1 else None,
                environment=args[2] if len(args) > 2 else None
            )
        elif command == "get_error_trends":
            result = reporter.get_error_trends(
                time_range=args[0],
                min_occurrences=int(args[1]) if len(args) > 1 else 10
            )
        elif command == "get_impact_analysis":
            result = reporter.get_impact_analysis(
                time_range=args[0],
                issue_id=args[1] if len(args) > 1 else None
            )
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except Exception as e:
        print(json.dumps({
            "error": str(e),
            "type": type(e).__name__
        }), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 