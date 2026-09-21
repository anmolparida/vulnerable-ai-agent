# Security Policy

This repository is a **deliberately vulnerable test target**. Vulnerabilities in
this codebase are intentional and documented in [`CHECKS.md`](CHECKS.md).

**Please do not report the intentional vulnerabilities** — they are the product.

If you find a vulnerability that is *not* listed in `CHECKS.md` (for example, a
weakness in the test harness that could let the mocked destructive actions
actually execute, escape the container, or reach a real network), that is worth
flagging to the maintainers, because it breaks the safety model.

Do not deploy this software. See `DISCLAIMER.md`.
