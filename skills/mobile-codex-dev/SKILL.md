---
name: mobile-codex-dev
description: First-class continuation workflow for Codex Mobile users working from a phone or away from their computer. Use when the user is on mobile, wants to keep a Codex session moving, needs visible progress, asks for phone previews or ngrok, needs screenshots/logs/browser proof in chat, or needs Codex to build, run, verify, start servers, inspect output, and summarize software work without relying on laptop access. Applies to frontend apps, backend services, Rust/Go/Python/Node CLIs, scripts, tests, builds, documents, slides, spreadsheets, browser work, desktop-app work, and multi-session handoffs.
---

# Mobile Codex Dev

Engineer as if Codex Mobile at `https://chatgpt.com/codex/mobile/` is the user's primary control surface while the real workspace keeps running elsewhere. This skill does not replace Codex; it makes Codex feel continuous from mobile by keeping work moving, making local state visible in chat, and leaving each step resumable.

Codex Mobile is a continuation surface, not a separate environment. Use the existing workspace, files, plugins, browser sessions, credentials already available in the active machine context, and project configuration. Do not make the user return to the laptop just to inspect routine state.

Assume Codex must inspect the repo, make safe local decisions, run commands, start servers, open browser previews, capture proof, and report the result in chat. Favor autonomous progress, runnable proof, compact handoffs, mobile screenshots when visual output exists, and exact blockers when mobile preview is not possible.

## Start Every Task

1. Treat short mobile prompts as enough to begin when the risk is low.
2. Inspect the repository and classify the work before asking questions.
3. For first-time setup, preview failures, or missing-tool suspicion, run `scripts/mobile_dev.py doctor --root <workspace> --format markdown` and report the action_required items.
4. Run `scripts/mobile_dev.py snapshot --root <workspace> --format markdown` when resuming, pausing, or handing off incomplete work.
5. Run `scripts/mobile_dev.py detect --root <workspace> --format markdown` when project shape is unclear.
6. Choose the relevant reference file below and follow it.
7. Run the relevant local commands yourself when safe, including installs, tests, builds, scripts, and dev servers.
8. For browser work, use `server-start`/`server-list` for preview servers when practical, run `ux-proof` when Playwright tooling is available, and keep the server running when the user needs a live preview.
9. Keep the phone view useful throughout the task: send concise progress updates for milestones, decisions, approvals needed, preview URLs, screenshots, failing commands, and blockers.
10. For visual work, use Chrome DevTools or the in-app browser when available to open the target, capture screenshots, and inspect console/network status.
11. Bring important local evidence back into chat: URLs, screenshots, command output, exit codes, generated paths, background process status, and errors.
12. Before stopping, leave the thread resumable from mobile: state what is done, what is running, what can be opened, what remains, and the safest next action.

## Mobile Continuation Contract

- Keep working unless the next step needs approval, would expose sensitive data publicly, would cause destructive or external side effects, or is genuinely blocked.
- Prefer phone-visible proof over instructions to inspect the machine. Show the relevant terminal lines, browser screenshots, artifact paths, and app URLs in chat.
- Maintain orientation across interruptions. Name the active workspace, branch when relevant, task status, changed files, commands run, and any server/tunnel left running.
- Make approvals easy from mobile. Ask one concise question with the exact command or action being approved and the risk it carries.
- Support multiple sessions by labeling previews, servers, artifacts, and handoffs with the project or workspace name when ambiguity is possible.
- Use automations or heartbeat follow-ups when the user asks you to check back, keep an eye on a long run, or resume this thread later.
- For Computer Use, logged-in websites, desktop apps, documents, slides, spreadsheets, or files on the machine, operate them directly when the tool is available and report visible state back to chat.

## Reference Map

- For public phone previews, local dev servers, ports, ngrok, and screenshots, read `references/web-previews.md`.
- For scripts, CLIs, tests, builds, generated files, and terminal output, read `references/command-proof.md`.
- For Rust, Node, Python, Go, backend, frontend, and app-stack defaults, read `references/stack-playbooks.md`.
- For progress updates, resumable status, and final response structure, read `references/mobile-handoff.md`.
- For visual, mobile viewport, console, artifact, and regression checks, read `references/verification-checklists.md`.

## Helper Script

Use `scripts/mobile_dev.py` for repeatable mobile-dev support:

```bash
python scripts/mobile_dev.py doctor --root . --format markdown
python scripts/mobile_dev.py snapshot --root . --format markdown
python scripts/mobile_dev.py detect --root . --format markdown
python scripts/mobile_dev.py server-start --root . --name app --port 5173 -- npm run dev -- --host 127.0.0.1
python scripts/mobile_dev.py server-list --root . --format markdown
python scripts/mobile_dev.py server-stop --root . --name app
python scripts/mobile_dev.py proof-bundle --root . --format markdown
python scripts/mobile_dev.py ux-proof --root . --url http://127.0.0.1:5173 --format markdown
python scripts/mobile_dev.py ngrok-check
python scripts/mobile_dev.py ngrok-preview --port 5173
python scripts/mobile_dev.py handoff --result "..." --preview "..." --proof "..." --state "..." --next "..."
```

The script is advisory. It does not replace reading the codebase or running the real project commands.

## Non-Negotiables

- Do not tell the user to check the local terminal, browser, file explorer, or desktop without also summarizing the relevant output.
- Do not ask the user to run commands, start servers, open files, refresh browsers, inspect logs, or verify UI when Codex can safely do it locally.
- Do not leave a mobile user without a resumable state summary when work is incomplete, blocked, or still running.
- Run doctor before first-time public preview setup or when tool availability is unclear; if it reports action_required, give the user the exact setup step rather than a vague dependency complaint.
- Do not use Cloudflare Tunnel, localtunnel, router setup, VS Code ports, or other tunnel fallbacks. Use `ngrok http <port>` only for public phone previews.
- For public phone previews, prefer `scripts/mobile_dev.py ngrok-preview --port <port>` so the real forwarding URL is extracted from the local ngrok API and failures are reported consistently.
- If ngrok is missing, unauthenticated, or fails, report the exact failed command, key error lines, process/log status, and the smallest setup action.
- For UI work, verify with a browser-rendered page and a mobile viewport or mobile-sized screenshot before claiming completion when tooling makes that possible.
- When Chrome DevTools or the in-app browser is available, check console messages and network requests after visual changes; fix actionable errors before final handoff.
- For CLI/script work, run the command when safe and include exit code plus decisive stdout/stderr lines.
- Ask only targeted questions that materially change the implementation, expose data publicly, require credentials the user has not provided, or avoid destructive/external side effects.
