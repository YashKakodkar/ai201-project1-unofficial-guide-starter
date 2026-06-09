"""Central configuration for the Unofficial Guide RAG pipeline.

Keeping these values in one place means the planning.md spec, the ingestion
code, and the retrieval/generation code all agree on the same numbers.
"""
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = BASE_DIR / "documents"
CHROMA_DIR = BASE_DIR / "chroma_db"

# --- Embedding / chunking ---------------------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# all-MiniLM-L6-v2 truncates inputs at 256 tokens, so chunks are capped there.
# (planning.md originally guessed ~500; revised once we confirmed the model's
# real limit — a chunk longer than this would be silently truncated when embedded.)
MAX_TOKENS = 256
OVERLAP_TOKENS = 40          # only applied when a long review is sub-split
REVIEW_SEPARATOR = "---"     # boundary between reviews inside a course file

# --- Vector store / retrieval ----------------------------------------------
COLLECTION_NAME = "msai_reviews"
TOP_K = 5

# --- Generation -------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
