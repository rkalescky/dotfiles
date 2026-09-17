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

## Codex config

`codex/config.toml` is the shared, machine-agnostic Codex defaults file. Bootstrap merges those defaults into `~/.codex/config.toml` instead of copying or symlinking the whole file, so local Codex-managed state such as trusted projects and notices survives across runs.

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
