import pytest

from app.utils.verify_instagram import verify_instagram


@pytest.mark.skip(reason='This test might be blacklisted time to time. Skip for now.')
@pytest.mark.parametrize(
    'url,verification_result',
    [
        ('https://www.instagram.com/disney/', {'https://www.instagram.com/disney/': True}),
        ('https://www.instagram.com/test/', {'https://www.instagram.com/test/': False}),
        ('https://www.instagram.com/marvel/p/code/', {'https://www.instagram.com/marvel/p/code/': True}),
        ('https://www.instagram.com/marvel/reel/magic/', {'https://www.instagram.com/marvel/reel/magic/': True}),
        # TODO, if the URL contains a `p`, cannot be handled by the current implementation
        # ('https://www.instagram.com/p/C7SWkGfOioz/', {'https://www.instagram.com/p/C7SWkGfOioz/': True}),
        ('https://www.instagram.com/p/C7eJ2CbPjXL/', {'https://www.instagram.com/p/C7eJ2CbPjXL/': False}),
    ]
)
def test_verify_instagram(url, verification_result):
    assert verify_instagram(url) == verification_result
