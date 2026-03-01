from __future__ import annotations

import asyncio
import json
import subprocess
from typing import Any, Dict, List, Optional, cast
from urllib.parse import urlencode

import httpx

from ..exceptions import APIError
from ..models import ClinicalTrial
from .base import BaseProvider


class ClinicalTrialsProvider(BaseProvider):
    """
    Provider for ClinicalTrials.gov API.
    Handles searching and retrieving clinical studies with a curl fallback.
    """

    def __init__(self, client: httpx.Client | httpx.AsyncClient):
        super().__init__(client)
        self.name = "clinicaltrials"
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) "
                "Gecko/20100101 Firefox/110.0"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
        }

    def _curl_fetch(self, url: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Fallback to system curl to bypass TLS fingerprinting blocks."""
        cmd = ["curl", "-s", "-L", "--connect-timeout", "10", "--compressed"]
        for k, v in self.headers.items():
            cmd.extend(["-H", f"{k}: {v}"])

        full_url = url
        if params:
            full_url = f"{url}?{urlencode(params)}"
        cmd.append(full_url)

        try:
            result = subprocess.run(cmd, capture_output=True, check=True)
            return result.stdout.decode("utf-8", errors="replace")
        except Exception:
            return ""

    def _parse_study(self, study: Dict[str, Any]) -> ClinicalTrial:
        """Parse raw study data into a ClinicalTrial model."""
        try:
            protocol = study.get("protocolSection", {})
            id_info = protocol.get("identificationModule", {})

            # Robust NCT ID extraction with whitespace stripping
            raw_nct = id_info.get("nctId", study.get("nctId", "NCT00000000"))
            nct_id = str(raw_nct).strip() if raw_nct else "NCT00000000"

            # Basic validation to avoid breaking Pydantic types if any
            if not nct_id.startswith("NCT") or len(nct_id) < 3:
                nct_id = "NCT00000000"

            status_info = protocol.get("statusModule", {})
            description_info = protocol.get("descriptionModule", {})
            conditions_info = protocol.get("conditionsModule", {})
            arms_info = protocol.get("armsInterventionsModule", {})
            design_info = protocol.get("designModule", {})
            eligibility_info = protocol.get("eligibilityModule", {})

            phases = cast(List[str], design_info.get("phases", []))

            # Filter for meaningful interventions (Drugs and Biologicals)
            relevant_types = ["DRUG", "BIOLOGICAL", "COMBINATION_PRODUCT"]
            interventions = [
                str(i.get("name", ""))
                for i in arms_info.get("interventions", [])
                if i.get("name")
                and (not i.get("type") or i.get("type").upper() in relevant_types)
            ]

            return ClinicalTrial(
                nct_id=nct_id,
                title=id_info.get("briefTitle", "N/A"),
                status=status_info.get("overallStatus", "UNKNOWN"),
                conditions=conditions_info.get("conditions", []),
                description=description_info.get("briefSummary", "N/A"),
                recruiting=status_info.get("overallStatus")
                in ["RECRUITING", "AVAILABLE"],
                url=f"https://clinicaltrials.gov/study/{nct_id}",
                phase=phases,
                location=[],
                eligibility=eligibility_info.get("eligibilityCriteria"),
                interventions=interventions,
            )
        except Exception:
            return ClinicalTrial(
                nct_id="NCT00000000",
                title="Unknown Study",
                status="UNKNOWN",
                conditions=[],
                description="Failed to parse details.",
                recruiting=False,
                url="https://clinicaltrials.gov/",
                phase=[],
                location=[],
                eligibility=None,
                interventions=[],
            )

    async def health_check_async(self) -> bool:
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                self.base_url, params={"pageSize": 1}, headers=self.headers, timeout=2.0
            )
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        res = await asyncio.get_event_loop().run_in_executor(
            None, self._curl_fetch, self.base_url, {"pageSize": 1}
        )
        return bool(res and '"studies"' in res)

    def health_check(self) -> bool:
        if not isinstance(self.client, httpx.Client):
            return True
        sync_client = cast(httpx.Client, self.client)
        try:
            resp = sync_client.get(
                self.base_url, params={"pageSize": 1}, headers=self.headers, timeout=2.0
            )
            if resp.status_code == 200:
                return True
        except Exception:
            pass
        res = self._curl_fetch(self.base_url, {"pageSize": 1})
        return bool(res and '"studies"' in res)

    def capabilities(self) -> List[str]:
        return ["trials", "studies", "recruitment"]

    def search_sync(self, query: str, **kwargs: Any) -> List[ClinicalTrial]:
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting", False)
        params = {"pageSize": limit, "query.term": query}
        if recruiting:
            params["filter.overallStatus"] = "RECRUITING"

        if isinstance(self.client, httpx.Client):
            try:
                resp = self.client.get(
                    self.base_url, params=params, headers=self.headers, timeout=5.0
                )
                resp.raise_for_status()
                studies = resp.json().get("studies", [])
                return [self._parse_study(s) for s in studies]
            except Exception:
                pass

        # Fallback to curl
        res = self._curl_fetch(self.base_url, params)
        if res:
            try:
                data = json.loads(res)
                studies = data.get("studies", [])
                return [self._parse_study(s) for s in studies]
            except Exception:
                pass
        return []

    async def search(self, query: str, **kwargs: Any) -> List[ClinicalTrial]:
        limit = kwargs.get("limit", 10)
        recruiting = kwargs.get("recruiting", False)
        params = {"pageSize": limit, "query.term": query}
        if recruiting:
            params["filter.overallStatus"] = "RECRUITING"

        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                self.base_url, params=params, headers=self.headers, timeout=5.0
            )
            resp.raise_for_status()
            studies = resp.json().get("studies", [])
            return [self._parse_study(s) for s in studies]
        except Exception:
            pass

        # Fallback to curl
        res = await asyncio.get_event_loop().run_in_executor(
            None, self._curl_fetch, self.base_url, params
        )
        if res:
            try:
                data = json.loads(res)
                studies = data.get("studies", [])
                return [self._parse_study(s) for s in studies]
            except Exception:
                pass
        return []

    def get_sync(self, item_id: str) -> ClinicalTrial:
        if not isinstance(self.client, httpx.Client):
            return self._parse_study({"nctId": item_id})
        try:
            resp = self.client.get(f"{self.base_url}/{item_id}", headers=self.headers)
            resp.raise_for_status()
            return self._parse_study(resp.json())
        except Exception as e:
            raise APIError(f"ClinicalTrials.gov sync API error for {item_id}: {e}")

    async def get(self, item_id: str) -> ClinicalTrial:
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                f"{self.base_url}/{item_id}", headers=self.headers
            )
            resp.raise_for_status()
            return self._parse_study(resp.json())
        except Exception as e:
            raise APIError(f"ClinicalTrials.gov async API error for {item_id}: {e}")
