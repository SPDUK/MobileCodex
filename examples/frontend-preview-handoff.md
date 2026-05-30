# Example: Frontend Preview Handoff

This example shows how MobileCodex can make a local web UI visible from Codex Mobile.

## Phone Prompt

```text
Use $mobile-codex-dev to start the app preview, capture mobile proof, and give me a phone-readable handoff.
```

## What Codex Should Do

1. Inspect the project shape.
2. Start the local preview through the server registry.
3. Confirm the local URL responds.
4. Capture mobile UX proof.
5. Report the server status, screenshot paths, console/network issues, and next action.

## Representative Commands

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-start --root . --name app --port 5173 -- npm run dev -- --host 127.0.0.1 --port 5173
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-list --root .
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ux-proof --root . --url http://127.0.0.1:5173
```

## Handoff Shape

```text
Result: Started the app preview and verified the page renders.
Preview: Local preview is http://127.0.0.1:5173. Public phone URL is not exposed unless requested and safe.
Proof: Mobile screenshot and desktop screenshot saved under proof/mobilecodex-ux-YYYYMMDD-HHMMSS/.
State: Server registry has app on port 5173 with PID, command, URL, and log path.
Next: Review the screenshot, ask for ngrok if you need a phone URL, or ask me to keep iterating.
```

## Why This Helps From Mobile

The user does not need to see the laptop browser, terminal, or process list. The preview server is tracked, the proof is saved, and the handoff explains exactly what is running.

