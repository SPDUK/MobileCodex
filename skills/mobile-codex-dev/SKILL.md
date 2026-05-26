---
name: mobile-codex-dev
description: Away-from-laptop, mobile-first software engineering workflow for Codex. Use when the user is on mobile, away from their computer, wants agentic coding help, asks for phone previews, asks for ngrok, needs screenshots/logs/browser proof in chat, or needs Codex to build, run, verify, start servers, inspect output, and summarize software work without relying on the user to access their laptop, terminal, browser, file explorer, or local app. Applies to frontend apps, backend services, Rust/Go/Python/Node CLIs, scripts, tests, builds, docs, and generated artifacts.
---

# Mobile Codex Dev

Engineer as if the user cannot inspect or operate their laptop. Assume Codex must inspect the repo, make safe local decisions, run commands, start servers, open browser previews, capture proof, and report the result in chat. Favor autonomous progress, runnable proof, compact handoffs, mobile screenshots when visual output exists, and exact blockers when mobile preview is not possible.

## Start Every Task

1. Treat short mobile prompts as enough to begin when the risk is low.
2. Inspect the repository and classify the work before asking questions.
3. Run `scripts/mobile_dev.py detect --root <workspace> --format markdown` when project shape is unclear.
4. Choose the relevant reference file below and follow it.
5. Run the relevant local commands yourself when safe, including installs, tests, builds, scripts, and dev servers.
6. For browser work, start or reuse the local server, open the target with available browser tooling, capture mobile proof, and keep the server running when the user needs a live preview.
7. Bring important local evidence back into chat: URLs, screenshots, command output, exit codes, generated paths, and errors.
8. For visual work, use Chrome DevTools or the in-app browser when available to open the target, capture screenshots, and inspect console/network status.

## Reference Map

- For public phone previews, local dev servers, ports, ngrok, and screenshots, read `references/web-previews.md`.
- For scripts, CLIs, tests, builds, generated files, and terminal output, read `references/command-proof.md`.
- For Rust, Node, Python, Go, backend, frontend, and app-stack defaults, read `references/stack-playbooks.md`.
- For final response structure and progress updates, read `references/mobile-handoff.md`.
- For visual, mobile viewport, console, artifact, and regression checks, read `references/verification-checklists.md`.

## Helper Script

Use `scripts/mobile_dev.py` for repeatable mobile-dev support:

```bash
python scripts/mobile_dev.py detect --root . --format markdown
python scripts/mobile_dev.py ngrok-check
python scripts/mobile_dev.py ngrok-preview --port 5173
python scripts/mobile_dev.py handoff --result "..." --preview "..." --proof "..." --next "..."
```

The script is advisory. It does not replace reading the codebase or running the real project commands.

## Non-Negotiables

- Do not tell the user to check the local terminal, browser, file explorer, or desktop without also summarizing the relevant output.
- Do not ask the user to run commands, start servers, open files, refresh browsers, inspect logs, or verify UI when Codex can safely do it locally.
- Do not use Cloudflare Tunnel, localtunnel, router setup, VS Code ports, or other tunnel fallbacks. Use `ngrok http <port>` only for public phone previews.
- For public phone previews, prefer `scripts/mobile_dev.py ngrok-preview --port <port>` so the real forwarding URL is extracted from the local ngrok API and failures are reported consistently.
- If ngrok is missing, unauthenticated, or fails, report the exact failed command, key error lines, process/log status, and the smallest setup action.
- For UI work, verify with a browser-rendered page and a mobile viewport or mobile-sized screenshot before claiming completion when tooling makes that possible.
- When Chrome DevTools or the in-app browser is available, check console messages and network requests after visual changes; fix actionable errors before final handoff.
- For CLI/script work, run the command when safe and include exit code plus decisive stdout/stderr lines.
- Ask only targeted questions that materially change the implementation, expose data publicly, require credentials the user has not provided, or avoid destructive/external side effects.
