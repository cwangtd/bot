import pytest

from app.utils.verify_twitter import extract_twitter_username, verify_twitter


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url,expected_username',
    [
        ("https://x.com/johndoe", "johndoe"),
        ("https://x.com/johndoe/status/1234567890", "johndoe"),
        ("https://x.com/johndoe/status/1234567890/photo/1", "johndoe"),
        ("https://x.com/johndoe/", "johndoe"),
        ("https://x.com/intent/user?screen_name=", None),
        ("https://x.com/", None),
        ("https://twitter.com/johndoe", "johndoe"),
        ("https://twitter.com/johndoe/status/1234567890", "johndoe"),
        ("https://twitter.com/johndoe/status/1234567890/photo/1", "johndoe"),
        ("https://twitter.com/johndoe/", "johndoe"),
        ("https://twitter.com/intent/user?screen_name=", None),
        ("https://twitter.com/", None)
    ]
)
def test_extract_twitter_username(url, expected_username):
    assert extract_twitter_username(url) == expected_username


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url,expected_result',
    [
        ("https://x.com/123rf", True),
        ("https://x.com/pixlr", True),
        ("https://x.com/vectrlabs", True),
        ("https://x.com/alamy", True),
        ("https://x.com/Alamy_Editorial", True),
        ("https://x.com/nonexistentuser", False),
        ("https://twitter.com/123rf", True),
        ("https://twitter.com/pixlr", True),
        ("https://twitter.com/vectrlabs", True),
        ("https://twitter.com/alamy", True),
        ("https://twitter.com/Alamy_Editorial", True),
        ("https://twitter.com/nonexistentuser", False),
    ]
)
def test_verify_twitter(url, expected_result):
    assert verify_twitter(url) == expected_result
