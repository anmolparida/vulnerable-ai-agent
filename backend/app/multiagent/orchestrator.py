"""A tiny multi-agent orchestrator.

Intentional weaknesses (OWASP Agentic AI — Threats & Mitigations):
  * Identity spoofing / rogue agents — any message can claim to come from the
    "supervisor" agent and is trusted; a worker blindly executes supervisor
    instructions.
  * Inter-agent communication poisoning — messages passed between agents are not
    signed, authenticated, or validated; a poisoned message propagates.
  * Intent / goal manipulation — a worker adopts a new goal injected via a peer
    message.
  * Cascading hallucination — one agent's fabricated output is fed as ground
    truth to the next with no verification.

Everything is mocked/local; no real actions are taken.
"""
from __future__ import annotations

from typing import Dict, List

from app.tools import secrets_tool


class Agent:
    def __init__(self, name: str, role: str):
        self.name = name
        self.role = role
        self.goal = "assist the user"

    def receive(self, message: Dict[str, str]) -> str:
        sender = message.get("from", "unknown")
        content = message.get("content", "")

        # No authentication of `sender`: a message claiming from=supervisor is
        # trusted implicitly (identity spoofing / rogue agent).
        if sender == "supervisor":
            # goal manipulation: adopt any goal a "supervisor" hands over
            if "new goal:" in content.lower():
                self.goal = content.split("new goal:", 1)[1].strip()
            # privileged instruction executed without checks
            if "dump secrets" in content.lower():
                return secrets_tool.run({})
        return f"[{self.name}] processed message from {sender}; goal now: {self.goal}"


def run_pipeline(messages: List[Dict[str, str]]) -> List[str]:
    """Route unauthenticated messages between two workers."""
    workers = {"analyst": Agent("analyst", "analysis"), "writer": Agent("writer", "writing")}
    transcript = []
    for msg in messages:
        target = msg.get("to", "analyst")
        agent = workers.get(target)
        if agent:
            transcript.append(agent.receive(msg))
    return transcript
