import asyncio

import pytest

from app import AppConst
from app.api.image_v3 import exec_image, exec_session
from app.models.shooter_dto import ShooterStatus, ShooterDto
from app.services.facade_controller import Mode
from app.storage.storage_utils import CloudStorage
from tests import LOCAL_DEV_ENV


@pytest.mark.asyncio
async def test_get_images():
    await run_spider_man()
    await run_general()
    await run_stage_two()


async def run_spider_man():
    found_lens_results = False

    shooter_dto: ShooterDto = await exec_image(
        storage=CloudStorage.GCS,
        mode=Mode.FULL,
        request_id='001001',
        bucket='provenance-aigc-storage',
        path='provenance.local.dev/tests/instagram-spider-man.jpg',
        env=LOCAL_DEV_ENV,
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
    )
    assert len(shooter_dto.ranks) > 10
    for item in shooter_dto.ranks:
        if any(keyword in item['title'] for keyword in
               ('instagram', 'imdb', 'youtube', 'marvel', 'wikipedia', 'disney')):
            found_lens_results = True

    assert shooter_dto.request_id == '001001'
    assert shooter_dto.response_id is not None
    await asyncio.sleep(1)
    await assert_by_shooter(LOCAL_DEV_ENV, shooter_dto)

    assert found_lens_results


async def run_general():
    shooter_dto: ShooterDto = await exec_image(
        storage=CloudStorage.S3,
        mode=Mode.FACADE,
        request_id='001002',
        bucket='provenance-c-check-storage-us-east-1',
        path='bm_movie_images/000000_0.webp',
        env=LOCAL_DEV_ENV,
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
    )
    assert shooter_dto.request_id == '001002'
    assert shooter_dto.response_id is not None
    assert len(shooter_dto.ranks) > 10


async def run_stage_two():
    env = 'c-check.external.api.local'
    shooter_dto = await exec_image(
        storage=CloudStorage.GCS,
        mode=Mode.FULL,
        request_id='001003',
        bucket='provenance-aigc-storage',
        path='provenance.local.dev/tests/instagram-spider-man.jpg',
        env=env,
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
    )
    assert shooter_dto.request_id == '001003'
    assert shooter_dto.response_id is not None
    assert len(shooter_dto.ranks) == 0

    pending_count = 0
    stage1_count = 0
    complete_count = 0
    for _ in range(30):
        dto = await assert_by_shooter_and_get_status(env, shooter_dto)
        status = dto.status
        await asyncio.sleep(1)

        if status == ShooterStatus.PENDING:
            pending_count += 1
            assert 'ranks' not in dto
        elif status == ShooterStatus.STAGE1:
            stage1_count += 1
            assert len(dto.ranks) > 0
        elif status == ShooterStatus.COMPLETE:
            complete_count += 1
            shooter_dto = dto
            break
        else:
            pending_count = stage1_count = complete_count = 0
            break

    assert pending_count > 0
    assert stage1_count > 0
    assert complete_count > 0

    db_shooter_dto = await assert_by_shooter(env, shooter_dto)

    found_display_name = False
    for item in db_shooter_dto.ranks:
        if item['title'].endswith('| Independent Artist'):
            found_display_name = True
            break
    assert found_display_name


async def assert_by_shooter(env: str, shooter_dto: ShooterDto) -> ShooterDto:
    db_shooter_dto = await exec_session(env, shooter_dto.response_id)
    assert shooter_dto.request_id == db_shooter_dto.request_id
    assert len(shooter_dto.ranks) == len(db_shooter_dto.ranks)
    return db_shooter_dto


async def assert_by_shooter_and_get_status(env: str, shooter_dto: ShooterDto) -> ShooterDto:
    response_id = shooter_dto.response_id
    db_shooter_dto = await exec_session(env, response_id)
    assert db_shooter_dto.request_id == shooter_dto.request_id
    return db_shooter_dto
