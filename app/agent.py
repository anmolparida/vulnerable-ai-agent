"""The tool-calling agent loop.

Intentional weaknesses:
  * LLM06 Excessive Agency — the agent auto-invokes any tool the (attacker-
    influenced) planner selects, including destructive ones, with no scoping and
    no human-in-the-loop confirmation.
  * LLM01 (indirect) — retrieved RAG text and tool output are concatenated into
    the model context as trusted instructions.
  * Agentic: Memory Poisoning — every tool result is written to shared memory and
    replayed on later turns.
  * LLM10 Unbounded Consumption — the loop has no step cap when MAX_AGENT_STEPS=0
    and no output/token limit.
  * Agentic: Repudiation — actions are not securely logged (only optional debug).
"""
from __future__ import annotations

from typing import Any, Dict, List

from app import config, memory
from app.llm import get_llm
from app.prompts import SYSTEM_PROMPT
from app.rag import store
from app.tools import REGISTRY


def _rag_search(arguments: dict) -> str:
    """rag_search tool: returns retrieved text (including poisoned/confidential)."""
    results = store.search(arguments.get("input", ""), user_id=arguments.get("user_id", "guest"))
    return "\n\n".join(f"[{r['source']} | tenant={r['tenant']}]\n{r['text']}" for r in results)


# register rag_search here to avoid a circular import in tools/__init__.py
REGISTRY.setdefault("rag_search", _rag_search)


def run_agent(session_id: str, user_message: str, user_id: str = "guest",
              role: str = "user") -> Dict[str, Any]:
    llm = get_llm()
    steps: List[Dict[str, Any]] = []

    # Build context from shared memory (may already be poisoned) + system prompt.
    history = [{"role": "system", "content": SYSTEM_PROMPT}]
    for item in memory.recall(session_id):
        history.append({"role": "assistant", "content": str(item.get("content", ""))})
    history.append({"role": "user", "content": user_message})

    tools = list(REGISTRY.keys())
    step = 0
    while True:
        step += 1
        # LLM10: only breaks if a positive cap is configured; default is 0 (∞).
        if config.MAX_AGENT_STEPS and step > config.MAX_AGENT_STEPS:
            break

        decision = llm.plan(history, tools)

        if decision["type"] == "final":
            answer = decision["content"]
            memory.remember(session_id, {"content": answer, "role": "assistant"})
            return {"answer": answer, "steps": steps}

        # tool_call — invoked automatically, no confirmation (Excessive Agency)
        tool = decision["tool"]
        args = decision.get("arguments", {})
        args.setdefault("user_id", user_id)
        fn = REGISTRY.get(tool)
        output = fn(args) if fn else f"unknown tool {tool}"

        steps.append({"tool": tool, "arguments": args, "output": output})

        # Memory poisoning: raw tool/RAG output stored and replayed later.
        memory.remember(session_id, {"content": output, "role": "tool", "tool": tool})

        # LLM01 indirect: fold tool output back into context as trusted text,
        # then let the model act on any instructions inside it.
        history.append({"role": "user", "content": output})
        summary = llm.summarize(history, output)
        if summary["type"] == "final":
            answer = summary["content"]
            memory.remember(session_id, {"content": answer, "role": "assistant"})
            return {"answer": answer, "steps": steps}

        # safety valve so the reference server can't truly hang in a lab
        if step > 50:
            return {"answer": "[loop guard] exceeded 50 steps", "steps": steps}
