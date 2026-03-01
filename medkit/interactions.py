from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from .models import InteractionWarning

if TYPE_CHECKING:
    from .providers.openfda import OpenFDAProvider


class InteractionEngine:
    """
    A dynamic engine for detecting drug-drug interactions using OpenFDA labels.
    """

    def __init__(self, client: Any = None):
        # We take a client for compatibility but the check methods use providers
        self.client = client

    @staticmethod
    def _determine_severity(evidence: str) -> str:
        """Heuristic to determine severity from label text."""
        e = evidence.lower()
        high_severity_keywords = [
            "fatal",
            "life-threatening",
            "serious",
            "avoid",
            "contraindicated",
        ]
        if any(w in e for w in high_severity_keywords):
            return "High"
        if any(w in e for w in ["monitor", "caution", "adjustment", "careful"]):
            return "Moderate"
        return "Low"

    async def check(
        self, drugs: List[str], provider: "OpenFDAProvider"
    ) -> List[Dict[str, Any]]:
        """Check for interactions between a list of drugs using live FDA data."""
        if not drugs or len(drugs) < 2:
            return []

        raw_interactions = await provider.check_interactions(drugs)

        warnings = []
        for item in raw_interactions:
            evidence = item.get("evidence", "")
            severity = self._determine_severity(evidence)

            warning = InteractionWarning(
                severity=severity,
                risk=item.get("risk", "Potential interaction detected."),
                evidence=evidence or "Source: OpenFDA Labels",
            )

            warnings.append({"drugs": item["drugs"], "warning": warning})

        return warnings

    def check_sync(
        self, drugs: List[str], provider: "OpenFDAProvider"
    ) -> List[Dict[str, Any]]:
        """Synchronous version of interaction check."""
        if not drugs or len(drugs) < 2:
            return []

        raw_interactions = provider.check_interactions_sync(drugs)

        warnings = []
        for item in raw_interactions:
            evidence = item.get("evidence", "")
            severity = self._determine_severity(evidence)

            warning = InteractionWarning(
                severity=severity,
                risk=item.get("risk", "Potential interaction detected."),
                evidence=evidence or "Source: OpenFDA Labels",
            )

            warnings.append({"drugs": item["drugs"], "warning": warning})

        return warnings
