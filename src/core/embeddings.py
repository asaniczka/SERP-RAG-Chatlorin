"""This module contains all function related to embeddings"""

# pylint: disable = wrong-import-position

import sys
import os

sys.path.append(os.getcwd())

import random

import chromadb
from chromadb.api.models.Collection import Collection


from src.core.parse_html import split_at_h2, handle_convert_html_to_md


def rand_id_generator(make_str: bool = True) -> int:
    """
    Returns a random id.

    Parameters:
        make_str (bool): If True, the random id will be returned as a string.
                         If False, the random id will be returned as an integer.

    Returns:
        int or str: The random id generated.
    """

    rand_id = random.choice(range(100000, 999999999999999))

    if make_str:
        return str(rand_id)
    return rand_id


def create_collection() -> tuple[chromadb.Client, Collection]:
    """Creates a chromadb collection and returns it

    Returns:
        Collection: The created chromadb collection.
    """

    client = chromadb.Client()
    collection = client.get_or_create_collection("serp_webpages")

    return client, collection


def delete_embeddings(collection: Collection):
    """Delets all embeddings within the collection"""

    collection.delete(where={"source": "serp"})


def add_embeddings(
    chunks: list[str],
    collection: Collection,
):
    """Adds the given page chunks to the vector database.

    Args:
        chunks (list[str]): A list of page chunks to be added.
        collection (Collection): The vector database collection.

    Returns:
        None
    """

    collection.add(
        ids=[rand_id_generator() for _ in chunks],
        documents=chunks,
        metadatas=[{"source": "serp"} for _ in chunks],
    )


def get_embeddings(
    user_query: str,
    collection: Collection,
    num_results: int = 3,
) -> list[str]:
    """Retrieves embeddings from vector database.

    Args:
        user_query (str): The user query for which embeddings are retrieved.
        collection (Collection): The vector database collection.
        num_results (int, optional): The number of results to retrieve. Defaults to 3.

    Returns:
        list[str]: A list of retrieved embeddings.

    """
    results = collection.query(
        query_texts=[user_query],
        n_results=num_results,
    )

    return results["documents"][0]


def test_load_data() -> list[str]:
    """
    Load data from an HTML file, convert it to Markdown format, and split it at h2 tags.

    This is used for testing

    Returns:
        A list of strings representing the data split at h2 tags.
    """
    with open(
        "resources/core/get_pages/html_pages/2.html", "r", encoding="utf-8"
    ) as rf:
        html_content = rf.read()
    data = handle_convert_html_to_md(html_content)

    data = split_at_h2(data)

    return data


if __name__ == "__main__":

    chunks = test_load_data()
    collection = create_collection()
    add_embeddings(chunks, collection)
    rag = get_embeddings("Apple 3 or apple 2", collection)
    print(len(rag))
