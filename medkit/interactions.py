from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class InteractionWarning(BaseModel):
    severity: str  # High, Moderate, Low
    risk: str
    evidence: str


class InteractionEngine:
    """
    A rule-based engine for detecting drug-drug interactions.
    """

    # Simple rule database for v1.1
    RULES: Dict[str, Dict[str, InteractionWarning]] = {
        "aspirin": {
            "ibuprofen": InteractionWarning(
                severity="Moderate",
                risk="Increased bleeding risk and decreased aspirin effectiveness.",
                evidence="Multiple clinical studies (e.g., FDA labels, PubMed meta-analysis).",
            ),
            "warfarin": InteractionWarning(
                severity="High",
                risk="Significantly increased risk of severe bleeding.",
                evidence="Major clinical contraindication.",
            ),
        },
        "ibuprofen": {
            "naproxen": InteractionWarning(
                severity="Moderate",
                risk="Increased risk of gastrointestinal side effects.",
                evidence="Pharmacological data.",
            )
        },
        "metformin": {
            "contrast": InteractionWarning(
                severity="High",
                risk="Risk of lactic acidosis if iodine contrast is used.",
                evidence="Standard hospital protocol and FDA warning.",
            )
        },
    }

    @classmethod
    def check(cls, drugs: List[str]) -> List[dict]:
        """Check for interactions between a list of drugs."""
        warnings = []
        drugs_lower = [d.lower() for d in drugs]

        for i in range(len(drugs_lower)):
            for j in range(i + 1, len(drugs_lower)):
                d1 = drugs_lower[i]
                d2 = drugs_lower[j]

                # Check d1 against d2 and vice versa
                warn = cls.RULES.get(d1, {}).get(d2) or cls.RULES.get(d2, {}).get(d1)

                if warn:
                    warnings.append({"drugs": [drugs[i], drugs[j]], "warning": warn})
        return warnings
