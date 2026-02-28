from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

from .models import InteractionWarning

if TYPE_CHECKING:
    from .providers.openfda import OpenFDAProvider


class InteractionEngine:
    """
    A dynamic engine for detecting drug-drug interactions using OpenFDA labels.
    """

    @classmethod
    async def check(
        cls, drugs: List[str], provider: OpenFDAProvider
    ) -> List[Dict[str, Any]]:
        """Check for interactions between a list of drugs using live FDA data."""
        if not drugs or len(drugs) < 2:
            return []

        raw_interactions = await provider.check_interactions(drugs)
        
        warnings = []
        for item in raw_interactions:
            warning = InteractionWarning(
                severity=item.get("severity", "N/A"),
                risk=item.get("risk", "Potential interaction detected."),
                evidence=item.get("evidence", "Source: OpenFDA Labels")
            )
            
            warnings.append({
                "drugs": item["drugs"],
                "warning": warning
            })
            
        return warnings

    @classmethod
    def check_sync(
        cls, drugs: List[str], provider: OpenFDAProvider
    ) -> List[Dict[str, Any]]:
        """Synchronous version of interaction check."""
        if not drugs or len(drugs) < 2:
            return []

        raw_interactions = provider.check_interactions_sync(drugs)
        
        warnings = []
        for item in raw_interactions:
            warning = InteractionWarning(
                severity=item.get("severity", "N/A"),
                risk=item.get("risk", "Potential interaction detected."),
                evidence=item.get("evidence", "Source: OpenFDA Labels")
            )
            
            warnings.append({
                "drugs": item["drugs"],
                "warning": warning
            })
            
        return warnings
