"""
Example of using the MedKit SDK to fetch drug information.
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
            print("Fetching info for 'ibuprofen'...")
            info = med.drug("ibuprofen")
            
            print(f"Brand Name: {info.brand_name}")
            print(f"Generic Name: {info.generic_name}")
            print(f"Manufacturer: {info.manufacturer}")
            print(f"Warnings ({len(info.warnings)}):")
            for w in info.warnings[:3]:
                print(f" - {w}")
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
