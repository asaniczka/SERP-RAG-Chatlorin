"""This helper contains functions to find keywords, poll google, extract pages, and convert them in to embeddings"""

# pylint: disable = wrong-import-position
# pylint: disable = wrong-import-order

import os
import sys
import dotenv

sys.path.append(os.getcwd())
dotenv.load_dotenv()

import asyncio
from rich import print

from src.core.get_serp import handle_getting_serp
from src.core.get_pages import handle_loading_page_sources
from src.core.parse_html import handle_convert_html_to_md, split_at_h2
from src.core.embeddings import create_collection, add_embeddings, get_embeddings
from src.core.gemini import handle_generating_response

from src.models.messages import BaseMessageLog, BaseMessage


def construct_rag_message(rag_texts: list[str]) -> BaseMessage:
    """Puts all rag messages into 1 message"""

    rag_message = "Here are some snippets extracted from web pages related to the query. Use the information in these snippets to answer the user:\n\n"

    for idx, rag in enumerate(rag_texts, start=1):
        prefix = f"- Relevant web search context {idx}:\n"

        rag_message = rag_message + prefix + rag + "\n\n"

    return BaseMessage(role="rag", text=rag_message)


def start(messages: BaseMessageLog) -> str:
    """Init"""

    query = messages.messages[-1].text

    links = handle_getting_serp(query)
    pages_html = asyncio.run(handle_loading_page_sources(links))

    pages_md = []
    for page in pages_html:
        page_md = handle_convert_html_to_md(page)
        pages_md.append(page_md)

    h2_chunks: list[str] = []
    for page in pages_md:
        chunks = split_at_h2(page)
        h2_chunks.extend(chunks)

    collection = create_collection()
    add_embeddings(h2_chunks, collection)

    rag_texts = get_embeddings(query, collection, num_results=10)
    print(rag_texts)
    rag_message = construct_rag_message(rag_texts)

    messages.messages.insert(1, rag_message)

    reply = handle_generating_response(messages)
    return reply


if __name__ == "__main__":

    msg_log = BaseMessageLog(
        messages=[
            BaseMessage(
                role="user",
                text="Who is Asaniczka. What kind of data is available online about him?",
            )
        ]
    )
    reply = start(msg_log)
    print(reply)
