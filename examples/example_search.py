"""
Example of using the unified search() method in MedKit.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import MedKit
from medkit.exceptions import MedKitError

def main():
    query = "insulin"
    try:
        with MedKit() as med:
            print(f"Searching for '{query}' across all sources...")
            results = med.search(query)
            
            if results.drugs:
                print("\n=== Found Drugs ===")
                for d in results.drugs:
                    print(f"Drug: {d.brand_name} ({d.generic_name})")
            
            if results.papers:
                print(f"\n=== Research Papers (Top {len(results.papers)}) ===")
                for i, p in enumerate(results.papers, 1):
                    print(f"{i}. {p.title} ({p.year})")
            
            if results.trials:
                print(f"\n=== Clinical Trials ({len(results.trials)}) ===")
                for t in results.trials:
                    print(f"- {t.nct_id}: {t.status} - {t.title}")
                
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
