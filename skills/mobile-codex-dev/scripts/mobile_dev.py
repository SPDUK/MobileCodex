#!/usr/bin/env python3
"""Utilities for the mobile-codex-dev skill.

The commands are intentionally read-only except for printing formatted output.
They help Codex quickly inspect a project, check ngrok availability, and format
a compact mobile handoff.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
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
    web_signals = {"next", "vite", "astro", "sveltekit", "angular", "storybook", "expo-or-react-native", "flutter"}
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


def print_json_or_markdown(data: dict[str, Any], format_name: str, title: str) -> None:
    if format_name == "json":
        print(json.dumps(data, indent=2))
        return
    print(f"# {title}")
    for key, value in data.items():
        print(f"- {key.replace('_', ' ').title()}: {value}")


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


def read_log_tail(path: Path, lines: int) -> list[str]:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as exc:
        return [f"log read failed for {path}: {exc}"]
    tail = content[-max(lines, 1):]
    return [f"{path}: {line}" for line in tail]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Mobile Codex Dev helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    detect_parser = subparsers.add_parser("detect", help="Detect project shape and mobile proof hints")
    detect_parser.add_argument("--root", default=".", help="Project root")
    detect_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

    ngrok_parser = subparsers.add_parser("ngrok-check", help="Check ngrok availability")
    ngrok_parser.add_argument("--format", choices=["markdown", "json"], default="markdown")

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

    if args.command == "handoff":
        print(format_handoff(args))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
