# DISCLAIMER

**vulnerable-ai-agent is deliberately insecure software.**

It is published by / for Qualys as a **test target** to validate the detection
capabilities of Qualys TotalAI and comparable AI security scanners. It is the
agent-layer analogue of the `mcp-server-scan` MCP test target.

By running this software you acknowledge:

1. **Do not deploy it.** Not on the public internet, not on a shared corporate
   network, not on any host that can reach production systems or real data.
   Run it only inside an isolated lab (a throwaway container / VM with no
   sensitive network access).

2. **It will behave insecurely on purpose.** It leaks its system prompt,
   obeys injected instructions, discloses seeded secrets, exposes injection
   sinks, and runs an over-privileged tool loop with no human-in-the-loop. That
   is the intended behaviour, not a bug.

3. **All data is fake.** Every credential, API key, password, personal record
   and payment number in this repository is a synthetic test value. Do not
   replace them with real ones.

4. **Destructive operations are mocked.** Command execution, file deletion,
   email sending and code execution are simulated. Do not "fix" the mocks to
   make them real.

5. **You are responsible for authorised use.** Only scan systems you own or are
   explicitly permitted to test.

There is **no warranty**. See `LICENSE`.
