"""Tests for input validation functions."""
import pytest

from sentry_mcp.utils.exceptions import SentryValidationError
from sentry_mcp.utils.validators import validate_time_range

def test_validate_time_range_all():
    """Test validating 'all' time range."""
    # Should not raise an exception
    validate_time_range('all')

def test_validate_time_range_hours():
    """Test validating hour-based time ranges."""
    # Valid hour ranges
    validate_time_range('1h')
    validate_time_range('24h')
    validate_time_range('168h')  # 1 week
    
    # Invalid hour ranges
    with pytest.raises(SentryValidationError):
        validate_time_range('0h')
    with pytest.raises(SentryValidationError):
        validate_time_range('-1h')
    with pytest.raises(SentryValidationError):
        validate_time_range('169h')  # > 1 week

def test_validate_time_range_days():
    """Test validating day-based time ranges."""
    # Valid day ranges
    validate_time_range('1d')
    validate_time_range('7d')
    validate_time_range('90d')
    
    # Invalid day ranges
    with pytest.raises(SentryValidationError):
        validate_time_range('0d')
    with pytest.raises(SentryValidationError):
        validate_time_range('-1d')
    with pytest.raises(SentryValidationError):
        validate_time_range('91d')  # > 90 days

def test_validate_time_range_invalid_format():
    """Test validating invalid time range formats."""
    invalid_formats = [
        '',  # Empty string
        '1',  # Missing unit
        'h',  # Missing number
        '1x',  # Invalid unit
        '1.5h',  # Decimal not allowed
        '24H',  # Wrong case
        '7D',  # Wrong case
        '1h1d',  # Multiple units
        'day',  # Invalid format
        'hour',  # Invalid format
        'all day',  # Invalid format
        '1 h',  # Space not allowed
        '1 day',  # Invalid format
    ]
    
    for invalid_format in invalid_formats:
        with pytest.raises(SentryValidationError):
            validate_time_range(invalid_format) 