# Dotfiles

## Run

```bash
curl -fsSL https://raw.githubusercontent.com/rkalescky/dotfiles/main/bootstrap.sh | bash
```

On macOS this ensures Homebrew is installed and installs/updates Pixi via `brew`; on Linux it installs/updates the standalone Pixi binary. It then syncs this repo to `~/.dotfiles` and runs `bootstrap.yml`.

macOS bootstrap also sets “Require password after screen saver begins or display is turned off” to “Immediately”. If a change is needed, bootstrap asks for your login password in a hidden terminal prompt and verifies the effective setting afterward. Homebrew installation can also prompt for your administrator password, including when using the piped command above.

The macOS firewall is enabled with “Block all incoming connections”, both automatic allow options (built-in and downloaded signed software), and stealth mode turned on. Bootstrap prompts for administrator authentication when needed and verifies the settings. To apply only these firewall settings, run:

```bash
~/.pixi/envs/ansible/bin/ansible-playbook -i inventory/localhost.yml bootstrap.yml --tags macos-firewall
```

Bootstrap also enables “Require an administrator password to access system-wide settings”. Use `--tags macos-admin-settings` to apply only this setting; administrator authentication is requested only when a change needs it.

Wallpaper uses Shuffle Aerials → Shuffle All, changing every 12 hours. Use `--tags macos-wallpaper` to apply only the wallpaper configuration. Existing display/Space assignments and wallpaper/screen saver linkage are preserved; the original wallpaper store is backed up before the first change.

For forks, set `BOOTSTRAP_REPO_URL` to your public repo URL before running bootstrap. If your private repo lives somewhere else, set `PRIVATE_BOOTSTRAP_REPO_URL` as well.

If `~/.dotfiles_private/bootstrap.nu` exists, the public bootstrap runs it afterward. If it does not exist, bootstrap completes with only the public repo.

For first-time private setup, run `bootstrap_private` from Fish after bootstrap completes. It will use GitHub SSH bootstrap if needed, clone `PRIVATE_BOOTSTRAP_REPO_URL` if set or else `git@github.com:rkalescky/dotfiles_private.git` into `~/.dotfiles_private`, and rerun the public bootstrap.

GitHub SSH bootstrap attempts to load the key into ssh-agent, but warns and continues if loading fails, including when no agent is running. Unsandboxed SSH can use the key on disk; Safehouse launches still require successful agent loading when the key exists.

## Codex config

`codex/config.toml` is the shared, machine-agnostic Codex defaults file. Bootstrap merges those defaults into `~/.codex/config.toml` instead of copying or symlinking the whole file, so local Codex-managed state such as trusted projects and notices survives across runs.

## Agent Safehouse

Bootstrap installs Devin CLI through the `devin-cli` Homebrew cask on macOS and the [official install script](https://docs.devin.ai/cli) on Linux. The Linux installer places `devin` in `~/.local/bin`, which is included in the Fish path.

On macOS, bootstrap installs `agent-safehouse` and a Fish snippet that runs `claude`, `codex`, and `devin` inside [Agent Safehouse](https://agent-safehouse.dev) with their permission prompts disabled; the kernel sandbox limits writes to the launch directory. Use `command codex` (etc.) to run unsandboxed, or `safe <cmd>` to wrap any other command.

All wrappers enable Safehouse's GPU and Xcode integrations for Metal, Xcode app bundles, the full Apple Command Line Tools tree, and scoped build/simulator state. Additional toolchains in `/Library/Developer/Toolchains` and `~/Library/Developer/Toolchains` are readable. `DEVELOPER_DIR` and `TOOLCHAINS` selections are passed through. Homebrew tools are readable through Safehouse's baseline policy, and Fish adds the standard Apple Silicon and Intel Homebrew binary directories to `PATH`. Keg-only tools remain available by their explicit paths, such as `/opt/homebrew/opt/swift/bin/swiftc`. These grants do not permit modifying installed toolchains or Homebrew packages. Apply changes with bootstrap and start a new agent session; an existing sandbox cannot gain these permissions.

Devin has no upstream Safehouse profile, so `safehouse/devin.sb` grants its state directories. Never pass `--sandbox` to Devin inside Safehouse; the wrapper uses `--permission-mode dangerous` instead.

SSH keys are never readable inside the sandbox; `git push` works through ssh-agent. Before each `safe` or wrapped agent launch, the GitHub key is loaded outside the sandbox if it exists and is missing from the agent, including after a reboot or agent restart. An identity-loading failure stops the launch. `gh_ssh_bootstrap` uses the same helper, selecting `ssh-add --apple-use-keychain` on macOS and plain `ssh-add` on Linux. `safehouse/common.sb` allows reading only the public key so `IdentitiesOnly` can pick the agent identity. Safehouse installation and wrapper functions are restricted to macOS.

To grant extra directories per launch, use `safehouse --add-dirs-ro=~/other-repo -- codex ...`, or place a trusted `.safehouse` file in the workdir.

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
