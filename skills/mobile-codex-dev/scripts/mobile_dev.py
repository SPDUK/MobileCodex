#!/usr/bin/env python3
"""Utilities for the mobile-codex-dev skill.

The commands are intentionally read-only except for printing formatted output.
They help Codex quickly inspect a project, run setup checks, check ngrok
availability, and format a compact mobile handoff.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


KNOWN_PORTS = {
    "next": 3000,
    "next.js": 3000,
    "remix": 3000,
    "vite": 5173,
    "sveltekit": 5173,
    "astro": 4321,
    "angular": 4200,
    "storybook": 6006,
    "django": 8000,
    "fastapi": 8000,
    "flask": 5000,
    "rails": 3000,
    "jupyter": 8888,
}

DEFAULT_NGROK_API_URL = "http://127.0.0.1:4040/api/tunnels"
COMMON_PORTS = [3000, 4200, 4321, 5000, 5173, 6006, 8000, 8080, 8888]
REQUIRED_SKILL_FILES = [
    "SKILL.md",
    "agents/openai.yaml",
    "references/command-proof.md",
    "references/mobile-handoff.md",
    "references/stack-playbooks.md",
    "references/verification-checklists.md",
    "references/web-previews.md",
    "scripts/mobile_dev.py",
]


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def file_exists(root: Path, *names: str) -> bool:
    return any((root / name).exists() for name in names)


def detect_package_manager(root: Path) -> str | None:
    if (root / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (root / "yarn.lock").exists():
        return "yarn"
    if (root / "bun.lockb").exists() or (root / "bun.lock").exists():
        return "bun"
    if (root / "package-lock.json").exists():
        return "npm"
    if (root / "package.json").exists():
        return "npm"
    return None


def detect_ports_from_scripts(scripts: dict[str, str]) -> list[int]:
    ports: set[int] = set()
    patterns = [
        r"(?:--port|-p)\s+([0-9]{2,5})",
        r"PORT=([0-9]{2,5})",
        r"localhost:([0-9]{2,5})",
        r"127\.0\.0\.1:([0-9]{2,5})",
    ]
    for script in scripts.values():
        for pattern in patterns:
            for match in re.finditer(pattern, script):
                ports.add(int(match.group(1)))
    return sorted(ports)


def detect_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    package_json = read_json(root / "package.json") if (root / "package.json").exists() else {}
    scripts = package_json.get("scripts", {}) if isinstance(package_json.get("scripts"), dict) else {}
    dependencies = {}
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        value = package_json.get(key)
        if isinstance(value, dict):
            dependencies.update(value)

    signals: list[str] = []
    commands: list[str] = []
    ports = set(detect_ports_from_scripts(scripts))
    package_manager = detect_package_manager(root)

    if package_json:
        signals.append("node")
        if package_manager:
            for name in ("dev", "start", "build", "test", "typecheck", "lint"):
                if name in scripts:
                    commands.append(f"{package_manager} run {name}")
        for dep in dependencies:
            dep_lower = dep.lower()
            if dep_lower in ("next", "vite", "astro", "@sveltejs/kit", "@angular/core", "storybook"):
                label = "sveltekit" if dep_lower == "@sveltejs/kit" else dep_lower.replace("@angular/core", "angular")
                signals.append(label)
                if label in KNOWN_PORTS:
                    ports.add(KNOWN_PORTS[label])

    if file_exists(root, "Cargo.toml"):
        signals.append("rust")
        commands.extend(["cargo test", "cargo run -- --help"])

    html_files = sorted(root.glob("*.html"))
    if html_files:
        signals.append("static-html")
        commands.append("python -m http.server 8000")
        ports.add(8000)

    if file_exists(root, "pyproject.toml", "requirements.txt", "setup.py"):
        signals.append("python")
        commands.extend(["py -m pytest", "py -m <module-or-script> --help"])

    if file_exists(root, "go.mod"):
        signals.append("go")
        commands.extend(["go test ./...", "go run ."])

    if file_exists(root, "pubspec.yaml"):
        signals.append("flutter")
        commands.extend(["flutter test", "flutter run -d chrome"])

    if file_exists(root, "app.json", "app.config.js", "app.config.ts"):
        signals.append("expo-or-react-native")
        if package_manager:
            commands.append(f"{package_manager} run start")

    if file_exists(root, "docker-compose.yml", "docker-compose.yaml", "compose.yml"):
        signals.append("docker-compose")
        commands.append("docker compose up")

    if file_exists(root, "Makefile"):
        signals.append("make")
        commands.append("make")

    if file_exists(root, "justfile", "Justfile"):
        signals.append("just")
        commands.append("just --list")

    return {
        "root": str(root),
        "signals": sorted(set(signals)),
        "package_manager": package_manager,
        "package_scripts": scripts,
        "candidate_ports": sorted(ports),
        "candidate_commands": dedupe(commands),
        "references": recommend_references(signals),
    }


def recommend_references(signals: list[str]) -> list[str]:
    refs = ["references/mobile-handoff.md", "references/command-proof.md"]
    web_signals = {
        "next",
        "vite",
        "astro",
        "sveltekit",
        "angular",
        "storybook",
        "expo-or-react-native",
        "flutter",
        "static-html",
    }
    if web_signals.intersection(signals):
        refs.insert(0, "references/web-previews.md")
        refs.append("references/verification-checklists.md")
    if signals:
        refs.append("references/stack-playbooks.md")
    return dedupe(refs)


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def run_version_command(command: list[str], timeout: float = 8.0) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return {
            "available": False,
            "exit_code": None,
            "output": str(exc),
        }

    output = (completed.stdout or completed.stderr).strip()
    return {
        "available": completed.returncode == 0,
        "exit_code": completed.returncode,
        "output": first_non_empty_line(output),
    }


def first_non_empty_line(value: str) -> str:
    for line in value.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def make_check(
    name: str,
    status: str,
    detail: str,
    next_step: str,
    *,
    required: bool = True,
    proof: str | list[str] | dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "required": required,
        "detail": detail,
        "proof": proof or "not available",
        "next": next_step,
    }


def command_check(
    name: str,
    binary: str,
    version_args: list[str],
    install_next: str,
    *,
    required: bool = True,
) -> dict[str, Any]:
    path = shutil.which(binary)
    if not path:
        return make_check(
            name,
            "action_required",
            f"{binary} is not installed or not on PATH",
            install_next,
            required=required,
            proof=f"`{binary}` not found",
        )

    result = run_version_command([path, *version_args])
    if not result["available"]:
        return make_check(
            name,
            "action_required",
            f"{binary} exists but did not run cleanly",
            install_next,
            required=required,
            proof=[f"path {path}", f"exit {result['exit_code']}", result["output"]],
        )

    return make_check(
        name,
        "ok",
        f"{binary} is available",
        "No action needed.",
        required=required,
        proof=[f"path {path}", result["output"]],
    )


def collect_ngrok_config_paths(ngrok_path: str | None) -> list[Path]:
    paths: list[Path] = []
    if ngrok_path:
        result = run_version_command([ngrok_path, "config", "check"], timeout=8)
        output = str(result.get("output") or "")
        paths.extend(Path(match) for match in re.findall(r"([A-Za-z]:\\[^\r\n]+ngrok\.ya?ml|/[^\s]+ngrok\.ya?ml)", output))

    home = Path.home()
    appdata = Path.home()
    if sys.platform.startswith("win"):
        appdata_env = Path(str(Path.home()))
        appdata_value = os.environ.get("APPDATA")
        if appdata_value:
            appdata_env = Path(appdata_value)
        appdata = appdata_env

    paths.extend(
        [
            appdata / "ngrok" / "ngrok.yml",
            home / ".ngrok2" / "ngrok.yml",
            home / ".config" / "ngrok" / "ngrok.yml",
            home / "Library" / "Application Support" / "ngrok" / "ngrok.yml",
        ]
    )
    return dedupe_paths(paths)


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def ngrok_has_authtoken(paths: list[Path]) -> tuple[bool, list[str]]:
    checked: list[str] = []
    token_pattern = re.compile(r"^\s*(?:authtoken|token)\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)
    nested_pattern = re.compile(r"^\s*authtoken\s*:\s*(\S+)", re.IGNORECASE | re.MULTILINE)
    for path in paths:
        checked.append(str(path))
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if token_pattern.search(content) or nested_pattern.search(content):
            return True, checked
    return False, checked


def ngrok_doctor_check() -> dict[str, Any]:
    ngrok = shutil.which("ngrok")
    if not ngrok:
        return make_check(
            "ngrok preview setup",
            "action_required",
            "ngrok is not installed or not on PATH",
            "Create an ngrok account, install the ngrok agent, then run `ngrok config add-authtoken <token>` using the token from the ngrok dashboard.",
            proof="`ngrok` not found",
        )

    version = run_version_command([ngrok, "version"])
    config_paths = collect_ngrok_config_paths(ngrok)
    has_token, checked = ngrok_has_authtoken(config_paths)
    if not has_token:
        return make_check(
            "ngrok preview setup",
            "action_required",
            "ngrok is installed but no local authtoken config was found",
            "Sign in or create an ngrok account, copy your authtoken from the ngrok dashboard, then run `ngrok config add-authtoken <token>` on this machine.",
            proof=[f"path {ngrok}", str(version.get("output") or "version unavailable"), f"checked {', '.join(checked) if checked else 'no config paths'}"],
        )

    return make_check(
        "ngrok preview setup",
        "ok",
        "ngrok is installed and an authtoken config was found",
        "No action needed before requesting public phone previews.",
        proof=[f"path {ngrok}", str(version.get("output") or "version unavailable"), f"config checked {', '.join(checked)}"],
    )


def playwright_doctor_check(root: Path) -> dict[str, Any]:
    candidates = [
        shutil.which("playwright"),
        str(root / "node_modules" / ".bin" / ("playwright.cmd" if sys.platform.startswith("win") else "playwright")),
    ]
    existing = [candidate for candidate in candidates if candidate and Path(candidate).exists()]
    package_json = read_json(root / "package.json") if (root / "package.json").exists() else {}
    deps: dict[str, Any] = {}
    for key in ("dependencies", "devDependencies"):
        value = package_json.get(key)
        if isinstance(value, dict):
            deps.update(value)

    if existing:
        result = run_version_command([existing[0], "--version"])
        return make_check(
            "browser proof tooling",
            "ok" if result["available"] else "warning",
            "Playwright CLI is available" if result["available"] else "Playwright CLI exists but did not run cleanly",
            "No action needed." if result["available"] else "Run `npx playwright install chromium` or reinstall the project browser tooling.",
            proof=[f"path {existing[0]}", result["output"]],
        )

    if "@playwright/test" in deps or "playwright" in deps:
        return make_check(
            "browser proof tooling",
            "warning",
            "Playwright is listed in package.json, but the local CLI was not found",
            "Run the project install command, then `npx playwright install chromium` if browser binaries are missing.",
            proof="package.json includes Playwright dependency",
        )

    return make_check(
        "browser proof tooling",
        "action_required",
        "No Playwright CLI or project dependency was found for repeatable browser proof",
        "Install browser proof tooling with `npm install -D @playwright/test` and `npx playwright install chromium`, or rely on Codex's built-in browser only when it is available.",
        proof="no local Playwright CLI found",
    )


def port_is_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def ports_doctor_check(ports: list[int]) -> dict[str, Any]:
    results = {str(port): ("free" if port_is_free(port) else "in_use") for port in ports}
    in_use = [port for port, status in results.items() if status == "in_use"]
    if in_use:
        return make_check(
            "common preview ports",
            "warning",
            f"Some common ports are already in use: {', '.join(in_use)}",
            "Reuse the running server only after identifying it, or choose another free port before creating a public preview.",
            required=False,
            proof=results,
        )
    return make_check(
        "common preview ports",
        "ok",
        "Common preview ports are free",
        "No action needed.",
        required=False,
        proof=results,
    )


def skill_files_doctor_check(skill_root: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_SKILL_FILES if not (skill_root / name).exists()]
    skill_md = skill_root / "SKILL.md"
    frontmatter_ok = False
    if skill_md.exists():
        try:
            content = skill_md.read_text(encoding="utf-8", errors="replace")
            frontmatter_ok = content.startswith("---") and "name: mobile-codex-dev" in content
        except Exception:
            frontmatter_ok = False

    if missing or not frontmatter_ok:
        detail_parts = []
        if missing:
            detail_parts.append(f"missing {', '.join(missing)}")
        if not frontmatter_ok:
            detail_parts.append("SKILL.md frontmatter is missing or unexpected")
        return make_check(
            "skill files",
            "action_required",
            "; ".join(detail_parts),
            "Restore the missing skill files before installing or publishing the skill.",
            proof=f"skill root {skill_root}",
        )

    validator = Path.home() / ".codex" / "skills" / ".system" / "skill-creator" / "scripts" / "quick_validate.py"
    if validator.exists():
        result = run_version_command([sys.executable, str(validator), str(skill_root)], timeout=15)
        if not result["available"]:
            return make_check(
                "skill files",
                "action_required",
                "Codex skill validation failed",
                "Fix the validator errors before installing or publishing the skill.",
                proof=[f"validator {validator}", f"exit {result['exit_code']}", result["output"]],
            )
        return make_check(
            "skill files",
            "ok",
            "Required skill files are present and the Codex validator passed",
            "No action needed.",
            proof=[f"skill root {skill_root}", f"validator {validator}", result["output"]],
        )

    return make_check(
        "skill files",
        "ok",
        "Required skill files are present; Codex validator was not found locally",
        "No action needed.",
        proof=f"skill root {skill_root}",
    )


def readme_doctor_check(repo_root: Path) -> dict[str, Any]:
    readme = repo_root / "README.md"
    if not readme.exists():
        return make_check(
            "README and install path",
            "action_required",
            "README.md was not found at the repo root",
            "Add a README with install instructions for `~/.agents/skills` and the mobile-first setup flow.",
            proof=f"repo root {repo_root}",
        )

    content = readme.read_text(encoding="utf-8", errors="replace")
    required_phrases = ["~/.agents/skills", "mobile-codex-dev", "Work with Codex from anywhere"]
    missing = [phrase for phrase in required_phrases if phrase not in content]
    if missing:
        return make_check(
            "README and install path",
            "warning",
            f"README is present but missing expected setup language: {', '.join(missing)}",
            "Update README setup copy before publishing so first-time mobile users know where to install the skill.",
            required=False,
            proof=f"README {readme}",
        )

    return make_check(
        "README and install path",
        "ok",
        "README includes the expected install path and mobile-first positioning",
        "No action needed.",
        required=False,
        proof=f"README {readme}",
    )


def doctor(args: argparse.Namespace) -> int:
    repo_root = Path(args.root).resolve()
    skill_root = Path(args.skill_root).resolve() if args.skill_root else Path(__file__).resolve().parents[1]
    ports = args.ports or COMMON_PORTS

    checks = [
        make_check(
            "Python runtime",
            "ok",
            "Python is available because this helper is running",
            "No action needed.",
            proof=[f"executable {sys.executable}", f"version {sys.version.split()[0]}"],
        ),
        command_check(
            "Node.js runtime",
            "node",
            ["--version"],
            "Install Node.js LTS, then reopen the terminal so `node` is on PATH.",
        ),
        command_check(
            "npm package runner",
            "npm",
            ["--version"],
            "Install Node.js LTS, which includes npm, then rerun doctor.",
        ),
        command_check(
            "git version control",
            "git",
            ["--version"],
            "Install Git, then reopen the terminal so `git` is on PATH.",
        ),
        ngrok_doctor_check(),
        playwright_doctor_check(repo_root),
        ports_doctor_check(ports),
        skill_files_doctor_check(skill_root),
        readme_doctor_check(repo_root),
    ]

    required_failures = [check for check in checks if check["required"] and check["status"] == "action_required"]
    warnings = [check for check in checks if check["status"] == "warning"]
    data = {
        "result": "ready" if not required_failures else "setup action required",
        "summary": f"{len(checks) - len(required_failures) - len(warnings)} ok, {len(warnings)} warning, {len(required_failures)} action required",
        "root": str(repo_root),
        "skill_root": str(skill_root),
        "checks": checks,
        "next": "You can run mobile-first Codex work now." if not required_failures else "Complete the action_required items, then rerun doctor before relying on phone previews.",
    }
    print_doctor(data, args.format)
    return 0 if not required_failures else 2


def print_doctor(data: dict[str, Any], format_name: str) -> None:
    if format_name == "json":
        print(json.dumps(data, indent=2))
        return

    print("# Mobile Codex Doctor")
    print(f"- Result: {data['result']}")
    print(f"- Summary: {data['summary']}")
    print(f"- Root: `{data['root']}`")
    print(f"- Skill Root: `{data['skill_root']}`")
    print("")
    print("## Checks")
    for check in data["checks"]:
        required = "required" if check["required"] else "advisory"
        print(f"- {check['status'].upper()} [{required}] {check['name']}: {check['detail']}")
        proof = check.get("proof")
        if isinstance(proof, list):
            print("  - Proof: " + "; ".join(str(item) for item in proof if item))
        elif isinstance(proof, dict):
            print("  - Proof: " + ", ".join(f"{key}={value}" for key, value in proof.items()))
        else:
            print(f"  - Proof: {proof}")
        print(f"  - Next: {check['next']}")
    print("")
    print(f"Next: {data['next']}")


def render_markdown_detection(data: dict[str, Any]) -> str:
    lines = [
        "# Mobile Dev Detection",
        "",
        f"Root: `{data['root']}`",
        f"Signals: {', '.join(data['signals']) if data['signals'] else 'none detected'}",
        f"Package manager: {data['package_manager'] or 'none detected'}",
        f"Candidate ports: {', '.join(map(str, data['candidate_ports'])) if data['candidate_ports'] else 'none detected'}",
        "",
        "## Candidate Commands",
    ]
    commands = data.get("candidate_commands") or []
    if commands:
        lines.extend(f"- `{command}`" for command in commands)
    else:
        lines.append("- none detected")

    scripts = data.get("package_scripts") or {}
    if scripts:
        lines.extend(["", "## Package Scripts"])
        for name, command in scripts.items():
            lines.append(f"- `{name}`: `{command}`")

    refs = data.get("references") or []
    lines.extend(["", "## Suggested References"])
    lines.extend(f"- `{ref}`" for ref in refs)
    return "\n".join(lines)


def ngrok_check(format_name: str) -> int:
    ngrok = shutil.which("ngrok")
    if not ngrok:
        data = {
            "available": False,
            "message": "ngrok is not installed or not on PATH",
            "next": "Install ngrok, then run `ngrok config add-authtoken <token>`.",
        }
        print_json_or_markdown(data, format_name, "Ngrok Check")
        return 2

    try:
        completed = subprocess.run(
            [ngrok, "version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        data = {
            "available": False,
            "path": ngrok,
            "message": str(exc),
            "next": "Verify ngrok installation and authentication.",
        }
        print_json_or_markdown(data, format_name, "Ngrok Check")
        return 2

    output = (completed.stdout or completed.stderr).strip()
    data = {
        "available": completed.returncode == 0,
        "path": ngrok,
        "version_output": output,
        "exit_code": completed.returncode,
        "next": "Use `ngrok http <port>` for phone previews." if completed.returncode == 0 else "Verify ngrok installation and authentication.",
    }
    print_json_or_markdown(data, format_name, "Ngrok Check")
    return 0 if completed.returncode == 0 else 2


def read_ngrok_api(api_url: str, timeout: float = 2.0) -> dict[str, Any]:
    request = urllib.request.Request(api_url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def tunnel_matches_port(tunnel: dict[str, Any], port: int) -> bool:
    config = tunnel.get("config") if isinstance(tunnel.get("config"), dict) else {}
    addr = str(config.get("addr") or "")
    return addr == str(port) or addr.endswith(f":{port}") or addr.endswith(f"//localhost:{port}") or addr.endswith(f"//127.0.0.1:{port}")


def extract_ngrok_url(data: dict[str, Any], port: int | None = None) -> dict[str, Any] | None:
    tunnels = data.get("tunnels")
    if not isinstance(tunnels, list):
        return None

    candidates = [tunnel for tunnel in tunnels if isinstance(tunnel, dict)]
    if port is not None:
        port_matches = [tunnel for tunnel in candidates if tunnel_matches_port(tunnel, port)]
        if port_matches:
            candidates = port_matches

    https_candidates = [
        tunnel for tunnel in candidates if str(tunnel.get("public_url", "")).startswith("https://")
    ]
    ordered = https_candidates or candidates
    for tunnel in ordered:
        public_url = str(tunnel.get("public_url") or "")
        if public_url:
            return {
                "public_url": public_url,
                "name": tunnel.get("name"),
                "proto": tunnel.get("proto"),
                "config": tunnel.get("config"),
            }
    return None


def read_log_tail(path: Path, lines: int) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [f"log read failed for {path}: {exc}"]
    tail = content[-max(lines, 1):]
    return [f"{path}: {line}" for line in tail]


def start_ngrok_preview(args: argparse.Namespace) -> int:
    if args.port < 1 or args.port > 65535:
        print_json_or_markdown(
            {
                "result": "ngrok preview blocked",
                "preview": "blocked because the requested port is invalid",
                "proof": f"`ngrok http {args.port}` was not started because ports must be between 1 and 65535",
                "next": "Pass a valid local HTTP port between 1 and 65535.",
            },
            args.format,
            "Ngrok Preview",
        )
        return 2

    ngrok = shutil.which("ngrok")
    command_display = f"ngrok http {args.port}"
    if not ngrok:
        data = {
            "result": "ngrok preview blocked",
            "preview": "blocked because ngrok is not installed or not on PATH",
            "proof": f"`{command_display}` could not start: command not found",
            "next": "Install and authenticate ngrok on this machine before requesting a public phone preview.",
        }
        print_json_or_markdown(data, args.format, "Ngrok Preview")
        return 2

    log_file = Path(args.log_file) if args.log_file else Path(tempfile.gettempdir()) / f"mobilecodex-ngrok-{args.port}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    log_handle = log_file.open("a", encoding="utf-8", errors="replace")
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [ngrok, "http", str(args.port), "--log", "stdout"],
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )

        deadline = time.monotonic() + args.timeout
        last_error = ""
        tunnel: dict[str, Any] | None = None
        while time.monotonic() < deadline:
            if process.poll() is not None:
                last_error = f"ngrok exited early with code {process.returncode}"
                break
            try:
                tunnel = extract_ngrok_url(read_ngrok_api(args.api_url), args.port)
                if tunnel:
                    break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                last_error = str(exc)
            time.sleep(args.poll_interval)

        if tunnel:
            public_url = str(tunnel["public_url"])
            data = {
                "result": "ngrok public phone preview is running",
                "preview": public_url,
                "proof": [
                    f"`{command_display}` started",
                    f"process id {process.pid}",
                    f"local port {args.port}",
                    f"local URL http://127.0.0.1:{args.port}",
                    f"ngrok API {args.api_url}",
                    f"log file {log_file}",
                ],
                "next": "Open the preview URL from the phone, and keep this ngrok process running while the preview is needed.",
            }
            print_json_or_markdown(data, args.format, "Ngrok Preview")
            return 0

        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        tail = read_log_tail(log_file, args.log_lines)
        data = {
            "result": "ngrok preview blocked",
            "preview": "blocked because no forwarding URL was found",
            "proof": [
                f"`{command_display}` did not produce a tunnel within {args.timeout:g}s",
                f"ngrok API {args.api_url}",
                f"last error {last_error or 'none'}",
                *tail,
            ],
            "next": "Verify ngrok is authenticated, no other ngrok agent is conflicting, and the local app responds on the requested port.",
        }
        print_json_or_markdown(data, args.format, "Ngrok Preview")
        return 2
    except Exception as exc:
        if process and process.poll() is None:
            process.terminate()
        data = {
            "result": "ngrok preview blocked",
            "preview": "blocked because ngrok failed to start",
            "proof": f"`{command_display}` failed: {exc}",
            "next": "Verify ngrok installation, authentication, and local port availability.",
        }
        print_json_or_markdown(data, args.format, "Ngrok Preview")
        return 2
    finally:
        log_handle.close()


def print_json_or_markdown(data: dict[str, Any], format_name: str, title: str) -> None:
    if format_name == "json":
        print(json.dumps(data, indent=2))
        return
    print(f"# {title}")
    for key, value in data.items():
        label = key.replace("_", " ").title()
        if isinstance(value, list):
            print(f"- {label}:")
            for item in value:
                print(f"  - {item}")
        else:
            print(f"- {label}: {value}")


def format_handoff(args: argparse.Namespace) -> str:
    lines = [
        f"Result: {args.result}",
        f"Preview: {args.preview}",
    ]
    proof = args.proof or []
    if args.log_file:
        proof.extend(read_log_tail(Path(args.log_file), args.log_lines))
    lines.append("Proof: " + ("; ".join(proof) if proof else "not provided"))
    next_items = args.next or []
    lines.append("Next: " + ("; ".join(next_items) if next_items else "no immediate next action"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mobile Codex Dev helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect project shape and mobile proof hints")
    detect_parser.add_argument("--root", default=".", help="Project root")
    detect_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    ngrok_parser = subparsers.add_parser("ngrok-check", help="Check ngrok availability")
    ngrok_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    ngrok_preview_parser = subparsers.add_parser("ngrok-preview", help="Start ngrok and extract a phone preview URL")
    ngrok_preview_parser.add_argument("--port", type=int, required=True, help="Local HTTP port to expose")
    ngrok_preview_parser.add_argument("--api-url", default=DEFAULT_NGROK_API_URL, help="ngrok local API URL")
    ngrok_preview_parser.add_argument("--timeout", type=float, default=20.0, help="Seconds to wait for a forwarding URL")
    ngrok_preview_parser.add_argument("--poll-interval", type=float, default=0.5, help="Seconds between API checks")
    ngrok_preview_parser.add_argument("--log-file", help="Path to capture ngrok logs")
    ngrok_preview_parser.add_argument("--log-lines", type=int, default=8)
    ngrok_preview_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    doctor_parser = subparsers.add_parser("doctor", help="Run first-time setup checks for mobile Codex work")
    doctor_parser.add_argument("--root", default=".", help="Repository root to inspect")
    doctor_parser.add_argument("--skill-root", help="Skill root to validate")
    doctor_parser.add_argument("--ports", type=int, nargs="*", default=COMMON_PORTS, help="Ports to check for availability")
    doctor_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    handoff_parser = subparsers.add_parser("handoff", help="Format a compact mobile handoff")
    handoff_parser.add_argument("--result", required=True)
    handoff_parser.add_argument("--preview", required=True)
    handoff_parser.add_argument("--proof", action="append", default=[])
    handoff_parser.add_argument("--next", action="append", default=[])
    handoff_parser.add_argument("--log-file")
    handoff_parser.add_argument("--log-lines", type=int, default=8)

    args = parser.parse_args(argv)

    if args.command == "detect":
        data = detect_project(Path(args.root))
        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            print(render_markdown_detection(data))
        return 0

    if args.command == "ngrok-check":
        return ngrok_check(args.format)

    if args.command == "ngrok-preview":
        return start_ngrok_preview(args)

    if args.command == "doctor":
        return doctor(args)

    if args.command == "handoff":
        print(format_handoff(args))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
