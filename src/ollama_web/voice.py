"""
Local audio companion dispatcher for ollama-web.
Delegates to local 100% offline ollama-speak (Kokoro-82M / Piper) or local voice daemons.
Zero telemetry, zero cloud APIs, zero audio dependencies inside pure ollama-web.
"""

import sys
import shutil
import subprocess


def speak_text(text: str) -> None:
    """Dispatches text to local ollama-speak or local voice daemons if available."""
    clean = text.strip()
    if not clean:
        return

    # 1. Check for standalone ollama-speak / ospeak command (Kokoro-82M / Piper)
    speak_cmd = shutil.which("ollama-speak") or shutil.which("ospeak")
    if speak_cmd:
        try:
            subprocess.run([speak_cmd, clean], check=False)
            return
        except Exception:
            pass

    # 2. Check for host local voice daemon shortcut (ai-say)
    ai_say = shutil.which("ai-say")
    if ai_say:
        try:
            subprocess.run([ai_say, "--kokoro", clean], check=False)
            return
        except Exception:
            pass

    print("\n[Tip] For 100% local spoken audio (Kokoro-82M / Piper), install ollama-speak:\n      pip install ollama-speak", file=sys.stderr)
