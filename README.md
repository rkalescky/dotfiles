# Dotfiles

## Run

```bash
curl -fsSL https://raw.githubusercontent.com/rkalescky/dotfiles/main/bootstrap.sh | bash
```

On macOS this ensures Homebrew is installed and installs/updates Pixi via `brew`; on Linux it installs/updates the standalone Pixi binary. It then syncs this repo to `~/.dotfiles` and runs `bootstrap.yml`.

Bootstrap always assumes a headless run: nothing prompts for input. Steps that need administrator access apply automatically when running as root or with passwordless sudo, and are skipped with a warning otherwise.

macOS bootstrap expects “Require password after screen saver begins or display is turned off” to be “Immediately”. Since `sysadminctl` needs the login password, bootstrap warns and skips when the setting is not already immediate; set it manually in System Settings > Lock Screen.

The macOS firewall is enabled with “Block all incoming connections”, both automatic allow options (built-in and downloaded signed software), and stealth mode turned on. Changes apply automatically with passwordless sudo and are skipped with a warning otherwise. To apply only these firewall settings, run:

```bash
~/.pixi/envs/ansible/bin/ansible-playbook -i inventory/localhost.yml bootstrap.yml --tags macos-firewall
```

Bootstrap also enables “Require an administrator password to access system-wide settings” when passwordless sudo is available, and warns and skips otherwise. Use `--tags macos-admin-settings` to apply only this setting.

Wallpaper uses Shuffle Aerials → Shuffle All, changing every 12 hours. Use `--tags macos-wallpaper` to apply only the wallpaper configuration. Existing display/Space assignments and wallpaper/screen saver linkage are preserved; the original wallpaper store is backed up before the first change.

For forks, set `BOOTSTRAP_REPO_URL` to your public repo URL before running bootstrap. If your private repo lives somewhere else, set `PRIVATE_BOOTSTRAP_REPO_URL` as well.

If `~/.dotfiles_private/bootstrap.nu` exists, the public bootstrap runs it afterward. If it does not exist, bootstrap completes with only the public repo.

For first-time private setup, run `bootstrap_private` from Fish after bootstrap completes. It will use GitHub SSH bootstrap if needed, clone `PRIVATE_BOOTSTRAP_REPO_URL` if set or else `git@github.com:rkalescky/dotfiles_private.git` into `~/.dotfiles_private`, and rerun the public bootstrap.

GitHub SSH bootstrap attempts to load the key into ssh-agent, but warns and continues if loading fails, including when no agent is running. Unsandboxed SSH can use the key on disk. Generated keys are passphrase-protected; on macOS `ssh-add --apple-use-keychain` stores the passphrase in the keychain so later loads do not prompt.

## Git config

Bootstrap installs shared Git defaults in `~/.config/git/dotfiles.gitconfig` and adds a managed include at the beginning of `~/.gitconfig`. It preserves existing personal settings and includes, and backs up `~/.gitconfig` when changing the include block. Personal settings after the include take precedence over shared defaults; use `git config --global` normally for your identity and other preferences. Existing includes for `~/.gitconfig.local`, `~/.gitconfig-work`, and `~/.gitconfig-personal` are preserved but are no longer installed as shared defaults.

To apply only the Git configuration change:

```bash
~/.pixi/envs/ansible/bin/ansible-playbook -i inventory/localhost.yml bootstrap.yml --tags git-config
```

## Codex config

`codex/config.toml` is the shared, machine-agnostic Codex defaults file. Bootstrap merges those defaults into `~/.codex/config.toml` instead of copying or symlinking the whole file, so local Codex-managed state such as trusted projects and notices survives across runs.

## Devin config

`devin/config.json` is the shared, machine-agnostic Devin defaults file. Bootstrap merges those defaults into `~/.config/devin/config.json` instead of copying or symlinking the whole file, so Devin-managed state such as the organization id and interactive "always allow" grants survives across runs. `permissions.allow`/`deny`/`ask` lists are unioned rather than replaced; every other managed key wins over the local value.

The managed defaults set `process_model` to `in-process` (sessions run inside each `devin` process rather than the shared background daemon) and `permission_mode` to `normal`, so unwrapped invocations (`command devin`, editor-spawned `devin acp`) prompt for shell commands and writes. The Safehouse fish wrapper passes `--permission-mode dangerous` per launch, keeping wrapped sessions unattended inside the sandbox. `permissions.allow` seeds a small read-only `Exec(...)` list (git status/diff/log/show/remote/fetch, wc, grep, sed, ls); because permission lists union rather than replace, removing an entry here does not remove it locally — delete any unwanted entries (e.g. a previously merged `exec` or `mcp__*`) from `~/.config/devin/config.json` once by hand.

## Agent Safehouse

Bootstrap installs Devin CLI through the [official install script](https://docs.devin.ai/cli) on macOS and Linux. The installer places `devin` in `~/.local/bin`, which is included in the Fish path.

Bootstrap skips the installer's interactive setup wizard. Run `devin setup` in a terminal after bootstrap to authenticate and configure MCP. Bootstrap fails if the installer changes its setup invocation, so the skip can be reviewed.

Claude Code and Codex are installed through their official install scripts (`claude.ai/install.sh` and `chatgpt.com/codex/install.sh`) on macOS and Linux, with executables at `~/.local/bin/claude` and `~/.local/bin/codex`. Bootstrap removes the superseded `claude-code`, `codex`, and `devin-cli` Homebrew casks on macOS.

On macOS, bootstrap installs `agent-safehouse` and a Fish snippet that runs `claude`, `codex`, and `devin` inside [Agent Safehouse](https://agent-safehouse.dev) with their permission prompts disabled; the kernel sandbox limits writes to the launch directory. Use `command codex` (etc.) to run unsandboxed, or `safe <cmd>` to wrap any other command.

All wrappers enable Safehouse's GPU integration only, which covers Metal compute — PyTorch MPS, OpenMM-Metal, and burn/cubecl need nothing more. Xcode integration (Xcode app bundles, the full Apple Command Line Tools tree, and scoped simulator/device state) is available on demand via `safe-xcode <cmd>` or a trusted `.safehouse` file with `enable=xcode`; it is needed for `xcrun metal` offline shader compilation, `xcodebuild`, simulators, CLT Swift, `xctrace`/Instruments recording, and OpenCL on GPU. `safe-xcode` and `devin-xcode` append `xcode-extras.sb`, which permits the `com.apple.dt.*` XPC services that load Instruments' analysis cores, task-port access for `--attach` profiling, and the OpenCL cl2Metal JIT path — `com.apple.metalfe`/`com.apple.gpuarchiver` lookups plus file-extension issuance scoped to the shader caches. CPU OpenCL devices work in any session; GPU OpenCL works only in these opt-in sessions, not in plain `safe`. Additional toolchains in `/Library/Developer/Toolchains` and `~/Library/Developer/Toolchains` are readable. `DEVELOPER_DIR` and `TOOLCHAINS` selections are passed through. Homebrew tools are readable through Safehouse's baseline policy, and Fish adds the standard Apple Silicon and Intel Homebrew binary directories to `PATH`. Keg-only tools remain available by their explicit paths, such as `/opt/homebrew/opt/swift/bin/swiftc`. These grants do not permit modifying installed toolchains or Homebrew packages. Apply changes with bootstrap and start a new agent session; an existing sandbox cannot gain these permissions.

On macOS, Fish also adds `/Library/TeX/texbin` to `PATH` when installed. The shared Safehouse profile grants read-only access to `/Library/TeX` for every wrapped agent and `safe` command; the backing TeX Live distribution under `/usr` is covered by Safehouse's baseline policy.

`~/.pixi` is readable (read-only) inside the sandbox, so `make bootstrap` syntax checks and Pixi-installed tools such as Ansible work when wrapped.

Devin has no upstream Safehouse profile, so `safehouse/devin.sb` grants its state directories. Never pass `--sandbox` to Devin inside Safehouse; the wrapper uses `--permission-mode dangerous` instead. Unwrapped invocations follow the `normal` permission mode from the managed config and prompt per action.

Safehouse wrappers do not enable SSH integration, load SSH identities, or grant access to the GitHub public key. The shared overlay additionally denies SCM and package-manager credential stores (`~/.config/gh`, `~/.config/glab-cli` and their cache/state dirs, `~/.npmrc`, `~/.config/pnpm`, `~/Library/Preferences/pnpm`, `~/.config/configstore`, `~/.local/share/uv/credentials`, `~/.cargo/credentials*`, `~/.netrc`). Run authenticated GitHub/GitLab and registry operations outside the sandbox. `~/.dotfiles_private` must be a real directory, not a symlink, because the sandbox matches resolved paths. Safehouse installation and wrapper functions are restricted to macOS.

To grant extra directories per launch, use `safehouse --add-dirs-ro=~/other-repo -- codex ...`, or place a trusted `.safehouse` file in the workdir. The wrappers refuse to run with `$HOME` or `/` as the workdir, and `codex -C DIR` scopes the sandbox to DIR.

What remains readable by design: the agents' own state (`~/.codex`, `~/.claude`, and Devin credentials under `~/.local/share/devin`), which they cannot function without, and the keychain, microphone, and browser-native-messaging integrations Safehouse auto-injects for `claude` and `codex`. Outbound network access is unrestricted by Safehouse's design.

## btop on Linux

Linux bootstrap builds btop from the pinned upstream source with Pixi's build system. The local recipe enables dynamic GPU support; it replaces the conda-forge btop global tool. macOS continues to install btop through Homebrew.

## Lima VMs

Use the dedicated playbook target to configure the Lima VM set.

```bash
make lima-vms
```

To recreate and start:

```bash
make lima-vms EXTRA_ARGS="-e lima_vm_recreate=true"
```

When changing the base image (e.g. 24.04 -> 22.04), recreate is required.

By default, VM start runs in parallel. Disable that with:

```bash
make lima-vms EXTRA_ARGS="-e lima_vm_start_parallel=false"
```

Each VM mounts only `~/share` (writable) from the host — a dedicated exchange point, not the host home directory, so guest processes cannot reach host credentials or the private dotfiles checkout. The guest home is its own disk; user provisioning bootstraps the public repo inside it.
