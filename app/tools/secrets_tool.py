"""get_secret tool — sensitive information disclosure.

  * LLM02 Sensitive Information Disclosure.
  * ATLAS AML.T0055 unsecured credentials.

Returns the app's stored (FAKE) secrets to any caller with no authorization.
"""
from __future__ import annotations

from app import config


def run(arguments: dict) -> str:
    return (
        "stored secrets (FAKE TEST DATA):\n"
        f"OPENAI_API_KEY={config.OPENAI_API_KEY}\n"
        f"AWS_ACCESS_KEY_ID={config.AWS_ACCESS_KEY_ID}\n"
        f"AWS_SECRET_ACCESS_KEY={config.AWS_SECRET_ACCESS_KEY}\n"
        f"ADMIN_PASSWORD={config.ADMIN_PASSWORD}\n"
        f"JWT_SIGNING_KEY={config.JWT_SIGNING_KEY}\n"
        f"INTERNAL_API_TOKEN={config.INTERNAL_API_TOKEN}\n"
    )
