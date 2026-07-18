# CLAUDE.md

Local text-to-speech toolkit: turn English PDFs/Markdown into audio and
YouTube-ready video. Everything below is hard-won operational knowledge;
read it before changing synthesis code.

## Hard constraint: local-only TTS

**All TTS must run on this machine (author's rule, 2026-07-15).** Do not
propose or wire in cloud TTS APIs (ElevenLabs, Azure, OpenAI, etc.). The
quality ceiling is whatever runs locally.

## The three tools

- `./pdf2speech file.pdf` - PDF to WAV via Piper (fast draft tool).
- `./make_audiobook file.{pdf,md}` - MP3 + MP4, engine selectable
  (`--engine kokoro|piper`, `--voice`).
- `./narrate_book chapters_dir/` - book-quality narration from per-chapter
  Markdown with structured pauses; this is the flagship. Skips YAML
  frontmatter; `## 3. Name` is spoken as "Chapter 3. Name"; `>` blocks are
  epigraphs (last line = attribution); pauses: heading 1.5s, epigraph 1.8s,
  paragraph 0.5s, chapter end 3.0s (constants at top of `narrate_book.py`).

## Engines: measured facts (this machine)

- **Kokoro-82M** (default): the best local quality. ~3x realtime on CPU.
  English voices: `am_michael` (male narrator, ~167 wpm natural - already
  moderate, never stretch it), `af_heart` (best female). No Persian; langs
  are en/es/fr/hi/it/ja/pt/zh. First use downloads ~330 MB from HF.
- **Piper** (`en_US-lessac-medium` in `voices/`): ~8x realtime, mechanical
  next to Kokoro. Speed via `LENGTH_SCALE` in `pdf2speech.py`; stretching
  beyond ~1.2 makes it drone (that, not the model, caused the "very
  mechanical" complaint). Prefer a naturally slower voice over stretching.
- Piper wpm varies with word length: ~160 wpm on academic text, ~200 on
  fiction, same engine settings. Judge pace by listening, not wpm math.

## Other languages (Persian, Danish)

- Kokoro has **no Persian**. Local ceiling is Piper's five fa_IR medium
  voices: `amir`, `ganji`, `ganji_adabi`, `gyro`, `reza_ibrahim`. The
  author auditioned all five and picked **`ganji` (best reading and pace,
  2026-07-15)** as the default. Samples from the book's actual Persian
  opening: `~/projects/books/unjudgeable/voice-samples/piper-fa-*`.
- Persian script omits the ezafe, so TTS guesses it and natives hear the
  misses. Sample-check with the author before committing to a full run.
- `narrate_book` supports any local Piper voice via `--engine piper
  --voice <model> --chapter-label <word> --name <base>`. Python's `\d`
  matches Persian digits, so `## ۱.` headings become «فصل ۱. ...». Piper
  pace for this path is `PIPER_LENGTH_SCALE` (1.1, as auditioned).
- **Danish**: Piper has exactly one voice, `da_DK-talesyntese-medium`
  (no alternative locally; Kokoro has no Danish). Used with
  `--chapter-label Kapitel`. Sample: `voice-samples/piper-da-talesyntese.mp3`.

## Environment quirks

- No system pip/ensurepip: `.venv` was built `--without-pip` + get-pip.py.
- Install torch CPU-only BEFORE `requirements.txt`, or pip pulls the CUDA
  build: `pip install torch --index-url https://download.pytorch.org/whl/cpu`.
- No system ffmpeg. Use the bundled static one:
  `.venv/bin/python -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())"`
  (has libx264, aac, libmp3lame).
- Title cards use `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`.
- Piper voices live in `voices/` (gitignored); re-download with
  `.venv/bin/python -m piper.download_voices <name> --data-dir voices`.

## Extraction gotchas (learned the hard way)

- Page-numbered PDFs leave a bare digit line at each page's text tail;
  `extract_text` strips it (it was being read aloud mid-sentence).
- Rejoin hyphenated line breaks before synthesis; collapse whitespace.
- Scanned/image PDFs have no text: fail with a clear error, no OCR here.
- When Markdown sources exist, always narrate from them, never the PDF:
  cleaner text, real structure (chapters, epigraphs), no layout artifacts.

## Packaging for YouTube

- MP4 = static 1920x1080 cover (PDF page 1 letterboxed, or generated title
  card) + `-loop 1 -framerate 5 -c:v libx264 -tune stillimage -c:a aac
  -pix_fmt yuv420p -shortest -movflags +faststart`.
- MP3 shows 160 kb/s despite `-b:a 192k`: LAME caps MPEG-2 layer III
  (needed at 22.05/24 kHz mono) at 160k. Not a bug.
- Kokoro leaves ~0.5-1s trailing silence per synthesized segment, so
  configured pauses come out roughly that much longer in the audio.

## Verifying narration changes cheaply

- Parser changes: print `parse_chapter()` segments for a title file, a
  numbered chapter, and the unnumbered epilogue; grep for frontmatter leaks.
- Pause changes: build a 2-chapter mini-book in the scratchpad, then
  `ffmpeg -af silencedetect=noise=-40dB:d=0.4` and match silences to the
  expected pause pattern.
- Full-book runs: always background them (Kokoro book run is ~30 min alone,
  ~75 min if the CPU is shared); spot-check the result with `volumedetect`
  on a mid-file slice and check container durations.

## The Unjudgeable book (~/projects/books/unjudgeable)

- Its own CLAUDE.md governs; read it first. Key points that bind this
  project: **narration is on hold** (author, 2026-07-15; do not run or
  suggest `build_all.fish` / narration until the text settles), the repo is
  private, and its house style bans em-dashes.
- `build/build_all.fish` there = rebuild PDFs + narrate ALL editions:
  English via Kokoro `am_michael` -> `unjudgeable.mp3/.mp4`, Persian via
  Piper `fa_IR-ganji-medium` with «فصل» labels -> `unjudgeable-fa.mp3/.mp4`,
  Danish via Piper `da_DK-talesyntese-medium` with "Kapitel" labels ->
  `unjudgeable-da.mp3/.mp4`; **all into `media/`** (mp3/mp4 gitignored).
  When running a single edition manually, always pass `-o media` and copy
  the voice/label/cover flags from the script, or outputs land in the
  book root by default (narrate_book defaults to the chapters folder's
  parent).
- `voice-samples/` there holds all auditioned voices (English and Persian).
