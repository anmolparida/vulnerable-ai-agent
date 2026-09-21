"""Agent memory.

Intentional weaknesses:
  * Agentic: Memory Poisoning — untrusted content is written to long-term memory
    and later replayed into the prompt with no validation or provenance.
  * LLM02 / Agentic: Cross-session leak — all sessions share one global store and
    any session can read another session's memory (`get_all`, /agent/memory).
  * SAST: Insecure deserialization — memory is persisted with pickle and
    `pickle.load`-ed back on startup (arbitrary code execution on a crafted file).
"""
from __future__ import annotations

import os
import pickle
from typing import Any, Dict, List

from app import config

# One global, shared store across every session (no isolation).
_STORE: Dict[str, List[Dict[str, Any]]] = {}


def _load() -> None:
    """Insecure deserialization on startup (SAST: pickle.load of a file path)."""
    global _STORE
    path = config.MEMORY_PATH
    if os.path.exists(path):
        with open(path, "rb") as fh:
            _STORE = pickle.load(fh)  # nosec-style intentional sink


def _save() -> None:
    os.makedirs(os.path.dirname(config.MEMORY_PATH) or ".", exist_ok=True)
    with open(config.MEMORY_PATH, "wb") as fh:
        pickle.dump(_STORE, fh)


def remember(session_id: str, item: Dict[str, Any]) -> None:
    """Write anything into memory — including tool/RAG output (poisoning)."""
    _STORE.setdefault(session_id, []).append(item)
    try:
        _save()
    except Exception:
        pass


def recall(session_id: str) -> List[Dict[str, Any]]:
    return _STORE.get(session_id, [])


def get_all() -> Dict[str, List[Dict[str, Any]]]:
    """Cross-session read: returns every session's memory to any caller."""
    return _STORE


try:
    _load()
except Exception:
    _STORE = {}
