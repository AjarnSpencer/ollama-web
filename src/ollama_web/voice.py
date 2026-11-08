"""
Cross-platform text-to-speech audio engine supporting Linux, macOS, and Windows.
"""

import os
import re
import sys
import shutil
import subprocess

def speak_text(text: str, engine: str = "auto") -> None:
    """Synthesizes speech aloud across Linux, macOS, and Windows with multilingual script routing."""
    clean = re.sub(r"https?://\S+", "", text)
    clean = re.sub(r"[`*_#>\[\]()~|]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return

    # Summarize long text for spoken output so tables don't flood audio
    words = clean.split()
    if len(words) > 85:
        clean = " ".join(words[:85]) + "... Full structured results and tables are displayed on your screen."

    # Multilingual script detection: Kokoro is English-only.
    # Non-Latin scripts (Thai, Chinese, Japanese) must route to appropriate neural voices.
    is_thai = bool(re.search(r"[\u0e00-\u0e7f]", clean))
    is_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", clean))

    if is_thai or is_cjk:
        try:
            import asyncio
            import edge_tts
            voice_name = "th-TH-NiwatNeural" if is_thai else "zh-CN-YunxiNeural"
            out_mp3 = "/tmp/ollama_web_voice_multi.mp3"
            out_wav = "/tmp/ollama_web_voice_multi.wav"

            async def _synth():
                comm = edge_tts.Communicate(clean, voice_name)
                await comm.save(out_mp3)

            asyncio.run(_synth())
            if os.path.exists(out_mp3) and os.path.getsize(out_mp3) > 100:
                if shutil.which("paplay"):
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", out_mp3, out_wav],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    subprocess.run(["paplay", out_wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
                    return
                elif shutil.which("ffplay"):
                    subprocess.run(
                        ["ffplay", "-nodisp", "-autoexit", out_mp3],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False
                    )
                    return
        except Exception:
            pass  # Fall through to platform TTS if edge_tts fails

    # Linux DGX Workstation / ai-say (English / Latin)
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
