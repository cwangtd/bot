import logging
from urllib.parse import urlparse

logger = logging.getLogger('main.app')

TWITTER_WHITELIST = [
    '123rf',
    'pixlr',
    'vectrlabs',
    'alamy',
    'Alamy_Editorial',
    'AlamyContent',
    'AlamyNews',
    'envato',
    'EnvatoElements',
    'envato_help',
    'EnvatoMarket',
    'tutsplus',
    'GettyImages',
    'gettyvip',
    'iStock',
    'picscout',
    'MSI_Images',
    'Shutterstock',
    'ShutterstockNow',
    'SKcontributors',
    'pond5',
    'PremiumBeat',
    'TurboSquid',
    'GIPHY',
    'SplashNews',
    'BackgridUK',
    'BackgridUS',
    'Disney',
    'DisneyStudios',
    'DisneyPlus',
    'DisneyChannel',
    'DisneyAnimation',
    'DisneyParks',
    'DisneyMusic',
    'DisneyGames',
    'DisneyXD',
    'DisneyD23',
    'Pixar',
    'Marvel',
    'MarvelStudios',
    'MarvelGames',
    'LEGO_Group',
    'Nintendo',
    'NintendoAmerica',
    'NintendoEurope',
    'NintendoAUNZ',
    'NintendoUK',
    'NintendoFrance',
    'NintendoDE',
    'NintendoES',
    'NintendoItalia',
    'NintendoRU',
    'NintendoNYC',
    'NintendoVS',
    'Pokemon',
    'Pokemon_cojp',
    'apppokemon',
    'pokemon_movie',
    'sanrio',
    'sanrio_news',
    'hellokitty',
    'gudetamatweets',
    'LottieFiles',
    'IconScout'
]


def is_whitelist_twitter_item(source: str, page_url: str) -> bool | None:
    if is_twitter_source_or_hostname(source, page_url) is True:
        username = extract_twitter_username(page_url)
        if username in TWITTER_WHITELIST:
            logger.debug(f'TwitterWhitelist | {username} | {page_url}')
            return True
        else:
            logger.debug(f'TwitterExcluded | {username} | {page_url}')
            return False

    return None


def is_twitter_source_or_hostname(source: str, page_url: str) -> bool:
    if 'twitter' in source.lower():
        return True

    if 'x' == source.lower():
        return True

    hostname = urlparse(page_url).hostname

    if '.twitter.' in hostname or hostname.startswith('twitter.'):
        return True

    if '.x.' in hostname or hostname.startswith('x.'):
        return True

    return False


def verify_twitter(url: str) -> bool:
    username = extract_twitter_username(url)
    return username in TWITTER_WHITELIST if username else False


def extract_twitter_username(twitter_url: str) -> str | None:
    parsed = urlparse(twitter_url)

    path_parts = parsed.path.strip('/').split('/')

    # Check for direct handle
    # https://x.com/[HANDLE] or https://twitter.com/[HANDLE]
    if len(path_parts) == 1 and path_parts[0]:
        return path_parts[0]

    # Check for post URL or photo URL
    # https://x.com/[HANDLE]/status/[POST_ID] or https://x.com/[HANDLE]/status/[POST_ID]/photo/[PHOTO_#]
    if len(path_parts) >= 3 and path_parts[1] == 'status':
        return path_parts[0]

    return None

    # TODO - other cases are not common and require API calls
    # # Check for intent URL with screen name: https://x.com/intent/user?screen_name=[HANDLE]
    # if parsed.path == '/intent/user':
    #     query_params = parse_qs(parsed.query)
    #     if 'screen_name' in query_params:
    #         return query_params['screen_name'][0]
    #     elif 'user_id' in query_params:
    #         user_id = query_params['user_id'][0]
    #         return await get_username_from_user_id(user_id)
    #
    # # Handle short URL: https://x.com/i/status/[POST_ID]
    # if len(path_parts) == 3 and path_parts[0] == 'i' and path_parts[1] == 'status':
    #     post_id = path_parts[2]
    #     return await get_tweet_author_username(post_id)
    #
    # return None

# BEARER_TOKEN = 'BEARER_TOKEN'
#
# HEADERS = {
#     'Authorization': f'Bearer {BEARER_TOKEN}'
# }

# async def get_username_from_user_id(user_id):
#     url = f'https://api.twitter.com/2/users/{user_id}'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=HEADERS) as response:
#             user_data = await response.json()
#             return user_data['data']['username']
#
#
# async def get_tweet_author_username(tweet_id):
#     url = f'https://api.twitter.com/2/tweets/{tweet_id}?expansions=author_id'
#     async with aiohttp.ClientSession() as session:
#         async with session.get(url, headers=HEADERS) as response:
#             tweet_data = await response.json()
#             author_id = tweet_data['includes']['users'][0]['id']
#             return await get_username_from_user_id(author_id)
