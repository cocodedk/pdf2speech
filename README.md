# pdf2speech

Converts any English text PDF into spoken audio (a WAV file), read at an
unhurried audiobook pace (25% slower than the voice's natural speed; see
`LENGTH_SCALE` in `pdf2speech.py` to adjust).

Runs fully offline: text is extracted with [pypdf](https://pypi.org/project/pypdf/)
and spoken with [Piper](https://github.com/OHF-Voice/piper1-gpl), a neural
text-to-speech engine, using the `en_US-lessac-medium` voice.

## Usage

```sh
./pdf2speech mybook.pdf              # writes mybook.wav next to the PDF
./pdf2speech mybook.pdf -o out.wav   # choose the output path
```

Play the result with any audio player, e.g. `aplay out.wav` or `mpv out.wav`.

## MP3 + YouTube-ready MP4

`make_audiobook` narrates a PDF **or Markdown** file and writes both an MP3
and an MP4 (H.264 + AAC, 1920x1080) that can be uploaded to YouTube directly.
The video shows a static cover: the first page for PDFs, a generated title
card (from the first `#` heading) for Markdown.

```sh
./make_audiobook mybook.pdf            # writes mybook.mp3 + mybook.mp4
./make_audiobook notes.md -o ~/out/    # choose the output directory
```

Two TTS engines are available:

- `--engine kokoro` (default) — [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M),
  the most natural voice, ~3x realtime on CPU. Pick a narrator with
  `--voice`: `af_heart` (female, default) or `am_michael` (male) are the
  best; the model downloads from Hugging Face on first use.
- `--engine piper` — the Piper voice above, ~30x realtime, for quick runs.

Note: install the CPU build of torch **before** the requirements, or pip
will pull the huge CUDA build:

```sh
.venv/bin/pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Setup (already done in this checkout)

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m piper.download_voices en_US-lessac-medium --data-dir voices
```

## Limitations

- Scanned/image-only PDFs have no extractable text and are rejected with a
  clear error (OCR is not included).
- English voice only; other languages will be read with English pronunciation.
