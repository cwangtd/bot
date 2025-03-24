import logging
from urllib.parse import urlparse

logger = logging.getLogger('main.app')

TIKTOK_WHITELIST = [
    '@123rf_official',
    '@pixlrofficial',
    '@envato',
    '@shutterstock',
    '@giphy',
    '@splashnewsofficial',
    '@backgrid',
    '@disney',
    '@disneyplus',
    '@disneyparks',
    '@disneychannel',
    '@disneyanimation',
    '@disneystudios',
    '@disneymusic',
    '@disneyd23',
    '@pixar',
    '@marvel',
    '@marvelstudios',
    '@lego',
    '@sanrio',
    '@hellokitty',
    '@hellokittylatinoamerica',
    '@hellokitty_50th',
    '@hellokittybrasil',
    '@kuromi_project',
    '@gudetama',
    '@lottiefiles'
]


def is_whitelist_tiktok_item(source: str, page_url: str) -> bool | None:
    if is_tiktok_source_or_hostname(source, page_url) is True:
        handle = extract_tiktok_handle(page_url)
        if handle in TIKTOK_WHITELIST:
            logger.debug(f'TikTokWhitelist | {handle} | {page_url}')
            return True
        else:
            logger.debug(f'TikTokExcluded | {handle} | {page_url}')
            return False

    return None


def is_tiktok_source_or_hostname(source: str, page_url: str) -> bool:
    if 'tiktok' in source.lower():
        return True

    hostname = urlparse(page_url).hostname

    if '.tiktok.' in hostname or hostname.startswith('tiktok.'):
        return True

    return False


def extract_tiktok_handle(url) -> str:
    parsed = urlparse(url)
    path_parts = parsed.path.strip('/').split('/')

    handle = path_parts[0]
    return handle


def verify_tiktok(url) -> dict[str, bool]:
    handle = extract_tiktok_handle(url)
    if handle in TIKTOK_WHITELIST:
        return {handle: True}
    else:
        return {handle: False}


def verify_tiktok_batch(video_urls) -> dict[str, bool]:
    results = {}
    for url in video_urls:
        results = results | verify_tiktok(url)
    return results
