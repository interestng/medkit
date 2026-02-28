"""
Example of using the asynchronous MedKit SDK.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import AsyncMedKit
from medkit.exceptions import MedKitError

async def main():
    query = "diabetes"
    try:
        async with AsyncMedKit() as med:
            print(f"Async search for '{query}'...")
            results = await med.search(query)
            
            print(f"\n--- Results for {query} ---")
            print(f"Drugs found: {len(results.drugs)}")
            print(f"Papers found: {len(results.papers)}")
            print(f"Trials found: {len(results.trials)}")
            
            if results.papers:
                print("\nTop Paper:")
                print(f"- {results.papers[0].title}")
                
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
