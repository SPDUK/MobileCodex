# Web Previews

Use this when a project has a browser UI, static page, local dev server, Storybook, docs site, API docs UI, or any output the user should open on a phone. Assume Codex owns the full preview loop because the user cannot reach the laptop. A preview is not complete until the user can tell from chat what is running, what URL is safe to open, and what proof was captured.

## Workflow

1. Discover the server command and candidate port from package scripts, config files, framework defaults, static files, or running process logs.
2. Install dependencies if the project clearly needs them and the install is local, safe, and expected for the stack.
3. Start or reuse the local server. Prefer `scripts/mobile_dev.py server-start --root <workspace> --name <label> --port <port> -- <command...>` so PID, port, URL, and logs are registered.
4. Verify locally before exposing it. Use `scripts/mobile_dev.py ux-proof --root <workspace> --url <local-url>` or Codex browser/proof tooling when available.
5. If this is the first public preview attempt or tooling looks incomplete, run `scripts/mobile_dev.py doctor --root <workspace>` before tunneling.
6. Start the tunnel with `scripts/mobile_dev.py ngrok-preview --port <port>` when the user needs phone access and the safety gate passes. Do this only after the local server responds.
7. Use the extracted `https://...` forwarding URL from the helper output. Never invent a URL or copy a stale URL.
8. Capture at least one mobile-sized screenshot when visual output matters.
9. Label the preview with the workspace/app name when the user may have multiple Codex sessions open.
10. Finish with the mobile handoff from `mobile-handoff.md`, including `server-list` output and whether the tunnel is still running.

## Ngrok Only Policy

Use `ngrok http <port>` as the only public tunnel provider. Prefer the helper wrapper:

```bash
python scripts/mobile_dev.py ngrok-preview --port <port>
```

The helper starts ngrok, polls the local ngrok API, extracts the real forwarding URL for the requested port, reports the process id and log file, and leaves the tunnel running on success.

Do not use:
- Cloudflare Tunnel
- localtunnel
- VS Code forwarded ports
- router or firewall changes
- deployment services as a preview shortcut

If ngrok is not installed, not authenticated, rate limited, or fails:

```text
Preview: blocked because ngrok is not available.
Proof: `ngrok http <port>` failed with: <key error>.
Next: create/sign into an ngrok account, install the ngrok agent, then run `ngrok config add-authtoken <token>` from the ngrok dashboard before a public phone preview can be created.
```

Still provide local proof when available: server logs, local URL, screenshots from localhost, or test output.

## Mobile Preview Continuity

When a public preview is provided, make the phone handoff self-contained:

- include the local URL and the ngrok URL
- state the server command, port, and whether it remains running
- state the tunnel command and whether the tunnel remains running
- include the freshest mobile screenshot path or inline image
- summarize console and network status after the latest reload
- mention if clicking, auth, seed data, or environment setup is required before the phone preview is meaningful

If the preview may expire when the process stops, say so directly.

## Server Registry

Use the registry for preview servers Codex starts:

```bash
python scripts/mobile_dev.py server-start --root . --name app --port 5173 -- npm run dev -- --host 127.0.0.1
python scripts/mobile_dev.py server-list --root .
python scripts/mobile_dev.py server-stop --root . --name app
```

Only stop processes recorded in the registry. If a user already has a server running outside the registry, identify it and report it without claiming registry ownership.

## Safety Gate

Ask before opening a public tunnel when the local app shows or can mutate:
- secrets, tokens, API keys, private credentials, or local environment values
- production data, customer data, private documents, or personal data
- admin panels, destructive controls, billing, email sending, deploy buttons, or write-heavy automation

If unsure, verify locally and ask one concise question before tunneling. Do not stop local verification while waiting for a public tunnel decision.

## Useful Port Hints

Prefer discovered ports over defaults. Defaults are only hints:

| Stack | Common local port |
| --- | --- |
| Next.js, Remix, Rails | 3000 |
| Vite, SvelteKit, Vitest UI | 5173 |
| Astro | 4321 |
| Angular | 4200 |
| Django, FastAPI | 8000 |
| Flask | 5000 |
| Storybook | 6006 |
| Jupyter | 8888 |

## Screenshot Standard

Capture the narrow mobile view first, then desktop only if useful.

Preferred mobile viewport proof:
- 390 x 844 for modern iPhone-like checks
- 375 x 667 for smaller phone checks
- include a screenshot after any key interaction, not only the landing state

Verify:
- no horizontal scroll
- readable text without zoom
- touch targets are not cramped
- fixed headers/footers do not cover content
- console errors are summarized
- loading, empty, and error states are visible when relevant

## Static HTML

If a file can be opened directly, serve the directory locally instead of asking the user to open the file:

```bash
python -m http.server 8000
python scripts/mobile_dev.py ngrok-preview --port 8000
```

Report both the local file path and the ngrok URL.
