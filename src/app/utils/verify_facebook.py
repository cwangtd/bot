import logging
import re
from urllib.parse import urlparse

# TODO: selenium requires to enable the webdriver in the docker container. skip it for now.
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger('main.app')

# Notes the white list needs to include ['custom id', 'user id', 'page id'],
# due to different facebook links may contain different type of ids.
FACEBOOK_WHITELIST = [
    "123rf", "100064597277703", "226337619020",
    "pixlr", "100087924176394", "35846011511",
    "vectrlabs", "100063653376591", "374473049367685",
    "alamy", "100044551984398", "150454471633963",
    "envato", "100064697080464", "80655071208",
    "tutsplus", "100064909863265", "262345235441",
    "gettyimages", "100064621066413", "59323386296",
    "gettyimagescreative", "100063803791861", "177779596171657",
    "istock", "100063803791861", "20425620824",
    "unsplash", "100037567525321", "274126369394815",
    "photosdotcom", "100063803791861", "235405413329678",
    "msimages", "100058167635434", "133490353855070",
    "shutterstock", "61559669277032", "8333641277",
    "shutterstockin", "100064682463042", "139297833376018",
    "shutterstocknow", "100067203391106", "488694027963779",
    "pond5", "100064769138584", "29824144776",
    "premiumbeat", "100082225600065", "19077477128",
    "turbosquid3dmodels", "100064405105209", "98679001927",
    "giphy", "100083174770172", "161296994019700",
    "splashnewsofficial", "100063582100026", "64983634297",
    "backgriduk", "100064643923517", "230900160435474",
    "disney", "61564264790404", "11784025953",
    "waltdisneyworld", "100089566255515", "155669083273",
    "thewaltdisneycompany", "100077226707064", "100439316228953",
    "officialdisneyfamily", "100063579670651", "779608638838023",
    "waltdisneystudios", "100093837594721", "111382562236411",
    "disneyplus", "100008766162551", "1233731130062594",
    "disneyparks", "100089566255515", "143728699029618",
    "disneyd23", "100069666487055", "147415861937130",
    "disneymusic", "100077226707064", "104788928960",
    "disneystore", "100064937371914", "59526724529",
    "disneyanimation", "100064814673345", "23245476854",
    "disneygames", "100064782096202", "107118476015267",
    "wdwcastandcommunity", "100064622084725", "342155202547002",
    "disneycareers", "100064713785350", "159083610825448",
    "disneyxd", "100042292598188", "312170355491069",
    "pixar", "100063746942453", "35245929077",
    "marvel", "100044606041735", "6883542487",
    "marvelstudios", "61564264790404", "134891530271801",
    "marveluk", "100025213840304", "237586379701646",
    "marvelaunz", "100064351732658", "110105795765751",
    "marvelindia", "100005912319815", "238025949580163",
    "lego", "100083145071487", "6665038402",
    "nintendoamerica", "61561984949285", "119240841493711",
    "nintendoswitch", "100064811613959", "1125429570886433",
    "nintendoofcanada", "100063573759760", "164247893699572",
    "nintendosea", "100072645960786", "108195071594208",
    "nintendo3ds", "100079178540208", "149152295156770",
    "nintendohk", "100067411749149", "1407500729466406",
    "pokemon", "61555068958123", "230809307041021",
    "officialpokemonindia", "100066663694478", "185178755369989",
    "officialpokemonph", "100065084328470", "203560506853810",
    "pokemonthailand", "100064564426896", "782591045138650",
    "pokemonofficialsingapore", "100063456282102", "1914558152204438",
    "pokemonofficialindonesia", "100047612777311", "1986498921639214",
    "sanrio", "100036174776166", "51860737815",
    "hellokitty", "100044331464480", "40444963499",
    "gudetama", "100083348317123", "1078616742164891",
    "lottiefiles", "100063832940702", "1688971301114476",
    "theiconscout", "100063890470457", "508565185968336",
]

global_driver = None


# def get_driver():
#     global global_driver
#     if global_driver is not None:
#         return global_driver
#
#     options = Options()
#     options.add_argument('--headless')
#     options.add_argument('--no-sandbox')
#     options.add_argument('--disable-dev-shm-usage')
#
#     service = Service(ChromeDriverManager().install())
#     global_driver = webdriver.Chrome(service=service, options=options)
#     return global_driver


def is_whitelist_facebook_item(source: str, page_url: str) -> bool | None:
    if is_facebook_source_or_hostname(source, page_url) is True:
        facebook_id = get_facebook_id(page_url)
        if facebook_id in FACEBOOK_WHITELIST:
            logger.debug(f'FacebookWhitelist | {facebook_id} | {page_url}')
            return True
        else:
            logger.debug(f'FacebookExcluded | {facebook_id} | {page_url}')
            return False

    return None


def is_facebook_source_or_hostname(source: str, page_url: str) -> bool:
    if 'facebook' in source.lower():
        return True

    hostname = urlparse(page_url).hostname

    if '.facebook.' in hostname or hostname.startswith('facebook.'):
        return True

    return False


# def fetch_facebook_user_id(url):
#     driver = get_driver()
#     driver.get(url)
#
#     found_user_ids = re.findall(r"\"owner\":\{\"__typename\":\"User\",\"id\":\"([0-9]+)\"", driver.page_source)
#     if len(found_user_ids) > 0:
#         return found_user_ids[0]
#
#     canonical_element = driver.find_element(By.CSS_SELECTOR, 'link[rel="canonical"]')
#     if canonical_element is not None:
#         matched_items = re.findall(r"[&?]id=([0-9]+)", canonical_element.get_attribute('href'))
#         if len(matched_items) > 0:
#             return matched_items[0]
#
#     return None


def get_facebook_id(url):
    split_link = url.split('/')
    if len(split_link) > 4 and split_link[4] in ['photos', 'videos', 'posts', 'community', 'about', 'events']:
        to_verify_id = split_link[3]
    elif len(split_link) == 5 and split_link[4] == "":
        to_verify_id = split_link[3]
    elif re.search(r'[&?]id=[0-9]+', url):
        to_verify_id = re.search(r'[&?]id=([0-9]+)', url).group(1)
    elif split_link[3] == 'p':
        split_page_name = split_link[4].split('-')
        to_verify_id = split_page_name[-1]
    elif len(split_link) == 5 and "id=" not in split_link[4]:
        to_verify_id = split_link[3]
    elif split_link[3] in ['marketplace', 'hashtag', 'groups', 'public']:
        to_verify_id = None
    elif len(split_link) == 4 and '?' not in split_link[3]:
        split_page_name = split_link[3].split('-')
        to_verify_id = split_page_name[-1]
    elif split_link[3] == 'people':
        to_verify_id = split_link[5]
    elif split_link[3] in ['pages', 'watch', 'gaming']:
        to_verify_id = split_link[4]
    elif split_link[3].startswith('photo.php?') or split_link[3] in ['media', 'photo', 'reel']:
        # to_verify_id = fetch_facebook_user_id(url)
        logger.debug(f'FacebookUrl | skipped | {url}')
        to_verify_id = None
    else:
        logger.debug(f'FacebookUrl | unknown | {url}')
        to_verify_id = None

    if to_verify_id is None:
        return None
    # Dot will be ignored for username. See https://www.facebook.com/help/1644118259243888
    return to_verify_id.lower().replace('.', '')
