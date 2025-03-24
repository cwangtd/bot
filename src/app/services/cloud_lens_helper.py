import time
from datetime import date, timedelta

from playwright.sync_api import sync_playwright

LOGIN_URL = 'https://my.lifetime.life/login.html?resource=%2Fclubs%2Fnj%2Fflorham-park.html'
USERNAME = 'jj-gardener@hotmail.com'
PASSWORD = 'JiaJia!018'


class LTHelper:
    def __init__(self):
        self.playwright = None
        self.p_browser = None
        self.p_context = None

    def exec(self):
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            page.goto(LOGIN_URL)
            print(f'Navigated to {LOGIN_URL}')

            page.click('text=Accept All', timeout=1000)
            print('Accepted cookies')

            time.sleep(0.5)

            page.fill("#account-username", USERNAME)
            page.fill("#account-password", PASSWORD)
            page.click("#login-btn")

            page.wait_for_load_state("networkidle")
            print("Loaded login page")

            time.sleep(0.5)

            page.click('a:has-text("Class Schedules and Reservations")')
            page.wait_for_load_state("networkidle")
            print("Loaded reservation page")

            time.sleep(2)

            print("click DayView")
            page.get_by_text("Day View").click()
            print("clicked DayView")

            time.sleep(0.5)

            print("click NextWeek")
            page.get_by_text("Next Week").click()
            print("clicked NextWeek")

            today = date.today()
            target_date = today + timedelta(days=8)
            day_box_index = (target_date.weekday() + 1) % 7
            print(f'today: {today}, target_date: {target_date}, parsed: {day_box_index}')

            print("click Day")
            page.click(f'label[for="day-{day_box_index}"]')
            print("clicked Day")

            time_text = "10:30 AM"
            total_height = page.evaluate('document.body.scrollHeight')
            scroll_amount = total_height * 1
            print(f"Total height: {total_height}, scroll amount: {scroll_amount}")

            locator = page.locator(f"div.planner-time >> text={time_text}")
            bounding_box = locator.bounding_box()
            page.evaluate(f'window.scrollBy(0, {bounding_box.get("y")} - 150)')
            print("Scrolled to TimeText")

            locator = page.locator(f"div.planner-time >> text={time_text}")
            bounding_box = locator.bounding_box()
            print("TimeText position: ", bounding_box)

            time.sleep(300)

            # Close browser
            browser.close()
