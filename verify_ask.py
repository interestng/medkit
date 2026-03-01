from medkit.client import MedKit

with MedKit() as client:
    query = "What is the clinial status for malignant tumors"
    conclusion = client.ask(query)
    print(f"Query: {conclusion.query}")
    print(f"Confidence: {conclusion.confidence_score}")
    print(f"Interventions: {conclusion.top_interventions}")
