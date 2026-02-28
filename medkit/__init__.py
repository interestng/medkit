"""
MedKit - A unified Python SDK for public medical APIs.
"""

from .client import MedKit, AsyncMedKit
from .models import DrugInfo, ResearchPaper, ClinicalTrial, DrugExplanation, SearchResults, ConditionSummary, SearchMetadata
from .graph import MedicalGraph
from .cache import MemoryCache, DiskCache
from .exporter import Exporter
from .interactions import InteractionEngine
from .exceptions import MedKitError, APIError, RateLimitError, NotFoundError, PluginError

__version__ = "0.1.0"
__all__ = [
    "MedKit",
    "AsyncMedKit",
    "DrugInfo",
    "ResearchPaper",
    "ClinicalTrial",
    "DrugExplanation",
    "SearchResults",
    "ConditionSummary",
    "SearchMetadata",
    "MedicalGraph",
    "Exporter",
    "MemoryCache",
    "DiskCache",
    "InteractionEngine",
    "MedKitError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "PluginError",
]
