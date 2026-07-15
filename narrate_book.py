#!/usr/bin/env python3
"""Narrate a book from a folder of per-chapter Markdown files into an MP3
and a YouTube-ready MP4, with human-friendly pauses.

Chapters are read in filename order. Understood structure per file:

    --- yaml frontmatter ---   skipped, never narrated
    # Title                    book title
    ## 3. Chapter Name         spoken as "Chapter 3. Chapter Name"
    > quote lines              epigraph; the LAST > line is the attribution
    blank line                 paragraph break
    ---                        separator, skipped

Pauses: after headings and epigraphs, a short breath between paragraphs,
and a long rest at the end of each chapter.
"""

import argparse
import re
import sys
import tempfile
import warnings
import wave
from pathlib import Path

import numpy as np

from kokoro_speech import SAMPLE_RATE, SPEED
from make_audiobook import pdf_cover, run_ffmpeg, title_card

PAUSE_HEADING = 1.5
PAUSE_EPIGRAPH_BODY = 0.6
PAUSE_EPIGRAPH = 1.8
PAUSE_PARAGRAPH = 0.5
PAUSE_CHAPTER_END = 3.0

# Piper pacing for the piper engine (matches the auditioned fa_IR samples).
PIPER_LENGTH_SCALE = 1.1


def clean_inline(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links -> label
    text = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", text)  # emphasis
    text = re.sub(r"`([^`]*)`", r"\1", text)  # inline code
    return re.sub(r"\s+", " ", text).strip()


def end_sentence(text: str) -> str:
    return text if text[-1] in ".!?؟…" else text + "."


def parse_chapter(md_path: Path, chapter_label: str = "Chapter") -> list[tuple[str, float]]:
    """Return the chapter as (text, pause_after_seconds) segments."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    if lines and lines[0].strip() == "---":  # yaml frontmatter
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                lines = lines[i + 1 :]
                break

    segments: list[tuple[str, float]] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or re.fullmatch(r"-{3,}", line):
            i += 1
        elif line.startswith("## "):
            heading = line[3:].strip()
            numbered = re.match(r"(\d+)\.\s*(.+)", heading)  # \d matches ۱۲۳ too
            if numbered:
                heading = f"{chapter_label} {numbered.group(1)}. {numbered.group(2)}"
            segments.append((end_sentence(heading), PAUSE_HEADING))
            i += 1
        elif line.startswith("# "):
            segments.append((end_sentence(line[2:].strip()), PAUSE_HEADING))
            i += 1
        elif line.startswith(">"):
            quote = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quoted = lines[i].strip().lstrip(">").strip()
                if quoted:
                    quote.append(quoted)
                i += 1
            if len(quote) > 1:
                segments.append((clean_inline(" ".join(quote[:-1])), PAUSE_EPIGRAPH_BODY))
                segments.append((end_sentence(clean_inline(quote[-1])), PAUSE_EPIGRAPH))
            elif quote:
                segments.append((clean_inline(quote[0]), PAUSE_EPIGRAPH))
        else:
            para = []
            while i < len(lines) and lines[i].strip() and not re.match(
                r"#|>|-{3,}\s*$", lines[i].strip()
            ):
                para.append(lines[i].strip())
                i += 1
            text = clean_inline(" ".join(para))
            if text:
                segments.append((text, PAUSE_PARAGRAPH))

    if segments:  # rest at the end of the chapter
        segments[-1] = (segments[-1][0], PAUSE_CHAPTER_END)
    return segments


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Narrate per-chapter Markdown files into an MP3 and a "
        "YouTube-ready MP4 with chapter-aware pauses."
    )
    parser.add_argument(
        "chapters_dir", type=Path, help="folder of chapter .md files (read in name order)"
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="directory for the .mp3/.mp4 (default: parent of the chapters folder)",
    )
    parser.add_argument(
        "--engine",
        choices=("kokoro", "piper"),
        default="kokoro",
        help="TTS engine (kokoro has no Persian; use piper with a fa_IR voice)",
    )
    parser.add_argument(
        "--voice",
        default="af_heart",
        help="kokoro voice (e.g. am_michael) or piper model name "
        "(e.g. fa_IR-ganji_adabi-medium, looked up in voices/)",
    )
    parser.add_argument(
        "--chapter-label",
        default="Chapter",
        help='word spoken before numbered chapter headings (e.g. "فصل")',
    )
    parser.add_argument(
        "--name", help="output base name (default: a slug of the book title)"
    )
    parser.add_argument(
        "--cover-pdf",
        type=Path,
        help="PDF whose first page becomes the video cover "
        "(default: a title card generated from the book title)",
    )
    args = parser.parse_args()

    md_files = sorted(args.chapters_dir.glob("*.md"))
    if not md_files:
        sys.exit(f"error: no .md files in {args.chapters_dir}")

    chapters = [(f.name, parse_chapter(f, args.chapter_label)) for f in md_files]
    chapters = [(name, segs) for name, segs in chapters if segs]
    if not chapters:
        sys.exit(f"error: no narratable text in {args.chapters_dir}")
    words = sum(len(t.split()) for _, segs in chapters for t, _ in segs)

    # Book title: the first file's opening segment, unless it is already a
    # chapter heading — then fall back to the folder's parent name.
    title = args.chapters_dir.resolve().parent.name
    first_segment = chapters[0][1][0][0]
    if not first_segment.startswith(args.chapter_label):
        title = first_segment.rstrip(".")
    slug = args.name or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") or "book"

    out_dir = args.output_dir or args.chapters_dir.resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3 = out_dir / f"{slug}.mp3"
    mp4 = out_dir / f"{slug}.mp4"

    print(f"Narrating {len(chapters)} files, {words} words...")
    warnings.filterwarnings("ignore")
    if args.engine == "kokoro":
        from kokoro import KPipeline  # imports torch; keep out of module load

        pipeline = KPipeline(lang_code=args.voice[0], repo_id="hexgrad/Kokoro-82M")
        sample_rate = SAMPLE_RATE

        def speak(text: str, wav_file: wave.Wave_write) -> None:
            for _, _, audio in pipeline(text, voice=args.voice, speed=SPEED):
                pcm = (np.clip(audio.numpy(), -1.0, 1.0) * 32767).astype("<i2")
                wav_file.writeframes(pcm.tobytes())

    else:
        from piper import PiperVoice, SynthesisConfig

        model = Path(__file__).resolve().parent / "voices" / f"{args.voice}.onnx"
        if not model.is_file():
            sys.exit(
                f"error: piper voice missing at {model}\nDownload it with:\n"
                f"  .venv/bin/python -m piper.download_voices {args.voice} --data-dir voices"
            )
        piper_voice = PiperVoice.load(model)
        sample_rate = piper_voice.config.sample_rate
        syn_config = SynthesisConfig(length_scale=PIPER_LENGTH_SCALE)

        def speak(text: str, wav_file: wave.Wave_write) -> None:
            piper_voice.synthesize_wav(
                text, wav_file, syn_config=syn_config, set_wav_format=False
            )

    chapter_marks: list[tuple[str, float]] = []
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = Path(tmp) / "audio.wav"
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            for name, segments in chapters:
                print(f"  {name} ({len(segments)} segments)")
                # Chapter start = frames written so far; the spoken heading is
                # the chapter's display title (trailing period dropped).
                chapter_marks.append(
                    (segments[0][0].rstrip("."), wav_file.tell() / sample_rate)
                )
                for text, pause in segments:
                    speak(text, wav_file)
                    wav_file.writeframes(b"\x00\x00" * int(pause * sample_rate))

        with wave.open(str(wav_path), "rb") as wav_file:
            seconds = wav_file.getnframes() / wav_file.getframerate()
        print(f"Synthesized {seconds / 60:.1f} minutes of audio. Encoding MP3...")

        # YouTube chapter list: description-ready timestamps. YouTube needs the
        # first stamp at 0:00 and at least 10 seconds per chapter, so any
        # section shorter than that (the title page) is folded into the next
        # chapter, which inherits the earlier start time.
        merged: list[tuple[str, float]] = []
        for mark_title, start in chapter_marks:
            if merged and start - merged[-1][1] < 10.0:
                merged[-1] = (mark_title, merged[-1][1])
            else:
                merged.append((mark_title, start))

        def stamp(t: float) -> str:
            hours, rem = divmod(int(t), 3600)
            minutes, secs = divmod(rem, 60)
            if seconds >= 3600:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"

        chapters_txt = out_dir / f"{slug}-chapters.txt"
        chapters_txt.write_text(
            "".join(f"{stamp(start)} {mark_title}\n" for mark_title, start in merged),
            encoding="utf-8",
        )
        print(f"Wrote {chapters_txt} (YouTube chapter list).")
        run_ffmpeg(["-i", str(wav_path), "-c:a", "libmp3lame", "-b:a", "192k", str(mp3)])
        print(f"Wrote {mp3}. Encoding MP4...")

        cover = pdf_cover(args.cover_pdf) if args.cover_pdf else title_card(title)
        cover_png = Path(tmp) / "cover.png"
        cover.save(cover_png)
        run_ffmpeg(
            [
                "-loop", "1", "-framerate", "5", "-i", str(cover_png),
                "-i", str(wav_path),
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart",
                str(mp4),
            ]
        )
    print(f"Wrote {mp4}. Done.")


if __name__ == "__main__":
    main()
