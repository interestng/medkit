"""
Example of using the MedKit SDK to get a comprehensive explanation of a condition (e.g. diabetes).
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
            print(f"Generating comprehensive report for '{query}'...")
            explanation = med.explain_drug(query)
            
            if explanation.drug_info:
                print("\n=== FDA Information ===")
                print(f"Brand Name: {explanation.drug_info.brand_name}")
                print(f"Generic Name: {explanation.drug_info.generic_name}")
            else:
                print("\n=== FDA Information ===")
                print(f"No FDA info found for '{query}'")
            
            if explanation.papers:
                print(f"\n=== Research Papers (Top {len(explanation.papers)}) ===")
                for i, p in enumerate(explanation.papers, 1):
                    print(f"{i}. {p.title} ({p.year})")
            else:
                print("\n=== Research Papers ===")
                print("No recent papers found")
                
            if explanation.trials:
                print(f"\n=== Clinical Trials ===")
                for t in explanation.trials:
                    print(f"- {t.title} [{t.status}]")
            else:
                print("\n=== Clinical Trials ===")
                print("No active recruiting trials found")
                
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
