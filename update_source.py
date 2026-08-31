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

SOURCE_URL = (
    "https://raw.githubusercontent.com/"
    "SNRahulYT/Reddit-source/main/moe-reddit.json"
)

WEBSITE_URL = "https://moe.mohkg1017.pro/"

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


def extract_reddit_version(text):
    matches = re.findall(
        r"Reddit\s+(\d{4}\.\d+\.\d+)",
        text,
        re.IGNORECASE
    )

    if not matches:
        raise RuntimeError(
            "Could not find Reddit version on Moe's page."
        )

    return matches[0]


def extract_moe_version(text):
    patterns = [
        r"Moe\s*(?:Version|Ver\.?|v)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)+)",
        r"Moe\s+(\d+\.\d+(?:\.\d+)?)",
        r"Version\s*[:\-]?\s*Moe\s*([0-9]+(?:\.[0-9]+)+)",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return match.group(1)

    return None


def extract_release_date(text):
    patterns = [
        r"(?:Last\s+Modified|Modified|Updated|Release(?:d)?|Published)"
        r"\s*[:\-]?\s*"
        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",

        r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})"
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            raw_date = match.group(1)

            raw_date = raw_date.replace(
                "/",
                "-"
            )

            try:
                parsed = datetime.strptime(
                    raw_date,
                    "%Y-%m-%d"
                )

                return (
                    parsed.replace(
                        tzinfo=timezone.utc
                    )
                    .isoformat()
                    .replace(
                        "+00:00",
                        "Z"
                    )
                )

            except ValueError:
                pass

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

        with open(
            temp_path,
            "wb"
        ) as file:

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

    print(
        "Checking Moe's Reddit page..."
    )

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

    # ---------------------------------------------------------
    # Reddit version
    # ---------------------------------------------------------

    version = extract_reddit_version(
        text
    )

    print(
        f"Reddit version: {version}"
    )

    # ---------------------------------------------------------
    # Moe version
    # ---------------------------------------------------------

    moe_version = extract_moe_version(
        text
    )

    if moe_version:
        print(
            f"Moe version: {moe_version}"
        )
    else:
        print(
            "Moe version not found on page."
        )

    # ---------------------------------------------------------
    # Release date
    # ---------------------------------------------------------

    release_date = extract_release_date(
        text
    )

    if release_date:
        print(
            f"Release date found: {release_date}"
        )
    else:
        print(
            "Release date not found; using current date."
        )

        release_date = (
            datetime.now(
                timezone.utc
            )
            .isoformat()
            .replace(
                "+00:00",
                "Z"
            )
        )

    # ---------------------------------------------------------
    # Google Drive download link
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Real IPA size
    # ---------------------------------------------------------

    size = download_and_measure(
        file_id
    )

    print(
        f"REAL IPA SIZE: {size} bytes"
    )

    # ---------------------------------------------------------
    # Direct download URL
    # ---------------------------------------------------------

    direct_url = (
        "https://drive.usercontent.google.com/download"
        f"?id={file_id}"
        "&export=download"
        "&confirm=t"
    )

    # ---------------------------------------------------------
    # Version description
    # ---------------------------------------------------------

    if moe_version:

        version_description = (
            f"Moe Version {moe_version} • "
            f"Reddit Version {version}"
        )

    else:

        version_description = (
            f"Reddit Version {version}"
        )

    # ---------------------------------------------------------
    # About description
    # ---------------------------------------------------------

    if moe_version:

        about_description = (
            f"Moe's Reddit • "
            f"Moe Version {moe_version} • "
            f"Reddit Version {version}"
        )

    else:

        about_description = (
            f"Moe's Reddit • "
            f"Reddit Version {version}"
        )

    # ---------------------------------------------------------
    # SideStore source
    # ---------------------------------------------------------

    data = {

        "name":
            "Moe's Reddit",

        "identifier":
            "moe.reddit.source",

        "apiVersion":
            "v2",

        "subtitle":
            "Automated Moe's Reddit IPA builds",

        "description":
            about_description,

        "iconURL":
            ICON_URL,

        "website":
            WEBSITE_URL,

        "sourceURL":
            SOURCE_URL,

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

                "category":
                    "social-networking",

                "iconURL":
                    ICON_URL,

                "version":
                    version,

                "versionDate":
                    release_date,

                "versionDescription":
                    version_description,

                "downloadURL":
                    direct_url,

                "size":
                    size,

                "localizedDescription":
                    (
                        "Moe's Reddit is a modified "
                        "Reddit IPA with Moe's patches "
                        "and fixes."
                    ),

                "versions": [

                    {

                        "version":
                            version,

                        "date":
                            release_date,

                        "localizedDescription":
                            version_description,

                        "downloadURL":
                            direct_url,

                        "size":
                            size

                    }

                ]

            }

        ],

        "news":
            []

    }

    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------

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
