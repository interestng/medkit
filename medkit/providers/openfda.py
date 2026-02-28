from __future__ import annotations

from typing import Any, cast

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
        return ["drugs", "interactions"]

    def get_sync(self, item_id: str) -> DrugInfo:
        return self.search_sync(item_id)

    async def get(self, item_id: str) -> DrugInfo:
        return await self.search(item_id)

    def search_sync(self, query: str, **kwargs) -> DrugInfo:
        search_query = f'openfda.brand_name:"{query}" OR openfda.generic_name:"{query}"'
        try:
            response = cast(httpx.Client, self.http_client).get(
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
        search_query = f'openfda.brand_name:"{query}" OR openfda.generic_name:"{query}"'
        try:
            response = await cast(httpx.AsyncClient, self.http_client).get(
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

    async def check_interactions(self, drugs: list[str]) -> list[dict[str, Any]]:
        """Check for interactions between drugs using label data."""
        if len(drugs) < 2:
            return []

        # Search for labels where interactions mention both drugs
        # We'll check the first drug against the others to find evidence
        interactions = []
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                d1, d2 = drugs[i], drugs[j]
                query = f'drug_interactions:"{d1}" AND drug_interactions:"{d2}"'
                try:
                    response = await cast(httpx.AsyncClient, self.http_client).get(
                        self.BASE_URL, params={"search": query, "limit": 1}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data["results"][0]
                        evidence = result.get("drug_interactions", ["No specific text found."])[0]
                        short_evidence = evidence[:500] + "..." if len(evidence) > 500 else evidence
                        
                        interactions.append({
                            "drugs": [d1, d2],
                            "severity": "Discussed in Label",
                            "risk": f"Potential interaction found in FDA label for {d1}/{d2}.",
                            "evidence": short_evidence
                        })
                except Exception:
                    continue
        return interactions

    def check_interactions_sync(self, drugs: list[str]) -> list[dict[str, Any]]:
        """Synchronous version of interaction check."""
        if len(drugs) < 2:
            return []

        interactions = []
        for i in range(len(drugs)):
            for j in range(i + 1, len(drugs)):
                d1, d2 = drugs[i], drugs[j]
                query = f'drug_interactions:"{d1}" AND drug_interactions:"{d2}"'
                try:
                    response = cast(httpx.Client, self.http_client).get(
                        self.BASE_URL, params={"search": query, "limit": 1}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        result = data["results"][0]
                        evidence = result.get("drug_interactions", ["No specific text found."])[0]
                        short_evidence = evidence[:500] + "..." if len(evidence) > 500 else evidence
                        
                        interactions.append({
                            "drugs": [d1, d2],
                            "severity": "Discussed in Label",
                            "risk": f"Potential interaction found in FDA label for {d1}/{d2}.",
                            "evidence": short_evidence
                        })
                except Exception:
                    continue
        return interactions
