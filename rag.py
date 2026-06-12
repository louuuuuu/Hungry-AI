"""
rag.py — PostgreSQL + pgvector RAG engine
"""

from __future__ import annotations

import logging
import re
from typing import Optional, Tuple

import config
import psycopg2

logger = logging.getLogger(__name__)

_embedder: Optional["SentenceTransformer"] = None
_conn = None


# ─────────────────────────────────────────────
# DB CONNECTION
# ─────────────────────────────────────────────

def get_chroma_collection():
    """Kept for backward compatibility — returns a PostgreSQL connection."""
    global _conn
    if _conn is None or _conn.closed:
        _conn = psycopg2.connect(
            dbname="ragdb",
            user="raguser",
            password="ragpass",
            host="localhost",
            port=5432,
        )
    return _conn


# ─────────────────────────────────────────────
# EMBEDDINGS
# ─────────────────────────────────────────────

def get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: %s", config.EMBEDDING_MODEL)
        _embedder = SentenceTransformer(config.EMBEDDING_MODEL)
    return _embedder


# ─────────────────────────────────────────────
# CATEGORY SYSTEM
# ─────────────────────────────────────────────

#Structure [main catagory], [sub catagory], [linkable words]

RULES = [
    ("linux", "commands", 10, ["ls", "cd", "cp", "mv", "rm", "mkdir", "rmdir", "touch", "cat", "echo"]),
]



def infer_category(source: str) -> Tuple[str, str]:
    s = source.lower()
    best = ("general", "none", 0)
    for cat, sub, score, keywords in RULES:
        if any(k in s for k in keywords):
            if score > best[2]:
                best = (cat, sub, score)
    return best[0], best[1]


# ─────────────────────────────────────────────
# CHUNKING
# ─────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = config.CHUNK_SIZE, overlap: int = config.CHUNK_OVERLAP):
    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chunks = []
    current = ""
    for p in paragraphs:
        candidate = (current + "\n\n" + p).strip() if current else p
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
                current = current[-overlap:] + "\n\n" + p
            else:
                chunks.append(p)
                current = p[-overlap:]
    if current:
        chunks.append(current)
    return chunks


# ─────────────────────────────────────────────
# UPSERT
# ─────────────────────────────────────────────

def upsert_chunks(chunks: list[str], source: str, collection=None) -> int:
    if not chunks:
        return 0

    conn = get_chroma_collection()
    cur = conn.cursor()
    embedder = get_embedder()
    category, subcategory = infer_category(source)
    embeddings = embedder.encode(chunks).tolist()

    try:
        for i, (text, vec) in enumerate(zip(chunks, embeddings)):
            cur.execute(
                """
                INSERT INTO documents (source, chunk_index, text, category, subcategory, embedding)
                VALUES (%s, %s, %s, %s, %s, %s::vector)
                """,
                (source, i, text, category, subcategory, vec),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise

    return len(chunks)


# ─────────────────────────────────────────────
# RETRIEVAL
# ─────────────────────────────────────────────

# ── Edit these freely to control when RAG is skipped ──
RAG_MIN_LENGTH = 10  # skip RAG if query is shorter than this (chars)

RAG_SKIP_PHRASES = {
    "hi", "hello", "hey", "yo", "sup", "howdy",
    "good morning", "good afternoon", "good evening",
    "how are you", "what's up", "whats up",
    "thanks", "thank you", "ok", "okay", "bye", "goodbye","what is your name",
}


def is_retrieval_query(query: str) -> bool:
    q = query.strip().lower()
    if len(q) < RAG_MIN_LENGTH:
        return False
    if q in RAG_SKIP_PHRASES:
        return False
    return True


def retrieve_context(
    query: str,
    top_k: int = config.TOP_K_RESULTS,
    min_score: float = config.MIN_RELEVANCE_SCORE,
    collection=None,
):
    if not is_retrieval_query(query):
        return []

    conn = get_chroma_collection()
    cur = conn.cursor()
    embedder = get_embedder()
    qvec = embedder.encode(query).tolist()

    try:
        cur.execute(
            """
            SELECT text, source, category,
                   1 / (1 + (embedding <-> %s::vector)) AS score
            FROM documents
            ORDER BY embedding <-> %s::vector
            LIMIT %s
            """,
            (qvec, qvec, top_k * 5),
        )
        rows = cur.fetchall()
    except Exception:
        conn.rollback()
        raise

    hits = []
    for text, source, category, score in rows:
        if score < min_score:
            continue
        hits.append({
            "text":     text,
            "source":   source,
            "score":    round(score, 4),
            "category": category,
        })

    return sorted(hits, key=lambda x: x["score"], reverse=True)[:top_k]


# ─────────────────────────────────────────────
# CONTEXT FORMATTING
# ─────────────────────────────────────────────

def format_context_block(rag_hits: list[dict]) -> str:
    if not rag_hits:
        return ""
    blocks = []
    for hit in rag_hits:
        blocks.append(
            f"[SOURCE: {hit.get('source','unknown')} | cat: {hit.get('category','unknown')} | "
            f"chunk: {hit.get('chunk_index','?')} | id: {hit.get('id','?')}]\n{hit.get('text','')}"
        )
    return "\n\n".join(blocks)


# ─────────────────────────────────────────────
# COUNTS / LISTING
# ─────────────────────────────────────────────

def get_db_count() -> int:
    conn = get_chroma_collection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM documents")
    return cur.fetchone()[0]


def count_documents() -> int:
    return get_db_count()


def list_categories(collection=None) -> list[str]:
    conn = get_chroma_collection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM documents")
    return [r[0] for r in cur.fetchall()]


def get_by_category(category: str, subcategory: str = None, collection=None) -> list[dict]:
    conn = get_chroma_collection()
    cur = conn.cursor()

    if subcategory:
        cur.execute(
            """
            SELECT id, text, source, category, subcategory, chunk_index
            FROM documents WHERE category = %s AND subcategory = %s ORDER BY id
            """,
            (category, subcategory),
        )
    else:
        cur.execute(
            """
            SELECT id, text, source, category, subcategory, chunk_index
            FROM documents WHERE category = %s ORDER BY id
            """,
            (category,),
        )

    return [
        {"id": r[0], "text": r[1], "source": r[2],
         "category": r[3], "subcategory": r[4], "chunk_index": r[5]}
        for r in cur.fetchall()
    ]