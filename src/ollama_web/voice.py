"""
Cross-platform text-to-speech audio engine supporting Linux, macOS, and Windows.
"""

import os
import re
import sys
import shutil
import subprocess

def speak_text(text: str, engine: str = "auto") -> None:
    """Synthesizes speech aloud across Linux, macOS, and Windows."""
    clean = re.sub(r"https?://\S+", "", text)
    clean = re.sub(r"[`*_#>\[\]()~|]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return

    # Summarize long text for spoken output so tables don't flood audio
    words = clean.split()
    if len(words) > 85:
        clean = " ".join(words[:85]) + "... Full structured results and tables are displayed on your screen."

    # Linux DGX Workstation / ai-say
    if sys.platform.startswith("linux"):
        if shutil.which("ai-say"):
            cmd = ["ai-say", "--kokoro", clean] if engine in ("kokoro", "auto") else ["ai-say", clean]
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # macOS Native 'say'
    elif sys.platform == "darwin":
        if shutil.which("say"):
            subprocess.run(["say", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Windows PowerShell SAPI
    elif sys.platform == "win32":
        escaped = clean.replace('"', '""').replace("'", "''")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Speak('{escaped}')"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
