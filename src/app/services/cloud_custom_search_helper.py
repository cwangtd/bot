import time
from urllib.parse import urlunparse, urlencode

from app.common.http_async_builder import HttpAsyncBuilder
from app.common.logger_common import log_exception, logger

""" item JSON
{
  "kind": "customsearch#result",
  "title": "Goku - Wikipedia",
  "htmlTitle": "<b>Goku</b> - Wikipedia",
  "link": "https://upload.wikimedia.org/wikipedia/en/4/4c/GokumangaToriyama.png",
  "displayLink": "en.wikipedia.org",
  "snippet": "Goku - Wikipedia",
  "htmlSnippet": "<b>Goku</b> - Wikipedia",
  "mime": "image/png",
  "fileFormat": "image/png",
  "image": {
    "contextLink": "https://en.wikipedia.org/wiki/Goku",
    "height": 388,
    "width": 257,
    "byteSize": 124042,
    "thumbnailLink": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTsTOHHlXF3xuKWWywffZsolosc6p6iwFj5oR6Ug_6nQfZVaHS0I1PpaA&s",
    "thumbnailHeight": 123,
    "thumbnailWidth": 81
  }
}
"""

API_KEYS = [
    # Provenance-Product
    'AIzaSyCr56C-ReSQCXAU1lOP3bfV7D_d3Ye-9ME',
    # Provenance-External
    'AIzaSyAi-njeRhbcrIgDZDiHhtq160M5s-i48gQ',
]
SEARCH_ENGINE_ID = '270a05d3ad6b74449'


# Firefox
async def exec_custom_search(keywords, domains) -> dict:
    _ret = {'matches': [], 'omissions': []}

    if len(keywords) == 0 or len(domains) == 0:
        return _ret

    url = build_url(domains, keywords)
    response = await HttpAsyncBuilder(url, tag='CustomSearch').execute()
    if not response.is_success:
        return _ret

    result = response.json()
    source_items = {}
    for item in result.get('items', []):
        item = convert_custom_searched_to_cloud_item(item)
        if item:
            source_items.setdefault(item['source'], []).append(item)

    _ret['matches'] = [{'key': source, 'items': items} for source, items in source_items.items()]
    return _ret


def build_url(domains, keywords) -> str:
    key_index = int(time.time()) % len(API_KEYS)
    api_key = API_KEYS[key_index]
    logger.debug(f'Using API key {key_index}: {api_key}')

    domains_param = ' OR '.join(f'site:*.{d}.*' for d in domains)
    keywords_param = ' OR '.join('"' + k + '"' for k in keywords)

    # param list: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
    # search operations: https://ahrefs.com/blog/google-advanced-search-operators/
    params = {
        'key': api_key,
        'cx': SEARCH_ENGINE_ID,
        'searchType': 'image',
        'q': f'{keywords_param}+{domains_param}'
    }

    return urlunparse((
        'https',
        'www.googleapis.com',
        'customsearch/v1',
        '',
        urlencode(params),
        ''
    ))


def convert_custom_searched_to_cloud_item(item) -> dict | None:
    title = item.get('title', None)
    source = item.get('displayLink', None)
    image_url = item.get('link', None)
    page_url = item.get('image', []).get('contextLink', None)

    if title and source and image_url:
        return {
            'title': title,
            'source': source,
            'pageUrl': page_url,
            'imageUrl': image_url
        }
    else:
        log_exception(tag=f'CustomSearch | {item}', level_func=logger.warning)
        return None
