from __future__ import annotations

from typing import Any, Protocol, Union, runtime_checkable

import httpx


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

    async def health_check_async(self) -> bool:
        """Check if the provider is available asynchronously."""
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

    def __init__(self, client: Union[httpx.Client, httpx.AsyncClient]):
        self.client = client
        self.name = "base"

    async def search(self, query: str, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement search()")

    def search_sync(self, query: str, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement search_sync()")

    async def health_check_async(self) -> bool:
        """Default health check: verify base URL is reachable."""
        return True

    def health_check(self) -> bool:
        """Default health check: verify base URL is reachable."""
        return True

    def capabilities(self) -> list[str]:
        return []

    async def get(self, item_id: str) -> Any:
        raise NotImplementedError

    def get_sync(self, item_id: str) -> Any:
        raise NotImplementedError
