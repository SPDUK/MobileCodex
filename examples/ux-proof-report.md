# Example: UX Proof Report

This example shows how MobileCodex verifies a visual change for a phone-sized viewport.

## Phone Prompt

```text
Use $mobile-codex-dev to capture UX proof for the local preview and tell me if there are console errors, failed requests, or horizontal scroll.
```

## What Codex Should Do

1. Confirm a local preview URL responds.
2. Run `ux-proof` against the URL.
3. Capture a `390x844` mobile screenshot.
4. Capture a desktop screenshot unless mobile-only proof was requested.
5. Report console warnings/errors, failed requests, final URL, page title, and horizontal-scroll status.

## Representative Command

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ux-proof --root . --url http://127.0.0.1:5173
```

## Handoff Shape

```text
Result: Captured mobile and desktop UX proof for the preview.
Preview: Local page verified at http://127.0.0.1:5173.
Proof: Screenshots saved under proof/mobilecodex-ux-YYYYMMDD-HHMMSS/. Console errors: none. Failed requests: none. Horizontal scroll: none detected.
State: Preview server remains registered on port 5173.
Next: Review the screenshot or ask for another viewport.
```

## Why This Helps From Mobile

Visual feedback becomes concrete. The user can inspect screenshots and issues directly in chat instead of trusting a vague "looks good."

