import json
import re
import os
import tempfile
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

APP_PAGE = "https://moe.mohkg1017.pro/app/app_1769231115_3988"
OUT = "moe-reddit.json"
BUNDLE_ID = "com.reddit.Reddit"

ICON_URL = (
    "https://redditinc.com/hs-fs/hubfs/Reddit%20Inc/"
    "Content/Brand%20Page/Reddit_Logo.png"
    "?height=400&name=Reddit_Logo.png&width=400"
)

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

    patterns = [
        r"/file/d/([A-Za-z0-9_-]{20,})",
        r"[?&]id=([A-Za-z0-9_-]{20,})",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)

        if match:
            return match.group(1)

    return None


def download_and_measure(file_id):

    url = (
        "https://drive.usercontent.google.com/download"
        f"?id={file_id}"
        "&export=download"
        "&confirm=t"
    )

    temp_file = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".ipa"
    )

    temp_path = temp_file.name
    temp_file.close()

    try:

        print("Downloading IPA temporarily...")

        response = session.get(
            url,
            allow_redirects=True,
            stream=True,
            timeout=180
        )

        response.raise_for_status()

        total = 0

        with open(temp_path, "wb") as file:

            for chunk in response.iter_content(
                chunk_size=1024 * 1024
            ):

                if chunk:
                    file.write(chunk)
                    total += len(chunk)

        response.close()

        print(
            f"Downloaded {total} bytes"
        )

        if total < 10 * 1024 * 1024:

            raise RuntimeError(
                f"Google Drive returned only {total} bytes "
                "instead of the IPA."
            )

        with open(
            temp_path,
            "rb"
        ) as file:

            signature = file.read(4)

        if signature not in (
            b"PK\x03\x04",
            b"PK\x05\x06",
            b"PK\x07\x08"
        ):

            raise RuntimeError(
                "Downloaded file is not a valid ZIP/IPA."
            )

        return total

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)


def main():

    print("Checking Moe's Reddit page...")

    response = session.get(
        APP_PAGE,
        timeout=60
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

    print(
        f"Found Reddit version: {version}"
    )

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
            "Could not extract Google Drive file ID."
        )

    print(
        f"Google Drive ID: {file_id}"
    )

    size = download_and_measure(
        file_id
    )

    print(
        f"REAL IPA SIZE: {size} bytes"
    )

    direct_url = (
        "https://drive.usercontent.google.com/download"
        f"?id={file_id}"
        "&export=download"
        "&confirm=t"
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
        "Successfully updated moe-reddit.json"


if __name__ == "__main__":
    main()
