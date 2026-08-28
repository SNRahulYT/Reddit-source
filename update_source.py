#!/usr/bin/env python3
import json, re, sys
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, unquote
import requests
from bs4 import BeautifulSoup

APP_PAGE = "https://moe.mohkg1017.pro/app/app_1769231115_3988"
OUT = "moe-reddit.json"
BUNDLE_ID = "com.reddit.Reddit"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MoeRedditSideStoreUpdater/1.0)"
})

def drive_direct(url):
    url = unquote(url)
    m = re.search(r"(?:/file/d/|[?&]id=)([A-Za-z0-9_-]{10,})", url)
    if not m:
        return url
    file_id = m.group(1)
    return f"https://drive.usercontent.google.com/download?id={file_id}&export=download&confirm=t"

def find_version(text):
    patterns = [
        r"Reddit\s+(\d{4}\.\d+\.\d+)",
        r"(\d{4}\.\d+\.\d+)\s*[—-]\s*Moe",
        r"Moe(?:'s)?\s*Reddit[^\d]*(\d{4}\.\d+\.\d+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            return m.group(1)
    return None

def find_download(soup):
    candidates = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        label = a.get_text(" ", strip=True).lower()
        blob = (href + " " + label).lower()
        if any(x in blob for x in ["drive.google.com", "download", ".ipa", "googleusercontent"]):
            candidates.append(href)
    for href in candidates:
        if "drive.google.com" in href or ".ipa" in href.lower() or "googleusercontent" in href:
            return drive_direct(href)
    # Fall back to any URL containing an IPA-like path.
    for href in candidates:
        return drive_direct(href)
    return None

def main():
    r = session.get(APP_PAGE, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    version = find_version(text)
    if not version:
        raise RuntimeError("Could not find a Reddit version on Moe's app page.")

    download = find_download(soup)
    if not download:
        raise RuntimeError(
            "Could not find the IPA/Google Drive download link. "
            "The site may have changed its HTML or may require JavaScript."
        )

    data = {
        "name": "Moe's Reddit",
        "identifier": "moe.reddit.source",
        "subtitle": "Moe's Reddit SideStore source",
        "description": "Auto-updating source for Moe's Reddit.",
        "iconURL": "https://moe.mohkg1017.pro/favicon.ico",
        "apps": [{
            "name": "Moe's Reddit",
            "bundleIdentifier": BUNDLE_ID,
            "developerName": "Moe / mohkg1017",
            "subtitle": "Patched Reddit",
            "localizedDescription": f"Moe's patched Reddit build {version}.",
            "iconURL": "https://moe.mohkg1017.pro/favicon.ico",
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

    print(f"Updated {OUT}: {version}")
    print(download)

if __name__ == "__main__":
    main()
