# Selenium causes cold start. Replaced it with requests already. Keep it here for reference and benchmarking.
import sys
import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service

from app.services.cloud_lens_helper import SINGLE_KIND, GROUP_KIND, logger
from app.common.logger_common import log_exception, timed_log

WEBDRIVER_OPTIONS = webdriver.FirefoxOptions()
WEBDRIVER_OPTIONS.add_argument('--headless')
WEBDRIVER_OPTIONS.add_argument('--disable-gpu')
WEBDRIVER_OPTIONS.add_argument('--no-sandbox')
WEBDRIVER_OPTIONS.add_argument('window-size=1024,768')

FIREFOX_DRIVER_PATH = '/usr/bin/geckodriver'

is_mac = 'darwin' in sys.platform
if is_mac:
    web_driver = webdriver.Firefox(options=WEBDRIVER_OPTIONS)
else:
    service = Service(executable_path=FIREFOX_DRIVER_PATH)
    web_driver = webdriver.Firefox(service=service, options=WEBDRIVER_OPTIONS)


async def lens_selenium_crawler(page_url) -> dict:
    try:
        start_time = time.perf_counter()
        web_driver.get(page_url)
        timed_log('LensSeleniumCrawler', start_time, page_url)

        soup = BeautifulSoup(web_driver.page_source, 'html.parser')
        divs = soup.findAll(custom_selector)

        data_dict = {
            SINGLE_KIND: [],
            GROUP_KIND: []
        }
        for div in divs:
            kind, item = extract_item(div)
            if kind == SINGLE_KIND:
                data_dict[kind].append(item[0])
            elif kind == GROUP_KIND:
                data_dict[kind].extend(item)
            else:
                logger.warning(f'Unsupported div | {div}')
        return data_dict

    except Exception:
        log_exception(tag='LensSeleniumCrawl', level_func=logger.warning)
        return {}


def stop_selenium():
    web_driver.quit()


def custom_selector(tag):
    return tag.name == 'div' and \
        (tag.find(is_div_with_data_action_url_and_with_a_with_img, recursive=False) or
         tag.find(is_div_with_span_and_with_div_with_a_with_img, recursive=False) or
         tag.find(is_div_with_div_with_data_index_and_with_div_with_div_with_img, recursive=False))


def is_div_with_span_and_with_div_with_a_with_img(tag):
    return tag.name == 'div' and \
        tag.find('span', recursive=False) and \
        tag.find(is_div_with_a_with_img, recursive=False)


def is_div_with_a_with_img(tag):
    return tag.name == 'div' and tag.find(is_a_with_img, recursive=False)


def is_div_with_data_action_url_and_with_a_with_img(tag):
    return tag.name == 'div' and tag.has_attr('data-action-url') and tag.find(is_a_with_img, recursive=False)


def is_div_with_div_with_data_index_and_with_div_with_div_with_img(tag):
    return tag.name == 'div' and tag.find(is_div_with_data_index_and_with_div_with_div_with_img, recursive=False)


def is_div_with_data_index_and_with_div_with_div_with_img(tag):
    return tag.name == 'div' and \
        tag.has_attr('data-index') and \
        tag.find(is_div_with_div_with_a_with_img, recursive=False)


def is_div_with_div_with_a_with_img(tag):
    return tag.name == 'div' and tag.find(is_div_with_img, recursive=False)


def is_div_with_img(tag):
    return tag.name == 'div' and tag.find(is_img_tag, recursive=False)


def is_a_with_img(tag):
    return tag.name == 'a' and tag.has_attr('aria-label') and tag.find(is_img_tag)


def is_img_tag(tag):
    return tag.name == 'img'


def extract_item(box) -> tuple:
    try:
        box = box.findChildren()[0]
        if box.findChildren()[0].name == 'a':
            content = {}

            main_a = box.select_one('a')
            content['title'] = main_a['aria-label']
            content['pageUrl'] = main_a['href']

            thumbnail_div = box.select_one('div[data-thumbnail-url]')
            content['imageUrl'] = thumbnail_div['data-thumbnail-url']

            # TODO: is it necessary?
            # icon_img = box.select_one('div > img')
            # content['source_icon'] = icon_img['src']

            source_span = box.select_one('div > span')
            content['source'] = source_span.text.strip()
            return SINGLE_KIND, [content]

        elif box.findChildren()[0].name == 'span':
            data = []
            children = box.select(':scope > div')

            for child in children:
                content = {}

                link_a = child.select_one('a')
                if link_a is not None:
                    content['keyword'] = link_a['aria-label']
                    content['pageUrl'] = link_a['href']

                    thumbnail_img = box.select_one('img')
                    content['imageUrl'] = thumbnail_img['src']
                    data.append(content)

            return GROUP_KIND, data

        elif box.findChildren()[0].name == 'div':
            data = []
            children = box.select(':scope > div')

            for child in children:
                content = {}

                tag_img = child.select_one('img')
                if tag_img is not None:
                    content['keyword'] = child['aria-label'].replace('Show results for ', '')  # TODO: hacks
                    content['pageUrl'] = ''

                    content['imageUrl'] = tag_img['src']
                    data.append(content)

            return GROUP_KIND, data

        else:
            return None, [box]

    except Exception:
        log_exception(tag='ExtractItem', level_func=logger.warning)
        return SINGLE_KIND, []
