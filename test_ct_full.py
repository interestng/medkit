import asyncio

from medkit.client import AsyncMedKit


async def test_full_flow():
    # Mimic the AsyncMedKit setup
    async with AsyncMedKit(debug=True) as sdk:
        query = "diabetes"
        print(f"--- Testing Full Async Search for: {query} ---")

        # Test individual provider search
        trials_prov = sdk._get_provider("clinicaltrials")
        print(f"Provider health check: {await trials_prov.health_check_async()}")

        results = await sdk.search(query)
        print("Final results count:")
        print(f"  Drugs: {len(results.drugs)}")
        print(f"  Papers: {len(results.papers)}")
        print(f"  Trials: {len(results.trials)}")

        if len(results.trials) == 0:
            print(
                "\nDIAGNOSIS: Trials came back empty. Checking if fallback was triggered."
            )
            # We can't easily check internal state, but debug=True should show errors.


if __name__ == "__main__":
    asyncio.run(test_full_flow())
