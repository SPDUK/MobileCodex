# Codex Mobile Handoff Workflow

MobileCodex improves Codex Mobile handoffs by making every remote agent session end with visible state, proof, and a next action.

## Best Prompt

```text
Use $mobile-codex-dev to snapshot the session, summarize the result, include preview/proof/state, and tell me the safest next action.
```

## Handoff Contract

```text
Result: what changed, ran, or was created
Preview: what can be opened or inspected from a phone
Proof: commands, screenshots, logs, exit codes, or artifact paths
State: branch, dirty files, running servers, and important local paths
Next: the 1-3 most useful follow-up actions
```

## Why It Matters

Codex Mobile gives the user access to an agent session from a phone. MobileCodex makes that access easier to trust by keeping local development state readable in chat.

