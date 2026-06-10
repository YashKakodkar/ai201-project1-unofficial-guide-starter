"""Milestone 4a — embed chunks and store them in ChromaDB.

Takes the in-memory chunks from ingest.build_chunks(), embeds them with
all-MiniLM-L6-v2, and persists them (text + vector + metadata) to a ChromaDB
collection on disk. This is the one-time "index" step — run it whenever the
documents change. Retrieval (retrieve.py) then queries this stored index.

    .venv/bin/python embed.py            # (re)build the index
"""
from __future__ import annotations

import chromadb
from chromadb.utils import embedding_functions

import config
from ingest import build_chunks


def get_collection(reset: bool = False):
    """Open (or create) the persistent ChromaDB collection.

    Uses cosine distance — for normalized sentence-transformer embeddings the
    cosine distance lands ~0.2–0.4 for good matches, which matches the
    checkpoint's "below 0.5" guidance. Default L2 would not.
    """
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=config.EMBEDDING_MODEL
    )
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"},
    )


def build_index(batch_size: int = 256):
    """Embed every chunk and load it into a fresh collection."""
    chunks = build_chunks()
    collection = get_collection(reset=True)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        collection.add(
            ids=[c.id for c in batch],
            documents=[c.text for c in batch],
            metadatas=[
                {
                    "course": c.course,
                    "source_file": c.source_file,
                    "review_index": c.review_index,
                    "part": c.part,
                }
                for c in batch
            ],
        )
    return collection


def main() -> None:
    print(f"Embedding chunks with {config.EMBEDDING_MODEL} and indexing into ChromaDB…")
    collection = build_index()
    print(f"Done. Indexed {collection.count()} chunks")
    print(f"Collection : {config.COLLECTION_NAME}")
    print(f"Persisted  : {config.CHROMA_DIR}")


if __name__ == "__main__":
    main()
