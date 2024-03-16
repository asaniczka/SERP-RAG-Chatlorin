"""
This module contains all functions responsible for load pages and getting their source html.

All functions are async since speed is the primary focus here
"""

from typing import Any
import asyncio

import httpx
from playwright.async_api import async_playwright
from playwright._impl._browser import Browser
from playwright.async_api._generated import Playwright
from fastapi import HTTPException


# -----------------------------------------------------
#                       WORKERS
# -----------------------------------------------------


async def load_pw_browser(headless: bool = True) -> tuple[Playwright, Browser]:
    """Loads the Playwright browser.

    Args:
        headless (bool, optional): Whether to run the browser in headless mode. Defaults to True.
        timeout (int, optional): The maximum time in milliseconds to wait for the browser to launch. Defaults to 10000.

    Returns:
        tuple[Playwright, Browser]: A tuple containing the Playwright instance and the launched browser.
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless, timeout=10000)

    return (playwright, browser)


async def close_pw_browser(playwright: Playwright, browser: Browser):
    """Closes the playwright browser.

    Args:
        playwright (Playwright): The Playwright instance.
        browser (Browser): The browser instance to be closed.
    """
    await browser.close()
    await playwright.stop()


async def load_pages_with_httpx(
    link: str,
    client: httpx.AsyncClient,
) -> tuple[str, str] | None:
    """Function loads the given links using httpx.

    Args:
        link (str): The URL of the page to load.
        client (httpx.AsyncClient): The httpx client to use for making the request.

    Returns:
        tuple[str, str] | None: A tuple containing the link and page source if successful,
        otherwise None.
    """

    response = await client.get(link)

    if response.status_code == 200:

        # if the page contains more than 50K characters, return it
        # Else, mark it as page needs js rendering
        if len(response.text) >= 50000:
            return link, response.text

        return None

    return None


async def load_pages_with_playwright(
    link: str,
    browser: Browser,
    timeout=8000,
) -> str | None:
    """
    Loads the page and extracts the page source using playwright.

    Args:
        link (str): The URL of the page to load.
        browser (Browser): The playwright browser instance.
        timeout (int, optional): The maximum time to wait for the page to load, in milliseconds. Defaults to 8000.

    Returns:
        str | None: The page source if successful, else None.
    """

    try:
        page = await browser.new_page()
        page.set_default_timeout(timeout=timeout)
        await page.goto(link)

        page_source = await page.content()

        return page_source
    except Exception as e:
        print(f"Error when loading page: {e}")
        return None


# -----------------------------------------------------
#                       HANDLERS
# -----------------------------------------------------


async def handle_loading_pages_fast(links: list[str]) -> tuple[set[str], list[str]]:
    """Handles loading pages with get requests.

    Args:
        links (list): A list of URLs to load.

    Returns:
        A tuple containing two elements:
        - urls_left_to_process (set): A set of URLs that were not successfully loaded.
        - page_sources (list): A list of page sources for the successfully loaded URLs.
    """

    print(f"Loading {len(links)} pages with Fast")

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.7,en-US;q=0.3",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
        "TE": "trailers",
    }

    input_links: set[str] = set(links)
    client = httpx.AsyncClient(headers=headers, timeout=3, follow_redirects=True)

    url_tasks = []
    for link in input_links:
        url_tasks.append(load_pages_with_httpx(link, client))

    data = await asyncio.gather(*url_tasks)

    processed_urls: set[str] = set()
    page_sources = []
    for item in data:
        if item:
            url, page_source = item
            page_sources.append(page_source)
            processed_urls.add(url)

    urls_left_to_process = input_links.difference(processed_urls)

    return urls_left_to_process, page_sources


async def handle_loading_pages_slow(links: list[str]) -> list[str]:
    """Handles getting page sources of the given links using playwright.

    Args:
        links (list[str]): A list of links to load page sources from.

    Returns:
        list[str]: A list of page sources corresponding to the given links.
    """

    print(f"Loading {len(links)} pages with Slow")

    pw, browser = await load_pw_browser(headless=False)

    url_tasks = []
    for link in links:
        url_tasks.append(load_pages_with_playwright(link, browser))

    data = await asyncio.gather(*url_tasks)

    await close_pw_browser(pw, browser)

    page_sources = []
    for item in data:
        if item:
            page_sources.append(item)

    return page_sources


async def handle_loading_page_sources(links: list) -> list[str]:
    """
    Function that handles getting page sources of the given URLs using multiple methods.

    Args:
        links (list): A list of URLs to retrieve page sources from.

    Returns:
        list[str]: A list of page sources.
    """

    if not links:
        raise HTTPException(500, "We need links to get pages")

    urls_left_to_process, page_sources = await handle_loading_pages_fast(links)

    # Return pages if no links are left to process
    if not urls_left_to_process:
        return page_sources

    # Return pages if we got data of 80% of the links
    if len(urls_left_to_process) / len(links) >= 0.8:
        return page_sources

    # Retry the remaining URLs with playwright
    remaining_page_sources = await handle_loading_pages_slow(list(urls_left_to_process))
    page_sources.extend(remaining_page_sources)

    return page_sources


async def testing():
    """
    This function is used for testing purposes.
    """

    page_sources = await handle_loading_page_sources(
        [
            "https://www.soundguys.com/apple-airpods-review-11072/",
            "https://www.cnet.com/tech/mobile/apple-airpods-pro-2-review-better-battery-life-and-improved-sound/",
            "https://www.rtings.com/headphones/reviews/apple/airpods-2nd-generation-truly-wireless",
        ]
    )

    for idx, page in enumerate(page_sources):
        with open(
            f"resources/core/get_pages/html_pages/{idx}.html", "w", encoding="utf-8"
        ) as wf:
            wf.write(page)


if __name__ == "__main__":
    asyncio.run(testing())
