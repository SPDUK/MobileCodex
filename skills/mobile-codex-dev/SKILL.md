---
name: mobile-codex-dev
description: Mobile-first software engineering workflow for Codex users working from a phone or away from their PC. Use when the user is on mobile, wants an on-the-go coding experience, asks for phone previews, asks for ngrok, needs screenshots/logs in chat, or needs Codex to build, run, verify, and summarize software work without requiring desktop terminal or browser access. Applies to frontend apps, backend services, Rust/Go/Python/Node CLIs, scripts, tests, builds, and anything in between.
---

# Mobile Codex Dev

Engineer as if the user cannot inspect the desktop, terminal, browser, files, or long logs. Favor autonomous progress, runnable proof, compact handoffs, mobile screenshots when visual output exists, and exact blockers when mobile preview is not possible.

## Start Every Task

1. Treat short mobile prompts as enough to begin when the risk is low.
2. Inspect the repository and classify the work before asking questions.
3. Run `scripts/mobile_dev.py detect --root <workspace> --format markdown` when project shape is unclear.
4. Choose the relevant reference file below and follow it.
5. Bring important local evidence back into chat: URLs, screenshots, command output, exit codes, generated paths, and errors.

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
python scripts/mobile_dev.py handoff --result "..." --preview "..." --proof "..." --next "..."
```

The script is advisory. It does not replace reading the codebase or running the real project commands.

## Non-Negotiables

- Do not tell the user to check the local terminal, browser, file explorer, or desktop without also summarizing the relevant output.
- Do not use Cloudflare Tunnel, localtunnel, router setup, VS Code ports, or other tunnel fallbacks. Use `ngrok http <port>` only for public phone previews.
- If ngrok is missing, unauthenticated, or fails, report the exact failed command, key error lines, and the smallest setup action.
- For UI work, verify with a mobile viewport or mobile-sized screenshot before claiming completion when tooling makes that possible.
- For CLI/script work, run the command when safe and include exit code plus decisive stdout/stderr lines.
- Ask only targeted questions that materially change the implementation, expose data publicly, or avoid destructive/external side effects.
