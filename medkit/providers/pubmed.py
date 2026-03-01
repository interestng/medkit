from __future__ import annotations

from typing import Any, Dict, List, cast

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import ResearchPaper
from .base import BaseProvider


class PubMedProvider(BaseProvider):
    """
    Provider for PubMed (NCBI Entrez) API.
    Handles publication search and retrieval.
    """

    def __init__(self, client: httpx.Client | httpx.AsyncClient):
        super().__init__(client)
        self.name = "pubmed"
        self.search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    async def health_check_async(self) -> bool:
        """Check if PubMed API is reachable asynchronously."""
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            resp = await async_client.get(
                self.search_url,
                params={"db": "pubmed", "term": "test", "retmax": 1},
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def health_check(self) -> bool:
        """Check if PubMed API is reachable synchronously."""
        if not isinstance(self.client, httpx.Client):
            return True
        sync_client = cast(httpx.Client, self.client)
        try:
            resp = sync_client.get(
                self.search_url,
                params={"db": "pubmed", "term": "test", "retmax": 1},
                timeout=2.0,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def capabilities(self) -> List[str]:
        return ["papers", "publications", "literature"]

    def _parse_summaries(
        self, data: Dict[str, Any], pmids: List[str]
    ) -> List[ResearchPaper]:
        """Parse PubMed API results into ResearchPaper models."""
        results = data.get("result", {})
        papers = []

        for pmid in pmids:
            paper_data = results.get(pmid, {})
            if not paper_data or "error" in paper_data:
                continue

            title = paper_data.get("title", "Untitled Publication")
            authors = [
                str(author.get("name"))
                for author in paper_data.get("authors", [])
                if author.get("name")
            ]
            journal = paper_data.get("fulljournalname")

            pubdate = paper_data.get("pubdate", "")
            year = None
            if pubdate:
                # Often '2023 May 1' or just '2023'
                year_match = pubdate.split(" ")[0]
                if year_match.isdigit():
                    year = int(year_match)

            try:
                papers.append(
                    ResearchPaper(
                        pmid=pmid,
                        title=title,
                        authors=authors,
                        journal=journal,
                        year=year,
                        abstract=None,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    )
                )
            except Exception:
                continue
        return papers

    def get_sync(self, item_id: str) -> ResearchPaper:
        """Retrieve a single research paper by PMID synchronously."""
        sync_client = cast(httpx.Client, self.client)
        try:
            response = sync_client.get(
                self.summary_url,
                params={"db": "pubmed", "id": item_id, "retmode": "json"},
            )
            response.raise_for_status()
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found in PubMed.")
            return results[0]
        except Exception as e:
            raise APIError(f"PubMed sync get error: {e}")

    async def get(self, item_id: str) -> ResearchPaper:
        """Retrieve a single research paper by PMID asynchronously."""
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            response = await async_client.get(
                self.summary_url,
                params={"db": "pubmed", "id": item_id, "retmode": "json"},
            )
            response.raise_for_status()
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found in PubMed.")
            return results[0]
        except Exception as e:
            raise APIError(f"PubMed async get error: {e}")

    def search_sync(self, query: str, **kwargs: Any) -> List[ResearchPaper]:
        """Search for research papers synchronously."""
        limit = kwargs.get("limit", 10)
        sync_client = cast(httpx.Client, self.client)
        try:
            # Step 1: Search for IDs
            search_res = sync_client.get(
                self.search_url,
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": limit,
                },
            )
            search_res.raise_for_status()
            pmids = search_res.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            # Step 2: Get summaries
            summary_res = sync_client.get(
                self.summary_url,
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            )
            summary_res.raise_for_status()
            return self._parse_summaries(summary_res.json(), pmids)
        except Exception as e:
            raise APIError(f"PubMed sync search error: {e}")

    async def search(self, query: str, **kwargs: Any) -> List[ResearchPaper]:
        """Search for research papers asynchronously."""
        limit = kwargs.get("limit", 10)
        async_client = cast(httpx.AsyncClient, self.client)
        try:
            # Step 1: Search for IDs
            search_res = await async_client.get(
                self.search_url,
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": limit,
                },
            )
            search_res.raise_for_status()
            pmids = search_res.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            # Step 2: Get summaries
            summary_res = await async_client.get(
                self.summary_url,
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            )
            summary_res.raise_for_status()
            return self._parse_summaries(summary_res.json(), pmids)
        except Exception as e:
            raise APIError(f"PubMed async search error: {e}")
