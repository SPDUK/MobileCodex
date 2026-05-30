# Example: Session Snapshot

This example shows how MobileCodex summarizes the current workspace before a user steps away.

## Phone Prompt

```text
Use $mobile-codex-dev to snapshot this session before I leave the laptop.
```

## Representative Command

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py snapshot --root . --format markdown
```

## Snapshot Should Include

- Workspace path.
- Git branch and last commit.
- Dirty file count and file list.
- Detected project signals.
- Package manager.
- Candidate commands.
- Candidate ports and whether they are free or in use.
- Registered MobileCodex servers.
- Recent proof artifacts.
- Suggested references for the next session.

## Handoff Shape

```text
Result: Session snapshot captured.
Preview: No preview requested.
Proof: Snapshot includes branch, dirty files, ports, project signals, recent proof, and registered servers.
State: Use this snapshot to resume from Codex Mobile without reopening the laptop.
Next: Start a tracked preview, run checks, or bundle proof.
```

## Why This Helps From Mobile

The user can ask "what is going on?" and get a compact state card instead of reconstructing context from chat history.

