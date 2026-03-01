from __future__ import annotations

from typing import TYPE_CHECKING, Union, cast

from .intelligence import IntelligenceEngine
from .models import (
    ClinicalConclusion,
    ConditionSummary,
    DrugExplanation,
    SearchResults,
)

if TYPE_CHECKING:
    from .client import AsyncMedKit, MedKit


class AskEngine:
    """
    High-level orchestration engine for clinical questions.
    Routes queries to appropriate synthesis methods based on intent and complexity.
    """

    def __init__(self, client: Union["MedKit", "AsyncMedKit"]):
        self.client = client
        self.intelligence = IntelligenceEngine()

    def _determine_intent(self, query: str) -> str:
        """Categorize query to decide orchestration strategy."""
        query_lower = query.lower()

        # Drug Detail Intent
        drug_keywords = ["what is", "mechanism", "dose", "dosage", "side effect", "rx"]
        if any(w in query_lower for w in drug_keywords):
            return "explain_drug"

        # Condition Summary Intent
        condition_keywords = ["summary", "overview", "treatments for", "status of"]
        if any(w in query_lower for w in condition_keywords):
            return "summarize_condition"

        return "synthesize"

    def _extract_search_terms(self, query: str) -> str:
        """
        Strip natural language filler to improve API search hits using heuristics.
        """
        import re

        q = query.lower()

        # Typos and common variations
        q = q.replace("clinial", "clinical")

        # Robustly strip common question prefixes/filler
        stop_patterns = [
            r"what (?:is|are) the clinical status of",
            r"what (?:is|are) the status of",
            r"what (?:is|are) clinical trials for",
            r"what (?:is|are|is are)",
            r"clinical status of",
            r"clinical trials for",
            r"overview of",
            r"summary of",
            r"information on",
            r"tell me about",
            r"research for",
            r"papers on",
            r"trials for",
        ]

        for pattern in stop_patterns:
            q = re.sub(pattern, "", q).strip()

        # Heuristic: If "for"/"in" exists after a status-like phrase,
        # we want the part AFTER the preposition (the actual condition).
        # e.g. "status for malignant tumors" -> "malignant tumors"
        prepositions = [" for ", " in ", " with ", " as "]
        for sep in prepositions:
            if sep in q:
                parts = q.split(sep)
                # If the first part is very short or just "status", prioritize the second part
                if any(w in parts[0] for w in ["status", "overview", "summary"]):
                    q = parts[1]
                elif len(parts[0].strip()) < 3:  # "A in B" -> "B"
                    q = parts[1]
                else:
                    # Keep both parts for conditions (e.g. "immunotherapy lung cancer")
                    # But strip the preposition itself for a cleaner search
                    q = f"{parts[0]} {parts[1]}"

        # Final cleanup: strip common leading words that might linger
        q = re.sub(r"^(?:the|of|a|an)\s+", "", q)
        return q.strip("? ").strip()

    async def ask(
        self, query: str
    ) -> Union[DrugExplanation, ConditionSummary, ClinicalConclusion]:
        """Asynchronous entry point for structured clinical queries."""
        from .client import AsyncMedKit

        intent = self._determine_intent(query)
        search_query = self._extract_search_terms(query)
        client = cast(AsyncMedKit, self.client)

        results: SearchResults = await client.search(search_query)

        if intent == "explain_drug" and results.drugs:
            return DrugExplanation(
                drug_info=results.drugs[0],
                papers=results.papers[:5],
                trials=results.trials[:5],
            )
        elif intent == "summarize_condition":
            return ConditionSummary(
                condition=query,
                drugs=[d.brand_name for d in results.drugs[:5]],
                papers=results.papers[:5],
                trials=results.trials[:5],
            )
        else:
            return self.intelligence.synthesize(
                query=query,
                drugs=results.drugs,
                papers=results.papers,
                trials=results.trials,
            )

    def ask_sync(
        self, query: str
    ) -> Union[DrugExplanation, ConditionSummary, ClinicalConclusion]:
        """Synchronous entry point for structured clinical queries."""
        from .client import MedKit

        intent = self._determine_intent(query)
        search_query = self._extract_search_terms(query)
        client = cast(MedKit, self.client)
        results: SearchResults = client.search(search_query)

        if intent == "explain_drug" and results.drugs:
            return DrugExplanation(
                drug_info=results.drugs[0],
                papers=results.papers[:5],
                trials=results.trials[:5],
            )
        elif intent == "summarize_condition":
            return ConditionSummary(
                condition=query,
                drugs=[d.brand_name for d in results.drugs[:5]],
                papers=results.papers[:5],
                trials=results.trials[:5],
            )
        else:
            return self.intelligence.synthesize(
                query=query,
                drugs=results.drugs,
                papers=results.papers,
                trials=results.trials,
            )
