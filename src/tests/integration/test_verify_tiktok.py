import pytest

from app.utils.verify_tiktok import verify_tiktok, verify_tiktok_batch


@pytest.mark.parametrize(
    'url,verification_result',
    [
        ('https://www.tiktok.com/@disney/video/6948180391740148998', {'@disney': True}),
        ('https://www.tiktok.com/@prophettlkelvin/video/7106774981551459589', {'@prophettlkelvin': False}),
        ('https://www.tiktok.com/discover/aesthetic-movies-on-disney-plus', {'discover': False}),
        ('https://www.tiktok.com/tag/superherofetish', {'tag': False}),
    ]
)
def test_verify_tiktok(url, verification_result):
    assert verify_tiktok(url) == verification_result


@pytest.mark.parametrize(
    'urls,verification_results',
    [
        ([
             'https://www.tiktok.com/@disney/video/6948180391740148998',
             'https://www.tiktok.com/@prophettlkelvin/video/7106774981551459589',
             'https://www.tiktok.com/discover/aesthetic-movies-on-disney-plus',
             'https://www.tiktok.com/tag/superherofetish',
         ], {
             '@disney': True,
             '@prophettlkelvin': False,
             'discover': False,
             'tag': False,
         })
    ]
)
def test_verify_tiktok_batch(urls, verification_results):
    assert verify_tiktok_batch(urls) == verification_results
