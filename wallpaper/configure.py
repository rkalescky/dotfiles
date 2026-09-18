#!/usr/bin/env python3
"""Configure macOS Aerial wallpaper using the format recorded by System Settings."""

import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import plistlib
import shutil
import tempfile


PROVIDER = "com.apple.wallpaper.choice.aerials"
ASSET = {"assetID": "shuffle-all-aerials"}
FREQUENCY = {"picker": {"_0": {"id": "shuffle_every_12_hours"}}}


def decode(data):
    return plistlib.loads(data) if isinstance(data, bytes) else {}


def set_encoded(container, key, value):
    # Compare decoded data so serialization differences do not trigger a reset.
    if decode(container.get(key)) != value:
        container[key] = plistlib.dumps(value, fmt=plistlib.FMT_BINARY)


def configure_entry(entry):
    previous = copy.deepcopy(entry.get("Content", {}))
    content = entry.setdefault("Content", {})
    choices = content.get("Choices", [])
    aerial = len(choices) == 1 and choices[0].get("Provider") == PROVIDER
    choice = copy.deepcopy(choices[0]) if aerial else {"Provider": PROVIDER}
    choice["Files"] = []
    set_encoded(choice, "Configuration", ASSET)
    content["Choices"] = [choice]
    content["Shuffle"] = "$null"
    options = decode(content.get("EncodedOptionValues")) if aerial else {}
    options.setdefault("values", {})["aerialShuffleFrequency"] = FREQUENCY
    set_encoded(content, "EncodedOptionValues", options)
    if content != previous:
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        entry["LastSet"] = now
        entry["LastUse"] = now


def configure_store(store):
    """Update existing wallpaper scopes, retaining their linkage and idle entries."""
    result = copy.deepcopy(store)
    entries = 0

    def visit(node):
        nonlocal entries
        if not isinstance(node, dict):
            return
        kind = node.get("Type")
        if kind in ("linked", "individual"):
            key = "Linked" if kind == "linked" else "Desktop"
            configure_entry(node.setdefault(key, {}))
            entries += 1
            return
        if kind == "idle":
            return
        for value in node.values():
            visit(value)

    visit(result)
    if not entries:
        raise ValueError("No supported wallpaper entries found; open Wallpaper settings once before running bootstrap.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, default=Path.home() / "Library/Application Support/com.apple.wallpaper/Store/Index.plist")
    parser.add_argument("--mode", choices=("apply", "check", "verify"), default="apply")
    args = parser.parse_args()
    original = args.dest.read_bytes()
    store = plistlib.loads(original)
    updated = configure_store(store)
    changed = updated != store
    if changed and args.mode == "apply":
        # Keep the previous store and replace atomically, including on interrupted runs.
        backup = args.dest.with_name(args.dest.name + ".bootstrap-backup")
        if not backup.exists():
            shutil.copy2(args.dest, backup)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=args.dest.parent, delete=False) as temp:
                temp_path = Path(temp.name)
                temp.write(plistlib.dumps(updated, fmt=plistlib.FMT_BINARY))
            temp_path.chmod(args.dest.stat().st_mode & 0o777)
            if args.dest.read_bytes() != original:
                raise RuntimeError("Wallpaper settings changed during bootstrap; rerun to apply the new selection.")
            os.replace(temp_path, args.dest)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
    print(json.dumps({"changed": changed}))
    if changed and args.mode == "verify":
        raise SystemExit("Wallpaper is not set to Shuffle All every 12 hours.")


if __name__ == "__main__":
    main()
