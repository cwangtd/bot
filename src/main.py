import argparse
import platform
import time
from datetime import date, timedelta, datetime

from playwright.sync_api import sync_playwright

LOGIN_URL = 'https://my.lifetime.life/login.html?resource=%2Fclubs%2Fnj%2Fflorham-park.html'
RESERVE_URL = 'https://my.lifetime.life/clubs/nj/florham-park/resource-booking.html?sport=Pickleball%3A+Indoor&clubId=165&hideModal=true&startTime=-1'

ACCOUNT = [
    ('jj-gardener@hotmail.com', 'JiaJia!018')
]

TOTAL_ATTEMPTS = 10

MAKE_RESERVATION_ATTEMPTS = 10

RENDER_RESERVATION_MAX_ATTEMPTS = 20
RENDER_RESERVATION_RETRY_PAUSE = 2

RENDER_RESERVATION_ATTEMPTS_PER_MIN = 60 / RENDER_RESERVATION_RETRY_PAUSE
RENDER_RESERVATION_ATTEMPT_DURATION_MIN = RENDER_RESERVATION_MAX_ATTEMPTS / RENDER_RESERVATION_ATTEMPTS_PER_MIN

BROWSER_TIMEOUT = int(RENDER_RESERVATION_ATTEMPT_DURATION_MIN * 2) * 60 * 1000
PAGE_TIMEOUT = 5 * 1000
UI_TIMEOUT = 3 * 1000


class LTHelper:
    def __init__(self, account_id, advance_in_days, rev_time):
        self.username, self.password = ACCOUNT[account_id]
        self.target_date = date.today() + timedelta(days=advance_in_days)
        self.target_time = rev_time
        print(f'{datetime.now()} | target date: {self.target_date}, target time: {self.target_time}')

    def exec(self):
        is_not_mac = platform.system().lower() != "darwin"
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(timeout=BROWSER_TIMEOUT, headless=is_not_mac)
            context = browser.new_context()
            page = context.new_page()

            page.goto(LOGIN_URL)
            time.sleep(1)

            try:
                page.click('text=Accept All', timeout=UI_TIMEOUT)
                time.sleep(1)
            except:
                print(f'{datetime.now()} | No cookies to accept')

            page.fill('#account-username', self.username)
            page.fill('#account-password', self.password)
            page.click('#login-btn')
            page.wait_for_load_state('networkidle')
            print(f'{datetime.now()} | Loaded login page')

            for _ in range(TOTAL_ATTEMPTS):
                if self.attempt(page):
                    break

            time.sleep(1)
            browser.close()

    def attempt(self, page) -> bool:
        on_reservation_page = self.render_reservation(page)
        if not on_reservation_page:
            print(f'{datetime.now()} | Abort')
            return False

        made_reservation = self.make_reservation(page)
        if not made_reservation:
            print(f'{datetime.now()} | Result: {made_reservation}')
            return False

        return True

    @staticmethod
    def make_reservation(page) -> bool:
        checkbox_selector = "label[data-testid='acceptWaiver']"
        finish_button_selector = "button[data-testid='finishBtn']"

        for attempt in range(MAKE_RESERVATION_ATTEMPTS):
            try:
                checkbox = page.locator(checkbox_selector)
                checkbox.click(timeout=UI_TIMEOUT)
                if checkbox.is_checked(timeout=UI_TIMEOUT):
                    finish = page.locator(finish_button_selector)
                    finish.click(timeout=UI_TIMEOUT)
                    print(f'{datetime.now()} | Clicked Finish')
                    return True
            except Exception as e:
                print(f'{datetime.now()} | Attempt {attempt + 1}/{MAKE_RESERVATION_ATTEMPTS}, failed: {e}')
        return False

    def render_reservation(self, page) -> bool:
        _max_attempts = RENDER_RESERVATION_MAX_ATTEMPTS
        _count = 0
        while _count < _max_attempts:
            _date = str(self.target_date)
            _duration = 30 if _count % 2 == 0 else 60
            _clicked = self.goto_reservation_page(page, _date, _duration)
            print(f'{datetime.now()} | Reservation {_count}/{_max_attempts}, page opened: {_clicked}')
            _count += 1
            if _clicked:
                return True
            else:
                time.sleep(RENDER_RESERVATION_RETRY_PAUSE)
        return False

    def goto_reservation_page(self, page, date, duration) -> bool:
        try:
            rev_url = RESERVE_URL + f'&date={date}&duration={duration}'
            page.goto(rev_url, timeout=PAGE_TIMEOUT)
            page.wait_for_load_state('networkidle')

            timeslot = f"a[data-testid='resourceBookingTile']:has(div.timeslot-time:text('{self.target_time}'))"
            locator = page.locator(timeslot).nth(0)
            if locator.is_visible(timeout=UI_TIMEOUT):
                locator.click(timeout=UI_TIMEOUT)
                page.wait_for_load_state('networkidle')
                print(f'{datetime.now()} | Clicked: {self.target_time}')
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False


parser = argparse.ArgumentParser(description='ArgumentParser')
parser.add_argument("--a", type=int, default=0)
parser.add_argument("--d", type=int, default=8)
parser.add_argument("--t", type=str, default='9:30PM')
args = parser.parse_args()

LTHelper(args.a, args.d, args.t.replace('AM', ' AM').replace('PM', ' PM')).exec()
