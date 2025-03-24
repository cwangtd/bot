import pytest

from app.models.dto import FacadeMainExtractorMessage, CloudItemExtractorMessage
from app.services.facade_service import ExtractorService, SearcherService
from tests import LOCAL_DEV_ENV

ELSA_URI = 'gs://provenance-aigc-storage/provenance.local.dev/tests/elsa.jpg'
MARIO_URL = 'https://pngimg.com/d/mario_PNG125.png'
DEFAULT_PROMPTS = 'cartoon character'


@pytest.mark.skip(reason='tdd')
@pytest.mark.asyncio
async def test_search_with_milvus():
    extractor_message = FacadeMainExtractorMessage(
        env=LOCAL_DEV_ENV, session_id='000000-facade-unit-test', uri=ELSA_URI, prompts=DEFAULT_PROMPTS, min_box=0.25, rmbg=False
    )

    r1 = await ExtractorService.do_extract(extractor_message)
    assert r1 is not None

    r2 = await SearcherService.search_milvus(r1)
    assert r2 is not None


@pytest.mark.skip(reason='tdd')
@pytest.mark.asyncio
async def test_extract_features_from_url():
    results = await ExtractorService.do_extract(
        extractor_message=CloudItemExtractorMessage(
            env=LOCAL_DEV_ENV, session_id='000000-facade-unit-test',
            uri='https://lumiere-a.akamaihd.net/v1/images/ct_frozen_elsa_18466_22a50822.jpeg',
            serial=1
        )
    )

    assert results is not None
