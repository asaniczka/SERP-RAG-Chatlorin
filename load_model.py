"""This module is to be run by docker build so that chromadb will download the default embeddings model"""

import chromadb

client = chromadb.Client()
collection = client.create_collection("load")
collection.add(ids=["1"], documents=["hello"])
