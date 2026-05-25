# Web Previews

Use this when a project has a browser UI, static page, local dev server, Storybook, docs site, API docs UI, or any output the user should open on a phone.

## Workflow

1. Discover the server command and candidate port from package scripts, config files, framework defaults, or running process logs.
2. Start or reuse the local server. Capture command, port, PID or process note, and the first useful ready/error lines.
3. Verify locally before exposing it. Use Codex browser/proof tooling when available.
4. Start `ngrok http <port>` only after the local server responds.
5. Extract the actual `https://...ngrok-free.app` forwarding URL from ngrok output or the ngrok local API. Never invent it.
6. Capture at least one mobile-sized screenshot when visual output matters.
7. Finish with the mobile handoff from `mobile-handoff.md`.

## Ngrok Only Policy

Use `ngrok http <port>` as the only public tunnel provider.

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
Next: install ngrok, then run `ngrok config add-authtoken <token>`.
```

Still provide local proof when available: server logs, local URL, screenshots from localhost, or test output.

## Safety Gate

Ask before opening a public tunnel when the local app shows or can mutate:
- secrets, tokens, API keys, private credentials, or local environment values
- production data, customer data, private documents, or personal data
- admin panels, destructive controls, billing, email sending, deploy buttons, or write-heavy automation

If unsure, verify locally and ask one concise question before tunneling.

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

If a file can be opened directly but the user needs phone preview, serve the directory locally instead of asking them to open the file:

```bash
python -m http.server 8000
ngrok http 8000
```

Report both the local file path and the ngrok URL.
