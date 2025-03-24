from unittest.mock import AsyncMock

import pytest

from app import AppConst
from app.models.dto import SearchCategory
from app.models.dto_v3 import ExtractorResponse
from app.services.facade_service import ExtractorService, SearcherService, FacadeService
from tests import LOCAL_DEV_ENV

_MY_ENV = LOCAL_DEV_ENV
_MY_SESSION_ID = 'test_session_id'
_MY_URI = 'test_uri'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'run_searchers, expected_do_extract_called, expected_search_milvus_called',
    [
        (True, True, True),
        (False, True, False)
    ]
)
async def test_extract_and_search(
        run_searchers: bool, expected_do_extract_called: bool, expected_search_milvus_called: bool
):
    mock_do_extract = AsyncMock(return_value=ExtractorResponse(env=_MY_ENV, session_id=_MY_SESSION_ID, uri=_MY_URI))
    ExtractorService.do_extract = mock_do_extract

    mock_search_milvus = AsyncMock(return_value=SearchCategory())
    SearcherService.search_milvus = mock_search_milvus

    await FacadeService.extract_and_search(
        env=_MY_ENV,
        session_id=_MY_SESSION_ID,
        uri=_MY_URI,
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL,
        run_searchers=run_searchers
    )
    assert mock_do_extract.called == expected_do_extract_called
    assert mock_search_milvus.called == expected_search_milvus_called
