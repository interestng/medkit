"""
Example of using the MedKit SDK to fetch research papers.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import MedKit
from medkit.exceptions import MedKitError


def main():
    try:
        with MedKit() as med:
            print("Searching for recent papers on 'CRISPR'...")
            papers = med.papers("CRISPR", limit=5)

            for paper in papers:
                print(f"\nTitle: {paper.title}")
                print(f"Journal: {paper.journal} ({paper.year})")
                print(f"Authors: {', '.join(paper.authors[:3])}")
                print(f"PMID: {paper.pmid}")
    except MedKitError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
