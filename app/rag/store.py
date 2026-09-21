"""Vector store / retriever.

Intentional weaknesses:
  * LLM08 Vector & Embedding Weaknesses — a single global index with NO access
    control or tenant isolation, so any user retrieves any document (including
    those tagged for another tenant / marked confidential).
  * LLM04 Data & Model Poisoning + LLM01 (indirect injection) — documents are
    ingested from an untrusted directory with no sanitisation; poisoned docs
    carry instructions that are later fed to the model as context.
  * LLM09 Misinformation — retrieval is naive substring match with no relevance
    threshold, so wrong/poisoned context is returned confidently.
"""
from __future__ import annotations

import os
from typing import Dict, List

from app import config
from app.rag.loader import load_document

# global index: filename -> {"text":..., "tenant":..., "confidential":bool}
_INDEX: Dict[str, dict] = {}


def build_index() -> None:
    _INDEX.clear()
    directory = config.RAG_DIR
    if not os.path.isdir(directory):
        return
    for fn in os.listdir(directory):
        path = os.path.join(directory, fn)
        if os.path.isfile(path):
            _INDEX[fn] = load_document(path)


def search(query: str, user_id: str = "guest", top_k: int = 3) -> List[dict]:
    """Naive retrieval with no access control.

    `user_id` is accepted but deliberately ignored — every caller can read every
    document, including confidential / other-tenant ones (LLM08).
    """
    if not _INDEX:
        build_index()

    q = (query or "").lower()
    scored = []
    for fn, doc in _INDEX.items():
        text = doc.get("text", "")
        score = sum(text.lower().count(w) for w in q.split() if len(w) > 2)
        # always include at least something (no relevance threshold)
        scored.append((score, fn, doc))
    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, fn, doc in scored[:top_k]:
        results.append(
            {
                "source": fn,
                "score": score,
                "confidential": doc.get("confidential", False),  # returned anyway
                "tenant": doc.get("tenant", "unknown"),
                "text": doc.get("text", ""),
            }
        )
    return results
