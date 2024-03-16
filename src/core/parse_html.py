"""This module is responsible for parsing the html content and splitting it into chunks"""

import re

from markdownify import markdownify as md
from bs4 import BeautifulSoup

# -----------------------------------------------
#                   WORKERS
# -----------------------------------------------


def remove_tags(page: str) -> str:
    """Removes useless tags from the page source

    Args:
        page (str): The HTML source code of the page.

    Returns:
        str: The modified HTML source code with the specified tags removed.
    """

    tags_to_remove = ["footer", "script", "style", "meta"]

    soup = BeautifulSoup(page, "html.parser")

    for tag in tags_to_remove:
        queued_tags = soup.select(tag)
        for qtag in queued_tags:
            qtag.extract()

    return soup.prettify()


def remove_spaces(
    markdown_content: str,
    split_at="\n\n",
    check_valid_line=True,
) -> str:
    """Removes unwanted spaces from the given markdown content.

    Args:
        markdown_content (str): The markdown content to remove spaces from.
        split_at (str, optional): The delimiter to split the markdown content into lines. Defaults to "\n\n".
        check_valid_line (bool, optional): Flag indicating whether to check for valid lines. Defaults to True.

    Returns:
        str: The markdown content with unwanted spaces removed.
    """
    lines = markdown_content.split(split_at)
    lines = [line.strip().replace("\r", "") for line in lines]

    if check_valid_line:
        trimmed_md = split_at.join([line for line in lines if line])
    else:
        trimmed_md = split_at.join([line for line in lines])

    return trimmed_md


def format_headings(markdown_content: str) -> str:
    """Put the heading text in the same line as a marker

    Args:
        markdown_content (str): The markdown content to format.

    Returns:
        str: The formatted markdown content.
    """
    lines = markdown_content.split("\n")

    formatted_lines = []
    for idx, line in enumerate(lines):
        if line.startswith("#") and len(line) < 5:
            full_heading = line.strip() + " " + lines.pop(idx + 1).strip()
            formatted_lines.append(full_heading)
        else:
            formatted_lines.append(line)

    formatted_md = "\n".join([line for line in formatted_lines])

    return formatted_md


def remove_links(markdown_content: str) -> str:
    """
    Removes links and images from the given markdown content.

    Args:
        markdown_content (str): The markdown content to remove links and images from.

    Returns:
        str: The markdown content with links and images removed.
    """

    # remove images
    links_to_remove = re.findall(r"(!\[.*\]\(*.*\))", markdown_content)
    links_to_remove.extend(re.findall(r"(!\[\n.*\]\(*.*\))", markdown_content))
    for link in links_to_remove:
        markdown_content = markdown_content.replace(link, "")

    # remove links
    links_to_remove = re.findall(r"((?:])\(.*\))", markdown_content)
    for link in links_to_remove:
        markdown_content = markdown_content.replace(link, "")

    markdown_content = markdown_content.replace("[", "")
    markdown_content = remove_spaces(
        markdown_content, split_at="\n", check_valid_line=False
    )
    return markdown_content


def remove_everything_before_h1(markdown_content: str) -> str:
    """Remove everything before the first h1 heading in the markdown content.

    Args:
        markdown_content (str): The input markdown content.

    Returns:
        str: The markdown content with everything before the first h1 heading removed.
    """

    finds = re.findall(r"(\n#\s)", markdown_content)

    if not finds:
        return markdown_content

    h1_location = markdown_content.index(finds[0])
    markdown_content = markdown_content[h1_location:]

    return markdown_content


def split_at_h2(page: str) -> list[str]:
    """Splits the content into h2 chunks where each chunk will contain a single h2"""

    splits = page.split("\n## ")
    for idx, split in enumerate(splits):
        if idx == 0:
            continue
        splits[idx] = "## " + split

    return splits


# -----------------------------------------------
#                   HANDLERS
# -----------------------------------------------
def handle_clean_markdown(markdown_content: str) -> str:
    """Cleans up markdown content by removing links.

    Args:
        markdown_content (str): The markdown content to be cleaned.

    Returns:
        str: The cleaned markdown content.
    """

    markdown_content = remove_spaces(markdown_content)
    markdown_content = format_headings(markdown_content)
    markdown_content = remove_links(markdown_content)
    markdown_content = remove_spaces(markdown_content)
    markdown_content = remove_everything_before_h1(markdown_content)

    return markdown_content


def handle_convert_html_to_md(page: str) -> str:
    """Converts HTML to Markdown.

    Args:
        page (str): The HTML content to be converted.

    Returns:
        str: The converted Markdown content.
    """

    clean_page = remove_tags(page)
    markdown_content = md(
        clean_page,
        heading_style="ATX",
        bullets="-",
        newline_style="BACKSLASH",
    )
    cleaned_content = handle_clean_markdown(markdown_content)

    return cleaned_content


if __name__ == "__main__":
    with open(
        "resources/core/get_pages/html_pages/2.html", "r", encoding="utf-8"
    ) as rf:
        html_content = rf.read()
    data = handle_convert_html_to_md(html_content)

    with open("test.md", "w", encoding="utf-8") as wf:
        wf.write(data)

    split_at_h2(data)
