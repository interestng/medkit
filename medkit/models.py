from __future__ import annotations

import time
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class SearchMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query_time: float = Field(..., description="Latency of the query in seconds.")
    sources: List[str] = Field(
        default_factory=list, description="List of providers that returned data."
    )
    cached: bool = Field(False, description="Whether the result was served from cache.")
    offline_providers: List[str] = Field(
        default_factory=list, description="List of providers that were unreachable."
    )


class DrugInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand_name: str = Field(..., description="Brand name of the drug.")
    generic_name: str = Field(..., description="Generic name of the drug.")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the drug.")
    indications: List[str] = Field(
        default_factory=list, description="Indications for the drug."
    )
    interactions: List[str] = Field(
        default_factory=list, description="Known drug interactions."
    )
    dosage_form: Optional[str] = Field(None, description="Dosage form of the drug.")
    route: List[str] = Field(
        default_factory=list, description="Route of administration."
    )


class ResearchPaper(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pmid: str = Field(..., pattern=r"^\d+$", description="PubMed ID.")
    title: str = Field(..., description="Title of the paper.")
    authors: List[str] = Field(default_factory=list, description="List of authors.")
    journal: Optional[str] = Field(None, description="Journal name.")
    year: Optional[int] = Field(None, description="Year of publication.")
    abstract: Optional[str] = Field(None, description="Abstract of the paper.")
    url: Optional[str] = Field(None, description="URL to the paper.")

    @property
    def full_url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


class ClinicalTrial(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nct_id: str = Field(..., description="ClinicalTrials.gov Identifier.")
    title: Optional[str] = Field(None, description="Title of the clinical trial.")
    status: Optional[str] = Field(None, description="Recruitment status.")
    conditions: List[str] = Field(
        default_factory=list, description="Conditions studied."
    )
    description: Optional[str] = Field(None, description="Description of the trial.")
    recruiting: bool = Field(
        False, description="Whether the trial is currently recruiting."
    )
    url: Optional[str] = Field(None, description="URL to the clinical trial.")
    phase: List[str] = Field(default_factory=list, description="Phases of the trial.")
    location: List[str] = Field(
        default_factory=list, description="Locations of the trial."
    )
    eligibility: Optional[str] = Field(None, description="Eligibility criteria.")
    interventions: List[str] = Field(
        default_factory=list, description="Drugs or therapies studied."
    )

    @property
    def full_url(self) -> str:
        return f"https://clinicaltrials.gov/study/{self.nct_id}"


class SearchResults(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drugs: List[DrugInfo] = Field(
        default_factory=list, description="Drugs matching the query."
    )
    papers: List[ResearchPaper] = Field(
        default_factory=list, description="Research papers matching the query."
    )
    trials: List[ClinicalTrial] = Field(
        default_factory=list, description="Clinical trials matching the query."
    )
    metadata: SearchMetadata


class DrugExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    drug_info: Optional[DrugInfo] = Field(
        None, description="FDA information about the drug."
    )
    papers: List[ResearchPaper] = Field(
        default_factory=list, description="Recent research papers."
    )
    trials: List[ClinicalTrial] = Field(
        default_factory=list, description="Active clinical trials."
    )


class ConditionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., description="The medical condition or term.")
    drugs: List[str] = Field(
        default_factory=list, description="Commonly associated drug names."
    )
    papers: List[ResearchPaper] = Field(
        default_factory=list, description="Recent research highlights."
    )
    trials: List[ClinicalTrial] = Field(
        default_factory=list, description="Key recruiting clinical trials."
    )


class ClinicalConclusion(BaseModel):
    """Production-grade evidence synthesis."""

    model_config = ConfigDict(extra="forbid")

    query: str
    summary: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    evidence_count: Dict[str, int]
    top_interventions: List[str]
    suggested_trials: List[str]
    last_updated: float = Field(default_factory=time.time)


class InteractionWarning(BaseModel):
    model_config = ConfigDict(extra="forbid")

    severity: str = Field(..., description="Severity level.")
    risk: str = Field(..., description="Risk description.")
    evidence: str = Field(..., description="Evidence source.")
