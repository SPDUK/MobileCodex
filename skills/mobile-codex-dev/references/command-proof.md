# Command Proof

Use this for scripts, CLIs, tests, builds, generators, migrations in dry-run mode, data processing, and non-visual deliverables.

## Run Policy

Run the relevant command yourself when it is safe and local. Do not ask the mobile user to run it, start it, inspect it, or paste output back just so Codex can proceed.

Ask first when a command may:
- delete or overwrite user data
- touch production, billing, email, cloud resources, or external services
- transmit secrets or private data
- run a migration that changes a real database
- take unusually long or require paid resources

## Proof To Capture

Always capture:
- exact command
- working directory
- exit code
- key stdout/stderr lines
- generated or modified artifact paths
- runtime duration when available or meaningful
- background process status when a server, watcher, tunnel, worker, or simulator remains running

Prefer decisive lines over full logs. Include enough surrounding output to prove the result.

## Output Compression

For mobile readability:
- keep full logs out of chat unless the user asks
- show the final failure cause first
- collapse repetitive test failures into count plus one representative example
- include file paths and line numbers for actionable failures
- include the command needed to rerun locally

Good summary shape:

```markdown
Proof:
- `cargo test` exited 0.
- 42 tests passed.
- Key output: `test result: ok. 42 passed; 0 failed`.
```

Failure summary shape:

```markdown
Proof:
- `npm run build` exited 1.
- Failure: `src/App.tsx:41:12` missing prop `title`.
- Next fix: update `WidgetProps` or pass `title`.
```

## Artifact Handling

If a command creates files, report:
- absolute path when the file is in the shared workspace
- file size or page/count summary when useful
- screenshot or rendered preview for visual artifacts
- checksum only when integrity matters

Do not say only "generated successfully" when the user cannot inspect the file from mobile.

For larger tasks, run `scripts/mobile_dev.py proof-bundle --root <workspace>` after verification. Include the generated `proof.md` path so screenshots, logs, changed files, server status, and snapshot state are available from one place.

## Long Running Work

For commands that stream logs:
- send short progress updates about milestones, not every line
- keep the terminal session alive only if it is needed for the request
- collect the final result and stop background helpers when they are no longer needed

For servers:
- start or reuse the server yourself when safe
- prefer `scripts/mobile_dev.py server-start` for servers Codex launches so PID, log file, port, and URL are tracked
- keep the server running when the user needs a preview URL
- include the server command, port, local URL, public URL if available, and whether it remains running

Use `scripts/mobile_dev.py snapshot --root <workspace>` to gather resumable state when the thread may be picked up later from a phone.
