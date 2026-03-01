import json
import subprocess

url = "https://clinicaltrials.gov/api/v2/studies/NCT04455620"
cmd = ["curl", "-s", "-L", url]

result = subprocess.run(cmd, capture_output=True, check=True)
data = json.loads(result.stdout.decode("utf-8", errors="replace"))
protocol = data.get("protocolSection", {})
arms = protocol.get("armsInterventionsModule", {})
interventions = arms.get("interventions", [])
print(json.dumps(interventions, indent=2))
