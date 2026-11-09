"""
Terminal integration and shell hook manager for ollama-web.
Seamlessly integrates live web search and neural voice into the native 'ollama' command in terminal.
Supports Bash, Zsh, and Windows PowerShell with resilient binary discovery and fallback.
"""

import os
import sys
from pathlib import Path

HOOK_START = "# >>> ollama-web terminal integration >>>"
HOOK_END = "# <<< ollama-web terminal integration <<<"

BASH_ZSH_HOOK = f"""{HOOK_START}
# Seamlessly routes 'ollama run <model> "prompt"' and 'ollama web "query"' to ollama-web
ollama() {{
    # 1. Resolve ollama-web binary across PATH, ~/.local/bin, and standard virtualenvs
    local oweb_bin=""
    if command -v ollama-web >/dev/null 2>&1; then
        oweb_bin="ollama-web"
    elif command -v oweb >/dev/null 2>&1; then
        oweb_bin="oweb"
    elif [ -x "$HOME/.local/bin/ollama-web" ]; then
        oweb_bin="$HOME/.local/bin/ollama-web"
    elif [ -x "$HOME/ai-workspace/environments/tts-env/bin/ollama-web" ]; then
        oweb_bin="$HOME/ai-workspace/environments/tts-env/bin/ollama-web"
    fi

    # 2. Dedicated web search shortcut: 'ollama web ...' or 'ollama search ...'
    if [ "$1" = "web" ] || [ "$1" = "search" ]; then
        shift
        if [ -n "$oweb_bin" ]; then
            "$oweb_bin" "$@"
        else
            echo "[!] ollama-web binary not found. Please install: pip install ollama-web" >&2
            return 1
        fi
        return 0
    fi

    # 3. Intercept 'ollama run <model> [options...] "prompt"' (when prompt arguments exist)
    if [ "$1" = "run" ] && [ -n "$3" ] && [ -n "$oweb_bin" ]; then
        local model="$2"
        shift 2
        "$oweb_bin" -m "$model" "$@"
        return 0
    fi

    # 4. Clean pass-through for interactive REPL or all management commands (pull, list, serve, rm)
    command ollama "$@"
}}
{HOOK_END}
"""

POWERSHELL_HOOK = f"""{HOOK_START}
function ollama {{
    $oweb = Get-Command ollama-web -ErrorAction SilentlyContinue
    if (-not $oweb) {{
        $oweb = Get-Command oweb -ErrorAction SilentlyContinue
    }}

    if ($args[0] -eq 'web' -or $args[0] -eq 'search') {{
        $rest = $args[1..($args.Count - 1)]
        if ($oweb) {{
            & $oweb @rest
        }} else {{
            Write-Error "ollama-web binary not found. Please install: pip install ollama-web"
        }}
        return
    }}

    if ($args[0] -eq 'run' -and $args.Count -gt 2 -and $oweb) {{
        $model = $args[1]
        $rest = $args[2..($args.Count - 1)]
        & $oweb -m $model @rest
        return
    }}

    & (Get-Command -CommandType Application ollama) @args
}}
{HOOK_END}
"""


def get_target_shell_rc_files() -> list[Path]:
    """Finds active shell rc files in the user's home directory."""
    targets = []
    home = Path.home()

    if sys.platform == "win32":
        docs = home / "Documents" / "WindowsPowerShell"
        docs.mkdir(parents=True, exist_ok=True)
        targets.append(docs / "Microsoft.PowerShell_profile.ps1")
    else:
        bashrc = home / ".bashrc"
        if bashrc.exists():
            targets.append(bashrc)
        zshrc = home / ".zshrc"
        if zshrc.exists():
            targets.append(zshrc)
        if not targets:
            targets.append(bashrc)

    return targets


def is_hook_installed(rc_file: Path) -> bool:
    if not rc_file.exists():
        return False
    try:
        content = rc_file.read_text(encoding="utf-8")
        return HOOK_START in content
    except Exception:
        return False


def install_hook() -> bool:
    """Installs or updates the shell hook into active rc files."""
    targets = get_target_shell_rc_files()
    hook_content = POWERSHELL_HOOK if sys.platform == "win32" else BASH_ZSH_HOOK
    installed_any = False

    print("==================================================================")
    print(" 🔗 ollama-web Terminal Hook Installer")
    print("==================================================================")

    for rc in targets:
        # If already installed, replace with updated version
        if is_hook_installed(rc):
            try:
                content = rc.read_text(encoding="utf-8")
                before = content.split(HOOK_START)[0]
                after = content.split(HOOK_END)[1]
                cleaned = before.rstrip() + ("\n" + after.lstrip() if after.strip() else "\n")
                new_full = cleaned.rstrip() + "\n\n" + hook_content + "\n"
                rc.write_text(new_full, encoding="utf-8")
                print(f"✓ Updated terminal hook in: {rc}")
                installed_any = True
                continue
            except Exception as e:
                print(f"[!] Failed to update {rc}: {e}", file=sys.stderr)

        try:
            existing = rc.read_text(encoding="utf-8") if rc.exists() else ""
            prefix = "\n" if existing and not existing.endswith("\n") else ""
            with open(rc, "a", encoding="utf-8") as f:
                f.write(f"{prefix}{hook_content}\n")
            print(f"✓ Successfully installed terminal hook into: {rc}")
            installed_any = True
        except Exception as e:
            print(f"[!] Failed to write to {rc}: {e}", file=sys.stderr)

    if installed_any:
        print("\n🎉 Done! To activate in your current terminal, run:")
        if sys.platform == "win32":
            print("   . $PROFILE")
        else:
            first_rc = targets[0]
            print(f"   source {first_rc}")
        print("\nNow you can run:")
        print("  • ollama run <model> \"your live question\" (auto web search + voice)")
        print("  • ollama web \"latest sports scores or news\"")
        print("  • ollama list / ollama pull (standard native ollama commands)")
        print("==================================================================")
        return True

    return False


def remove_hook() -> bool:
    """Removes the shell hook from rc files."""
    targets = get_target_shell_rc_files()
    removed_any = False

    for rc in targets:
        if not rc.exists():
            continue
        try:
            content = rc.read_text(encoding="utf-8")
            if HOOK_START in content and HOOK_END in content:
                before = content.split(HOOK_START)[0]
                after = content.split(HOOK_END)[1]
                cleaned = before.rstrip() + ("\n" + after.lstrip() if after.strip() else "\n")
                rc.write_text(cleaned, encoding="utf-8")
                print(f"✓ Removed terminal hook from: {rc}")
                removed_any = True
        except Exception as e:
            print(f"[!] Error removing hook from {rc}: {e}", file=sys.stderr)

    if removed_any:
        print("Terminal hook removed. Reload your shell to apply changes.")
        return True
    else:
        print("No terminal hook found to remove.")
        return False
