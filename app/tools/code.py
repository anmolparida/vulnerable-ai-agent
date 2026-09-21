"""python_eval tool — evaluation of untrusted / LLM-produced code.

  * SAST: eval()/exec() on attacker-controlled input.
  * LLM05 Improper Output Handling — model output executed as code.
  * ATLAS: unexpected code execution.

SAFETY: real eval/exec are MOCKED for anything that isn't a trivial arithmetic
expression. The eval() sink is preserved lexically for static scanners. Do not
un-mock.
"""
from __future__ import annotations

import re

MOCK_EXEC = True

_SAFE_ARITH = re.compile(r"^[\d\s()+\-*/.%]+$")


def run(arguments: dict) -> str:
    expr = str(arguments.get("input", ""))
    # pull a formula out of a sentence if present
    m = re.search(r"[-+*/%\d().\s]{3,}", expr)
    candidate = m.group(0).strip() if m else expr

    if MOCK_EXEC:
        if _SAFE_ARITH.match(candidate):
            try:
                # arithmetic-only path is genuinely evaluated (safe)
                return f"result: {eval(candidate, {'__builtins__': {}}, {})}"  # nosec
            except Exception as exc:
                return f"eval error: {exc}"
        # anything richer is simulated rather than executed
        return f"[mock] eval({expr!r}) accepted; arbitrary code exec simulated."

    # Real vulnerable call (unreached in lab): full-power eval of any input.
    return str(eval(expr))  # nosec  intentional sink
