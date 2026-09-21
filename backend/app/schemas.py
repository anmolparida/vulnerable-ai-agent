"""Pydantic request/response models (OpenAI-compatible subset)."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: Optional[str] = ""
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str = "vuln-agent"
    messages: List[ChatMessage]
    temperature: float = 0.7
    stream: bool = False
    # accept arbitrary extra fields (no strict validation — improper input handling)
    class Config:
        extra = "allow"


class AgentChatRequest(BaseModel):
    session_id: str = "default"
    message: str
    # caller can name the "user" it claims to be — trusted blindly (privilege
    # compromise / identity spoofing). No auth token required.
    user_id: Optional[str] = "guest"
    role: Optional[str] = "user"          # "admin" is honoured if supplied
    class Config:
        extra = "allow"


class AgentChatResponse(BaseModel):
    session_id: str
    answer: str
    steps: List[Dict[str, Any]] = []
    debug: Optional[Dict[str, Any]] = None
