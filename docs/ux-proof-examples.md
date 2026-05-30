# UX Proof Examples For Mobile Web Work

`ux-proof` captures browser evidence for Codex Mobile sessions where visual correctness matters.

## Capture Mobile And Desktop Proof

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ux-proof --root . --url http://127.0.0.1:5173
```

## Capture Mobile Only

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py ux-proof --root . --url http://127.0.0.1:5173 --mobile-only
```

## Reported Evidence

- Mobile screenshot at `390x844`.
- Desktop screenshot unless `--mobile-only` is passed.
- Page title and final URL.
- Console warnings and errors when Playwright tooling is available.
- Failed network requests when available.
- Basic horizontal-scroll check.

## Handoff Use

UX proof replaces vague visual claims with screenshots and browser evidence that the user can inspect from a phone.

