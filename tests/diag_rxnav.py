import httpx
import json

def test_rxnav():
    print("Testing RxNav Connectivity...")
    
    # 1. Test get_rxcui
    name = "warfarin"
    url1 = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={name}"
    print(f"Requesting: {url1}")
    r1 = httpx.get(url1)
    print(f"Status: {r1.status_code}")
    if r1.status_code == 200:
        cui = r1.json().get("idGroup", {}).get("rxnormId", [None])[0]
        print(f"Resolved {name} to {cui}")
    else:
        print(f"Error: {r1.text}")

    # 2. Test interaction
    # Warfarin (11289) and Aspirin (1191)
    url2 = "https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis=11289+1191"
    print(f"Requesting: {url2}")
    r2 = httpx.get(url2)
    print(f"Status: {r2.status_code}")
    if r2.status_code == 200:
        print("Success! Data received.")
        # print(json.dumps(r2.json(), indent=2)[:500])
    else:
        print(f"Error: {r2.text}")

if __name__ == "__main__":
    test_rxnav()
