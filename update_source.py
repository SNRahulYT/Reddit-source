import json
import re
from datetime import datetime, timezone
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

APP_PAGE = "https://moe.mohkg1017.pro/app/app_1769231115_3988"
OUT = "moe-reddit.json"
BUNDLE_ID = "com.reddit.Reddit"

# Reddit icon
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


def get_file_size(url):
    """
    Get the real IPA size without downloading the entire IPA.

    Google Drive can return Content-Length: 0 on HEAD requests,
    so zero is never accepted.
    """

    # First try a ranged GET.
    try:
        response = session.get(
            url,
            headers={
                "Range": "bytes=0-0"
            },
            allow_redirects=True,
            stream=True,
            timeout=60
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
            size = int(match.group(1))

            if size > 0:
                response.close()
                return size

        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            size = int(content_length)

            if size > 0:
                response.close()
                return size

        response.close()

    except requests.RequestException:
        pass

    # Second attempt: HEAD.
    try:
        response = session.head(
            url,
            allow_redirects=True,
            timeout=60
        )

        content_length = response.headers.get(
            "Content-Length"
        )

        if content_length:
            size = int(content_length)

            if size > 0:
                return size

    except requests.RequestException:
        pass

    raise RuntimeError(
        "Google Drive did not provide a valid IPA size."
    )


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

    # Find Reddit version.
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

    # Find Google Drive download link.
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

    print(
        f"Google Drive ID: {file_id}"
    )

    # Get actual IPA size.
    size = get_file_size(
        direct_url
    )

    print(
        f"IPA size: {size} bytes"
    )

    if size <= 0:
        raise RuntimeError(
            "Invalid IPA size returned."
        )

    data = {

        "name": "Moe's Reddit",

        "identifier": "moe.reddit.source",

        "subtitle":
            "Moe's Reddit SideStore source",

        "description":
            "Automatically tracked Moe's Reddit source.",

        "apps": [

            {

                "name":
                    "Moe's Reddit",

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
    )


if __name__ == "__main__":
    main()
