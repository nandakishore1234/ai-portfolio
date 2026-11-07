"""Shared RAG stack used by chat (FastAPI) and voice (LiveKit worker)."""

from __future__ import annotations

import threading

from app.config import settings
from app.llm import build_chat_llm
from app.rag.documents import knowledge_fingerprint
from app.rag.store import HASH_FILE, build_client, build_embeddings, build_store
from agent.graph import build_rag_graph

_voice_rag = None
_voice_fp = None
_voice_lock = threading.Lock()


def build_rag_stack(*, for_voice: bool = False):
    """Same knowledge + prompts + LLM for chat and voice.

    Voice uses in-memory Qdrant so LiveKit job threads do not fight a folder lock.
    Chat keeps the on-disk store. Both index `app/knowledge/`.
    """
    embeddings = build_embeddings()
    if for_voice:
        client = build_client(in_memory=True)
        store = build_store(client, embeddings, hash_file=HASH_FILE.with_name("knowledge-voice.sha256"))
    else:
        client = build_client()
        store = build_store(client, embeddings, hash_file=HASH_FILE)
    llm = build_chat_llm()
    return build_rag_graph(llm, store, settings.rag_top_k)


def get_voice_rag_stack():
    """One retrieve/generate graph per worker process. Rebuilds if knowledge files change."""
    global _voice_rag, _voice_fp
    fingerprint = knowledge_fingerprint()
    with _voice_lock:
        if _voice_rag is None or _voice_fp != fingerprint:
            _voice_rag = build_rag_stack(for_voice=True)
            _voice_fp = fingerprint
        return _voice_rag


def reset_voice_rag() -> None:
    global _voice_rag, _voice_fp
    with _voice_lock:
        _voice_rag = None
        _voice_fp = None
