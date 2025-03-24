import argparse
import time
from datetime import date, timedelta, datetime

from playwright.sync_api import sync_playwright

LOGIN_URL = 'https://my.lifetime.life/login.html?resource=%2Fclubs%2Fnj%2Fflorham-park.html'
RESERVE_URL = 'https://my.lifetime.life/clubs/nj/florham-park/resource-booking.html?sport=Pickleball%3A+Indoor&clubId=165&duration=60&hideModal=true&startTime=-1&date='
USERNAME = 'jj-gardener@hotmail.com'
PASSWORD = 'JiaJia!018'


class LTHelper:
    @staticmethod
    def exec(rev_in_days: int, rev_time: str):
        target_date = date.today() + timedelta(days=rev_in_days)
        print(f'Now: {datetime.now()}, target_date: {target_date}, target time: {rev_time}')

        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(timeout=120000)
            context = browser.new_context()
            page = context.new_page()

            page.goto(LOGIN_URL)
            print(f'Loaded {LOGIN_URL}')

            time.sleep(1)

            try:
                page.click('text=Accept All', timeout=1000)
                print('Accepted cookies')
                time.sleep(1)
            except:
                print('No cookies to accept')

            page.fill('#account-username', USERNAME)
            page.fill('#account-password', PASSWORD)
            page.click('#login-btn')
            print('Clicked login button')

            page.wait_for_load_state('networkidle')
            print('Loaded login page')

            time.sleep(1)

            rev_url = RESERVE_URL + str(target_date)
            page.goto(rev_url)
            print(f'Goto {rev_url}')

            time.sleep(1)

            rev_time_element = f"a[data-testid='resourceBookingTile']:has(div.timeslot-time:text('{rev_time}'))"
            rev_time_locator = page.locator(rev_time_element).nth(0)

            try:
                bounding_box = rev_time_locator.bounding_box()
                print(f'Found RevText [0] at: {bounding_box}')
            except:
                print(f'Failed to find RevTime at {rev_time}')
                return

            rev_time_locator.click()
            print(f'Clicked RevTime: {rev_time}')

            page.wait_for_load_state('networkidle')

            checkbox = page.locator("label[data-testid='acceptWaiver']")
            checkbox.click()
            is_checked = checkbox.is_checked()
            print(f'Checkbox is checked: {is_checked}')

            finish_button = page.locator("button[data-testid='finishBtn']")
            finish_button.click()
            print('Clicked Finish')

            time.sleep(1)
            browser.close()
            print('All set!')


parser = argparse.ArgumentParser(description='Example script for reading arguments')
parser.add_argument("--in_days", type=int, default=8)
parser.add_argument("--time", type=str, default='9:30_PM')
args = parser.parse_args()

LTHelper.exec(args.in_days, args.time.replace('_', ' '))
