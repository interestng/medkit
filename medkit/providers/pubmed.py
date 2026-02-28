from __future__ import annotations

from typing import Any, cast

import httpx

from ..exceptions import APIError, NotFoundError
from ..models import ResearchPaper
from .base import BaseProvider


class PubMedProvider(BaseProvider):
    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    def __init__(self, http_client: httpx.Client | httpx.AsyncClient):
        super().__init__(name="pubmed")
        self.http_client = http_client

    def capabilities(self) -> list[str]:
        return ["papers"]

    def get_sync(self, item_id: str) -> ResearchPaper:
        try:
            response = cast(httpx.Client, self.http_client).get(
                self.SUMMARY_URL,
                params={"db": "pubmed", "id": item_id, "retmode": "json"},
            )
            response.raise_for_status()
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found.")
            return results[0]
        except httpx.HTTPError as e:
            raise APIError(f"PubMed API error: {e}") from e

    async def get(self, item_id: str) -> ResearchPaper:
        try:
            response = await cast(httpx.AsyncClient, self.http_client).get(
                self.SUMMARY_URL,
                params={"db": "pubmed", "id": item_id, "retmode": "json"},
            )
            response.raise_for_status()
            results = self._parse_summaries(response.json(), [item_id])
            if not results:
                raise NotFoundError(f"PMID {item_id} not found.")
            return results[0]
        except httpx.HTTPError as e:
            raise APIError(f"PubMed API error: {e}") from e

    def search_sync(self, query: str, **kwargs) -> list[ResearchPaper]:
        limit = kwargs.get("limit", 10)
        try:
            search_response = cast(httpx.Client, self.http_client).get(
                self.SEARCH_URL,
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": limit,
                },
            )
            search_response.raise_for_status()
            pmids = search_response.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            summary_response = cast(httpx.Client, self.http_client).get(
                self.SUMMARY_URL,
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            )
            summary_response.raise_for_status()
            return self._parse_summaries(summary_response.json(), pmids)
        except httpx.HTTPError as e:
            raise APIError(f"PubMed API error: {e}") from e

    async def search(self, query: str, **kwargs) -> list[ResearchPaper]:
        limit = kwargs.get("limit", 10)
        try:
            search_response = await cast(httpx.AsyncClient, self.http_client).get(
                self.SEARCH_URL,
                params={
                    "db": "pubmed",
                    "term": query,
                    "retmode": "json",
                    "retmax": limit,
                },
            )
            search_response.raise_for_status()
            pmids = search_response.json().get("esearchresult", {}).get("idlist", [])

            if not pmids:
                return []

            summary_response = await cast(httpx.AsyncClient, self.http_client).get(
                self.SUMMARY_URL,
                params={"db": "pubmed", "id": ",".join(pmids), "retmode": "json"},
            )
            summary_response.raise_for_status()
            return self._parse_summaries(summary_response.json(), pmids)
        except httpx.HTTPError as e:
            raise APIError(f"PubMed API error: {e}") from e

    def _parse_summaries(
        self, data: dict[str, Any], pmids: list[str]
    ) -> list[ResearchPaper]:
        results = data.get("result", {})
        papers = []

        for pmid in pmids:
            paper_data = results.get(pmid, {})
            if not paper_data or "error" in paper_data:
                continue

            title = paper_data.get("title", "")
            authors = [
                author.get("name", "") for author in paper_data.get("authors", [])
            ]
            journal = paper_data.get("fulljournalname", "")

            pubdate = paper_data.get("pubdate", "")
            year = None
            if pubdate:
                year_str = pubdate.split(" ")[0]
                if year_str.isdigit():
                    year = int(year_str)

            papers.append(
                ResearchPaper(
                    pmid=pmid,
                    title=title,
                    authors=authors,
                    journal=journal,
                    year=year,
                    abstract="",
                )
            )
        return papers
