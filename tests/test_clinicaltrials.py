from unittest.mock import AsyncMock, patch

import httpx
import pytest

from medkit.models import ClinicalTrial
from medkit.providers.clinicaltrials import ClinicalTrialsProvider


@pytest.fixture
def test_client():
    return httpx.AsyncClient()


@pytest.fixture
def test_provider(test_client):
    from medkit.config import ProviderConfig

    provider = ClinicalTrialsProvider(client=test_client)
    provider.config = ProviderConfig(timeout=10.0, max_retries=3)
    return provider


@pytest.mark.asyncio
async def test_clinicaltrials_health_check(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        assert await test_provider.health_check_async() is True

        # Test fallback
        with patch.object(test_provider, "_curl_fetch", return_value='{"studies": []}'):
            mock_get.return_value.status_code = 500
            assert await test_provider.health_check_async() is True


@pytest.mark.asyncio
async def test_clinicaltrials_search_returns_empty_list_on_404(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_req:
        # Simulate API Error
        mock_req.side_effect = Exception("Not found")

        # Must patch _curl_fetch too to ensure fallback payload represents an empty search
        with patch.object(test_provider, "_curl_fetch", return_value='{"studies": []}'):
            results = await test_provider.search("random_nonexistent_disease")
            assert results == []


@pytest.mark.asyncio
async def test_clinicaltrials_search_success(test_provider):
    with patch.object(test_provider.client, "get", new_callable=AsyncMock) as mock_req:
        import httpx

        mock_response = httpx.Response(
            200,
            json={
                "studies": [
                    {
                        "protocolSection": {
                            "identificationModule": {
                                "nctId": "NCT01234567",
                                "briefTitle": "Mock Trial",
                            },
                            "statusModule": {"overallStatus": "RECRUITING"},
                            "designModule": {"phases": ["PHASE2"]},
                            "descriptionModule": {"briefSummary": "Mock summary."},
                        }
                    }
                ]
            },
        )
        mock_response._request = httpx.Request("GET", "https://clinicaltrials.gov")
        mock_req.return_value = mock_response

        results = await test_provider.search("cancer")
        assert len(results) >= 1
        assert isinstance(results[0], ClinicalTrial)
        assert results[0].nct_id is not None
        assert results[0].status is not None


def test_parse_study_reads_design_sponsor_dates_and_locations(test_provider):
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT04567890", "briefTitle": "Example Trial"},
            "statusModule": {
                "overallStatus": "COMPLETED",
                "startDateStruct": {"date": "2021-03"},
                "primaryCompletionDateStruct": {"date": "2023-06-30"},
            },
            "designModule": {
                "studyType": "INTERVENTIONAL",
                "phases": ["PHASE3"],
                "enrollmentInfo": {"count": 412},
            },
            "sponsorCollaboratorsModule": {"leadSponsor": {"name": "Example Pharma"}},
            "contactsLocationsModule": {
                "locations": [
                    {"city": "Boston", "state": "Massachusetts", "country": "United States"},
                    {"city": "Boston", "state": "Massachusetts", "country": "United States"},
                    {"city": "Toronto", "country": "Canada"},
                ]
            },
        }
    }
    trial = test_provider._parse_study(study)
    assert trial.study_type == "INTERVENTIONAL"
    assert trial.enrollment == 412
    assert trial.sponsor == "Example Pharma"
    assert trial.start_date == "2021-03"
    assert trial.completion_date == "2023-06-30"
    assert trial.location == ["Boston, Massachusetts, United States", "Toronto, Canada"]


def test_parse_study_tolerates_missing_or_bad_enrollment(test_provider):
    study = {
        "protocolSection": {
            "identificationModule": {"nctId": "NCT04567890"},
            "designModule": {"enrollmentInfo": {"count": "not a number"}},
        }
    }
    trial = test_provider._parse_study(study)
    assert trial.enrollment is None
    assert trial.location == []
    assert trial.sponsor is None


def test_build_params_defaults(test_provider):
    params = test_provider._build_params("asthma")
    assert params == {"pageSize": 10, "query.term": "asthma"}


@pytest.mark.parametrize(
    "phase, expected",
    [
        (3, "AREA[Phase](PHASE3)"),
        ("phase 2", "AREA[Phase](PHASE2)"),
        (["PHASE2", "Phase3"], "AREA[Phase](PHASE2 OR PHASE3)"),
        ("early_phase1", "AREA[Phase](EARLY_PHASE1)"),
    ],
)
def test_build_params_phase_filter(test_provider, phase, expected):
    assert test_provider._build_params("asthma", phase=phase)["filter.advanced"] == expected


def test_build_params_status_and_recruiting(test_provider):
    params = test_provider._build_params(
        "asthma", status=["completed", "ACTIVE_NOT_RECRUITING"], recruiting=True, limit=5
    )
    assert params["pageSize"] == 5
    assert params["filter.overallStatus"] == "COMPLETED,ACTIVE_NOT_RECRUITING,RECRUITING"


def test_build_params_rejects_unknown_phase(test_provider):
    with pytest.raises(ValueError):
        test_provider._build_params("asthma", phase="phase 9")


def test_client_trials_passes_phase_and_status_through(mocker):
    from medkit.client import MedKit

    with MedKit() as med:
        provider = med._get_provider("clinicaltrials")
        spy = mocker.patch.object(provider, "search_sync", return_value=[])
        med.trials("asthma", limit=3, phase=3, status="completed")
        spy.assert_called_once_with(
            "asthma", limit=3, recruiting=False, phase=3, status="completed"
        )
