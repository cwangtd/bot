import json

import pytest

from app import AppConst
from app.api.image_v3 import exec_image
from app.services.facade_controller import Mode
from app.storage.storage_utils import CloudStorage


async def get_gcs(
        bucket, path, env,
        mode=Mode.FULL,
        request_id='000000',
        prompts=AppConst.DEFAULT_BOX_PROMPTS,
        min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
        rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
):
    return await exec_image(
        bucket=bucket,
        path=path,
        env=env,
        request_id=request_id,
        mode=mode,
        prompts=prompts,
        min_box=min_box,
        rmbg=rmbg
    )


@pytest.mark.asyncio
async def test_get_image():
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenance.local.dev/tests/elsa.jpg',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenance.local.dev/tests/lion.png',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    # for i in range(1):
    #     results = await get_gcs(
    #         bucket='provenance-aigc-storage',
    #         path='provenance.local.dev/tests/instagram-spider-man.jpg',
    #         env='provenance.local.dev',
    #         mode=Mode.CLOUD
    #     )
    # for i in range(1):
    #     results = await get_gcs(
    #         bucket='provenance-aigc-storage',
    #         path='provenance.local.dev/tests/cherry-blossom.webp',
    #         env='provenance.local.dev',
    #         mode=Mode.CLOUD
    #     )
    for i in range(1):
        # results = await get_gcs(
        #     bucket='provenance-aigc-storage',
        #     path='provenance.local.dev/tests/wire-tree-06175_1025_2WC869J.jpg',
        #     env='provenance.local.dev',
        #     mode=Mode.CLOUD
        # )
        results = await exec_image(
            storage=CloudStorage.S3,
            bucket='alamy-data',
            path='0001/2A000A2.jpg',
            env='provenance.local.dev',
            mode=Mode.FULL,
            request_id='000000',
            prompts=AppConst.DEFAULT_BOX_PROMPTS,
            min_box=AppConst.DEFAULT_MIN_BOX_DETECT_RATIO,
            rmbg=AppConst.DEFAULT_BACKGROUND_REMOVAL
        )
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/HELIOS/665fe9609f3c561fd7e88dad/00.jpeg',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/text-to-image/67906946e43c844139059232/9d5bbfbf-b9f7-4aca-97ca-4d38d65b18b1.webp',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    #
    # desc: nothing in lens but box_lens
    # results = get_image(
    #     bucket='provenance-aigc-storage',
    #     path='provenance.local.dev/tests/metal_guy.png',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    #
    # desc: contains TikTok
    # results = get_image(
    #     bucket='provenance-aigc-storage',
    #     path='provenance.cool/HELIOS/66624cb10ef0207874bce154/00.png',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    #
    # desc: 'https://www.nintendo.com/us/store/products/lion-simulator-survival-rpg-animal-battle-switch/'
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/HELIOS/66679666932a6b6b9db5c057/00.png',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    #
    # desc: runner, many repeat frames
    # results = get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/HELIOS/666b68914bcbc56c89305fcd/00.png',
    #     env='provenance.local.dev',
    #     req_id='000000'
    # )
    #
    # results = get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/text-to-image/669d3956200d4825a42128cb/3f5da706-9e3f-4ca2-b8d6-206930c62a5c.webp',
    #     env='provenance.local.dev',
    #     req_id='000000-facade',
    #
    # )
    #
    # desc: snow field
    # results = await get_image(
    #     storage=CloudStorage.GCS,
    #     bucket='provenance-aigc-storage',
    #     path='provenancenow.xyz/text-to-image/6792aa63e43c8441390592e4/495aee5d-6b2b-4896-85a0-e8d549bea05b.webp',
    #     env='provenance.local.dev',
    #     req_id='000000-facade',
    # )

    # S3

    # results = get_image(
    #     storage=CloudStorage.S3,
    #     bucket='provenance-c-check-crawled-assets',
    #     path='midjourney_recreate/original/artists_cleaned/108_graffiti/108_graffiti_1717165301-870888.jpg',
    #     env='provenance.local.dev',
    #     req_id='000000-facade'
    # )

    results_json = json.dumps(results, default=lambda o: o.__dict__, ensure_ascii=False)
    assert results_json is not None
    assert results is not None
