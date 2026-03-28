# Dotfiles

## Run

```bash
curl -fsSL https://raw.githubusercontent.com/rkalescky/dotfiles/main/bootstrap.sh | bash
```

This installs/updates Pixi, syncs this repo to `~/.dotfiles`, and runs `bootstrap.yml`.

For forks, set `BOOTSTRAP_REPO_URL` to your public repo URL before running bootstrap. If your private repo lives somewhere else, set `PRIVATE_BOOTSTRAP_REPO_URL` as well.

If `~/.dotfiles_private/bootstrap.nu` exists, the public bootstrap runs it afterward. If it does not exist, bootstrap completes with only the public repo.

For first-time private setup, run `bootstrap_private` from Fish after bootstrap completes. It will use GitHub SSH bootstrap if needed, clone `PRIVATE_BOOTSTRAP_REPO_URL` if set or else `git@github.com:rkalescky/dotfiles_private.git` into `~/.dotfiles_private`, and rerun the public bootstrap.

## Codex config

`codex/config.toml` is the shared, machine-agnostic Codex defaults file. Bootstrap merges those defaults into `~/.codex/config.toml` instead of copying or symlinking the whole file, so local Codex-managed state such as trusted projects and notices survives across runs.

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
