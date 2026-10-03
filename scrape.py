import json, re
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

BASE = "https://www.qbhouse.co.jp/search/"
HEADERS = {"User-Agent": "QB-HOUSE-Observatory/0.1 (unofficial personal project)"}

def parse_page(page):
    r = requests.get(BASE, params={"pg": page}, headers=HEADERS, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text("\n", strip=True)

    # QB HOUSEの表示テキストから「営業中 店舗名 ... N人 M席」を拾う。
    # サイト側HTML変更時に壊れやすいため、0件なら異常終了させる。
    pattern = re.compile(
        r"営業中\s*([^\n]+?店)\s*.*?(\d+)人\s+(\d+)席",
        re.S
    )
    out = []
    for name, wait, chairs in pattern.findall(text):
        out.append({
            "name": re.sub(r"\s+", " ", name).strip(),
            "wait": int(wait),
            "chairs": int(chairs),
            "open": True
        })
    return out, text

def main():
    shops = []
    seen = set()

    # 全国605店。1ページあたりの件数が変わっても余裕を持って巡回し、
    # 連続して店舗が見つからなくなったら終了。
    empty = 0
    for page in range(1, 80):
        rows, text = parse_page(page)
        if not rows:
            empty += 1
            if empty >= 3:
                break
            continue
        empty = 0
        for x in rows:
            key = x["name"]
            if key not in seen:
                seen.add(key)
                x["ratio"] = round(x["wait"] / x["chairs"], 3) if x["chairs"] else 0
                shops.append(x)

    if not shops:
        raise RuntimeError("店舗データを取得できませんでした。QB HOUSE側の表示変更を確認してください。")

    shops.sort(key=lambda x: (-x["wait"], x["name"]))
    payload = {
        "updated_at": datetime.now(ZoneInfo("Asia/Tokyo")).isoformat(timespec="seconds"),
        "source": BASE,
        "count": len(shops),
        "shops": shops
    }
    with open("data/shops.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
