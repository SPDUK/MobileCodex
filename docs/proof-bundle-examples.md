# Proof Bundle Examples

Proof bundles are useful when a Codex Mobile session spans multiple files, commands, screenshots, or servers.

## Create A Bundle

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --format markdown
```

## Include Logs

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --log-file .\test-output.log --format markdown
```

## Include Extra Artifacts

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py proof-bundle --root . --include .\proof\mobile.png --format markdown
```

## What The User Gets

The bundle gives the user one `proof.md` file with snapshot state, changed files, server registry state, recent artifacts, safe copied screenshots, and optional log tails.

