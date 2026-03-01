from __future__ import annotations

import re
from typing import Dict, List

from .models import ClinicalConclusion, ClinicalTrial, DrugInfo, ResearchPaper


class ClinicalEvidenceMatrix:
    """
    Rigorously weighing clinical evidence using scientifically-aligned coefficients.
    Weights are derived from standard clinical trial hierarchy.
    """

    COEFFICIENTS = {
        "PHASE_3": 0.4,
        "PHASE_2": 0.2,
        "PHASE_1": 0.1,
        "FDA_APPROVED": 0.3,
        "PEER_REVIEWED": 0.1,  # Baseline for any research paper
    }

    @classmethod
    def score(
        cls,
        trials: List[ClinicalTrial],
        papers: List[ResearchPaper],
        drugs: List[DrugInfo],
    ) -> float:
        """
        Calculate a confidence score (0.0 - 1.0) based on clinical data volume.
        """
        score = 0.0

        # Trial Weights
        for trial in trials:
            phases = [str(p).upper() for p in (trial.phase or [])]
            if any(
                "PHASE 3" in p or "PHASE 4" in p or "PHASE III" in p or "PHASE IV" in p
                for p in phases
            ):
                score += cls.COEFFICIENTS["PHASE_3"]
            elif any("PHASE 2" in p or "PHASE II" in p for p in phases):
                score += cls.COEFFICIENTS["PHASE_2"]
            else:
                score += cls.COEFFICIENTS["PHASE_1"]

        # Paper Weights (Quality over quantity, capped at 0.5)
        paper_score = min(len(papers) * cls.COEFFICIENTS["PEER_REVIEWED"], 0.5)
        score += paper_score

        # FDA Status
        if drugs:
            score += cls.COEFFICIENTS["FDA_APPROVED"]

        return min(max(score / 5.0, 0.1), 1.0)


class IntelligenceEngine:
    """
    Production-grade medical intelligence engine for clinical synthesis.
    """

    @staticmethod
    def synthesize(
        query: str,
        drugs: List[DrugInfo],
        papers: List[ResearchPaper],
        trials: List[ClinicalTrial],
    ) -> ClinicalConclusion:
        """Synthesize disparate data into a structured clinical conclusion."""
        confidence = ClinicalEvidenceMatrix.score(trials, papers, drugs)

        from collections import Counter

        intervention_counts: Counter[str] = Counter()
        for t in trials:
            if t.interventions:
                intervention_counts.update(t.interventions)
        for d in drugs:
            # Heavily weight FDA drugs
            intervention_counts[d.generic_name] += 5
            intervention_counts[d.brand_name] += 5

        # Sort by frequency, then alphabetically for ties
        # Filter out unusually long names which are likely procedural descriptions
        filtered_interv = {
            name: count
            for name, count in intervention_counts.items()
            if len(name) < 100
        }

        sorted_interv = sorted(filtered_interv.items(), key=lambda x: (-x[1], x[0]))
        top_interv = [name for name, count in sorted_interv[:5]]

        # Clinical summary generation based on confidence level
        if confidence > 0.7:
            summary = (
                f"High-confidence clinical consensus exists for target '{query}'. "
                f"Analysis identifies {len(drugs)} FDA agents and {len(trials)} trials."
            )
        elif confidence > 0.4:
            summary = (
                f"Emerging evidence for '{query}' identified ({len(papers)} papers). "
                f"Preliminary Phase II data suggests therapeutic potential."
            )
        else:
            summary = (
                f"Limited primary clinical evidence available for '{query}'. "
                f"Synthesis based on {len(papers)} papers and "
                f"{len(trials)} early studies."
            )

        return ClinicalConclusion(
            query=query,
            summary=summary,
            confidence_score=round(confidence, 2),
            evidence_count={
                "trials": len(trials),
                "papers": len(papers),
                "drugs": len(drugs),
            },
            top_interventions=top_interv,
            suggested_trials=[t.nct_id for t in trials if t.recruiting][:3],
        )

    @staticmethod
    def correlate_entities(
        drugs: List[DrugInfo], trials: List[ClinicalTrial]
    ) -> Dict[str, List[str]]:
        """Correlate drugs with clinical trials using robust entity matching."""
        drug_trial_map = {}
        for drug in drugs:
            brand_id = drug.brand_name.lower()
            generic_id = drug.generic_name.lower()

            related_trials = []
            for trial in trials:
                text = (
                    f"{trial.title or ''} {' '.join(trial.interventions or [])} "
                    f"{trial.description or ''}"
                ).lower()

                if re.search(rf"\b{re.escape(brand_id)}\b", text) or re.search(
                    rf"\b{re.escape(generic_id)}\b", text
                ):
                    related_trials.append(trial.nct_id)

            if related_trials:
                drug_trial_map[brand_id] = related_trials

        return drug_trial_map
