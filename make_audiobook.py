#!/usr/bin/env python3
"""Turn an English PDF or Markdown file into an MP3 and a YouTube-ready MP4.

The MP4 is the narration over a static 1920x1080 cover: the first page for
PDFs, a generated title card for Markdown files.
"""

import argparse
import re
import subprocess
import sys
import tempfile
import textwrap
import wave
from pathlib import Path

import imageio_ffmpeg
import pypdfium2 as pdfium
from PIL import Image, ImageDraw, ImageFont

from pdf2speech import extract_text as extract_pdf_text
from pdf2speech import require_voice_model, synthesize

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
CANVAS = (1920, 1080)


def extract_md_text(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    text = re.sub(r"```.*?```", " ", text, flags=re.S)  # code blocks
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)  # images
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)  # links -> label
    text = re.sub(r"^\s{0,3}#{1,6}\s+", "", text, flags=re.M)  # heading marks
    text = re.sub(r"^\s{0,3}(?:[-*+]|\d+\.)\s+", "", text, flags=re.M)  # list markers
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.M)  # blockquotes
    text = re.sub(r"^\s*[-=_*]{3,}\s*$", " ", text, flags=re.M)  # horizontal rules
    text = re.sub(r"[*_]{1,3}([^*_\n]+)[*_]{1,3}", r"\1", text)  # emphasis
    text = re.sub(r"`([^`]*)`", r"\1", text)  # inline code
    return re.sub(r"\s+", " ", text).strip()


def md_title(md_path: Path) -> str:
    for line in md_path.read_text(encoding="utf-8").splitlines():
        heading = re.match(r"\s{0,3}#\s+(.+)", line)
        if heading:
            return heading.group(1).strip()
    return md_path.stem.replace("-", " ").replace("_", " ")


def letterbox(img: Image.Image) -> Image.Image:
    """Scale an image to fit 1920x1080, centered on a black background."""
    img = img.convert("RGB")
    scale = min(CANVAS[0] / img.width, CANVAS[1] / img.height)
    resized = img.resize(
        (round(img.width * scale), round(img.height * scale)), Image.LANCZOS
    )
    canvas = Image.new("RGB", CANVAS, "black")
    canvas.paste(
        resized, ((CANVAS[0] - resized.width) // 2, (CANVAS[1] - resized.height) // 2)
    )
    return canvas


def pdf_cover(pdf_path: Path) -> Image.Image:
    page = pdfium.PdfDocument(pdf_path)[0]
    return letterbox(page.render(scale=4).to_pil())


def title_card(title: str) -> Image.Image:
    img = Image.new("RGB", CANVAS, "black")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT, 110)
    lines = textwrap.wrap(title, width=24) or [title]
    line_height = 140
    y = (CANVAS[1] - line_height * len(lines)) / 2
    for line in lines:
        width = draw.textlength(line, font=font)
        draw.text(((CANVAS[0] - width) / 2, y), line, font=font, fill="white")
        y += line_height
    return img


def run_ffmpeg(ffmpeg_args: list[str]) -> None:
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ffmpeg, "-y", "-loglevel", "error", *ffmpeg_args], check=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Narrate a PDF or Markdown file into an MP3 and a "
        "YouTube-ready MP4 with a static cover image."
    )
    parser.add_argument("input", type=Path, help="PDF or Markdown file to narrate")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        help="directory for the .mp3/.mp4 (default: next to the input)",
    )
    args = parser.parse_args()

    src = args.input
    if not src.is_file():
        sys.exit(f"error: file not found: {src}")
    suffix = src.suffix.lower()
    if suffix == ".pdf":
        text = extract_pdf_text(src)
        cover = pdf_cover(src)
    elif suffix in (".md", ".markdown"):
        text = extract_md_text(src)
        cover = title_card(md_title(src))
    else:
        sys.exit(f"error: unsupported input type '{src.suffix}' (use .pdf or .md)")
    if not text:
        sys.exit(
            "error: no text could be extracted from this PDF. "
            "It is probably a scanned/image-only PDF, which would need OCR."
        )
    require_voice_model()

    out_dir = args.output_dir or src.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    mp3 = out_dir / (src.stem + ".mp3")
    mp4 = out_dir / (src.stem + ".mp4")

    print(f"Extracted {len(text.split())} words from {src.name}. Synthesizing speech...")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "audio.wav"
        synthesize(text, wav)
        with wave.open(str(wav), "rb") as wav_file:
            seconds = wav_file.getnframes() / wav_file.getframerate()
        print(f"Synthesized {seconds / 60:.1f} minutes of audio. Encoding MP3...")

        run_ffmpeg(["-i", str(wav), "-c:a", "libmp3lame", "-b:a", "192k", str(mp3)])
        print(f"Wrote {mp3}. Encoding MP4...")

        cover_png = Path(tmp) / "cover.png"
        cover.save(cover_png)
        run_ffmpeg(
            [
                "-loop", "1", "-framerate", "5", "-i", str(cover_png),
                "-i", str(wav),
                "-c:v", "libx264", "-tune", "stillimage",
                "-c:a", "aac", "-b:a", "192k",
                "-pix_fmt", "yuv420p", "-shortest", "-movflags", "+faststart",
                str(mp4),
            ]
        )
    print(f"Wrote {mp4}. Done.")


if __name__ == "__main__":
    main()
