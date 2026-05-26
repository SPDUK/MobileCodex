# Mobile Handoff

Use this for progress updates and final replies. The user may be reading from a phone and may not have the terminal, file explorer, or browser visible.

## Progress Updates

Keep updates short and concrete:

- what is running
- what was learned
- what proof is being collected
- whether the preview or command is blocked
- what remains running for the user's phone preview

Do not stream noisy logs. Mention only decisive changes, failures, URLs, and artifacts.

## Final Handoff Template

Use this shape for meaningful tasks:

```markdown
Result: <what changed, ran, or was created>
Preview: <ngrok URL, screenshot, artifact path, local URL, or blocked reason>
Proof: <commands, exit codes, key logs, screenshots, generated files>
Next: <1-3 short options>
```

For very small tasks, compress this into a short paragraph while preserving the same facts.

## Web Example

```markdown
Result: Updated the checkout screen and verified the mobile layout.
Preview: https://example.ngrok-free.app
Proof: `npm run build` exited 0; dev server on port 5173; mobile screenshot at C:\path\shot.png; console had no errors.
Next: Test payment edge cases, add loading skeletons, or ship this change.
```

## CLI Example

```markdown
Result: Added the Rust `scan` command.
Preview: CLI output is below.
Proof: `cargo test` exited 0; `cargo run -- scan fixtures/demo.txt` printed 12 matches in 3 files.
Next: Add JSON output, support ignore globs, or package the binary.
```

## Blocker Example

```markdown
Result: Local app starts, but phone preview is blocked.
Preview: blocked because `ngrok` is not installed on PATH.
Proof: `ngrok http 5173` failed: command not found. Local server responded at http://localhost:5173.
Next: ngrok must be installed and authenticated on this machine before Codex can create a public preview URL.
```

## Mobile Style Rules

- Put the answer before the detail.
- Keep logs clipped to the few lines that matter.
- Use absolute file paths for local artifacts.
- Include screenshots inline when the final answer is visual.
- Include server URL, port, and running status when a preview is part of the task.
- State assumptions only when they affected the implementation.
- Give choices as short next actions, not open-ended homework.
