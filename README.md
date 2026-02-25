# Dotfiles

## Run

```bash
curl -fsSL https://raw.githubusercontent.com/rkalescky/dotfiles/main/bootstrap.sh | bash
```

This installs/updates Pixi, syncs this repo to `~/.dotfiles`, and runs `bootstrap.yml`.

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
