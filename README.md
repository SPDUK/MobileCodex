# Mobile Codex Dev

Mobile Codex Dev is a Codex skill for building software when the user is working from a phone, away from their PC, or relying on Codex to be their eyes on the local machine.

It makes Codex prioritize runnable proof, mobile-friendly previews, concise logs, screenshots, and self-contained handoffs across web apps, APIs, CLIs, scripts, tests, builds, and generated artifacts.

## What This Adds

Most coding agents assume the user can inspect the desktop, terminal, browser, and filesystem. This skill flips that default:

- Codex should run safe commands itself instead of asking the user to run them.
- Codex should summarize terminal output in chat instead of saying "check the logs."
- Codex should provide `ngrok` phone previews for web work when safe and available.
- Codex should capture mobile screenshots or visual proof for UI work.
- Codex should include exact blockers when mobile preview is not possible.
- Codex should keep replies compact enough to use on the go.

## Feature Overview

| Area | Behavior |
| --- | --- |
| Mobile-first work style | Treat short mobile prompts as enough to begin when risk is low. |
| Web previews | Start/reuse local dev servers, verify locally, then expose with `ngrok http <port>` only. |
| Visual proof | Prefer mobile viewport screenshots and console summaries for UI changes. |
| CLI/script proof | Run safe commands, capture exit codes, summarize stdout/stderr, and report generated paths. |
| Stack playbooks | Covers frontend web, backend APIs, Rust, Node/TypeScript, Python, Go, native/mobile apps, and docs. |
| Handoff format | Final replies include result, preview, proof, and next options. |
| Helper tooling | `scripts/mobile_dev.py` detects project shape, checks ngrok, and formats handoffs. |

## What The Reference Repo Has That We Still Do Not

The example project, [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill), is a larger packaged ecosystem. It includes several things this project does not currently replicate:

| Reference repo capability | Current Mobile Codex Dev status |
| --- | --- |
| Large root `README.md` with install, usage, examples, and advanced commands | Added here. |
| Root package metadata such as `skill.json` | Not yet added; Codex uses `agents/openai.yaml` inside the skill. |
| Dedicated CLI package with install/update/uninstall commands | Not yet added; current helper script is local and lightweight. |
| Large searchable data tables | Not needed yet; current references are curated playbooks. |
| Preview demo artifacts and screenshots | Not yet added; future versions can include example mobile proof reports. |
| GitHub workflows and release packaging | Not yet added. |
| Multiple platform templates | Not needed yet; this skill is Codex-first. |
| Extra docs folder | Not needed yet; reference docs live inside the skill. |

The immediate priority is a Codex-native skill that works well from mobile. Packaging, screenshots, and a full installer can be added once the workflow stabilizes.

## Project Structure

```text
MobileCodex/
├── README.md
└── skills/
    └── mobile-codex-dev/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── references/
        │   ├── command-proof.md
        │   ├── mobile-handoff.md
        │   ├── stack-playbooks.md
        │   ├── verification-checklists.md
        │   └── web-previews.md
        └── scripts/
            └── mobile_dev.py
```

The installed auto-discovered copy also lives at:

```text
C:\Users\slush\.codex\skills\mobile-codex-dev
```

## Installation

### Project Copy

The source copy is kept in this repo:

```text
C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev
```

### Codex Auto-Discovery

Codex discovers user skills from:

```text
C:\Users\slush\.codex\skills
```

To sync the project copy into the installed location on Windows PowerShell:

```powershell
Copy-Item -Path C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\* `
  -Destination C:\Users\slush\.codex\skills\mobile-codex-dev `
  -Recurse -Force
```

## Prerequisites

### Python

The helper script uses Python. On this machine, `py` is preferred because `python` may point to the Windows Store shim.

```powershell
py --version
```

### Ngrok

Public phone previews use `ngrok` only.

```powershell
ngrok version
ngrok config add-authtoken <token>
```

If `ngrok` is missing or unauthenticated, the skill should stop the public preview workflow and report the exact blocker. It should not fall back to Cloudflare Tunnel, localtunnel, VS Code port forwarding, or router changes.

## Usage

### Skill Mode

Invoke the skill directly:

```text
Use $mobile-codex-dev to build this feature and show me proof I can inspect from my phone.
```

It should also trigger naturally when the user says things like:

- "I'm on mobile."
- "Show me this on my phone."
- "Use ngrok."
- "Run it and paste the output here."
- "I can't access my PC right now."
- "Make the smallest safe decision and show proof."

### Example Prompts

```text
Use $mobile-codex-dev to build the landing page and give me a phone preview.
```

```text
Use $mobile-codex-dev to finish this Rust CLI and run a realistic sample command.
```

```text
Use $mobile-codex-dev to fix the failing tests and summarize the important logs.
```

```text
Use $mobile-codex-dev to inspect this repo, decide what stack it is, and give me the next mobile-friendly proof step.
```

## How It Works

The main `SKILL.md` stays short so it can load quickly. It points Codex to focused reference files when more detail is needed.

| File | Purpose |
| --- | --- |
| `SKILL.md` | Triggering, core behavior, and non-negotiables. |
| `references/web-previews.md` | Local servers, ngrok-only previews, mobile screenshots, and safety gates. |
| `references/command-proof.md` | Running scripts, CLIs, tests, builds, and summarizing output. |
| `references/stack-playbooks.md` | Stack-specific defaults for web, APIs, Rust, Node, Python, Go, and mobile apps. |
| `references/mobile-handoff.md` | Mobile-friendly progress updates and final response shape. |
| `references/verification-checklists.md` | Proof checklist for UI, CLI, backend, and delivery. |
| `scripts/mobile_dev.py` | Project detection, ngrok checks, and handoff formatting. |

## Helper Commands

Run these from the skill folder or reference the script by absolute path.

### Detect Project Shape

```powershell
py C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\scripts\mobile_dev.py detect --root . --format markdown
```

Example output includes detected stack signals, package manager, candidate commands, candidate ports, and suggested reference files.

### Check Ngrok

```powershell
py C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\scripts\mobile_dev.py ngrok-check
```

Expected blocked output when ngrok is missing:

```text
# Ngrok Check
- Available: False
- Message: ngrok is not installed or not on PATH
- Next: Install ngrok, then run `ngrok config add-authtoken <token>`.
```

### Format A Mobile Handoff

```powershell
py C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\scripts\mobile_dev.py handoff `
  --result "Updated the CLI parser" `
  --preview "CLI output summarized below" `
  --proof "cargo test exited 0" `
  --next "Add JSON output"
```

## Supported Workflows

### Frontend Web

Codex should:

1. Inspect project scripts and framework config.
2. Start or reuse the dev server.
3. Verify locally with browser/proof tooling.
4. Use `ngrok http <port>` only when safe.
5. Capture mobile screenshots when possible.
6. Finalize with URL, screenshot path, build/test output, and console summary.

### Backend APIs

Codex should:

1. Run tests or start the local service.
2. Exercise a representative endpoint.
3. Report status code, response excerpt, and relevant logs.
4. Avoid public tunneling for private or destructive endpoints without asking.

### Rust CLI

Codex should:

1. Run `cargo test` when tests exist.
2. Run a safe sample CLI command.
3. Include stdout/stderr excerpts and exit codes.
4. Report generated file paths or binary output clearly.

### Node And TypeScript CLI

Codex should:

1. Infer the package manager from lockfiles.
2. Run build/test/typecheck scripts when available.
3. Run `--help` or a safe sample command.
4. Summarize output in chat.

### Python Scripts

Codex should:

1. Prefer `py -m ...` on Windows when appropriate.
2. Run tests or safe script samples.
3. Include generated artifact paths and meaningful output.

### Go CLI Or Service

Codex should:

1. Run `go test ./...`.
2. Run `go run .` or the relevant command under `cmd/`.
3. Include command output and exit code.

## Mobile Proof Standard

Every meaningful final reply should answer these four questions:

```text
Result: What changed, ran, or was created?
Preview: What can I open or inspect from my phone?
Proof: What command, screenshot, log, exit code, or artifact proves it?
Next: What are the 1-3 useful follow-up options?
```

For tiny tasks, this can be compressed into one paragraph. The important rule is that the user should not need local desktop access to understand the outcome.

## Safety Rules

Ask before:

- opening a public tunnel to private data, admin screens, destructive flows, or local secrets
- running destructive commands
- touching production systems, billing, email, cloud resources, or external services
- transmitting sensitive data

Do not ask just because the prompt is short. Make low-risk local decisions and state the assumption in the handoff.

## Validation

Validate the skill with:

```powershell
py C:\Users\slush\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev
```

Compile-check the helper script with:

```powershell
py -m py_compile C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\scripts\mobile_dev.py
```

## Troubleshooting

### Codex Does Not Pick Up The Skill

Make sure the installed copy exists:

```text
C:\Users\slush\.codex\skills\mobile-codex-dev\SKILL.md
```

Then start a fresh Codex session or explicitly invoke:

```text
Use $mobile-codex-dev ...
```

### Ngrok Preview Is Blocked

Run:

```powershell
ngrok version
```

If that fails, install ngrok and authenticate:

```powershell
ngrok config add-authtoken <token>
```

The skill should still provide local proof even when public phone preview is blocked.

### Python Command Hangs Or Opens The Store

Use `py` instead of `python` on Windows:

```powershell
py C:\Users\slush\Projects\MobileCodex\skills\mobile-codex-dev\scripts\mobile_dev.py detect --root .
```

## Roadmap

- Add root `skill.json` package metadata if this becomes a distributable skill repo.
- Add a small installer/sync CLI for project-to-user skill syncing.
- Add example proof reports and screenshots.
- Add more stack-specific reference files if repeated mobile workflows need deeper playbooks.
- Add automated validation for reference links and helper command examples.

## License

No license has been selected yet. Add one before publishing or redistributing this project.
