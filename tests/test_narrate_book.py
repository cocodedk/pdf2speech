"""Tests for narrate_book's Markdown-to-segments parsing.

These only exercise text parsing (parse_chapter, clean_inline, end_sentence);
they do not touch TTS synthesis, so no kokoro/piper/torch is needed.
"""

from pathlib import Path

from narrate_book import clean_inline, end_sentence, parse_chapter


def test_parse_chapter_full_structure(tmp_path: Path) -> None:
    md = tmp_path / "chapter.md"
    md.write_text(
        "---\n"
        "chapter: 1\n"
        "---\n"
        "## 1. First\n"
        "\n"
        "> Quote line.\n"
        "> Sage\n"
        "\n"
        "Para one.\n"
        "\n"
        "Para two.\n",
        encoding="utf-8",
    )

    segments = parse_chapter(md)

    assert segments == [
        ("Chapter 1. First.", 1.5),
        ("Quote line.", 0.6),
        ("Sage.", 1.8),
        ("Para one.", 0.5),
        ("Para two.", 3.0),
    ]
    # Frontmatter must never leak into narrated text.
    for text, _pause in segments:
        assert "chapter: 1" not in text
        assert "---" not in text


def test_parse_chapter_persian_numbered_heading(tmp_path: Path) -> None:
    md = tmp_path / "chapter.md"
    md.write_text("## ۱. یادبود\n", encoding="utf-8")

    segments = parse_chapter(md, chapter_label="فصل")

    assert segments[0][0] == "فصل ۱. یادبود."


def test_parse_chapter_title_only(tmp_path: Path) -> None:
    md = tmp_path / "title.md"
    md.write_text("# My Book\n", encoding="utf-8")

    segments = parse_chapter(md)

    assert segments == [("My Book.", 3.0)]


def test_clean_inline_strips_markdown() -> None:
    assert (
        clean_inline("**bold** and [link](http://x) and `code`")
        == "bold and link and code"
    )


def test_end_sentence() -> None:
    assert end_sentence("Hi") == "Hi."
    assert end_sentence("Hi!") == "Hi!"
    assert end_sentence("سلام؟") == "سلام؟"
