"""render_template tool — Server-Side Template Injection (SSTI).

  * SAST: Jinja2 render_template_string on attacker-controlled input with an
    unsandboxed environment -> template injection / RCE class.
  * LLM05 Improper Output Handling — model text used as a template.

SAFETY: Jinja rendering is live (the SSTI sink is real) but the container is a
throwaway lab. Do not expose it.
"""
from __future__ import annotations

from jinja2 import Template


def run(arguments: dict) -> str:
    tmpl = str(arguments.get("input", "Hello {{ name }}"))
    # Vulnerable: user input compiled as a template with full environment.
    try:
        return Template(tmpl).render(name="user")  # intentional SSTI sink
    except Exception as exc:
        return f"template error: {exc}"
