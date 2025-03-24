from urllib.parse import quote

import pytest

from app.main import AppConst
from app.services.cloud_lens_helper import LTHelper, SINGLE_KIND, GROUP_KIND, LENS_API
from app.storage.storage_utils import CloudStorage


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_all_tests(request):
    yield
    # #ReviveSelenium
    # from tests.utils.lens_service_selenium_helper import stop_selenium
    # stop_selenium()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url',
    [
        'https://element-static.s3.us-east-1.amazonaws.com/c-scraper-test/son_goku.png',
        'https://element-static.s3.us-east-1.amazonaws.com/c-scraper-test/elsa.jpg',
        'https://element-static.s3.us-east-1.amazonaws.com/c-scraper-test/lion.png',
    ]
)
async def test_exec_lens(url):
    helper = LTHelper()
    lens_dto, _ = await helper.exec_lens(
        img_url=url,
        domains=list(set(AppConst.DOMAINS + AppConst.SUB_DOMAINS))
    )
    lens_returned_total = sum(len(match['items']) for match in lens_dto['matches']) + len(lens_dto['omissions'])
    assert lens_returned_total > 0


def test_org_lens_items():
    disney_items = [
        {
            'title': 'Elsa1',
            'pageUrl': 'https://disney.fandom.com/wiki/Elsa',
            'imageUrl': 'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
            'source': 'disney'
        },
        {
            'title': 'Elsa2',
            'pageUrl': 'https://disney.fandom.com/wiki/Elsa',
            'imageUrl': 'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
            'source': 'disney'
        }
    ]
    frozen_items = [
        {
            'title': 'Elsa',
            'pageUrl': 'https://frozen.fandom.com/wiki/Elsa',
            'imageUrl': 'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
            'source': 'frozen'
        }
    ]
    x_items = [
        {
            'title': 'x1',
            'pageUrl': 'https://frozen.fandom.com/wiki/Elsa',
            'imageUrl': 'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
            'source': 'x'
        },
        {
            'title': 'x2',
            'pageUrl': 'https://frozen.fandom.com/wiki/Elsa',
            'imageUrl': 'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
            'source': 'x'
        }
    ]

    lens_dto, _ = LTHelper.org_lens_items(
        domains=['disney', 'frozen', 'fandom'],
        items={
            SINGLE_KIND: disney_items + frozen_items + x_items,
            GROUP_KIND: []
        })

    disney_frozen_kind_count = 2
    match_count = len(lens_dto['matches'])
    assert disney_frozen_kind_count == match_count

    disney_frozen_item_count = len(disney_items + frozen_items)
    match_item_count = sum(len(match['items']) for match in lens_dto['matches'])
    assert disney_frozen_item_count == match_item_count

    total_item_count = len(disney_items + frozen_items + x_items)
    assert total_item_count > match_item_count


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'url,domains',
    [
        ('https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg', ['disney', 'fandom', 'frozen']),
        ('https://element-static.s3.amazonaws.com/c-scraper-test/lion.png', []),
        ('https://element-static.s3.amazonaws.com/c-scraper-test/metal_guy.png', []),
        ('https://element-static.s3.amazonaws.com/c-scraper-test/cat.png', []),
    ]
)
async def test_search_lens(url, domains):
    domains = domains or []
    helper = LTHelper()
    lens_dto, topics = await helper.exec_lens(url, domains.copy())

    num_matches = sum(len(items['items']) for items in lens_dto['matches'])
    num_omissions = len(lens_dto['omissions'])
    assert num_matches + num_omissions > 0, 'No matches or omissions found'

    num_related_topics = len(topics)
    assert num_related_topics > 0, 'Missing related topics'


@pytest.mark.asyncio
@pytest.mark.parametrize(
    'img_url',
    [
        'https://element-static.s3.amazonaws.com/c-scraper-test/elsa.jpg',
        'https://element-static.s3.amazonaws.com/c-scraper-test/lion.png',
    ]
)
async def test_lens_crawlers(img_url):
    url = f'{LENS_API}?url={quote(img_url)}'
    helper = LTHelper()
    r_results = await helper.lens_requests_crawler(url)

    assert r_results is not None, 'Requests crawler failed'

    # #ReviveSelenium
    # from tests.utils.lens_service_selenium_helper import lens_selenium_crawler
    # s_results = await lens_selenium_crawler(url)
    # assert s_results is not None, 'Selenium crawler failed'
    # assert len(s_results[SINGLE_KIND]) <= len(r_results[SINGLE_KIND])


@pytest.mark.asyncio
async def test_lens_no_result():
    bucket = 'provenance-aigc-storage'
    path = 'provenancedata.tech/HELIOS/667f44ee6a78646b8ec675c4/00.png'
    img_url = CloudStorage.GCS.sign_url(bucket, path)
    url = f'{LENS_API}?url={quote(img_url)}'
    helper = LTHelper()
    lens_dto, topics = await helper.exec_lens(url, [])

    assert len(lens_dto['matches']) == 0, 'Should be empty items'
    assert len(lens_dto['omissions']) == 0, 'Should be empty omissions'
    assert len(topics) == 0, 'Should be empty topic'


@pytest.mark.asyncio
async def test_lens_requests_crawler_no_result_wont_crash():
    url = 'https://www.yahoo.com'
    helper = LTHelper()
    result = await helper.lens_requests_crawler(url)
    assert len(result[SINGLE_KIND]) == 0, 'No results found'
