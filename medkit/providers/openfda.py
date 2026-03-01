from __future__ import annotations

from typing import Any, Dict, List, cast

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import DrugInfo
from .base import BaseProvider


class OpenFDAProvider(BaseProvider):
    """
    Provider for OpenFDA API.
    Handles drug labeling and pharmacovigilance data.
    """

    def __init__(self, client: httpx.Client | httpx.AsyncClient):
        super().__init__(client)
        self.name = "openfda"
        self.base_url = "https://api.fda.gov/drug/label.json"

    async def health_check_async(self) -> bool:
        """Check if OpenFDA API is reachable asynchronously."""
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                self.base_url, params={"limit": 1}, timeout=2.0
            )
            return resp.status_code == 200
        except Exception:
            return False

    def health_check(self) -> bool:
        """Check if OpenFDA API is reachable synchronously."""
        if not isinstance(self.client, httpx.Client):
            return True  # Avoid blocking if client is async
        sync_client = cast(httpx.Client, self.client)
        try:
            resp = sync_client.get(self.base_url, params={"limit": 1}, timeout=2.0)
            return resp.status_code == 200
        except Exception:
            return False

    def capabilities(self) -> List[str]:
        return ["drugs", "labels", "interactions", "pharmacology"]

    def _parse_drug(self, data: Dict[str, Any]) -> DrugInfo:
        """Parse raw OpenFDA result into a DrugInfo model."""
        openfda = data.get("openfda", {})

        brand_names = openfda.get("brand_name", ["Unknown"])
        generic_names = openfda.get("generic_name", ["Unknown"])

        brand_name = brand_names[0] if isinstance(brand_names, list) else brand_names
        generic_name = (
            generic_names[0] if isinstance(generic_names, list) else generic_names
        )

        # Expanded interaction retrieval
        # OpenFDA label paths are inconsistent; check common ones
        interaction_fields = [
            "drug_interactions",
            "drug_and_or_laboratory_test_interactions",
            "precautions",
            "warnings",
        ]

        interactions = []
        for field in interaction_fields:
            val = data.get(field, [])
            if isinstance(val, str):
                interactions.append(val)
            elif isinstance(val, list):
                interactions.extend([str(i) for i in val])

        indications = data.get("indications_and_usage", [])
        if isinstance(indications, str):
            indications = [indications]
        elif isinstance(indications, list):
            indications = [str(i) for i in indications]

        return DrugInfo(
            brand_name=brand_name,
            generic_name=generic_name,
            manufacturer=openfda.get("manufacturer_name", [None])[0],
            indications=indications,
            interactions=interactions,
            dosage_form=openfda.get("dosage_form", [None])[0],
            route=openfda.get("route", []),
        )

    def get_sync(self, item_id: str) -> DrugInfo:
        """Fetch drug by application number or ID synchronously."""
        sync_client = cast(httpx.Client, self.client)
        try:
            response = sync_client.get(
                self.base_url, params={"search": f'id:"{item_id}"'}
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                raise NotFoundError(f"Drug ID {item_id} not found.")
            return self._parse_drug(results[0])
        except Exception as e:
            raise APIError(f"OpenFDA sync get error: {e}")

    async def get(self, item_id: str) -> DrugInfo:
        """Fetch drug by application number or ID asynchronously."""
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            response = await async_client.get(
                self.base_url, params={"search": f'id:"{item_id}"'}
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            if not results:
                raise NotFoundError(f"Drug ID {item_id} not found.")
            return self._parse_drug(results[0])
        except Exception as e:
            raise APIError(f"OpenFDA async get error: {e}")

    def search_sync(self, query: str, **kwargs: Any) -> List[DrugInfo]:
        """Search for drugs synchronously."""
        limit = kwargs.get("limit", 1)
        sync_client = cast(httpx.Client, self.client)
        try:
            # Enhanced search query to catch more generic/brand overlaps
            search_query = (
                f'openfda.brand_name:"{query}" openfda.generic_name:"{query}"'
            )
            response = sync_client.get(
                self.base_url, params={"search": search_query, "limit": limit}
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return [self._parse_drug(r) for r in results]
        except Exception:
            return []

    async def search(self, query: str, **kwargs: Any) -> List[DrugInfo]:
        """Search for drugs asynchronously."""
        limit = kwargs.get("limit", 1)
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            search_query = (
                f'openfda.brand_name:"{query}" openfda.generic_name:"{query}"'
            )
            response = await async_client.get(
                self.base_url, params={"search": search_query, "limit": limit}
            )
            response.raise_for_status()
            results = response.json().get("results", [])
            return [self._parse_drug(r) for r in results]
        except Exception:
            return []

    def check_interactions_sync(self, drugs: List[str]) -> List[Dict[str, Any]]:
        """Check for interactions between drugs using labels (sync)."""
        if len(drugs) < 2:
            return []

        # Heuristic keywords for cross-referencing
        # e.g. Aspirin label mentions "anticoagulants" (Warfarin)
        drug_synonyms = {
            "warfarin": ["anticoagulant", "blood thinner", "coumadin", "jantoven"],
            "aspirin": ["nsaid", "salicylates", "platelet inhibitor"],
            "metformin": ["biguanide", "antidiabetic"],
        }

        found = []
        # Check intersections in both directions for robustness
        for i, drug_a in enumerate(drugs):
            info_list = self.search_sync(drug_a, limit=1)
            if not info_list:
                continue

            drug_info = info_list[0]
            label_text = " ".join(drug_info.interactions).lower()

            for j, drug_b in enumerate(drugs):
                if i == j:
                    continue

                target_keys = [drug_b.lower()] + drug_synonyms.get(drug_b.lower(), [])

                for key in target_keys:
                    if key in label_text:
                        # Find the specific evidence snippet
                        evidence = "Source: FDA Label. "
                        for snippet in drug_info.interactions:
                            if key in snippet.lower():
                                evidence = snippet
                                break

                        found.append(
                            {
                                "drugs": [drug_a, drug_b],
                                "evidence": evidence,
                                "risk": (
                                    f"Potential interaction identified "
                                    f"between {drug_a} and {drug_b}."
                                ),
                            }
                        )
                        break
        return found

    async def check_interactions(self, drugs: List[str]) -> List[Dict[str, Any]]:
        """Check for interactions between drugs using labels (async)."""
        if len(drugs) < 2:
            return []

        drug_synonyms = {
            "warfarin": ["anticoagulant", "blood thinner", "coumadin", "jantoven"],
            "aspirin": ["nsaid", "salicylates", "platelet inhibitor"],
        }

        found = []
        for i, drug_a in enumerate(drugs):
            info_list = await self.search(drug_a, limit=1)
            if not info_list:
                continue

            drug_info = info_list[0]
            label_text = " ".join(drug_info.interactions).lower()

            for j, drug_b in enumerate(drugs):
                if i == j:
                    continue

                target_keys = [drug_b.lower()] + drug_synonyms.get(drug_b.lower(), [])
                for key in target_keys:
                    if key in label_text:
                        evidence = "Source: FDA Label. "
                        for snippet in drug_info.interactions:
                            if key in snippet.lower():
                                evidence = snippet
                                break
                        found.append(
                            {
                                "drugs": [drug_a, drug_b],
                                "evidence": evidence,
                                "risk": (
                                    f"Potential interaction identified "
                                    f"between {drug_a} and {drug_b}."
                                ),
                            }
                        )
                        break
        return found
