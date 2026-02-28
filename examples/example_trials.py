"""
Example of using the MedKit SDK to fetch active clinical trials.
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
            print("Searching for recruiting clinical trials for 'breast cancer'...")
            # We specifically request recruiting trials
            trials = med.trials("breast cancer", recruiting=True, limit=5)

            for trial in trials:
                print(f"\nTrial: {trial.title}")
                print(f"ID: {trial.nct_id}")
                print(f"Status: {trial.status}")
                if trial.phase:
                    print(f"Phase: {', '.join(trial.phase)}")
    except MedKitError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
