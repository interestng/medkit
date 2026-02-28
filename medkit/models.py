from __future__ import annotations

from pydantic import BaseModel, Field


class SearchMetadata(BaseModel):
    query_time: float = Field(..., description="Latency of the query in seconds.")
    sources: list[str] = Field(
        default_factory=list, description="List of providers that returned data."
    )
    cached: bool = Field(False, description="Whether the result was served from cache.")


class DrugInfo(BaseModel):
    brand_name: str = Field(..., description="Brand name of the drug.")
    generic_name: str = Field(..., description="Generic name of the drug.")
    warnings: list[str] = Field(
        default_factory=list, description="Warnings associated with the drug."
    )
    manufacturer: str | None = Field(None, description="Manufacturer of the drug.")


class ResearchPaper(BaseModel):
    pmid: str = Field(..., description="PubMed ID.")
    title: str = Field(..., description="Title of the paper.")
    authors: list[str] = Field(default_factory=list, description="List of authors.")
    journal: str = Field(..., description="Journal name.")
    year: int | None = Field(None, description="Year of publication.")
    abstract: str = Field(..., description="Abstract of the paper.")

    @property
    def url(self) -> str:
        return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"


class ClinicalTrial(BaseModel):
    nct_id: str = Field(..., description="ClinicalTrials.gov Identifier (NCT number).")
    title: str = Field(..., description="Title of the clinical trial.")
    status: str = Field(..., description="Recruitment status.")
    phase: list[str] = Field(default_factory=list, description="Phases of the trial.")
    location: list[str] = Field(
        default_factory=list, description="Locations of the trial."
    )
    eligibility: str = Field(..., description="Eligibility criteria.")

    @property
    def url(self) -> str:
        return f"https://clinicaltrials.gov/study/{self.nct_id}"


class DrugExplanation(BaseModel):
    drug_info: DrugInfo | None = Field(
        None, description="FDA information about the drug."
    )
    papers: list[ResearchPaper] = Field(
        default_factory=list, description="Recent research papers related to the drug."
    )
    trials: list[ClinicalTrial] = Field(
        default_factory=list, description="Active clinical trials for the drug."
    )


class SearchResults(BaseModel):
    drugs: list[DrugInfo] = Field(
        default_factory=list, description="Drugs matching the query."
    )
    papers: list[ResearchPaper] = Field(
        default_factory=list, description="Research papers matching the query."
    )
    trials: list[ClinicalTrial] = Field(
        default_factory=list, description="Clinical trials matching the query."
    )
    metadata: SearchMetadata | None = Field(
        None, description="Metadata about the query execution."
    )


class ConditionSummary(BaseModel):
    condition: str = Field(..., description="The medical condition or term.")
    drugs: list[str] = Field(
        default_factory=list, description="Commonly associated drug names."
    )
    papers: list[ResearchPaper] = Field(
        default_factory=list, description="Recent research highlights."
    )
    trials: list[ClinicalTrial] = Field(
        default_factory=list, description="Key recruiting clinical trials."
    )
