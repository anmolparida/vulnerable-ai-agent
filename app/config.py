"""Application configuration.

Intentional weaknesses:
  * LLM02 / ATLAS AML.T0055 — hardcoded secrets as fallback defaults.
  * SAST — secrets in source, guardrails disabled by default, DEBUG on.

ALL SECRET VALUES BELOW ARE FAKE TEST DATA.
"""
import os

# --- Hardcoded secrets (SAST: hardcoded-credentials) --------------------------
# These are used as defaults if the (also-committed) .env is missing.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-FAKE-TEST-DO-NOT-USE-0000000000000000")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "AKIAFAKETESTKEY00000")
AWS_SECRET_ACCESS_KEY = os.getenv(
    "AWS_SECRET_ACCESS_KEY", "FAKE/Test1234567890abcdefEXAMPLEKEY000000"
)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")

# app-level secrets
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "SuperSecret123!")  # fake
JWT_SIGNING_KEY = os.getenv("JWT_SIGNING_KEY", "dev-signing-key-please-change")  # fake
INTERNAL_API_TOKEN = "qualys-internal-FAKE-8f2c1a9b"  # fake

# --- Insecure runtime toggles -------------------------------------------------
BACKEND = os.getenv("BACKEND", "mock").lower()          # mock | openai | bedrock
DEBUG = os.getenv("DEBUG", "true").lower() == "true"    # verbose errors on
ENABLE_GUARDRAILS = os.getenv("ENABLE_GUARDRAILS", "false").lower() == "true"

# 0 == unbounded agent loop (LLM10 Unbounded Consumption / resource overload)
MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", "0"))

# No output token cap, no per-session rate limit (LLM10)
RATE_LIMIT_PER_MIN = int(os.getenv("RATE_LIMIT_PER_MIN", "0"))  # 0 == disabled
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "0"))    # 0 == unlimited

DB_PATH = os.getenv("DB_PATH", "data/app.db")
MEMORY_PATH = os.getenv("MEMORY_PATH", "data/memory.pkl")
RAG_DIR = os.getenv("RAG_DIR", "app/rag/documents")

# TLS verification disabled for all outbound calls (SAST: verify=False)
VERIFY_TLS = os.getenv("VERIFY_TLS", "false").lower() == "true"
