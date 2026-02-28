from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .client import MedKit, AsyncMedKit

class AskEngine:
    """
    Natural Language Router for MedKit.
    Detects intent and routes queries to the correct providers.
    """

    @staticmethod
    def clean_query(query: str) -> str:
        """Strip noise words from the query."""
        noise_words = [
            "clinical trials for", "clinical trial for", "trials for", "trial for",
            "research on", "research for", "papers about", "papers for", "paper on",
            "information about", "info on", "tell me about", "what is", "what are"
        ]
        q = query.lower()
        for word in noise_words:
            q = q.replace(word, "")
        return q.strip()

    @staticmethod
    def route(question: str) -> str:
        """Route the natural language query to an intent."""
        q = question.lower()
        
        # Simple keyword-based intent detection
        if any(w in q for w in ["trial", "study", "nct"]):
            return "trials"
        if any(w in q for w in ["paper", "research", "pmid", "journal", "abstract", "article"]):
            return "papers"
        if any(w in q for w in ["drug", "fda", "label", "manufacturer", "side effect", "warning"]):
            return "explain"
        if any(w in q for w in ["summary", "overview", "brief"]):
            return "summary"
            
        return "search"
