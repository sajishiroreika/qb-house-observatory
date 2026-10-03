import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

BASE = "https://www.qbhouse.co.jp/search/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; QB-HOUSE-Observatory/0.2)"
}


def get_page(page):
    r = requests.get(
        BASE,
        params={"pref": "13", "pg": page},
        headers=HEADERS,
        timeout=15
    )
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def main():
    shops = []
    seen = set()

    # 東京都は現在146店舗。
    # 1ページ20店舗なので余裕を持って
