import json

import httpx

from medkit.providers.clinicaltrials import ClinicalTrialsProvider


def diagnose():
    client = httpx.Client()
    provider = ClinicalTrialsProvider(client)

    query = "diabetes"
    print(f"Testing search for: {query}")

    # Test httpx directly
    try:
        resp = client.get(
            provider.base_url,
            params={"pageSize": 5, "query.term": query},
            headers=provider.headers,
            timeout=5.0,
        )
        print(f"HTTPX Status: {resp.status_code}")
        if resp.status_code == 200:
            studies = resp.json().get("studies", [])
            print(f"HTTPX found {len(studies)} studies")
        else:
            print(f"HTTPX response: {resp.text[:200]}")
    except Exception as e:
        print(f"HTTPX Exception: {e}")

    # Test curl directly
    params = {"pageSize": 5, "query.term": query}
    res = provider._curl_fetch(provider.base_url, params)

    if not res:
        print("FAIL: Curl returned nothing")
        return

    print(f"Curl response length: {len(res)}")
    try:
        data = json.loads(res)
        studies = data.get("studies", [])
        print(f"Found {len(studies)} studies via curl fallback")
        if studies:
            print(
                f"First study title: {studies[0].get('protocolSection', {}).get('identificationModule', {}).get('briefTitle')}"
            )
    except Exception as e:
        print(f"FAIL: JSON parse error: {e}")
        print(f"Raw output start: {res[:200]}")


if __name__ == "__main__":
    diagnose()
