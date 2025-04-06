"""Input validation utilities for the Sentry MCP."""
import re
from typing import Dict, List, Optional, Union

from sentry_mcp.utils.exceptions import SentryValidationError

def validate_time_range(time_range: str) -> None:
    """
    Validate time range format.
    
    Valid formats:
    - Nx where N is a number and x is either 'h' (hours) or 'd' (days)
    - 'all' for all time since project creation
    
    Args:
        time_range: Time range string to validate
        
    Raises:
        SentryValidationError: If time range format is invalid
    """
    if time_range == 'all':
        return
        
    pattern = r'^\d+[hd]$'
    if not re.match(pattern, time_range):
        raise SentryValidationError(
            f'Invalid time range format: {time_range}. '
            'Must be a number followed by \'h\' (hours) or \'d\' (days), '
            'or \'all\' for all time.'
        )
        
    # Extract numeric value
    value = int(time_range[:-1])
    if value <= 0:
        raise SentryValidationError(
            f'Time range value must be positive, got: {value}'
        )
        
    # Validate reasonable ranges
    unit = time_range[-1]
    if unit == 'h' and value > 168:  # 1 week in hours
        raise SentryValidationError(
            f'Hour-based time range too large: {value}h. '
            'Use days for ranges > 168 hours.'
        )
    elif unit == 'd' and value > 90:  # ~3 months
        raise SentryValidationError(
            f'Day-based time range too large: {value}d. '
            'Use \'all\' for ranges > 90 days.'
        ) 