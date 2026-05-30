# MobileCodex

[![GitHub stars](https://img.shields.io/github/stars/SPDUK/MobileCodex?style=social)](https://github.com/SPDUK/MobileCodex/stargazers)
[![Codex Mobile](https://img.shields.io/badge/Codex-Mobile-111827)](https://chatgpt.com/codex/mobile/)
[![LLM friendly](https://img.shields.io/badge/LLM-friendly_llms.txt-0b6bcb)](llms.txt)
[![Python](https://img.shields.io/badge/Python-3.x-3776ab)](skills/mobile-codex-dev/scripts/mobile_dev.py)

**The support layer for [Codex Mobile](https://chatgpt.com/codex/mobile/): session snapshots, tracked previews, UX proof, proof bundles, and phone-readable handoffs.**

MobileCodex helps Codex users keep real software work moving from a phone. It teaches Codex to inspect the repo, run the right commands, start and track local preview servers, capture screenshots and logs, bundle proof, and hand back the useful state in chat.

No "check your terminal." No mystery localhost. No giant log dumps. Just the current state, the change, the preview, the proof, and the next useful move.

## Try This From Codex Mobile

Use this prompt from [Codex Mobile](https://chatgpt.com/codex/mobile/) when you want a session to become visible and resumable:

```text
Use $mobile-codex-dev, run doctor, snapshot this workspace, start the preview if safe, capture UX proof, bundle the proof, and give me a phone-readable handoff.
```

For a smaller first check:

```text
Use $mobile-codex-dev to show me the menu, run doctor, and tell me what is ready or blocked.
```

## Why Developers Use It

- **Continue from a phone:** Codex Mobile becomes the control surface while the workspace stays on the development machine.
- **See real state:** Snapshot branch, dirty files, candidate commands, ports, servers, recent proof, and next references.
- **Trust previews:** Start tracked local servers, verify URLs, capture mobile screenshots, and expose ngrok only when safe.
- **Keep proof:** Save screenshots, logs, changed files, command output, and server state into one reviewable bundle.
- **Resume cleanly:** End every session with result, preview, proof, state, and next action.

## Examples

- [Frontend preview handoff](examples/frontend-preview-handoff.md)
- [Bugfix from phone](examples/bugfix-from-phone.md)
- [UX proof report](examples/ux-proof-report.md)
- [Session snapshot](examples/session-snapshot.md)
- [Proof bundle](examples/proof-bundle.md)

## Guides

- [Codex Mobile handoff workflow](docs/codex-mobile-handoff.md)
- [Mobile preview workflow](docs/mobile-preview-workflow.md)
- [Server registry](docs/server-registry.md)
- [UX proof examples](docs/ux-proof-examples.md)
- [Proof bundle examples](docs/proof-bundle-examples.md)

## Looking For Feedback

MobileCodex is especially useful to test with real Codex Mobile workflows. Feedback is welcome from:

- people using Codex Mobile away from their laptop
- developers who need local previews visible from a phone
- skill authors building repeatable Codex workflows
- teams that need proof artifacts and resumable handoffs

Open an issue using the templates in this repo, or start a discussion with the prompt, project type, what worked, what failed, and what proof would have made the handoff easier to trust.

## Step 1: Use Codex From Anywhere

MobileCodex is built as the practical partner workflow for [Work with Codex from anywhere](https://openai.com/index/work-with-codex-from-anywhere/) and [Codex Mobile](https://chatgpt.com/codex/mobile/). Codex Mobile gives you access to the live development environment from your phone; this skill makes that environment behave like a continuous, inspectable work session instead of a black box.

Use it when your phone is the control surface and Codex needs to:

- inspect the repo before asking questions
- run safe commands and summarize the output
- start local servers and report their status
- create an ngrok phone preview when safe
- capture browser proof and screenshots
- keep local state visible while work continues
- create session snapshots, proof bundles, and registered server handoffs
- return a compact mobile handoff

## Preflight: Run Doctor

Before relying on phone previews, run the setup doctor once on the machine Codex controls:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py doctor --root .
```

Doctor checks the practical setup pieces that make away-from-laptop work dependable:

- Python, Node/npm, and git availability
- `ngrok` installation and local authtoken configuration
- Playwright/browser proof tooling
- common preview ports
- session snapshot readiness
- server registry health
- proof directory health
- installed skill copy drift
- mobile UX proof readiness
- required skill files and Codex skill validation when the local validator exists
- README install path and first-time setup copy

If something is missing, doctor reports the blocker in the same mobile handoff style Codex should use later. For example, if `ngrok` is not installed, it explains that you need an ngrok account, the local ngrok agent, and `ngrok config add-authtoken <token>` before public phone previews can work.

## Why It Feels Different

Most coding workflows assume you can see the desktop, browser, terminal, and file tree. MobileCodex flips that assumption.

Codex should do the local work itself, then bring the important evidence back to you:

- runnable commands and exit codes
- concise stdout/stderr summaries
- browser screenshots for visual changes
- local server status and ports
- session snapshots for resumable state
- server registry entries with PID, port, URL, and log path
- proof bundles with screenshots, logs, changed files, and snapshot state
- `ngrok` phone previews with real URL extraction when safe
- exact blockers when previewing is not possible
- final handoffs that are short enough to read on the go

## The Standard

Every meaningful handoff should answer four things:

```text
Result: what changed, ran, or was created
Preview: what you can open or inspect from your phone
Proof: commands, screenshots, logs, exit codes, or artifact paths
Next: the 1-3 most useful follow-up options
```

That simple contract is the product. It keeps Codex accountable, keeps you unblocked, and makes remote development feel continuous instead of blurry.

## Continuation Contract

Codex Mobile is the control surface; the workspace stays on the machine Codex is already using. This skill pushes Codex to:

- keep working unless approval, sensitive exposure, destructive side effects, or a real blocker stops it
- make local state visible in chat with URLs, screenshots, output, paths, ports, process status, and errors
- label previews and artifacts so multiple mobile Codex sessions stay easy to distinguish
- leave incomplete work resumable with workspace, branch, changed files, running servers, last proof, last failure, and next action
- ask only targeted approval questions that can be answered from a phone

## Install

Copy the skill folder into your Codex skills directory. Current Codex docs describe local user skills under `~/.agents/skills`; older/local setups may also use `~/.codex/skills`.

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.agents\skills" | Out-Null
Copy-Item -Path .\skills\mobile-codex-dev `
  -Destination "$env:USERPROFILE\.agents\skills" `
  -Recurse -Force
```

On macOS or Linux:

```bash
mkdir -p ~/.agents/skills
cp -R ./skills/mobile-codex-dev ~/.agents/skills/
```

Then start a fresh Codex session or invoke it explicitly:

```text
Use $mobile-codex-dev to keep this moving while I am on my phone and show me proof I can inspect here.
```

## Try It

These prompts are the sweet spot:

```text
Use $mobile-codex-dev to build the UI, run it, and give me a phone preview.
```

```text
Use $mobile-codex-dev to fix the failing tests and summarize the important output.
```

```text
Use $mobile-codex-dev to inspect this repo, choose the safest next step, and show proof.
```

```text
Use $mobile-codex-dev to finish this CLI and run a realistic sample command.
```

## What Can I Ask For?

Run the capability menu any time you want the current list of MobileCodex actions:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py menu
```

The menu is designed for phone handoffs. It shows what to ask, what helper command Codex can run, and what proof or state comes back.

| Ask for                                      | What Codex should do                                                                                      | Helper command                                            |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| "Show me the current session state."         | Summarize workspace, branch, changed files, ports, servers, recent proof, and suggested references.       | `snapshot --root .`                                       |
| "Start the app preview and keep it visible." | Start a tracked local server with PID, port, URL, command, and log path.                                  | `server-start --root . --name app --port <port> -- <cmd>` |
| "What previews are still running?"           | List MobileCodex-owned preview servers and status.                                                        | `server-list --root .`                                    |
| "Capture mobile proof for this page."        | Save mobile and desktop screenshots, plus browser evidence when local Playwright is available.            | `ux-proof --root . --url <local-url>`                     |
| "Bundle the proof so I can review later."    | Create one `proof.md` with snapshot state, artifacts, logs, changed files, and server state.              | `proof-bundle --root .`                                   |
| "Check if this machine is ready."            | Run readiness checks for runtimes, ngrok, proof tooling, registry health, proof storage, and skill drift. | `doctor --root .`                                         |
| "Give me a safe phone preview URL."          | Start ngrok only after local verification and safety checks, then report the real forwarding URL.         | `ngrok-preview --port <port>`                             |
| "Summarize where we landed."                 | Produce a compact Result / Preview / Proof / State / Next handoff.                                        | `handoff ...`                                             |

## What It Covers

| Workflow               | What Codex is guided to do                                                                                                                                    |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Frontend apps          | Start or reuse the dev server, verify in browser, capture mobile screenshots, summarize console/network issues, and keep preview servers running when useful. |
| Backend APIs           | Run tests or a local service, exercise representative endpoints, report status codes and key responses.                                                       |
| CLIs and scripts       | Run safe sample commands, include exit codes, summarize decisive stdout/stderr, report generated files.                                                       |
| Rust, Go, Python, Node | Prefer local project scripts and standard verification commands for each stack.                                                                               |
| Session snapshots      | Summarize workspace, branch, dirty files, detected stack, ports, registered servers, and recent proof artifacts.                                              |
| Server registry        | Track Codex-started preview servers with PID, port, URL, command, and log path outside git.                                                                   |
| Proof bundles          | Gather snapshot state, artifacts, server status, changed files, and log tails into one `proof.md`.                                                            |
| Mobile UX proof        | Capture mobile and desktop screenshots with Playwright tooling, plus browser metadata when available.                                                         |
| Mobile handoffs        | Keep progress updates and final replies concise, evidence-backed, resumable, and useful from a phone.                                                         |
| Public previews        | Use `ngrok http <port>` only, after local verification and safety checks, with helper-based URL extraction.                                                   |

## Public Preview Policy

MobileCodex intentionally uses one tunnel provider: `ngrok`.

That keeps preview behavior predictable. It also prevents Codex from reaching for random tunnel services, deployment shortcuts, router changes, or editor-specific port forwarding.

If `ngrok` is missing, unauthenticated, rate limited, or unsafe for the current app, Codex should say exactly what blocked it and still provide local proof where possible.

For public previews, the helper command starts ngrok, polls the local ngrok API, extracts the real forwarding URL for the requested port, reports the process/log status, and leaves the tunnel running when successful:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ngrok-preview --port 5173
```

## Repository

```text
MobileCodex/
|-- README.md
|-- index.html
|-- .gitignore
`-- skills/
    `-- mobile-codex-dev/
        |-- SKILL.md
        |-- agents/
        |   `-- openai.yaml
        |-- references/
        |   |-- command-proof.md
        |   |-- mobile-handoff.md
        |   |-- stack-playbooks.md
        |   |-- verification-checklists.md
        |   `-- web-previews.md
        `-- scripts/
            `-- mobile_dev.py
```

The root `index.html` is a single-file demo page for the skill. The skill itself lives entirely under `skills/mobile-codex-dev`, with `SKILL.md` at that folder root.

## Helper CLI

The bundled helper is intentionally small. It gives Codex quick, repeatable checks without replacing normal engineering judgment.

Show the phone-readable capability menu:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py menu
```

Run first-time setup checks:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py doctor --root .
```

Detect project shape:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py detect --root . --format markdown
```

Create a resumable session snapshot:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py snapshot --root . --format markdown
```

Start, inspect, and stop a registered preview server:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-start --root . --name app --port 8000 -- py -m http.server 8000 --bind 127.0.0.1
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-list --root .
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-stop --root . --name app
```

Create a proof bundle:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --format markdown
```

Capture mobile UX proof for a local preview:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ux-proof --root . --url http://127.0.0.1:8000/index.html
```

When a project has a local Playwright dependency, `ux-proof` can collect console, failed request, and horizontal-scroll checks. Without a local dependency, it uses the `npx playwright screenshot` path for screenshot proof and basic page metadata.

Check `ngrok` availability:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ngrok-check
```

Start an ngrok phone preview and extract the real forwarding URL:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ngrok-preview --port 5173
```

Format a compact handoff:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py handoff `
  --result "Updated the CLI parser" `
  --preview "CLI output summarized below" `
  --proof "tests exited 0" `
  --state "No servers left running" `
  --next "Add JSON output"
```

## Validate

Run the Codex skill validator:

```powershell
$validator = "$env:USERPROFILE\.codex\skills\.system\skill-creator\scripts\quick_validate.py"
if (Test-Path $validator) {
  py $validator .\skills\mobile-codex-dev
}
```

Compile-check the helper:

```powershell
py -m py_compile .\skills\mobile-codex-dev\scripts\mobile_dev.py
```

## Design Notes

This skill is intentionally lean:

- `SKILL.md` holds the core behavior and routing.
- `references/` holds deeper playbooks that Codex loads only when needed.
- `scripts/mobile_dev.py` handles repeatable inspection and handoff formatting.
- local Codex installs, caches, screenshots, logs, and secrets stay out of git.

## License

MIT License. See [LICENSE](LICENSE).
