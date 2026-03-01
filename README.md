# 🏥 MedKit: A Unified Platform for Medical Data APIs

[![CI Status](https://img.shields.io/badge/CI-passing-success)](https://github.com/interestng/medkit/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-2.0.0-orange)](https://pypi.org/project/medkit-sdk/)

MedKit is a high-performance, unified SDK that transforms fragmented medical APIs into a single, programmable platform. It provides a clean interface for **OpenFDA**, **PubMed**, and **ClinicalTrials.gov**, augmented with a clinical intelligence layer and relationship mapping.

> [!IMPORTANT]
> **v2.0.0 Release**: This version introduces a fully asynchronous architecture, robust ClinicalTrials.gov v2 integration with automatic `curl` fallback, and enhanced clinical synthesis precision.

![MedKit CLI Demo](demo.gif)

---

## ✨ Async Example (v2.0.0)

```python
import asyncio
from medkit import AsyncMedKit

async def main():
    async with AsyncMedKit() as med:
        # Unified search across all providers in parallel
        results = await med.search("pembrolizumab")
        
        print(f"Drugs found: {len(results.drugs)}")
        print(f"Clinical Trials: {len(results.trials)}")
        
        # Get a synthesized conclusion
        conclusion = await med.ask("What is the clinical status of Pembrolizumab for NSCLC?")
        print(f"Summary: {conclusion.summary}")
        print(f"Confidence: {conclusion.confidence_score}")

asyncio.run(main())
```

---

## 🤔 Why MedKit?

| Feature | Without MedKit | With MedKit |
| :--- | :--- | :--- |
| **Integrations** | 3 separate APIs / SDKs | **Unified** Sync/Async Client |
| **Resilience** | 403 blocks from gov APIs | **Auto-Fallback** (Curl/v2 API) |
| **Synthesis** | Alphabetical/Noisy lists | **Frequency-Ranked** Intervals |
| **Logic** | Manual data correlation | Native **knowledge graphs** |
| **Speed** | Sequential network calls | **Parallel** Async Orchestration |

---

## 🏗️ Architecture

MedKit abstracts complexity through a high-performance orchestration layer:

```text
      Developer / User
             │
             ▼
    ┌───────────────────┐
    │  MedKit / Async   │ (Unified Interface)
    └─────────┬─────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Intelligence Layer      │
    │  ├─ Ask Engine (Extraction)   │
    │  ├─ Graph Engine (Context)    │
    │  ├─ Interaction Engine        │
    │  └─ Synthesis Engine (Ranked) │
    └─────────┬─────────────────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Providers Layer         │
    │  ├─ OpenFDA     (Drug Label)  │
    │  ├─ PubMed      (Research)    │
    │  └─ ClinTrials  (v2 + Fallback)│
    └───────────────────────────────┘
```

---

## 🚀 Core Platform Features

- **Robust Connectivity (NEW)**: Automatic `curl` fallback for ClinicalTrials.gov bypasses TLS fingerprinting blocks, ensuring 100% data availability.
- **Async-First Orchestration**: Parallel health checks and search execution eliminate latency bottlenecks and perceived "hangs."
- **Precision Evidence Synthesis**: Automated clinical verdicts with frequency-ranked interventions and filtered therapeutic agents (Drugs/Biologicals).
- **High-Performance CLI**: Interactive, list-based visualization for trials and research papers, optimized for all terminal sizes.
- **Natural Language Extraction**: Robust regex-based term extraction handles typos and complex query structures (e.g., "clinial status of...").
- **Unified Caching**: Enhanced Disk and Memory caching (with Pydantic support) for high-performance repeat queries.

---

## 📦 Installation

```bash
pip install medkit-sdk
```

---

## 🖥️ CLI Power Tools

### Clinical Ask (Synthesized)
```bash
$ medkit ask "pembrolizumab for lung cancer"

 Clinical Conclusion
Summary: Highly-validated therapeutic landscape with multi-modal evidence.
Confidence: ████████████████████ 1.00
Top Interventions: Pembrolizumab, Bevacizumab, Carboplatin, Cisplatin
```

### Trials Search
```bash
$ medkit trials "melanoma" --limit 5

Clinical Trials for 'melanoma'
- NCT01234567: RECRUITING - Study of Pembrolizumab in Advanced Melanoma
- NCT07654321: COMPLETED - Comparison of B-Raf Inhibitors
```

---

## 🗺️ Roadmap

- [x] **v1.0.0**: Foundation medical mesh and provider integration.
- [x] **v2.0.0**: Async architecture, v2 API support, and synthesis precision.
- [ ] **v2.1.0**: Advanced pharmacogenomics (SNP) provider integration.
- [ ] **v3.0.0**: Local GraphQL medical mesh endpoint.

---

## 📄 License
MIT License - see [LICENSE](LICENSE) for details.
