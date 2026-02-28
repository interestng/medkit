from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class AskEngine:
    """
    Natural Language Router for MedKit.
    Detects intent and routes queries to the correct providers using
    weighted scoring and regex word boundaries.
    """

    @staticmethod
    def clean_query(query: str) -> str:
        """Strip noise words and routing keywords from the query."""
        # Phrases to remove safely 
        noise_patterns = [
            r"clinical trials? (for|on|about)",
            r"research (on|for|about)",
            r"papers? (about|for|on)",
            r"information about",
            r"info on",
            r"tell me (more )?about",
            r"what (is|are)( the)?",
            r"(common|typical|recent|latest|new)",
            r"side(-| )?effects?( of| for)?",
            r"summarize",
            r"summarise",
            r"summarization",
            r"explanation (of|for)?",
            r"explain",
            r"overview (of|for)?",
            r"briefly",
            r"warnings?( of| for)?",
            r"dosages?( of| for)?",
            r"trials?( for| of)?",
            r"studies( of| for)?",
            r"study( of| for)?",
        ]
        
        q = query.lower()
        for pattern in noise_patterns:
            # Use \b for word boundaries to avoid partial matches
            q = re.sub(rf"\b{pattern}\b", "", q)
            
        # Clean up extra whitespace from deletions
        q = re.sub(r"\s+", " ", q).strip()
        # Strip trailing punctuation (e.g., ?, ., !)
        q = re.sub(r"[?\.!]+$", "", q).strip()
        return q

    @staticmethod
    def route(question: str, capabilities: list[str] | None = None) -> str:
        """
        Route the natural language query to an intent using weighted scoring.
        If 'capabilities' are provided, routes are filtered/prioritized based
        on which providers are actually registered.
        """
        q = question.lower()

        # Intent weights
        scores = {
            "conclude": 0,
            "trials": 0,
            "papers": 0,
            "explain": 0,
            "summary": 0,
        }

        # Mapping intents to capabilities
        intent_to_capability = {
            "conclude": "conclude", # New intent
            "trials": "trials",
            "papers": "papers",
            "explain": "drugs",
            "summary": "drugs",  # Summaries usually need drug info
        }

        # Regex patterns for each intent (word boundaries are critical)
        patterns = {
            "conclude": [
                r"\bconclusion\b", 
                r"\bbottom line\b", 
                r"\bevidences?\b", 
                r"\bsynthesis\b", 
                r"\bconclude\b",
                r"\bconsensus\b",
                r"\bverdict\b",
                r"\boutcomes?\b"
            ],
            "trials": [
                r"\btrials?\b", 
                r"\bstudies\b", 
                r"\bstudy\b", 
                r"\bnct\b"
            ],
            "papers": [
                r"\bpapers?\b",
                r"\bresearch\b",
                r"\bpmids?\b",
                r"\bjournals?\b",
                r"\babstracts?\b",
                r"\barticles?\b",
            ],
            "explain": [
                r"\bdrugs?\b",
                r"\bfda\b",
                r"\blabels?\b",
                r"\bmanufacturers?\b",
                r"\bside(-| )?effects?\b",
                r"\bwarnings?\b",
                r"\bdosages?\b",
            ],
            "summary": [
                r"\bsummaries\b",
                r"\bsummary\b", 
                r"\boverviews?\b", 
                r"\bbriefs?\b",
                r"\bsummarize\b",
                r"\bsummarise\b"
            ],
        }

        # Calculate scores based on keyword presence
        for intent, regex_list in patterns.items():
            for pattern in regex_list:
                if re.search(pattern, q):
                    scores[intent] += 1
            
            # Boost score if capability exists
            if capabilities and intent_to_capability.get(intent) in capabilities:
                if scores[intent] > 0:
                    scores[intent] += 2  # Capability boost

        # Find intent with maximum score
        if not scores:
            return "search"
            
        max_score = max(scores.values())
        if max_score == 0:
            return "search"

        # Get the intent(s) with the highest score
        top_intents = [k for k, v in scores.items() if v == max_score]
        
        # If there's a tie, use a predefined priority (v1.1 logic)
        priority = ["conclude", "explain", "trials", "papers", "summary"]
        
        # Filter priority by capabilities if possible
        if capabilities:
            # Separate capable and non-capable intents, 
            # ensuring 'conclude' is always considered capable
            capable_priority = []
            non_capable_priority = []
            for p in priority:
                if p == "conclude" or intent_to_capability.get(p) in capabilities:
                    capable_priority.append(p)
                else:
                    non_capable_priority.append(p)
            
            # Reconstruct priority with capable intents first, 
            # maintaining relative order
            priority = capable_priority + non_capable_priority

        for p in priority:
            if p in top_intents:
                return p

        return top_intents[0]
