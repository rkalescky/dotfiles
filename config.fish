if status is-interactive
set -g fish_greeting
abbr -a vi nvim
abbr -a vim nvim
abbr -a ghsshu gh_ssh_bootstrap
abbr -a ghsshd gh_ssh_cleanup
abbr -a bpriv bootstrap_private

if command -q squeue
    abbr -a cq 'squeue --me'
end

set -gx EDITOR nvim
set -gx VISUAL nvim
set -g GH_SSH_KEY_PATH "$HOME/.ssh/id_ed25519_gh"

function gh_ssh_bootstrap --description "Login to GitHub via SSH and upload local key"
if not type -q gh
echo "gh is not installed"
return 1
end

if not test -f "$GH_SSH_KEY_PATH"
mkdir -p "$HOME/.ssh"
chmod 700 "$HOME/.ssh"
ssh-keygen -t ed25519 -f "$GH_SSH_KEY_PATH" -N "" -C "$(whoami)@$(hostname)"
end

set -l ssh_config "$HOME/.ssh/config"
set -l managed_begin "# >>> gh-bootstrap >>>"
set -l managed_end "# <<< gh-bootstrap <<<"
touch "$ssh_config"
chmod 600 "$ssh_config"
set -l tmp_config (mktemp)
printf "%s\nHost github.com\n  HostName github.com\n  User git\n  IdentityFile %s\n  IdentitiesOnly yes\n%s\n" "$managed_begin" "$GH_SSH_KEY_PATH" "$managed_end" > "$tmp_config"
awk -v begin="$managed_begin" -v end="$managed_end" '
  $0 == begin { skip = 1; next }
  $0 == end { skip = 0; next }
  !skip { print }
' "$ssh_config" >> "$tmp_config"
mv "$tmp_config" "$ssh_config"
chmod 600 "$ssh_config"

gh auth login --git-protocol ssh --web
gh auth setup-git

set -l pubkey (string trim (cat "$GH_SSH_KEY_PATH.pub"))
set -l key_id (gh api user/keys --jq '.[] | select(.key == "'"$pubkey"'") | .id' 2>/dev/null)
if test -z "$key_id"
gh ssh-key add "$GH_SSH_KEY_PATH.pub" --title "$(hostname)"
end
end

function gh_ssh_cleanup --description "Delete uploaded local SSH key from GitHub and logout"
if not type -q gh
echo "gh is not installed"
return 1
end

if test -f "$GH_SSH_KEY_PATH.pub"
set -l pubkey (string trim (cat "$GH_SSH_KEY_PATH.pub"))
set -l key_ids (gh api user/keys --jq '.[] | select(.key == "'"$pubkey"'") | .id' 2>/dev/null)
for id in $key_ids
gh api -X DELETE "/user/keys/$id"
end
end

gh auth logout -h github.com
end

function bootstrap_private --description "Clone private dotfiles and rerun bootstrap"
set -l private_repo_dir "$HOME/.dotfiles_private"
set -l private_repo_url "git@github.com:rkalescky/dotfiles_private.git"
if set -q PRIVATE_BOOTSTRAP_REPO_URL
set private_repo_url "$PRIVATE_BOOTSTRAP_REPO_URL"
end
set -l public_bootstrap "$HOME/.dotfiles/bootstrap.sh"

if not test -x "$public_bootstrap"
echo "Public bootstrap not found at $public_bootstrap"
return 1
end

if test -d "$private_repo_dir/.git"
echo "Private dotfiles already present at $private_repo_dir"
"$public_bootstrap"
return $status
end

if not type -q gh
echo "gh is not installed"
return 1
end

if not git ls-remote "$private_repo_url" >/dev/null 2>&1
gh_ssh_bootstrap
or return $status
git ls-remote "$private_repo_url" >/dev/null 2>&1
or return 1
end

git clone "$private_repo_url" "$private_repo_dir"
or return $status

"$public_bootstrap"
end

end
