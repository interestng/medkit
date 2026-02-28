from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Provider(Protocol):
    """
    Protocol defining the contract for a MedKit data provider.
    """

    name: str

    async def search(self, query: str, **kwargs) -> Any:
        """Asynchronous search interface."""
        ...

    def search_sync(self, query: str, **kwargs) -> Any:
        """Synchronous search interface."""
        ...

    def health_check(self) -> bool:
        """Check if the provider is available."""
        ...

    def capabilities(self) -> list[str]:
        """Return list of supported features."""
        ...

    async def get(self, item_id: str) -> Any:
        """Fetch record by ID."""
        ...

    def get_sync(self, item_id: str) -> Any:
        """Fetch record by ID (sync)."""
        ...


class BaseProvider:
    """
    Base class for MedKit providers.
    """

    def __init__(self, name: str):
        self.name = name

    async def search(self, query: str, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement search()")

    def search_sync(self, query: str, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement search_sync()")

    def health_check(self) -> bool:
        return True

    def capabilities(self) -> list[str]:
        return []

    async def get(self, item_id: str) -> Any:
        raise NotImplementedError

    def get_sync(self, item_id: str) -> Any:
        raise NotImplementedError
