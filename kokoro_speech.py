#!/usr/bin/env python3
"""Kokoro TTS synthesis: ~3x realtime on CPU, the most natural offline voice.

Voices: af_heart (best overall, female), am_michael (best male narrator,
~167 wpm at natural speed), am_fenrir, am_puck, bm_george (British), ...
The first letter of the voice name selects the language ('a' American,
'b' British).
"""

import warnings
import wave
from pathlib import Path

import numpy as np

SAMPLE_RATE = 24000
SPEED = 1.0  # natural pace; lower = slower


def synthesize(text: str, wav_path: Path, voice: str = "af_heart") -> None:
    warnings.filterwarnings("ignore")
    from kokoro import KPipeline  # imports torch; keep out of module load

    pipeline = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")
    with wave.open(str(wav_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(SAMPLE_RATE)
        for _, _, audio in pipeline(text, voice=voice, speed=SPEED):
            pcm = (np.clip(audio.numpy(), -1.0, 1.0) * 32767).astype("<i2")
            wav_file.writeframes(pcm.tobytes())
