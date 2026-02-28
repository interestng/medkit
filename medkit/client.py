from __future__ import annotations

import time
from typing import Any, Dict

import httpx

from .ask_engine import AskEngine
from .exceptions import MedKitError, PluginError
from .exporter import Exporter
from .graph import MedicalGraph
from .interactions import InteractionEngine
from .models import (
    ClinicalTrial,
    ConditionSummary,
    DrugExplanation,
    DrugInfo,
    ResearchPaper,
    SearchMetadata,
    SearchResults,
)
from .providers.base import Provider
from .providers.clinicaltrials import ClinicalTrialsProvider
from .providers.openfda import OpenFDAProvider
from .providers.pubmed import PubMedProvider
from .utils import RateLimiter, cache_response, paginate


class AsyncMedKit:
    """
    Asynchronous unified medical developer platform.
    """

    def __init__(
        self, timeout: float = 10.0, max_connections: int = 100, debug: bool = False
    ):
        self.debug = debug
        self._http_client = httpx.AsyncClient(
            timeout=timeout,
            http2=False,
            limits=httpx.Limits(
                max_connections=max_connections, max_keepalive_connections=20
            ),
        )
        self._providers: Dict[str, Provider] = {}
 
        # Register default providers
        self.register_provider(OpenFDAProvider(self._http_client))
        self.register_provider(PubMedProvider(self._http_client))
        self.register_provider(ClinicalTrialsProvider(self._http_client))

        self._pubmed_limiter = RateLimiter(calls=3, period=1.0)
        self._fda_limiter = RateLimiter(calls=40, period=60.0)
        self._trials_limiter = RateLimiter(calls=10, period=1.0)

    def register_provider(self, provider: Provider) -> None:
        """Register a new data provider."""
        if not hasattr(provider, "name") or not provider.name:
            raise PluginError("Provider must have a non-empty 'name' attribute.")
        self._providers[provider.name] = provider
        if self.debug:
            print(f"[MedKit] Registered provider: {provider.name}")

    async def close(self) -> None:
        await self._http_client.aclose()

    async def __aenter__(self) -> AsyncMedKit:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def drug(self, name: str) -> DrugInfo:
        """Search for a drug asynchronously (OpenFDA)."""
        provider = self._providers.get("openfda")
        if not provider:
            raise MedKitError("OpenFDA provider not registered.")
        self._fda_limiter.wait()
        return await provider.search(name)

    async def papers(self, query: str, limit: int = 10) -> list[ResearchPaper]:
        """Search for research papers (PubMed), sorted by year."""
        provider = self._providers.get("pubmed")
        if not provider:
            raise MedKitError("PubMed provider not registered.")
        self._pubmed_limiter.wait()
        results = await provider.search(query, limit=limit)
        return sorted(results, key=lambda p: p.year or 0, reverse=True)

    async def trials(
        self, term: str, recruiting: bool | None = None, limit: int = 10
    ) -> list[ClinicalTrial]:
        """Search for clinical trials (ClinicalTrials.gov)."""
        provider = self._providers.get("clinicaltrials")
        if not provider:
            raise MedKitError("ClinicalTrials provider not registered.")
        self._trials_limiter.wait()
        return await provider.search(term, recruiting=recruiting, limit=limit)

    async def search(self, query: str) -> SearchResults:
        """Unified async search across all providers."""
        start_time = time.time()
        drugs = []
        sources = []
        try:
            drug_info = await self.drug(query)
            drugs = [drug_info]
            sources.append("openfda")
        except MedKitError:
            pass

        try:
            papers = await self.papers(query, limit=5)
            if papers:
                sources.append("pubmed")
        except MedKitError:
            papers = []

        try:
            trials = await self.trials(query, limit=5)
            if trials:
                sources.append("clinicaltrials")
        except MedKitError:
            trials = []

        latency = time.time() - start_time
        metadata = SearchMetadata(query_time=latency, sources=sources, cached=False)

        return SearchResults(
            drugs=drugs, papers=papers, trials=trials, metadata=metadata
        )

    async def explain_drug(self, name: str) -> DrugExplanation:
        """Comprehensive async drug explanation."""
        drug_info = None
        try:
            drug_info = await self.drug(name)
        except MedKitError:
            pass

        try:
            papers = await self.papers(name, limit=5)
        except MedKitError:
            papers = []

        try:
            trials = await self.trials(name, recruiting=True, limit=5)
        except MedKitError:
            trials = []

        return DrugExplanation(drug_info=drug_info, papers=papers, trials=trials)

    async def summary(self, query: str) -> ConditionSummary:
        """Get a high-level summary of a medical condition."""
        results = await self.search(query)
        drug_names = list(
            set(
                [d.generic_name for d in results.drugs]
                + [d.brand_name for d in results.drugs]
            )
        )
        return ConditionSummary(
            condition=query,
            drugs=drug_names[:5],
            papers=results.papers[:5],
            trials=results.trials[:3],
        )

    async def graph(self, query: str) -> MedicalGraph:
        """Build a medical relationship graph."""
        results = await self.search(query)
        graph = MedicalGraph()

        # Add root condition node
        graph.add_node(query.lower(), query.title(), "condition")

        for d in results.drugs:
            graph.add_node(d.brand_name.lower(), d.brand_name, "drug")
            graph.add_edge(d.brand_name.lower(), query.lower(), "treats")

        for p in results.papers:
            graph.add_node(p.pmid, p.title[:30] + "...", "paper")
            graph.add_edge(p.pmid, query.lower(), "researches")

        for t in results.trials:
            graph.add_node(t.nct_id, t.nct_id, "trial")
            graph.add_edge(t.nct_id, query.lower(), "studies")

        return graph

    async def stream_papers(self, query: str, limit: int = 50, chunk_size: int = 10):
        """Stream research papers in chunks."""
        for i in range(0, limit, chunk_size):
            chunk = await self.papers(query, limit=chunk_size)
            if not chunk:
                break
            for paper in chunk:
                yield paper

    def export(self, data: Any, path: str, format: str = "json"):
        """Export data to file."""
        if format.lower() == "csv":
            Exporter.to_csv(data, path)
        else:
            Exporter.to_json(data, path)

    async def interactions(self, drugs: list[str]) -> Any:
        """Check for drug interactions asynchronously using OpenFDA labels."""
        return await InteractionEngine.check(drugs, self._providers["openfda"])

    async def ask(self, question: str) -> Any:
        """Natural language router."""
        intent = AskEngine.route(question)
        cleaned_q = AskEngine.clean_query(question)

        if self.debug:
            print(
                f"[MedKit] Ask intent: {intent} for query: "
                f"'{cleaned_q}' (from '{question}')"
            )

        if intent == "trials":
            return await self.trials(cleaned_q)
        elif intent == "papers":
            return await self.papers(cleaned_q)
        elif intent == "explain":
            return await self.explain_drug(cleaned_q)
        elif intent == "summary":
            return await self.summary(cleaned_q)
        else:
            return await self.search(cleaned_q)


class MedKit:
    """
    Unified medical developer platform.
    """

    def __init__(
        self, timeout: float = 10.0, max_connections: int = 100, debug: bool = False
    ):
        self.debug = debug
        self._http_client = httpx.Client(
            timeout=timeout,
            http2=False,
            limits=httpx.Limits(
                max_connections=max_connections, max_keepalive_connections=20
            ),
        )
        self._providers: Dict[str, Provider] = {}
 
        self.register_provider(OpenFDAProvider(self._http_client))
        self.register_provider(PubMedProvider(self._http_client))
        self.register_provider(ClinicalTrialsProvider(self._http_client))

        self._pubmed_limiter = RateLimiter(calls=3, period=1.0)
        self._fda_limiter = RateLimiter(calls=40, period=60.0)
        self._trials_limiter = RateLimiter(calls=10, period=1.0)

    def register_provider(self, provider: Provider) -> None:
        """Register a new data provider."""
        if not hasattr(provider, "name") or not provider.name:
            raise PluginError("Provider must have a non-empty 'name' attribute.")
        self._providers[provider.name] = provider
        if self.debug:
            print(f"[MedKit] Registered provider: {provider.name}")

    def close(self) -> None:
        self._http_client.close()

    def __enter__(self) -> MedKit:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    @cache_response(maxsize=128)
    def drug(self, name: str) -> DrugInfo:
        provider = self._providers.get("openfda")
        if not provider:
            raise MedKitError("OpenFDA provider not registered.")
        self._fda_limiter.wait()
        return provider.search_sync(name)

    @cache_response(maxsize=128)
    def papers(self, query: str, limit: int = 10) -> list[ResearchPaper]:
        provider = self._providers.get("pubmed")
        if not provider:
            raise MedKitError("PubMed provider not registered.")
        self._pubmed_limiter.wait()
        results = provider.search_sync(query, limit=limit)
        return sorted(results, key=lambda p: p.year or 0, reverse=True)

    @cache_response(maxsize=128)
    def trials(
        self, term: str, recruiting: bool | None = None, limit: int = 10
    ) -> list[ClinicalTrial]:
        provider = self._providers.get("clinicaltrials")
        if not provider:
            raise MedKitError("ClinicalTrials provider not registered.")
        self._trials_limiter.wait()
        return provider.search_sync(term, recruiting=recruiting, limit=limit)

    def search(self, query: str) -> SearchResults:
        start_time = time.time()
        drugs = []
        sources = []
        try:
            drug_info = self.drug(query)
            drugs = [drug_info]
            sources.append("openfda")
        except MedKitError:
            pass

        try:
            papers = self.papers(query, limit=5)
            if papers:
                sources.append("pubmed")
        except MedKitError:
            papers = []

        try:
            trials = self.trials(query, limit=5)
            if trials:
                sources.append("clinicaltrials")
        except MedKitError:
            trials = []

        latency = time.time() - start_time
        metadata = SearchMetadata(query_time=latency, sources=sources, cached=False)

        return SearchResults(
            drugs=drugs, papers=papers, trials=trials, metadata=metadata
        )

    def explain_drug(self, name: str) -> DrugExplanation:
        drug_info = None
        try:
            drug_info = self.drug(name)
        except MedKitError:
            pass

        try:
            papers = self.papers(name, limit=5)
        except MedKitError:
            papers = []

        try:
            trials = self.trials(name, recruiting=True, limit=5)
        except MedKitError:
            trials = []

        return DrugExplanation(drug_info=drug_info, papers=papers, trials=trials)

    def summary(self, query: str) -> ConditionSummary:
        results = self.search(query)
        drug_names = list(
            set(
                [d.generic_name for d in results.drugs]
                + [d.brand_name for d in results.drugs]
            )
        )
        return ConditionSummary(
            condition=query,
            drugs=drug_names[:5],
            papers=results.papers[:5],
            trials=results.trials[:3],
        )

    def graph(self, query: str) -> MedicalGraph:
        """Build a medical relationship graph."""
        results = self.search(query)
        graph = MedicalGraph()

        # Add root condition node
        graph.add_node(query.lower(), query.title(), "condition")

        for d in results.drugs:
            graph.add_node(d.brand_name.lower(), d.brand_name, "drug")
            graph.add_edge(d.brand_name.lower(), query.lower(), "treats")

        for p in results.papers:
            graph.add_node(p.pmid, p.title[:30] + "...", "paper")
            graph.add_edge(p.pmid, query.lower(), "researches")

        for t in results.trials:
            graph.add_node(t.nct_id, t.nct_id, "trial")
            graph.add_edge(t.nct_id, query.lower(), "studies")

        return graph

    def export(self, data: Any, path: str, format: str = "json"):
        """Export data to file."""
        if format.lower() == "csv":
            Exporter.to_csv(data, path)
        else:
            Exporter.to_json(data, path)

    def interactions(self, drugs: list[str]) -> Any:
        """Check for drug interactions using OpenFDA labels."""
        return InteractionEngine.check_sync(drugs, self._providers["openfda"])

    def ask(self, question: str) -> Any:
        """Natural language router."""
        intent = AskEngine.route(question)
        cleaned_q = AskEngine.clean_query(question)

        if self.debug:
            print(
                f"[MedKit] Ask intent: {intent} for query: "
                f"'{cleaned_q}' (from '{question}')"
            )

        if intent == "trials":
            return self.trials(cleaned_q)
        elif intent == "papers":
            return self.papers(cleaned_q)
        elif intent == "explain":
            return self.explain_drug(cleaned_q)
        elif intent == "summary":
            return self.summary(cleaned_q)
        else:
            return self.search(cleaned_q)
