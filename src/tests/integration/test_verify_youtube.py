import pytest

from app.utils.verify_youtube import batch_verify_youtube


@pytest.mark.parametrize(
    'video_ids,verification_result',
    [
        (['b1ByiH7IMSI', 'dPsZJGN32QY'],
         {'b1ByiH7IMSI': True, 'dPsZJGN32QY': False})
    ]
)
@pytest.mark.asyncio
async def test_batch_verify_youtube(video_ids, verification_result):
    assert await batch_verify_youtube(video_ids) == verification_result
