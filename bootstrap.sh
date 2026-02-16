#!/usr/bin/env bash
set -euo pipefail

PLAYBOOK_REL_PATH="${1:-bootstrap.yml}"
PIXI_BIN="$HOME/.pixi/bin/pixi"
BOOTSTRAP_DIR="$HOME/.dotfiles"
BOOTSTRAP_REPO_URL="${BOOTSTRAP_REPO_URL:-https://github.com/rkalescky/dotfiles.git}"
PIXI_PATH_BLOCK_BEGIN="# >>> pixi-path >>>"
PIXI_PATH_BLOCK_END="# <<< pixi-path <<<"

upsert_managed_block() {
  local file="$1"
  local block="$2"
  local tmp
  tmp="$(mktemp)"
  touch "$file"
  awk -v begin="$PIXI_PATH_BLOCK_BEGIN" -v end="$PIXI_PATH_BLOCK_END" '
    $0 == begin { skip = 1; next }
    $0 == end { skip = 0; next }
    !skip { print }
  ' "$file" >"$tmp"
  printf "%s\n%s\n%s\n" "$PIXI_PATH_BLOCK_BEGIN" "$block" "$PIXI_PATH_BLOCK_END" >>"$tmp"
  mv "$tmp" "$file"
}

resolve_pixi_target() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os:$arch" in
    Linux:x86_64) echo "x86_64-unknown-linux-musl" ;;
    Linux:aarch64 | Linux:arm64) echo "aarch64-unknown-linux-musl" ;;
    Darwin:x86_64) echo "x86_64-apple-darwin" ;;
    Darwin:arm64) echo "aarch64-apple-darwin" ;;
    *) return 1 ;;
  esac
}

install_or_update_pixi() {
  local target asset base_url tmp_dir tmp_bin release_json expected actual
  target="$(resolve_pixi_target || true)"
  if [[ -z "$target" ]]; then
    echo "Unsupported OS/architecture for Pixi: $(uname -s) $(uname -m)" >&2
    return 1
  fi
  asset="pixi-${target}"
  base_url="https://github.com/prefix-dev/pixi/releases/latest/download"
  tmp_dir="$(mktemp -d)"
  tmp_bin="${tmp_dir}/${asset}"
  trap 'rm -rf "$tmp_dir"' RETURN

  mkdir -p "$HOME/.pixi/bin"
  curl -fsSL -o "$tmp_bin" "${base_url}/${asset}"

  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is required to validate Pixi release metadata digest." >&2
    return 1
  fi

  release_json="$(curl -fsSL https://api.github.com/repos/prefix-dev/pixi/releases/latest)"
  expected="$(python3 -c '
import json,sys
data=json.load(sys.stdin)
asset=sys.argv[1]
for a in data.get("assets", []):
    if a.get("name") == asset:
        digest=a.get("digest","")
        if digest.startswith("sha256:"):
            print(digest.split(":",1)[1])
            raise SystemExit(0)
raise SystemExit(1)
' "$asset" <<<"$release_json")"

  if command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$tmp_bin" | awk '{print $1}')"
  elif command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$tmp_bin" | awk '{print $1}')"
  else
    echo "No checksum tool found (sha256sum/shasum)." >&2
    return 1
  fi

  [[ "$expected" == "$actual" ]]

  install -m 0755 "$tmp_bin" "$PIXI_BIN"
}

if [[ ! -x "$PIXI_BIN" ]]; then
  install_or_update_pixi
else
  "$PIXI_BIN" self-update
fi

export PATH="$HOME/.pixi/bin:$PATH"

upsert_managed_block "$HOME/.profile" 'export PATH="$HOME/.pixi/bin:$PATH"'
upsert_managed_block "$HOME/.bashrc" 'export PATH="$HOME/.pixi/bin:$PATH"'
upsert_managed_block "$HOME/.zshrc" '[ -f "$HOME/.profile" ] && . "$HOME/.profile"'

if ! command -v git >/dev/null 2>&1; then
  echo "git is required to sync bootstrap repository." >&2
  exit 1
fi

if [[ -d "$BOOTSTRAP_DIR/.git" ]]; then
  git -C "$BOOTSTRAP_DIR" pull --ff-only
elif [[ -e "$BOOTSTRAP_DIR" ]]; then
  echo "$BOOTSTRAP_DIR exists but is not a git repository." >&2
  exit 1
else
  git clone --depth 1 "$BOOTSTRAP_REPO_URL" "$BOOTSTRAP_DIR"
fi

PLAYBOOK_PATH="$BOOTSTRAP_DIR/$PLAYBOOK_REL_PATH"
if [[ ! -f "$PLAYBOOK_PATH" ]]; then
  echo "Playbook not found: $PLAYBOOK_PATH" >&2
  exit 1
fi

"$PIXI_BIN" global install --channel conda-forge ansible

"$HOME/.pixi/envs/ansible/bin/ansible-playbook" -i localhost, -c local "$PLAYBOOK_PATH"
