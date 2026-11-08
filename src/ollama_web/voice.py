"""
Cross-platform text-to-speech audio engine supporting Linux, macOS, and Windows.
Works out of the box on any OS with zero external audio daemons or API keys required.
Powered by Microsoft Edge-TTS neural voices by default, with optional local Kokoro/Piper acceleration.
"""

import os
import re
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path


def play_audio_file(file_path: str) -> bool:
    """
    Plays an audio file (.mp3 or .wav) natively across Linux, macOS, and Windows.
    Uses built-in OS tools without requiring external Python audio bindings.
    """
    if not os.path.exists(file_path) or os.path.getsize(file_path) < 100:
        return False

    # macOS: native afplay plays mp3/wav directly on every Mac
    if sys.platform == "darwin":
        if shutil.which("afplay"):
            res = subprocess.run(["afplay", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return res.returncode == 0

    # Windows: native PowerShell Media Player
    if sys.platform == "win32":
        abs_p = os.path.abspath(file_path).replace("\\", "\\\\")
        if file_path.endswith(".mp3"):
            ps_cmd = (
                f"$wmp = New-Object -ComObject WMPlayer.OCX; "
                f"$wmp.URL = '{abs_p}'; $wmp.controls.play(); "
                f"while ($wmp.playState -ne 1) {{ Start-Sleep -Milliseconds 100 }}"
            )
        else:
            ps_cmd = (
                f"$player = New-Object System.Media.SoundPlayer('{abs_p}'); "
                f"if ($player) {{ $player.PlaySync() }}"
            )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return res.returncode == 0

    # Linux: check audio backends in order of reliability for MP3/WAV
    # 1. mpv
    if shutil.which("mpv"):
        res = subprocess.run(["mpv", "--no-video", "--really-quiet", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # 2. ffplay (ffmpeg)
    if shutil.which("ffplay"):
        res = subprocess.run(["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # 3. mpg123 (lightweight MP3 player common on minimal Linux)
    if shutil.which("mpg123") and file_path.endswith(".mp3"):
        res = subprocess.run(["mpg123", "-q", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # 4. cvlc (VLC command line)
    if shutil.which("cvlc"):
        res = subprocess.run(["cvlc", "--play-and-exit", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # 5. pw-play (modern PipeWire audio player)
    if shutil.which("pw-play"):
        res = subprocess.run(["pw-play", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    # 6. paplay (PulseAudio): converts MP3 to WAV if ffmpeg/sox present
    if shutil.which("paplay"):
        if file_path.endswith(".mp3") and shutil.which("ffmpeg"):
            wav_tmp = file_path.rsplit(".", 1)[0] + ".wav"
            subprocess.run(["ffmpeg", "-y", "-i", file_path, wav_tmp], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if os.path.exists(wav_tmp):
                res = subprocess.run(["paplay", wav_tmp], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    os.remove(wav_tmp)
                except OSError:
                    pass
                if res.returncode == 0:
                    return True
        elif file_path.endswith(".wav"):
            res = subprocess.run(["paplay", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if res.returncode == 0:
                return True

    # 7. aplay (ALSA raw PCM player, WAV only)
    if shutil.which("aplay") and file_path.endswith(".wav"):
        res = subprocess.run(["aplay", "-q", file_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if res.returncode == 0:
            return True

    return False


def detect_voice_for_text(text: str) -> str:
    """
    Selects high-fidelity neural voice model matched to the primary linguistic script.
    Zero phonetic corruption: ensures Thai and Asian scripts are never fed to Latin-only models.
    """
    # Thai script
    if re.search(r"[\u0e00-\u0e7f]", text):
        return "th-TH-NiwatNeural"

    # CJK scripts (Chinese, Japanese, Korean)
    if re.search(r"[\u4e00-\u9fff]", text):
        return "zh-CN-YunxiNeural"
    if re.search(r"[\u3040-\u30ff]", text):
        return "ja-JP-NanamiNeural"
    if re.search(r"[\uac00-\ud7af]", text):
        return "ko-KR-SunHiNeural"

    # Cyrillic script
    if re.search(r"[\u0400-\u04ff]", text):
        return "ru-RU-DmitryNeural"

    # Arabic script
    if re.search(r"[\u0600-\u06ff]", text):
        return "ar-SA-HamedNeural"

    # Spanish script
    if re.search(r"[áéíóúñ¿¡]", text, re.IGNORECASE):
        return "es-ES-AlvaroNeural"

    # Latin / European scripts (default to warm British Baritone en-GB-RyanNeural)
    return "en-GB-RyanNeural"


def speak_text(text: str, engine: str = "edge") -> None:
    """
    Synthesizes speech aloud across Linux, macOS, and Windows.

    Engines:
    - 'edge' (Default, Universal): Uses Microsoft Edge-TTS neural voices across 75+ languages.
      Zero API keys, zero local model weights, pristine multi-lingual accuracy.
    - 'local' / 'kokoro' / 'piper': Optional local acceleration for users with local TTS daemons.
      Automatically falls back to Edge-TTS for non-Latin scripts (Thai, CJK) to prevent phonetic corruption.
    - 'off': Mutes speech.
    """
    if engine in ("off", "none", "mute"):
        return

    clean = re.sub(r"https?://\S+", "", text)
    clean = re.sub(r"[`*_#>\[\]()~|]+", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()
    if not clean:
        return

    # Summarize long text for spoken output so tables and code blocks don't flood audio
    words = clean.split()
    if len(words) > 85:
        clean = " ".join(words[:85]) + "... Full structured results and tables are displayed on your screen."

    is_thai = bool(re.search(r"[\u0e00-\u0e7f]", clean))
    is_cjk = bool(re.search(r"[\u4e00-\u9fff\u3040-\u30ff]", clean))

    # Optional Local Acceleration (Only if explicitly requested via --local-voice or config)
    if engine in ("local", "kokoro", "piper", "ai-say"):
        # Local English/Latin acceleration via ai-say, kokoro, or piper
        if not (is_thai or is_cjk):
            if shutil.which("ai-say"):
                cmd = ["ai-say", "--kokoro", clean] if engine in ("local", "kokoro") else ["ai-say", clean]
                res = subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
            elif shutil.which("kokoro"):
                res = subprocess.run(["kokoro", "-t", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if res.returncode == 0:
                    return
            elif shutil.which("piper"):
                pass  # Fall through to edge-tts if custom piper flags not configured

    # Universal Default Engine: Microsoft Edge-TTS (Zero keys, 75+ languages)
    try:
        import asyncio
        import edge_tts

        voice_name = detect_voice_for_text(clean)
        tmp_dir = Path(tempfile.gettempdir())
        out_mp3 = str(tmp_dir / "ollama_web_voice.mp3")

        comm = edge_tts.Communicate(clean, voice_name)
        if hasattr(comm, "save_sync"):
            comm.save_sync(out_mp3)
        else:
            asyncio.run(comm.save(out_mp3))

        if play_audio_file(out_mp3):
            return
    except Exception:
        pass  # Fall through to native OS fallback if offline or edge-tts fails

    # Native Operating System Voice Fallbacks (Offline emergency fallback)
    if sys.platform == "darwin" and shutil.which("say"):
        subprocess.run(["say", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform == "win32":
        escaped = clean.replace('"', '""').replace("'", "''")
        ps_cmd = (
            f"Add-Type -AssemblyName System.Speech; "
            f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            f"$synth.Speak('{escaped}')"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif sys.platform.startswith("linux"):
        if shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif shutil.which("espeak"):
            subprocess.run(["espeak", clean], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
