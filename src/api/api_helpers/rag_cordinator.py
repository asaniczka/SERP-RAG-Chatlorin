"""
This helper contains functions related to finding keywords, polling google, extracting pages, and converting them in to embeddings
"""

# pylint: disable = wrong-import-position
# pylint: disable = wrong-import-order

import os
import sys
import dotenv

sys.path.append(os.getcwd())
dotenv.load_dotenv()

import asyncio
import json
import concurrent.futures

from rich import print
from fastapi.exceptions import HTTPException

from src.core.get_serp import handle_getting_serp
from src.core.get_pages import handle_loading_page_sources
from src.core.parse_html import handle_convert_html_to_md, split_at_h2
from src.core.embeddings import (
    create_collection,
    add_embeddings,
    get_embeddings,
    delete_embeddings,
)
from src.core.gemini import handle_generating_response

from src.models.messages import BaseMessageLog, BaseMessage
from src.models.models_gemini import GeminiKeywords


def count_rag_text_words(rag_texts: list[str]):
    """
    Counts how many words are in rag texts.
    If there's more than 20,000, remove the rest

    Args:
        rag_texts (list[str]): A list of rag texts.

    Returns:
        list[str]: The modified rag_texts list with words removed if the total word count exceeds 20,000.
    """

    total_words = 0

    for idx, context in enumerate(rag_texts):
        splits = context.split()
        total_words += len(splits)

        if total_words >= 20_000:
            rag_texts = rag_texts[:idx]
            break

    print(f"Rag Texts have {total_words} words")
    return rag_texts


def construct_rag_message(rag_texts: list[str]) -> BaseMessage:
    """Puts all rag messages into 1 message.

    Args:
        rag_texts (list[str]): A list of rag messages.

    Returns:
        BaseMessage: The constructed rag message.

    """
    rag_message = "Here are some snippets extracted from web pages related to the query. Try to ignore information that is not relevant to the task at hand Use the information in these snippets to answer the user.:\n\n"

    for idx, rag in enumerate(rag_texts, start=1):
        prefix = f"- Relevant web search context {idx}:\n"

        rag_message = rag_message + prefix + rag + "\n\n"

    return BaseMessage(role="rag", content=rag_message)


def get_system_message() -> BaseMessage:
    """
    Returns the system message to primt the LLM
    """

    system_message = "You are an helpful assistant. Your task is to try your absolutely best to answer the user. The system will try to provide you with helpful google search results. Look throught them and try to find something to answer the user"

    return BaseMessage(role="system", content=system_message)


def get_seeds_serp_keywords(messages: BaseMessageLog) -> GeminiKeywords:
    """Sends the original query to Gemini to generate SERP keywords.

    Args:
        messages (BaseMessageLog): The conversation messages.

    Returns:
        GeminiKeywords: The generated SERP keywords.

    Raises:
        HTTPException: If unable to get seed keywords after 5 retries.
    """

    prompt = """You are a helpful search assistant.
    
    Your task is to look at the conversation and suggest 2-5 different search phrases
    that the user should search on Google to find the answer to their questions.

    Search keywords should be short and make sense.
    
    You should only reply with the search keywords in the JSON format below:
    
    {
        "keywords": list[str]
    }
    """
    system_message = BaseMessage(role="system", content=prompt)
    loc_messages = messages.model_copy(deep=True)
    loc_messages.messages.insert(0, system_message)

    # Change all roles to user or Gemini thinks it should follow a few shot prompt
    for idx, message in enumerate(loc_messages.messages):
        loc_messages.messages[idx].role = "user"

    retries = 0
    while retries < 5:
        try:
            reply = handle_generating_response(loc_messages)
            reply = reply.replace("```json", "").strip("`")
            keywords = GeminiKeywords(**json.loads(reply))
            return keywords
        except Exception as e:
            print(reply)
            print(f"Error generating keywords: {e}")
            retries += 1
            continue

    raise HTTPException(500, "Unable to get seed keywords")


def get_all_serp_pages(keywords: GeminiKeywords) -> list[str]:
    """
    Calls get serp for all the keywords simultaneously.

    Args:
        keywords (GeminiKeywords): An instance of the GeminiKeywords class containing the keywords.

    Returns:
        list[str]: A list of links retrieved from the SERP (Search Engine Results Page) for all the keywords.
    """

    links = []

    with concurrent.futures.ThreadPoolExecutor() as thread_executor:
        futures = []
        for keyword in keywords.keywords:
            future = thread_executor.submit(handle_getting_serp, keyword)
            futures.append(future)

        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                links.extend(result)

    return links


def handle_reply_generation(messages: BaseMessageLog) -> str:
    """
    ### Responsibility:
    - Generate response using AI via RAG
    - Serve as the main coordinator for handling response generation from the API

    ### Args:
       - `messages`: An object of BaseMessageLog containing message logs for generating response

    ### Returns:
     - `str` : Returns the generated response as a string

    ### How does the function work:
     - Extract the query from the last message in the message log
     - Get search engine result page links related to the query
     - Load page sources asynchronously
     - Convert the HTML content of pages to Markdown format
     - Split the Markdown content at heading level 2 (h2) tags
     - Create a collection for storing embeddings
     - Add embeddings of the h2 chunks to the collection
     - Retrieve texts related to query embeddings from collection
     - Construct a response message using the retrieved texts
     - Insert the generated response as a message in the log
     - Generate the final response using the message log
     - Return the generated response
    """

    keywords = get_seeds_serp_keywords(messages)
    print(f"Got {len(keywords.keywords)} keywords for query")
    links = get_all_serp_pages(keywords)
    print(f"Got {len(links)} links for query")
    pages_html = asyncio.run(handle_loading_page_sources(links))

    pages_md = []
    for page in pages_html:
        page_md = handle_convert_html_to_md(page)
        pages_md.append(page_md)

    h2_chunks: list[str] = []
    for page in pages_md:
        chunks = split_at_h2(page)
        h2_chunks.extend(chunks)

    client, collection = create_collection()
    add_embeddings(h2_chunks, collection)

    query = messages.messages[-1].content
    rag_texts = get_embeddings(query, collection, num_results=20)
    rag_texts = count_rag_text_words(rag_texts)
    messages.messages.insert(1, construct_rag_message(rag_texts))
    messages.messages.insert(0, get_system_message())

    reply = handle_generating_response(messages)
    delete_embeddings(collection)

    return reply


if __name__ == "__main__":

    msg_log = BaseMessageLog(
        messages=[
            BaseMessage(
                role="user",
                content="How to allow users to pass in arbitary fields to a pydantic model class?",
            )
        ]
    )
    reply = handle_reply_generation(msg_log)
    print(reply)
