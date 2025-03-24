import pytest

from app import AppConst
from app.services.facade_service import FacadeService
from app.storage.storage_utils import CloudStorage


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'storage, bucket, path',
    [
        # (CloudStorage.S3, 'element-static', 'c-scraper-test/son_goku.png'),
        # (CloudStorage.S3, 'element-static', 'c-scraper-test/lion.png'),
        # (CloudStorage.GCS, 'provenance-aigc-storage', 'provenance.local.dev/tests/coke-cola.jpg'),
        # iPhone
        (CloudStorage.GCS, 'provenance-aigc-storage', 'provenancedata.tech/text-to-image/67d0d7e22eaf8d2242dcb7d0/0f519275-5dd7-4985-9f0c-065aab64f5f0.webp'),
    ]
)
async def test_exec_lens(storage, bucket, path):
    custom_search_dto, _ = await FacadeService.cloud_execution_vision(
        storage, bucket, path, list(set(AppConst.DOMAINS + AppConst.SUB_DOMAINS))
    )
    count = (sum(len(match['items']) for match in custom_search_dto['matches']) + len(custom_search_dto['omissions']))
    assert count > 0
