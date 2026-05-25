# Stack Playbooks

Use these defaults after inspecting the repo. Prefer project scripts and local conventions over generic commands.

## Detection Order

1. Read manifests and lockfiles.
2. Read existing scripts, Makefiles, task runners, justfiles, CI files, and docs.
3. Use `scripts/mobile_dev.py detect --root <workspace> --format markdown` for a quick inventory.
4. Use framework or SDK docs tools when API details may have changed.

## Frontend Web

Signals:
- `package.json`, `vite.config.*`, `next.config.*`, `astro.config.*`, `svelte.config.*`, `angular.json`

Default proof:
- install status if dependencies are missing
- typecheck, lint, or build command from project scripts
- local server screenshot at mobile width
- console error summary
- ngrok URL when phone preview is requested and safe

Common commands:
- `npm run dev`, `pnpm dev`, `yarn dev`, or project equivalent
- `npm run build`
- `npm test` or project equivalent

## Backend Web And APIs

Signals:
- server manifests, route files, OpenAPI files, framework config, Docker Compose, `.env.example`

Default proof:
- local server starts or tests pass
- health endpoint or representative request output
- API response excerpt, status code, and route tested
- ngrok only if the user needs phone access to a browser UI or API endpoint

Do not expose private local APIs through ngrok without checking for sensitive data or write actions.

## Rust CLI Or Service

Signals:
- `Cargo.toml`, `Cargo.lock`, `src/main.rs`, `src/lib.rs`

Default proof:
- `cargo test`
- `cargo run -- <safe sample args>` when a CLI exists
- `cargo clippy -- -D warnings` when clippy is installed and the project already uses it
- generated output or stdout excerpt

Mobile handoff should include a runnable example command and the actual output.

## Node Or TypeScript CLI

Signals:
- `package.json` with `bin`, `tsx`, `ts-node`, `commander`, `oclif`, or CLI scripts

Default proof:
- package manager script for test/build/typecheck
- run the CLI with `--help` or safe sample input
- include stdout excerpt and generated artifact paths

If the package manager is ambiguous, infer from lockfiles in this order: `pnpm-lock.yaml`, `yarn.lock`, `package-lock.json`, then `npm`.

## Python Script Or Package

Signals:
- `pyproject.toml`, `requirements.txt`, `setup.py`, `uv.lock`, `.python-version`

Default proof:
- run tests with the project runner when configured
- run the script/module with safe sample input
- include stdout/stderr and generated paths

On Windows, prefer `py -m ...` when the plain `python` command is a Store shim or unavailable.

## Go CLI Or Service

Signals:
- `go.mod`, `main.go`, `cmd/`

Default proof:
- `go test ./...`
- `go run .` or `go run ./cmd/<name>` with safe sample args
- include stdout and exit code

## Native Or Cross-Platform Mobile Apps

Signals:
- `app.json`, `expo`, `react-native`, `pubspec.yaml`, `android/`, `ios/`, `build.gradle`, `Package.swift`

Default proof:
- static checks or tests available in scripts
- screenshots or simulator/browser previews when available
- mobile viewport web preview if the app has a web build

Do not claim device verification unless an actual simulator, emulator, web build, or screenshot proof was used.

## Docs, Generated Assets, And Reports

Default proof:
- render or inspect generated output when possible
- include key excerpt, page count, table count, image dimensions, or validation output
- provide absolute artifact paths

If the artifact is visual, include a screenshot or rendered preview in the final response.
