import json, re
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, NavigableString, Tag

BASE = "https://www.qbhouse.co.jp/search/"
HEADERS = {"User-Agent": "Mozilla/5.0 QB-HOUSE-Observatory/0.3"}
STORE = re.compile(r"^/search/\d+/?$")


def store_url(a):
    u = urljoin(BASE, a.get("href", ""))
    return u if STORE.fullmatch(urlparse(u).path) else None


def block_after(a):
    current = store_url(a)
    parts = []

    for x in a.next_elements:
        if isinstance(x, Tag) and x.name == "a":
            u = store_url(x)
            if u and u != current:
                break

        if isinstance(x, NavigableString):
            s = " ".join(str(x).split())
            if s:
                parts.append(s)

        if sum(map(len, parts)) > 800:
            break

    return " ".join(parts)


def fetch_page(page):
    r = requests.get(
        BASE,
        params={"pg": page},
        headers=HEADERS,
        timeout=(5, 15)
    )
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    anchors = []
    seen = set()

    for a in soup.find_all("a", href=True):
        u = store_url(a)
        name = " ".join(a.get_text(" ", strip=True).split())
        name = re.sub(r"^営業中\s*", "", name)

        if u and u not in seen and name.endswith("店"):
            seen.add(u)
            anchors.append((a, name, u))

    rows = []

    for a, name, u in anchors:
        text = block_after(a)
        mw = re.search(r"(\d{1,3})\s*人", text)
        mc = re.search(r"(\d{1,2})\s*席", text)

        if not (mw and mc):
            continue

        wait = int(mw.group(1))
        chairs = int(mc.group(1))

        rows.append({
            "name": name,
            "wait": wait,
            "chairs": chairs,
            "ratio": round(wait / chairs, 3) if chairs else 0,
            "open": True,
            "url": u
        })

    print(f"page {page}: stores={len(anchors)} live={len(rows)}")
    return rows, len(anchors)


def main():
    shops = []
    names = set()

    for page in range(1, 40):
        rows, count = fetch_page(page)

        for x in rows:
            if x["name"] not in names:
                names.add(x["name"])
                shops.append(x)

        if count < 20:
            break

    if not shops:
        raise RuntimeError("待ち人数・稼働席数を1件も抽出できませんでした")

    shops.sort(key=lambda x: (-x["wait"], x["name"]))

    data = {
        "updated_at": datetime.now(
            ZoneInfo("Asia/Tokyo")
        ).isoformat(timespec="seconds"),
        "source": BASE,
        "count": len(shops),
        "shops": shops
    }

    with open("data/shops.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"SAVED: {len(shops)} live shops")


if __name__ == "__main__":
    main()
