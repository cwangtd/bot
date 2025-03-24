import logging
import random
from urllib.parse import urlunparse, urlencode, urlparse, parse_qs, unquote

from app.common.http_async_builder import HttpAsyncBuilder

logger = logging.getLogger('main.app')

YOUTUBE_HOSTNAMES_1 = [
    'youtu.be'
]

YOUTUBE_HOSTNAMES_2 = [
    'youtube.com',
    'www.youtube.com',
    'm.youtube.com',
    'music.youtube.com'
]

YOUTUBE_CHANNEL_IDS = [
    'UCeYC3Tgzxk5pfjwuZ3H-FAg',
    'UCGUShWfYw_wQqekVE1P6lXg',
    'UC-cJMcXP4znmrj8_DF-EuvA',
    'UCUMsDSS8qUmnjhC0ZVx3IHQ',
    'UCJr72fY4cTaNZv7WPbvjaSw',
    'UC8lxnUR_CzruT2KA6cb7p0Q',
    'UCcIgGcUE-nb1tYKya3Qtp0Q',
    'UCuvxk-nQcFFDjdWK0-84O0Q',
    'UCqtjgA6BJGCijCFPwDV8m7w',
    'UCmhVYUCCOm0D5bT12MOr5_w',
    'UC1wcziqCAX3PggjsmmivVJQ',
    'UC9jxLH1qpABekhHjmWrvjfg',
    'UCP1hdrxYHdebGqbQawOMRpQ',
    'UCYwFyFjFUSRcwYCIxHmRBMQ',
    'UC_5niPa-d35gg88HaS7RrIw',
    'UCIrgJInjLS2BhlHOMDW7v0g',
    'UC3uPK6zOTe0HOfcIkuzII0Q',
    'UC1xwwLwm6WSMbUn_Tp597hQ',
    'UCgwv23FVv3lqh567yagXfNg',
    'UCApaSzvP6jM9rfs8UbcqD1g',
    'UCw7SNYrYei7F5ttQO3o-rpA',
    'UC_IRYSp4auq7hKLvziWVH6w',
    'UC1ofxPvkeZ178_jNcQhpGdw',
    'UCvC4D8onUfXzvjTOM-dBfEA',
    'UCxwitsUVNzwS5XBSC5UQV8Q',
    'UCP-Ng5SXUEt0VE-TXqRdL6g',
    'UCpeX7ds2tTpiRMwga0jUq8g',
    'UCGIY_O-8vW4rfX98KlMkvRg',
    'UCkH3CcMfqww9RsZvPRPkAJA',
    'UCEG4fd9DERXPzziMo3WgYMA',
    'UCFctpiB_Hnlk3ejWfHqSm6Q',
    'UC_SI1j1d8vJo_rYMV5o_dRg',
    'UCQBOAYwPdqzr1TxmjT-91Sg',
    'UCpZqbJnB1yr3pzNgYGjWvfw'
]

YOUTUBE_API_KEYS = [
    # Provenance-Produce
    # https://console.cloud.google.com/apis/api/youtube.googleapis.com/credentials?project=provenance-a100
    # TODO: restore it later
    # 'AIzaSyDI3q1VkG_reT8C7HII-UZUunzHgOadZaU',
    # Provenance-External
    # https://console.cloud.google.com/apis/credentials?project=provenance-external
    'AIzaSyAi-njeRhbcrIgDZDiHhtq160M5s-i48gQ',
    # Provenance-Research
    # https://console.cloud.google.com/apis/api/youtube.googleapis.com/credentials?project=deft-ellipse-396423
    'AIzaSyAm0Iyn8-GDCpMUE05i8ISyEDh67deSPGs'
]


def is_whitelist_youtube_item(source: str, page_url: str) -> bool | None:
    if is_youtube_source_or_hostname(source, page_url) is True:
        video_id = parse_youtube_video_id(page_url)
        if video_id is not None:
            return True
        else:
            logger.debug(f'YouTubeExcluded | {page_url}')
            return False

    return None


def is_youtube_source_or_hostname(source: str, page_url: str) -> bool:
    if 'youtube' in source.lower():
        return True

    hostname = urlparse(page_url).hostname

    if '.youtube.' in hostname or hostname.startswith('youtube.'):
        return True

    if 'youtu.be' in hostname:
        return True

    return False


def parse_youtube_video_id(video_url) -> str | None:
    # Examples:
    # - http://youtu.be/SA2iWivDJiE
    # - http://www.youtube.com/watch?v=_oPAwA_Udwc&feature=feedu
    # - http://www.youtube.com/embed/SA2iWivDJiE
    # - http://www.youtube.com/shorts/SA2iWivDJiE
    # - http://www.youtube.com/v/SA2iWivDJiE?version=3&amp;hl=en_US
    parsed = urlparse(video_url)
    if parsed.hostname in YOUTUBE_HOSTNAMES_1:
        return parsed.path[1:]

    if parsed.hostname in YOUTUBE_HOSTNAMES_2:
        if parsed.path == '/watch': return parse_qs(parsed.query)['v'][0]
        if parsed.path[:7] == '/watch/': return parsed.path.split('/')[2]
        if parsed.path[:7] == '/embed/': return parsed.path.split('/')[2]
        if parsed.path[:8] == '/shorts/': return parsed.path.split('/')[2]
        if parsed.path[:3] == '/v/': return parsed.path.split('/')[2]

    logger.debug(f'YouTubeExcluded | {video_url}')

    return None


async def batch_verify_youtube(video_ids: list[str]) -> dict[str, bool]:
    index = random.randint(0, len(YOUTUBE_API_KEYS) - 1)

    params = {
        'part': 'snippet',
        'fields': 'items(id,snippet(channelId))',
        'id': ','.join(video_ids),
        'key': YOUTUBE_API_KEYS[index]
    }

    url = urlunparse((
        'https',
        'www.googleapis.com',
        'youtube/v3/videos',
        '',
        urlencode(params),
        ''
    ))

    # TODO: what's the max number of video_ids?
    video_id_channel_dict = {x: False for x in video_ids}

    response = await HttpAsyncBuilder(url).execute()
    if not response.is_success:
        return video_id_channel_dict

    status_code = response.status_code
    result = response.json()
    if status_code == 200:
        if 'items' in result and len(result['items']) > 0:
            for item in result['items']:
                video_id = item['id']
                channel_id = item['snippet']['channelId']
                if channel_id in YOUTUBE_CHANNEL_IDS:
                    video_id_channel_dict[video_id] = True
    else:
        if 'error' in result and 'message' in result['error']:
            message = unquote(result['error']['message'])
            logger.error(f'YouTubeUrl | HTTP_{status_code} | {url} | {message}')
        else:
            logger.info(f'YouTubeUrl | HTTP_{status_code} | {url}')

    official = []
    non_official = []
    for k, v in video_id_channel_dict.items():
        if v is False:
            official.append(k)
        else:
            non_official.append(k)
    logger.info(f'YouTubeVerify | {official} | {non_official}')

    return video_id_channel_dict
