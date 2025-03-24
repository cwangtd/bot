import asyncio
from datetime import date, timedelta

from app.services.cloud_lens_helper import LTHelper

if __name__ == '__main__':
    lt_helper = LTHelper()
    lt_helper.exec()
