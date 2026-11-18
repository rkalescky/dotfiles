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

HEADER_COMMENT = (
    "  // Managed by ~/.dotfiles/devin/sync_config.py. Repo defaults are merged\n"
    "  // with local Devin state; destination-only keys are preserved."
)
PERMISSION_LIST_KEYS = frozenset({"allow", "deny", "ask"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge repo-managed Devin defaults into a local config.json."
    )
    parser.add_argument("--source", required=True, type=Path, help="Repo-managed source JSON file")
    parser.add_argument("--dest", required=True, type=Path, help="Destination JSON file")
    return parser.parse_args()


def strip_jsonc(text: str) -> str:
    """Remove // and /* */ comments and trailing commas, respecting strings."""
    out: list[str] = []
    i = 0
    n = len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 1
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            while i < n and text[i] != "\n":
                i += 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        if ch == ",":
            lookahead = i + 1
            while lookahead < n and text[lookahead] in " \t\r\n":
                lookahead += 1
            if lookahead < n and text[lookahead] in "}]":
                i += 1
                continue
        out.append(ch)
        i += 1
    return "".join(out)


def load_jsonc(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return {}
    data = json.loads(strip_jsonc(text))
    if not isinstance(data, dict):
        raise TypeError(f"{path} did not parse as a JSON object")
    return data


def clone(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: clone(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clone(item) for item in value]
    return value


def merge_values(source_value: Any, dest_value: Any, path: tuple[str, ...]) -> Any:
    if isinstance(source_value, Mapping) and isinstance(dest_value, Mapping):
        return merge_tables(source_value, dest_value, path)
    if (
        len(path) == 2
        and path[0] == "permissions"
        and path[1] in PERMISSION_LIST_KEYS
        and isinstance(source_value, list)
        and isinstance(dest_value, list)
    ):
        merged_list = [clone(item) for item in dest_value]
        for item in source_value:
            if item not in merged_list:
                merged_list.append(clone(item))
        return merged_list
    return clone(source_value)


def merge_tables(
    source: Mapping[str, Any], dest: Mapping[str, Any], path: tuple[str, ...] = ()
) -> dict[str, Any]:
    merged: dict[str, Any] = {}

    for key, source_value in source.items():
        if key in dest:
            merged[key] = merge_values(source_value, dest[key], path + (key,))
        else:
            merged[key] = clone(source_value)

    for key, dest_value in dest.items():
        if key not in merged:
            merged[key] = clone(dest_value)

    return merged


def render_json(data: Mapping[str, Any]) -> str:
    body = json.dumps(data, indent=2, ensure_ascii=False)
    if body.startswith("{\n"):
        body = body.replace("{\n", "{\n" + HEADER_COMMENT + "\n", 1)
    return body.rstrip() + "\n"


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
        source_data = load_jsonc(args.source)
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError) as exc:
        print(f"Failed to load source config: {exc}", file=sys.stderr)
        return 1

    dest_exists = args.dest.exists()
    try:
        dest_data = load_jsonc(args.dest) if dest_exists else {}
    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError) as exc:
        print(f"Failed to load destination config: {exc}", file=sys.stderr)
        return 1

    merged = merge_tables(source_data, dest_data)
    rendered = render_json(merged)
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
