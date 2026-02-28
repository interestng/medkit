"""
Example of creating and registering a custom provider plugin.
"""

import sys
from pathlib import Path
from typing import Any

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import MedKit
from medkit.providers.base import BaseProvider

class MyHospitalProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="hospital")

    def search_sync(self, query: str, **kwargs) -> dict[str, Any]:
        return {
            "source": "Local Hospital Database",
            "patient_count": 120,
            "query": query
        }

def main():
    try:
        med = MedKit(debug=True)
        
        # Register the plugin
        med.register_provider(MyHospitalProvider())
        
        # Query the plugin (via some generic search or direct provider access)
        # For now, let's just see if it's in the list
        print(f"Registered providers: {list(med._providers.keys())}")
        
        # Direct query test
        res = med._providers["hospital"].search_sync("diabetes")
        print(f"Plugin result: {res}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
