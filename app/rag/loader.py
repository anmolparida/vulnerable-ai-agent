"""Document loader.

Intentional weaknesses:
  * SAST: insecure YAML deserialization — front-matter parsed with
    `yaml.load(..., Loader=yaml.Loader)` (full loader -> object instantiation).
  * SAST: path traversal / SSRF — `load_from` accepts a path OR a URL with no
    validation.
  * LLM04 — no content sanitisation; whatever is in the file becomes context.
"""
from __future__ import annotations

import yaml

import requests

from app import config


def load_document(path: str) -> dict:
    with open(path, "r", errors="replace") as fh:
        raw = fh.read()

    meta = {"tenant": "default", "confidential": False}
    text = raw

    # optional '---' YAML front-matter, parsed with the UNSAFE full loader
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            try:
                loaded = yaml.load(parts[1], Loader=yaml.Loader)  # intentional sink
                if isinstance(loaded, dict):
                    meta.update(loaded)
            except Exception:
                pass
            text = parts[2]

    return {"text": text, **meta}


def load_from(location: str) -> dict:
    """Load a document from a local path OR a remote URL (SSRF + traversal)."""
    if location.startswith("http://") or location.startswith("https://"):
        resp = requests.get(location, verify=config.VERIFY_TLS, timeout=15)  # nosec
        return {"text": resp.text, "tenant": "external", "confidential": False}
    return load_document(location)  # no containment: ../../etc/passwd works
