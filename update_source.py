import json
import re
from datetime import datetime, timezone
from urllib.parse import unquote
import requests
from bs4 import BeautifulSoup

HOME = "https://moe.mohkg1017.pro/"
OUT = "moe-reddit.json"
BUNDLE_ID = "com.reddit.Reddit"
UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15"

s = requests.Session()
s.headers.update({"User-Agent": UA})

def clean_url(href):
    return unquote(href.strip())

def drive_id(url):
    url = clean_url(url)
    m = re.search(r"(?:/file/d/|[?&]id=)([A-Za-z0-9_-]{20,})", url)
    return m.group(1) if m else None

def find_reddit_card(soup):
    # Find the card containing the Reddit version/title, then search that card
    # (and a few parents) for its Drive download link.
    for node in soup.find_all(string=re.compile(r"Reddit\s+\d{4}\.\d+\.\d+", re.I)):
        el = node.parent
        for level in range(5):
            if el is None:
                break
            links = el.find_all("a", href=True)
            drive_links = [
                clean_url(a["href"]) for a in links
                if "drive.google.com" in a["href"] or "drive.usercontent.google.com" in a["href"]
            ]
            if drive_links:
                return el, drive_links[0]
            el = el.parent
    return None, None

def main():
    r = s.get(HOME, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    vm = re.search(r"Reddit\s+(\d{4}\.\d+\.\d+)", text, re.I)
    if not vm:
        raise RuntimeError("Could not find a Reddit version on Moe's homepage.")
    version = vm.group(1)

    card, href = find_reddit_card(soup)
    if not href:
        raise RuntimeError("Could not find the Reddit Google Drive link near the Reddit card.")

    fid = drive_id(href)
    if not fid:
        raise RuntimeError(f"Found a Reddit download link, but could not extract its Drive file ID: {href}")

    # Use the stable Google Drive download endpoint. It redirects to the
    # usercontent endpoint and is the form exposed by Moe's current site.
    download = f"https://drive.google.com/uc?export=download&id={fid}"

    data = {
        "name": "Moe's Reddit",
        "identifier": "moe.reddit.source",
        "subtitle": "Moe's Reddit SideStore source",
        "description": "Moe's Reddit — automatically tracked from Moe's App Hub.",
        "apps": [{
            "name": "Moe's Reddit",
            "bundleIdentifier": BUNDLE_ID,
            "developerName": "Moe / mohkg1017",
            "subtitle": "Patched Reddit",
            "localizedDescription": f"Moe's Reddit {version}.",
            "versions": [{
                "version": version,
                "date": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "downloadURL": download
            }]
        }]
    }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"Found Moe's Reddit {version}")
    print(f"Google Drive file: {fid}")
    print(f"Source updated: {OUT}")

if __name__ == "__main__":
    main()
