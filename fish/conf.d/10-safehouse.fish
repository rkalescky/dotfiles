if test (uname -s) = Darwin; and command -q safehouse
    function __safehouse_workdir
        set -l dir $PWD
        if test (count $argv) -gt 0
            set dir $argv[1]
        end
        set dir (realpath -- $dir)
        or return 1
        if test "$dir" = (realpath -- "$HOME"); or test "$dir" = /
            echo "safehouse: refusing to sandbox $dir; cd into a project directory first" >&2
            return 1
        end
        echo $dir
    end

    function safe --description "Run a command inside Agent Safehouse"
        set -l workdir_arg
        for arg in $argv
            if test "$arg" = --
                break
            else if string match -q -- "--workdir*" "$arg"
                set workdir_arg 1
                break
            else if not string match -q -- "-*" "$arg"
                break
            end
        end
        if test -z "$workdir_arg"
            set -l dir (__safehouse_workdir)
            or return 1
            set workdir_arg --workdir=$dir
        else
            set workdir_arg
        end
        safehouse --enable=gpu --env-pass=DEVELOPER_DIR,TOOLCHAINS --append-profile="$HOME/.config/safehouse/common.sb" $workdir_arg $argv
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
            set -l workdir
            set -l i 1
            while test $i -le (count $argv)
                set -l arg $argv[$i]
                if test "$arg" = --
                    break
                else if test "$arg" = -C; or test "$arg" = --cd
                    set i (math $i + 1)
                    if test $i -le (count $argv)
                        set workdir $argv[$i]
                    end
                    break
                else if string match -q -- "-C*" "$arg"
                    set workdir (string sub -s 3 -- $arg)
                    break
                else if string match -q -- "--cd=*" "$arg"
                    set workdir (string replace -- "--cd=" "" $arg)
                    break
                end
                set i (math $i + 1)
            end
            if test -n "$workdir"
                set -l dir (__safehouse_workdir $workdir)
                or return 1
                safe --workdir=$dir codex --dangerously-bypass-approvals-and-sandbox $argv
            else
                safe codex --dangerously-bypass-approvals-and-sandbox $argv
            end
        end
    end

    if command -q devin
        function devin --description "Devin CLI inside Agent Safehouse (bypass with `command devin`)"
            for arg in $argv
                if test "$arg" = --sandbox; or string match -q -- "--sandbox=*" "$arg"
                    echo "devin: --sandbox cannot be nested inside Safehouse; use `command devin --sandbox` instead" >&2
                    return 1
                end
            end
            safe --append-profile="$HOME/.config/safehouse/devin.sb" devin --permission-mode dangerous $argv
        end
    end
end
