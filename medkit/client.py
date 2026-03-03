from __future__ import annotations

import abc
import asyncio
import os
import time
from typing import TYPE_CHECKING, Any, Dict, List, Union, cast

import httpx

if TYPE_CHECKING:
    from .config import MedKitConfig


from .ask_engine import AskEngine
from .cache_backends import DiskCache, MemoryCache
from .exceptions import APIError, MedKitError, PluginError, RateLimitError
from .graph import MedicalGraph
from .intelligence import IntelligenceEngine
from .interactions import InteractionEngine
from .models import (
    ClinicalConclusion,
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
from .utils import AsyncRateLimiter, RateLimiter

if TYPE_CHECKING:
    pass


class BaseMedKit(abc.ABC):
    """
    Base class for MedKit developer platform.
    Shares common provider registration, routing, and error handling logic.
    """

    def __init__(self, debug: bool = False):
        self.debug = debug
        self._providers: Dict[str, Provider] = {}
        if os.getenv("MEDKIT_TESTING"):
            self.cache: Any = MemoryCache()
        else:
            self.cache = DiskCache()

    def register_provider(self, provider: Provider) -> None:
        """Register a new data provider."""
        if not hasattr(provider, "name") or not provider.name:
            raise PluginError("Provider must have a non-empty 'name' attribute.")
        self._providers[provider.name] = provider

    def _handle_provider_error(self, provider_name: str, error: Exception) -> None:
        """Unified error handler for provider failures."""
        if not isinstance(error, MedKitError):
            if isinstance(error, (httpx.ConnectError, httpx.TimeoutException)):
                raise APIError(f"Connection failure from {provider_name}: {error}")
            elif isinstance(error, httpx.HTTPStatusError):
                if error.response.status_code == 429:
                    raise RateLimitError(f"Rate limit exceeded for {provider_name}")
                raise APIError(f"{provider_name} API returned {error.response.status_code}")
        raise error

    def _get_provider(self, name: str) -> Provider:
        provider = self._providers.get(name)
        if not provider:
            raise PluginError(f"Provider '{name}' not registered.")
        return provider


class AsyncMedKit(BaseMedKit):
    """Asynchronous unified medical developer platform."""

    def __init__(self, config: MedKitConfig | None = None, debug: bool = False):
        super().__init__(debug=debug)
        from .config import MedKitConfig

        self.config = config or MedKitConfig()

        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
            keepalive_expiry=self.config.keepalive_expiry,
        )

        # Determine global client settings
        client_kwargs = {
            "timeout": self.config.timeout,
            "limits": limits,
            "http2": self.config.http2,
        }

        # Avoid passing `trust_env` or `verify` unless explicitly configured later,
        # but configure base properties

        # Use a modern browser User-Agent to avoid API blocks
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        self._http_client = httpx.AsyncClient(
            timeout=client_kwargs["timeout"],  # type: ignore
            limits=client_kwargs["limits"],  # type: ignore
            http2=client_kwargs["http2"],  # type: ignore
            headers=default_headers,
        )
        self._pubmed_limiter = AsyncRateLimiter(3, 1.0)
        self._fda_limiter = AsyncRateLimiter(5, 1.0)
        self._trials_limiter = AsyncRateLimiter(5, 1.0)

        # Built-in providers
        self.register_provider(OpenFDAProvider(self._http_client))
        self.register_provider(PubMedProvider(self._http_client))

        # ClinicalTrials specific overrides (e.g. forced HTTP/1.1)
        ct_headers = default_headers.copy()
        ct_headers["Connection"] = "close"
        self._ct_client = httpx.AsyncClient(
            timeout=client_kwargs["timeout"],  # type: ignore
            limits=client_kwargs["limits"],  # type: ignore
            http2=False,
            headers=ct_headers,
        )
        self.register_provider(ClinicalTrialsProvider(self._ct_client))

    async def __aenter__(self) -> AsyncMedKit:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self._http_client.aclose()
        await self._ct_client.aclose()

    async def search(self, query: str) -> SearchResults:
        """Unified search across all registered providers."""
        start_time = time.perf_counter()

        offline_providers = []

        async def _safe_search(name: str, limiter: AsyncRateLimiter) -> Any:
            await limiter.wait()
            try:
                prov = self._get_provider(name)
                # First check health to avoid slow timeout hangs if provider is dead
                if not await prov.health_check_async():
                    offline_providers.append(name)
                    return []
                res = await prov.search(query)
                return res if res is not None else []
            except Exception as e:
                offline_providers.append(name)
                if self.debug:
                    print(f"Async provider {name} error: {e}")
                return []

        fda_task = _safe_search("openfda", self._fda_limiter)
        pubmed_task = _safe_search("pubmed", self._pubmed_limiter)
        trials_task = _safe_search("clinicaltrials", self._trials_limiter)

        fda_res, pubmed_res, trials_res = await asyncio.gather(fda_task, pubmed_task, trials_task)

        metadata = SearchMetadata(
            query_time=time.perf_counter() - start_time,
            sources=list(self._providers.keys()),
            cached=False,
            offline_providers=offline_providers,
        )

        return SearchResults(
            drugs=fda_res if isinstance(fda_res, list) else [fda_res] if fda_res else [],
            papers=pubmed_res
            if isinstance(pubmed_res, list)
            else [pubmed_res]
            if pubmed_res
            else [],
            trials=trials_res
            if isinstance(trials_res, list)
            else [trials_res]
            if trials_res
            else [],
            metadata=metadata,
        )

    async def ask(self, query: str) -> Union[DrugExplanation, ConditionSummary, ClinicalConclusion]:
        """High-level clinical question answering."""
        engine = AskEngine(self)
        return await engine.ask(query)

    async def graph(self, query: str) -> MedicalGraph:
        """Build a relationship graph for a query term."""
        results = await self.search(query)
        graph = MedicalGraph()

        # Add explicit FDA drugs as nodes
        for drug in results.drugs:
            graph.add_node(drug.brand_name, drug.brand_name, "drug")

        # Add Research Papers
        for paper in results.papers:
            graph.add_node(paper.pmid, paper.title[:50] + "...", "paper")

        # Track which interventions we've already added as generic drug nodes
        known_interventions = {d.brand_name.lower() for d in results.drugs}

        # Add Clinical Trials and map their interventions
        for trial in results.trials:
            display_title = (trial.title[:50] + "...") if trial.title else trial.nct_id
            graph.add_node(trial.nct_id, display_title, "trial")
            
            if trial.interventions:
                for intervention in trial.interventions:
                    clean_name = intervention.split(" ")[0] # Grab primary drug name
                    
                    # If this intervention wasn't in the FDA drug list, add it as a new node
                    if clean_name.lower() not in known_interventions and len(clean_name) > 3:
                        graph.add_node(clean_name, clean_name.title(), "drug")
                        known_interventions.add(clean_name.lower())
                    
                    # Link the drug to the trial
                    graph.add_edge(clean_name, trial.nct_id, "intervenes")

        return graph

    async def interactions(self, drugs: List[str]) -> List[Dict[str, Any]]:
        engine = InteractionEngine(self)
        provider = cast(OpenFDAProvider, self._get_provider("openfda"))
        return await engine.check(drugs, provider)


class MedKit(BaseMedKit):
    """Synchronous unified medical developer platform."""

    def __init__(self, config: MedKitConfig | None = None, debug: bool = False):
        super().__init__(debug=debug)
        from .config import MedKitConfig

        self.config = config or MedKitConfig()

        limits = httpx.Limits(
            max_connections=self.config.max_connections,
            max_keepalive_connections=self.config.max_keepalive_connections,
            keepalive_expiry=self.config.keepalive_expiry,
        )

        # Use a modern browser User-Agent to avoid API blocks
        default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        self._http_client = httpx.Client(
            timeout=self.config.timeout,
            limits=limits,
            http2=self.config.http2,
            headers=default_headers,
        )
        self._pubmed_limiter = RateLimiter(3, 1.0)
        self._fda_limiter = RateLimiter(5, 1.0)
        self._trials_limiter = RateLimiter(5, 1.0)

        self.register_provider(OpenFDAProvider(self._http_client))
        self.register_provider(PubMedProvider(self._http_client))

        # ClinicalTrials specific overrides (e.g. forced HTTP/1.1)
        ct_headers = default_headers.copy()
        ct_headers["Connection"] = "close"
        self._ct_client = httpx.Client(
            timeout=self.config.timeout, limits=limits, http2=False, headers=ct_headers
        )
        self.register_provider(ClinicalTrialsProvider(self._ct_client))

    def __enter__(self) -> MedKit:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self._http_client.close()
        self._ct_client.close()

    def search(self, query: str) -> SearchResults:
        """Unified search across all registered providers."""
        start_time = time.perf_counter()

        offline_providers = []

        def _safe_call(name: str) -> Any:
            try:
                prov = self._get_provider(name)
                if not prov.health_check():
                    offline_providers.append(name)
                    return []
                res = prov.search_sync(query)
                return res if res is not None else []
            except Exception as e:
                offline_providers.append(name)
                if self.debug:
                    print(f"Sync provider {name} error: {e}")
                return []

        fda_res = _safe_call("openfda")
        pubmed_res = _safe_call("pubmed")
        trials_res = _safe_call("clinicaltrials")

        metadata = SearchMetadata(
            query_time=time.perf_counter() - start_time,
            sources=list(self._providers.keys()),
            cached=False,
            offline_providers=offline_providers,
        )

        return SearchResults(
            drugs=fda_res if isinstance(fda_res, list) else [fda_res] if fda_res else [],
            papers=pubmed_res
            if isinstance(pubmed_res, list)
            else [pubmed_res]
            if pubmed_res
            else [],
            trials=trials_res
            if isinstance(trials_res, list)
            else [trials_res]
            if trials_res
            else [],
            metadata=metadata,
        )

    def ask(self, query: str) -> Union[DrugExplanation, ConditionSummary, ClinicalConclusion]:
        engine = AskEngine(self)
        return engine.ask_sync(query)

    def drug(self, name: str) -> DrugInfo:
        results = self._get_provider("openfda").search_sync(name)
        if not results:
            raise MedKitError(f"Drug '{name}' not found.")
        return cast(DrugInfo, results[0])

    def papers(self, query: str, limit: int = 10) -> List[ResearchPaper]:
        return cast(
            List[ResearchPaper], self._get_provider("pubmed").search_sync(query, limit=limit)
        )

    def trials(
        self, condition: str, limit: int = 10, recruiting: bool = False
    ) -> List[ClinicalTrial]:
        return cast(
            List[ClinicalTrial],
            self._get_provider("clinicaltrials").search_sync(
                condition, limit=limit, recruiting=recruiting
            ),
        )

    def interactions(self, drugs: List[str]) -> List[Dict[str, Any]]:
        engine = InteractionEngine(self)
        provider = cast(OpenFDAProvider, self._get_provider("openfda"))
        return engine.check_sync(drugs, provider)

    def conclude(self, query: str) -> ClinicalConclusion:
        results = self.search(query)
        intelligence = IntelligenceEngine()
        return intelligence.synthesize(query, results.drugs, results.papers, results.trials)
