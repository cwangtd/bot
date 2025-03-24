import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger('main.app')

INSTAGRAM_WHITELIST = [
    "123rf",
    "pixlr",
    "vectrlabs",
    "alamyltd",
    "envato",
    "gettyimages",
    "gettyentertainment",
    "gettyimagesgallery",
    "gettyimageslatam",
    "gettyfc",
    "gettyfashion",
    "gettyimagescreative",
    "istockbygettyimages",
    "photos_dot_com",
    "motorsport.images",
    "shutterstock",
    "shutterstocknow",
    "pond5official",
    "premiumbeat",
    "turbosquid3d",
    "giphy",
    "splashnews",
    "backgrid_usa",
    "disney",
    "disneyland",
    "disneyparks",
    "disneysprings",
    "disneyplus",
    "waltdisneyworld",
    "disneychannel",
    "disneystore",
    "disneyxd",
    "disneyd23",
    "disneymusic",
    "disneygames",
    "pixar",
    "disneystudios",
    "marvel",
    "marvelstudios",
    "marvel_uk",
    "marvelsingapore",
    "spiderman",
    "lego",
    "nintendoamerica",
    "nintendo_jp",
    "nintendoswitches",
    "nintendonyc",
    "nintendoswitcheurope",
    "nintendo_brasil",
    "nintendoswitchde",
    "nintendoeurope",
    "nintendolatam",
    "sanrio",
    "hellokitty",
    "hellokittyeu",
    "gudetama",
    "lottie.files",
    "iconscout",
]


def is_whitelist_instagram_item(source: str, page_url: str) -> bool | None:
    if is_instagram_source_or_hostname(source, page_url) is True:
        username = get_instagram_username(page_url)
        if username in INSTAGRAM_WHITELIST:
            logger.debug(f'InstagramWhitelist | {username} | {page_url}')
            return True
        else:
            logger.debug(f'InstagramExcluded | {username} | {page_url}')
            return False

    return None


def is_instagram_source_or_hostname(source: str, page_url: str) -> bool:
    if 'instagram' in source.lower():
        return True

    hostname = urlparse(page_url).hostname

    if '.instagram.' in hostname or hostname.startswith('instagram.'):
        return True

    return False


def get_instagram_username(url):
    url_parts = url.split('?')[0].split('/')

    # This kinds of links contains target id, no need to open the page
    if len(url_parts) == 5 or url_parts[4] in ['p', 'reel', 'reels']:
        return url_parts[3]

    return None


# The following posts the URL externally to verify the Instagram URL for the username. No need as of now, since parsing
# the URLs with above checks provides covering 75% with 99% accuracy already.

def verify_instagram(url) -> dict[str, bool]:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    tag = soup.find('link', {'rel': 'canonical'})

    if tag and isinstance(tag['href'], str):
        username = tag['href'].split('/')[3]
    else:
        logger.debug(f'InstagramUrl | video id not found | {url}')
        username = None

    return {url: username in INSTAGRAM_WHITELIST}
