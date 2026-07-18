# pdf2speech

An offline toolkit that turns PDF or Markdown books into audiobook MP3s and
YouTube-ready MP4 videos, narrated by natural neural voices (Kokoro + Piper)
with chapter-aware pacing and support for English, Persian, and Danish.

## Website

- [English](https://cocodedk.github.io/pdf2speech/)
- [فارسی (Persian)](https://cocodedk.github.io/pdf2speech/fa/)

## Features

- **Fully offline and private** — text extraction and speech synthesis both
  run on your machine; nothing is uploaded anywhere.
- **Natural neural voices** — [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M)
  for the most natural English narration, or [Piper](https://github.com/OHF-Voice/piper1-gpl)
  for ~30 languages, including Persian and Danish.
- **Book-quality pacing** — spoken chapter announcements, epigraph beats,
  paragraph breaths, and longer rests at chapter ends.
- **YouTube-ready MP4** — a static cover (PDF page or generated title card)
  plus an auto-generated chapter list with real timestamps, ready to paste
  into a video description.
- **Three tools for three input shapes** — a quick PDF-to-WAV draft tool, a
  single-file MP3+MP4 converter, and a flagship chapter-Markdown narrator.

## Usage

### `./pdf2speech` — quick PDF to WAV

```sh
./pdf2speech mybook.pdf              # writes mybook.wav next to the PDF
./pdf2speech mybook.pdf -o out.wav   # choose the output path
```

Play the result with any audio player, e.g. `aplay out.wav` or `mpv out.wav`.

### `./make_audiobook` — MP3 + YouTube-ready MP4

Narrates a PDF **or Markdown** file and writes both an MP3 and an MP4
(H.264 + AAC, 1920x1080) that can be uploaded to YouTube directly. The video
shows a static cover: the first page for PDFs, a generated title card
(from the first `#` heading) for Markdown.

```sh
./make_audiobook mybook.pdf            # writes mybook.mp3 + mybook.mp4
./make_audiobook notes.md -o ~/out/    # choose the output directory
./make_audiobook mybook.pdf --engine piper --voice af_heart
```

### `./narrate_book` — flagship chapter-aware narration

Reads a folder of per-chapter `.md` files (in filename order) and produces
one MP3 + MP4 with human-friendly pauses: after chapter headings (`## 3.
Name` is spoken as "Chapter 3. Name"), after epigraphs (`>` blocks, last
line read as the attribution), a short breath between paragraphs, and a
long rest at chapter ends. YAML frontmatter is skipped.

```sh
./narrate_book mybook/chapters --voice am_michael --cover-pdf mybook.pdf
```

Non-English books use the Piper engine (Kokoro has no Persian) with a
spoken chapter label and an explicit output name:

```sh
./narrate_book mybook/persian --engine piper --voice fa_IR-ganji_adabi-medium \
    --chapter-label فصل --cover-pdf mybook-fa.pdf --name mybook-fa
```

Other useful flags: `--audio-bitrate 192k` (audio bitrate for MP3/MP4) and
`--no-mp3` (produce only the MP4).

Two TTS engines are available everywhere `--engine` appears:

- `kokoro` (default) — the most natural voice, ~3x realtime on CPU. Pick a
  narrator with `--voice`: `af_heart` (female, default) or `am_michael`
  (male) are the best; the model downloads from Hugging Face on first use.
- `piper` — much faster (~8-30x realtime), for quick drafts or languages
  Kokoro doesn't support.

## Build from Source

Prerequisites: Python 3.12. No system ffmpeg is needed — a static binary
ships via `imageio-ffmpeg`.

```sh
git clone git@github.com:cocodedk/pdf2speech.git
cd pdf2speech
python3 -m venv .venv
```

Install the CPU build of torch **before** the rest of the requirements, or
pip will pull the huge CUDA build:

```sh
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
.venv/bin/pip install -r requirements.txt
```

Download a Piper voice (used by `pdf2speech` and as the `--engine piper`
option elsewhere):

```sh
.venv/bin/python -m piper.download_voices en_US-lessac-medium --data-dir voices
```

Run the tests:

```sh
.venv/bin/pytest
```

## Architecture

```
pdf2speech.py      # PDF -> WAV (Piper, fast draft tool)
make_audiobook.py  # PDF/Markdown -> MP3 + MP4 (Kokoro or Piper)
narrate_book.py    # chapter-aware Markdown -> MP3 + MP4 (flagship)
kokoro_speech.py   # shared Kokoro synthesis helpers
pdf2speech         # venv-wrapping shell entry point
make_audiobook     # venv-wrapping shell entry point
narrate_book       # venv-wrapping shell entry point
voices/            # downloaded Piper voice models (gitignored)
tests/             # test suite and fixtures
```

| Purpose            | Technology                                              |
| ------------------ | -------------------------------------------------------- |
| TTS engines         | [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M), [Piper](https://github.com/OHF-Voice/piper1-gpl) |
| PDF/text extraction | [pypdf](https://pypi.org/project/pypdf/), [pypdfium2](https://pypi.org/project/pypdfium2/) |
| Video packaging     | ffmpeg via [imageio-ffmpeg](https://pypi.org/project/imageio-ffmpeg/) |
| Title card images   | [Pillow](https://pypi.org/project/pillow/)                |

## Author

**Babak Bandpey** — [cocode.dk](https://cocode.dk) | [LinkedIn](https://linkedin.com/in/babakbandpey) | [GitHub](https://github.com/cocodedk)

## License

Apache-2.0 | © 2026 [Cocode](https://cocode.dk) | Created by [Babak Bandpey](https://linkedin.com/in/babakbandpey)
