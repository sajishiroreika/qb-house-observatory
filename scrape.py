import json
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

URL = "https://www.qbhouse.co.jp/search/?pref=13"

def main():
    print("START")
    r = requests.get(URL, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    shops = []
    seen = set()

    for a in soup.find_all("a"):
        name = a.get_text(" ", strip=True)
        href = a.get("href", "")

        if "/shop/" in href and name.endswith("店") and name not in seen:
            seen.add(name)
            shops.append({
                "name": name,
                "wait": 0,
                "chairs": 0,
                "open": False
            })

    print("FOUND:", len(shops))

    if not shops:
        raise RuntimeError("0 shops found")

    data = {
        "updated_at": datetime.now(
            ZoneInfo("Asia/Tokyo")
        ).isoformat(timespec="seconds"),
        "source": URL,
        "count": len(shops),
        "shops": shops
    }

    with open("data/shops.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("SAVED")

if __name__ == "__main__":
    main()
