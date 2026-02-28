from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, List


class Exporter:
    """
    Handles exporting MedKit results to different formats.
    """

    @staticmethod
    def to_json(data: Any, path: str | Path):
        content = ""
        if hasattr(data, "model_dump_json"):
            content = data.model_dump_json(indent=2)
        else:
            content = json.dumps(data, indent=2, default=str)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    @staticmethod
    def to_csv(data: Any, path: str | Path):
        """
        Flatten and export to CSV.
        """
        records = []
        if hasattr(data, "drugs"):  # SearchResults
            for d in data.drugs:
                records.append(
                    {"type": "drug", "name": d.brand_name, "detail": d.generic_name}
                )
            for p in data.papers:
                records.append({"type": "paper", "name": p.title, "detail": p.pmid})
            for t in data.trials:
                records.append({"type": "trial", "name": t.nct_id, "detail": t.status})
        elif isinstance(data, list):
            for item in data:
                if hasattr(item, "model_dump"):
                    records.append(item.model_dump())
                else:
                    records.append({"data": str(item)})

        if not records:
            return

        keys = records[0].keys()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)
