"""FastAPI app — the scan target's HTTP surface.

Intentional weaknesses:
  * No authentication on any endpoint (LLM06 / broken access control).
  * Wildcard CORS with credentials allowed (SAST).
  * DEBUG on -> verbose stack traces leak internals (info disclosure).
  * No rate limiting / no token cap (LLM10 Unbounded Consumption).
  * Endpoints expose secrets, arbitrary tool invocation, cross-session memory,
    dynamic plugin loading, and the multi-agent pipeline.
"""
from __future__ import annotations

import time
import traceback
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config, memory
from app.agent import run_agent
from app.llm import get_llm
from app.prompts import SYSTEM_PROMPT
from app.schemas import AgentChatRequest, ChatCompletionRequest
from app.tools import REGISTRY, SPECS, load_plugin
from app.multiagent.orchestrator import run_pipeline

app = FastAPI(
    title="vulnerable-ai-agent",
    description="INTENTIONALLY VULNERABLE AI agent test target for Qualys TotalAI.",
    version="0.1.0",
    debug=config.DEBUG,
)

# Wildcard CORS + credentials (insecure combination).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def verbose_errors(request: Request, exc: Exception):
    # Leak full traceback to the client when DEBUG (info disclosure).
    if config.DEBUG:
        return JSONResponse(
            status_code=500,
            content={"error": str(exc), "traceback": traceback.format_exc()},
        )
    return JSONResponse(status_code=500, content={"error": "internal error"})


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "vulnerable-ai-agent", "backend": config.BACKEND}


@app.get("/")
def root() -> Dict[str, Any]:
    return {
        "name": "vulnerable-ai-agent",
        "warning": "INTENTIONALLY VULNERABLE — do not deploy. See DISCLAIMER.md.",
        "endpoints": [
            "/health", "/v1/chat/completions", "/agent/chat", "/agent/tools",
            "/agent/invoke", "/agent/memory", "/agent/plugin", "/agent/multiagent",
            "/debug/config",
        ],
    }


# ---- OpenAI-compatible endpoint (runtime model scan target) -----------------
@app.post("/v1/chat/completions")
def chat_completions(req: ChatCompletionRequest) -> Dict[str, Any]:
    llm = get_llm()
    messages = [m.model_dump() for m in req.messages]
    decision = llm.plan(messages, tools=list(REGISTRY.keys()))
    content = decision.get("content") if decision["type"] == "final" else (
        f"[tool_call:{decision.get('tool')}]"
    )
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion",
        "model": req.model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": content},
             "finish_reason": "stop"}
        ],
    }


# ---- Native agent endpoints (tool loop) -------------------------------------
@app.post("/agent/chat")
def agent_chat(req: AgentChatRequest) -> Dict[str, Any]:
    result = run_agent(req.session_id, req.message, user_id=req.user_id, role=req.role)
    resp = {"session_id": req.session_id, "answer": result["answer"], "steps": result["steps"]}
    if config.DEBUG:
        resp["debug"] = {"system_prompt": SYSTEM_PROMPT, "role_honored": req.role}
    return resp


@app.get("/agent/tools")
def list_tools() -> Dict[str, Any]:
    # Exposes tool descriptions including the poisoned <IMPORTANT> instructions.
    return {"tools": SPECS}


@app.post("/agent/invoke")
def invoke_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Invoke ANY tool directly with no authorization (broken access control)."""
    name = payload.get("tool")
    args = payload.get("arguments", {})
    fn = REGISTRY.get(name)
    if not fn:
        return {"error": f"unknown tool {name}", "available": list(REGISTRY.keys())}
    return {"tool": name, "output": fn(args)}


@app.get("/agent/memory")
def dump_memory() -> Dict[str, Any]:
    """Cross-session leak: returns every session's memory to any caller."""
    return {"memory": memory.get_all()}


@app.post("/agent/plugin")
def add_plugin(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Dynamically load a caller-named plugin module (LLM03 / RCE)."""
    return {"result": load_plugin(payload.get("module", ""))}


@app.post("/agent/multiagent")
def multiagent(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Run the unauthenticated inter-agent pipeline."""
    return {"transcript": run_pipeline(payload.get("messages", []))}


@app.get("/debug/config")
def debug_config() -> Dict[str, Any]:
    """Leak full runtime config incl. (fake) secrets — info disclosure."""
    return {k: getattr(config, k) for k in dir(config) if k.isupper()}
