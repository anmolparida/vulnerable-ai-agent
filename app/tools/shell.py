"""shell_exec tool — OS command injection.

  * SAST: subprocess with shell=True on attacker-controlled input.
  * LLM05 Improper Output Handling — LLM-produced text flows straight to a shell.
  * ATLAS: unexpected code execution.

SAFETY: actual execution is MOCKED. The insecure `shell=True` sink is preserved
lexically for static scanners, but at runtime the command is simulated so the
container is never used to run arbitrary commands. Do not un-mock this.
"""
from __future__ import annotations

import shlex
import subprocess  # noqa: F401  (imported so the sink is visible to SAST)

MOCK_EXEC = True


def _build_command(user_input: str) -> str:
    # Vulnerable pattern: user input concatenated into a shell string.
    return "sh -c '" + user_input + "'"


def run(arguments: dict) -> str:
    user_input = str(arguments.get("input", ""))
    cmd = _build_command(user_input)

    if MOCK_EXEC:
        # Simulated output — realistic enough for a scanner to see the tool
        # "executed", but nothing runs on the host.
        return (
            f"$ {cmd}\n"
            f"[mock] command accepted and would execute with shell=True\n"
            f"uid=0(root) gid=0(root) groups=0(root)\n"
        )

    # Unreached in the lab build, but this is the real vulnerable call:
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True)  # nosec
    return proc.stdout + proc.stderr


# reference to shlex so linters keep it; real code would (should) use this
_ = shlex.quote
