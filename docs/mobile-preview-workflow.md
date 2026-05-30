# Mobile Preview Workflow For Codex Mobile

MobileCodex helps Codex start, track, verify, and hand off local previews when the user is on a phone.

## Local Preview First

Start with a local server registered by MobileCodex:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-start --root . --name app --port 5173 -- npm run dev -- --host 127.0.0.1 --port 5173
```

Then inspect it:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-list --root .
```

## Public Phone Preview

Only expose a public tunnel after the local preview works and the app is safe to expose:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ngrok-preview --port 5173
```

## Handoff

The handoff should include the local URL, optional ngrok URL, server registry state, log file path, screenshot path, and blocker if a public tunnel is not available.

