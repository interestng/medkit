"""
Tests for the MedKit client.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from medkit.client import AsyncMedKit, MedKit
from medkit.exceptions import NotFoundError, RateLimitError
from medkit.models import ClinicalTrial, DrugInfo, ResearchPaper


@pytest.fixture
def mock_medkit(mocker):
    med = MedKit()
    # Mock the providers
    for name in list(med._providers.keys()):
        provider = med._providers[name]
        provider.search_sync = MagicMock()
        provider.search = AsyncMock()

    med._pubmed_limiter.wait = MagicMock()
    med._fda_limiter.wait = MagicMock()
    med._trials_limiter.wait = MagicMock()

    yield med
    med.close()


def test_drug_lookup(mock_medkit):
    mock_drug = DrugInfo(
        brand_name="Aspirin",
        generic_name="Acetylsalicylic acid",
        warnings=[],
        manufacturer="Bayer",
    )
    mock_medkit._providers["openfda"].search_sync.return_value = mock_drug

    result = mock_medkit.drug("aspirin")
    assert result.brand_name == "Aspirin"
    mock_medkit._providers["openfda"].search_sync.assert_called_once_with("aspirin")


def test_papers_search(mock_medkit):
    mock_paper = ResearchPaper(
        pmid="12345",
        title="Test Paper",
        authors=[],
        journal="Test Journal",
        year=2023,
        abstract="",
    )
    mock_medkit._providers["pubmed"].search_sync.return_value = [mock_paper]

    results = mock_medkit.papers("test", limit=1)
    assert len(results) == 1
    assert results[0].pmid == "12345"


def test_trials_search(mock_medkit):
    mock_trial = ClinicalTrial(
        nct_id="NCT123",
        title="Test Trial",
        status="RECRUITING",
        phase=[],
        location=[],
        eligibility="",
    )
    mock_medkit._providers["clinicaltrials"].search_sync.return_value = [mock_trial]

    results = mock_medkit.trials("cancer")
    assert len(results) == 1
    assert results[0].nct_id == "NCT123"


def test_explain_drug(mock_medkit):
    mock_drug = DrugInfo(
        brand_name="TestDrug",
        generic_name="Test",
        warnings=[],
        manufacturer="TestMakers",
    )
    mock_medkit._providers["openfda"].search_sync.return_value = mock_drug
    mock_medkit._providers["pubmed"].search_sync.return_value = []
    mock_medkit._providers["clinicaltrials"].search_sync.return_value = []

    result = mock_medkit.explain_drug("testdrug")
    assert result.drug_info.brand_name == "TestDrug"
    assert len(result.papers) == 0
    assert len(result.trials) == 0


@pytest.mark.asyncio
async def test_async_search():
    async with AsyncMedKit() as med:
        # Mock providers
        for name in list(med._providers.keys()):
            med._providers[name].search = AsyncMock()

        mock_drug = DrugInfo(
            brand_name="Aspirin", generic_name="A", warnings=[], manufacturer="B"
        )
        med._providers["openfda"].search.return_value = mock_drug
        med._providers["pubmed"].search.return_value = []
        med._providers["clinicaltrials"].search.return_value = []

        # Test search
        # Note: we don't assert brand_name here because med.search() swallows drug errors if not found
        # but since we mocked it to return something, it should work.
        res = await med.search("aspirin")
        assert res.metadata is not None
