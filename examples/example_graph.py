"""
Example of the med.graph() relationship visualizer.
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
            print(f"Building medical relationship graph for '{query}'...")
            graph = med.graph(query)
            
            print(f"\nNodes found: {len(graph.nodes)}")
            print(f"Relationships found: {len(graph.edges)}")
            
            print("\nRelationships:")
            for edge in graph.edges[:10]:
                print(f"- {edge.source} --({edge.relationship})--> {edge.target}")
                
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
