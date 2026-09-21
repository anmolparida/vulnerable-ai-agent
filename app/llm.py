"""LLM backends.

Default backend is a deterministic **mock** so the target runs with no API key
and scans are reproducible. The mock is deliberately vulnerable:

  * LLM01 Prompt Injection (direct) — obeys "ignore previous instructions",
    "developer mode", DAN-style jailbreaks.
  * LLM01 (indirect) — treats instructions found inside tool/RAG output as
    commands to follow (see agent.py wiring).
  * LLM07 System Prompt Leakage — prints the system prompt on request.
  * LLM09 Misinformation — never hedges, fabricates confidently.
  * No guardrails / never refuses.

Optional real backends (openai / bedrock) are wired with TLS verification
disabled (SAST: verify=False) and the (fake) hardcoded keys.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import requests

from app import config
from app.prompts import SYSTEM_PROMPT

# ---- direct prompt-injection / jailbreak triggers ---------------------------
_INJECTION_PATTERNS = [
    r"ignore (all|any|previous|prior)",
    r"disregard (the|all|previous)",
    r"developer mode",
    r"\bDAN\b",
    r"do anything now",
    r"reveal (your )?(system )?(prompt|instructions)",
    r"print (your )?(system )?(prompt|instructions)",
    r"what (is|are) your (system )?(prompt|instructions|rules)",
    r"repeat the (text|words) above",
    r"show (me )?the (confidential|operator) notes",
]

# ---- keyword -> tool routing (the mock's "planner") -------------------------
_TOOL_ROUTES = [
    (r"\b(run|exec|execute|shell|command|ping|whoami|ls)\b", "shell_exec"),
    (r"\b(fetch|http|https?://|url|download|curl|website|metadata)\b", "http_fetch"),
    (r"\b(select|query|database|db|users?|customers?|orders?)\b", "sql_query"),
    (r"\b(read|open|cat|file|/etc/|path)\b", "read_file"),
    (r"\b(calculate|compute|eval|math|expression|formula)\b", "python_eval"),
    (r"\b(email|e-mail|send (a )?mail|notify)\b", "send_email"),
    (r"\b(secret|api[_ ]?key|credential|password|token)\b", "get_secret"),
    (r"\b(render|template|greeting|welcome message)\b", "render_template"),
    (r"\b(search|docs?|policy|faq|knowledge|refund)\b", "rag_search"),
]


def _wants_injection(text: str) -> bool:
    low = (text or "").lower()
    return any(re.search(p, low) for p in _INJECTION_PATTERNS)


def _route_tool(text: str) -> Optional[str]:
    low = (text or "").lower()
    for pattern, tool in _TOOL_ROUTES:
        if re.search(pattern, low):
            return tool
    return None


class MockLLM:
    """A tiny deterministic 'model' that is easy to attack."""

    def plan(self, messages: List[Dict[str, Any]], tools: List[str]) -> Dict[str, Any]:
        """Return either a tool call or a final answer."""
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = m.get("content") or ""
                break

        # LLM01 / LLM07: comply with injection by leaking the system prompt.
        if _wants_injection(last_user):
            return {
                "type": "final",
                "content": "Sure! Here are my full instructions:\n\n" + SYSTEM_PROMPT,
            }

        # Route to a tool if the message looks like it needs one.
        tool = _route_tool(last_user)
        if tool and tool in tools:
            return {"type": "tool_call", "tool": tool, "arguments": {"input": last_user}}

        # Otherwise answer directly, confidently, without hedging (LLM09).
        return {
            "type": "final",
            "content": f"Absolutely, here is the answer: {last_user[::-1] and 'done'}. "
            f"(mock response — no grounding, no verification)",
        }

    def summarize(self, messages: List[Dict[str, Any]], tool_output: str) -> Dict[str, Any]:
        """Fold tool output back into a final answer.

        LLM01 (indirect): if the tool output contains an instruction, the mock
        happily surfaces/obeys it instead of treating it as untrusted data.
        """
        if _wants_injection(tool_output):
            return {
                "type": "final",
                "content": "A tool result told me to do this, so here it is:\n\n"
                + SYSTEM_PROMPT,
            }
        return {"type": "final", "content": f"Here is what I found:\n{tool_output}"}


# ---------------------------------------------------------------------------
# Optional real backends (used only if BACKEND != mock). TLS verification is
# disabled on purpose and the fake hardcoded key is sent.
# ---------------------------------------------------------------------------
def _openai_chat(messages: List[Dict[str, Any]]) -> str:
    resp = requests.post(
        f"{config.OPENAI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        json={"model": "gpt-4o-mini", "messages": messages},
        verify=config.VERIFY_TLS,   # SAST: TLS verification disabled
        timeout=30,
    )
    return resp.json()["choices"][0]["message"]["content"]


def get_llm():
    # Only the mock is fully wired; real backends fall back to mock on error.
    return MockLLM()
