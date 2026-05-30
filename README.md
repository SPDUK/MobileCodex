# Mobile Codex Dev

**A first-class continuation skill for Codex Mobile.**

Mobile Codex Dev supports [Codex Mobile](https://chatgpt.com/codex/mobile/) by teaching Codex to keep the same desktop workspace moving while your phone is the control surface. It inspects the repo, runs the right commands, verifies the result, captures proof, and hands back the useful bits in a phone-readable format.

No "check your terminal." No mystery localhost. No giant log dumps. Just the current state, the change, the preview, the proof, and the next useful move.

## Step 1: Use Codex From Anywhere

Mobile Codex Dev is built as the practical partner workflow for [Work with Codex from anywhere](https://openai.com/index/work-with-codex-from-anywhere/) and [Codex Mobile](https://chatgpt.com/codex/mobile/). Codex Mobile gives you access to the live development environment from your phone; this skill makes that environment behave like a continuous, inspectable work session instead of a black box.

Use it when your phone is the control surface and Codex needs to:

- inspect the repo before asking questions
- run safe commands and summarize the output
- start local servers and report their status
- create an ngrok phone preview when safe
- capture browser proof and screenshots
- keep local state visible while work continues
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
- required skill files and Codex skill validation when the local validator exists
- README install path and first-time setup copy

If something is missing, doctor reports the blocker in the same mobile handoff style Codex should use later. For example, if `ngrok` is not installed, it explains that you need an ngrok account, the local ngrok agent, and `ngrok config add-authtoken <token>` before public phone previews can work.

## Why It Feels Different

Most coding workflows assume you can see the desktop, browser, terminal, and file tree. Mobile Codex Dev flips that assumption.

Codex should do the local work itself, then bring the important evidence back to you:

- runnable commands and exit codes
- concise stdout/stderr summaries
- browser screenshots for visual changes
- local server status and ports
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

## What It Covers

| Workflow | What Codex is guided to do |
| --- | --- |
| Frontend apps | Start or reuse the dev server, verify in browser, capture mobile screenshots, summarize console/network issues, and keep preview servers running when useful. |
| Backend APIs | Run tests or a local service, exercise representative endpoints, report status codes and key responses. |
| CLIs and scripts | Run safe sample commands, include exit codes, summarize decisive stdout/stderr, report generated files. |
| Rust, Go, Python, Node | Prefer local project scripts and standard verification commands for each stack. |
| Mobile handoffs | Keep progress updates and final replies concise, evidence-backed, resumable, and useful from a phone. |
| Public previews | Use `ngrok http <port>` only, after local verification and safety checks, with helper-based URL extraction. |

## Public Preview Policy

Mobile Codex Dev intentionally uses one tunnel provider: `ngrok`.

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

Run first-time setup checks:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py doctor --root .
```

Detect project shape:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py detect --root . --format markdown
```

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

No license has been selected yet. Add one before publishing or redistributing this project.
