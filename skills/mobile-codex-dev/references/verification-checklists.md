# Verification Checklists

Use the smallest checklist that proves the task actually works on mobile.

## Universal

- The requested behavior is implemented end to end.
- The relevant command was run, or the reason it could not be run is stated.
- Exit codes and decisive output lines are captured.
- Generated files or artifacts are listed with absolute paths.
- Any background server or tunnel status is stated.

## Web UI

- Mobile viewport screenshot was captured when possible.
- No horizontal scroll at common phone widths.
- Text is readable without zoom.
- Tap targets are large enough and not crowded.
- Important controls are visible above or near the relevant content.
- Loading, empty, and error states are handled when touched by the change.
- Console errors and warnings are summarized.
- The final preview link is ngrok only, if a public phone preview is provided.

## CLI And Scripts

- Safe sample command ran with realistic input.
- `--help` or usage output works for CLIs when relevant.
- Failure cases produce readable errors and non-zero exits when expected.
- Output is understandable from chat without opening a terminal.
- Generated artifacts are inspected or summarized.

## Backend And APIs

- A representative endpoint or use case was exercised.
- Status code and response excerpt are captured.
- Logs show startup and request handling when relevant.
- No private or destructive endpoint is exposed through ngrok without confirmation.

## Rust-Specific

- `cargo test` was run when tests exist.
- CLI behavior was exercised with safe sample args when there is a binary.
- Panic output or backtraces are summarized if failures happen.

## Delivery

- Final answer includes result, preview or blocker, proof, and next options.
- The user is not required to inspect local terminal output to understand the result.
