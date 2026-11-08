"""
Optional audio companion dispatcher for ollama-web.
Delegates to ollama-speak if installed, or provides guidance on installing it.
Zero audio dependencies inside pure ollama-web.
"""

import sys
import shutil
import subprocess


def speak_text(text: str) -> None:
    """Dispatches text to ollama-speak if available."""
    clean = text.strip()
    if not clean:
        return

    # 1. Check for standalone ollama-speak / ospeak command
    speak_cmd = shutil.which("ollama-speak") or shutil.which("ospeak")
    if speak_cmd:
        try:
            subprocess.run([speak_cmd, clean], check=False)
            return
        except Exception:
            pass

    # 2. If edge-tts is present in environment, allow seamless fallback
    try:
        import asyncio
        import tempfile
        import os
        import edge_tts

        voice = "th-TH-NiwatNeural" if any("\u0e00" <= c <= "\u0e7f" for c in clean) else "en-GB-RyanNeural"
        out_mp3 = os.path.join(tempfile.gettempdir(), "ollama_web_voice.mp3")
        comm = edge_tts.Communicate(clean[:400], voice)
        if hasattr(comm, "save_sync"):
            comm.save_sync(out_mp3)
        else:
            asyncio.run(comm.save(out_mp3))

        if sys.platform == "darwin" and shutil.which("afplay"):
            subprocess.run(["afplay", out_mp3], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        elif sys.platform == "win32":
            abs_p = os.path.abspath(out_mp3).replace("\\", "\\\\")
            ps_cmd = (
                f"$wmp = New-Object -ComObject WMPlayer.OCX; "
                f"$wmp.URL = '{abs_p}'; $wmp.controls.play(); "
                f"while ($wmp.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return
        else:
            for p in ["mpv", "ffplay", "mpg123", "pw-play"]:
                bin_path = shutil.which(p)
                if bin_path:
                    if p == "mpv":
                        subprocess.run(["mpv", "--no-video", "--really-quiet", out_mp3], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif p == "ffplay":
                        subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", out_mp3], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif p == "mpg123":
                        subprocess.run(["mpg123", "-q", out_mp3], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    elif p == "pw-play":
                        subprocess.run(["pw-play", out_mp3], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
    except Exception:
        pass

    print("\n[Tip] For spoken audio output, install ollama-speak: pip install 'ollama-web[speak]' (or: pip install ollama-speak)", file=sys.stderr)
