#!/usr/bin/env python3
"""Utilities for the mobile-codex-dev skill.

The commands are intentionally read-only except for printing formatted output.
They help Codex quickly inspect a project, run setup checks, check ngrok
availability, and format a compact mobile handoff.
"""

from __future__ import annotations

import argparse
import hashlib
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
from datetime import datetime
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
PROOF_DIR_NAMES = ["proof", "screenshots", "artifacts"]
PROOF_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".pdf", ".html", ".txt", ".log", ".md", ".json"}
SECRET_FILE_PATTERNS = [".env", ".env.*", "*secret*", "*token*", "*credential*", "*.pem", "*.key"]
SKIP_DIR_NAMES = {".git", "node_modules", ".venv", "venv", "__pycache__", "target", "dist", "build", ".next", ".cache"}
MAX_PROOF_COPY_BYTES = 5 * 1024 * 1024
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


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def workspace_key(root: Path) -> str:
    return hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:16]


def mobilecodex_temp_root(root: Path) -> Path:
    return Path(tempfile.gettempdir()) / "mobilecodex" / workspace_key(root)


def registry_path(root: Path) -> Path:
    return mobilecodex_temp_root(root) / "servers.json"


def logs_dir(root: Path) -> Path:
    return mobilecodex_temp_root(root) / "logs"


def run_git(root: Path, args: list[str], timeout: float = 8.0) -> tuple[int | None, str]:
    git = shutil.which("git")
    if not git:
        return None, "git not found"
    try:
        completed = subprocess.run(
            [git, *args],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except Exception as exc:
        return None, str(exc)
    output = (completed.stdout or completed.stderr).strip()
    return completed.returncode, output


def git_info(root: Path) -> dict[str, Any]:
    branch_code, branch = run_git(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    commit_code, commit = run_git(root, ["log", "-1", "--pretty=%h %s"])
    status_code, status = run_git(root, ["status", "--short"])
    dirty_files = [line for line in status.splitlines() if line.strip()] if status_code == 0 else []
    return {
        "available": branch_code == 0,
        "branch": branch if branch_code == 0 else "unavailable",
        "last_commit": commit if commit_code == 0 else "unavailable",
        "dirty_count": len(dirty_files),
        "dirty_files": dirty_files[:25],
        "dirty_truncated": max(0, len(dirty_files) - 25),
    }


def port_statuses(ports: list[int]) -> dict[str, str]:
    return {str(port): ("free" if port_is_free(port) else "in_use") for port in ports}


def port_accepts_connections(port: int, host: str = "127.0.0.1", timeout: float = 0.4) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((host, port)) == 0
        except OSError:
            return False


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def is_secret_path(path: Path) -> bool:
    name = path.name.lower()
    for pattern in SECRET_FILE_PATTERNS:
        regex = "^" + re.escape(pattern.lower()).replace("\\*", ".*") + "$"
        if re.match(regex, name):
            return True
    return False


def is_skipped_dir(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.parts)


def collect_proof_artifacts(root: Path, *, limit: int = 12, exclude: Path | None = None) -> list[dict[str, Any]]:
    candidates: list[Path] = []
    search_roots = [root / name for name in PROOF_DIR_NAMES]
    temp_root = mobilecodex_temp_root(root)
    if temp_root.exists():
        search_roots.append(temp_root)

    for search_root in search_roots:
        if not search_root.exists():
            continue
        for path in search_root.rglob("*"):
            if not path.is_file():
                continue
            if exclude and is_relative_to(path, exclude):
                continue
            if is_skipped_dir(path.relative_to(search_root) if is_relative_to(path, search_root) else path):
                continue
            if is_secret_path(path):
                continue
            if path.suffix.lower() not in PROOF_EXTENSIONS:
                continue
            candidates.append(path)

    candidates = sorted(candidates, key=lambda item: item.stat().st_mtime, reverse=True)
    artifacts: list[dict[str, Any]] = []
    for path in candidates[:limit]:
        try:
            stat = path.stat()
        except OSError:
            continue
        artifacts.append(
            {
                "path": str(path.resolve()),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
            }
        )
    return artifacts


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

    npx = shutil.which("npx")
    if npx:
        return make_check(
            "browser proof tooling",
            "warning",
            "No local Playwright dependency was found, but `npx playwright` is available for screenshot fallback",
            "Add `@playwright/test` to the project for full console/network UX proof, or use the npx fallback for screenshots.",
            required=False,
            proof=f"npx {npx}",
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


def process_is_running(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform.startswith("win"):
        try:
            completed = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
        except Exception:
            return False
        return str(pid) in completed.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def terminate_process(pid: int) -> tuple[bool, str]:
    if sys.platform.startswith("win"):
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as exc:
            return False, str(exc)
        output = (completed.stdout or completed.stderr).strip()
        return completed.returncode == 0, output
    try:
        os.kill(pid, 15)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if not process_is_running(pid):
                return True, "terminated"
            time.sleep(0.2)
        os.kill(pid, 9)
        return True, "killed after timeout"
    except Exception as exc:
        return False, str(exc)


def load_registry(root: Path) -> dict[str, Any]:
    path = registry_path(root)
    if not path.exists():
        return {"workspace": str(root.resolve()), "servers": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"workspace": str(root.resolve()), "servers": []}
    if not isinstance(data.get("servers"), list):
        data["servers"] = []
    return data


def save_registry(root: Path, data: dict[str, Any]) -> None:
    path = registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_server_entry(entry: dict[str, Any]) -> dict[str, Any]:
    port = int(entry.get("port") or 0)
    pid = int(entry.get("pid") or 0)
    running = process_is_running(pid)
    port_open = port_accepts_connections(port) if port else False
    status = "running" if running and port_open else "process_running" if running else "stopped"
    normalized = dict(entry)
    normalized.update(
        {
            "pid": pid,
            "port": port,
            "local_url": entry.get("local_url") or (f"http://127.0.0.1:{port}" if port else ""),
            "status": status,
            "port_open": port_open,
            "pid_running": running,
            "last_checked": datetime.now().isoformat(timespec="seconds"),
        }
    )
    return normalized


def list_servers(root: Path) -> list[dict[str, Any]]:
    data = load_registry(root)
    servers = [normalize_server_entry(server) for server in data.get("servers", []) if isinstance(server, dict)]
    if servers != data.get("servers", []):
        data["servers"] = servers
        save_registry(root, data)
    return servers


def render_servers_markdown(root: Path, servers: list[dict[str, Any]]) -> str:
    lines = ["# MobileCodex Server Registry", "", f"Workspace: `{root.resolve()}`", f"Registry: `{registry_path(root)}`", ""]
    if not servers:
        lines.append("No registered servers.")
        return "\n".join(lines)
    for server in servers:
        lines.extend(
            [
                f"- `{server['name']}`: {server['status']}",
                f"  - PID: `{server['pid']}`",
                f"  - Port: `{server['port']}`",
                f"  - URL: {server['local_url']}",
                f"  - Command: `{server['command']}`",
                f"  - Log: `{server['log_file']}`",
            ]
        )
    return "\n".join(lines)


def server_start(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    command = list(args.server_command or [])
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print_json_or_markdown(
            {"result": "server start blocked", "proof": "no command was provided", "next": "Pass a command after `--`."},
            args.format,
            "Server Start",
        )
        return 2

    registry = load_registry(root)
    existing = [normalize_server_entry(item) for item in registry.get("servers", []) if isinstance(item, dict)]
    if any(item.get("name") == args.name and item.get("status") != "stopped" for item in existing):
        print_json_or_markdown(
            {
                "result": "server start blocked",
                "proof": f"a registered server named `{args.name}` already exists",
                "next": "Use `server-list` to inspect it or `server-stop --name` before starting a replacement.",
            },
            args.format,
            "Server Start",
        )
        return 2

    log_dir = logs_dir(root)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{args.name}-{args.port}-{now_stamp()}.log"
    log_handle = log_file.open("a", encoding="utf-8", errors="replace")
    try:
        process = subprocess.Popen(
            command,
            cwd=root,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception as exc:
        log_handle.close()
        print_json_or_markdown(
            {"result": "server start blocked", "proof": f"`{' '.join(command)}` failed: {exc}", "next": "Fix the command and retry."},
            args.format,
            "Server Start",
        )
        return 2
    finally:
        try:
            log_handle.flush()
        except Exception:
            pass

    time.sleep(args.wait)
    entry = {
        "name": args.name,
        "command": " ".join(command),
        "command_args": command,
        "cwd": str(root),
        "pid": process.pid,
        "port": args.port,
        "local_url": f"http://127.0.0.1:{args.port}",
        "log_file": str(log_file),
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    entry = normalize_server_entry(entry)
    registry["workspace"] = str(root)
    registry["servers"] = [item for item in existing if item.get("name") != args.name]
    registry["servers"].append(entry)
    save_registry(root, registry)
    log_handle.close()
    print_json_or_markdown(
        {
            "result": "server registered",
            "preview": entry["local_url"],
            "proof": [
                f"command `{entry['command']}`",
                f"pid {entry['pid']}",
                f"port {entry['port']} status {entry['status']}",
                f"log file {entry['log_file']}",
            ],
            "next": "Use `server-list` to inspect it or `server-stop` when the preview is no longer needed.",
        },
        args.format,
        "Server Start",
    )
    return 0 if entry["pid_running"] else 2


def server_list(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    servers = list_servers(root)
    data = {"workspace": str(root), "registry": str(registry_path(root)), "servers": servers}
    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        print(render_servers_markdown(root, servers))
    return 0


def server_stop(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    registry = load_registry(root)
    servers = [normalize_server_entry(item) for item in registry.get("servers", []) if isinstance(item, dict)]
    matches = []
    for server in servers:
        if args.name and server.get("name") == args.name:
            matches.append(server)
        elif args.port and int(server.get("port") or 0) == args.port:
            matches.append(server)
    if not matches:
        print_json_or_markdown(
            {
                "result": "server stop blocked",
                "proof": "no matching registered server was found",
                "next": "Use `server-list` to inspect registered servers. This command only stops registry-owned processes.",
            },
            args.format,
            "Server Stop",
        )
        return 2

    stopped: list[str] = []
    failed: list[str] = []
    match_ids = {(server.get("name"), server.get("pid"), server.get("port")) for server in matches}
    for server in matches:
        if server.get("pid_running"):
            ok, output = terminate_process(int(server["pid"]))
            if ok:
                stopped.append(f"{server['name']} pid {server['pid']}: {output}")
            else:
                failed.append(f"{server['name']} pid {server['pid']}: {output}")
        else:
            stopped.append(f"{server['name']} pid {server['pid']}: already stopped")

    registry["servers"] = [
        server for server in servers if (server.get("name"), server.get("pid"), server.get("port")) not in match_ids
    ]
    save_registry(root, registry)
    print_json_or_markdown(
        {
            "result": "server stop complete" if not failed else "server stop partial",
            "proof": [*stopped, *failed],
            "next": "Use `server-list` to confirm current registry state.",
        },
        args.format,
        "Server Stop",
    )
    return 0 if not failed else 2


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
    required_phrases = ["~/.agents/skills", "mobile-codex-dev", "Work with Codex from anywhere", "Codex Mobile", "chatgpt.com/codex/mobile"]
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


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def skill_tree_digest(root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        if path.is_file() and not is_skipped_dir(path.relative_to(root)):
            result[str(path.relative_to(root)).replace("\\", "/")] = file_digest(path)
    return result


def installed_skill_drift_check(skill_root: Path) -> dict[str, Any]:
    candidates = [
        Path.home() / ".agents" / "skills" / "mobile-codex-dev",
        Path.home() / ".codex" / "skills" / "mobile-codex-dev",
    ]
    source_digest = skill_tree_digest(skill_root)
    details: list[str] = []
    found = False
    drift = False
    for candidate in candidates:
        if not candidate.exists():
            details.append(f"{candidate}: missing")
            continue
        found = True
        candidate_digest = skill_tree_digest(candidate)
        if candidate_digest == source_digest:
            details.append(f"{candidate}: matches")
        else:
            drift = True
            details.append(f"{candidate}: differs from repo skill")
    if not found:
        status = "warning"
        detail = "No installed mobile-codex-dev skill copy was found in common locations"
        next_step = "Install the skill into `~/.agents/skills/mobile-codex-dev` before relying on a fresh Codex session to discover it."
    elif drift:
        status = "warning"
        detail = "At least one installed skill copy differs from the repo copy"
        next_step = "Reinstall the skill from this repo after validating changes."
    else:
        status = "ok"
        detail = "Installed skill copy matches the repo copy"
        next_step = "No action needed."
    return make_check("installed skill copy drift", status, detail, next_step, required=False, proof=details)


def server_registry_doctor_check(root: Path) -> dict[str, Any]:
    servers = list_servers(root)
    stale = [server for server in servers if server.get("status") == "stopped"]
    if stale:
        return make_check(
            "server registry health",
            "warning",
            f"{len(stale)} stale registered server entry exists",
            "Run `server-list`, then `server-stop --name <label>` for stale entries if cleanup is needed.",
            required=False,
            proof=[f"{server['name']} pid {server['pid']} port {server['port']}" for server in stale],
        )
    return make_check(
        "server registry health",
        "ok",
        f"{len(servers)} registered server entry(s), none stale",
        "No action needed.",
        required=False,
        proof=f"registry {registry_path(root)}",
    )


def proof_directory_doctor_check(root: Path) -> dict[str, Any]:
    proof_dir = root / "proof"
    try:
        proof_dir.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return make_check(
            "proof directory health",
            "action_required",
            f"proof directory could not be created: {exc}",
            "Fix filesystem permissions or choose a writable proof output path.",
            proof=str(proof_dir),
        )
    artifacts = collect_proof_artifacts(root, limit=100)
    large = [artifact for artifact in artifacts if int(artifact["size"]) > MAX_PROOF_COPY_BYTES]
    status = "warning" if large else "ok"
    return make_check(
        "proof directory health",
        status,
        f"proof directory is writable; {len(artifacts)} recent artifact(s) found",
        "Review large proof artifacts before sharing." if large else "No action needed.",
        required=False,
        proof=[artifact["path"] for artifact in large[:5]] if large else str(proof_dir),
    )


def playwright_browser_readiness_check(root: Path) -> dict[str, Any]:
    if not (root / "node_modules" / "playwright").exists():
        npx = shutil.which("npx")
        return make_check(
            "Playwright browser readiness",
            "warning" if npx else "action_required",
            "Local Playwright package was not found, so Chromium launch was not verified",
            "Run `npx playwright install chromium` or add Playwright to the project before relying on `ux-proof`." if npx else "Install Node/npm and Playwright browser tooling.",
            required=False if npx else True,
            proof=f"npx {npx}" if npx else "npx not found",
        )
    command = find_playwright_node_command(root)
    if not command:
        return make_check(
            "Playwright browser readiness",
            "action_required",
            "No Node+npx or local Playwright package was found for UX proof",
            "Install Node/npm and run `npx playwright install chromium`, or add Playwright to the project.",
            proof="no Playwright node command available",
        )
    js = "const { chromium } = require('playwright'); (async()=>{ const b=await chromium.launch({headless:true}); await b.close(); console.log('chromium ok'); })().catch(e=>{ console.error(e.message); process.exit(1); });"
    try:
        completed = subprocess.run([*command, "-e", js], cwd=root, check=False, capture_output=True, text=True, timeout=45)
    except Exception as exc:
        return make_check(
            "Playwright browser readiness",
            "action_required",
            "Playwright readiness command failed to run",
            "Install Playwright browser dependencies, then rerun doctor.",
            proof=str(exc),
        )
    output = first_non_empty_line((completed.stdout or completed.stderr).strip())
    return make_check(
        "Playwright browser readiness",
        "ok" if completed.returncode == 0 else "action_required",
        "Chromium can launch for UX proof" if completed.returncode == 0 else "Playwright is available but Chromium could not launch",
        "No action needed." if completed.returncode == 0 else "Run `npx playwright install chromium` and retry.",
        proof=[f"command {' '.join(command)} -e <script>", f"exit {completed.returncode}", output],
    )


def mobile_ux_readiness_check(root: Path) -> dict[str, Any]:
    command = find_playwright_node_command(root) or find_playwright_cli_command(root)
    return make_check(
        "mobile UX proof readiness",
        "ok" if command else "action_required",
        "`ux-proof` has a Playwright execution path" if command else "`ux-proof` cannot run because Playwright/npx is unavailable",
        "No action needed." if command else "Install Node/npm and Playwright browser tooling before running UX proof.",
        proof=" ".join(command) if command else "no command",
    )


def snapshot_readiness_check(root: Path) -> dict[str, Any]:
    snapshot = build_snapshot(root)
    detected = snapshot["detected"]
    return make_check(
        "session snapshot readiness",
        "ok",
        "Snapshot command can summarize workspace state",
        "Use `snapshot --root . --format markdown` before pausing or resuming mobile work.",
        required=False,
        proof=[
            f"branch {snapshot['git']['branch']}",
            f"dirty {snapshot['git']['dirty_count']}",
            f"signals {', '.join(detected['signals']) if detected['signals'] else 'none'}",
        ],
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
        playwright_browser_readiness_check(repo_root),
        mobile_ux_readiness_check(repo_root),
        ports_doctor_check(ports),
        server_registry_doctor_check(repo_root),
        proof_directory_doctor_check(repo_root),
        skill_files_doctor_check(skill_root),
        installed_skill_drift_check(skill_root),
        readme_doctor_check(repo_root),
        snapshot_readiness_check(repo_root),
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


def capability_menu() -> str:
    return "\n".join(
        [
            "# MobileCodex Capability Menu",
            "",
            "Use this when the user asks what MobileCodex can do, when starting a broad mobile continuation task, or when the session needs an obvious next action.",
            "",
            "## Available Actions",
            "",
            "1. Session Snapshot",
            "   - Ask: `Show me the current session state before I step away.`",
            "   - Command: `mobile_dev.py snapshot --root . --format markdown`",
            "   - Gives: workspace, branch, changed files, ports, registered servers, recent proof, and suggested references.",
            "",
            "2. Tracked Preview Server",
            "   - Ask: `Start the app preview and keep it visible from my phone.`",
            "   - Command: `mobile_dev.py server-start --root . --name app --port <port> -- <server command>`",
            "   - Gives: registered PID, port, local URL, command, log file, and safe stop/list commands.",
            "",
            "3. Server Status",
            "   - Ask: `What previews are still running?`",
            "   - Command: `mobile_dev.py server-list --root .`",
            "   - Gives: running/stopped status for MobileCodex-owned preview servers.",
            "",
            "4. Mobile UX Proof",
            "   - Ask: `Capture mobile proof for this page.`",
            "   - Command: `mobile_dev.py ux-proof --root . --url <local-url>`",
            "   - Gives: mobile and desktop screenshots plus browser evidence when local Playwright tooling is available.",
            "",
            "5. Proof Bundle",
            "   - Ask: `Bundle the proof so I can review it later.`",
            "   - Command: `mobile_dev.py proof-bundle --root . --format markdown`",
            "   - Gives: one `proof.md` with snapshot state, changed files, registered servers, artifacts, and log tails.",
            "",
            "6. Setup Doctor",
            "   - Ask: `Check whether this machine is ready for mobile Codex work.`",
            "   - Command: `mobile_dev.py doctor --root . --format markdown`",
            "   - Gives: readiness checks for runtimes, ngrok, proof tooling, registry health, proof storage, skill files, and install drift.",
            "",
            "7. Public Phone Preview",
            "   - Ask: `Give me a safe phone preview URL.`",
            "   - Command: `mobile_dev.py ngrok-preview --port <port>`",
            "   - Gives: real ngrok forwarding URL, process ID, local URL, log file, or an exact blocker.",
            "",
            "8. Compact Handoff",
            "   - Ask: `Summarize the result, proof, current state, and next move.`",
            "   - Command: `mobile_dev.py handoff --result \"...\" --preview \"...\" --proof \"...\" --state \"...\" --next \"...\"`",
            "   - Gives: a phone-readable Result / Preview / Proof / State / Next summary.",
        ]
    )


def build_snapshot(root: Path) -> dict[str, Any]:
    root = root.resolve()
    detected = detect_project(root)
    candidate_ports = detected.get("candidate_ports") or []
    ports = dedupe([str(port) for port in [*COMMON_PORTS, *candidate_ports]])
    port_numbers = [int(port) for port in ports]
    servers = list_servers(root)
    return {
        "workspace": str(root),
        "workspace_key": workspace_key(root),
        "git": git_info(root),
        "detected": {
            "signals": detected.get("signals") or [],
            "package_manager": detected.get("package_manager"),
            "candidate_commands": detected.get("candidate_commands") or [],
            "candidate_ports": candidate_ports,
            "references": detected.get("references") or [],
        },
        "ports": port_statuses(port_numbers),
        "servers": servers,
        "proof_artifacts": collect_proof_artifacts(root),
        "registry": str(registry_path(root)),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }


def render_snapshot_markdown(data: dict[str, Any]) -> str:
    git = data["git"]
    detected = data["detected"]
    dirty = f"{git['dirty_count']} dirty file(s)"
    if git.get("dirty_truncated"):
        dirty += f" (+{git['dirty_truncated']} more)"
    lines = [
        "# Mobile Session Snapshot",
        "",
        f"Workspace: `{data['workspace']}`",
        f"Branch: `{git['branch']}`",
        f"Last Commit: `{git['last_commit']}`",
        f"Dirty State: {dirty}",
        f"Signals: {', '.join(detected['signals']) if detected['signals'] else 'none detected'}",
        f"Package Manager: {detected['package_manager'] or 'none detected'}",
        f"Generated: {data['generated_at']}",
        "",
        "## Candidate Commands",
    ]
    commands = detected.get("candidate_commands") or []
    lines.extend(f"- `{command}`" for command in commands) if commands else lines.append("- none detected")

    lines.extend(["", "## Ports"])
    for port, status in data["ports"].items():
        lines.append(f"- `{port}`: {status}")

    lines.extend(["", "## Server Registry"])
    servers = data.get("servers") or []
    if servers:
        for server in servers:
            lines.append(
                f"- `{server['name']}` port `{server['port']}` pid `{server['pid']}`: {server['status']} ({server['local_url']})"
            )
    else:
        lines.append("- no registered servers")

    dirty_files = git.get("dirty_files") or []
    lines.extend(["", "## Changed Files"])
    lines.extend(f"- `{item}`" for item in dirty_files) if dirty_files else lines.append("- none")

    artifacts = data.get("proof_artifacts") or []
    lines.extend(["", "## Recent Proof Artifacts"])
    if artifacts:
        for artifact in artifacts:
            lines.append(f"- `{artifact['path']}` ({artifact['size']} bytes, {artifact['modified']})")
    else:
        lines.append("- none found")

    refs = detected.get("references") or []
    lines.extend(["", "## Suggested References"])
    lines.extend(f"- `{ref}`" for ref in refs) if refs else lines.append("- none")
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


def safe_copy_artifact(source: Path, destination_dir: Path) -> dict[str, Any]:
    source = source.resolve()
    if not source.exists() or not source.is_file():
        return {"source": str(source), "copied": False, "reason": "not a file"}
    if is_secret_path(source) or source.stat().st_size > MAX_PROOF_COPY_BYTES:
        return {"source": str(source), "copied": False, "reason": "secret-like name or too large"}
    destination_dir.mkdir(parents=True, exist_ok=True)
    target = destination_dir / source.name
    if target.exists():
        target = destination_dir / f"{source.stem}-{hashlib.sha256(str(source).encode('utf-8')).hexdigest()[:8]}{source.suffix}"
    shutil.copy2(source, target)
    return {"source": str(source), "copied": True, "target": str(target.resolve()), "size": target.stat().st_size}


def render_proof_bundle_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# MobileCodex Proof Bundle",
        "",
        f"Workspace: `{data['workspace']}`",
        f"Bundle: `{data['bundle_dir']}`",
        f"Generated: {data['generated_at']}",
        "",
        "## Snapshot",
        "",
        data["snapshot_markdown"],
        "",
        "## Server Registry",
    ]
    servers = data.get("servers") or []
    if servers:
        for server in servers:
            lines.append(f"- `{server['name']}` port `{server['port']}`: {server['status']} ({server['local_url']})")
    else:
        lines.append("- no registered servers")

    lines.extend(["", "## Included Artifacts"])
    copied = data.get("copied_artifacts") or []
    if copied:
        for item in copied:
            if item.get("copied"):
                lines.append(f"- `{item['target']}` copied from `{item['source']}` ({item['size']} bytes)")
            else:
                lines.append(f"- skipped `{item['source']}`: {item['reason']}")
    else:
        lines.append("- none")

    log_tails = data.get("log_tails") or []
    if log_tails:
        lines.extend(["", "## Log Tails"])
        lines.extend(f"- {line}" for line in log_tails)
    return "\n".join(lines)


def proof_bundle(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    bundle_dir = Path(args.output).resolve() if args.output else root / "proof" / f"mobilecodex-{now_stamp()}"
    artifacts_dir = bundle_dir / "artifacts"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    snapshot_data = build_snapshot(root)
    snapshot_markdown = render_snapshot_markdown(snapshot_data)
    copied: list[dict[str, Any]] = []
    recent_artifacts = snapshot_data.get("proof_artifacts") or []
    for artifact in recent_artifacts:
        copied.append(safe_copy_artifact(Path(artifact["path"]), artifacts_dir))
    for include in args.include or []:
        copied.append(safe_copy_artifact(Path(include), artifacts_dir))

    log_tails: list[str] = []
    for log_file in args.log_file or []:
        log_tails.extend(read_log_tail(Path(log_file), args.log_lines))

    data = {
        "workspace": str(root),
        "bundle_dir": str(bundle_dir),
        "proof_file": str((bundle_dir / "proof.md").resolve()),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "snapshot": snapshot_data,
        "snapshot_markdown": snapshot_markdown,
        "servers": list_servers(root),
        "copied_artifacts": copied,
        "log_tails": log_tails,
    }
    proof_md = render_proof_bundle_markdown(data)
    (bundle_dir / "proof.md").write_text(proof_md, encoding="utf-8")

    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        print_json_or_markdown(
            {
                "result": "proof bundle created",
                "preview": data["proof_file"],
                "proof": [
                    f"bundle {data['bundle_dir']}",
                    f"{len([item for item in copied if item.get('copied')])} artifact(s) copied",
                    f"{len(log_tails)} log tail line(s)",
                ],
                "next": "Attach or reference the proof bundle in the mobile handoff.",
            },
            "markdown",
            "Proof Bundle",
        )
    return 0


def find_playwright_node_command(root: Path) -> list[str] | None:
    node = shutil.which("node")
    if node and (root / "node_modules" / "playwright").exists():
        return [node]
    return None


def find_playwright_cli_command(root: Path) -> list[str] | None:
    local = root / "node_modules" / ".bin" / ("playwright.cmd" if sys.platform.startswith("win") else "playwright")
    if local.exists():
        return [str(local)]
    direct = shutil.which("playwright")
    if direct:
        return [direct]
    npx = shutil.which("npx")
    if npx:
        return [npx, "--yes", "playwright"]
    return None


def fetch_basic_page_metrics(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            body = response.read(512_000).decode("utf-8", errors="replace")
            final_url = response.geturl()
    except Exception:
        return {"title": "unknown", "finalUrl": url, "horizontalScroll": "not measured", "metricsMode": "unavailable"}
    title_match = re.search(r"<title[^>]*>(.*?)</title>", body, re.IGNORECASE | re.DOTALL)
    title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
    return {"title": title or "unknown", "finalUrl": final_url, "horizontalScroll": "not measured", "metricsMode": "basic-http"}


def playwright_eval(root: Path, url: str, width: int, height: int, screenshot: Path) -> dict[str, Any]:
    command = find_playwright_node_command(root)
    screenshot.parent.mkdir(parents=True, exist_ok=True)
    if not command:
        cli = find_playwright_cli_command(root)
        if not cli:
            return {"ok": False, "error": "No Playwright CLI or npx was found on PATH."}
        try:
            completed = subprocess.run(
                [*cli, "screenshot", f"--viewport-size={width},{height}", url, str(screenshot)],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc), "command": " ".join([*cli, "screenshot", "<url>", "<path>"])}
        if completed.returncode != 0:
            return {
                "ok": False,
                "error": (completed.stderr or completed.stdout).strip(),
                "exit_code": completed.returncode,
                "command": " ".join([*cli, "screenshot", f"--viewport-size={width},{height}", url, str(screenshot)]),
                "screenshot": str(screenshot.resolve()),
            }
        return {
            "ok": True,
            "messages": [],
            "failed": [],
            "metrics": fetch_basic_page_metrics(url),
            "exit_code": completed.returncode,
            "command": " ".join([*cli, "screenshot", f"--viewport-size={width},{height}", "<url>", "<path>"]),
            "screenshot": str(screenshot.resolve()),
            "capture_mode": "playwright-cli-screenshot",
        }

    js = (
        "const { chromium } = require('playwright');"
        "(async()=>{"
        "const browser=await chromium.launch({headless:true});"
        f"const page=await browser.newPage({{viewport:{{width:{width},height:{height}}}}});"
        "const messages=[];const failed=[];"
        "page.on('console',m=>{if(['error','warning'].includes(m.type()))messages.push({type:m.type(),text:m.text()});});"
        "page.on('requestfailed',r=>failed.push({url:r.url(),failure:r.failure()?.errorText||'failed'}));"
        f"await page.goto({json.dumps(url)},{{waitUntil:'networkidle',timeout:30000}});"
        "const metrics=await page.evaluate(()=>({title:document.title,finalUrl:location.href,"
        "scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,"
        "horizontalScroll:document.documentElement.scrollWidth>document.documentElement.clientWidth+1}));"
        f"await page.screenshot({{path:{json.dumps(str(screenshot))},fullPage:false}});"
        "await browser.close();"
        "console.log(JSON.stringify({ok:true,messages,failed,metrics}));"
        "})().catch(err=>{console.error(err.stack||String(err));process.exit(1);});"
    )
    try:
        completed = subprocess.run(
            [*command, "-e", js],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc), "command": " ".join([*command, "-e", "<script>"])}
    output = (completed.stdout or "").strip().splitlines()
    json_line = output[-1] if output else ""
    try:
        data = json.loads(json_line)
    except Exception:
        data = {"ok": False, "error": (completed.stderr or completed.stdout).strip()}
    data["exit_code"] = completed.returncode
    data["command"] = " ".join([*command, "-e", "<script>"])
    data["screenshot"] = str(screenshot.resolve())
    if completed.returncode != 0:
        data["ok"] = False
        data["error"] = data.get("error") or (completed.stderr or completed.stdout).strip()
    return data


def render_ux_proof_markdown(data: dict[str, Any]) -> str:
    lines = [
        "# Mobile UX Proof",
        "",
        f"URL: {data['url']}",
        f"Output: `{data['out_dir']}`",
        f"Result: {data['result']}",
        "",
        "## Screenshots",
    ]
    for shot in data.get("screenshots", []):
        lines.append(f"- `{shot['label']}`: `{shot['path']}`")
    lines.extend(["", "## Browser State"])
    metrics = data.get("metrics") or {}
    lines.append(f"- Capture mode: {data.get('capture_mode', 'unknown')}")
    lines.append(f"- Title: {metrics.get('title', 'unknown')}")
    lines.append(f"- Final URL: {metrics.get('finalUrl', 'unknown')}")
    lines.append(f"- Horizontal scroll: {metrics.get('horizontalScroll', 'unknown')}")
    messages = data.get("console_messages") or []
    failed = data.get("failed_requests") or []
    lines.extend(["", "## Issues"])
    has_horizontal_scroll = metrics.get("horizontalScroll") is True
    if not messages and not failed and not has_horizontal_scroll:
        lines.append("- none detected")
    for message in messages:
        lines.append(f"- console {message.get('type')}: {message.get('text')}")
    for request in failed:
        lines.append(f"- request failed: {request.get('url')} ({request.get('failure')})")
    if has_horizontal_scroll:
        lines.append("- page has horizontal scroll at mobile width")
    return "\n".join(lines)


def ux_proof(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    out_dir = Path(args.out).resolve() if args.out else root / "proof" / f"mobilecodex-ux-{now_stamp()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    mobile_path = out_dir / "mobile-390x844.png"
    mobile = playwright_eval(root, args.url, 390, 844, mobile_path)
    if not mobile.get("ok"):
        data = {
            "result": "ux proof blocked",
            "url": args.url,
            "out_dir": str(out_dir),
            "proof": mobile,
            "next": "Install Playwright tooling or run `npx playwright install chromium`, then retry.",
        }
        print_json_or_markdown(data, args.format, "Mobile UX Proof")
        return 2

    screenshots = [{"label": "mobile 390x844", "path": str(mobile_path.resolve())}]
    desktop: dict[str, Any] | None = None
    if not args.mobile_only:
        desktop_path = out_dir / "desktop-1440x900.png"
        desktop = playwright_eval(root, args.url, 1440, 900, desktop_path)
        if desktop.get("ok"):
            screenshots.append({"label": "desktop 1440x900", "path": str(desktop_path.resolve())})

    data = {
        "result": "passed" if not mobile.get("messages") and not mobile.get("failed") and mobile.get("metrics", {}).get("horizontalScroll") is not True else "issues found",
        "url": args.url,
        "out_dir": str(out_dir.resolve()),
        "screenshots": screenshots,
        "console_messages": mobile.get("messages") or [],
        "failed_requests": mobile.get("failed") or [],
        "metrics": mobile.get("metrics") or {},
        "capture_mode": mobile.get("capture_mode") or "playwright-node",
        "mobile_command": mobile.get("command"),
        "desktop_error": None if not desktop or desktop.get("ok") else desktop.get("error"),
    }
    summary = render_ux_proof_markdown(data)
    (out_dir / "ux-proof.md").write_text(summary, encoding="utf-8")
    if args.format == "json":
        print(json.dumps(data, indent=2))
    else:
        print(summary)
    return 0


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
    if args.state:
        lines.append(f"State: {args.state}")
    next_items = args.next or []
    lines.append("Next: " + ("; ".join(next_items) if next_items else "no immediate next action"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mobile Codex Dev helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("menu", help="Show phone-readable MobileCodex capabilities")

    detect_parser = subparsers.add_parser("detect", help="Detect project shape and mobile proof hints")
    detect_parser.add_argument("--root", default=".", help="Project root")
    detect_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    snapshot_parser = subparsers.add_parser("snapshot", help="Create a mobile session state snapshot")
    snapshot_parser.add_argument("--root", default=".", help="Project root")
    snapshot_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    server_start_parser = subparsers.add_parser("server-start", help="Start and register a local preview server")
    server_start_parser.add_argument("--root", default=".", help="Project root")
    server_start_parser.add_argument("--name", required=True, help="Server label")
    server_start_parser.add_argument("--port", type=int, required=True, help="Local HTTP port")
    server_start_parser.add_argument("--wait", type=float, default=1.5, help="Seconds to wait before checking status")
    server_start_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    server_start_parser.add_argument("server_command", nargs=argparse.REMAINDER, help="Command to run after --")

    server_list_parser = subparsers.add_parser("server-list", help="List registered local preview servers")
    server_list_parser.add_argument("--root", default=".", help="Project root")
    server_list_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    server_stop_parser = subparsers.add_parser("server-stop", help="Stop a registered local preview server")
    server_stop_parser.add_argument("--root", default=".", help="Project root")
    server_stop_parser.add_argument("--name", help="Server label")
    server_stop_parser.add_argument("--port", type=int, help="Local HTTP port")
    server_stop_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    proof_bundle_parser = subparsers.add_parser("proof-bundle", help="Create a mobile-readable proof bundle")
    proof_bundle_parser.add_argument("--root", default=".", help="Project root")
    proof_bundle_parser.add_argument("--output", help="Output directory")
    proof_bundle_parser.add_argument("--include", action="append", default=[], help="Extra artifact to include")
    proof_bundle_parser.add_argument("--log-file", action="append", default=[], help="Log file to tail into the bundle")
    proof_bundle_parser.add_argument("--log-lines", type=int, default=12)
    proof_bundle_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    ux_proof_parser = subparsers.add_parser("ux-proof", help="Capture mobile UX proof for a URL")
    ux_proof_parser.add_argument("--url", required=True, help="URL to verify")
    ux_proof_parser.add_argument("--root", default=".", help="Project root")
    ux_proof_parser.add_argument("--out", help="Output directory")
    ux_proof_parser.add_argument("--mobile-only", action="store_true", help="Skip desktop screenshot")
    ux_proof_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

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
    handoff_parser.add_argument("--state")
    handoff_parser.add_argument("--next", action="append", default=[])
    handoff_parser.add_argument("--log-file")
    handoff_parser.add_argument("--log-lines", type=int, default=8)

    args = parser.parse_args(argv)

    if args.command == "menu":
        print(capability_menu())
        return 0

    if args.command == "detect":
        data = detect_project(Path(args.root))
        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            print(render_markdown_detection(data))
        return 0

    if args.command == "snapshot":
        data = build_snapshot(Path(args.root))
        if args.format == "json":
            print(json.dumps(data, indent=2))
        else:
            print(render_snapshot_markdown(data))
        return 0

    if args.command == "server-start":
        return server_start(args)

    if args.command == "server-list":
        return server_list(args)

    if args.command == "server-stop":
        if not args.name and not args.port:
            print_json_or_markdown(
                {"result": "server stop blocked", "proof": "missing --name or --port", "next": "Pass one registered server selector."},
                args.format,
                "Server Stop",
            )
            return 2
        return server_stop(args)

    if args.command == "proof-bundle":
        return proof_bundle(args)

    if args.command == "ux-proof":
        return ux_proof(args)

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
