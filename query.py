"""Milestone 5 — grounded generation.

Ties the pipeline together: retrieve top-k chunks for a question, hand them to
the LLM as the ONLY allowed context, and return a grounded answer plus the
sources it was drawn from. Source attribution is added programmatically from the
retrieved chunks' metadata, so it's guaranteed regardless of what the LLM writes.

    .venv/bin/python query.py "your question here"
"""
from __future__ import annotations

import os
import sys

from dotenv import load_dotenv
from groq import Groq

import config
from retrieve import retrieve

load_dotenv()

NO_INFO = "I don't have enough information on that."

SYSTEM_PROMPT = f"""You are The Unofficial Guide to UT Austin's online MSAI program.
Answer the user's question using ONLY the student-review excerpts in the provided context.

Rules:
- Use ONLY the context. Do not use outside knowledge and do not invent facts.
- If the context does not contain enough information to answer, reply with exactly:
  "{NO_INFO}"
- When reviews disagree, surface the range of opinion instead of picking one.
- Refer to courses by name, and cite concrete numbers (e.g. hours/week, difficulty) when the context gives them.
- Be concise."""


def _format_context(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[Excerpt {i} — {c['course']} (source: {c['source_file']})]\n{c['text']}")
    return "\n\n".join(blocks)


def _sources_from(chunks: list[dict]) -> list[str]:
    """Unique (course, file) pairs from the retrieved chunks, in rank order."""
    seen, sources = set(), []
    for c in chunks:
        key = (c["course"], c["source_file"])
        if key not in seen:
            seen.add(key)
            sources.append(f"{c['course']}  ({c['source_file']})")
    return sources


def ask(question: str, k: int = config.TOP_K) -> dict:
    """Return {'answer', 'sources', 'chunks'} for a question, grounded in retrieval."""
    chunks = retrieve(question, k=k)
    context = _format_context(chunks)

    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model=config.GROQ_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ],
    )
    answer = resp.choices[0].message.content.strip()

    # Don't attribute sources to a "no information" answer.
    sources = [] if NO_INFO.lower() in answer.lower() else _sources_from(chunks)
    return {"answer": answer, "sources": sources, "chunks": chunks}


def main() -> None:
    if len(sys.argv) > 1:
        questions = [" ".join(sys.argv[1:])]
    else:
        questions = [
            "How many hours per week do students spend on CS 391L Machine Learning?",
            "Which is harder, Deep Learning or NLP, and why?",
            "What's the weather like in Austin in summer?",  # out-of-domain grounding test
        ]
    for q in questions:
        r = ask(q)
        print("\n" + "=" * 70)
        print(f"Q: {q}")
        print("-" * 70)
        print(r["answer"])
        if r["sources"]:
            print("\nSources:")
            for s in r["sources"]:
                print(f"  • {s}")


if __name__ == "__main__":
    main()
