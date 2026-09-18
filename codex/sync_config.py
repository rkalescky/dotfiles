#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import tomllib

HEADER = [
    "# Managed by ~/.dotfiles/codex/sync_config.py.",
    "# Repo defaults are merged with local Codex state; destination-only keys are preserved.",
]
BARE_KEY_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge repo-managed Codex defaults into a local config.toml."
    )
    parser.add_argument("--source", required=True, type=Path, help="Repo-managed source TOML file")
    parser.add_argument("--dest", required=True, type=Path, help="Destination TOML file")
    return parser.parse_args()


def load_toml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = tomllib.loads(text)
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not parse as a TOML table")
    return data


def clone(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: clone(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone(item) for item in value]
    return value


def merge_tables(source: Mapping[str, Any], dest: Mapping[str, Any]) -> dict[str, Any]:
    merged: dict[str, Any] = {}

    for key, source_value in source.items():
        if key in dest:
            dest_value = dest[key]
            if isinstance(source_value, Mapping) and isinstance(dest_value, Mapping):
                merged[key] = merge_tables(source_value, dest_value)
            else:
                merged[key] = clone(source_value)
        else:
            merged[key] = clone(source_value)

    for key, dest_value in dest.items():
        if key not in merged:
            merged[key] = clone(dest_value)

    return merged


def is_bare_key(key: str) -> bool:
    return bool(key) and all(char in BARE_KEY_CHARS for char in key)


def format_key(key: str) -> str:
    return key if is_bare_key(key) else json.dumps(key)


def format_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        return "[" + ", ".join(format_value(item) for item in value) + "]"
    raise TypeError(f"Unsupported TOML value type: {type(value).__name__}")


def emit_table(path: list[str], table: Mapping[str, Any], lines: list[str]) -> None:
    if path:
        lines.append("[" + ".".join(format_key(part) for part in path) + "]")

    scalar_items: list[tuple[str, Any]] = []
    table_items: list[tuple[str, Mapping[str, Any]]] = []

    for key, value in table.items():
        if isinstance(value, Mapping):
            table_items.append((key, value))
        else:
            scalar_items.append((key, value))

    for key, value in scalar_items:
        lines.append(f"{format_key(key)} = {format_value(value)}")

    for index, (key, value) in enumerate(table_items):
        if lines and lines[-1] != "":
            lines.append("")
        emit_table(path + [key], value, lines)
        if index != len(table_items) - 1 and lines[-1] != "":
            lines.append("")


def render_toml(data: Mapping[str, Any]) -> str:
    lines = HEADER.copy()
    if data:
        lines.append("")
        emit_table([], data, lines)
    return "\n".join(lines).rstrip() + "\n"


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)


def backup_existing(dest: Path) -> Path | None:
    backup = dest.with_name(dest.name + ".pre-dotfiles-sync.bak")
    if backup.exists():
        return None
    shutil.copy2(dest, backup)
    return backup


def atomic_write(path: Path, content: str) -> None:
    ensure_parent_dir(path)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=path.name + ".", delete=False
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    os.chmod(temp_path, 0o600)
    os.replace(temp_path, path)


def main() -> int:
    args = parse_args()
    try:
        source_data = load_toml(args.source)
    except (FileNotFoundError, OSError, tomllib.TOMLDecodeError, TypeError) as exc:
        print(f"Failed to load source config: {exc}", file=sys.stderr)
        return 1

    dest_exists = args.dest.exists()
    try:
        dest_data = load_toml(args.dest) if dest_exists else {}
    except (FileNotFoundError, OSError, tomllib.TOMLDecodeError, TypeError) as exc:
        print(f"Failed to load destination config: {exc}", file=sys.stderr)
        return 1

    merged = merge_tables(source_data, dest_data)
    rendered = render_toml(merged)
    existing_text = args.dest.read_text(encoding="utf-8") if dest_exists else None

    if existing_text == rendered:
        print("changed=false")
        return 0

    backup_path: Path | None = None
    if dest_exists:
        backup_path = backup_existing(args.dest)

    try:
        atomic_write(args.dest, rendered)
    except OSError as exc:
        print(f"Failed to write destination config: {exc}", file=sys.stderr)
        return 1

    print("changed=true")
    if backup_path is not None:
        print(f"backup={backup_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
