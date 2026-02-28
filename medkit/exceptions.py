from __future__ import annotations


class MedKitError(Exception):
    """Base exception for MedKit SDK."""

    pass


class APIError(MedKitError):
    """Raised when an external API returns an error."""

    pass


class RateLimitError(MedKitError):
    """Raised when an API rate limit is exceeded."""

    pass


class NotFoundError(MedKitError):
    """Raised when a requested resource is not found."""

    pass


class ProviderUnavailableError(APIError):
    """Raised when a specific provider is down."""

    pass


class InvalidQueryError(MedKitError):
    """Raised when a query is malformed or invalid."""

    pass


class PluginError(MedKitError):
    """Raised when there is an issue with a provider plugin."""

    pass
