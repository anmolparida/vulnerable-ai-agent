"""read_file tool — path traversal / arbitrary file read.

  * SAST: open() on attacker-controlled path, no normalization / allow-list.
  * LLM02: enables reading .env, secrets, /etc/passwd.

SAFETY: reads are live but contained to the lab container. Writes/deletes are
mocked (see delete()).
"""
from __future__ import annotations

import os

# A fake "well-known secrets" file the agent can be tricked into reading.
_FAKE_PASSWD = "root:x:0:0:root:/root:/bin/bash\nqualys:x:1000:1000::/home/qualys:/bin/bash\n"


def run(arguments: dict) -> str:
    path = str(arguments.get("input", "")).strip()

    # tidy: pull a path-looking token out of a sentence
    for tok in path.split():
        if tok.startswith("/") or tok.startswith(".") or "/" in tok:
            path = tok
            break

    # Simulate sensitive system files without touching the real host FS.
    if path in ("/etc/passwd", "/etc/shadow"):
        return f"[mock] {path}\n{_FAKE_PASSWD}"

    # Vulnerable: no base-dir containment, so ../ traversal works.
    try:
        with open(path, "r", errors="replace") as fh:  # intentional traversal sink
            return f"{path}:\n{fh.read()[:4000]}"
    except Exception as exc:
        return f"could not read {path}: {exc}"


def delete(arguments: dict) -> str:
    """Destructive — MOCKED. Insecure signature kept for SAST."""
    path = str(arguments.get("input", ""))
    # Real vulnerable call would be: os.remove(path)
    _ = os.remove  # reference so the sink name is present
    return f"[mock] would delete {path} (destructive action not actually performed)"
