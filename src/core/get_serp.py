"""Module contains all functions for gettings serp results from google"""

from typing import Any
from urllib import parse

import requests
from fastapi import HTTPException
from bs4 import BeautifulSoup


def get_serp(query: str) -> str:
    """gets the serps"""

    base_url = "https://www.google.com/search?channel=fs&client=ubuntu-sn&q="
    quote_query = parse.quote(query)

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.7,en-US;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    response = requests.get(base_url + quote_query, headers=headers, timeout=5)

    if response.status_code == 200:
        return response.text

    return None


def parse_serp_for_links(page: str) -> list[str]:
    """
    Parses the serp page and returns a list of URLs.

    Args:
        page (str): The HTML content of the SERP page.

    Returns:
        list[str]: A list of URLs extracted from the SERP page.

    Raises:
        HTTPException: If no valid links are found on the SERP page.
    """

    soup = BeautifulSoup(page, "html.parser")

    anchors = soup.select("a[jsname=UWckNb]")

    links = [a.get("href") for a in anchors]

    if not links:
        raise HTTPException(500, "No valid links found")

    return links


def handle_getting_serp(query: str) -> list[str] | None:
    """
    Main entrypoint for getting page links from serp

    Args:
        query (str): The search query to retrieve the SERP for.

    Returns:
        list[str]: A list of page links extracted from the SERP.
    """

    serp = get_serp(query)
    if not serp:
        return None

    links = parse_serp_for_links(serp)

    return links


if __name__ == "__main__":
    handle_getting_serp("How to install fast api")
