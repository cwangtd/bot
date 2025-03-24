import pytest
from fastapi import HTTPException

from app import AppConst
from app.api.image_v3 import exec_image
from app.services.facade_controller import Mode
from app.storage.storage_utils import CloudStorage
from tests import LOCAL_DEV_ENV

BUCKET = 'provenance-aigc-storage'
PATH = 'provenance.local.dev/tests/elsa.jpg'
REQUEST_ID = '000000'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'storage',
    [
        CloudStorage.GCS,
        CloudStorage.S3,
        'gcs',
        's3'
    ]
)
async def test_invalid_env(storage):
    with pytest.raises(HTTPException) as e:
        await exec_image(
            storage=storage,
            bucket=BUCKET,
            path=PATH,
            env='invalid_env',
            request_id=REQUEST_ID,
            mode=Mode.FULL,
            prompts=AppConst.DEFAULT_BOX_PROMPTS,
            min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
            rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
        )

    assert 'env' in str(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'storage',
    [
        '',
        'x',
    ]
)
async def test_invalid_storage(storage):
    with pytest.raises(HTTPException) as e:
        await exec_image(
            storage=storage,
            bucket=BUCKET,
            path=PATH,
            env=LOCAL_DEV_ENV,
            request_id=REQUEST_ID,
            mode='full',
            prompts=AppConst.DEFAULT_BOX_PROMPTS,
            min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
            rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
        )

    assert 'storage' in str(e.value)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'storage',
    [
        CloudStorage.GCS,
        CloudStorage.S3,
        'gcs',
        's3'
    ]
)
async def test_invalid_mode(storage):
    with pytest.raises(HTTPException) as e:
        await exec_image(
            storage=storage,
            bucket=BUCKET,
            path=PATH,
            env=LOCAL_DEV_ENV,
            request_id=REQUEST_ID,
            mode='invalid_mode',
            prompts=AppConst.DEFAULT_BOX_PROMPTS,
            min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
            rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
        )

    assert 'mode' in str(e.value)
