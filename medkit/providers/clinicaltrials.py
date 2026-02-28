import json
import urllib.parse
import urllib.request
from typing import Any

from ..exceptions import APIError
from ..models import ClinicalTrial
from .base import BaseProvider


class ClinicalTrialsProvider(BaseProvider):
    """
    Provider for ClinicalTrials.gov API v2.
    Note: Some environments may experience 403 Forbidden errors due to strict
    automated-access policies on the NIH servers.
    """

    BASE_URL = "https://www.clinicaltrials.gov/api/v2/studies"

    def __init__(self, http_client: Any = None):
        super().__init__(name="clinicaltrials")
        # http_client is ignored, we use urllib for 403 bypass

    def capabilities(self) -> list[str]:
        return ["trials"]

    def get_sync(self, item_id: str) -> ClinicalTrial:
        encoded_id = urllib.parse.quote(item_id)
        url = f"{self.BASE_URL}/{encoded_id}"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                # Wrap in studies list for parsing
                # (v2 single study returns study object)
                results = self._parse_response({"studies": [data]})
                return results[0]
        except Exception as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    async def get(self, item_id: str) -> ClinicalTrial:
        # Run sync version in thread for simplicity & reliability
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.get_sync, item_id)

    def _get_headers(self) -> dict[str, str]:
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        return {
            "User-Agent": ua,
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.clinicaltrials.gov/",
            "Cache-Control": "no-cache",
            "Sec-Ch-Ua": (
                '"Chromium";v="120", "Not(A:Brand)";v="24", '
                '"Google Chrome";v="120"'
            ),
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }

    def search_sync(self, query: str, **kwargs) -> list[ClinicalTrial]:
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting")
        encoded_query = urllib.parse.quote(query)
        url = f"{self.BASE_URL}?query.cond={encoded_query}&pageSize={limit}"
        try:
            req = urllib.request.Request(url, headers=self._get_headers())
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                return self._parse_response(data, recruiting)
        except Exception as e:
            raise APIError(f"ClinicalTrials.gov API error: {e}") from e

    async def search(self, query: str, **kwargs) -> list[ClinicalTrial]:
        # Run sync version in thread to bypass httpx-specific blocking
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.search_sync(query, **kwargs)
        )

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

            # Extract interventions (drugs/therapies)
            arms_int = protocol.get("armsInterventionsModule", {})
            interventions = [
                inter.get("name", "Unknown")
                for inter in arms_int.get("interventions", [])
                if inter.get("name")
            ]

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
                    interventions=interventions,
                )
            )
        return trials
