if test (uname -s) = Darwin; and command -q safehouse
    function safe --description "Run a command inside Agent Safehouse"
        safehouse --enable=gpu --env-pass=DEVELOPER_DIR,TOOLCHAINS --append-profile="$HOME/.config/safehouse/common.sb" $argv
    end

    function safe-xcode --description "Run a command inside Agent Safehouse with Xcode integration"
        safe --enable=xcode $argv
    end

    if command -q claude
        function claude --description "Claude Code inside Agent Safehouse (bypass with `command claude`)"
            safe claude --dangerously-skip-permissions $argv
        end
    end

    if command -q codex
        function codex --description "Codex inside Agent Safehouse (bypass with `command codex`)"
            safe codex --dangerously-bypass-approvals-and-sandbox $argv
        end
    end

    if command -q devin
        function devin --description "Devin CLI inside Agent Safehouse (bypass with `command devin`)"
            safe --append-profile="$HOME/.config/safehouse/devin.sb" devin --permission-mode dangerous $argv
        end
    end
end
