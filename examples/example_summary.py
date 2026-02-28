"""
Example of using the med.summary() feature in MedKit.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import MedKit
from medkit.exceptions import MedKitError


def main():
    query = "diabetes"
    try:
        with MedKit() as med:
            print(f"Generating medical summary for '{query}'...")
            summary = med.summary(query)

            print(f"\nCondition: {summary.condition.capitalize()}")

            if summary.drugs:
                print("\nDrugs:")
                for drug in summary.drugs:
                    print(f"- {drug}")

            if summary.papers:
                years = [p.year for p in summary.papers if p.year]
                year_range = f" ({max(years)}–{min(years)})" if years else ""
                print(f"\nLatest Research{year_range}:")
                for p in summary.papers:
                    print(f"- {p.title} ({p.year})")

            if summary.trials:
                print("\nClinical Trials:")
                for t in summary.trials:
                    print(f"- {t.nct_id}: {t.status} - {t.title}")
            else:
                print("\nClinical Trials:")
                print("No active recruiting trials found")

    except MedKitError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
