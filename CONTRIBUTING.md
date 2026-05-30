# Contributing To MobileCodex

MobileCodex is a support skill for Codex Mobile. Contributions are most useful when they improve away-from-laptop agent work: clearer state, safer previews, better proof, cleaner handoffs, or easier installation.

## Good First Contributions

- Add a real workflow example under `examples/`.
- Improve README copy for a specific Codex Mobile use case.
- Add a doctor check for a common setup blocker.
- Improve snapshot, server registry, proof bundle, or UX proof output.
- Report where a mobile handoff was confusing or missing proof.

## Feedback Reports

When reporting feedback, include:

- Operating system and shell.
- Project type, such as Vite, Next.js, Python CLI, Rust service, or static HTML.
- The Codex Mobile prompt you used.
- The MobileCodex command or workflow involved.
- The result, blocker, or confusing part.
- Any proof path, screenshot, log tail, or server registry output that helps reproduce the issue.

## Development Checks

Run these before opening a pull request:

```powershell
py -m py_compile .\skills\mobile-codex-dev\scripts\mobile_dev.py
py .\skills\mobile-codex-dev\scripts\mobile_dev.py doctor --root . --format markdown
git diff --check
```

If you change the landing page, also serve it locally and inspect the mobile viewport:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-start --root . --name site --port 8033 -- py -m http.server 8033 --bind 127.0.0.1
```

Then open `http://127.0.0.1:8033/index.html`, check the browser console, and stop the registered server:

```powershell
py .\skills\mobile-codex-dev\scripts\mobile_dev.py server-stop --root . --name site
```

## Pull Request Shape

Keep pull requests focused. A strong PR usually includes:

- The user-facing mobile problem.
- The command, doc, or workflow changed.
- The proof that it works.
- Any known limitations.

