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

    raise HTTPException(500, "Unable to load url google serp")


def parse_serp_for_links(page: str) -> list[str]:
    """Parses the serp page and return a list of urls"""

    soup = BeautifulSoup(page, "html.parser")

    anchors = soup.select("a[jsname=UWckNb]")
    print("Num Links found: ", len(anchors))

    links = [a.get("href") for a in anchors]

    if not links:
        raise HTTPException(500, "No valid links found")

    return links


def handle_getting_serp(query: str) -> list[str]:
    """
    Main entrypoint for getting page links from serp
    """

    serp = get_serp(query)
    links = parse_serp_for_links(serp)

    return links


if __name__ == "__main__":
    handle_getting_serp("How to install fast api")
