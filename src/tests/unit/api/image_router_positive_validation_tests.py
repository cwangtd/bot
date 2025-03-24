import pytest

from app.api.image_v3 import param_validator
from app.services.facade_controller import Stage, Mode
from app.storage.storage_utils import CloudStorage
from tests import LOCAL_DEV_ENV


@param_validator
async def mock_get_image(storage, env, mode, stage) -> dict:
    return {
        'storage': storage,
        'env': env,
        'mode': mode,
        'stage': stage
    }


@pytest.mark.asyncio
async def test_validation_and_transformation():
    transformed = await mock_get_image(
        storage='s3',
        env=LOCAL_DEV_ENV,
        mode='faCAde',
        stage='single'
    )
    assert transformed['storage'] == CloudStorage.S3
    assert transformed['mode'] == Mode.FACADE
    assert transformed['stage'] == Stage.SINGLE


@pytest.mark.asyncio
async def test_c_check_external_api_should_be_stage_two():
    transformed = await mock_get_image(
        storage='gcs',
        env='c-check.external.api.local',
        mode='full',
        stage='single'
    )
    assert transformed['storage'] == CloudStorage.GCS
    assert transformed['mode'] == Mode.FULL
    assert transformed['stage'] == Stage.TWO
