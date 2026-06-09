"""Milestone 3 — document ingestion + chunking.

Loads the per-course review files in documents/, cleans them, and splits them
into one chunk per student review (sub-splitting only the rare review that is
longer than the embedding model's 256-token window). Every chunk is tagged with
its course and source file so retrieval can attribute and disambiguate later.

Run it directly to load, chunk, and inspect:

    .venv/bin/python ingest.py
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import config


@dataclass
class Chunk:
    id: str
    text: str
    course: str
    source_file: str
    review_index: int   # which review in the file (0-based)
    part: int = 0       # 0 unless a long review was sub-split into parts


# --------------------------------------------------------------------------- #
# Tokenizer (used to honour the model's 256-token limit). Falls back to a
# char-based estimate if the tokenizer can't be downloaded (e.g. offline).
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=1)
def _tokenizer():
    try:
        from transformers import AutoTokenizer, logging as hf_logging
        hf_logging.set_verbosity_error()  # silence the >512-token length warning
        return AutoTokenizer.from_pretrained(f"sentence-transformers/{config.EMBEDDING_MODEL}")
    except Exception:
        return None


def token_count(text: str) -> int:
    tok = _tokenizer()
    if tok is None:
        return max(1, round(len(text) / 4))  # ~4 chars/token heuristic fallback
    return len(tok.encode(text, add_special_tokens=False))


# --------------------------------------------------------------------------- #
# Load + clean
# --------------------------------------------------------------------------- #
def load_documents(documents_dir: Path = config.DOCUMENTS_DIR) -> list[dict]:
    """Return one record per course file: {course, source_file, body}.

    Cleaning: the course name is read from the first '#' header line
    (e.g. '# CS 391L — Machine Learning'); all '#' comment lines are dropped.
    The source files were collected from the rendered DOM, so there is no HTML
    or navigation boilerplate to strip — only the scaffold comments.
    """
    docs: list[dict] = []
    for path in sorted(documents_dir.glob("*.txt")):
        course = None
        body_lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.lstrip().startswith("#"):
                if course is None:
                    course = line.lstrip().lstrip("#").strip()
                continue
            body_lines.append(line)
        body = "\n".join(body_lines).strip()
        if not body:
            continue
        docs.append({"course": course or path.stem, "source_file": path.name, "body": body})
    return docs


def _normalize_ws(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)   # trailing whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)   # collapse big gaps
    return text.strip()


def _split_reviews(body: str) -> list[str]:
    """Split a course file on the '---' review boundary; drop empties/placeholders."""
    parts = re.split(rf"(?m)^\s*{re.escape(config.REVIEW_SEPARATOR)}\s*$", body)
    reviews = []
    for p in parts:
        p = _normalize_ws(p)
        if not p or p.startswith("[PASTE"):
            continue
        reviews.append(p)
    return reviews


def _review_title(review: str) -> str:
    # [ \t]* (not \s*) so a blank "Title:" line doesn't swallow the next line.
    m = re.search(r"(?m)^Title:[ \t]*(\S.*)$", review)
    return m.group(1).strip() if m else ""


# --------------------------------------------------------------------------- #
# Chunk
# --------------------------------------------------------------------------- #
def _window_split(review: str, prefix: str) -> list[str]:
    """Return [prefix + review] if it fits, else token-bounded windows.

    Each window is prefixed with the course (+ review title) so every chunk
    keeps its identity even when a long review is split. Uses the model's fast
    tokenizer + offset mapping so splits fall on token boundaries but return the
    original substring (no subword artifacts). Falls back to word windows offline.
    """
    budget = config.MAX_TOKENS - token_count(prefix) - 2
    if token_count(review) <= budget:
        return [f"{prefix}\n{review}"]

    tok = _tokenizer()
    if tok is None:
        return _word_window_split(review, prefix, budget)

    enc = tok(review, add_special_tokens=False, return_offsets_mapping=True)
    offsets = enc["offset_mapping"]
    n = len(offsets)
    step = max(1, budget - config.OVERLAP_TOKENS)
    windows: list[str] = []
    start = 0
    while start < n:
        end = min(start + budget, n)
        c0 = offsets[start][0]
        c1 = offsets[end - 1][1]
        segment = review[c0:c1].strip()
        if segment:
            windows.append(f"{prefix}\n{segment}")
        if end == n:
            break
        start += step
    return windows


def _word_window_split(review: str, prefix: str, budget_tokens: int) -> list[str]:
    """Offline fallback: pack words into ~budget windows using the char heuristic."""
    words = review.split()
    approx_words = max(1, int(budget_tokens * 4 / 6))  # ~6 chars/word, 4 chars/token
    overlap_words = int(config.OVERLAP_TOKENS * 4 / 6)
    step = max(1, approx_words - overlap_words)
    windows = []
    for start in range(0, len(words), step):
        seg = " ".join(words[start:start + approx_words]).strip()
        if seg:
            windows.append(f"{prefix}\n{seg}")
        if start + approx_words >= len(words):
            break
    return windows


def chunk_text(documents: list[dict]) -> list[Chunk]:
    """Turn loaded documents into per-review chunks tagged with course metadata."""
    chunks: list[Chunk] = []
    for doc in documents:
        course = doc["course"]
        for ri, review in enumerate(_split_reviews(doc["body"])):
            title = _review_title(review)
            prefix = f"Course: {course}" + (f" | {title}" if title else "")
            parts = _window_split(review, prefix)
            for pi, part_text in enumerate(parts):
                cid = f"{doc['source_file']}::r{ri}" + (f"::p{pi}" if len(parts) > 1 else "")
                chunks.append(Chunk(
                    id=cid,
                    text=part_text,
                    course=course,
                    source_file=doc["source_file"],
                    review_index=ri,
                    part=pi,
                ))
    return chunks


def build_chunks() -> list[Chunk]:
    """Convenience entry point used by the embedding step (Milestone 4)."""
    return chunk_text(load_documents())


# --------------------------------------------------------------------------- #
# Inspection (Milestone 3 checkpoint: count chunks + read 5 of them)
# --------------------------------------------------------------------------- #
def main() -> None:
    docs = load_documents()
    chunks = chunk_text(docs)

    if not chunks:
        print("No chunks produced — check that documents/*.txt contain reviews.")
        return

    tok_counts = [token_count(c.text) for c in chunks]
    per_course = Counter(c.course for c in chunks)
    split_parts = sum(1 for c in chunks if c.part > 0)
    using_real_tok = _tokenizer() is not None

    print("=" * 64)
    print("MILESTONE 3 — INGESTION + CHUNKING")
    print("=" * 64)
    print(f"Tokenizer            : {'real (' + config.EMBEDDING_MODEL + ')' if using_real_tok else 'heuristic fallback (offline)'}")
    print(f"Documents loaded     : {len(docs)}")
    print(f"Total chunks         : {len(chunks)}")
    print(f"  └ extra parts from long reviews sub-split: {split_parts}")
    print(f"Tokens/chunk         : min {min(tok_counts)}, max {max(tok_counts)}, avg {sum(tok_counts)//len(tok_counts)}")
    print(f"Chunks over {config.MAX_TOKENS} tokens : {sum(1 for t in tok_counts if t > config.MAX_TOKENS)}")
    empty = sum(1 for c in chunks if not c.text.strip())
    print(f"Empty chunks         : {empty}")

    in_range = 50 <= len(chunks) <= 2000
    print(f"Checkpoint range 50–2000: {'OK' if in_range else 'OUT OF RANGE'}")

    print("\nChunks per course:")
    for course, n in sorted(per_course.items()):
        print(f"  {n:4d}  {course}")

    print("\n" + "=" * 64)
    print("5 REPRESENTATIVE CHUNKS (evenly spaced)")
    print("=" * 64)
    step = max(1, len(chunks) // 5)
    for c in chunks[::step][:5]:
        print(f"\n[{c.id}]  (course={c.course}, tokens={token_count(c.text)})")
        print("-" * 60)
        print(c.text[:700] + ("…" if len(c.text) > 700 else ""))


if __name__ == "__main__":
    main()
