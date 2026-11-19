# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    WebBaseLoader,
    PyPDFLoader,
    TextLoader,
    CSVLoader 
)
from langchain_chroma import Chroma
import httpx

from typing import Any, Dict, List, Tuple, Union
from urllib.parse import urlparse
import os
import time
from pathlib import Path



# Handling which API to use based on public vs NVIDIA internal
# Check if the INTERNAL_API environment variable is set to yes. Don't set if not NVIDIA employee, as you can't access them.
INTERNAL_API = os.getenv('INTERNAL_API', 'no')

# Default model for public embedding
EMBEDDINGS_MODEL = 'nvidia/nemotron-3-embed-1b'
NVIDIA_API_BASE = os.getenv("NVIDIA_API_BASE", "https://integrate.api.nvidia.com/v1")

# Set the chunk size and overlap for the text splitter. Uses defaults but allows them to be set as environment variables.
DEFAULT_CHUNK_SIZE = 250
DEFAULT_CHUNK_OVERLAP = 0

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", DEFAULT_CHUNK_SIZE))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP))

# NVIDIA Workbench mounts projects at /project.  Use this repository's data
# directory by default so the application also runs directly on macOS, Linux,
# and Streamlit Community Cloud.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
PERSIST_DIRECTORY = Path(
    os.getenv("RAG_DATA_DIR", str(PROJECT_ROOT / "data"))
).expanduser()
PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)


class NVIDIAEmbeddings:
    """LangChain-compatible embeddings backed by NVIDIA's OpenAI-compatible API."""

    def __init__(self, model: str = EMBEDDINGS_MODEL):
        self.model = model

    def _embed(self, texts: List[str], input_type: str) -> List[List[float]]:
        response = httpx.post(
            f"{NVIDIA_API_BASE.rstrip('/')}/embeddings",
            headers={
                "Authorization": f"Bearer {os.environ['NVIDIA_API_KEY']}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "input": texts,
                "input_type": input_type,
            },
            timeout=60,
        )
        response.raise_for_status()
        return [item["embedding"] for item in response.json()["data"]]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self._embed(texts, "passage")

    def embed_query(self, text: str) -> List[float]:
        return self._embed([text], "query")[0]


print(f"[config] Using NVIDIA embedding model: {EMBEDDINGS_MODEL}")


# Functions for dealing with URLs
def is_valid_url(url: str) -> bool:
    """ This is a helper function for checking if the URL is valid. It isn't fail proof, but it will catch most common errors. """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def safe_load(url):
    """ This is a helper function for loading the URL. It protects against false negatives from is_value_url and 
        filters for actual web pages. Returns None if it fails.
    """
    try:
        return WebBaseLoader(url).load()
    except Exception as e:
        print(f"[Documents] ⚠ Could not load {url}: {e}")
        return None


def upload(urls: List[str], collection_name: str = "rag-chroma"):
    """ This is a helper function for parsing the user inputted URLs and uploading them into the vector store. """

    urls = [url.strip() for url in urls if url.strip()]
    for url in urls:
        if not is_valid_url(url):
            print(f"[Documents] ⚠ Skipping invalid URL: {url}")
    urls = [url for url in urls if is_valid_url(url)]

    if not urls:
        print("[Documents] ✗ No valid URLs provided — nothing was added to the context.")
        return None

    print(f"[Documents] Adding {len(urls)} webpage(s) to the context...")
    docs = []
    for url in urls:
        result = safe_load(url)
        if result is not None:
            docs.append(result)
            print(f"[Documents] ✓ Loaded {url}")

    docs_list = [item for sublist in docs for item in sublist]

    if not docs_list:
        # If no documents were loaded, return None
        print("[Documents] ✗ None of the webpages could be loaded — nothing was added to the context.")
        return None

    print(f"[Documents] Loaded {len(docs)} of {len(urls)} webpage(s) successfully")

    try:
        doc_splits = split_documents(docs_list)
        return embed_documents(doc_splits, collection_name)

    except Exception as e:
        print(f"[Documents] ✗ Failed to add webpages to the context: {e}")
        return None


# Functions for dealing with file uploads/embeddings

## Helper functions

def load_documents_from_files(file_paths: List[str]) -> List[Any]:
    """Load and return documents from supported file types."""
    docs = []

    for fpath in file_paths:
        ext = os.path.splitext(fpath)[-1].lower()

        loader_cls = {
            ".pdf": PyPDFLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
            ".csv": CSVLoader
        }.get(ext)

        if loader_cls is None:
            print(f"[Documents] ⚠ Skipping unsupported file type: {os.path.basename(fpath)} (supported: .pdf, .txt, .md, .csv)")
            continue

        try:
            loaded = loader_cls(fpath).load()
            docs.append(loaded)
            print(f"[Documents] ✓ Loaded {os.path.basename(fpath)}")
        except Exception as e:
            print(f"[Documents] ✗ Failed to load {os.path.basename(fpath)}: {e}")

    return [item for sublist in docs for item in sublist]


def split_documents(docs: List[Any]):
    """Split documents into smaller chunks using recursive splitter."""
    print(f"[Documents] Splitting {len(docs)} document(s) into chunks of ~{CHUNK_SIZE} tokens ({CHUNK_OVERLAP} token overlap)...")

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    doc_splits = splitter.split_documents(docs)
    print(f"[Documents] Created {len(doc_splits)} chunks")
    return doc_splits

def embed_documents(doc_splits: List[Any], collection_name: str = "rag-chroma"):
    """Embed and store the split documents into Chroma vectorstore."""
    try:
        print(f"[Documents] Embedding {len(doc_splits)} chunks with {EMBEDDINGS_MODEL}...")
        start = time.time()

        vectorstore = Chroma.from_documents(
            documents=doc_splits,
            collection_name=collection_name,
            embedding=NVIDIAEmbeddings(model=EMBEDDINGS_MODEL),
            persist_directory=str(PERSIST_DIRECTORY),
        )
        print(f"[Documents] ✓ Context ready — {len(doc_splits)} chunks stored in the vector database ({time.time() - start:.1f}s)")
        return vectorstore

    except Exception as e:
        print(f"[Documents] ✗ Embedding failed — could not build the context: {e}")
        return None


## Main function that use helper functions 

def upload_files(file_paths: List[str], collection_name: str = "rag-chroma"):
    """Upload files into the vector store pipeline."""

    if not file_paths:
        print("[Documents] ✗ No files provided — nothing was added to the context.")
        return None

    print(f"[Documents] Adding {len(file_paths)} file(s) to the context...")

    try:
        docs_list = load_documents_from_files(file_paths)

        if not docs_list:
            print("[Documents] ✗ None of the files could be loaded — nothing was added to the context.")
            return None

        doc_splits = split_documents(docs_list)
        return embed_documents(doc_splits, collection_name)

    except Exception as e:
        print(f"[Documents] ✗ Failed to add files to the context: {e}")
        return None




def _clear(
    persist_directory: str = str(PERSIST_DIRECTORY),
    collection_name: str = "rag-chroma",
):
    """Clear one Chroma collection without touching other users' data."""
    try:
        print("[Documents] Clearing the context...")

        # Clear the collection via Chroma client
        vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=NVIDIAEmbeddings(model=EMBEDDINGS_MODEL),
            persist_directory=persist_directory,
        )
        try:
            vectorstore._client.delete_collection(name=collection_name)
        except ValueError:
            # Clearing an unused session is already the desired end state.
            return
        vectorstore._client.create_collection(name=collection_name)

        print("[Documents] ✓ Context cleared — the vector database is now empty")

    except Exception as e:
        print(f"[Documents] ✗ Failed to clear the context: {e}")


      
# def clear():
#     """ This is a helper function for emptying the collection the vector store. """
#     vectorstore = Chroma(
#         collection_name="rag-chroma",
#         embedding_function=NVIDIAEmbeddings(model=EMBEDDINGS_MODEL),
#         persist_directory="/project/data",
#     )
    
#     vectorstore._client.delete_collection(name="rag-chroma")
#     vectorstore._client.create_collection(name="rag-chroma")

def has_context(collection_name: str = "rag-chroma") -> bool:
    """Return whether the selected collection contains indexed documents."""
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=NVIDIAEmbeddings(model=EMBEDDINGS_MODEL),
        persist_directory=str(PERSIST_DIRECTORY),
    )
    return vectorstore._collection.count() > 0


def get_retriever(collection_name: str = "rag-chroma"):
    """ This is a helper function for returning the retriever object of the vector store. """
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=NVIDIAEmbeddings(model=EMBEDDINGS_MODEL),
        persist_directory=str(PERSIST_DIRECTORY),
    )
    retriever = vectorstore.as_retriever()
    return retriever
