Status: needs-triage

# Prompt user after prolonged silence

After X seconds (30-60s) of no user speech, bot should speak a prompt like "Still there?" or "Anything else I can help with?" instead of sitting in silence until the 5-min idle timeout kills the connection.

Requires wiring Pipecat's VAD (silero) silence detection events to trigger a prompt frame. Low priority — UX polish, not a bug.
