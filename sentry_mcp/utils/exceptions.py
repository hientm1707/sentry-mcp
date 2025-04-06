"""Custom exceptions for the Sentry MCP."""

class SentryMCPError(Exception):
    """Base exception for all Sentry MCP errors."""
    pass

class SentryAPIError(SentryMCPError):
    """Raised when there is an error communicating with the Sentry API."""
    pass

class SentryConfigError(SentryMCPError):
    """Raised when there is an error with the Sentry configuration."""
    pass

class SentryValidationError(SentryMCPError):
    """Raised when there is an error validating input parameters."""
    pass 