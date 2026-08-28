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
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/18.0 Mobile/15E148 Safari/604.1"
    )
})


def extract_drive_id(url):
    url = unquote(url.strip())

    for pattern in (
        r"/file/d/([A-Za-z0-9_-]{20,})",
        r"[?&]id=([A-Za-z0-9_-]{20,})",
    ):
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def get_file_size(url):
    try:
        response = session.head(
            url,
            allow_redirects=True,
            timeout=30
        )

        value = response.headers.get("Content-Length")

        if value and value.isdigit():
            return int(value)

    except requests.RequestException:
        pass

    try:
        response = session.get(
            url,
            headers={"Range": "bytes=0-0"},
            allow_redirects=True,
            stream=True,
            timeout=30
        )

        content_range = response.headers.get(
            "Content-Range",
            ""
        )

        match = re.search(
            r"/(\d+)$",
            content_range
        )

        if match:
            response.close()
            return int(match.group(1))

        value = response.headers.get(
            "Content-Length"
        )

        if value and value.isdigit():
            response.close()
            return int(value)

        response.close()

    except requests.RequestException:
        pass

    raise RuntimeError(
        "Could not determine IPA file size."
    )


def main():

    response = session.get(
        APP_PAGE,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    text = soup.get_text(
        " ",
        strip=True
    )

    versions = re.findall(
        r"Reddit\s+(\d{4}\.\d+\.\d+)",
        text,
        re.IGNORECASE
    )

    if not versions:
        raise RuntimeError(
            "Could not find Reddit version."
        )

    version = versions[0]

    download_url = None

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = unquote(
            link["href"].strip()
        )

        label = link.get_text(
            " ",
            strip=True
        ).lower()

        if "drive.google.com" in href:

            download_url = href

            if "download ipa" in label:
                break

    if not download_url:
        raise RuntimeError(
            "Could not find Google Drive IPA link."
        )

    file_id = extract_drive_id(
        download_url
    )

    if not file_id:
        raise RuntimeError(
            "Could not extract Google Drive ID."
        )

    direct_url = (
        f"https://drive.google.com/uc?"
        f"id={file_id}&export=download"
    )

    size = get_file_size(
        direct_url
    )

    data = {

        "name": "Moe's Reddit",

        "identifier": "moe.reddit.source",

        "subtitle": "Moe's Reddit SideStore source",

        "description":
            "Automatically tracked Moe's Reddit source.",

        "apps": [

            {

                "name": "Moe's Reddit",

                "bundleIdentifier":
                    BUNDLE_ID,

                "developerName":
                    "Moe / mohkg1017",

                "subtitle":
                    "Patched Reddit",

                "iconURL":
                    ICON_URL,

                "localizedDescription":
                    f"Moe's Reddit {version}.",

                "versions": [

                    {

                        "version":
                            version,

                        "date":
                            datetime.now(
                                timezone.utc
                            ).isoformat()
                            .replace(
                                "+00:00",
                                "Z"
                            ),

                        "downloadURL":
                            direct_url,

                        "size":
                            size

                    }

                ]

            }

        ]

    }

    with open(
        OUT,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")

    print(
        f"Found Moe's Reddit {version}"
    )

    print(
        f"Google Drive ID: {file_id}"
    )

    print(
        f"IPA size: {size} bytes"
    )


if __name__ == "__main__":
    main()
