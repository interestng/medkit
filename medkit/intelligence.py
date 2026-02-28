from __future__ import annotations

import re
from typing import Dict, List

from pydantic import BaseModel, Field

from .models import ClinicalTrial, DrugInfo, ResearchPaper


class ClinicalConclusion(BaseModel):
    summary: str = Field(..., description="Synthesized clinical conclusion.")
    evidence_score: float = Field(
        ..., description="Calculated strength of evidence (0.0-1.0)."
    )
    key_findings: List[str] = Field(
        default_factory=list, description="Top clinical take-aways."
    )
    recommendation: str = Field(
        ..., description="Suggested clinical next-step based on data."
    )


class IntelligenceEngine:
    """
    Core engine for medical data synthesis and entity correlation.
    """

    @staticmethod
    def synthesize(
        query: str, 
        drugs: List[DrugInfo], 
        papers: List[ResearchPaper], 
        trials: List[ClinicalTrial]
    ) -> ClinicalConclusion:
        """
        Synthesize disparate data points into a single clinical conclusion.
        """
        # 1. Evidence Scoring Logic (Ultra-Granular)
        score = 0.0
        findings = []

        # FDA Authority (0.15)
        if drugs:
            score += 0.15
            drug_names = [d.brand_name for d in drugs[:2]]
            findings.append(
                f"FDA data available for: {', '.join(drug_names)}."
            )
            
        # Clinical Trial Depth & Quality (Max 0.50)
        p3_trials = []
        p2_trials = []
        p3_regex = re.compile(r"PHASE[ \-]?(3|III)", re.IGNORECASE)
        p2_regex = re.compile(r"PHASE[ \-]?(2|II)", re.IGNORECASE)

        for t in trials:
            phases = [str(p) for p in t.phase]
            if any(p3_regex.search(p) for p in phases):
                p3_trials.append(t)
            elif any(p2_regex.search(p) for p in phases):
                p2_trials.append(t)

        if p3_trials:
            # Phase 3: 0.25 base + 0.05 per trial (higher base to clear 0.50 easily)
            p3_score = min(0.25 + (len(p3_trials) * 0.05), 0.45)
            score += p3_score
            findings.append(
                f"Validated by {len(p3_trials)} Phase III clinical trials."
            )
        
        if p2_trials:
            # Phase 2: 0.10 base + 0.02 per trial
            p2_score = min(0.10 + (len(p2_trials) * 0.02), 0.20)
            score += p2_score
            findings.append(
                f"Includes {len(p2_trials)} mid-stage (Phase II) studies."
            )

        # Research Depth & Recency (Max 0.35)
        from datetime import datetime
        current_year = datetime.now().year
        recent_papers = [p for p in papers if p.year and (current_year - p.year <= 3)]
        
        # Volume bonus: 0.01 per relevant data point found (Total Volume)
        volume_bonus = min((len(trials) + len(papers)) * 0.015, 0.25)
        score += volume_bonus
        
        # Recency bonus: 0.03 per recent paper
        recency_bonus = min(len(recent_papers) * 0.03, 0.10)
        score += recency_bonus
        
        if recent_papers:
            findings.append(
                f"High recent academic activity ({len(recent_papers)} papers)."
            )

        # 2. Results Differentiation (Deterministic Template)
        summary = f"Clinical synthesis for '{query}': "
        
        if score >= 0.7:
            summary += (
                "Highly-validated therapeutic landscape with multi-modal evidence."
            )
            recommendation = (
                "Standard-of-care identified; focus on Phase III long-term outcomes."
            )
        elif score >= 0.5:
            summary += (
                "Strong clinical evidence base found across multiple regulated sources."
            )
            recommendation = (
                "Actionable; prioritize approved labels and late-stage trial cohorts."
            )
        elif score >= 0.3:
            summary += (
                "Emerging clinical consensus with moderate late-stage validation."
            )
            recommendation = (
                "Monitor Phase II/III pivot points for therapeutic changes."
            )
        elif score >= 0.15:
            summary += (
                "Preliminary evidence base characterized by early-phase research."
            )
            recommendation = (
                "Exploratory; focus on mechanistic studies and Phase I/II data."
            )
        else:
            summary += "Sparse clinical evidence found in primary repositories."
            recommendation = (
                "Broaden search parameters or investigate case-study literature."
            )

        return ClinicalConclusion(
            summary=summary,
            evidence_score=round(min(score, 1.0), 2),
            key_findings=findings[:4],
            recommendation=recommendation
        )

    @staticmethod
    def correlate_entities(
        drugs: List[DrugInfo], 
        trials: List[ClinicalTrial]
    ) -> Dict[str, List[str]]:
        """
        Maps drugs to trials based on intervention matching.
        """
        mapping = {}
        for drug in drugs:
            pattern = (
                rf"\b({re.escape(drug.brand_name)}|"
                rf"{re.escape(drug.generic_name)})\b"
            )
            drug_regex = re.compile(pattern, re.IGNORECASE)
            related_trials = []
            for trial in trials:
                if any(drug_regex.search(inter) for inter in trial.interventions):
                    related_trials.append(trial.nct_id)
            mapping[drug.brand_name.lower()] = related_trials
        return mapping
