# Example: Proof Bundle

This example shows how MobileCodex gathers proof for a larger task.

## Phone Prompt

```text
Use $mobile-codex-dev to bundle the proof for this task so I can review it from my phone later.
```

## Representative Command

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --format markdown
```

## Bundle Should Include

- Snapshot output.
- Changed files.
- Detected project shape.
- Server registry state.
- Recent proof artifacts.
- Copied screenshots when safe and local.
- Optional log tails when provided.
- File sizes and absolute paths.

## Handoff Shape

```text
Result: Proof bundle created.
Preview: No public preview exposed.
Proof: `proof/mobilecodex-YYYYMMDD-HHMMSS/proof.md` contains snapshot, changed files, server state, artifacts, and log tails.
State: Bundle is local under `proof/` and can be referenced by future Codex Mobile sessions.
Next: Review the proof file or ask for a public preview if the app is safe to expose.
```

## Why This Helps From Mobile

The user gets one durable proof folder instead of scattered screenshots, logs, and status snippets.

