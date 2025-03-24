from unittest.mock import patch

import pytest

from app import AppConst
from app.api.image_v3 import exec_image
from app.models.dto import SearchCategory
from app.models.dto_v3 import ExtractorResponse, ExtractionDto
from app.services.facade_controller import Mode, FacadeController
from app.storage.storage_utils import CloudStorage
from tests import LOCAL_DEV_ENV

BUCKET = 'provenance-aigc-storage'
PATH = 'provenance.local.dev/tests/elsa.jpg'
REQUEST_ID = '000000'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'mode, expected_exec_facade_called, expected_exec_full_called',
    [
        (Mode.FACADE, True, False),
        (Mode.FULL, False, True),
        (Mode.CLOUD, False, True),
    ]
)
@patch.object(FacadeController, 'exec_facade')
@patch.object(FacadeController, 'exec_full')
@patch.object(FacadeController, 'insert_doc')
@patch.object(FacadeController, 'update_doc')
async def test_get_image_router(
        _1, _2, mock_exec_full, mock_exec_facade,
        mode: Mode, expected_exec_facade_called: bool, expected_exec_full_called: bool
):
    mock_exec_facade.return_value = (
        ExtractorResponse(
            env=LOCAL_DEV_ENV,
            session_id=REQUEST_ID,
            uri='',
            extraction=[ExtractionDto(score=0.0, ratio=0.0, boxes=[], features=[])],
        ),
        SearchCategory(),
        {},
        {}
    )
    assert 'exec_facade' in str(mock_exec_facade)

    mock_exec_full.return_value = (
        ExtractorResponse(
            env=LOCAL_DEV_ENV,
            session_id=REQUEST_ID,
            uri='',
            extraction=[ExtractionDto(score=0.0, ratio=0.0, boxes=[], features=[])],
        ),
        SearchCategory(),
        {},
        {},
        []
    )
    assert 'exec_full' in str(mock_exec_full)

    await exec_image(
        storage=CloudStorage.GCS,
        bucket=BUCKET,
        path=PATH,
        env=LOCAL_DEV_ENV,
        request_id=REQUEST_ID,
        mode=mode,
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
    )

    assert mock_exec_facade.call_count == expected_exec_facade_called
    assert mock_exec_full.call_count == expected_exec_full_called



