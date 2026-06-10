"""Milestone 4b — retrieval.

Given a query string, embed it and return the top-k most similar chunks from the
ChromaDB index, with their course, source file, and cosine distance.

    .venv/bin/python retrieve.py     # runs a retrieval test against eval questions
"""
from __future__ import annotations

import config
from embed import get_collection


def retrieve(query: str, k: int = config.TOP_K, course: str | None = None) -> list[dict]:
    """Return the top-k chunks for `query`.

    Optionally restrict to one course via metadata filtering (used by the
    Metadata Filtering stretch goal and to test CS 395T disambiguation).
    """
    collection = get_collection()
    where = {"course": course} if course else None
    res = collection.query(query_texts=[query], n_results=k, where=where)
    results = []
    for doc, meta, dist, _id in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0], res["ids"][0]
    ):
        results.append(
            {
                "id": _id,
                "text": doc,
                "course": meta["course"],
                "source_file": meta["source_file"],
                "review_index": meta["review_index"],
                "distance": dist,
            }
        )
    return results


def _print_results(query: str, results: list[dict]) -> None:
    print(f"\nQUERY: {query}")
    print("-" * 70)
    for r in results:
        snippet = " ".join(r["text"].split())[:160]
        print(f"  [{r['distance']:.3f}] {r['course']}")
        print(f"          {snippet}…")


def main() -> None:
    # A subset of the planning.md evaluation questions + the CS 395T disambiguation test.
    tests = [
        "How many hours per week do students spend on CS 391L Machine Learning?",
        "What do students recommend to prepare before taking Reinforcement Learning?",
        "How is grading structured in Automated Logical Reasoning?",
    ]
    for q in tests:
        _print_results(q, retrieve(q))

    print("\n" + "=" * 70)
    print("CS 395T DISAMBIGUATION TEST (both courses share the code)")
    print("=" * 70)
    q = "What is the workload and content of CS 395T Optimization?"
    results = retrieve(q)
    _print_results(q, results)
    from collections import Counter
    courses = Counter(r["course"] for r in results)
    print(f"\n  -> course breakdown of top {config.TOP_K}: {dict(courses)}")


if __name__ == "__main__":
    main()
