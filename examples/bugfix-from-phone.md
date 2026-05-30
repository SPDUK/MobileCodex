# Example: Bugfix From Phone

This example shows how MobileCodex keeps a bugfix inspectable while the user is away from the laptop.

## Phone Prompt

```text
Use $mobile-codex-dev to fix the failing test, run the focused checks, and give me the proof and next step.
```

## What Codex Should Do

1. Inspect changed files and test signals.
2. Run the smallest useful failing command.
3. Patch the bug.
4. Re-run the focused command.
5. Summarize only decisive output with exit codes.
6. Create a snapshot or proof bundle if the fix spans multiple files.

## Representative Commands

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py snapshot --root . --format markdown
npm test -- --runInBand
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --format markdown --log-file .\test-output.log
```

## Handoff Shape

```text
Result: Fixed the failing parser edge case and updated the focused test.
Preview: No browser preview needed for this CLI/test change.
Proof: `npm test -- --runInBand` exited 0. Proof bundle written to proof/mobilecodex-YYYYMMDD-HHMMSS/proof.md.
State: Two source files changed, no registered servers running.
Next: Run the full suite or review the diff.
```

## Why This Helps From Mobile

The user gets the important output without reading a full terminal log. If the work needs to resume later, the snapshot and proof bundle preserve the state.

