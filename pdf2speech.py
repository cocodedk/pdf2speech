#!/usr/bin/env python3
"""Convert an English text PDF to spoken audio (WAV) at a moderate reading pace."""

import argparse
import re
import sys
import wave
from pathlib import Path

from piper import PiperVoice, SynthesisConfig
from pypdf import PdfReader

VOICE_MODEL = Path(__file__).resolve().parent / "voices" / "en_US-lessac-medium.onnx"

# 1.0 is the voice's natural pace (~160 words per minute, a comfortable
# audiobook speed). Higher = slower, lower = faster.
LENGTH_SCALE = 1.0


def extract_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    # Re-join words hyphenated across line breaks: "exam-\nple" -> "example"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse layout line breaks and repeated whitespace; sentence
    # punctuation is what drives the pauses in the speech.
    return re.sub(r"\s+", " ", text).strip()


def require_voice_model() -> None:
    if not VOICE_MODEL.is_file():
        sys.exit(
            f"error: voice model missing at {VOICE_MODEL}\n"
            "Download it with:\n"
            "  .venv/bin/python -m piper.download_voices en_US-lessac-medium --data-dir voices"
        )


def synthesize(text: str, wav_path: Path) -> None:
    voice = PiperVoice.load(VOICE_MODEL)
    with wave.open(str(wav_path), "wb") as wav_file:
        voice.synthesize_wav(
            text, wav_file, syn_config=SynthesisConfig(length_scale=LENGTH_SCALE)
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert an English text PDF to a spoken WAV file."
    )
    parser.add_argument("pdf", type=Path, help="path to the PDF to read aloud")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output WAV path (default: same name as the PDF, .wav extension)",
    )
    args = parser.parse_args()

    if not args.pdf.is_file():
        sys.exit(f"error: file not found: {args.pdf}")
    require_voice_model()

    text = extract_text(args.pdf)
    if not text:
        sys.exit(
            "error: no text could be extracted from this PDF. "
            "It is probably a scanned/image-only PDF, which would need OCR."
        )

    words = len(text.split())
    print(f"Extracted {words} words from {args.pdf.name}. Synthesizing speech...")

    voice = PiperVoice.load(VOICE_MODEL)
    output = args.output or args.pdf.with_suffix(".wav")
    with wave.open(str(output), "wb") as wav_file:
        voice.synthesize_wav(
            text, wav_file, syn_config=SynthesisConfig(length_scale=LENGTH_SCALE)
        )

    with wave.open(str(output), "rb") as wav_file:
        seconds = wav_file.getnframes() / wav_file.getframerate()
    print(f"Wrote {output} ({seconds / 60:.1f} minutes of audio).")


if __name__ == "__main__":
    main()
