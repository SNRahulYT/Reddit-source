import json
import re
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

APP_PAGE = "https://moe.mohkg1017.pro/app/app_1769231115_3988"
OUT = "moe-reddit.json"
BUNDLE_ID = "com.reddit.Reddit"
ICON_URL = "https://moe.mohkg1017.pro/favicon.ico"

session = requests.Session()
session.headers.update({
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
        "AppleWebKit/605.1.15"
    )
})


def drive_id(url):
    url = unquote(url.strip())

    patterns = [
        r"/file/d/([A-Za-z0-9_-]{20,})",
        r"[?&]id=([A-Za-z0-9_-]{20,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def main():
    response = session.get(APP_PAGE, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(" ", strip=True)

    # Find Reddit version
    matches = re.findall(
        r"Reddit\s+(\d{4}\.\d+\.\d+)",
        text,
        re.IGNORECASE
    )

    if not matches:
        raise RuntimeError(
            "Could not find Reddit version on Moe's app page."
        )

    version = matches[0]

    # Find Google Drive download link
    download_url = None

    for link in soup.find_all("a", href=True):
        href = unquote(link["href"].strip())
        label = link.get_text(" ", strip=True).lower()

        if (
            "download ipa" in label
            or "drive.google.com" in href
        ):
            if "drive.google.com" in href:
                download_url = href
                break

    if not download_url:
        raise RuntimeError(
            "Could not find Reddit Download IPA / Google Drive link."
        )

    file_id = drive_id(download_url)

    if not file_id:
        raise RuntimeError(
            f"Could not extract Google Drive ID from: {download_url}"
        )

    direct_url = (
        f"https://drive.google.com/uc?"
        f"id={file_id}&export=download"
    )

    data = {
        "name": "Moe's Reddit",
        "identifier": "moe.reddit.source",
        "subtitle": "Moe's Reddit SideStore source",
        "description": "Automatically tracked Moe's Reddit source.",
        "apps": [
            {
                "name": "Moe's Reddit",
                "bundleIdentifier": BUNDLE_ID,
                "developerName": "Moe / mohkg1017",
                "subtitle": "Patched Reddit",
                "iconURL": ICON_URL,
                "localizedDescription": (
                    f"Moe's Reddit {version}."
                ),
                "versions": [
                    {
                        "version": version,
                        "date": datetime.now(
                            timezone.utc
                        ).isoformat().replace("+00:00", "Z"),
                        "downloadURL": direct_url
                    }
                ]
            }
        ]
    }

    with open(OUT, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )
        file.write("\n")

    print(f"Found Moe's Reddit {version}")
    print(f"Google Drive ID: {file_id}")
    print(f"Updated {OUT}")


if __name__ == "__main__":
    main()
