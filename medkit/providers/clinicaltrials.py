from __future__ import annotations

from typing import Any

import httpx

from ..exceptions import APIError
from ..models import ClinicalTrial
from .base import BaseProvider


class ClinicalTrialsProvider(BaseProvider):
    """
    Provider for ClinicalTrials.gov API v2.
    Note: Some environments may experience 403 Forbidden errors due to strict
    automated-access policies on the NIH servers.
    """

    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"

    def __init__(self, http_client: httpx.Client | httpx.AsyncClient):
        super().__init__(name="clinicaltrials")
        self.http_client = http_client

    def capabilities(self) -> list[str]:
        return ["trials"]

    def get_sync(self, item_id: str) -> ClinicalTrial:
        url = f"{self.BASE_URL}/{item_id}"
        try:
            response = self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            # Wrap in studies list for parsing
            data = {"studies": [response.json()]}
            results = self._parse_response(data)
            return results[0]
        except httpx.HTTPError as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    async def get(self, item_id: str) -> ClinicalTrial:
        url = f"{self.BASE_URL}/{item_id}"
        try:
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
            data = {"studies": [response.json()]}
            results = self._parse_response(data)
            return results[0]
        except httpx.HTTPError as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    def _get_headers(self) -> dict[str, str]:
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

    def search_sync(self, query: str, **kwargs) -> list[ClinicalTrial]:
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting")
        params = {"query.cond": query, "pageSize": limit}
        try:
            response = self.http_client.get(
                self.BASE_URL,
                params=params,
                headers=self._get_headers(),
                follow_redirects=True,
            )  # type: ignore
            response.raise_for_status()
            return self._parse_response(response.json(), recruiting)
        except httpx.HTTPError as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    async def search(self, query: str, **kwargs) -> list[ClinicalTrial]:
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting")
        params = {"query.cond": query, "pageSize": limit}
        try:
            response = await self.http_client.get(
                self.BASE_URL,
                params=params,
                headers=self._get_headers(),
                follow_redirects=True,
            )  # type: ignore
            response.raise_for_status()
            return self._parse_response(response.json(), recruiting)
        except httpx.HTTPError as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    def _parse_response(
        self, data: dict[str, Any], recruiting: bool | None = None
    ) -> list[ClinicalTrial]:
        trials = []
        studies = data.get("studies", [])

        for study in studies:
            protocol = study.get("protocolSection", {})
            identification = protocol.get("identificationModule", {})
            nct_id = identification.get("nctId", "Unknown")
            title = identification.get("briefTitle", "Unknown Trial")

            status_module = protocol.get("statusModule", {})
            overall_status = status_module.get("overallStatus", "Unknown")

            if recruiting is not None:
                is_currently_recruiting = overall_status.upper() == "RECRUITING"
                if recruiting and not is_currently_recruiting:
                    continue
                if not recruiting and is_currently_recruiting:
                    continue

            design = protocol.get("designModule", {})
            phases = design.get("phases", [])

            contacts = protocol.get("contactsLocationsModule", {})
            locations_data = contacts.get("locations", [])
            locations = [
                loc.get("facility", "Unknown Location")
                for loc in locations_data
                if loc.get("facility")
            ]

            eligibility_mod = protocol.get("eligibilityModule", {})
            eligibility_criteria = eligibility_mod.get(
                "eligibilityCriteria", "Not specified"
            )

            trials.append(
                ClinicalTrial(
                    nct_id=nct_id,
                    title=title,
                    status=overall_status,
                    phase=phases,
                    location=locations,
                    eligibility=eligibility_criteria,
                )
            )
        return trials
