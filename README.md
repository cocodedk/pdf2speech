# pdf2speech

Converts any English text PDF into spoken audio (a WAV file), read at a
moderate, audiobook-like pace (~160 words per minute — neither fast nor slow).

Runs fully offline: text is extracted with [pypdf](https://pypi.org/project/pypdf/)
and spoken with [Piper](https://github.com/OHF-Voice/piper1-gpl), a neural
text-to-speech engine, using the `en_US-lessac-medium` voice.

## Usage

```sh
./pdf2speech mybook.pdf              # writes mybook.wav next to the PDF
./pdf2speech mybook.pdf -o out.wav   # choose the output path
```

Play the result with any audio player, e.g. `aplay out.wav` or `mpv out.wav`.

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
