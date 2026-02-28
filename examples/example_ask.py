"""
Example of using the med.ask() natural language engine.
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from medkit import MedKit
from medkit.exceptions import MedKitError

def main():
    questions = [
        "What are new treatments for Alzheimer's?",
        "clinical trials for diabetes",
        "latest research on CRISPR",
        "tell me about ibuprofen"
    ]
    
    try:
        with MedKit(debug=True) as med:
            for q in questions:
                print(f"\n>>> Question: {q}")
                res = med.ask(q)
                print(f"Result type: {type(res).__name__}")
                
    except MedKitError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
