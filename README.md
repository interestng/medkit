# 🏥 MedKit: A Unified Platform for Medical Data APIs

[![CI Status](https://img.shields.io/badge/CI-passing-success)](https://github.com/interestng/medkit/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Version](https://img.shields.io/badge/Version-1.4.0-orange)](https://pypi.org/project/medkit-sdk/)

MedKit is a high-performance, unified SDK that transforms fragmented medical APIs into a single, programmable platform. It provides a clean interface for **OpenFDA**, **PubMed**, and **ClinicalTrials.gov**, augmented with a clinical intelligence layer and relationship mapping.

> [!NOTE]
> A lot of functionality may still be at a POC Layer, but the core engines are functional and being refined daily. Please contact us through an issue if you see anything you want implemented soon.

![MedKit CLI Demo](demo.gif)

---

## ✨ Quick Example

```python
from medkit import MedKit

with MedKit() as med:
    # Get a synthesized clinical conclusion
    conclusion = med.conclude("pembrolizumab")
    
    # Output: Highly-validated therapeutic landscape (Score: 1.00)
    print(f"Summary: {conclusion.summary}")
    print(f"Evidence Score: {conclusion.evidence_score}")
```

---

## 🤔 Why MedKit?

| Feature | Without MedKit | With MedKit |
| :--- | :--- | :--- |
| **Integrations** | 3 separate APIs / SDKs | **One** unified client |
| **Clinical Verdicts**| Manual paper review | **med.conclude()** synthesis |
| **Logic** | Manual data correlation | Native **knowledge graphs** |
| **Speed** | Ad-hoc caching | Built-in **Disk/Memory Cache** |

---

## 🏗️ Architecture

MedKit abstracts complexity through a multi-layered provider system:

```text
      Developer / User
             │
             ▼
    ┌───────────────────┐
    │   MedKit Client   │ (Sync / Async)
    └─────────┬─────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Intelligence Layer      │
    │  ├─ Ask Engine (Routing)      │
    │  ├─ Graph Engine (Context)    │
    │  ├─ Interaction Engine        │
    │  └─ Synthesis Engine (NEW)    │
    └─────────┬─────────────────────┘
              │
    ┌─────────┴─────────────────────┐
    │       Providers Layer         │
    │  ├─ OpenFDA     (Drug Label)  │
    │  ├─ PubMed      (Research)    │
    │  └─ ClinTrials  (Studies)     │
    └───────────────────────────────┘
```

---

## 🚀 Core Platform Features (v1.4.0)

- **Evidence Synthesis (`med.conclude()`)**: Automated clinical verdicts with evidence strength scoring (0.0–1.0) based on trial phases, approval status, and research volume. High-accuracy regex matching for Phase I-III trials.
- **Precision Interaction Engine**: High-fidelity detection of drug-drug contraindications. Enhanced to catch cross-label mentions across brand and generic identifiers.
- **Medical Relationship Graph (`med.graph()`)**: Visualize connections with title-based node labeling. Now correlates drugs directly to the clinical trials they intervene in.
- **Natural Language Engine (`med.ask()`)**: Query medical data in plain English with automated capability-based routing.
- **Research Data Export**: Native CSV and JSON export for medical researchers via CLI or SDK.
- **Provider Health Dashboard**: Real-time status and latency tracking for all data providers.
- **Unified Caching**: Robust Disk and Memory caching for high-performance repeat queries.

---

## 📦 Installation

```bash
pip install medkit-sdk
```

---

## 📖 Quick Start

### 1. Synthesize Evidence
```python
with MedKit() as med:
    c = med.conclude("melanoma")
    print(c.key_findings) # -> ["FDA data found", "Phase III trial validated", ...]
```

### 2. Check Drug Interactions
```python
with MedKit() as med:
    risks = med.interactions(["aspirin", "warfarin"])
    for risk in risks:
        print(f"Risk: {risk['warning'].risk} (Severity: {risk['warning'].severity})")
```

### 3. Relationship Knowledge Graph
Map how drugs relate to trials and papers.
```python
graph = med.graph("metformin")
# Visualizes: Metformin -> Intervenes In -> [Trial A, Trial B] -> Mentions -> [Drug X]
```

---

## 🖥️ CLI Power Tools

### Clinical Conclusion
```bash
$ medkit conclude "pembrolizumab"

 Clinical Conclusion
Summary: Highly-validated therapeutic landscape with multi-modal evidence.
Evidence Strength: ████████████████████ 1.00
Key Findings: 
• FDA data available for: KEYTRUDA QLEX.
• Validated by 2 Phase III clinical trials.
```

### Knowledge Graph
```bash
$ medkit graph "lung cancer"
```

### Research Export
```bash
$ medkit export "immunotherapy" --format csv --path my_research.csv
```

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first.

### Development Setup
1. Clone the repository.
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Run quality checks:
```bash
ruff check .
mypy .
pytest
```

---

## 🗺️ Roadmap

- **v0.3.0**: AI-powered conversational agent integration (LLM plug-ins).
- **v0.4.0**: Advanced pharmacogenomics provider integration.
- **v1.0.0**: Local GraphQL API to serve the unified medical mesh.

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
