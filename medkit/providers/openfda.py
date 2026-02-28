from __future__ import annotations

from typing import Any

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import DrugInfo
from .base import BaseProvider


class OpenFDAProvider(BaseProvider):
    BASE_URL = "https://api.fda.gov/drug/label.json"

    def __init__(self, http_client: httpx.Client | httpx.AsyncClient):
        super().__init__(name="openfda")
        self.http_client = http_client

    def capabilities(self) -> list[str]:
        return ["drugs"]

    def get_sync(self, item_id: str) -> DrugInfo:
        return self.search_sync(item_id)

    async def get(self, item_id: str) -> DrugInfo:
        return await self.search(item_id)

    def search_sync(self, query: str, **kwargs) -> DrugInfo:
        search_query = f'openfda.brand_name:"{query}" openfda.generic_name:"{query}"'
        try:
            response = self.http_client.get(  # type: ignore
                self.BASE_URL, params={"search": search_query, "limit": 1}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Drug '{query}' not found on OpenFDA.") from e
            raise APIError(f"OpenFDA API error: {e}") from e
        except httpx.RequestError as e:
            raise APIError(f"Network error while connecting to OpenFDA: {e}") from e

        data = response.json()
        return self._parse_response(data, query)

    async def search(self, query: str, **kwargs) -> DrugInfo:
        search_query = f'openfda.brand_name:"{query}" openfda.generic_name:"{query}"'
        try:
            response = await self.http_client.get(  # type: ignore
                self.BASE_URL, params={"search": search_query, "limit": 1}
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise NotFoundError(f"Drug '{query}' not found on OpenFDA.") from e
            raise APIError(f"OpenFDA API error: {e}") from e
        except httpx.RequestError as e:
            raise APIError(f"Network error while connecting to OpenFDA: {e}") from e

        data = response.json()
        return self._parse_response(data, query)

    def _parse_response(self, data: dict[str, Any], name: str) -> DrugInfo:
        if not data.get("results"):
            raise NotFoundError(f"Drug '{name}' not found.")

        result = data["results"][0]
        openfda = result.get("openfda", {})

        brand_name = openfda.get("brand_name", ["Unknown"])[0]
        generic_name = openfda.get("generic_name", ["Unknown"])[0]
        manufacturer = openfda.get("manufacturer_name", [None])[0]

        warnings_list = result.get("warnings", [])

        return DrugInfo(
            brand_name=brand_name,
            generic_name=generic_name,
            warnings=warnings_list,
            manufacturer=manufacturer,
        )
