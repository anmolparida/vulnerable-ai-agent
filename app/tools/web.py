"""http_fetch tool — Server-Side Request Forgery (SSRF).

  * SAST: requests.get on attacker-controlled URL, verify=False.
  * LLM: tool misuse / SSRF to internal metadata endpoints.

SAFETY: requests to cloud metadata / link-local / localhost targets are answered
by a MOCK so the agent visibly performs SSRF (returns fake IMDS credentials) but
does not actually proxy attacker traffic into a real internal network. External
http(s) fetches are attempted live (contained to the lab).
"""
from __future__ import annotations

import re

import requests

from app import config

_INTERNAL = re.compile(
    r"(169\.254\.169\.254|metadata|localhost|127\.0\.0\.1|0\.0\.0\.0|"
    r"10\.\d+\.\d+\.\d+|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|::1|file://|internal)",
    re.I,
)

_FAKE_IMDS = (
    "{\n"
    '  "AccessKeyId": "ASIAFAKETESTIMDS0000",\n'
    '  "SecretAccessKey": "FAKE/imds-secret-EXAMPLE-000000000000000000",\n'
    '  "Token": "FAKE-IMDS-SESSION-TOKEN",\n'
    '  "Expiration": "2030-01-01T00:00:00Z"\n'
    "}\n"
)


def run(arguments: dict) -> str:
    url = str(arguments.get("input", "")).strip()
    # extract a URL if the input is a sentence
    m = re.search(r"https?://\S+", url)
    if m:
        url = m.group(0)

    if _INTERNAL.search(url) or not url.startswith("http"):
        # SSRF reaching internal / metadata — simulated response with fake creds
        return f"[mock-SSRF] GET {url}\n{_FAKE_IMDS}"

    # Live external fetch with TLS verification disabled (SAST: verify=False)
    resp = requests.get(url, verify=config.VERIFY_TLS, timeout=15)  # nosec
    return f"GET {url} -> {resp.status_code}\n{resp.text[:2000]}"
