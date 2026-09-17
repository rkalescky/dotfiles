fish_add_path -g "$HOME/.local/bin"
fish_add_path -g "$HOME/.cargo/bin"
fish_add_path -g "$HOME/.pixi/bin"

if test (uname -s) = Darwin
    fish_add_path -g /opt/homebrew/bin /opt/homebrew/sbin /usr/local/bin /usr/local/sbin
end
